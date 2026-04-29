from __future__ import annotations

from collections import Counter
from typing import Any, Callable, Iterable

from .config import RuntimeConfig
from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    CaseRecord,
    ReconciliationRecord,
)
from .readiness_contracts import ReadinessDiagnosticsAggregates
from .runtime_boundary import ControlPlaneStore, RuntimeBoundaryService, _is_missing_runtime_binding


class _ReadinessHealthProjection:
    def __init__(
        self,
        *,
        config: RuntimeConfig,
        store: ControlPlaneStore,
        runtime_boundary_service: RuntimeBoundaryService,
        startup_status_snapshot_factory: Callable[..., Any],
        readiness_diagnostics_snapshot_factory: Callable[..., Any],
        redacted_reconciliation_payload: Callable[[ReconciliationRecord], dict[str, object]],
        collect_readiness_review_snapshots: Callable[
            [ReadinessDiagnosticsAggregates], list[dict[str, object]]
        ],
        build_readiness_review_path_health: Callable[
            [ReadinessDiagnosticsAggregates, list[dict[str, object]]], dict[str, object]
        ],
        build_readiness_source_health: Callable[
            [ReadinessDiagnosticsAggregates, list[dict[str, object]]], dict[str, object]
        ],
        build_readiness_automation_substrate_health: Callable[
            [ReadinessDiagnosticsAggregates, list[dict[str, object]]], dict[str, object]
        ],
        build_optional_extension_operability: Callable[
            [ReadinessDiagnosticsAggregates, list[dict[str, object]]], dict[str, object]
        ],
        build_shutdown_status_snapshot: Callable[..., Any],
        derive_readiness_status: Callable[..., str],
    ) -> None:
        self._config = config
        self._store = store
        self._runtime_boundary_service = runtime_boundary_service
        self._startup_status_snapshot_factory = startup_status_snapshot_factory
        self._readiness_diagnostics_snapshot_factory = (
            readiness_diagnostics_snapshot_factory
        )
        self._redacted_reconciliation_payload = redacted_reconciliation_payload
        self._collect_readiness_review_snapshots = (
            collect_readiness_review_snapshots
        )
        self._build_readiness_review_path_health = (
            build_readiness_review_path_health
        )
        self._build_readiness_source_health = build_readiness_source_health
        self._build_readiness_automation_substrate_health = (
            build_readiness_automation_substrate_health
        )
        self._build_optional_extension_operability = (
            build_optional_extension_operability
        )
        self._build_shutdown_status_snapshot = build_shutdown_status_snapshot
        self._derive_readiness_status = derive_readiness_status

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
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER",
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
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER": (
                self._config.protected_surface_reviewed_identity_provider
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
            readiness_review_snapshots = self._collect_readiness_review_snapshots(
                readiness_aggregates
            )
            review_path_health = self._build_readiness_review_path_health(
                readiness_aggregates,
                readiness_review_snapshots,
            )
            source_health = self._build_readiness_source_health(
                readiness_aggregates,
                readiness_review_snapshots,
            )
            automation_substrate_health = (
                self._build_readiness_automation_substrate_health(
                    readiness_aggregates,
                    readiness_review_snapshots,
                )
            )
            optional_extensions = self._build_optional_extension_operability(
                readiness_aggregates,
                readiness_review_snapshots,
            )
            control_plane_change_authority_freeze = (
                self._control_plane_change_authority_freeze_status()
            )

        shutdown = self._build_shutdown_status_snapshot(
            open_case_ids=readiness_aggregates.open_case_ids,
            active_action_request_ids=readiness_aggregates.active_action_request_ids,
            active_action_execution_ids=readiness_aggregates.active_action_execution_ids,
            unresolved_reconciliation_ids=readiness_aggregates.unresolved_reconciliation_ids,
        )

        status = self._derive_readiness_status(
            startup_ready=startup.startup_ready,
            reconciliation_lifecycle_counts=readiness_aggregates.reconciliation_lifecycle_counts,
            review_path_health_overall_state=review_path_health["overall_state"],
            control_plane_authority_frozen=(
                control_plane_change_authority_freeze["state"] == "frozen"
            ),
        )
        operator_health = self._build_operator_health_signal(
            readiness_status=status,
            startup_ready=startup.startup_ready,
            shutdown_ready=shutdown.shutdown_ready,
            readiness_aggregates=readiness_aggregates,
            review_path_health=review_path_health,
            source_health=source_health,
            automation_substrate_health=automation_substrate_health,
            optional_extensions=optional_extensions,
            control_plane_change_authority_freeze=control_plane_change_authority_freeze,
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
            "review_path_health": review_path_health,
            "source_health": source_health,
            "automation_substrate_health": automation_substrate_health,
            "optional_extensions": optional_extensions,
            "control_plane_change_authority_freeze": (
                control_plane_change_authority_freeze
            ),
            "operator_health": operator_health,
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

    def _build_operator_health_signal(
        self,
        *,
        readiness_status: str,
        startup_ready: bool,
        shutdown_ready: bool,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
        review_path_health: dict[str, object],
        source_health: dict[str, object],
        automation_substrate_health: dict[str, object],
        optional_extensions: dict[str, object],
        control_plane_change_authority_freeze: dict[str, object],
    ) -> dict[str, object]:
        subordinate_context = {
            "source_health": self._operator_subordinate_context_entry(
                state=str(source_health.get("overall_state", "unknown")),
                tracked_count=int(source_health.get("tracked_sources", 0)),
            ),
            "automation_substrate_health": self._operator_subordinate_context_entry(
                state=str(automation_substrate_health.get("overall_state", "unknown")),
                tracked_count=int(
                    automation_substrate_health.get("tracked_surfaces", 0)
                ),
            ),
            "optional_extensions": {
                **self._operator_subordinate_context_entry(
                    state=str(optional_extensions.get("overall_state", "unknown")),
                    tracked_count=int(optional_extensions.get("tracked_extensions", 0)),
                ),
                "degraded_extensions": tuple(
                    extension_name
                    for extension_name, extension in sorted(
                        self._operator_extension_entries(optional_extensions).items()
                    )
                    if extension.get("readiness") == "degraded"
                ),
            },
        }
        subordinate_state = self._operator_worst_state(
            entry["state"] for entry in subordinate_context.values()
        )
        mainline_state = readiness_status
        overall_state = self._operator_worst_state((mainline_state, subordinate_state))

        return {
            "contract": "phase49_commercial_operator_health",
            "overall_state": overall_state,
            "authority_source": "aegisops_control_plane_records",
            "subordinate_signal_policy": "visibility_only",
            "subordinate_signals_authoritative": False,
            "mainline": {
                "readiness_status": readiness_status,
                "startup_ready": startup_ready,
                "shutdown_ready": shutdown_ready,
                "review_path_state": review_path_health.get("overall_state"),
                "authority_freeze_state": control_plane_change_authority_freeze.get(
                    "state"
                ),
                "open_case_count": len(readiness_aggregates.open_case_ids),
                "active_action_request_count": len(
                    readiness_aggregates.active_action_request_ids
                ),
                "active_action_execution_count": len(
                    readiness_aggregates.active_action_execution_ids
                ),
                "unresolved_reconciliation_count": len(
                    readiness_aggregates.unresolved_reconciliation_ids
                ),
            },
            "subordinate_context": subordinate_context,
            "commercial_claims": (),
        }

    @staticmethod
    def _operator_subordinate_context_entry(
        *,
        state: str,
        tracked_count: int,
    ) -> dict[str, object]:
        return {
            "state": state,
            "tracked_count": tracked_count,
            "authority_mode": "non_authoritative",
            "mainline_dependency": "non_blocking",
        }

    @staticmethod
    def _operator_extension_entries(
        optional_extensions: dict[str, object],
    ) -> dict[str, dict[str, object]]:
        extensions = optional_extensions.get("extensions")
        if not isinstance(extensions, dict):
            return {}
        return {
            str(extension_name): dict(extension)
            for extension_name, extension in extensions.items()
            if isinstance(extension, dict)
        }

    @staticmethod
    def _operator_worst_state(states: Iterable[object]) -> str:
        severity = {
            "ready": 0,
            "healthy": 0,
            "not_applicable": 0,
            "delayed": 1,
            "degraded": 2,
            "stale": 2,
            "failed": 3,
            "failing_closed": 3,
            "frozen": 3,
            "unknown": 3,
        }
        normalized_states = [
            str(state)
            for state in states
            if isinstance(state, str) and state.strip()
        ]
        if not normalized_states:
            return "unknown"
        return max(
            normalized_states,
            key=lambda state: severity.get(state, severity["unknown"]),
        )

    def _control_plane_change_authority_freeze_status(self) -> dict[str, object]:
        change_state = self._config.control_plane_change_state.strip()
        evidence_id = self._config.control_plane_change_evidence_id.strip()
        normalized_state = change_state or "unknown"
        is_verified = normalized_state in {"verified_current", "verified_safe"}
        return {
            "state": "verified" if is_verified else "frozen",
            "change_state": normalized_state,
            "evidence_id": evidence_id or None,
            "authority_sensitive_progression_allowed": is_verified,
            "reason": (
                "control_plane_state_verified"
                if is_verified
                else "control_plane_upgrade_or_rollback_verification_incomplete"
            ),
        }

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
            terminal_review_outcome_action_request_ids=tuple(
                record.action_request_id
                for record in action_requests
                if record.lifecycle_state
                in {
                    "completed",
                    "failed",
                    "rejected",
                    "expired",
                    "canceled",
                    "superseded",
                }
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
            terminal_action_execution_ids=tuple(
                record.action_execution_id
                for record in action_executions
                if record.lifecycle_state
                in {
                    "succeeded",
                    "failed",
                    "canceled",
                    "superseded",
                }
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
