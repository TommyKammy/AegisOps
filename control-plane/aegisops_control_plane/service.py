from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, fields
from datetime import datetime, timezone
import uuid
from typing import Mapping, Protocol, Type, TypeVar

from .adapters.n8n import N8NReconciliationAdapter
from .adapters.postgres import PostgresControlPlaneStore
from .config import RuntimeConfig
from .models import (
    AITraceRecord,
    ActionRequestRecord,
    AnalyticSignalAdmission,
    AnalyticSignalRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    NativeDetectionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


class ControlPlaneStore(Protocol):
    dsn: str
    persistence_mode: str

    def save(self, record: RecordT) -> RecordT:
        ...

    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        ...

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...


class NativeDetectionRecordAdapter(Protocol):
    substrate_key: str

    def build_analytic_signal_admission(
        self,
        record: NativeDetectionRecord,
    ) -> AnalyticSignalAdmission:
        ...


@dataclass(frozen=True)
class RuntimeSnapshot:
    service_name: str
    bind_host: str
    bind_port: int
    postgres_dsn: str
    persistence_mode: str
    opensearch_url: str
    n8n_base_url: str
    ownership_boundary: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FindingAlertIngestResult:
    alert: AlertRecord
    reconciliation: ReconciliationRecord
    disposition: str


@dataclass(frozen=True)
class RecordInspectionSnapshot:
    read_only: bool
    record_family: str
    total_records: int
    records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "record_family": self.record_family,
                "total_records": self.total_records,
                "records": self.records,
            }
        )


@dataclass(frozen=True)
class ReconciliationStatusSnapshot:
    read_only: bool
    total_records: int
    latest_compared_at: datetime | None
    by_lifecycle_state: dict[str, int]
    by_ingest_disposition: dict[str, int]
    records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "total_records": self.total_records,
                "latest_compared_at": self.latest_compared_at,
                "by_lifecycle_state": self.by_lifecycle_state,
                "by_ingest_disposition": self.by_ingest_disposition,
                "records": self.records,
            }
        )


RECORD_TYPES_BY_FAMILY: dict[str, Type[ControlPlaneRecord]] = {
    record_type.record_family: record_type
    for record_type in (
        AlertRecord,
        AnalyticSignalRecord,
        CaseRecord,
        EvidenceRecord,
        ObservationRecord,
        LeadRecord,
        RecommendationRecord,
        ApprovalDecisionRecord,
        ActionRequestRecord,
        HuntRecord,
        HuntRunRecord,
        AITraceRecord,
        ReconciliationRecord,
    )
}


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _record_to_dict(record: ControlPlaneRecord) -> dict[str, object]:
    return {
        field.name: getattr(record, field.name)
        for field in fields(record)
    }


class AegisOpsControlPlaneService:
    """Minimal local runtime skeleton for the first control-plane service."""

    def __init__(
        self,
        config: RuntimeConfig,
        store: ControlPlaneStore | None = None,
    ) -> None:
        self._config = config
        self._store = store or PostgresControlPlaneStore(config.postgres_dsn)
        self._reconciliation = N8NReconciliationAdapter(config.n8n_base_url)

    def describe_runtime(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(
            service_name="aegisops-control-plane",
            bind_host=self._config.host,
            bind_port=self._config.port,
            postgres_dsn=self._store.dsn,
            persistence_mode=self._store.persistence_mode,
            opensearch_url=self._config.opensearch_url,
            n8n_base_url=self._reconciliation.base_url,
            ownership_boundary={
                "runtime_root": "control-plane/",
                "postgres_contract_root": "postgres/control-plane/",
                "native_detection_intake": "substrate-adapters/",
                "admitted_signal_model": "control-plane/analytic-signals",
                "execution_plane": "n8n/",
            },
        )

    def persist_record(self, record: RecordT) -> RecordT:
        return self._store.save(record)

    def get_record(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        return self._store.get(record_type, record_id)

    def inspect_records(self, record_family: str) -> RecordInspectionSnapshot:
        record_type = RECORD_TYPES_BY_FAMILY.get(record_family)
        if record_type is None:
            known_families = ", ".join(sorted(RECORD_TYPES_BY_FAMILY))
            raise ValueError(
                f"Unsupported control-plane record family {record_family!r}; "
                f"expected one of: {known_families}"
            )

        records = tuple(_record_to_dict(record) for record in self._store.list(record_type))
        return RecordInspectionSnapshot(
            read_only=True,
            record_family=record_family,
            total_records=len(records),
            records=records,
        )

    def inspect_reconciliation_status(self) -> ReconciliationStatusSnapshot:
        records = self._store.list(ReconciliationRecord)
        latest_compared_at = max(
            (record.compared_at for record in records),
            default=None,
        )
        by_lifecycle_state = dict(
            sorted(Counter(record.lifecycle_state for record in records).items())
        )
        by_ingest_disposition = dict(
            sorted(Counter(record.ingest_disposition for record in records).items())
        )
        return ReconciliationStatusSnapshot(
            read_only=True,
            total_records=len(records),
            latest_compared_at=latest_compared_at,
            by_lifecycle_state=by_lifecycle_state,
            by_ingest_disposition=by_ingest_disposition,
            records=tuple(_record_to_dict(record) for record in records),
        )

    @staticmethod
    def _require_aware_datetime(value: object, field_name: str) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")
        return value

    def ingest_finding_alert(
        self,
        *,
        finding_id: str,
        analytic_signal_id: str | None,
        substrate_detection_record_id: str | None = None,
        correlation_key: str,
        first_seen_at: datetime,
        last_seen_at: datetime,
        materially_new_work: bool = False,
    ) -> FindingAlertIngestResult:
        return self._ingest_analytic_signal_admission(
            AnalyticSignalAdmission(
                finding_id=finding_id,
                analytic_signal_id=analytic_signal_id,
                substrate_detection_record_id=substrate_detection_record_id,
                correlation_key=correlation_key,
                first_seen_at=first_seen_at,
                last_seen_at=last_seen_at,
                materially_new_work=materially_new_work,
            )
        )

    def ingest_native_detection_record(
        self,
        adapter: NativeDetectionRecordAdapter,
        record: NativeDetectionRecord,
    ) -> FindingAlertIngestResult:
        if record.substrate_key != adapter.substrate_key:
            raise ValueError(
                "native detection record substrate does not match adapter boundary "
                f"({record.substrate_key!r} != {adapter.substrate_key!r})"
            )
        admission = adapter.build_analytic_signal_admission(record)
        if admission.substrate_detection_record_id is None:
            admission = AnalyticSignalAdmission(
                finding_id=admission.finding_id,
                analytic_signal_id=admission.analytic_signal_id,
                substrate_detection_record_id=record.native_record_id,
                correlation_key=admission.correlation_key,
                first_seen_at=admission.first_seen_at,
                last_seen_at=admission.last_seen_at,
                materially_new_work=admission.materially_new_work,
            )
        return self._ingest_analytic_signal_admission(admission)

    def _ingest_analytic_signal_admission(
        self,
        admission: AnalyticSignalAdmission,
    ) -> FindingAlertIngestResult:
        finding_id = admission.finding_id
        analytic_signal_id = admission.analytic_signal_id
        substrate_detection_record_id = admission.substrate_detection_record_id
        correlation_key = admission.correlation_key
        first_seen_at = self._require_aware_datetime(
            admission.first_seen_at,
            "first_seen_at",
        )
        last_seen_at = self._require_aware_datetime(
            admission.last_seen_at,
            "last_seen_at",
        )
        if last_seen_at < first_seen_at:
            raise ValueError(
                "last_seen_at must be greater than or equal to first_seen_at"
            )
        materially_new_work = admission.materially_new_work

        existing_reconciliations = [
            record
            for record in self._store.list(ReconciliationRecord)
            if record.correlation_key == correlation_key and record.alert_id is not None
        ]
        latest_reconciliation = max(
            existing_reconciliations,
            key=lambda record: record.compared_at,
            default=None,
        )

        if latest_reconciliation is None:
            alert = self.persist_record(
                AlertRecord(
                    alert_id=self._next_identifier("alert"),
                    finding_id=finding_id,
                    analytic_signal_id=analytic_signal_id,
                    case_id=None,
                    lifecycle_state="new",
                )
            )
            disposition = "created"
            linked_finding_ids = (finding_id,)
            linked_signal_ids = (
                (analytic_signal_id,) if analytic_signal_id is not None else tuple()
            )
            linked_substrate_detection_ids = self._merge_linked_ids(
                (),
                substrate_detection_record_id,
            )
            persisted_first_seen = first_seen_at
            persisted_last_seen = last_seen_at
        else:
            alert = self._store.get(AlertRecord, latest_reconciliation.alert_id)
            if alert is None:
                raise LookupError(
                    f"Missing alert {latest_reconciliation.alert_id!r} for correlation key {correlation_key!r}"
                )
            existing_finding_ids = latest_reconciliation.subject_linkage.get("finding_ids")
            existing_signal_ids = latest_reconciliation.subject_linkage.get(
                "analytic_signal_ids"
            )
            existing_substrate_detection_ids = latest_reconciliation.subject_linkage.get(
                "substrate_detection_record_ids"
            )
            linked_finding_ids = self._merge_linked_ids(
                existing_finding_ids,
                finding_id,
            )
            linked_signal_ids = self._merge_linked_ids(
                existing_signal_ids,
                analytic_signal_id,
            )
            linked_substrate_detection_ids = self._merge_linked_ids(
                existing_substrate_detection_ids,
                substrate_detection_record_id,
            )
            persisted_first_seen = min(
                latest_reconciliation.first_seen_at or first_seen_at,
                first_seen_at,
            )
            persisted_last_seen = max(
                latest_reconciliation.last_seen_at or last_seen_at,
                last_seen_at,
            )
            already_linked = (
                self._linked_id_exists(existing_finding_ids, finding_id)
                and (
                    analytic_signal_id is None
                    or self._linked_id_exists(existing_signal_ids, analytic_signal_id)
                )
                and (
                    substrate_detection_record_id is None
                    or self._linked_id_exists(
                        existing_substrate_detection_ids,
                        substrate_detection_record_id,
                    )
                )
            )
            if materially_new_work:
                alert = self.persist_record(
                    AlertRecord(
                        alert_id=alert.alert_id,
                        finding_id=finding_id,
                        analytic_signal_id=analytic_signal_id,
                        case_id=alert.case_id,
                        lifecycle_state=alert.lifecycle_state,
                    )
                )
                disposition = "updated"
            elif already_linked:
                disposition = "deduplicated"
            else:
                disposition = "restated"

        if analytic_signal_id is not None:
            existing_signal = self._store.get(AnalyticSignalRecord, analytic_signal_id)
            signal_alert_ids = self._merge_linked_ids(
                existing_signal.alert_ids if existing_signal is not None else (),
                alert.alert_id,
            )
            signal_case_ids = self._merge_linked_ids(
                existing_signal.case_ids if existing_signal is not None else (),
                alert.case_id,
            )
            signal_first_seen = first_seen_at
            if existing_signal is not None and existing_signal.first_seen_at is not None:
                signal_first_seen = min(existing_signal.first_seen_at, first_seen_at)
            signal_last_seen = last_seen_at
            if existing_signal is not None and existing_signal.last_seen_at is not None:
                signal_last_seen = max(existing_signal.last_seen_at, last_seen_at)
            self.persist_record(
                AnalyticSignalRecord(
                    analytic_signal_id=analytic_signal_id,
                    substrate_detection_record_id=(
                        substrate_detection_record_id
                        if substrate_detection_record_id is not None
                        else (
                            existing_signal.substrate_detection_record_id
                            if existing_signal is not None
                            else None
                        )
                    ),
                    finding_id=finding_id,
                    alert_ids=signal_alert_ids,
                    case_ids=signal_case_ids,
                    correlation_key=correlation_key,
                    first_seen_at=signal_first_seen,
                    last_seen_at=signal_last_seen,
                    lifecycle_state="active",
                )
            )

        reconciliation = self.persist_record(
            ReconciliationRecord(
                reconciliation_id=self._next_identifier("reconciliation"),
                subject_linkage={
                    "alert_ids": (alert.alert_id,),
                    "substrate_detection_record_ids": linked_substrate_detection_ids,
                    "finding_ids": linked_finding_ids,
                    "analytic_signal_ids": linked_signal_ids,
                },
                alert_id=alert.alert_id,
                finding_id=finding_id,
                analytic_signal_id=analytic_signal_id,
                workflow_execution_id=None,
                linked_execution_ids=(),
                correlation_key=correlation_key,
                first_seen_at=persisted_first_seen,
                last_seen_at=persisted_last_seen,
                ingest_disposition=disposition,
                mismatch_summary=f"{disposition} upstream analytic signal into alert lifecycle",
                compared_at=datetime.now(timezone.utc),
                lifecycle_state="matched",
            )
        )

        return FindingAlertIngestResult(
            alert=alert,
            reconciliation=reconciliation,
            disposition=disposition,
        )

    def reconcile_action_execution(
        self,
        *,
        action_request_id: str,
        workflow_id: str,
        observed_executions: tuple[Mapping[str, object], ...],
        compared_at: datetime,
        stale_after: datetime,
    ) -> ReconciliationRecord:
        compared_at = self._require_aware_datetime(compared_at, "compared_at")
        stale_after = self._require_aware_datetime(stale_after, "stale_after")
        action_request = self._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")
        if action_request.lifecycle_state != "approved":
            raise ValueError(
                f"Action request {action_request_id!r} is not approved "
                f"(state={action_request.lifecycle_state!r})"
            )

        normalized_executions = self._normalize_observed_executions(observed_executions)
        linked_execution_ids = tuple(
            execution["workflow_execution_id"] for execution in normalized_executions
        )
        unique_execution_ids = tuple(dict.fromkeys(linked_execution_ids))
        latest_execution = normalized_executions[-1] if normalized_executions else None

        subject_linkage: dict[str, object] = {
            "action_request_ids": (action_request.action_request_id,),
            "workflow_ids": (workflow_id,),
        }
        if action_request.approval_decision_id is not None:
            subject_linkage["approval_decision_ids"] = (
                action_request.approval_decision_id,
            )
        if action_request.alert_id is not None:
            subject_linkage["alert_ids"] = (action_request.alert_id,)
        if action_request.case_id is not None:
            subject_linkage["case_ids"] = (action_request.case_id,)
        if action_request.finding_id is not None:
            subject_linkage["finding_ids"] = (action_request.finding_id,)

        ingest_disposition: str
        lifecycle_state: str
        mismatch_summary: str
        workflow_execution_id: str | None = None
        last_seen_at = action_request.requested_at

        if latest_execution is None:
            ingest_disposition = "missing"
            lifecycle_state = "pending"
            mismatch_summary = (
                "missing downstream execution for approved action request correlation"
            )
        else:
            workflow_execution_id = latest_execution["workflow_execution_id"]
            last_seen_at = latest_execution["observed_at"]
            observed_workflow_id = latest_execution["workflow_id"]
            observed_idempotency_key = latest_execution["idempotency_key"]
            if last_seen_at < stale_after and compared_at >= stale_after:
                ingest_disposition = "stale"
                lifecycle_state = "stale"
                mismatch_summary = "stale downstream execution observation requires refresh"
            elif len(unique_execution_ids) > 1:
                ingest_disposition = "duplicate"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "duplicate downstream executions observed for one approved request"
                )
            elif (
                observed_workflow_id != workflow_id
                or observed_idempotency_key != action_request.idempotency_key
            ):
                ingest_disposition = "mismatch"
                lifecycle_state = "mismatched"
                mismatch_summary = (
                    "workflow/idempotency mismatch between approved request and observed execution"
                )
            else:
                ingest_disposition = "matched"
                lifecycle_state = "matched"
                mismatch_summary = (
                    "matched approved action request to downstream workflow execution"
                )

        return self.persist_record(
            ReconciliationRecord(
                reconciliation_id=self._next_identifier("reconciliation"),
                subject_linkage=subject_linkage,
                alert_id=action_request.alert_id,
                finding_id=action_request.finding_id,
                analytic_signal_id=None,
                workflow_execution_id=workflow_execution_id,
                linked_execution_ids=linked_execution_ids,
                correlation_key=(
                    f"{action_request.action_request_id}:{workflow_id}:{action_request.idempotency_key}"
                ),
                first_seen_at=action_request.requested_at,
                last_seen_at=last_seen_at,
                ingest_disposition=ingest_disposition,
                mismatch_summary=mismatch_summary,
                compared_at=compared_at,
                lifecycle_state=lifecycle_state,
            )
        )

    @staticmethod
    def _merge_linked_ids(
        existing_values: object,
        incoming_value: str | None,
    ) -> tuple[str, ...]:
        merged: list[str] = []
        if isinstance(existing_values, (list, tuple)):
            for value in existing_values:
                if isinstance(value, str) and value not in merged:
                    merged.append(value)
        if incoming_value is not None and incoming_value not in merged:
            merged.append(incoming_value)
        return tuple(merged)

    @staticmethod
    def _linked_id_exists(existing_values: object, candidate: str) -> bool:
        return isinstance(existing_values, (list, tuple)) and candidate in existing_values

    @staticmethod
    def _normalize_observed_executions(
        observed_executions: tuple[Mapping[str, object], ...],
    ) -> tuple[dict[str, object], ...]:
        normalized: list[dict[str, object]] = []
        for execution in observed_executions:
            workflow_execution_id = execution.get("workflow_execution_id")
            workflow_id = execution.get("workflow_id")
            idempotency_key = execution.get("idempotency_key")
            observed_at = execution.get("observed_at")
            if not isinstance(workflow_execution_id, str):
                raise ValueError("observed execution must include string workflow_execution_id")
            if not isinstance(workflow_id, str):
                raise ValueError("observed execution must include string workflow_id")
            if not isinstance(idempotency_key, str):
                raise ValueError("observed execution must include string idempotency_key")
            if not isinstance(observed_at, datetime):
                raise ValueError("observed execution must include datetime observed_at")
            observed_at = AegisOpsControlPlaneService._require_aware_datetime(
                observed_at,
                "observed_at",
            )
            normalized.append(
                {
                    "workflow_execution_id": workflow_execution_id,
                    "workflow_id": workflow_id,
                    "idempotency_key": idempotency_key,
                    "observed_at": observed_at,
                }
            )

        normalized.sort(key=lambda execution: execution["observed_at"])
        return tuple(normalized)

    @staticmethod
    def _next_identifier(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4()}"


def build_runtime_snapshot(environ: Mapping[str, str] | None = None) -> RuntimeSnapshot:
    config = RuntimeConfig.from_env(environ)
    service = AegisOpsControlPlaneService(config)
    return service.describe_runtime()


def build_runtime_service(
    environ: Mapping[str, str] | None = None,
) -> AegisOpsControlPlaneService:
    config = RuntimeConfig.from_env(environ)
    return AegisOpsControlPlaneService(config)
