from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from collections import Counter
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timezone
import hmac
import ipaddress
import json
import logging
import uuid
from typing import Iterator, Mapping, Protocol, Type, TypeVar

from .adapters.executor import IsolatedExecutorAdapter
from .adapters.n8n import N8NReconciliationAdapter
from .adapters.postgres import (
    PostgresControlPlaneStore,
    ReadinessDiagnosticsAggregates,
)
from .adapters.shuffle import ShuffleActionAdapter
from .adapters.wazuh import WazuhAlertAdapter
from .config import RuntimeConfig
from .execution_coordinator import ExecutionCoordinator
from .models import (
    AITraceRecord,
    ActionExecutionRecord,
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
from .assistant_context import AssistantContextAssembler


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)
REVIEWED_LIVE_WAZUH_SOURCE_FAMILIES = frozenset({"github_audit", "entra_id"})
REVIEWED_PHASE19_LIVE_SLICE_LABEL = "Wazuh-backed GitHub audit and Entra ID live slice"


class ControlPlaneStore(Protocol):
    dsn: str
    persistence_mode: str

    def save(self, record: RecordT) -> RecordT:
        ...

    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        ...

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...

    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> AbstractContextManager[None]:
        ...

    def inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
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
    shuffle_base_url: str
    isolated_executor_base_url: str
    ownership_boundary: dict[str, str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class FindingAlertIngestResult:
    alert: AlertRecord
    reconciliation: ReconciliationRecord
    disposition: str


@dataclass(frozen=True)
class AuthenticatedRuntimePrincipal:
    identity: str
    role: str
    access_path: str
    proxy_service_account: str | None = None


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


@dataclass(frozen=True)
class AnalystQueueSnapshot:
    read_only: bool
    queue_name: str
    total_records: int
    records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "queue_name": self.queue_name,
                "total_records": self.total_records,
                "records": self.records,
            }
        )


@dataclass(frozen=True)
class AlertDetailSnapshot:
    read_only: bool
    alert_id: str
    alert: dict[str, object]
    case_record: dict[str, object] | None
    analytic_signal_record: dict[str, object] | None
    latest_reconciliation: dict[str, object]
    linked_evidence_records: tuple[dict[str, object], ...]
    reviewed_context: dict[str, object]
    review_state: str
    escalation_boundary: str
    source_system: str
    native_rule: dict[str, object] | None
    provenance: dict[str, str] | None
    lineage: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "alert_id": self.alert_id,
                "alert": self.alert,
                "case_record": self.case_record,
                "analytic_signal_record": self.analytic_signal_record,
                "latest_reconciliation": self.latest_reconciliation,
                "linked_evidence_records": self.linked_evidence_records,
                "reviewed_context": self.reviewed_context,
                "review_state": self.review_state,
                "escalation_boundary": self.escalation_boundary,
                "source_system": self.source_system,
                "native_rule": self.native_rule,
                "provenance": self.provenance,
                "lineage": self.lineage,
            }
        )


@dataclass(frozen=True)
class CaseDetailSnapshot:
    read_only: bool
    case_id: str
    case_record: dict[str, object]
    advisory_output: dict[str, object]
    reviewed_context: dict[str, object]
    linked_alert_ids: tuple[str, ...]
    linked_observation_ids: tuple[str, ...]
    linked_lead_ids: tuple[str, ...]
    linked_evidence_ids: tuple[str, ...]
    linked_recommendation_ids: tuple[str, ...]
    linked_reconciliation_ids: tuple[str, ...]
    linked_alert_records: tuple[dict[str, object], ...]
    linked_observation_records: tuple[dict[str, object], ...]
    linked_lead_records: tuple[dict[str, object], ...]
    linked_evidence_records: tuple[dict[str, object], ...]
    linked_recommendation_records: tuple[dict[str, object], ...]
    linked_reconciliation_records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "case_id": self.case_id,
                "case_record": self.case_record,
                "advisory_output": self.advisory_output,
                "reviewed_context": self.reviewed_context,
                "linked_alert_ids": self.linked_alert_ids,
                "linked_observation_ids": self.linked_observation_ids,
                "linked_lead_ids": self.linked_lead_ids,
                "linked_evidence_ids": self.linked_evidence_ids,
                "linked_recommendation_ids": self.linked_recommendation_ids,
                "linked_reconciliation_ids": self.linked_reconciliation_ids,
                "linked_alert_records": self.linked_alert_records,
                "linked_observation_records": self.linked_observation_records,
                "linked_lead_records": self.linked_lead_records,
                "linked_evidence_records": self.linked_evidence_records,
                "linked_recommendation_records": self.linked_recommendation_records,
                "linked_reconciliation_records": self.linked_reconciliation_records,
            }
        )


@dataclass(frozen=True)
class AnalystAssistantContextSnapshot:
    read_only: bool
    record_family: str
    record_id: str
    record: dict[str, object]
    advisory_output: dict[str, object]
    reviewed_context: dict[str, object]
    linked_alert_ids: tuple[str, ...]
    linked_case_ids: tuple[str, ...]
    linked_evidence_ids: tuple[str, ...]
    linked_recommendation_ids: tuple[str, ...]
    linked_reconciliation_ids: tuple[str, ...]
    linked_alert_records: tuple[dict[str, object], ...]
    linked_case_records: tuple[dict[str, object], ...]
    linked_evidence_records: tuple[dict[str, object], ...]
    linked_recommendation_records: tuple[dict[str, object], ...]
    linked_reconciliation_records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "record_family": self.record_family,
                "record_id": self.record_id,
                "record": self.record,
                "advisory_output": self.advisory_output,
                "reviewed_context": self.reviewed_context,
                "linked_alert_ids": self.linked_alert_ids,
                "linked_case_ids": self.linked_case_ids,
                "linked_evidence_ids": self.linked_evidence_ids,
                "linked_recommendation_ids": self.linked_recommendation_ids,
                "linked_reconciliation_ids": self.linked_reconciliation_ids,
                "linked_alert_records": self.linked_alert_records,
                "linked_case_records": self.linked_case_records,
                "linked_evidence_records": self.linked_evidence_records,
                "linked_recommendation_records": self.linked_recommendation_records,
                "linked_reconciliation_records": self.linked_reconciliation_records,
            }
        )


@dataclass(frozen=True)
class AdvisoryInspectionSnapshot:
    read_only: bool
    record_family: str
    record_id: str
    output_kind: str
    status: str
    cited_summary: dict[str, object]
    key_observations: tuple[dict[str, object], ...]
    unresolved_questions: tuple[dict[str, object], ...]
    candidate_recommendations: tuple[dict[str, object], ...]
    citations: tuple[str, ...]
    uncertainty_flags: tuple[str, ...]
    reviewed_context: dict[str, object]
    linked_alert_ids: tuple[str, ...]
    linked_case_ids: tuple[str, ...]
    linked_evidence_ids: tuple[str, ...]
    linked_recommendation_ids: tuple[str, ...]
    linked_reconciliation_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "record_family": self.record_family,
                "record_id": self.record_id,
                "output_kind": self.output_kind,
                "status": self.status,
                "cited_summary": self.cited_summary,
                "key_observations": self.key_observations,
                "unresolved_questions": self.unresolved_questions,
                "candidate_recommendations": self.candidate_recommendations,
                "citations": self.citations,
                "uncertainty_flags": self.uncertainty_flags,
                "reviewed_context": self.reviewed_context,
                "linked_alert_ids": self.linked_alert_ids,
                "linked_case_ids": self.linked_case_ids,
                "linked_evidence_ids": self.linked_evidence_ids,
                "linked_recommendation_ids": self.linked_recommendation_ids,
                "linked_reconciliation_ids": self.linked_reconciliation_ids,
            }
        )


@dataclass(frozen=True)
class RecommendationDraftSnapshot:
    read_only: bool
    record_family: str
    record_id: str
    recommendation_draft: dict[str, object]
    reviewed_context: dict[str, object]
    linked_alert_ids: tuple[str, ...]
    linked_case_ids: tuple[str, ...]
    linked_evidence_ids: tuple[str, ...]
    linked_recommendation_ids: tuple[str, ...]
    linked_reconciliation_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "record_family": self.record_family,
                "record_id": self.record_id,
                "recommendation_draft": self.recommendation_draft,
                "reviewed_context": self.reviewed_context,
                "linked_alert_ids": self.linked_alert_ids,
                "linked_case_ids": self.linked_case_ids,
                "linked_evidence_ids": self.linked_evidence_ids,
                "linked_recommendation_ids": self.linked_recommendation_ids,
                "linked_reconciliation_ids": self.linked_reconciliation_ids,
            }
        )


@dataclass(frozen=True)
class StartupStatusSnapshot:
    read_only: bool
    startup_ready: bool
    required_bindings: tuple[str, ...]
    missing_bindings: tuple[str, ...]
    validated_surfaces: tuple[str, ...]
    blocking_reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(asdict(self))


@dataclass(frozen=True)
class ShutdownStatusSnapshot:
    read_only: bool
    shutdown_ready: bool
    blocking_reasons: tuple[str, ...]
    open_case_ids: tuple[str, ...]
    active_action_request_ids: tuple[str, ...]
    active_action_execution_ids: tuple[str, ...]
    unresolved_reconciliation_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(asdict(self))


@dataclass(frozen=True)
class RestoreDrillSnapshot:
    read_only: bool
    drill_passed: bool
    verified_case_ids: tuple[str, ...]
    verified_approval_decision_ids: tuple[str, ...]
    verified_action_execution_ids: tuple[str, ...]
    verified_reconciliation_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(asdict(self))


@dataclass(frozen=True)
class RestoreSummarySnapshot:
    read_only: bool
    restored_record_counts: dict[str, int]
    restore_drill: RestoreDrillSnapshot

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "restored_record_counts": self.restored_record_counts,
                "restore_drill": self.restore_drill.to_dict(),
            }
        )


@dataclass(frozen=True)
class ReadinessDiagnosticsSnapshot:
    read_only: bool
    booted: bool
    status: str
    startup: dict[str, object]
    shutdown: dict[str, object]
    metrics: dict[str, object]
    latest_reconciliation: dict[str, object] | None

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "booted": self.booted,
                "status": self.status,
                "startup": self.startup,
                "shutdown": self.shutdown,
                "metrics": self.metrics,
                "latest_reconciliation": self.latest_reconciliation,
            }
        )


def _derive_readiness_status(
    *,
    startup_ready: bool,
    reconciliation_lifecycle_counts: Mapping[str, int],
) -> str:
    if not startup_ready:
        return "failing_closed"
    if reconciliation_lifecycle_counts.get("stale", 0):
        return "stale"
    if reconciliation_lifecycle_counts.get("mismatched", 0):
        return "degraded"
    return "ready"


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
        ActionExecutionRecord,
        HuntRecord,
        HuntRunRecord,
        AITraceRecord,
        ReconciliationRecord,
    )
}

AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES: tuple[Type[ControlPlaneRecord], ...] = (
    AnalyticSignalRecord,
    AlertRecord,
    EvidenceRecord,
    CaseRecord,
    ApprovalDecisionRecord,
    ActionRequestRecord,
    ActionExecutionRecord,
    ReconciliationRecord,
)
AUTHORITATIVE_RECORD_CHAIN_FAMILIES: tuple[str, ...] = tuple(
    record_type.record_family for record_type in AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES
)
AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION = (
    "phase21.authoritative-record-chain.v1"
)
_AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY: dict[str, str] = {
    "analytic_signal": "analytic_signal_id",
    "alert": "alert_id",
    "evidence": "evidence_id",
    "case": "case_id",
    "approval_decision": "approval_decision_id",
    "action_request": "action_request_id",
    "action_execution": "action_execution_id",
    "reconciliation": "reconciliation_id",
}
_BACKUP_DATETIME_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("first_seen_at", "last_seen_at"),
    "evidence": ("acquired_at",),
    "approval_decision": ("decided_at", "approved_expires_at"),
    "action_request": ("requested_at", "expires_at"),
    "action_execution": ("delegated_at", "expires_at"),
    "reconciliation": ("first_seen_at", "last_seen_at", "compared_at"),
}
_BACKUP_TUPLE_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("alert_ids", "case_ids"),
    "case": ("evidence_ids",),
    "approval_decision": ("approver_identities",),
    "reconciliation": ("linked_execution_run_ids",),
}
_BACKUP_MAPPING_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("reviewed_context",),
    "alert": ("reviewed_context",),
    "case": ("reviewed_context",),
    "approval_decision": ("target_snapshot",),
    "action_request": (
        "target_scope",
        "requested_payload",
        "policy_basis",
        "policy_evaluation",
    ),
    "action_execution": ("target_scope", "approved_payload", "provenance"),
    "reconciliation": ("subject_linkage",),
}

_ACTION_POLICY_ALLOWED_VALUES: dict[str, tuple[str, ...]] = {
    "severity": ("low", "medium", "high", "critical"),
    "target_scope": (
        "single_identity",
        "single_asset",
        "multi_identity",
        "multi_asset",
        "fleet",
        "organization",
    ),
    "action_reversibility": (
        "reversible",
        "bounded_reversible",
        "irreversible",
    ),
    "asset_criticality": ("standard", "elevated", "high", "critical"),
    "identity_criticality": ("standard", "elevated", "high", "critical"),
    "blast_radius": (
        "single_target",
        "bounded_group",
        "multi_target",
        "organization",
    ),
    "execution_constraint": (
        "routine_allowed",
        "isolated_preferred",
        "requires_isolated_executor",
    ),
}

_ACTION_POLICY_RANKS: dict[str, dict[str, int]] = {
    field_name: {
        allowed_value: index for index, allowed_value in enumerate(allowed_values)
    }
    for field_name, allowed_values in _ACTION_POLICY_ALLOWED_VALUES.items()
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


def _classify_network_identifier(value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        return "missing"
    try:
        peer_ip = ipaddress.ip_address(value.strip())
    except ValueError:
        return "invalid"
    if peer_ip.is_loopback:
        return "loopback"
    if peer_ip.is_private:
        return "private"
    if peer_ip.is_global:
        return "public"
    return "special"


def _count_identity_values(value: object) -> int:
    if isinstance(value, (tuple, list)):
        return sum(
            1 for item in value if isinstance(item, str) and item.strip()
        )
    if isinstance(value, str) and value.strip():
        return 1
    return 0


def _sanitize_structured_event_fields(
    fields: Mapping[str, object],
) -> dict[str, object]:
    sanitized: dict[str, object] = {}
    for key, value in fields.items():
        normalized_key = str(key)
        if normalized_key == "peer_addr":
            sanitized["peer_addr_class"] = _classify_network_identifier(value)
            continue
        if normalized_key.endswith("_identity"):
            sanitized[f"{normalized_key}_present"] = (
                _count_identity_values(value) > 0
            )
            continue
        if normalized_key.endswith("_identities"):
            sanitized[f"{normalized_key}_count"] = _count_identity_values(value)
            continue
        sanitized[normalized_key] = _json_ready(value)
    return sanitized


def _record_to_dict(record: ControlPlaneRecord) -> dict[str, object]:
    return {
        field.name: getattr(record, field.name)
        for field in fields(record)
    }


def _redacted_reconciliation_payload(
    reconciliation: ReconciliationRecord,
) -> dict[str, object]:
    payload = _record_to_dict(reconciliation)
    subject_linkage_payload = payload.get("subject_linkage")
    if isinstance(subject_linkage_payload, Mapping):
        redacted_subject_linkage = dict(subject_linkage_payload)
        redacted_subject_linkage.pop("latest_native_payload", None)
        payload["subject_linkage"] = redacted_subject_linkage
    return payload


def _build_shutdown_status_snapshot(
    *,
    open_case_ids: tuple[str, ...],
    active_action_request_ids: tuple[str, ...],
    active_action_execution_ids: tuple[str, ...],
    unresolved_reconciliation_ids: tuple[str, ...],
) -> ShutdownStatusSnapshot:
    blocking_reasons: list[str] = []
    if open_case_ids:
        blocking_reasons.append(
            "controlled shutdown requires resolving or explicitly handing off open casework"
        )
    if active_action_request_ids:
        blocking_reasons.append(
            "controlled shutdown requires approval-bound action requests to leave an inactive state"
        )
    if active_action_execution_ids:
        blocking_reasons.append(
            "controlled shutdown requires queued or running executions to reach a terminal state"
        )
    if unresolved_reconciliation_ids:
        blocking_reasons.append(
            "controlled shutdown requires pending reconciliation mismatches to be reviewed first"
        )
    return ShutdownStatusSnapshot(
        read_only=True,
        shutdown_ready=not blocking_reasons,
        blocking_reasons=tuple(blocking_reasons),
        open_case_ids=open_case_ids,
        active_action_request_ids=active_action_request_ids,
        active_action_execution_ids=active_action_execution_ids,
        unresolved_reconciliation_ids=unresolved_reconciliation_ids,
    )


def _parse_backup_datetime(value: object, field_name: str) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty ISO 8601 datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO 8601 datetime") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return parsed


def _record_from_backup_payload(
    record_type: Type[RecordT],
    payload: Mapping[str, object],
) -> RecordT:
    if not isinstance(payload, Mapping):
        raise ValueError(
            f"{record_type.record_family} backup entries must be JSON objects"
        )
    family = record_type.record_family
    datetime_fields = set(_BACKUP_DATETIME_FIELDS_BY_FAMILY.get(family, ()))
    tuple_fields = set(_BACKUP_TUPLE_FIELDS_BY_FAMILY.get(family, ()))
    mapping_fields = set(_BACKUP_MAPPING_FIELDS_BY_FAMILY.get(family, ()))
    kwargs: dict[str, object] = {}
    for field_info in fields(record_type):
        if field_info.name not in payload:
            raise ValueError(
                f"{family} backup entry is missing required field {field_info.name!r}"
            )
        value = payload[field_info.name]
        if field_info.name in datetime_fields:
            value = _parse_backup_datetime(value, field_info.name)
        elif field_info.name in tuple_fields:
            if value is None:
                value = ()
            elif isinstance(value, list):
                value = tuple(value)
            elif not isinstance(value, tuple):
                raise ValueError(
                    f"{family}.{field_info.name} must be a JSON array in restore payload"
                )
            if any(not isinstance(item, str) or not item.strip() for item in value):
                raise ValueError(
                    f"{family}.{field_info.name} must contain only non-empty strings"
                )
        elif field_info.name in mapping_fields:
            if not isinstance(value, Mapping):
                raise ValueError(
                    f"{family}.{field_info.name} must be a JSON object in restore payload"
                )
            value = {str(key): item for key, item in value.items()}
        kwargs[field_info.name] = value
    return record_type(**kwargs)

def _merge_reviewed_context(
    existing_context: Mapping[str, object] | None,
    incoming_context: Mapping[str, object] | None,
) -> dict[str, object]:
    merged: dict[str, object] = {}
    if isinstance(existing_context, Mapping):
        merged.update({str(key): value for key, value in existing_context.items()})
    if not isinstance(incoming_context, Mapping):
        return merged

    for key, value in incoming_context.items():
        normalized_key = str(key)
        existing_value = merged.get(normalized_key)
        if isinstance(existing_value, Mapping) and isinstance(value, Mapping):
            merged[normalized_key] = _merge_reviewed_context(existing_value, value)
        else:
            merged[normalized_key] = value
    return merged


def _find_duplicate_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(value for value, count in Counter(values).items() if count > 1)
    )


def _normalize_admission_provenance(
    value: object,
) -> dict[str, str] | None:
    if not isinstance(value, Mapping):
        return None
    normalized: dict[str, str] = {}
    for field_name in ("admission_kind", "admission_channel"):
        field_value = value.get(field_name)
        if isinstance(field_value, str):
            normalized_value = field_value.strip()
            if normalized_value:
                normalized[field_name] = normalized_value
    if len(normalized) != 2:
        return None
    return normalized


def _advisory_inspection_snapshot_from_context(
    snapshot: AnalystAssistantContextSnapshot,
) -> AdvisoryInspectionSnapshot:
    advisory_output = snapshot.advisory_output
    return AdvisoryInspectionSnapshot(
        read_only=True,
        record_family=snapshot.record_family,
        record_id=snapshot.record_id,
        output_kind=str(advisory_output["output_kind"]),
        status=str(advisory_output["status"]),
        cited_summary=dict(advisory_output["cited_summary"]),
        key_observations=tuple(advisory_output["key_observations"]),
        unresolved_questions=tuple(advisory_output["unresolved_questions"]),
        candidate_recommendations=tuple(advisory_output["candidate_recommendations"]),
        citations=tuple(advisory_output["citations"]),
        uncertainty_flags=tuple(advisory_output["uncertainty_flags"]),
        reviewed_context=dict(snapshot.reviewed_context),
        linked_alert_ids=snapshot.linked_alert_ids,
        linked_case_ids=snapshot.linked_case_ids,
        linked_evidence_ids=snapshot.linked_evidence_ids,
        linked_recommendation_ids=snapshot.linked_recommendation_ids,
        linked_reconciliation_ids=snapshot.linked_reconciliation_ids,
    )


def _recommendation_draft_snapshot_from_context(
    snapshot: AnalystAssistantContextSnapshot,
) -> RecommendationDraftSnapshot:
    advisory_output = snapshot.advisory_output
    return RecommendationDraftSnapshot(
        read_only=True,
        record_family=snapshot.record_family,
        record_id=snapshot.record_id,
        recommendation_draft={
            "source_output_kind": advisory_output["output_kind"],
            "status": advisory_output["status"],
            "review_lifecycle_state": snapshot.record.get("lifecycle_state"),
            "cited_summary": advisory_output["cited_summary"],
            "candidate_recommendations": advisory_output["candidate_recommendations"],
            "unresolved_questions": advisory_output["unresolved_questions"],
            "citations": advisory_output["citations"],
            "uncertainty_flags": advisory_output["uncertainty_flags"],
        },
        reviewed_context=dict(snapshot.reviewed_context),
        linked_alert_ids=snapshot.linked_alert_ids,
        linked_case_ids=snapshot.linked_case_ids,
        linked_evidence_ids=snapshot.linked_evidence_ids,
        linked_recommendation_ids=snapshot.linked_recommendation_ids,
        linked_reconciliation_ids=snapshot.linked_reconciliation_ids,
    )


def _assistant_advisory_draft_without_revision_history(
    draft: Mapping[str, object],
) -> dict[str, object]:
    return {
        str(key): value
        for key, value in draft.items()
        if str(key) != "revision_history"
    }


def _assistant_advisory_draft_revision_history(
    draft: Mapping[str, object],
) -> tuple[dict[str, object], ...]:
    raw_history = draft.get("revision_history", ())
    if not isinstance(raw_history, (list, tuple)):
        return ()
    revision_history: list[dict[str, object]] = []
    for entry in raw_history:
        if isinstance(entry, Mapping):
            revision_history.append(
                _assistant_advisory_draft_without_revision_history(entry)
            )
    return tuple(revision_history)


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
        self._shuffle = ShuffleActionAdapter(config.shuffle_base_url)
        self._isolated_executor = IsolatedExecutorAdapter(
            config.isolated_executor_base_url
        )
        self._logger = logging.getLogger("aegisops.control_plane")
        self._assistant_context_assembler = AssistantContextAssembler(
            self,
            record_types_by_family=RECORD_TYPES_BY_FAMILY,
            record_to_dict=_record_to_dict,
            merge_reviewed_context=_merge_reviewed_context,
            assistant_context_snapshot_factory=AnalystAssistantContextSnapshot,
            advisory_snapshot_from_context=_advisory_inspection_snapshot_from_context,
            recommendation_draft_snapshot_from_context=(
                _recommendation_draft_snapshot_from_context
            ),
        )
        self._execution_coordinator = ExecutionCoordinator(self)

    def describe_runtime(self) -> RuntimeSnapshot:
        return RuntimeSnapshot(
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

    def persist_record(self, record: RecordT) -> RecordT:
        return self._store.save(record)

    def _emit_structured_event(
        self,
        level: int,
        event: str,
        **fields: object,
    ) -> None:
        payload = {
            "event": event,
            "service_name": "aegisops-control-plane",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            **_sanitize_structured_event_fields(fields),
        }
        self._logger.log(level, json.dumps(payload, sort_keys=True, separators=(",", ":")))

    def _emit_action_execution_delegated_event(
        self,
        execution: ActionExecutionRecord,
    ) -> None:
        self._emit_structured_event(
            logging.INFO,
            "action_execution_delegated",
            action_execution_id=execution.action_execution_id,
            action_request_id=execution.action_request_id,
            approval_decision_id=execution.approval_decision_id,
            execution_surface_type=execution.execution_surface_type,
            execution_surface_id=execution.execution_surface_id,
            execution_run_id=execution.execution_run_id,
            lifecycle_state=execution.lifecycle_state,
        )

    def get_record(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        return self._store.get(record_type, record_id)

    def validate_wazuh_ingest_runtime(self) -> None:
        if self._config.wazuh_ingest_shared_secret.strip() == "":
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
            not self._listener_is_loopback()
            and not self._config.wazuh_ingest_trusted_proxy_cidrs
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must be set "
                "before starting the live Wazuh ingest runtime on a non-loopback interface"
            )
        if self._config.wazuh_ingest_reverse_proxy_secret.strip() == "":
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
            not self._listener_is_loopback()
            and not self._config.protected_surface_trusted_proxy_cidrs
        ):
            raise ValueError(
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS must be set "
                "before starting protected control-plane surfaces on a non-loopback interface"
            )
        if self._config.protected_surface_trusted_proxy_cidrs:
            if self._config.protected_surface_reverse_proxy_secret.strip() == "":
                raise ValueError(
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET must be set "
                    "before admitting reviewed reverse-proxy traffic to protected control-plane surfaces"
                )
            if self._config.protected_surface_proxy_service_account.strip() == "":
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
    ) -> AuthenticatedRuntimePrincipal:
        self.validate_protected_surface_runtime()

        if self._peer_addr_is_loopback(peer_addr):
            principal = AuthenticatedRuntimePrincipal(
                identity="loopback-local-operator",
                role="loopback_local",
                access_path="loopback_direct",
            )
        else:
            if not self._is_trusted_protected_surface_peer(peer_addr):
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
            principal = AuthenticatedRuntimePrincipal(
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
        if expected_token == "":
            raise PermissionError(
                "admin bootstrap contract is disabled until AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN is bound"
            )
        if not hmac.compare_digest((supplied_token or "").strip(), expected_token):
            raise PermissionError("admin bootstrap token did not match the reviewed secret")

    def require_break_glass_token(self, supplied_token: str | None) -> None:
        expected_token = self._config.break_glass_token.strip()
        if expected_token == "":
            raise PermissionError(
                "break-glass contract is disabled until AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN is bound"
            )
        if not hmac.compare_digest((supplied_token or "").strip(), expected_token):
            raise PermissionError("break-glass token did not match the reviewed secret")

    def ingest_wazuh_alert(
        self,
        *,
        raw_alert: Mapping[str, object],
        authorization_header: str | None,
        forwarded_proto: str | None,
        reverse_proxy_secret_header: str | None,
        peer_addr: str | None,
    ) -> FindingAlertIngestResult:
        self.validate_wazuh_ingest_runtime()

        if not self._is_trusted_wazuh_ingest_peer(peer_addr):
            self._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="untrusted_peer",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest rejects requests that bypass the reviewed reverse proxy peer boundary"
            )

        if (forwarded_proto or "").strip().lower() != "https":
            self._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="forwarded_proto_not_https",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest requires the reviewed reverse proxy HTTPS boundary"
            )
        if not hmac.compare_digest(
            (reverse_proxy_secret_header or "").strip(),
            self._config.wazuh_ingest_reverse_proxy_secret,
        ):
            self._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="reverse_proxy_secret_mismatch",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest requires the reviewed reverse proxy boundary credential"
            )

        scheme, separator, supplied_secret = (authorization_header or "").partition(" ")
        if separator == "" or scheme != "Bearer" or supplied_secret.strip() == "":
            self._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="missing_bearer_secret",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest requires Authorization: Bearer <shared secret>"
            )
        if not hmac.compare_digest(
            supplied_secret.strip(),
            self._config.wazuh_ingest_shared_secret,
        ):
            self._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="bearer_secret_mismatch",
                peer_addr=peer_addr,
            )
            raise PermissionError(
                "live Wazuh ingest bearer credential did not match the reviewed shared secret"
            )

        native_alert = self._require_mapping(raw_alert, "alert")
        source_family = self._normalize_optional_string(
            (
                self._require_mapping(
                    native_alert.get("data"),
                    "data",
                )
            ).get("source_family"),
            "data.source_family",
        )
        if source_family not in REVIEWED_LIVE_WAZUH_SOURCE_FAMILIES:
            self._emit_structured_event(
                logging.WARNING,
                "wazuh_ingest_rejected",
                reason="unsupported_source_family",
                peer_addr=peer_addr,
                source_family=source_family,
            )
            raise ValueError(
                "live Wazuh ingest only admits the reviewed github_audit and entra_id live source families"
            )

        adapter = WazuhAlertAdapter()
        native_record = self._with_native_detection_admission_provenance(
            adapter.build_native_detection_record(native_alert),
            admission_kind="live",
            admission_channel="live_wazuh_webhook",
        )
        ingest_result = self.ingest_native_detection_record(adapter, native_record)
        self._emit_structured_event(
            logging.INFO,
            "wazuh_ingest_admitted",
            peer_addr=peer_addr,
            source_family=source_family,
            disposition=ingest_result.disposition,
            alert_id=ingest_result.alert.alert_id,
            finding_id=ingest_result.alert.finding_id,
            reconciliation_id=ingest_result.reconciliation.reconciliation_id,
        )
        return ingest_result

    def _listener_is_loopback(self) -> bool:
        host = self._config.host.strip()
        if host.lower() == "localhost":
            return True
        try:
            return ipaddress.ip_address(host).is_loopback
        except ValueError:
            return False

    def _is_trusted_wazuh_ingest_peer(self, peer_addr: str | None) -> bool:
        return self._is_trusted_peer_for_proxy_cidrs(
            peer_addr,
            self._config.wazuh_ingest_trusted_proxy_cidrs,
        )

    def _is_trusted_protected_surface_peer(self, peer_addr: str | None) -> bool:
        return self._is_trusted_peer_for_proxy_cidrs(
            peer_addr,
            self._config.protected_surface_trusted_proxy_cidrs,
        )

    def _is_trusted_peer_for_proxy_cidrs(
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
        if self._listener_is_loopback():
            return peer_ip.is_loopback
        for cidr in trusted_proxy_cidrs:
            if peer_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        return False

    @staticmethod
    def _peer_addr_is_loopback(peer_addr: str | None) -> bool:
        if peer_addr is None or peer_addr.strip() == "":
            return False
        try:
            return ipaddress.ip_address(peer_addr.strip()).is_loopback
        except ValueError:
            return False

    def delegate_approved_action_to_shuffle(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        return self._execution_coordinator.delegate_approved_action_to_shuffle(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
        )

    def delegate_approved_action_to_isolated_executor(
        self,
        *,
        action_request_id: str,
        approved_payload: Mapping[str, object],
        delegated_at: datetime,
        delegation_issuer: str,
        evidence_ids: tuple[str, ...] = (),
    ) -> ActionExecutionRecord:
        return self._execution_coordinator.delegate_approved_action_to_isolated_executor(
            action_request_id=action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer=delegation_issuer,
            evidence_ids=evidence_ids,
        )

    def evaluate_action_policy(self, action_request_id: str) -> ActionRequestRecord:
        action_request_id = self._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        action_request = self._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")

        normalized_policy_basis = self._normalize_action_policy_basis(
            action_request.policy_basis
        )
        policy_evaluation = self._apply_action_policy_evaluation_overrides(
            computed_policy_evaluation=self._determine_action_policy(
                normalized_policy_basis
            ),
            persisted_policy_evaluation=action_request.policy_evaluation,
        )
        evaluated = ActionRequestRecord(
            action_request_id=action_request.action_request_id,
            approval_decision_id=action_request.approval_decision_id,
            case_id=action_request.case_id,
            alert_id=action_request.alert_id,
            finding_id=action_request.finding_id,
            idempotency_key=action_request.idempotency_key,
            target_scope=action_request.target_scope,
            payload_hash=action_request.payload_hash,
            requested_at=action_request.requested_at,
            expires_at=action_request.expires_at,
            lifecycle_state=action_request.lifecycle_state,
            requester_identity=action_request.requester_identity,
            requested_payload=action_request.requested_payload,
            policy_basis=normalized_policy_basis,
            policy_evaluation=policy_evaluation,
        )
        return self.persist_record(evaluated)

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

    def describe_startup_status(self) -> StartupStatusSnapshot:
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
            if not str(binding_values[binding_name]).strip()
            or binding_values[binding_name] == "<set-me>"
        )
        validated_surfaces: list[str] = []
        blocking_reasons: list[str] = []
        try:
            self.validate_wazuh_ingest_runtime()
        except ValueError as exc:
            blocking_reasons.append(str(exc))
        else:
            validated_surfaces.append("wazuh_ingest")
        try:
            self.validate_protected_surface_runtime()
        except ValueError as exc:
            blocking_reasons.append(str(exc))
        else:
            validated_surfaces.append("protected_surface")

        return StartupStatusSnapshot(
            read_only=True,
            startup_ready=not missing_bindings and not blocking_reasons,
            required_bindings=required_bindings,
            missing_bindings=missing_bindings,
            validated_surfaces=tuple(validated_surfaces),
            blocking_reasons=tuple(blocking_reasons),
        )

    def describe_shutdown_status(self) -> ShutdownStatusSnapshot:
        readiness_aggregates = self._inspect_readiness_aggregates()
        return _build_shutdown_status_snapshot(
            open_case_ids=readiness_aggregates.open_case_ids,
            active_action_request_ids=readiness_aggregates.active_action_request_ids,
            active_action_execution_ids=readiness_aggregates.active_action_execution_ids,
            unresolved_reconciliation_ids=readiness_aggregates.unresolved_reconciliation_ids,
        )

    def inspect_readiness_diagnostics(self) -> ReadinessDiagnosticsSnapshot:
        with self._store.transaction(isolation_level="REPEATABLE READ"):
            startup = self.describe_startup_status()
            readiness_aggregates = self._inspect_readiness_aggregates()

        shutdown = _build_shutdown_status_snapshot(
            open_case_ids=readiness_aggregates.open_case_ids,
            active_action_request_ids=readiness_aggregates.active_action_request_ids,
            active_action_execution_ids=readiness_aggregates.active_action_execution_ids,
            unresolved_reconciliation_ids=readiness_aggregates.unresolved_reconciliation_ids,
        )

        status = _derive_readiness_status(
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
                "queued": readiness_aggregates.action_execution_lifecycle_counts.get(
                    "queued", 0
                ),
                "running": readiness_aggregates.action_execution_lifecycle_counts.get(
                    "running", 0
                ),
                "terminal": sum(
                    count
                    for state, count in readiness_aggregates.action_execution_lifecycle_counts.items()
                    if state not in {"queued", "running"}
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

        return ReadinessDiagnosticsSnapshot(
            read_only=True,
            booted=True,
            status=status,
            startup=startup.to_dict(),
            shutdown=shutdown.to_dict(),
            metrics=metrics,
            latest_reconciliation=(
                _redacted_reconciliation_payload(
                    readiness_aggregates.latest_reconciliation
                )
                if readiness_aggregates.latest_reconciliation is not None
                else None
            ),
        )

    def _inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
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
                if record.lifecycle_state in {"queued", "running"}
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
            for record_type in AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES:
                family = record_type.record_family
                records = [
                    _json_ready(_record_to_dict(record))
                    for record in self._store.list(record_type)
                ]
                record_families[family] = records
                record_counts[family] = len(records)
        return {
            "backup_schema_version": AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "persistence_mode": self._store.persistence_mode,
            "record_families": record_families,
            "record_counts": record_counts,
        }

    def restore_authoritative_record_chain_backup(
        self,
        backup_payload: Mapping[str, object],
    ) -> RestoreSummarySnapshot:
        if not isinstance(backup_payload, Mapping):
            raise ValueError("restore payload must be a JSON object")
        backup_schema_version = backup_payload.get("backup_schema_version")
        if backup_schema_version != AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION:
            raise ValueError(
                "restore payload must declare the reviewed authoritative record-chain schema version"
            )
        record_families_payload = backup_payload.get("record_families")
        if not isinstance(record_families_payload, Mapping):
            raise ValueError("restore payload must contain record_families")
        record_counts_payload = backup_payload.get("record_counts")
        if not isinstance(record_counts_payload, Mapping):
            raise ValueError("restore payload must contain record_counts")

        parsed_records: dict[str, tuple[ControlPlaneRecord, ...]] = {}
        restored_record_counts: dict[str, int] = {}
        for record_type in AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES:
            family = record_type.record_family
            raw_records = record_families_payload.get(family)
            if not isinstance(raw_records, list):
                raise ValueError(
                    f"restore payload must contain a JSON array for record family {family!r}"
                )
            expected_count = record_counts_payload.get(family)
            if expected_count != len(raw_records):
                raise ValueError(
                    f"restore payload record count mismatch for {family!r}: "
                    f"expected {expected_count!r}, found {len(raw_records)}"
                )
            parsed = tuple(
                _record_from_backup_payload(record_type, raw_record)
                for raw_record in raw_records
            )
            parsed_records[family] = parsed
            restored_record_counts[family] = len(parsed)

        self._validate_authoritative_record_chain_restore(
            parsed_records,
            restored_record_counts=restored_record_counts,
        )
        with self._store.transaction(isolation_level="SERIALIZABLE"):
            self._require_empty_authoritative_restore_target()
            for record_type in AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES:
                for record in parsed_records[record_type.record_family]:
                    self.persist_record(record)
            restore_drill = self.run_authoritative_restore_drill()
        return RestoreSummarySnapshot(
            read_only=True,
            restored_record_counts=restored_record_counts,
            restore_drill=restore_drill,
        )

    @contextmanager
    def _restore_drill_snapshot_transaction(self) -> Iterator[None]:
        try:
            with self._store.transaction(isolation_level="REPEATABLE READ"):
                yield
                return
        except ValueError as exc:
            if str(exc) != "Cannot set isolation_level inside an active transaction":
                raise
        with self._store.transaction():
            yield

    def run_authoritative_restore_drill(self) -> RestoreDrillSnapshot:
        with self._restore_drill_snapshot_transaction():
            return self._run_authoritative_restore_drill_snapshot()

    def _run_authoritative_restore_drill_snapshot(self) -> RestoreDrillSnapshot:
        self._validate_authoritative_record_chain_restore(
            {
                record_type.record_family: self._store.list(record_type)
                for record_type in AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES
            }
        )
        verified_case_ids = tuple(
            record.case_id for record in self._store.list(CaseRecord)
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
            self.inspect_case_detail(case_id)
        for approval_decision_id in verified_approval_decision_ids:
            self.inspect_assistant_context("approval_decision", approval_decision_id)
        for action_execution_id in verified_action_execution_ids:
            self.inspect_assistant_context("action_execution", action_execution_id)
        for reconciliation_id in verified_reconciliation_ids:
            self.inspect_assistant_context("reconciliation", reconciliation_id)
        self.inspect_reconciliation_status()
        startup = self.describe_startup_status()
        readiness_aggregates = self._inspect_readiness_aggregates()
        readiness_status = _derive_readiness_status(
            startup_ready=startup.startup_ready,
            reconciliation_lifecycle_counts=readiness_aggregates.reconciliation_lifecycle_counts,
        )

        return RestoreDrillSnapshot(
            read_only=True,
            drill_passed=readiness_status == "ready",
            verified_case_ids=verified_case_ids,
            verified_approval_decision_ids=verified_approval_decision_ids,
            verified_action_execution_ids=verified_action_execution_ids,
            verified_reconciliation_ids=verified_reconciliation_ids,
        )

    def inspect_analyst_queue(self) -> AnalystQueueSnapshot:
        active_alert_states = {
            "new",
            "triaged",
            "investigating",
            "escalated_to_case",
            "reopened",
        }
        latest_reconciliation_by_alert_id = (
            self._latest_detection_reconciliations_by_alert_id()
        )
        queue_records: list[dict[str, object]] = []
        for alert in self._store.list(AlertRecord):
            if alert.lifecycle_state not in active_alert_states:
                continue
            reconciliation = latest_reconciliation_by_alert_id.get(alert.alert_id)
            if reconciliation is None:
                continue

            if not self._reconciliation_is_wazuh_origin(reconciliation):
                continue

            source_systems = self._merge_linked_ids(
                reconciliation.subject_linkage.get("source_systems"),
                None,
            )
            substrate_detection_record_ids = self._merge_linked_ids(
                reconciliation.subject_linkage.get("substrate_detection_record_ids"),
                None,
            )
            case_record = (
                self._store.get(CaseRecord, alert.case_id)
                if alert.case_id is not None
                else None
            )
            review_state = self._alert_review_state(alert)
            queue_records.append(
                {
                    "alert_id": alert.alert_id,
                    "finding_id": alert.finding_id,
                    "analytic_signal_id": alert.analytic_signal_id,
                    "case_id": alert.case_id,
                    "case_lifecycle_state": (
                        case_record.lifecycle_state if case_record is not None else None
                    ),
                    "queue_selection": "business_hours_triage",
                    "review_state": review_state,
                    "escalation_boundary": self._alert_escalation_boundary(alert),
                    "source_system": (
                        "wazuh"
                        if self._reconciliation_is_wazuh_origin(reconciliation)
                        else (source_systems[0] if source_systems else "wazuh")
                    ),
                    "substrate_detection_record_ids": substrate_detection_record_ids,
                    "accountable_source_identities": self._merge_linked_ids(
                        reconciliation.subject_linkage.get(
                            "accountable_source_identities"
                        ),
                        None,
                    ),
                    "reviewed_context": dict(alert.reviewed_context),
                    "native_rule": reconciliation.subject_linkage.get(
                        "latest_native_rule"
                    ),
                    "evidence_ids": self._merge_linked_ids(
                        reconciliation.subject_linkage.get("evidence_ids"),
                        None,
                    ),
                    "correlation_key": reconciliation.correlation_key,
                    "first_seen_at": reconciliation.first_seen_at,
                    "last_seen_at": reconciliation.last_seen_at,
                }
            )

        queue_records.sort(
            key=lambda record: (
                record["last_seen_at"]
                or datetime.min.replace(tzinfo=timezone.utc),
                record["alert_id"],
            ),
            reverse=True,
        )
        return AnalystQueueSnapshot(
            read_only=True,
            queue_name="analyst_review",
            total_records=len(queue_records),
            records=tuple(queue_records),
        )

    def inspect_alert_detail(self, alert_id: str) -> AlertDetailSnapshot:
        alert_id = self._require_non_empty_string(alert_id, "alert_id")
        alert = self._store.get(AlertRecord, alert_id)
        if alert is None:
            raise LookupError(f"Missing alert record {alert_id!r} for detail inspection")

        reconciliation = self._latest_detection_reconciliation_for_alert(alert.alert_id)
        if reconciliation is None or not self._reconciliation_is_wazuh_origin(reconciliation):
            raise LookupError(
                f"Missing reviewed Wazuh-backed reconciliation for alert {alert_id!r}"
            )

        case_record = (
            self._store.get(CaseRecord, alert.case_id)
            if alert.case_id is not None
            else None
        )
        analytic_signal_record = (
            self._store.get(AnalyticSignalRecord, alert.analytic_signal_id)
            if alert.analytic_signal_id is not None
            else None
        )
        evidence_records = self._assistant_evidence_records_for_context(
            alert_ids=(alert.alert_id,),
            case_ids=(),
            evidence_ids=self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "evidence_ids",
            ),
            exclude_evidence_id=None,
        )
        source_systems = self._merge_linked_ids(
            reconciliation.subject_linkage.get("source_systems"),
            None,
        )
        substrate_detection_record_ids = self._merge_linked_ids(
            reconciliation.subject_linkage.get("substrate_detection_record_ids"),
            None,
        )
        source_system = (
            "wazuh"
            if self._reconciliation_is_wazuh_origin(reconciliation)
            else (
                "wazuh"
                if "wazuh" in source_systems
                else (source_systems[0] if source_systems else "wazuh")
            )
        )
        latest_reconciliation_payload = _redacted_reconciliation_payload(
            reconciliation
        )
        lineage = {
            "finding_id": alert.finding_id,
            "analytic_signal_id": alert.analytic_signal_id,
            "case_id": alert.case_id,
            "reconciliation_id": reconciliation.reconciliation_id,
            "correlation_key": reconciliation.correlation_key,
            "source_systems": source_systems,
            "substrate_detection_record_ids": substrate_detection_record_ids,
            "accountable_source_identities": self._merge_linked_ids(
                reconciliation.subject_linkage.get("accountable_source_identities"),
                None,
            ),
            "evidence_ids": tuple(evidence.evidence_id for evidence in evidence_records),
            "first_seen_at": reconciliation.first_seen_at,
            "last_seen_at": reconciliation.last_seen_at,
        }

        return AlertDetailSnapshot(
            read_only=True,
            alert_id=alert.alert_id,
            alert=_record_to_dict(alert),
            case_record=_record_to_dict(case_record) if case_record is not None else None,
            analytic_signal_record=(
                _record_to_dict(analytic_signal_record)
                if analytic_signal_record is not None
                else None
            ),
            latest_reconciliation=latest_reconciliation_payload,
            linked_evidence_records=tuple(
                _record_to_dict(evidence) for evidence in evidence_records
            ),
            reviewed_context=dict(alert.reviewed_context),
            review_state=self._alert_review_state(alert),
            escalation_boundary=self._alert_escalation_boundary(alert),
            source_system=source_system,
            native_rule=(
                dict(reconciliation.subject_linkage.get("latest_native_rule"))
                if isinstance(reconciliation.subject_linkage.get("latest_native_rule"), Mapping)
                else None
            ),
            provenance=_normalize_admission_provenance(
                reconciliation.subject_linkage.get("admission_provenance")
            ),
            lineage=lineage,
        )

    def inspect_assistant_context(
        self,
        record_family: str,
        record_id: str,
    ) -> AnalystAssistantContextSnapshot:
        return self._assistant_context_assembler.inspect_assistant_context(
            record_family,
            record_id,
        )

    def inspect_case_detail(self, case_id: str) -> CaseDetailSnapshot:
        case = self._require_phase19_operator_case(case_id)
        case_id = case.case_id
        context_snapshot = self.inspect_assistant_context("case", case_id)
        observation_records = tuple(
            _record_to_dict(record)
            for record in self._observations_for_case(case_id)
        )
        lead_records = tuple(
            _record_to_dict(record)
            for record in self._leads_for_case(case_id)
        )
        return CaseDetailSnapshot(
            read_only=True,
            case_id=case_id,
            case_record=dict(context_snapshot.record),
            advisory_output=dict(context_snapshot.advisory_output),
            reviewed_context=dict(context_snapshot.reviewed_context),
            linked_alert_ids=context_snapshot.linked_alert_ids,
            linked_observation_ids=tuple(
                record["observation_id"] for record in observation_records
            ),
            linked_lead_ids=tuple(record["lead_id"] for record in lead_records),
            linked_evidence_ids=context_snapshot.linked_evidence_ids,
            linked_recommendation_ids=context_snapshot.linked_recommendation_ids,
            linked_reconciliation_ids=context_snapshot.linked_reconciliation_ids,
            linked_alert_records=context_snapshot.linked_alert_records,
            linked_observation_records=observation_records,
            linked_lead_records=lead_records,
            linked_evidence_records=context_snapshot.linked_evidence_records,
            linked_recommendation_records=context_snapshot.linked_recommendation_records,
            linked_reconciliation_records=context_snapshot.linked_reconciliation_records,
        )

    def record_case_observation(
        self,
        *,
        case_id: str,
        author_identity: str,
        observed_at: datetime,
        scope_statement: str,
        supporting_evidence_ids: tuple[str, ...] = (),
        observation_id: str | None = None,
        lifecycle_state: str = "confirmed",
    ) -> ObservationRecord:
        case = self._require_case_record(case_id)
        author_identity = self._require_non_empty_string(
            author_identity,
            "author_identity",
        )
        observed_at = self._require_aware_datetime(observed_at, "observed_at")
        scope_statement = self._require_non_empty_string(
            scope_statement,
            "scope_statement",
        )
        lifecycle_state = self._require_non_empty_string(
            lifecycle_state,
            "lifecycle_state",
        )
        normalized_evidence_ids = self._normalize_linked_record_ids(
            supporting_evidence_ids,
            "supporting_evidence_ids",
        )
        with self._store.transaction():
            case = self._require_phase19_operator_case(case_id)
            self._validate_case_evidence_linkage(
                case=case,
                evidence_ids=normalized_evidence_ids,
                field_name="supporting_evidence_ids",
            )
            resolved_observation_id = self._resolve_new_record_identifier(
                ObservationRecord,
                observation_id,
                "observation_id",
                "observation",
            )
            return self.persist_record(
                ObservationRecord(
                    observation_id=resolved_observation_id,
                    hunt_id=None,
                    hunt_run_id=None,
                    alert_id=case.alert_id,
                    case_id=case.case_id,
                    supporting_evidence_ids=normalized_evidence_ids,
                    author_identity=author_identity,
                    observed_at=observed_at,
                    scope_statement=scope_statement,
                    lifecycle_state=lifecycle_state,
                )
            )

    def record_case_lead(
        self,
        *,
        case_id: str,
        triage_owner: str,
        triage_rationale: str,
        observation_id: str | None = None,
        lead_id: str | None = None,
        lifecycle_state: str = "triaged",
    ) -> LeadRecord:
        triage_owner = self._require_non_empty_string(triage_owner, "triage_owner")
        triage_rationale = self._require_non_empty_string(
            triage_rationale,
            "triage_rationale",
        )
        lifecycle_state = self._require_non_empty_string(
            lifecycle_state,
            "lifecycle_state",
        )
        resolved_observation_id = self._normalize_optional_string(
            observation_id,
            "observation_id",
        )
        with self._store.transaction():
            case = self._require_phase19_operator_case(case_id)
            if resolved_observation_id is not None:
                observation = self._store.get(ObservationRecord, resolved_observation_id)
                if observation is None:
                    raise LookupError(f"Missing observation {resolved_observation_id!r}")
                if observation.case_id != case.case_id:
                    raise ValueError(
                        f"Observation {resolved_observation_id!r} is not linked to case "
                        f"{case.case_id!r}"
                    )

            resolved_lead_id = self._resolve_new_record_identifier(
                LeadRecord,
                lead_id,
                "lead_id",
                "lead",
            )
            return self.persist_record(
                LeadRecord(
                    lead_id=resolved_lead_id,
                    observation_id=resolved_observation_id,
                    finding_id=case.finding_id,
                    hunt_run_id=None,
                    alert_id=case.alert_id,
                    case_id=case.case_id,
                    triage_owner=triage_owner,
                    triage_rationale=triage_rationale,
                    lifecycle_state=lifecycle_state,
                )
            )

    def record_case_recommendation(
        self,
        *,
        case_id: str,
        review_owner: str,
        intended_outcome: str,
        lead_id: str | None = None,
        recommendation_id: str | None = None,
        lifecycle_state: str = "under_review",
    ) -> RecommendationRecord:
        review_owner = self._require_non_empty_string(review_owner, "review_owner")
        intended_outcome = self._require_non_empty_string(
            intended_outcome,
            "intended_outcome",
        )
        lifecycle_state = self._require_non_empty_string(
            lifecycle_state,
            "lifecycle_state",
        )
        resolved_lead_id = self._normalize_optional_string(lead_id, "lead_id")
        with self._store.transaction():
            case = self._require_phase19_operator_case(case_id)
            if resolved_lead_id is not None:
                lead = self._store.get(LeadRecord, resolved_lead_id)
                if lead is None:
                    raise LookupError(f"Missing lead {resolved_lead_id!r}")
                if lead.case_id != case.case_id:
                    raise ValueError(
                        f"Lead {resolved_lead_id!r} is not linked to case {case.case_id!r}"
                    )

            resolved_recommendation_id = self._resolve_new_record_identifier(
                RecommendationRecord,
                recommendation_id,
                "recommendation_id",
                "recommendation",
            )
            return self.persist_record(
                RecommendationRecord(
                    recommendation_id=resolved_recommendation_id,
                    lead_id=resolved_lead_id,
                    hunt_run_id=None,
                    alert_id=case.alert_id,
                    case_id=case.case_id,
                    ai_trace_id=None,
                    review_owner=review_owner,
                    intended_outcome=intended_outcome,
                    lifecycle_state=lifecycle_state,
                    reviewed_context=case.reviewed_context,
                )
            )

    def record_case_handoff(
        self,
        *,
        case_id: str,
        handoff_at: datetime,
        handoff_owner: str,
        handoff_note: str,
        follow_up_evidence_ids: tuple[str, ...] = (),
    ) -> CaseRecord:
        case = self._require_case_record(case_id)
        handoff_at = self._require_aware_datetime(handoff_at, "handoff_at")
        handoff_owner = self._require_non_empty_string(
            handoff_owner,
            "handoff_owner",
        )
        handoff_note = self._require_non_empty_string(handoff_note, "handoff_note")
        normalized_evidence_ids = self._normalize_linked_record_ids(
            follow_up_evidence_ids,
            "follow_up_evidence_ids",
        )
        with self._store.transaction():
            case = self._require_phase19_operator_case(case_id)
            self._validate_case_evidence_linkage(
                case=case,
                evidence_ids=normalized_evidence_ids,
                field_name="follow_up_evidence_ids",
            )
            updated_reviewed_context = _merge_reviewed_context(
                case.reviewed_context,
                {
                    "handoff": {
                        "handoff_at": handoff_at.isoformat(),
                        "handoff_owner": handoff_owner,
                        "note": handoff_note,
                        "follow_up_evidence_ids": normalized_evidence_ids,
                    }
                },
            )
            return self.persist_record(
                CaseRecord(
                    case_id=case.case_id,
                    alert_id=case.alert_id,
                    finding_id=case.finding_id,
                    evidence_ids=case.evidence_ids,
                    lifecycle_state=case.lifecycle_state,
                    reviewed_context=updated_reviewed_context,
                )
            )

    def record_case_disposition(
        self,
        *,
        case_id: str,
        disposition: str,
        rationale: str,
        recorded_at: datetime,
    ) -> CaseRecord:
        disposition = self._require_non_empty_string(disposition, "disposition")
        rationale = self._require_non_empty_string(rationale, "rationale")
        recorded_at = self._require_aware_datetime(recorded_at, "recorded_at")
        lifecycle_state = self._case_lifecycle_for_disposition(disposition)
        with self._store.transaction():
            case = self._require_phase19_operator_case(case_id)
            updated_reviewed_context = _merge_reviewed_context(
                case.reviewed_context,
                {
                    "triage": {
                        "disposition": disposition,
                        "closure_rationale": rationale,
                        "recorded_at": recorded_at.isoformat(),
                    }
                },
            )
            updated_case = self.persist_record(
                CaseRecord(
                    case_id=case.case_id,
                    alert_id=case.alert_id,
                    finding_id=case.finding_id,
                    evidence_ids=case.evidence_ids,
                    lifecycle_state=lifecycle_state,
                    reviewed_context=updated_reviewed_context,
                )
            )
            if case.alert_id is not None and lifecycle_state == "closed":
                alert = self._store.get(AlertRecord, case.alert_id)
                if alert is not None:
                    self.persist_record(
                        AlertRecord(
                            alert_id=alert.alert_id,
                            finding_id=alert.finding_id,
                            analytic_signal_id=alert.analytic_signal_id,
                            case_id=alert.case_id,
                            lifecycle_state="closed",
                            reviewed_context=_merge_reviewed_context(
                                alert.reviewed_context,
                                {"triage": updated_reviewed_context.get("triage", {})},
                            ),
                        )
                    )
        return updated_case

    def inspect_advisory_output(
        self,
        record_family: str,
        record_id: str,
    ) -> AdvisoryInspectionSnapshot:
        return self._assistant_context_assembler.inspect_advisory_output(
            record_family,
            record_id,
        )

    def render_recommendation_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationDraftSnapshot:
        return self._assistant_context_assembler.render_recommendation_draft(
            record_family,
            record_id,
        )

    def create_reviewed_action_request_from_advisory(
        self,
        *,
        record_family: str,
        record_id: str,
        requester_identity: str,
        recipient_identity: str,
        message_intent: str,
        escalation_reason: str,
        expires_at: datetime,
        action_request_id: str | None = None,
    ) -> ActionRequestRecord:
        return self._execution_coordinator.create_reviewed_action_request_from_advisory(
            record_family=record_family,
            record_id=record_id,
            requester_identity=requester_identity,
            recipient_identity=recipient_identity,
            message_intent=message_intent,
            escalation_reason=escalation_reason,
            expires_at=expires_at,
            action_request_id=action_request_id,
        )

    def attach_assistant_advisory_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationRecord | AITraceRecord:
        record_family = self._require_non_empty_string(record_family, "record_family")
        record_id = self._require_non_empty_string(record_id, "record_id")
        if record_family not in {"recommendation", "ai_trace"}:
            raise ValueError(
                "assistant advisory drafts may only be attached to "
                "'recommendation' or 'ai_trace' records"
            )

        record_type = RECORD_TYPES_BY_FAMILY[record_family]
        record = self._store.get(record_type, record_id)
        if record is None:
            raise LookupError(
                f"Missing {record_family} record {record_id!r} for advisory draft attachment"
            )
        if not isinstance(record, (RecommendationRecord, AITraceRecord)):
            raise TypeError(
                "assistant advisory drafts may only be attached to recommendation "
                "or ai_trace records"
            )

        draft_snapshot = self.render_recommendation_draft(record_family, record_id)
        attached_draft = {
            "draft_id": f"assistant-advisory-draft:{record_family}:{record_id}",
            "source_record_family": record_family,
            "source_record_id": record_id,
            "review_lifecycle_state": record.lifecycle_state,
            **draft_snapshot.recommendation_draft,
            "linked_alert_ids": draft_snapshot.linked_alert_ids,
            "linked_case_ids": draft_snapshot.linked_case_ids,
            "linked_evidence_ids": draft_snapshot.linked_evidence_ids,
            "linked_recommendation_ids": draft_snapshot.linked_recommendation_ids,
            "linked_reconciliation_ids": draft_snapshot.linked_reconciliation_ids,
        }
        current_attached_draft = _assistant_advisory_draft_without_revision_history(
            record.assistant_advisory_draft
        )
        if current_attached_draft == attached_draft:
            return record
        revision_history = _assistant_advisory_draft_revision_history(
            record.assistant_advisory_draft
        )
        if current_attached_draft:
            attached_draft["revision_history"] = (
                *revision_history,
                current_attached_draft,
            )
        return self.persist_record(
            replace(record, assistant_advisory_draft=attached_draft)
        )

    def _reconciliation_has_detection_lineage(
        self, record: ReconciliationRecord
    ) -> bool:
        return any(
            (
                record.analytic_signal_id is not None,
                bool(
                    self._merge_linked_ids(
                        record.subject_linkage.get("analytic_signal_ids"),
                        None,
                    )
                ),
                bool(
                    self._merge_linked_ids(
                        record.subject_linkage.get("substrate_detection_record_ids"),
                        None,
                    )
                ),
                bool(
                    self._merge_linked_ids(
                        record.subject_linkage.get("source_systems"),
                        None,
                    )
                ),
            )
        )

    def _latest_detection_reconciliation_for_alert(
        self,
        alert_id: str,
    ) -> ReconciliationRecord | None:
        latest: ReconciliationRecord | None = None
        for record in self._store.list(ReconciliationRecord):
            if (
                record.alert_id != alert_id
                or not self._reconciliation_has_detection_lineage(record)
                or not self._reconciliation_is_wazuh_origin(record)
            ):
                continue
            if latest is None or (
                record.compared_at,
                record.reconciliation_id,
            ) > (
                latest.compared_at,
                latest.reconciliation_id,
            ):
                latest = record
        return latest

    def _latest_detection_reconciliations_by_alert_id(
        self,
    ) -> dict[str, ReconciliationRecord]:
        latest_by_alert_id: dict[str, ReconciliationRecord] = {}
        for record in self._store.list(ReconciliationRecord):
            if (
                record.alert_id is None
                or not self._reconciliation_has_detection_lineage(record)
                or not self._reconciliation_is_wazuh_origin(record)
            ):
                continue
            current = latest_by_alert_id.get(record.alert_id)
            if current is None or (
                record.compared_at,
                record.reconciliation_id,
            ) > (
                current.compared_at,
                current.reconciliation_id,
            ):
                latest_by_alert_id[record.alert_id] = record
        return latest_by_alert_id

    def _reconciliation_is_wazuh_origin(self, record: ReconciliationRecord) -> bool:
        source_systems = self._merge_linked_ids(
            record.subject_linkage.get("source_systems"),
            None,
        )
        substrate_detection_record_ids = self._merge_linked_ids(
            record.subject_linkage.get("substrate_detection_record_ids"),
            None,
        )
        normalized_source_systems = tuple(
            source_system.strip().lower() for source_system in source_systems
        )
        normalized_substrate_detection_record_ids = tuple(
            detection_id.strip().lower()
            for detection_id in substrate_detection_record_ids
        )
        return "wazuh" in normalized_source_systems or any(
            detection_id.startswith("wazuh:")
            for detection_id in normalized_substrate_detection_record_ids
        )

    @staticmethod
    def _assistant_ids_from_value(value: object) -> tuple[str, ...]:
        if isinstance(value, str):
            return (value,)
        if isinstance(value, (list, tuple)):
            return tuple(item for item in value if isinstance(item, str))
        return ()

    @staticmethod
    def _assistant_ids_from_mapping(
        mapping: Mapping[str, object],
        key: str,
    ) -> tuple[str, ...]:
        return AegisOpsControlPlaneService._assistant_ids_from_value(mapping.get(key))

    @staticmethod
    def _assistant_merge_ids(
        existing_values: object,
        incoming_values: object,
    ) -> tuple[str, ...]:
        merged = AegisOpsControlPlaneService._merge_linked_ids(existing_values, None)
        if isinstance(incoming_values, (list, tuple)):
            for value in incoming_values:
                merged = AegisOpsControlPlaneService._merge_linked_ids(merged, value)
        else:
            merged = AegisOpsControlPlaneService._merge_linked_ids(
                merged,
                incoming_values if isinstance(incoming_values, str) else None,
            )
        return merged

    def _assistant_action_lineage_ids(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        action_request_ids = self._assistant_ids_from_value(
            getattr(record, "action_request_id", None)
        )
        approval_decision_ids = self._assistant_ids_from_value(
            getattr(record, "approval_decision_id", None)
        )
        action_execution_ids = self._assistant_ids_from_value(
            getattr(record, "action_execution_id", None)
        )
        delegation_ids = self._assistant_ids_from_value(getattr(record, "delegation_id", None))
        if isinstance(record, ReconciliationRecord):
            action_request_ids = self._assistant_merge_ids(
                action_request_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "action_request_ids",
                ),
            )
            approval_decision_ids = self._assistant_merge_ids(
                approval_decision_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "approval_decision_ids",
                ),
            )
            action_execution_ids = self._assistant_merge_ids(
                action_execution_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "action_execution_ids",
                ),
            )
            delegation_ids = self._assistant_merge_ids(
                delegation_ids,
                self._assistant_ids_from_mapping(
                    record.subject_linkage,
                    "delegation_ids",
                ),
            )
        return (
            action_request_ids,
            approval_decision_ids,
            action_execution_ids,
            delegation_ids,
        )

    def _assistant_merge_action_request_linkage(
        self,
        *,
        linked_alert_ids: tuple[str, ...],
        linked_case_ids: tuple[str, ...],
        linked_finding_ids: tuple[str, ...],
        action_request: ActionRequestRecord,
    ) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
        return (
            self._assistant_merge_ids(linked_alert_ids, action_request.alert_id),
            self._assistant_merge_ids(linked_case_ids, action_request.case_id),
            self._assistant_merge_ids(linked_finding_ids, action_request.finding_id),
        )

    def _assistant_action_execution_for_delegation_id(
        self,
        delegation_id: str,
    ) -> ActionExecutionRecord | None:
        for execution in self._store.list(ActionExecutionRecord):
            if execution.delegation_id == delegation_id:
                return execution
        return None

    def _assistant_ai_trace_records_for_context(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[AITraceRecord, ...]:
        records: list[AITraceRecord] = []
        seen_trace_ids: set[str] = set()

        def add_trace(trace: AITraceRecord | None) -> None:
            if trace is None or trace.ai_trace_id in seen_trace_ids:
                return
            seen_trace_ids.add(trace.ai_trace_id)
            records.append(trace)

        ai_trace_id = getattr(record, "ai_trace_id", None)
        if ai_trace_id is not None:
            add_trace(self._store.get(AITraceRecord, ai_trace_id))
        if isinstance(record, AITraceRecord):
            add_trace(record)

        record_recommendation_id = getattr(record, "recommendation_id", None)
        if record_recommendation_id is not None:
            for trace in self._store.list(AITraceRecord):
                if trace.ai_trace_id in seen_trace_ids:
                    continue
                if record_recommendation_id in self._assistant_ids_from_mapping(
                    trace.subject_linkage,
                    "recommendation_ids",
                ):
                    add_trace(trace)

        return tuple(records)

    def _assistant_ai_trace_evidence_ids(
        self,
        ai_trace_record: AITraceRecord,
    ) -> tuple[str, ...]:
        linked_evidence_ids = self._assistant_ids_from_mapping(
            ai_trace_record.subject_linkage,
            "evidence_ids",
        )
        linked_evidence_ids = self._assistant_merge_ids(
            linked_evidence_ids,
            ai_trace_record.material_input_refs,
        )
        return tuple(
            evidence_id
            for evidence_id in linked_evidence_ids
            if self._store.get(EvidenceRecord, evidence_id) is not None
        )

    def _assistant_linked_evidence_ids(self, record: ControlPlaneRecord) -> tuple[str, ...]:
        linked_evidence_ids = self._assistant_ids_from_value(getattr(record, "evidence_ids", ()))
        linked_evidence_ids = self._assistant_merge_ids(
            linked_evidence_ids,
            getattr(record, "supporting_evidence_ids", ()),
        )
        if isinstance(record, ActionExecutionRecord):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ids_from_mapping(record.provenance, "evidence_ids"),
            )
        if isinstance(record, ReconciliationRecord):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ids_from_mapping(record.subject_linkage, "evidence_ids"),
            )
        for ai_trace_record in self._assistant_ai_trace_records_for_context(record):
            linked_evidence_ids = self._assistant_merge_ids(
                linked_evidence_ids,
                self._assistant_ai_trace_evidence_ids(ai_trace_record),
            )
        return linked_evidence_ids

    def _assistant_evidence_siblings(self, record: EvidenceRecord) -> tuple[str, ...]:
        evidence_records = self._assistant_evidence_records_for_context(
            alert_ids=self._assistant_ids_from_value(record.alert_id),
            case_ids=self._assistant_ids_from_value(record.case_id),
            evidence_ids=(),
            exclude_evidence_id=record.evidence_id,
        )
        return tuple(evidence.evidence_id for evidence in evidence_records)

    def _assistant_evidence_records_for_context(
        self,
        *,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_evidence_id: str | None,
    ) -> tuple[EvidenceRecord, ...]:
        records: list[EvidenceRecord] = []
        seen_ids: set[str] = set()
        for evidence_id in evidence_ids:
            evidence = self._store.get(EvidenceRecord, evidence_id)
            if evidence is None:
                continue
            if exclude_evidence_id is not None and evidence.evidence_id == exclude_evidence_id:
                continue
            if evidence.evidence_id in seen_ids:
                continue
            seen_ids.add(evidence.evidence_id)
            records.append(evidence)
        for evidence in self._store.list(EvidenceRecord):
            if exclude_evidence_id is not None and evidence.evidence_id == exclude_evidence_id:
                continue
            if evidence.evidence_id in seen_ids:
                continue
            if evidence.alert_id in alert_ids or (
                evidence.case_id is not None and evidence.case_id in case_ids
            ):
                seen_ids.add(evidence.evidence_id)
                records.append(evidence)
        records.sort(key=lambda evidence: evidence.evidence_id)
        return tuple(records)

    def _assistant_recommendation_records_for_context(
        self,
        *,
        record: ControlPlaneRecord,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        ai_trace_records: tuple[AITraceRecord, ...],
        exclude_recommendation_id: str | None,
    ) -> tuple[RecommendationRecord, ...]:
        records: list[RecommendationRecord] = []
        lead_id = getattr(record, "lead_id", None)
        hunt_run_id = getattr(record, "hunt_run_id", None)
        ai_trace_id = getattr(record, "ai_trace_id", None)
        ai_trace_recommendation_ids: set[str] = set()
        for ai_trace_record in ai_trace_records:
            ai_trace_recommendation_ids.update(
                self._assistant_ids_from_mapping(
                    ai_trace_record.subject_linkage,
                    "recommendation_ids",
                )
            )
        for recommendation in self._store.list(RecommendationRecord):
            if (
                exclude_recommendation_id is not None
                and recommendation.recommendation_id == exclude_recommendation_id
            ):
                continue
            if recommendation.alert_id in alert_ids:
                records.append(recommendation)
                continue
            if recommendation.case_id is not None and recommendation.case_id in case_ids:
                records.append(recommendation)
                continue
            if lead_id is not None and recommendation.lead_id == lead_id:
                records.append(recommendation)
                continue
            if hunt_run_id is not None and recommendation.hunt_run_id == hunt_run_id:
                records.append(recommendation)
                continue
            if ai_trace_id is not None and recommendation.ai_trace_id == ai_trace_id:
                records.append(recommendation)
                continue
            if recommendation.recommendation_id in ai_trace_recommendation_ids:
                records.append(recommendation)
        records.sort(key=lambda recommendation: recommendation.recommendation_id)
        return tuple(records)

    def _assistant_reconciliation_records_for_context(
        self,
        *,
        record: ControlPlaneRecord,
        alert_ids: tuple[str, ...],
        case_ids: tuple[str, ...],
        finding_ids: tuple[str, ...],
        evidence_ids: tuple[str, ...],
        exclude_reconciliation_id: str | None,
    ) -> tuple[ReconciliationRecord, ...]:
        records: list[ReconciliationRecord] = []
        analytic_signal_id = getattr(record, "analytic_signal_id", None)
        finding_id = getattr(record, "finding_id", None)
        (
            action_request_ids,
            approval_decision_ids,
            action_execution_ids,
            delegation_ids,
        ) = self._assistant_action_lineage_ids(record)
        linked_finding_ids = set(finding_ids)
        for reconciliation in self._store.list(ReconciliationRecord):
            if (
                exclude_reconciliation_id is not None
                and reconciliation.reconciliation_id == exclude_reconciliation_id
            ):
                continue
            subject_action_request_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_request_ids",
            )
            if any(
                action_request_id in subject_action_request_ids
                for action_request_id in action_request_ids
            ):
                records.append(reconciliation)
                continue
            subject_approval_decision_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            )
            if any(
                approval_decision_id in subject_approval_decision_ids
                for approval_decision_id in approval_decision_ids
            ):
                records.append(reconciliation)
                continue
            subject_action_execution_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            )
            if any(
                action_execution_id in subject_action_execution_ids
                for action_execution_id in action_execution_ids
            ):
                records.append(reconciliation)
                continue
            subject_delegation_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "delegation_ids",
            )
            if any(
                delegation_id in subject_delegation_ids
                for delegation_id in delegation_ids
            ):
                records.append(reconciliation)
                continue
            if reconciliation.alert_id is not None and reconciliation.alert_id in alert_ids:
                records.append(reconciliation)
                continue
            if (
                analytic_signal_id is not None
                and reconciliation.analytic_signal_id == analytic_signal_id
            ):
                records.append(reconciliation)
                continue
            subject_alert_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "alert_ids",
            )
            if any(alert_id in subject_alert_ids for alert_id in alert_ids):
                records.append(reconciliation)
                continue
            subject_analytic_signal_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "analytic_signal_ids",
            )
            if (
                analytic_signal_id is not None
                and analytic_signal_id in subject_analytic_signal_ids
            ):
                records.append(reconciliation)
                continue
            if finding_id is not None and reconciliation.finding_id == finding_id:
                records.append(reconciliation)
                continue
            if (
                reconciliation.finding_id is not None
                and reconciliation.finding_id in linked_finding_ids
            ):
                records.append(reconciliation)
                continue
            subject_finding_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "finding_ids",
            )
            if any(finding_id in subject_finding_ids for finding_id in linked_finding_ids):
                records.append(reconciliation)
                continue
            subject_case_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "case_ids",
            )
            if any(case_id in subject_case_ids for case_id in case_ids):
                records.append(reconciliation)
                continue
            subject_evidence_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "evidence_ids",
            )
            if any(evidence_id in subject_evidence_ids for evidence_id in evidence_ids):
                records.append(reconciliation)
        records.sort(key=lambda reconciliation: reconciliation.reconciliation_id)
        return tuple(records)

    @staticmethod
    def _require_aware_datetime(value: object, field_name: str) -> datetime:
        if not isinstance(value, datetime):
            raise ValueError(f"{field_name} must be a datetime")
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(f"{field_name} must be timezone-aware")
        return value

    @staticmethod
    def _require_non_empty_string(value: object, field_name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty string")
        return value

    @staticmethod
    def _normalize_optional_string(value: object, field_name: str) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str):
            raise ValueError(f"{field_name} must be a string when provided")
        if not value.strip():
            return None
        return value

    def _resolve_new_record_identifier(
        self,
        record_type: Type[RecordT],
        requested_id: object,
        field_name: str,
        prefix: str,
    ) -> str:
        normalized_id = self._normalize_optional_string(requested_id, field_name)
        if normalized_id is None:
            generated_id = self._next_identifier(prefix)
            if self._store.get(record_type, generated_id) is not None:
                raise ValueError(f"{field_name} {generated_id!r} already exists")
            return generated_id
        if self._store.get(record_type, normalized_id) is not None:
            raise ValueError(f"{field_name} {normalized_id!r} already exists")
        return normalized_id

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
        reviewed_context: Mapping[str, object] | None = None,
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
                reviewed_context=reviewed_context or {},
            )
        )

    def promote_alert_to_case(
        self,
        alert_id: str,
        *,
        case_id: str | None = None,
        case_lifecycle_state: str = "open",
    ) -> CaseRecord:
        alert_id = self._require_non_empty_string(alert_id, "alert_id")
        requested_case_id = self._normalize_optional_string(case_id, "case_id")
        case_lifecycle_state = self._require_non_empty_string(
            case_lifecycle_state,
            "case_lifecycle_state",
        )
        with self._store.transaction():
            alert = self._store.get(AlertRecord, alert_id)
            if alert is None:
                raise LookupError(f"Missing alert {alert_id!r}")

            if alert.case_id is not None:
                resolved_case_id = alert.case_id
                if (
                    requested_case_id is not None
                    and requested_case_id != resolved_case_id
                ):
                    raise ValueError(
                        f"Alert {alert_id!r} is already linked to case {resolved_case_id!r}"
                    )
            else:
                resolved_case_id = requested_case_id or self._next_identifier("case")

            evidence_records = self._list_alert_evidence_records(
                alert_id=alert.alert_id,
                case_id=resolved_case_id,
            )
            if not evidence_records:
                raise ValueError(
                    f"Alert {alert_id!r} has no linked evidence to promote into a case"
                )

            merged_evidence_ids: tuple[str, ...] = ()
            for evidence in evidence_records:
                merged_evidence_ids = self._merge_linked_ids(
                    merged_evidence_ids,
                    evidence.evidence_id,
                )
                updated_lifecycle_state = (
                    "linked"
                    if evidence.lifecycle_state == "collected"
                    else evidence.lifecycle_state
                )
                if (
                    evidence.case_id == resolved_case_id
                    and updated_lifecycle_state == evidence.lifecycle_state
                ):
                    continue
                self.persist_record(
                    EvidenceRecord(
                        evidence_id=evidence.evidence_id,
                        source_record_id=evidence.source_record_id,
                        alert_id=evidence.alert_id,
                        case_id=resolved_case_id,
                        source_system=evidence.source_system,
                        collector_identity=evidence.collector_identity,
                        acquired_at=evidence.acquired_at,
                        derivation_relationship=evidence.derivation_relationship,
                        lifecycle_state=updated_lifecycle_state,
                    )
                )

            existing_case = self._store.get(CaseRecord, resolved_case_id)
            if existing_case is not None:
                if (
                    existing_case.alert_id is not None
                    and existing_case.alert_id != alert.alert_id
                ):
                    raise ValueError(
                        f"Case {resolved_case_id!r} is already linked to alert {existing_case.alert_id!r}"
                    )
                if (
                    existing_case.finding_id is not None
                    and existing_case.finding_id != alert.finding_id
                ):
                    raise ValueError(
                        f"Case {resolved_case_id!r} is already linked to finding {existing_case.finding_id!r}"
                    )
            merged_case_evidence_ids = self._merge_linked_ids(
                existing_case.evidence_ids if existing_case is not None else (),
                None,
            )
            for evidence_id in merged_evidence_ids:
                merged_case_evidence_ids = self._merge_linked_ids(
                    merged_case_evidence_ids,
                    evidence_id,
                )

            promoted_case = self.persist_record(
                CaseRecord(
                    case_id=resolved_case_id,
                    alert_id=alert.alert_id,
                    finding_id=alert.finding_id,
                    evidence_ids=merged_case_evidence_ids,
                    lifecycle_state=(
                        existing_case.lifecycle_state
                        if existing_case is not None
                        else case_lifecycle_state
                    ),
                    reviewed_context=_merge_reviewed_context(
                        existing_case.reviewed_context if existing_case is not None else {},
                        alert.reviewed_context,
                    ),
                )
            )
            promoted_alert = self.persist_record(
                AlertRecord(
                    alert_id=alert.alert_id,
                    finding_id=alert.finding_id,
                    analytic_signal_id=alert.analytic_signal_id,
                    case_id=promoted_case.case_id,
                    lifecycle_state="escalated_to_case",
                    reviewed_context=alert.reviewed_context,
                )
            )
            if promoted_alert.analytic_signal_id is not None:
                self._link_case_to_analytic_signals(
                    (promoted_alert.analytic_signal_id,),
                    promoted_case.case_id,
                )
            self._link_case_to_alert_reconciliations(
                alert_id=promoted_alert.alert_id,
                case_id=promoted_case.case_id,
                evidence_ids=merged_evidence_ids,
            )
            return promoted_case

    def ingest_native_detection_record(
        self,
        adapter: NativeDetectionRecordAdapter,
        record: NativeDetectionRecord,
    ) -> FindingAlertIngestResult:
        record = self._with_native_detection_admission_provenance(
            record,
            admission_kind="replay",
            admission_channel="fixture_replay",
        )
        adapter_substrate_key = self._require_non_empty_string(
            adapter.substrate_key,
            "adapter.substrate_key",
        )
        record_substrate_key = self._require_non_empty_string(
            record.substrate_key,
            "record.substrate_key",
        )
        if record_substrate_key != adapter_substrate_key:
            raise ValueError(
                "native detection record substrate does not match adapter boundary "
                f"({record_substrate_key!r} != {adapter_substrate_key!r})"
            )
        admission = adapter.build_analytic_signal_admission(record)
        admission_provenance = _normalize_admission_provenance(
            record.metadata.get("admission_provenance")
        )
        if admission_provenance is not None:
            admission = AnalyticSignalAdmission(
                finding_id=admission.finding_id,
                analytic_signal_id=admission.analytic_signal_id,
                substrate_detection_record_id=admission.substrate_detection_record_id,
                correlation_key=admission.correlation_key,
                first_seen_at=admission.first_seen_at,
                last_seen_at=admission.last_seen_at,
                materially_new_work=admission.materially_new_work,
                reviewed_context=_merge_reviewed_context(
                    admission.reviewed_context,
                    {"provenance": admission_provenance},
                ),
            )
        raw_substrate_detection_record_id = self._require_non_empty_string(
            admission.substrate_detection_record_id or record.native_record_id,
            "substrate_detection_record_id/native_record_id",
        )
        substrate_detection_record_id = self._normalize_substrate_detection_record_id(
            record_substrate_key,
            raw_substrate_detection_record_id,
        )
        admission = AnalyticSignalAdmission(
            finding_id=admission.finding_id,
            analytic_signal_id=admission.analytic_signal_id,
            substrate_detection_record_id=substrate_detection_record_id,
            correlation_key=admission.correlation_key,
            first_seen_at=admission.first_seen_at,
            last_seen_at=admission.last_seen_at,
            materially_new_work=admission.materially_new_work,
            reviewed_context=admission.reviewed_context,
        )
        with self._store.transaction():
            result = self._ingest_analytic_signal_admission(admission)
            return self._attach_native_detection_context(
                record=record,
                ingest_result=result,
                substrate_detection_record_id=substrate_detection_record_id,
            )

    def _ingest_analytic_signal_admission(
        self,
        admission: AnalyticSignalAdmission,
    ) -> FindingAlertIngestResult:
        finding_id = self._require_non_empty_string(
            admission.finding_id,
            "finding_id",
        )
        analytic_signal_id = self._normalize_optional_string(
            admission.analytic_signal_id,
            "analytic_signal_id",
        )
        substrate_detection_record_id = self._normalize_optional_string(
            admission.substrate_detection_record_id,
            "substrate_detection_record_id",
        )
        correlation_key = self._require_non_empty_string(
            admission.correlation_key,
            "correlation_key",
        )
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
        reviewed_context = _merge_reviewed_context({}, admission.reviewed_context)

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
        analytic_signal_id = self._resolve_analytic_signal_id(
            analytic_signal_id=analytic_signal_id,
            finding_id=finding_id,
            correlation_key=correlation_key,
            substrate_detection_record_id=substrate_detection_record_id,
            latest_reconciliation=latest_reconciliation,
        )

        if latest_reconciliation is None:
            alert = self.persist_record(
                AlertRecord(
                    alert_id=self._next_identifier("alert"),
                    finding_id=finding_id,
                    analytic_signal_id=analytic_signal_id,
                    case_id=None,
                    lifecycle_state="new",
                    reviewed_context=reviewed_context,
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
            linked_case_ids = self._merge_linked_ids((), alert.case_id)
            persisted_first_seen = first_seen_at
            persisted_last_seen = last_seen_at
        else:
            alert = self._store.get(AlertRecord, latest_reconciliation.alert_id)
            if alert is None:
                raise LookupError(
                    f"Missing alert {latest_reconciliation.alert_id!r} for correlation key {correlation_key!r}"
                )
            merged_reviewed_context = _merge_reviewed_context(
                alert.reviewed_context,
                admission.reviewed_context,
            )
            existing_finding_ids = latest_reconciliation.subject_linkage.get("finding_ids")
            existing_signal_ids = latest_reconciliation.subject_linkage.get(
                "analytic_signal_ids"
            )
            existing_substrate_detection_ids = latest_reconciliation.subject_linkage.get(
                "substrate_detection_record_ids"
            )
            existing_case_ids = latest_reconciliation.subject_linkage.get("case_ids")
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
            linked_case_ids = self._merge_linked_ids(
                existing_case_ids,
                alert.case_id,
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
                        reviewed_context=merged_reviewed_context,
                    )
                )
                disposition = "updated"
            elif merged_reviewed_context != alert.reviewed_context:
                alert = self.persist_record(
                    AlertRecord(
                        alert_id=alert.alert_id,
                        finding_id=alert.finding_id,
                        analytic_signal_id=alert.analytic_signal_id,
                        case_id=alert.case_id,
                        lifecycle_state=alert.lifecycle_state,
                        reviewed_context=merged_reviewed_context,
                    )
                )
                disposition = "updated"
            elif already_linked:
                disposition = "deduplicated"
            else:
                disposition = "restated"

            if alert.case_id is not None:
                existing_case = self._store.get(CaseRecord, alert.case_id)
                if existing_case is not None:
                    merged_case_reviewed_context = _merge_reviewed_context(
                        existing_case.reviewed_context,
                        alert.reviewed_context,
                    )
                    if merged_case_reviewed_context != existing_case.reviewed_context:
                        self.persist_record(
                            CaseRecord(
                                case_id=existing_case.case_id,
                                alert_id=existing_case.alert_id,
                                finding_id=existing_case.finding_id,
                                evidence_ids=existing_case.evidence_ids,
                                lifecycle_state=existing_case.lifecycle_state,
                                reviewed_context=merged_case_reviewed_context,
                            )
                        )

        if analytic_signal_id is not None:
            existing_signal = self._store.get(AnalyticSignalRecord, analytic_signal_id)
            signal_reviewed_context = _merge_reviewed_context(
                alert.reviewed_context,
                admission.reviewed_context,
            )
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
                    reviewed_context=signal_reviewed_context,
                )
            )

        self._link_case_to_analytic_signals(linked_signal_ids, alert.case_id)

        reconciliation = self.persist_record(
            ReconciliationRecord(
                reconciliation_id=self._next_identifier("reconciliation"),
                subject_linkage={
                    "alert_ids": (alert.alert_id,),
                    "case_ids": linked_case_ids,
                    "substrate_detection_record_ids": linked_substrate_detection_ids,
                    "finding_ids": linked_finding_ids,
                    "analytic_signal_ids": linked_signal_ids,
                },
                alert_id=alert.alert_id,
                finding_id=finding_id,
                analytic_signal_id=analytic_signal_id,
                execution_run_id=None,
                linked_execution_run_ids=(),
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

    def _attach_native_detection_context(
        self,
        *,
        record: NativeDetectionRecord,
        ingest_result: FindingAlertIngestResult,
        substrate_detection_record_id: str,
    ) -> FindingAlertIngestResult:
        source_system = self._normalize_optional_string(
            record.metadata.get("source_system"),
            "metadata.source_system",
        ) or record.substrate_key
        evidence_id = f"evidence-{uuid.uuid5(uuid.NAMESPACE_URL, substrate_detection_record_id)}"
        case_id = ingest_result.alert.case_id
        evidence = self.persist_record(
            EvidenceRecord(
                evidence_id=evidence_id,
                source_record_id=substrate_detection_record_id,
                alert_id=ingest_result.alert.alert_id,
                case_id=case_id,
                source_system=source_system,
                collector_identity=f"{record.substrate_key}-native-detection-adapter",
                acquired_at=self._require_aware_datetime(
                    record.first_seen_at,
                    "record.first_seen_at",
                ),
                derivation_relationship="native_detection_record",
                lifecycle_state="linked" if case_id is not None else "collected",
            )
        )

        if case_id is not None:
            existing_case = self._store.get(CaseRecord, case_id)
            if existing_case is not None:
                merged_case_evidence_ids = self._merge_linked_ids(
                    existing_case.evidence_ids,
                    evidence.evidence_id,
                )
                merged_case_reviewed_context = _merge_reviewed_context(
                    existing_case.reviewed_context,
                    ingest_result.alert.reviewed_context,
                )
                if (
                    merged_case_evidence_ids != existing_case.evidence_ids
                    or merged_case_reviewed_context != existing_case.reviewed_context
                ):
                    self.persist_record(
                        CaseRecord(
                            case_id=existing_case.case_id,
                            alert_id=existing_case.alert_id,
                            finding_id=existing_case.finding_id,
                            evidence_ids=merged_case_evidence_ids,
                            lifecycle_state=existing_case.lifecycle_state,
                            reviewed_context=merged_case_reviewed_context,
                        )
                    )

        subject_linkage = dict(ingest_result.reconciliation.subject_linkage)
        subject_linkage["evidence_ids"] = self._merge_linked_ids(
            subject_linkage.get("evidence_ids"),
            evidence.evidence_id,
        )
        subject_linkage["source_systems"] = self._merge_linked_ids(
            subject_linkage.get("source_systems"),
            source_system,
        )

        source_provenance = record.metadata.get("source_provenance")
        if isinstance(source_provenance, Mapping):
            accountable_source_identity = self._normalize_optional_string(
                source_provenance.get("accountable_source_identity"),
                "metadata.source_provenance.accountable_source_identity",
            )
            if accountable_source_identity is not None:
                subject_linkage["accountable_source_identities"] = (
                    self._merge_linked_ids(
                        subject_linkage.get("accountable_source_identities"),
                        accountable_source_identity,
                    )
                )

        native_rule = record.metadata.get("native_rule")
        if isinstance(native_rule, Mapping):
            native_rule_id = self._normalize_optional_string(
                native_rule.get("id"),
                "metadata.native_rule.id",
            )
            native_rule_description = self._normalize_optional_string(
                native_rule.get("description"),
                "metadata.native_rule.description",
            )
            rule_level = native_rule.get("level")
            subject_linkage["latest_native_rule"] = {
                "id": native_rule_id,
                "level": rule_level if isinstance(rule_level, int) else None,
                "description": native_rule_description,
            }

        reviewed_correlation_context = record.metadata.get("reviewed_correlation_context")
        if isinstance(reviewed_correlation_context, Mapping):
            subject_linkage["reviewed_correlation_context"] = {
                str(field_name): field_value
                for field_name, field_value in reviewed_correlation_context.items()
                if isinstance(field_value, str) and field_value.strip()
            }

        reviewed_source_profile = record.metadata.get("reviewed_source_profile")
        if isinstance(reviewed_source_profile, Mapping):
            subject_linkage["reviewed_source_profile"] = dict(reviewed_source_profile)

        raw_alert = record.metadata.get("raw_alert")
        if isinstance(raw_alert, Mapping):
            subject_linkage["latest_native_payload"] = dict(raw_alert)

        admission_provenance = _normalize_admission_provenance(
            record.metadata.get("admission_provenance")
        )
        if admission_provenance is not None:
            subject_linkage["admission_provenance"] = admission_provenance

        reconciliation = self.persist_record(
            ReconciliationRecord(
                reconciliation_id=ingest_result.reconciliation.reconciliation_id,
                subject_linkage=subject_linkage,
                alert_id=ingest_result.reconciliation.alert_id,
                finding_id=ingest_result.reconciliation.finding_id,
                analytic_signal_id=ingest_result.reconciliation.analytic_signal_id,
                execution_run_id=ingest_result.reconciliation.execution_run_id,
                linked_execution_run_ids=(
                    ingest_result.reconciliation.linked_execution_run_ids
                ),
                correlation_key=ingest_result.reconciliation.correlation_key,
                first_seen_at=ingest_result.reconciliation.first_seen_at,
                last_seen_at=ingest_result.reconciliation.last_seen_at,
                ingest_disposition=ingest_result.reconciliation.ingest_disposition,
                mismatch_summary=ingest_result.reconciliation.mismatch_summary,
                compared_at=ingest_result.reconciliation.compared_at,
                lifecycle_state=ingest_result.reconciliation.lifecycle_state,
            )
        )
        return FindingAlertIngestResult(
            alert=ingest_result.alert,
            reconciliation=reconciliation,
            disposition=ingest_result.disposition,
        )

    def _with_native_detection_admission_provenance(
        self,
        record: NativeDetectionRecord,
        *,
        admission_kind: str,
        admission_channel: str,
    ) -> NativeDetectionRecord:
        if _normalize_admission_provenance(record.metadata.get("admission_provenance")) is not None:
            return record
        metadata = dict(record.metadata)
        metadata["admission_provenance"] = {
            "admission_kind": admission_kind,
            "admission_channel": admission_channel,
        }
        return replace(record, metadata=metadata)

    def reconcile_action_execution(
        self,
        *,
        action_request_id: str,
        execution_surface_type: str,
        execution_surface_id: str,
        observed_executions: tuple[Mapping[str, object], ...],
        compared_at: datetime,
        stale_after: datetime,
    ) -> ReconciliationRecord:
        return self._execution_coordinator.reconcile_action_execution(
            action_request_id=action_request_id,
            execution_surface_type=execution_surface_type,
            execution_surface_id=execution_surface_id,
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
        )

    def _normalize_action_policy_basis(
        self,
        policy_basis: Mapping[str, object],
    ) -> dict[str, str]:
        normalized: dict[str, str] = {}
        for field_name, allowed_values in _ACTION_POLICY_ALLOWED_VALUES.items():
            raw_value = policy_basis.get(field_name)
            value = self._require_non_empty_string(raw_value, f"policy_basis.{field_name}")
            if value not in allowed_values:
                raise ValueError(
                    f"policy_basis.{field_name} must be one of {list(allowed_values)!r}"
                )
            normalized[field_name] = value
        return normalized

    def _determine_action_policy(
        self,
        policy_basis: Mapping[str, str],
    ) -> dict[str, str]:
        severity_rank = _ACTION_POLICY_RANKS["severity"][policy_basis["severity"]]
        target_scope_rank = _ACTION_POLICY_RANKS["target_scope"][
            policy_basis["target_scope"]
        ]
        reversibility_rank = _ACTION_POLICY_RANKS["action_reversibility"][
            policy_basis["action_reversibility"]
        ]
        blast_radius_rank = _ACTION_POLICY_RANKS["blast_radius"][
            policy_basis["blast_radius"]
        ]
        highest_criticality_rank = max(
            _ACTION_POLICY_RANKS["asset_criticality"][
                policy_basis["asset_criticality"]
            ],
            _ACTION_POLICY_RANKS["identity_criticality"][
                policy_basis["identity_criticality"]
            ],
        )
        execution_constraint = policy_basis["execution_constraint"]

        requires_isolated_executor = any(
            (
                execution_constraint == "requires_isolated_executor",
                severity_rank >= _ACTION_POLICY_RANKS["severity"]["critical"],
                reversibility_rank
                >= _ACTION_POLICY_RANKS["action_reversibility"]["irreversible"],
                blast_radius_rank
                >= _ACTION_POLICY_RANKS["blast_radius"]["organization"],
                highest_criticality_rank
                >= _ACTION_POLICY_RANKS["asset_criticality"]["critical"],
                target_scope_rank >= _ACTION_POLICY_RANKS["target_scope"]["organization"],
            )
        )
        if execution_constraint == "isolated_preferred" and any(
            (
                severity_rank >= _ACTION_POLICY_RANKS["severity"]["high"],
                blast_radius_rank >= _ACTION_POLICY_RANKS["blast_radius"]["multi_target"],
                highest_criticality_rank
                >= _ACTION_POLICY_RANKS["asset_criticality"]["high"],
            )
        ):
            requires_isolated_executor = True

        approval_required = any(
            (
                requires_isolated_executor,
                severity_rank >= _ACTION_POLICY_RANKS["severity"]["high"],
                target_scope_rank >= _ACTION_POLICY_RANKS["target_scope"]["multi_identity"],
                reversibility_rank
                >= _ACTION_POLICY_RANKS["action_reversibility"][
                    "bounded_reversible"
                ],
                blast_radius_rank
                >= _ACTION_POLICY_RANKS["blast_radius"]["multi_target"],
                highest_criticality_rank
                >= _ACTION_POLICY_RANKS["asset_criticality"]["high"],
            )
        )

        if requires_isolated_executor:
            execution_surface_type = "executor"
            execution_surface_id = "isolated-executor"
        else:
            execution_surface_type = "automation_substrate"
            execution_surface_id = "shuffle"

        return {
            "approval_requirement": (
                "human_required" if approval_required else "policy_authorized"
            ),
            "routing_target": (
                "approval"
                if approval_required
                else (
                    "shuffle"
                    if execution_surface_type == "automation_substrate"
                    else "executor"
                )
            ),
            "execution_surface_type": execution_surface_type,
            "execution_surface_id": execution_surface_id,
        }

    def _apply_action_policy_evaluation_overrides(
        self,
        *,
        computed_policy_evaluation: Mapping[str, str],
        persisted_policy_evaluation: Mapping[str, object],
    ) -> dict[str, str]:
        merged = dict(computed_policy_evaluation)
        approval_requirement_override = persisted_policy_evaluation.get(
            "approval_requirement_override"
        )
        if approval_requirement_override is None:
            return merged

        normalized_override = self._require_non_empty_string(
            approval_requirement_override,
            "policy_evaluation.approval_requirement_override",
        )
        if normalized_override != "human_required":
            raise ValueError(
                "policy_evaluation.approval_requirement_override must be "
                "'human_required'"
            )

        merged["approval_requirement"] = "human_required"
        merged["routing_target"] = "approval"
        merged["approval_requirement_override"] = normalized_override
        return merged

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

    def _link_case_to_analytic_signals(
        self,
        analytic_signal_ids: tuple[str, ...],
        case_id: str | None,
    ) -> None:
        if case_id is None:
            return

        for analytic_signal_id in analytic_signal_ids:
            existing_signal = self._store.get(AnalyticSignalRecord, analytic_signal_id)
            if existing_signal is None:
                continue
            linked_case_ids = self._merge_linked_ids(existing_signal.case_ids, case_id)
            if linked_case_ids == existing_signal.case_ids:
                continue
            self.persist_record(
                AnalyticSignalRecord(
                    analytic_signal_id=existing_signal.analytic_signal_id,
                    substrate_detection_record_id=(
                        existing_signal.substrate_detection_record_id
                    ),
                    finding_id=existing_signal.finding_id,
                    alert_ids=existing_signal.alert_ids,
                    case_ids=linked_case_ids,
                    correlation_key=existing_signal.correlation_key,
                    first_seen_at=existing_signal.first_seen_at,
                    last_seen_at=existing_signal.last_seen_at,
                    lifecycle_state=existing_signal.lifecycle_state,
                    reviewed_context=existing_signal.reviewed_context,
                )
            )

    def _list_alert_evidence_records(
        self,
        *,
        alert_id: str,
        case_id: str | None,
    ) -> tuple[EvidenceRecord, ...]:
        evidence_records: list[EvidenceRecord] = []
        for evidence in self._store.list(EvidenceRecord):
            if evidence.alert_id == alert_id or (
                case_id is not None and evidence.case_id == case_id
            ):
                evidence_records.append(evidence)
        return tuple(evidence_records)

    def _link_case_to_alert_reconciliations(
        self,
        *,
        alert_id: str,
        case_id: str,
        evidence_ids: tuple[str, ...],
    ) -> None:
        for reconciliation in self._store.list(ReconciliationRecord):
            if reconciliation.alert_id != alert_id:
                continue
            subject_linkage = dict(reconciliation.subject_linkage)
            updated_case_ids = self._merge_linked_ids(
                subject_linkage.get("case_ids"),
                case_id,
            )
            updated_evidence_ids = self._merge_linked_ids(
                subject_linkage.get("evidence_ids"),
                None,
            )
            for evidence_id in evidence_ids:
                updated_evidence_ids = self._merge_linked_ids(
                    updated_evidence_ids,
                    evidence_id,
                )
            if (
                tuple(subject_linkage.get("case_ids", ())) == updated_case_ids
                and tuple(subject_linkage.get("evidence_ids", ()))
                == updated_evidence_ids
            ):
                continue
            subject_linkage["case_ids"] = updated_case_ids
            subject_linkage["evidence_ids"] = updated_evidence_ids
            self.persist_record(
                ReconciliationRecord(
                    reconciliation_id=reconciliation.reconciliation_id,
                    subject_linkage=subject_linkage,
                    alert_id=reconciliation.alert_id,
                    finding_id=reconciliation.finding_id,
                    analytic_signal_id=reconciliation.analytic_signal_id,
                    execution_run_id=reconciliation.execution_run_id,
                    linked_execution_run_ids=(
                        reconciliation.linked_execution_run_ids
                    ),
                    correlation_key=reconciliation.correlation_key,
                    first_seen_at=reconciliation.first_seen_at,
                    last_seen_at=reconciliation.last_seen_at,
                    ingest_disposition=reconciliation.ingest_disposition,
                    mismatch_summary=reconciliation.mismatch_summary,
                    compared_at=reconciliation.compared_at,
                    lifecycle_state=reconciliation.lifecycle_state,
                )
            )

    def _resolve_analytic_signal_id(
        self,
        *,
        analytic_signal_id: str | None,
        finding_id: str,
        correlation_key: str,
        substrate_detection_record_id: str | None,
        latest_reconciliation: ReconciliationRecord | None,
    ) -> str:
        if analytic_signal_id is not None:
            return analytic_signal_id

        existing_signal_ids = self._merge_linked_ids(
            (
                latest_reconciliation.subject_linkage.get("analytic_signal_ids")
                if latest_reconciliation is not None
                else ()
            ),
            None,
        )
        if substrate_detection_record_id is not None:
            for existing_signal_id in existing_signal_ids:
                existing_signal = self._store.get(
                    AnalyticSignalRecord,
                    existing_signal_id,
                )
                if (
                    existing_signal is not None
                    and existing_signal.substrate_detection_record_id
                    == substrate_detection_record_id
                ):
                    return existing_signal_id

        if substrate_detection_record_id is None and len(existing_signal_ids) == 1:
            return existing_signal_ids[0]

        mint_material = "|".join(
            (
                finding_id,
                correlation_key,
                substrate_detection_record_id or "",
            )
        )
        return f"analytic-signal-{uuid.uuid5(uuid.NAMESPACE_URL, mint_material)}"

    def _require_empty_authoritative_restore_target(self) -> None:
        all_record_types = tuple(dict.fromkeys(RECORD_TYPES_BY_FAMILY.values()))
        populated_families = [
            record_type.record_family
            for record_type in all_record_types
            if self._store.list(record_type)
        ]
        if populated_families:
            raise ValueError(
                "authoritative restore target must be empty before restore; found existing "
                f"records for {', '.join(populated_families)}"
            )

    def _validate_authoritative_record_chain_restore(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
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
        case_records = tuple(
            record
            for record in records_by_family.get("case", ())
            if isinstance(record, CaseRecord)
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
        reconciliations = tuple(
            record
            for record in records_by_family.get("reconciliation", ())
            if isinstance(record, ReconciliationRecord)
        )
        for family, records in (
            ("analytic_signal", analytic_signal_records),
            ("alert", alert_records),
            ("evidence", evidence_record_family),
            ("case", case_records),
            ("approval_decision", approval_decision_records),
            ("action_request", action_request_records),
            ("action_execution", action_execution_records),
            ("reconciliation", reconciliations),
        ):
            duplicates = _find_duplicate_strings(
                tuple(
                    getattr(record, _AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY[family])
                    for record in records
                )
            )
            if duplicates:
                raise ValueError(
                    "restore payload contains duplicate "
                    f"{family} identifiers {duplicates!r}"
                    f"{duplicate_restore_count_suffix(family)}"
                )
        duplicate_execution_run_ids = _find_duplicate_strings(
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
        cases = {record.case_id: record for record in case_records}
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
        action_executions_by_run_id = {
            record.execution_run_id: record
            for record in action_execution_records
            if record.execution_run_id is not None
        }

        for alert in alerts.values():
            if alert.analytic_signal_id and alert.analytic_signal_id not in analytic_signals:
                raise ValueError(
                    f"missing analytic_signal record {alert.analytic_signal_id!r} required by alert "
                    f"{alert.alert_id!r}"
                )
            if alert.case_id and alert.case_id not in cases:
                raise ValueError(
                    f"missing case record {alert.case_id!r} required by alert {alert.alert_id!r}"
                )

        for analytic_signal in analytic_signals.values():
            for alert_id in analytic_signal.alert_ids:
                if alert_id not in alerts:
                    raise ValueError(
                        f"missing alert record {alert_id!r} required by analytic signal "
                        f"{analytic_signal.analytic_signal_id!r}"
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

        for case in cases.values():
            if case.alert_id and case.alert_id not in alerts:
                raise ValueError(
                    f"missing alert record {case.alert_id!r} required by case {case.case_id!r}"
                )
            for evidence_id in case.evidence_ids:
                if evidence_id not in evidence_records:
                    raise ValueError(
                        f"missing evidence record {evidence_id!r} required by case {case.case_id!r}"
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

    def _require_case_record(self, case_id: str) -> CaseRecord:
        case_id = self._require_non_empty_string(case_id, "case_id")
        case = self._store.get(CaseRecord, case_id)
        if case is None:
            raise LookupError(f"Missing case {case_id!r}")
        return case

    def _require_phase19_operator_case(self, case_id: str) -> CaseRecord:
        case = self._require_case_record(case_id)
        return self._require_phase19_operator_case_record(case)

    @staticmethod
    def _require_single_linked_case_id(linked_case_ids: tuple[str, ...]) -> str:
        if len(linked_case_ids) != 1:
            raise ValueError(
                "reviewed advisory context must bind exactly one case before creating an action request"
            )
        return linked_case_ids[0]

    @staticmethod
    def _require_single_recommendation_binding(
        *,
        record_family: str,
        record_id: str,
        linked_recommendation_ids: tuple[str, ...],
    ) -> str:
        recommendation_ids = linked_recommendation_ids
        if record_family == "recommendation":
            recommendation_ids = (record_id,)
        if len(recommendation_ids) != 1:
            raise ValueError(
                "reviewed advisory context must bind exactly one recommendation before creating an action request"
            )
        return recommendation_ids[0]

    def _require_phase19_case_scoped_advisory_read(
        self,
        context_snapshot: AnalystAssistantContextSnapshot,
    ) -> None:
        error_message = self._phase19_case_scoped_read_error(
            context_snapshot.record_family,
            context_snapshot.record_id,
        )
        if context_snapshot.record_family == "case":
            self._require_phase19_operator_case(context_snapshot.record_id)
            return
        if not context_snapshot.linked_case_ids:
            raise ValueError(error_message)

        approved_cases: dict[str, CaseRecord] = {}
        for case_id in context_snapshot.linked_case_ids:
            approved_cases[case_id] = self._require_phase19_operator_case(case_id)

        if context_snapshot.record_family == "recommendation":
            self._require_phase19_case_scoped_recommendation_payload(
                context_snapshot.record,
                approved_cases=approved_cases,
                error_message=error_message,
            )
        elif context_snapshot.record_family == "ai_trace":
            subject_linkage = context_snapshot.record.get("subject_linkage")
            if self._phase19_context_explicitly_declares_provenance(subject_linkage) and (
                self._phase19_context_declares_out_of_scope_provenance(subject_linkage)
            ):
                raise ValueError(error_message)
            if not context_snapshot.linked_recommendation_records:
                raise ValueError(error_message)
            for recommendation in context_snapshot.linked_recommendation_records:
                self._require_phase19_case_scoped_recommendation_payload(
                    recommendation,
                    approved_cases=approved_cases,
                    error_message=error_message,
                )

    @staticmethod
    def _phase19_case_scoped_read_error(record_family: str, record_id: str) -> str:
        return (
            f"{record_family} {record_id!r} is outside the approved Phase 19 "
            f"{REVIEWED_PHASE19_LIVE_SLICE_LABEL}"
        )

    def _require_phase19_case_scoped_recommendation_payload(
        self,
        payload: Mapping[str, object],
        *,
        approved_cases: Mapping[str, CaseRecord],
        error_message: str,
    ) -> None:
        case_id = self._normalize_optional_string(payload.get("case_id"), "case_id")
        if case_id is None:
            raise ValueError(error_message)
        approved_case = approved_cases.get(case_id)
        if approved_case is None:
            raise ValueError(error_message)

        alert_id = self._normalize_optional_string(payload.get("alert_id"), "alert_id")
        if alert_id is not None and approved_case.alert_id != alert_id:
            raise ValueError(error_message)

        lead_id = self._normalize_optional_string(payload.get("lead_id"), "lead_id")
        if lead_id is not None:
            lead = self._store.get(LeadRecord, lead_id)
            if lead is None or lead.case_id != case_id:
                raise ValueError(error_message)

        reviewed_context = payload.get("reviewed_context")
        if self._phase19_context_explicitly_declares_provenance(reviewed_context) and (
            self._phase19_context_declares_out_of_scope_provenance(reviewed_context)
        ):
            raise ValueError(error_message)

    def _require_phase19_operator_case_record(self, case: CaseRecord) -> CaseRecord:
        if not self._case_is_in_phase19_operator_slice(case):
            raise ValueError(
                f"Case {case.case_id!r} is outside the approved Phase 19 "
                f"{REVIEWED_PHASE19_LIVE_SLICE_LABEL}"
            )
        return case

    def _case_is_in_phase19_operator_slice(self, case: CaseRecord) -> bool:
        alert_id = self._normalize_optional_string(case.alert_id, "case.alert_id")
        if alert_id is None:
            return False

        alert = self._store.get(AlertRecord, alert_id)
        if alert is None:
            return False
        if alert.case_id != case.case_id:
            return False

        reconciliation = self._latest_detection_reconciliation_for_alert(alert.alert_id)
        if reconciliation is None or not self._reconciliation_is_wazuh_origin(reconciliation):
            return False
        if not self._linked_id_exists(
            reconciliation.subject_linkage.get("alert_ids"),
            alert.alert_id,
        ):
            return False
        if not self._linked_id_exists(
            reconciliation.subject_linkage.get("case_ids"),
            case.case_id,
        ):
            return False

        admission_provenance = (
            _normalize_admission_provenance(
                reconciliation.subject_linkage.get("admission_provenance")
            )
            or _normalize_admission_provenance(case.reviewed_context.get("provenance"))
            or _normalize_admission_provenance(alert.reviewed_context.get("provenance"))
        )
        if admission_provenance != {
            "admission_kind": "live",
            "admission_channel": "live_wazuh_webhook",
        }:
            return False

        return (
            self._phase19_operator_source_family(case.reviewed_context)
            or self._phase19_operator_source_family(alert.reviewed_context)
            or self._phase19_operator_source_family(
                reconciliation.subject_linkage.get("reviewed_source_profile")
            )
        ) in REVIEWED_LIVE_WAZUH_SOURCE_FAMILIES

    @staticmethod
    def _phase19_operator_source_family(context: object) -> str | None:
        if not isinstance(context, Mapping):
            return None

        source_context = context.get("source")
        if isinstance(source_context, Mapping):
            source_family = source_context.get("source_family")
            if isinstance(source_family, str):
                normalized_source_family = source_family.strip()
                if normalized_source_family:
                    return normalized_source_family

        source_family = context.get("source_family")
        if isinstance(source_family, str):
            normalized_source_family = source_family.strip()
            if normalized_source_family:
                return normalized_source_family

        return None

    def _phase19_context_declares_out_of_scope_provenance(self, context: object) -> bool:
        if not isinstance(context, Mapping):
            return True

        source_family = self._phase19_operator_source_family(
            context
        ) or self._phase19_operator_source_family(context.get("reviewed_source_profile"))
        if source_family not in REVIEWED_LIVE_WAZUH_SOURCE_FAMILIES:
            return True

        admission_provenance = _normalize_admission_provenance(
            context.get("provenance")
        ) or _normalize_admission_provenance(context.get("admission_provenance"))
        return (
            admission_provenance is not None
            and admission_provenance
            != {
                "admission_kind": "live",
                "admission_channel": "live_wazuh_webhook",
            }
        )

    @staticmethod
    def _phase19_context_explicitly_declares_provenance(context: object) -> bool:
        if not isinstance(context, Mapping):
            return context is not None
        if "source_family" in context or "source" in context:
            return True
        if "reviewed_source_profile" in context:
            return True
        return "provenance" in context or "admission_provenance" in context

    def _normalize_linked_record_ids(
        self,
        record_ids: tuple[str, ...],
        field_name: str,
    ) -> tuple[str, ...]:
        normalized_ids: tuple[str, ...] = ()
        for record_id in record_ids:
            normalized_id = self._require_non_empty_string(record_id, field_name)
            normalized_ids = self._merge_linked_ids(normalized_ids, normalized_id)
        return normalized_ids

    def _validate_case_evidence_linkage(
        self,
        *,
        case: CaseRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        for evidence_id in evidence_ids:
            evidence = self._store.get(EvidenceRecord, evidence_id)
            if evidence is None:
                raise LookupError(f"Missing evidence {evidence_id!r}")
            if evidence.case_id not in {None, case.case_id}:
                raise ValueError(
                    f"{field_name} contains evidence {evidence_id!r} linked to "
                    f"different case {evidence.case_id!r}"
                )
            if evidence.case_id is None and evidence.alert_id != case.alert_id:
                raise ValueError(
                    f"{field_name} contains evidence {evidence_id!r} that is not "
                    f"linked to case {case.case_id!r} or its source alert"
                )

    def _observations_for_case(self, case_id: str) -> tuple[ObservationRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self._store.list(ObservationRecord)
                    if record.case_id == case_id
                ),
                key=lambda record: (record.observed_at, record.observation_id),
            )
        )

    def _leads_for_case(self, case_id: str) -> tuple[LeadRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self._store.list(LeadRecord)
                    if record.case_id == case_id
                ),
                key=lambda record: record.lead_id,
            )
        )

    @staticmethod
    def _case_lifecycle_for_disposition(disposition: str) -> str:
        if disposition in {
            "closed_benign",
            "closed_duplicate",
            "closed_resolved",
            "closed_accepted_risk",
        }:
            return "closed"
        if disposition in {
            "business_hours_handoff",
            "awaiting_business_hours_review",
            "pending_external_validation",
            "pending_approval",
        }:
            return "pending_action"
        if disposition == "investigating":
            return "investigating"
        raise ValueError(f"Unsupported case disposition {disposition!r}")

    @staticmethod
    def _normalize_substrate_detection_record_id(
        substrate_key: str,
        substrate_detection_record_id: str,
    ) -> str:
        namespaced_prefix = f"{substrate_key}:"
        if substrate_detection_record_id.startswith(namespaced_prefix):
            return substrate_detection_record_id
        return f"{namespaced_prefix}{substrate_detection_record_id}"

    @staticmethod
    def _next_identifier(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4()}"

    @staticmethod
    def _alert_review_state(alert: AlertRecord) -> str:
        if alert.lifecycle_state in {"new", "reopened"}:
            return "pending_review"
        if alert.lifecycle_state == "escalated_to_case":
            return "case_required"
        if alert.lifecycle_state == "investigating":
            return "investigating"
        return "triaged"

    @staticmethod
    def _alert_escalation_boundary(alert: AlertRecord) -> str:
        if alert.lifecycle_state == "escalated_to_case":
            return "tracked_case"
        return "next_business_hours_review"

    @staticmethod
    def _require_mapping(value: object, field_name: str) -> dict[str, object]:
        if not isinstance(value, Mapping):
            raise ValueError(f"{field_name} must be a mapping")
        return {str(key): item for key, item in value.items()}


def build_runtime_snapshot(environ: Mapping[str, str] | None = None) -> RuntimeSnapshot:
    config = RuntimeConfig.from_env(environ)
    service = AegisOpsControlPlaneService(config)
    return service.describe_runtime()


def build_runtime_service(
    environ: Mapping[str, str] | None = None,
) -> AegisOpsControlPlaneService:
    config = RuntimeConfig.from_env(environ)
    return AegisOpsControlPlaneService(config)
