from __future__ import annotations

from collections import Counter
from contextlib import AbstractContextManager, contextmanager
from datetime import datetime, timedelta, timezone
import hmac
import ipaddress
from typing import Any, Callable, Iterator, Mapping, Protocol, Type

from .adapters.postgres import ReadinessDiagnosticsAggregates, _validate_lifecycle_state
from .config import RuntimeConfig
from .models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    AnalyticSignalRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    LifecycleTransitionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)

_LEGACY_PHASE21_MISSING_RECORD_FAMILIES = frozenset(
    {
        ObservationRecord.record_family,
        LeadRecord.record_family,
        RecommendationRecord.record_family,
        LifecycleTransitionRecord.record_family,
        HuntRecord.record_family,
        HuntRunRecord.record_family,
        AITraceRecord.record_family,
    }
)
_LEGACY_RESTORE_FALLBACK_TRANSITION_ANCHOR = datetime(
    2000,
    1,
    1,
    tzinfo=timezone.utc,
)


def _parse_optional_backup_created_at(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    return parsed


def _is_missing_runtime_binding(value: object) -> bool:
    if value is None:
        return True
    return str(value).strip() in {"", "<set-me>"}


class ControlPlaneStore(Protocol):
    dsn: str
    persistence_mode: str

    def save(self, record: ControlPlaneRecord) -> ControlPlaneRecord:
        ...

    def list(self, record_type: Type[ControlPlaneRecord]) -> tuple[ControlPlaneRecord, ...]:
        ...

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        ...

    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> AbstractContextManager[None]:
        ...


class RuntimeBoundaryService:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        store: ControlPlaneStore,
        reconciliation_adapter: Any,
        shuffle_adapter: Any,
        isolated_executor_adapter: Any,
        runtime_snapshot_factory: Callable[..., Any],
        authenticated_principal_factory: Callable[..., Any],
    ) -> None:
        self._config = config
        self._store = store
        self._reconciliation = reconciliation_adapter
        self._shuffle = shuffle_adapter
        self._isolated_executor = isolated_executor_adapter
        self._runtime_snapshot_factory = runtime_snapshot_factory
        self._authenticated_principal_factory = authenticated_principal_factory

    def describe_runtime(self) -> Any:
        return self._runtime_snapshot_factory(
            service_name="aegisops-control-plane",
            bind_host=self._config.host,
            bind_port=self._config.port,
            postgres_dsn=self._store.dsn,
            persistence_mode=self._store.persistence_mode,
            opensearch_url=self._config.opensearch_url,
            n8n_base_url=self._reconciliation.base_url,
            shuffle_base_url=self._shuffle.base_url,
            isolated_executor_base_url=self._isolated_executor.base_url,
            ownership_boundary={
                "runtime_root": "control-plane/",
                "postgres_contract_root": "postgres/control-plane/",
                "native_detection_intake": "substrate-adapters/",
                "admitted_signal_model": "control-plane/analytic-signals",
                "routine_automation_substrate": "shuffle/",
                "controlled_execution_surface": "executor/isolated-executor",
            },
        )

    def validate_wazuh_ingest_runtime(self) -> None:
        if _is_missing_runtime_binding(self._config.wazuh_ingest_shared_secret):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET must be set "
                "before starting the live Wazuh ingest runtime"
            )
        for cidr in self._config.wazuh_ingest_trusted_proxy_cidrs:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except ValueError as exc:
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must contain "
                    f"only valid IP networks, got: {cidr!r}"
                ) from exc
        if (
            not self.listener_is_loopback()
            and not self._config.wazuh_ingest_trusted_proxy_cidrs
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must be set "
                "before starting the live Wazuh ingest runtime on a non-loopback interface"
            )
        if _is_missing_runtime_binding(
            self._config.wazuh_ingest_reverse_proxy_secret
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET must be set "
                "before starting the live Wazuh ingest runtime"
            )

    def validate_protected_surface_runtime(self) -> None:
        for cidr in self._config.protected_surface_trusted_proxy_cidrs:
            try:
                ipaddress.ip_network(cidr, strict=False)
            except ValueError as exc:
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS must contain "
                    f"only valid IP networks, got: {cidr!r}"
                ) from exc
        if (
            not self.listener_is_loopback()
            and not self._config.protected_surface_trusted_proxy_cidrs
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS must be set "
                "before starting protected control-plane surfaces on a non-loopback interface"
            )
        if self._config.protected_surface_trusted_proxy_cidrs:
            if _is_missing_runtime_binding(
                self._config.protected_surface_reverse_proxy_secret
            ):
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET must be set "
                    "before admitting reviewed reverse-proxy traffic to protected control-plane surfaces"
                )
            if _is_missing_runtime_binding(
                self._config.protected_surface_proxy_service_account
            ):
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT must be set "
                    "before admitting reviewed reverse-proxy traffic to protected control-plane surfaces"
                )

    def authenticate_protected_surface_request(
        self,
        *,
        peer_addr: str | None,
        forwarded_proto: str | None,
        reverse_proxy_secret_header: str | None,
        proxy_service_account_header: str | None,
        authenticated_identity_header: str | None,
        authenticated_role_header: str | None,
        allowed_roles: tuple[str, ...],
    ) -> Any:
        self.validate_protected_surface_runtime()

        if self.peer_addr_is_loopback(peer_addr):
            principal = self._authenticated_principal_factory(
                identity="loopback-local-operator",
                role="loopback_local",
                access_path="loopback_direct",
            )
        else:
            if not self.is_trusted_protected_surface_peer(peer_addr):
                raise PermissionError(
                    "protected control-plane surfaces reject requests that bypass the reviewed reverse proxy peer boundary"
                )
            if (forwarded_proto or "").strip().lower() != "https":
                raise PermissionError(
                    "protected control-plane surfaces require the reviewed reverse proxy HTTPS boundary"
                )
            if not hmac.compare_digest(
                (reverse_proxy_secret_header or "").strip(),
                self._config.protected_surface_reverse_proxy_secret,
            ):
                raise PermissionError(
                    "protected control-plane surfaces require the reviewed reverse proxy boundary credential"
                )
            supplied_proxy_service_account = (proxy_service_account_header or "").strip()
            if not hmac.compare_digest(
                supplied_proxy_service_account,
                self._config.protected_surface_proxy_service_account,
            ):
                raise PermissionError(
                    "protected control-plane surfaces require the reviewed reverse proxy service account identity"
                )

            identity = (authenticated_identity_header or "").strip()
            if identity == "":
                raise PermissionError(
                    "protected control-plane surfaces require an attributed authenticated identity header"
                )
            role = (
                (authenticated_role_header or "")
                .strip()
                .lower()
                .replace("-", "_")
                .replace(" ", "_")
            )
            if role == "":
                raise PermissionError(
                    "protected control-plane surfaces require an attributed authenticated role header"
                )
            principal = self._authenticated_principal_factory(
                identity=identity,
                role=role,
                access_path="reviewed_reverse_proxy",
                proxy_service_account=supplied_proxy_service_account,
            )

        if principal.role not in allowed_roles:
            joined_roles = ", ".join(sorted(allowed_roles))
            raise PermissionError(
                "protected control-plane surface role is not authorized for this endpoint; "
                f"expected one of: {joined_roles}"
            )
        return principal

    def require_admin_bootstrap_token(self, supplied_token: str | None) -> None:
        expected_token = self._config.admin_bootstrap_token.strip()
        if _is_missing_runtime_binding(expected_token):
            raise PermissionError(
                "admin bootstrap contract is disabled until AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN is bound"
            )
        if not hmac.compare_digest((supplied_token or "").strip(), expected_token):
            raise PermissionError("admin bootstrap token did not match the reviewed secret")

    def require_break_glass_token(self, supplied_token: str | None) -> None:
        expected_token = self._config.break_glass_token.strip()
        if _is_missing_runtime_binding(expected_token):
            raise PermissionError(
                "break-glass contract is disabled until AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN is bound"
            )
        if not hmac.compare_digest((supplied_token or "").strip(), expected_token):
            raise PermissionError("break-glass token did not match the reviewed secret")

    def listener_is_loopback(self) -> bool:
        host = self._config.host.strip()
        if host.lower() == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def is_trusted_wazuh_ingest_peer(self, peer_addr: str | None) -> bool:
        return self.is_trusted_peer_for_proxy_cidrs(
            peer_addr,
            self._config.wazuh_ingest_trusted_proxy_cidrs,
        )

    def is_trusted_protected_surface_peer(self, peer_addr: str | None) -> bool:
        return self.is_trusted_peer_for_proxy_cidrs(
            peer_addr,
            self._config.protected_surface_trusted_proxy_cidrs,
        )

    def is_trusted_peer_for_proxy_cidrs(
        self,
        peer_addr: str | None,
        trusted_proxy_cidrs: tuple[str, ...],
    ) -> bool:
        if peer_addr is None:
            return False
        normalized_peer_addr = peer_addr.strip()
        if normalized_peer_addr == "":
            return False
        try:
            peer_ip = ipaddress.ip_address(normalized_peer_addr)
        except ValueError:
            return False
        if self.listener_is_loopback():
            return peer_ip.is_loopback
        for cidr in trusted_proxy_cidrs:
            if peer_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        return False

    @staticmethod
    def peer_addr_is_loopback(peer_addr: str | None) -> bool:
        if peer_addr is None or peer_addr.strip() == "":
            return False
        try:
            return ipaddress.ip_address(peer_addr.strip()).is_loopback
        except ValueError:
            return False


class RestoreReadinessService:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        store: ControlPlaneStore,
        runtime_boundary_service: RuntimeBoundaryService,
        startup_status_snapshot_factory: Callable[..., Any],
        readiness_diagnostics_snapshot_factory: Callable[..., Any],
        restore_drill_snapshot_factory: Callable[..., Any],
        restore_summary_snapshot_factory: Callable[..., Any],
        record_to_dict: Callable[[ControlPlaneRecord], dict[str, object]],
        json_ready: Callable[[object], object],
        redacted_reconciliation_payload: Callable[[ReconciliationRecord], dict[str, object]],
        build_shutdown_status_snapshot: Callable[..., Any],
        derive_readiness_status: Callable[..., str],
        record_from_backup_payload: Callable[[Type[ControlPlaneRecord], Mapping[str, object]], ControlPlaneRecord],
        authoritative_record_chain_record_types: tuple[Type[ControlPlaneRecord], ...],
        authoritative_record_chain_backup_schema_version: str,
        authoritative_primary_id_field_by_family: Mapping[str, str],
        record_types_by_family: Mapping[str, Type[ControlPlaneRecord]],
        find_duplicate_strings: Callable[[tuple[str, ...]], tuple[str, ...]],
        synthesize_lifecycle_transition_record: Callable[
            [ControlPlaneRecord, datetime | None],
            LifecycleTransitionRecord | None,
        ],
        assistant_ids_from_mapping: Callable[[Mapping[str, object] | None, str], tuple[str, ...]],
        inspect_case_detail: Callable[[str], Any],
        inspect_assistant_context: Callable[[str, str], Any],
        inspect_reconciliation_status: Callable[[], Any],
    ) -> None:
        self._config = config
        self._store = store
        self._runtime_boundary_service = runtime_boundary_service
        self._startup_status_snapshot_factory = startup_status_snapshot_factory
        self._readiness_diagnostics_snapshot_factory = (
            readiness_diagnostics_snapshot_factory
        )
        self._restore_drill_snapshot_factory = restore_drill_snapshot_factory
        self._restore_summary_snapshot_factory = restore_summary_snapshot_factory
        self._record_to_dict = record_to_dict
        self._json_ready = json_ready
        self._redacted_reconciliation_payload = redacted_reconciliation_payload
        self._build_shutdown_status_snapshot = build_shutdown_status_snapshot
        self._derive_readiness_status = derive_readiness_status
        self._record_from_backup_payload = record_from_backup_payload
        self._authoritative_record_chain_record_types = (
            authoritative_record_chain_record_types
        )
        self._authoritative_record_chain_backup_schema_version = (
            authoritative_record_chain_backup_schema_version
        )
        self._authoritative_primary_id_field_by_family = (
            authoritative_primary_id_field_by_family
        )
        self._record_types_by_family = record_types_by_family
        self._find_duplicate_strings = find_duplicate_strings
        self._synthesize_lifecycle_transition_record = (
            synthesize_lifecycle_transition_record
        )
        self._assistant_ids_from_mapping = assistant_ids_from_mapping
        self._inspect_case_detail = inspect_case_detail
        self._inspect_assistant_context = inspect_assistant_context
        self._inspect_reconciliation_status = inspect_reconciliation_status

    def describe_startup_status(self) -> Any:
        protected_surface_proxy_bindings_required = bool(
            self._config.protected_surface_trusted_proxy_cidrs
        )
        required_bindings = (
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN",
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET",
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET",
            *(
                (
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET",
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT",
                )
                if protected_surface_proxy_bindings_required
                else ()
            ),
            "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN",
        )
        binding_values = {
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN": self._config.postgres_dsn,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET": (
                self._config.wazuh_ingest_shared_secret
            ),
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET": (
                self._config.wazuh_ingest_reverse_proxy_secret
            ),
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET": (
                self._config.protected_surface_reverse_proxy_secret
            ),
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT": (
                self._config.protected_surface_proxy_service_account
            ),
            "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN": (
                self._config.admin_bootstrap_token
            ),
            "AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN": self._config.break_glass_token,
        }
        missing_bindings = tuple(
            binding_name
            for binding_name in required_bindings
            if _is_missing_runtime_binding(binding_values[binding_name])
        )
        validated_surfaces: list[str] = []
        blocking_reasons: list[str] = []
        try:
            self._runtime_boundary_service.validate_wazuh_ingest_runtime()
        except ValueError as exc:
            blocking_reasons.append(str(exc))
        else:
            validated_surfaces.append("wazuh_ingest")
        try:
            self._runtime_boundary_service.validate_protected_surface_runtime()
        except ValueError as exc:
            blocking_reasons.append(str(exc))
        else:
            validated_surfaces.append("protected_surface")

        return self._startup_status_snapshot_factory(
            read_only=True,
            startup_ready=not missing_bindings and not blocking_reasons,
            required_bindings=required_bindings,
            missing_bindings=missing_bindings,
            validated_surfaces=tuple(validated_surfaces),
            blocking_reasons=tuple(blocking_reasons),
        )

    def describe_shutdown_status(self) -> Any:
        readiness_aggregates = self.inspect_readiness_aggregates()
        return self._build_shutdown_status_snapshot(
            open_case_ids=readiness_aggregates.open_case_ids,
            active_action_request_ids=readiness_aggregates.active_action_request_ids,
            active_action_execution_ids=readiness_aggregates.active_action_execution_ids,
            unresolved_reconciliation_ids=readiness_aggregates.unresolved_reconciliation_ids,
        )

    def inspect_readiness_diagnostics(self) -> Any:
        with self._store.transaction(isolation_level="REPEATABLE READ"):
            startup = self.describe_startup_status()
            readiness_aggregates = self.inspect_readiness_aggregates()

        shutdown = self._build_shutdown_status_snapshot(
            open_case_ids=readiness_aggregates.open_case_ids,
            active_action_request_ids=readiness_aggregates.active_action_request_ids,
            active_action_execution_ids=readiness_aggregates.active_action_execution_ids,
            unresolved_reconciliation_ids=readiness_aggregates.unresolved_reconciliation_ids,
        )

        status = self._derive_readiness_status(
            startup_ready=startup.startup_ready,
            reconciliation_lifecycle_counts=readiness_aggregates.reconciliation_lifecycle_counts,
        )

        metrics = {
            "alerts": {
                "total": readiness_aggregates.alert_total,
                "by_lifecycle_state": dict(
                    sorted(readiness_aggregates.alert_lifecycle_counts.items())
                ),
            },
            "cases": {
                "total": readiness_aggregates.case_total,
                "open": len(readiness_aggregates.open_case_ids),
            },
            "action_requests": {
                "total": readiness_aggregates.action_request_total,
                "pending_approval": readiness_aggregates.action_request_lifecycle_counts.get(
                    "pending_approval", 0
                ),
                "approved": readiness_aggregates.action_request_lifecycle_counts.get(
                    "approved", 0
                ),
                "executing": readiness_aggregates.action_request_lifecycle_counts.get(
                    "executing", 0
                ),
                "unresolved": readiness_aggregates.action_request_lifecycle_counts.get(
                    "unresolved", 0
                ),
            },
            "action_executions": {
                "total": readiness_aggregates.action_execution_total,
                "dispatching": readiness_aggregates.action_execution_lifecycle_counts.get(
                    "dispatching", 0
                ),
                "queued": readiness_aggregates.action_execution_lifecycle_counts.get(
                    "queued", 0
                ),
                "running": readiness_aggregates.action_execution_lifecycle_counts.get(
                    "running", 0
                ),
                "terminal": sum(
                    count
                    for state, count in readiness_aggregates.action_execution_lifecycle_counts.items()
                    if state not in {"dispatching", "queued", "running"}
                ),
            },
            "reconciliations": {
                "total": readiness_aggregates.reconciliation_total,
                "matched": readiness_aggregates.reconciliation_lifecycle_counts.get(
                    "matched", 0
                ),
                "pending": readiness_aggregates.reconciliation_lifecycle_counts.get(
                    "pending", 0
                ),
                "mismatched": readiness_aggregates.reconciliation_lifecycle_counts.get(
                    "mismatched", 0
                ),
                "stale": readiness_aggregates.reconciliation_lifecycle_counts.get(
                    "stale", 0
                ),
                "by_ingest_disposition": dict(
                    sorted(
                        readiness_aggregates.reconciliation_ingest_disposition_counts.items()
                    )
                ),
            },
            "phase20_notify_identity_owner": {
                "requested_action_requests": readiness_aggregates.phase20_requested_action_requests,
                "approved_action_requests": readiness_aggregates.phase20_approved_action_requests,
                "reconciled_executions": readiness_aggregates.phase20_reconciled_executions,
            },
        }

        return self._readiness_diagnostics_snapshot_factory(
            read_only=True,
            booted=True,
            status=status,
            startup=startup.to_dict(),
            shutdown=shutdown.to_dict(),
            metrics=metrics,
            latest_reconciliation=(
                self._redacted_reconciliation_payload(
                    readiness_aggregates.latest_reconciliation
                )
                if readiness_aggregates.latest_reconciliation is not None
                else None
            ),
        )

    def inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
        aggregate_reader = getattr(self._store, "inspect_readiness_aggregates", None)
        if callable(aggregate_reader):
            return aggregate_reader()

        alerts = self._store.list(AlertRecord)
        cases = self._store.list(CaseRecord)
        action_requests = self._store.list(ActionRequestRecord)
        action_executions = self._store.list(ActionExecutionRecord)
        reconciliations = self._store.list(ReconciliationRecord)

        latest_reconciliation = max(
            reconciliations,
            key=lambda record: (record.compared_at, record.reconciliation_id),
            default=None,
        )
        phase20_action_requests = tuple(
            record
            for record in action_requests
            if record.requested_payload.get("action_type") == "notify_identity_owner"
        )
        phase20_request_ids = {
            record.action_request_id for record in phase20_action_requests
        }
        phase20_execution_run_ids = {
            record.execution_run_id
            for record in action_executions
            if (
                record.action_request_id in phase20_request_ids
                and record.execution_run_id is not None
            )
        }
        return ReadinessDiagnosticsAggregates(
            alert_total=len(alerts),
            alert_lifecycle_counts=dict(
                Counter(record.lifecycle_state for record in alerts)
            ),
            case_total=len(cases),
            open_case_ids=tuple(
                record.case_id
                for record in cases
                if record.lifecycle_state
                in {
                    "open",
                    "investigating",
                    "pending_action",
                    "contained_pending_validation",
                    "reopened",
                }
            ),
            action_request_total=len(action_requests),
            action_request_lifecycle_counts=dict(
                Counter(record.lifecycle_state for record in action_requests)
            ),
            active_action_request_ids=tuple(
                record.action_request_id
                for record in action_requests
                if record.lifecycle_state
                in {"pending_approval", "approved", "executing", "unresolved"}
            ),
            action_execution_total=len(action_executions),
            action_execution_lifecycle_counts=dict(
                Counter(record.lifecycle_state for record in action_executions)
            ),
            active_action_execution_ids=tuple(
                record.action_execution_id
                for record in action_executions
                if record.lifecycle_state in {"dispatching", "queued", "running"}
            ),
            reconciliation_total=len(reconciliations),
            reconciliation_lifecycle_counts=dict(
                Counter(record.lifecycle_state for record in reconciliations)
            ),
            reconciliation_ingest_disposition_counts=dict(
                Counter(record.ingest_disposition for record in reconciliations)
            ),
            unresolved_reconciliation_ids=tuple(
                record.reconciliation_id
                for record in reconciliations
                if record.lifecycle_state in {"pending", "mismatched", "stale"}
            ),
            latest_reconciliation=latest_reconciliation,
            phase20_requested_action_requests=len(phase20_action_requests),
            phase20_approved_action_requests=sum(
                1
                for record in phase20_action_requests
                if record.lifecycle_state == "approved"
            ),
            phase20_reconciled_executions=len(
                {
                    record.execution_run_id
                    for record in reconciliations
                    if (
                        record.lifecycle_state == "matched"
                        and record.execution_run_id in phase20_execution_run_ids
                    )
                }
            ),
        )

    def export_authoritative_record_chain_backup(self) -> dict[str, object]:
        record_families: dict[str, list[dict[str, object]]] = {}
        record_counts: dict[str, int] = {}
        with self._store.transaction(isolation_level="REPEATABLE READ"):
            authoritative_records = self._list_authoritative_record_chain_records()
            record_counts = {
                family: len(persisted_records)
                for family, persisted_records in authoritative_records.items()
            }
            self.validate_authoritative_record_chain_restore(
                authoritative_records,
                require_lifecycle_transition_history=True,
                restored_record_counts=record_counts,
            )
            for family, persisted_records in authoritative_records.items():
                records = [
                    self._json_ready(self._record_to_dict(record))
                    for record in persisted_records
                ]
                record_families[family] = records
        return {
            "backup_schema_version": self._authoritative_record_chain_backup_schema_version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "persistence_mode": self._store.persistence_mode,
            "record_families": record_families,
            "record_counts": record_counts,
        }

    def restore_authoritative_record_chain_backup(
        self,
        backup_payload: Mapping[str, object],
    ) -> Any:
        if not isinstance(backup_payload, Mapping):
            raise ValueError("restore payload must be a JSON object")
        backup_schema_version = backup_payload.get("backup_schema_version")
        legacy_phase21_backup = (
            backup_schema_version == "phase21.authoritative-record-chain.v1"
        )
        if not legacy_phase21_backup and (
            backup_schema_version
            != self._authoritative_record_chain_backup_schema_version
        ):
            raise ValueError(
                "restore payload must declare the reviewed authoritative record-chain schema version"
            )
        record_families_payload = backup_payload.get("record_families")
        if not isinstance(record_families_payload, Mapping):
            raise ValueError("restore payload must contain record_families")
        record_counts_payload = backup_payload.get("record_counts")
        if not isinstance(record_counts_payload, Mapping):
            raise ValueError("restore payload must contain record_counts")
        backup_created_at = _parse_optional_backup_created_at(
            backup_payload.get("created_at")
        )

        parsed_records: dict[str, tuple[ControlPlaneRecord, ...]] = {}
        restored_record_counts: dict[str, int] = {}
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            raw_records = record_families_payload.get(family)
            expected_count = record_counts_payload.get(family)
            if (
                legacy_phase21_backup
                and family in _LEGACY_PHASE21_MISSING_RECORD_FAMILIES
            ):
                raw_records = [] if raw_records is None else raw_records
                expected_count = 0 if expected_count is None else expected_count
            if not isinstance(raw_records, list):
                raise ValueError(
                    f"restore payload must contain a JSON array for record family {family!r}"
                )
            if expected_count != len(raw_records):
                raise ValueError(
                    f"restore payload record count mismatch for {family!r}: "
                    f"expected {expected_count!r}, found {len(raw_records)}"
                )
            parsed = tuple(
                self._record_from_backup_payload(record_type, raw_record)
                for raw_record in raw_records
            )
            parsed_records[family] = parsed
            restored_record_counts[family] = len(parsed)

        if legacy_phase21_backup:
            synthesized_transitions = self._synthesize_missing_lifecycle_transition_records(
                parsed_records,
                backup_created_at=backup_created_at,
            )
            parsed_records["lifecycle_transition"] = synthesized_transitions
            restored_record_counts["lifecycle_transition"] = len(synthesized_transitions)

        self.validate_authoritative_record_chain_restore(
            parsed_records,
            require_lifecycle_transition_history=True,
            restored_record_counts=restored_record_counts,
        )
        with self._store.transaction(isolation_level="SERIALIZABLE"):
            self.require_empty_authoritative_restore_target()
            for record_type in self._authoritative_record_chain_record_types:
                for record in parsed_records[record_type.record_family]:
                    self._store.save(record)
            restore_drill = self.run_authoritative_restore_drill(
                require_lifecycle_transition_history=True
            )
        return self._restore_summary_snapshot_factory(
            read_only=True,
            restored_record_counts=restored_record_counts,
            restore_drill=restore_drill,
        )

    @contextmanager
    def restore_drill_snapshot_transaction(self) -> Iterator[None]:
        try:
            with self._store.transaction(isolation_level="REPEATABLE READ"):
                yield
                return
        except ValueError as exc:
            if str(exc) != "Cannot set isolation_level inside an active transaction":
                raise
        with self._store.transaction():
            yield

    def run_authoritative_restore_drill(
        self,
        *,
        require_lifecycle_transition_history: bool = True,
    ) -> Any:
        with self.restore_drill_snapshot_transaction():
            return self.run_authoritative_restore_drill_snapshot(
                require_lifecycle_transition_history=require_lifecycle_transition_history
            )

    def run_authoritative_restore_drill_snapshot(
        self,
        *,
        require_lifecycle_transition_history: bool = True,
    ) -> Any:
        self.validate_authoritative_record_chain_restore(
            self._list_authoritative_record_chain_records(),
            require_lifecycle_transition_history=require_lifecycle_transition_history,
        )
        verified_case_ids = tuple(
            record.case_id for record in self._store.list(CaseRecord)
        )
        verified_recommendation_ids = tuple(
            record.recommendation_id for record in self._store.list(RecommendationRecord)
        )
        verified_approval_decision_ids = tuple(
            record.approval_decision_id
            for record in self._store.list(ApprovalDecisionRecord)
        )
        verified_action_execution_ids = tuple(
            record.action_execution_id
            for record in self._store.list(ActionExecutionRecord)
        )
        verified_reconciliation_ids = tuple(
            record.reconciliation_id
            for record in self._store.list(ReconciliationRecord)
        )

        for case_id in verified_case_ids:
            self._inspect_case_detail(case_id)
        for recommendation_id in verified_recommendation_ids:
            self._inspect_assistant_context("recommendation", recommendation_id)
        for approval_decision_id in verified_approval_decision_ids:
            self._inspect_assistant_context("approval_decision", approval_decision_id)
        for action_execution_id in verified_action_execution_ids:
            self._inspect_assistant_context("action_execution", action_execution_id)
        for reconciliation_id in verified_reconciliation_ids:
            self._inspect_assistant_context("reconciliation", reconciliation_id)
        self._inspect_reconciliation_status()
        startup = self.describe_startup_status()
        readiness_aggregates = self.inspect_readiness_aggregates()
        readiness_status = self._derive_readiness_status(
            startup_ready=startup.startup_ready,
            reconciliation_lifecycle_counts=readiness_aggregates.reconciliation_lifecycle_counts,
        )

        return self._restore_drill_snapshot_factory(
            read_only=True,
            drill_passed=readiness_status == "ready",
            verified_case_ids=verified_case_ids,
            verified_approval_decision_ids=verified_approval_decision_ids,
            verified_action_execution_ids=verified_action_execution_ids,
            verified_reconciliation_ids=verified_reconciliation_ids,
        )

    def _list_authoritative_record_chain_records(
        self,
    ) -> dict[str, tuple[ControlPlaneRecord, ...]]:
        authoritative_records: dict[str, tuple[ControlPlaneRecord, ...]] = {}
        authoritative_subject_ids_by_family: dict[str, set[str]] = {}
        persisted_records_by_family: dict[str, tuple[ControlPlaneRecord, ...]] = {}
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            persisted_records_by_family[family] = tuple(self._store.list(record_type))
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            persisted_records = persisted_records_by_family[family]
            if record_type is LifecycleTransitionRecord:
                continue
            authoritative_subject_ids_by_family[family] = {
                getattr(record, self._authoritative_primary_id_field_by_family[family])
                for record in persisted_records
            }
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            persisted_records = persisted_records_by_family[family]
            if record_type is LifecycleTransitionRecord:
                for record in persisted_records:
                    subject_ids = authoritative_subject_ids_by_family.get(
                        record.subject_record_family
                    )
                    if subject_ids is None:
                        raise ValueError(
                            "lifecycle transition "
                            f"{record.transition_id!r} references unsupported "
                            f"subject_record_family {record.subject_record_family!r}"
                        )
                    if record.subject_record_id not in subject_ids:
                        raise ValueError(
                            "missing "
                            f"{record.subject_record_family} record "
                            f"{record.subject_record_id!r} required by lifecycle "
                            f"transition {record.transition_id!r}"
                        )
                authoritative_records[family] = persisted_records
                continue
            authoritative_records[family] = persisted_records
        return authoritative_records

    def _synthesize_missing_lifecycle_transition_records(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        backup_created_at: datetime | None,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        synthesized_transitions = list(
            record
            for record in records_by_family.get("lifecycle_transition", ())
            if isinstance(record, LifecycleTransitionRecord)
        )
        covered_subjects = {
            (record.subject_record_family, record.subject_record_id)
            for record in synthesized_transitions
        }
        pending_subject_records: list[ControlPlaneRecord] = []
        for record_type in self._authoritative_record_chain_record_types:
            if record_type is LifecycleTransitionRecord:
                continue
            for record in records_by_family.get(record_type.record_family, ()):
                subject_key = (record.record_family, record.record_id)
                if subject_key in covered_subjects:
                    continue
                pending_subject_records.append(record)
                covered_subjects.add(subject_key)
        fallback_anchor = (
            backup_created_at
            if backup_created_at is not None
            else _LEGACY_RESTORE_FALLBACK_TRANSITION_ANCHOR
        )
        pending_count = len(pending_subject_records)
        for index, record in enumerate(pending_subject_records):
            fallback_transitioned_at = fallback_anchor - timedelta(
                microseconds=pending_count - index
            )
            synthesized_transition = self._synthesize_lifecycle_transition_record(
                record,
                fallback_transitioned_at,
            )
            if synthesized_transition is None:
                continue
            synthesized_transitions.append(synthesized_transition)
        synthesized_transitions.sort(
            key=lambda transition: (
                transition.transitioned_at,
                transition.transition_id,
            )
        )
        return tuple(synthesized_transitions)

    def require_empty_authoritative_restore_target(self) -> None:
        authoritative_subject_families = {
            record_type.record_family
            for record_type in self._authoritative_record_chain_record_types
            if record_type is not LifecycleTransitionRecord
        }
        populated_families: list[str] = []
        for record_type in self._authoritative_record_chain_record_types:
            family = record_type.record_family
            persisted_records = tuple(self._store.list(record_type))
            if record_type is LifecycleTransitionRecord:
                persisted_records = tuple(
                    record
                    for record in persisted_records
                    if record.subject_record_family in authoritative_subject_families
                )
            if persisted_records:
                populated_families.append(family)
        if populated_families:
            raise ValueError(
                "authoritative restore target must be empty before restore; found existing "
                f"records for {', '.join(populated_families)}"
            )

    def validate_authoritative_record_chain_restore(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        require_lifecycle_transition_history: bool = True,
        restored_record_counts: Mapping[str, int] | None = None,
    ) -> None:
        def duplicate_restore_count_suffix(family: str) -> str:
            if restored_record_counts is None:
                return ""
            return (
                "; restored_record_counts"
                f"[{family!r}]={restored_record_counts.get(family)!r}"
            )

        analytic_signal_records = tuple(
            record
            for record in records_by_family.get("analytic_signal", ())
            if isinstance(record, AnalyticSignalRecord)
        )
        alert_records = tuple(
            record
            for record in records_by_family.get("alert", ())
            if isinstance(record, AlertRecord)
        )
        evidence_record_family = tuple(
            record
            for record in records_by_family.get("evidence", ())
            if isinstance(record, EvidenceRecord)
        )
        observation_records = tuple(
            record
            for record in records_by_family.get("observation", ())
            if isinstance(record, ObservationRecord)
        )
        lead_records = tuple(
            record
            for record in records_by_family.get("lead", ())
            if isinstance(record, LeadRecord)
        )
        case_records = tuple(
            record
            for record in records_by_family.get("case", ())
            if isinstance(record, CaseRecord)
        )
        recommendation_records = tuple(
            record
            for record in records_by_family.get("recommendation", ())
            if isinstance(record, RecommendationRecord)
        )
        lifecycle_transition_records = tuple(
            record
            for record in records_by_family.get("lifecycle_transition", ())
            if isinstance(record, LifecycleTransitionRecord)
        )
        approval_decision_records = tuple(
            record
            for record in records_by_family.get("approval_decision", ())
            if isinstance(record, ApprovalDecisionRecord)
        )
        action_request_records = tuple(
            record
            for record in records_by_family.get("action_request", ())
            if isinstance(record, ActionRequestRecord)
        )
        action_execution_records = tuple(
            record
            for record in records_by_family.get("action_execution", ())
            if isinstance(record, ActionExecutionRecord)
        )
        hunt_records = tuple(
            record
            for record in records_by_family.get("hunt", ())
            if isinstance(record, HuntRecord)
        )
        hunt_run_records = tuple(
            record
            for record in records_by_family.get("hunt_run", ())
            if isinstance(record, HuntRunRecord)
        )
        ai_trace_records = tuple(
            record
            for record in records_by_family.get("ai_trace", ())
            if isinstance(record, AITraceRecord)
        )
        reconciliations = tuple(
            record
            for record in records_by_family.get("reconciliation", ())
            if isinstance(record, ReconciliationRecord)
        )
        for family, records in (
            ("analytic_signal", analytic_signal_records),
            ("alert", alert_records),
            ("evidence", evidence_record_family),
            ("observation", observation_records),
            ("lead", lead_records),
            ("case", case_records),
            ("recommendation", recommendation_records),
            ("lifecycle_transition", lifecycle_transition_records),
            ("approval_decision", approval_decision_records),
            ("action_request", action_request_records),
            ("action_execution", action_execution_records),
            ("hunt", hunt_records),
            ("hunt_run", hunt_run_records),
            ("ai_trace", ai_trace_records),
            ("reconciliation", reconciliations),
        ):
            duplicates = self._find_duplicate_strings(
                tuple(
                    getattr(record, self._authoritative_primary_id_field_by_family[family])
                    for record in records
                )
            )
            if duplicates:
                raise ValueError(
                    "restore payload contains duplicate "
                    f"{family} identifiers {duplicates!r}"
                    f"{duplicate_restore_count_suffix(family)}"
                )
        duplicate_execution_run_ids = self._find_duplicate_strings(
            tuple(
                record.execution_run_id
                for record in action_execution_records
                if record.execution_run_id is not None
            )
        )
        if duplicate_execution_run_ids:
            raise ValueError(
                "restore payload contains duplicate action_execution "
                f"execution_run_id values {duplicate_execution_run_ids!r}"
                f"{duplicate_restore_count_suffix('action_execution')}"
            )

        analytic_signals = {
            record.analytic_signal_id: record for record in analytic_signal_records
        }
        alerts = {record.alert_id: record for record in alert_records}
        evidence_records = {
            record.evidence_id: record for record in evidence_record_family
        }
        observations = {
            record.observation_id: record for record in observation_records
        }
        leads = {record.lead_id: record for record in lead_records}
        cases = {record.case_id: record for record in case_records}
        recommendations = {
            record.recommendation_id: record for record in recommendation_records
        }
        approval_decisions = {
            record.approval_decision_id: record
            for record in approval_decision_records
        }
        action_requests = {
            record.action_request_id: record for record in action_request_records
        }
        action_executions = {
            record.action_execution_id: record for record in action_execution_records
        }
        hunts = {record.hunt_id: record for record in hunt_records}
        hunt_runs = {record.hunt_run_id: record for record in hunt_run_records}
        ai_traces = {record.ai_trace_id: record for record in ai_trace_records}
        action_executions_by_run_id = {
            record.execution_run_id: record
            for record in action_execution_records
            if record.execution_run_id is not None
        }
        reconciliations_by_id = {
            record.reconciliation_id: record for record in reconciliations
        }
        authoritative_subject_ids_by_family: dict[str, set[str]] = {
            "analytic_signal": set(analytic_signals),
            "alert": set(alerts),
            "evidence": set(evidence_records),
            "observation": set(observations),
            "lead": set(leads),
            "case": set(cases),
            "recommendation": set(recommendations),
            "approval_decision": set(approval_decisions),
            "action_request": set(action_requests),
            "action_execution": set(action_executions),
            "hunt": set(hunts),
            "hunt_run": set(hunt_runs),
            "ai_trace": set(ai_traces),
            "reconciliation": set(reconciliations_by_id),
        }
        authoritative_subject_records_by_family: dict[str, Mapping[str, ControlPlaneRecord]] = {
            "analytic_signal": analytic_signals,
            "alert": alerts,
            "evidence": evidence_records,
            "observation": observations,
            "lead": leads,
            "case": cases,
            "recommendation": recommendations,
            "approval_decision": approval_decisions,
            "action_request": action_requests,
            "action_execution": action_executions,
            "hunt": hunts,
            "hunt_run": hunt_runs,
            "ai_trace": ai_traces,
            "reconciliation": reconciliations_by_id,
        }

        for alert in alerts.values():
            if alert.analytic_signal_id and alert.analytic_signal_id not in analytic_signals:
                raise ValueError(
                    f"missing analytic_signal record {alert.analytic_signal_id!r} required by alert "
                    f"{alert.alert_id!r}"
                )
            if (
                alert.analytic_signal_id
                and alert.alert_id
                not in analytic_signals[alert.analytic_signal_id].alert_ids
            ):
                raise ValueError(
                    f"alert {alert.alert_id!r} does not match analytic signal binding "
                    f"{alert.analytic_signal_id!r}"
                )
            if alert.case_id and alert.case_id not in cases:
                raise ValueError(
                    f"missing case record {alert.case_id!r} required by alert {alert.alert_id!r}"
                )
            if alert.case_id and cases[alert.case_id].alert_id != alert.alert_id:
                raise ValueError(
                    f"alert {alert.alert_id!r} does not match case binding {alert.case_id!r}"
                )

        for analytic_signal in analytic_signals.values():
            for alert_id in analytic_signal.alert_ids:
                if alert_id not in alerts:
                    raise ValueError(
                        f"missing alert record {alert_id!r} required by analytic signal "
                        f"{analytic_signal.analytic_signal_id!r}"
                    )
                if alerts[alert_id].analytic_signal_id != analytic_signal.analytic_signal_id:
                    raise ValueError(
                        f"analytic signal {analytic_signal.analytic_signal_id!r} does not match "
                        f"alert binding {alert_id!r}"
                    )
            for case_id in analytic_signal.case_ids:
                if case_id not in cases:
                    raise ValueError(
                        f"missing case record {case_id!r} required by analytic signal "
                        f"{analytic_signal.analytic_signal_id!r}"
                    )

        for evidence in evidence_records.values():
            if evidence.alert_id and evidence.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {evidence.alert_id!r} required by evidence "
                    f"{evidence.evidence_id!r}"
                )
            if evidence.case_id and evidence.case_id not in cases:
                raise ValueError(
                    f"missing case record {evidence.case_id!r} required by evidence "
                    f"{evidence.evidence_id!r}"
                )

        for observation in observations.values():
            if observation.hunt_id and observation.hunt_id not in hunts:
                raise ValueError(
                    f"missing hunt record {observation.hunt_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.hunt_run_id and observation.hunt_run_id not in hunt_runs:
                raise ValueError(
                    f"missing hunt_run record {observation.hunt_run_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.alert_id and observation.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {observation.alert_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            if observation.case_id and observation.case_id not in cases:
                raise ValueError(
                    f"missing case record {observation.case_id!r} required by observation "
                    f"{observation.observation_id!r}"
                )
            for evidence_id in observation.supporting_evidence_ids:
                if evidence_id not in evidence_records:
                    raise ValueError(
                        f"missing evidence record {evidence_id!r} required by observation "
                        f"{observation.observation_id!r}"
                    )

        for lead in leads.values():
            if lead.observation_id and lead.observation_id not in observations:
                raise ValueError(
                    f"missing observation record {lead.observation_id!r} required by lead "
                    f"{lead.lead_id!r}"
                )
            if lead.hunt_run_id and lead.hunt_run_id not in hunt_runs:
                raise ValueError(
                    f"missing hunt_run record {lead.hunt_run_id!r} required by lead "
                    f"{lead.lead_id!r}"
                )
            if lead.alert_id and lead.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {lead.alert_id!r} required by lead {lead.lead_id!r}"
                )
            if lead.case_id and lead.case_id not in cases:
                raise ValueError(
                    f"missing case record {lead.case_id!r} required by lead {lead.lead_id!r}"
                )

        for case in cases.values():
            if case.alert_id and case.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {case.alert_id!r} required by case {case.case_id!r}"
                )
            if case.alert_id and alerts[case.alert_id].case_id != case.case_id:
                raise ValueError(
                    f"case {case.case_id!r} does not match alert binding {case.alert_id!r}"
                )
            for evidence_id in case.evidence_ids:
                if evidence_id not in evidence_records:
                    raise ValueError(
                        f"missing evidence record {evidence_id!r} required by case {case.case_id!r}"
                    )

        for recommendation in recommendations.values():
            if recommendation.lead_id and recommendation.lead_id not in leads:
                raise ValueError(
                    "missing lead record "
                    f"{recommendation.lead_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.hunt_run_id and recommendation.hunt_run_id not in hunt_runs:
                raise ValueError(
                    "missing hunt_run record "
                    f"{recommendation.hunt_run_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.alert_id and recommendation.alert_id not in alerts:
                raise ValueError(
                    "missing alert record "
                    f"{recommendation.alert_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.case_id and recommendation.case_id not in cases:
                raise ValueError(
                    "missing case record "
                    f"{recommendation.case_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )
            if recommendation.ai_trace_id and recommendation.ai_trace_id not in ai_traces:
                raise ValueError(
                    "missing ai_trace record "
                    f"{recommendation.ai_trace_id!r} required by recommendation "
                    f"{recommendation.recommendation_id!r}"
                )

        for hunt in hunts.values():
            if hunt.alert_id and hunt.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {hunt.alert_id!r} required by hunt {hunt.hunt_id!r}"
                )
            if hunt.case_id and hunt.case_id not in cases:
                raise ValueError(
                    f"missing case record {hunt.case_id!r} required by hunt {hunt.hunt_id!r}"
                )

        for hunt_run in hunt_runs.values():
            if hunt_run.hunt_id not in hunts:
                raise ValueError(
                    f"missing hunt record {hunt_run.hunt_id!r} required by hunt_run "
                    f"{hunt_run.hunt_run_id!r}"
                )

        for approval_decision in approval_decisions.values():
            action_request = action_requests.get(approval_decision.action_request_id)
            if action_request is None:
                raise ValueError(
                    f"missing action_request record {approval_decision.action_request_id!r} required by "
                    f"approval decision {approval_decision.approval_decision_id!r}"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"approval decision {approval_decision.approval_decision_id!r} does not match "
                    "action request target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"approval decision {approval_decision.approval_decision_id!r} does not match "
                    "action request payload binding"
                )

        for action_request in action_requests.values():
            if action_request.case_id and action_request.case_id not in cases:
                raise ValueError(
                    f"missing case record {action_request.case_id!r} required by action request "
                    f"{action_request.action_request_id!r}"
                )
            if action_request.alert_id and action_request.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {action_request.alert_id!r} required by action request "
                    f"{action_request.action_request_id!r}"
                )
            if (
                action_request.approval_decision_id
                and action_request.approval_decision_id not in approval_decisions
            ):
                raise ValueError(
                    f"missing approval_decision record {action_request.approval_decision_id!r} "
                    f"required by action request {action_request.action_request_id!r}"
                )
            approval_decision = approval_decisions.get(action_request.approval_decision_id)
            if approval_decision is None:
                continue
            if approval_decision.action_request_id != action_request.action_request_id:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision binding"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} does not match approval "
                    "decision payload binding"
                )

        for action_execution in action_executions.values():
            action_request = action_requests.get(action_execution.action_request_id)
            if action_request is None:
                raise ValueError(
                    f"missing action_request record {action_execution.action_request_id!r} required by "
                    f"action execution {action_execution.action_execution_id!r}"
                )
            if action_execution.approval_decision_id not in approval_decisions:
                raise ValueError(
                    f"missing approval_decision record {action_execution.approval_decision_id!r} "
                    f"required by action execution {action_execution.action_execution_id!r}"
                )
            approval_decision = approval_decisions[action_execution.approval_decision_id]
            if action_request.approval_decision_id != action_execution.approval_decision_id:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    f"request approval binding"
                )
            if approval_decision.action_request_id != action_request.action_request_id:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision binding"
                )
            if action_execution.idempotency_key != action_request.idempotency_key:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request idempotency binding"
                )
            if action_execution.target_scope != action_request.target_scope:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request target binding"
                )
            if action_execution.approved_payload != action_request.requested_payload:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request approved payload binding"
                )
            if action_execution.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request payload binding"
                )
            policy_evaluation = action_request.policy_evaluation
            if (
                policy_evaluation.get("execution_surface_type")
                != action_execution.execution_surface_type
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request execution surface binding"
                )
            if (
                policy_evaluation.get("execution_surface_id")
                != action_execution.execution_surface_id
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request execution surface binding"
                )
            if approval_decision.target_snapshot != action_request.target_scope:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision target binding"
                )
            if approval_decision.payload_hash != action_request.payload_hash:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision payload binding"
                )
            if approval_decision.approved_expires_at != action_request.expires_at:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match approval "
                    "decision expiry binding"
                )
            if action_execution.expires_at != action_request.expires_at:
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} does not match action "
                    "request expiry binding"
                )
            if (
                approval_decision.approved_expires_at is not None
                and action_execution.delegated_at > approval_decision.approved_expires_at
            ):
                raise ValueError(
                    f"action execution {action_execution.action_execution_id!r} exceeds approval "
                    "expiry binding"
                )

        for reconciliation in reconciliations:
            subject_action_execution_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            )
            subject_execution_run_ids = {
                action_executions[action_execution_id].execution_run_id
                for action_execution_id in subject_action_execution_ids
                if action_execution_id in action_executions
                and action_executions[action_execution_id].execution_run_id is not None
            }
            if reconciliation.alert_id and reconciliation.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {reconciliation.alert_id!r} required by reconciliation "
                    f"{reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.analytic_signal_id
                and reconciliation.analytic_signal_id not in analytic_signals
            ):
                raise ValueError(
                    f"missing analytic_signal record {reconciliation.analytic_signal_id!r} required by "
                    f"reconciliation {reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.execution_run_id
                and reconciliation.execution_run_id not in action_executions_by_run_id
            ):
                raise ValueError(
                    f"missing action execution run {reconciliation.execution_run_id!r} required by "
                    f"reconciliation {reconciliation.reconciliation_id!r}"
                )
            if (
                reconciliation.execution_run_id is not None
                and subject_execution_run_ids
                and reconciliation.execution_run_id not in subject_execution_run_ids
            ):
                raise ValueError(
                    f"reconciliation {reconciliation.reconciliation_id!r} does not match its action "
                    "execution run binding"
                )
            for linked_execution_run_id in reconciliation.linked_execution_run_ids:
                if linked_execution_run_id not in action_executions_by_run_id:
                    raise ValueError(
                        f"missing action execution run {linked_execution_run_id!r} required by "
                        f"reconciliation {reconciliation.reconciliation_id!r}"
                    )
                if (
                    subject_execution_run_ids
                    and linked_execution_run_id not in subject_execution_run_ids
                ):
                    raise ValueError(
                        f"reconciliation {reconciliation.reconciliation_id!r} does not match its linked "
                        "action execution runs"
                    )
            for field_name, known_ids in (
                ("analytic_signal_ids", analytic_signals),
                ("alert_ids", alerts),
                ("case_ids", cases),
                ("evidence_ids", evidence_records),
                ("approval_decision_ids", approval_decisions),
                ("action_request_ids", action_requests),
                ("action_execution_ids", action_executions),
            ):
                for linked_id in self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    field_name,
                ):
                    if linked_id not in known_ids:
                        singular_name = (
                            field_name[:-4]
                            if field_name.endswith("_ids")
                            else field_name
                        )
                        raise ValueError(
                            f"missing {singular_name} record {linked_id!r} required by reconciliation "
                            f"{reconciliation.reconciliation_id!r}"
                        )

        lifecycle_transitions_by_subject: dict[
            tuple[str, str], list[LifecycleTransitionRecord]
        ] = {}
        for transition in lifecycle_transition_records:
            subject_ids = authoritative_subject_ids_by_family.get(
                transition.subject_record_family
            )
            if subject_ids is None:
                raise ValueError(
                    "lifecycle transition "
                    f"{transition.transition_id!r} references unsupported subject_record_family "
                    f"{transition.subject_record_family!r}"
                )
            if transition.subject_record_id not in subject_ids:
                raise ValueError(
                    "missing "
                    f"{transition.subject_record_family} record {transition.subject_record_id!r} "
                    f"required by lifecycle transition {transition.transition_id!r}"
                )
            _validate_lifecycle_state(transition)
            lifecycle_transitions_by_subject.setdefault(
                (
                    transition.subject_record_family,
                    transition.subject_record_id,
                ),
                [],
            ).append(transition)

        if require_lifecycle_transition_history:
            for subject_family, subject_records in authoritative_subject_records_by_family.items():
                for subject_id, subject_record in subject_records.items():
                    subject_lifecycle_state = getattr(
                        subject_record,
                        "lifecycle_state",
                        None,
                    )
                    if (
                        not isinstance(subject_lifecycle_state, str)
                        or not subject_lifecycle_state.strip()
                    ):
                        continue
                    if (subject_family, subject_id) not in lifecycle_transitions_by_subject:
                        raise ValueError(
                            f"missing lifecycle transition history for {subject_family} "
                            f"record {subject_id!r}"
                        )

        for (subject_family, subject_id), subject_transitions in (
            lifecycle_transitions_by_subject.items()
        ):
            ordered_transitions = sorted(
                subject_transitions,
                key=lambda transition: (
                    transition.transitioned_at,
                    transition.transition_id,
                ),
            )
            first_transition = ordered_transitions[0]
            if first_transition.previous_lifecycle_state is not None:
                raise ValueError(
                    "lifecycle transition chain for "
                    f"{subject_family} record {subject_id!r} must start with a "
                    "creation anchor: "
                    f"{first_transition.transition_id!r} has previous_lifecycle_state "
                    f"{first_transition.previous_lifecycle_state!r}"
                )
            prior_transition: LifecycleTransitionRecord | None = None
            for transition in ordered_transitions:
                if (
                    prior_transition is not None
                    and transition.previous_lifecycle_state
                    != prior_transition.lifecycle_state
                ):
                    raise ValueError(
                        "lifecycle transition chain for "
                        f"{subject_family} record {subject_id!r} is inconsistent: "
                        f"{transition.transition_id!r} previous_lifecycle_state "
                        f"{transition.previous_lifecycle_state!r} does not match prior "
                        f"lifecycle_state {prior_transition.lifecycle_state!r}"
                    )
                if transition.previous_lifecycle_state == transition.lifecycle_state:
                    raise ValueError(
                        "lifecycle transition chain for "
                        f"{subject_family} record {subject_id!r} contains no-op transition: "
                        f"{transition.transition_id!r} previous_lifecycle_state "
                        f"{transition.previous_lifecycle_state!r} matches lifecycle_state "
                        f"{transition.lifecycle_state!r}"
                    )
                prior_transition = transition

            latest_transition = ordered_transitions[-1]
            subject_record = authoritative_subject_records_by_family[subject_family][
                subject_id
            ]
            subject_lifecycle_state = getattr(subject_record, "lifecycle_state", None)
            if subject_lifecycle_state != latest_transition.lifecycle_state:
                raise ValueError(
                    f"{subject_family} record {subject_id!r} lifecycle_state "
                    f"{subject_lifecycle_state!r} does not match latest lifecycle transition "
                    f"{latest_transition.transition_id!r} state "
                    f"{latest_transition.lifecycle_state!r}"
                )
