from __future__ import annotations

from contextlib import AbstractContextManager, contextmanager
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, fields, replace
from datetime import datetime, timedelta, timezone
import hmac
import ipaddress
import json
import logging
import re
import uuid
from typing import Iterable, Iterator, Mapping, Protocol, Type, TypeVar

_DATETIME_TYPE = datetime

from .adapters.executor import IsolatedExecutorAdapter
from .adapters.n8n import N8NReconciliationAdapter
from .adapters.osquery import OsqueryHostContextAdapter
from .adapters.postgres import (
    PostgresControlPlaneStore,
    ReadinessDiagnosticsAggregates,
    ReadinessReviewPathRecords,
)
from .adapters.shuffle import ShuffleActionAdapter
from .adapters.wazuh import WazuhAlertAdapter
from .assistant_provider import (
    AssistantProviderAdapter,
    AssistantProviderFailure,
    AssistantProviderResult,
    AssistantProviderTransport,
)
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
    LifecycleTransitionRecord,
    NativeDetectionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from .operations import RestoreReadinessService, RuntimeBoundaryService
from .assistant_context import (
    AssistantContextAssembler,
    _advisory_text_claims_authority_or_scope_expansion,
)
from .reviewed_slice_policy import (
    REVIEWED_LIVE_SLICE_LABEL,
    REVIEWED_LIVE_SOURCE_FAMILIES,
    ReviewedSlicePolicy,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)

_AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS = frozenset(
    {
        "business_hours_handoff",
        "awaiting_business_hours_review",
    }
)
_CASE_CLOSED_TRIAGE_DISPOSITIONS = frozenset(
    {
        "closed_benign",
        "closed_duplicate",
        "closed_resolved",
        "closed_accepted_risk",
    }
)
_CASE_PENDING_ACTION_TRIAGE_DISPOSITIONS = frozenset(
    {
        "business_hours_handoff",
        "awaiting_business_hours_review",
        "pending_external_validation",
        "pending_approval",
    }
)
_CASE_LIFECYCLE_STATE_BY_TRIAGE_DISPOSITION = {
    **{
        disposition: "closed"
        for disposition in _CASE_CLOSED_TRIAGE_DISPOSITIONS
    },
    **{
        disposition: "pending_action"
        for disposition in _CASE_PENDING_ACTION_TRIAGE_DISPOSITIONS
    },
    "investigating": "investigating",
}

_LATEST_LIFECYCLE_TRANSITION_UNSET = object()
_LINKED_ALERT_CASE_LIFECYCLE_LOCK_FAMILY = "linked_alert_case_lifecycle"
_SAME_TIMESTAMP_LIFECYCLE_TRANSITION_ID_PREFIX = "~"
_PHASE24_WORKFLOW_FAMILY = "first_live_assistant_summary_family"
_PHASE24_WORKFLOW_PROMPT_VERSIONS = {
    "case_summary": "phase24-case-summary-v1",
    "queue_triage_summary": "phase24-queue-summary-v1",
}


class _ReviewedSummaryTransport(AssistantProviderTransport):
    """Deterministic reviewed-only transport for the first live workflow family."""

    def send_request(self, *, request: Mapping[str, object]) -> Mapping[str, object]:
        metadata = request.get("request_metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError("provider request metadata must be a mapping")
        output_text = metadata.get("bounded_summary_text")
        if not isinstance(output_text, str) or output_text.strip() == "":
            raise ValueError("provider request metadata must include bounded_summary_text")
        workflow_task = str(request.get("workflow_task") or "summary")
        request_id = f"reviewed-provider-request:{uuid.uuid4()}"
        response_id = f"reviewed-provider-response:{uuid.uuid4()}"
        transcript_id = f"reviewed-provider-transcript:{uuid.uuid4()}"
        return {
            "provider_request_id": request_id,
            "provider_response_id": response_id,
            "provider_transcript_id": transcript_id,
            "model_version": f"reviewed-local-{workflow_task}-v1",
            "output_text": output_text.strip(),
        }


class ControlPlaneStore(Protocol):
    dsn: str
    persistence_mode: str

    def save(self, record: RecordT) -> RecordT:
        ...

    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        ...

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        ...

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
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
    lifecycle_transitions: tuple[dict[str, object], ...]
    current_action_review: dict[str, object] | None
    action_reviews: tuple[dict[str, object], ...]
    external_ticket_reference: dict[str, object]

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
                "lifecycle_transitions": self.lifecycle_transitions,
                "current_action_review": self.current_action_review,
                "action_reviews": self.action_reviews,
                "external_ticket_reference": self.external_ticket_reference,
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
    lifecycle_transitions: tuple[dict[str, object], ...]
    cross_source_timeline: tuple[dict[str, object], ...]
    provenance_summary: dict[str, object]
    current_action_review: dict[str, object] | None
    action_reviews: tuple[dict[str, object], ...]
    external_ticket_reference: dict[str, object]

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
                "lifecycle_transitions": self.lifecycle_transitions,
                "cross_source_timeline": self.cross_source_timeline,
                "provenance_summary": self.provenance_summary,
                "current_action_review": self.current_action_review,
                "action_reviews": self.action_reviews,
                "external_ticket_reference": self.external_ticket_reference,
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
    lifecycle_transitions: tuple[dict[str, object], ...]

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
                "lifecycle_transitions": self.lifecycle_transitions,
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
class LiveAssistantWorkflowSnapshot:
    workflow_family: str
    workflow_task: str
    status: str
    summary: str
    citations: tuple[dict[str, object], ...]
    unresolved_reasons: tuple[str, ...]
    operator_follow_up: str | None

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "workflow_family": self.workflow_family,
                "workflow_task": self.workflow_task,
                "status": self.status,
                "summary": self.summary,
                "citations": self.citations,
                "unresolved_reasons": self.unresolved_reasons,
                "operator_follow_up": self.operator_follow_up,
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
    verified_recommendation_ids: tuple[str, ...]
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


@dataclass(frozen=True)
class _ActionReviewRecordIndex:
    requests_by_case_id: dict[str, tuple[ActionRequestRecord, ...]]
    requests_by_alert_id: dict[str, tuple[ActionRequestRecord, ...]]
    requests_by_scope: dict[tuple[str | None, str | None], tuple[ActionRequestRecord, ...]]
    approvals_by_id: dict[str, ApprovalDecisionRecord]
    approvals_by_action_request_id: dict[str, tuple[ApprovalDecisionRecord, ...]]
    executions_by_action_request_id: dict[str, tuple[ActionExecutionRecord, ...]]
    reconciliations_by_action_request_id: dict[str, tuple[ReconciliationRecord, ...]]
    reconciliations_by_approval_decision_id: dict[str, tuple[ReconciliationRecord, ...]]
    reconciliations_by_action_execution_id: dict[str, tuple[ReconciliationRecord, ...]]
    reconciliations_by_delegation_id: dict[str, tuple[ReconciliationRecord, ...]]

    def matching_requests(
        self,
        *,
        case_id: str | None,
        alert_id: str | None,
    ) -> tuple[ActionRequestRecord, ...]:
        matching_by_id: dict[str, ActionRequestRecord] = {}
        if case_id is not None:
            for record in self.requests_by_case_id.get(case_id, ()):
                matching_by_id[record.action_request_id] = record
        if alert_id is not None:
            for record in self.requests_by_alert_id.get(alert_id, ()):
                matching_by_id[record.action_request_id] = record
        return tuple(matching_by_id.values())

    def scoped_requests(
        self,
        *,
        case_id: str | None,
        alert_id: str | None,
    ) -> tuple[ActionRequestRecord, ...]:
        return self.requests_by_scope.get((case_id, alert_id), ())


def _derive_readiness_status(
    *,
    startup_ready: bool,
    reconciliation_lifecycle_counts: Mapping[str, int],
    review_path_health_overall_state: str | None = None,
) -> str:
    if not startup_ready:
        return "failing_closed"
    if reconciliation_lifecycle_counts.get("stale", 0):
        return "stale"
    if reconciliation_lifecycle_counts.get("mismatched", 0):
        return "degraded"
    if review_path_health_overall_state in {"degraded", "failed"}:
        return "degraded"
    return "ready"


RECORD_TYPES_BY_FAMILY: dict[str, Type[ControlPlaneRecord]] = {
    record_type.record_family: record_type
    for record_type in (
        AlertRecord,
        AnalyticSignalRecord,
        CaseRecord,
        EvidenceRecord,
        LifecycleTransitionRecord,
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
    ObservationRecord,
    LeadRecord,
    CaseRecord,
    RecommendationRecord,
    LifecycleTransitionRecord,
    ApprovalDecisionRecord,
    ActionRequestRecord,
    ActionExecutionRecord,
    HuntRecord,
    HuntRunRecord,
    AITraceRecord,
    ReconciliationRecord,
)
AUTHORITATIVE_RECORD_CHAIN_FAMILIES: tuple[str, ...] = tuple(
    record_type.record_family for record_type in AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES
)
AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION = (
    "phase23.authoritative-record-chain.v2"
)
_AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY: dict[str, str] = {
    "analytic_signal": "analytic_signal_id",
    "alert": "alert_id",
    "evidence": "evidence_id",
    "observation": "observation_id",
    "lead": "lead_id",
    "case": "case_id",
    "recommendation": "recommendation_id",
    "lifecycle_transition": "transition_id",
    "approval_decision": "approval_decision_id",
    "action_request": "action_request_id",
    "action_execution": "action_execution_id",
    "hunt": "hunt_id",
    "hunt_run": "hunt_run_id",
    "ai_trace": "ai_trace_id",
    "reconciliation": "reconciliation_id",
}
_BACKUP_DATETIME_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("first_seen_at", "last_seen_at"),
    "evidence": ("acquired_at",),
    "observation": ("observed_at",),
    "lifecycle_transition": ("transitioned_at",),
    "approval_decision": ("decided_at", "approved_expires_at"),
    "action_request": ("requested_at", "expires_at"),
    "action_execution": ("delegated_at", "expires_at"),
    "hunt": ("opened_at",),
    "hunt_run": ("started_at", "completed_at"),
    "ai_trace": ("generated_at",),
    "reconciliation": ("first_seen_at", "last_seen_at", "compared_at"),
}
_BACKUP_TUPLE_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("alert_ids", "case_ids"),
    "case": ("evidence_ids",),
    "observation": ("supporting_evidence_ids",),
    "approval_decision": ("approver_identities",),
    "ai_trace": ("material_input_refs",),
    "reconciliation": ("linked_execution_run_ids",),
}
_BACKUP_MAPPING_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("reviewed_context",),
    "alert": ("reviewed_context",),
    "case": ("reviewed_context",),
    "recommendation": ("reviewed_context", "assistant_advisory_draft"),
    "lifecycle_transition": ("attribution",),
    "approval_decision": ("target_snapshot",),
    "action_request": (
        "target_scope",
        "requested_payload",
        "policy_basis",
        "policy_evaluation",
    ),
    "action_execution": ("target_scope", "approved_payload", "provenance"),
    "hunt_run": ("scope_snapshot", "output_linkage"),
    "ai_trace": ("subject_linkage", "assistant_advisory_draft"),
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
    if isinstance(value, _DATETIME_TYPE):
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


def _coordination_reference_payload(
    record: Mapping[str, object] | ControlPlaneRecord | None,
) -> dict[str, str] | None:
    if record is None:
        return None
    if isinstance(record, Mapping):
        payload = record
    else:
        payload = _record_to_dict(record)

    coordination_reference_id = payload.get("coordination_reference_id")
    coordination_target_type = payload.get("coordination_target_type")
    coordination_target_id = payload.get("coordination_target_id")
    ticket_reference_url = payload.get("ticket_reference_url")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (
            coordination_reference_id,
            coordination_target_type,
            coordination_target_id,
            ticket_reference_url,
        )
    ):
        return None
    return {
        "coordination_reference_id": coordination_reference_id.strip(),
        "coordination_target_type": coordination_target_type.strip(),
        "coordination_target_id": coordination_target_id.strip(),
        "ticket_reference_url": ticket_reference_url.strip(),
    }


def _coordination_reference_signature(
    record: Mapping[str, object] | ControlPlaneRecord | None,
) -> tuple[str, str, str, str] | None:
    payload = _coordination_reference_payload(record)
    if payload is None:
        return None
    return (
        payload["coordination_reference_id"],
        payload["coordination_target_type"],
        payload["coordination_target_id"],
        payload["ticket_reference_url"],
    )


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
            "controlled shutdown requires dispatching, queued, or running executions to reach a terminal state"
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


def _dedupe_strings(values: Iterable[str]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value not in deduped:
            deduped.append(value)
    return tuple(deduped)


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


def _phase24_live_assistant_unresolved_reasons(
    uncertainty_flags: Iterable[str],
) -> tuple[str, ...]:
    mapping = {
        "missing_supporting_citations": "required citations are missing",
        "missing_evidence_citation": "linked evidence required for the summary is missing",
        "conflicting_reviewed_context": (
            "reviewed records conflict on lifecycle state, ownership, scope, or evidence-backed facts"
        ),
        "ambiguous_identity_alias_only": (
            "the requested summary would require the assistant to collapse identity ambiguity"
        ),
        "reviewed_casework_identity_ambiguity": (
            "reviewed multi-source casework still contains unresolved identity ambiguity"
        ),
        "authority_overreach": (
            "the requested summary would widen into approval, delegation, execution, or policy interpretation"
        ),
        "scope_expansion_attempt": (
            "the requested summary would widen beyond the reviewed record chain"
        ),
        "prompt_injection_attempt": (
            "the requested summary would follow prompt-injection or instruction-override text instead of reviewed records"
        ),
        "provider_generation_failed": (
            "the bounded live assistant did not return a trusted summary within the reviewed retry budget"
        ),
    }
    reasons: list[str] = []
    for flag in uncertainty_flags:
        reason = mapping.get(str(flag))
        if reason is not None and reason not in reasons:
            reasons.append(reason)
    return tuple(reasons)


def _phase24_live_assistant_prompt_injection_flags(text: object) -> tuple[str, ...]:
    if not isinstance(text, str):
        return ()

    lowered = text.lower()
    normalized = re.sub(r"[\W_]+", " ", lowered)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    flags: list[str] = []
    prompt_injection_terms = (
        r"\bignore(?:\s+all)?\s+previous\s+instructions\b",
        r"\bdisregard\s+previous\s+instructions\b",
        r"\boverride\s+previous\s+instructions\b",
        r"\breveal\s+(?:the\s+)?hidden\s+system\s+prompt\b",
        r"\breveal\s+(?:the\s+)?system\s+prompt\b",
        r"\bshow\s+(?:the\s+)?system\s+prompt\b",
        r"\breveal\s+(?:the\s+)?developer\s+message\b",
    )
    if any(re.search(term, normalized) for term in prompt_injection_terms):
        flags.append("prompt_injection_attempt")
    return _dedupe_strings(tuple(flags))


def _phase24_live_assistant_citations_from_context(
    snapshot: AnalystAssistantContextSnapshot,
) -> tuple[dict[str, object], ...]:
    citations: list[dict[str, object]] = []
    seen: set[tuple[object, ...]] = set()

    def append_citation(
        *,
        record_family: str,
        record_id: str,
        claim: str,
        evidence_id: str | None,
        reviewed_context_field: str | None,
    ) -> None:
        key = (record_family, record_id, claim, evidence_id, reviewed_context_field)
        if key in seen:
            return
        seen.add(key)
        citations.append(
            {
                "record_family": record_family,
                "record_id": record_id,
                "claim": claim,
                "evidence_id": evidence_id,
                "reviewed_context_field": reviewed_context_field,
            }
        )

    lifecycle_state = snapshot.record.get("lifecycle_state")
    if snapshot.record_family == "case":
        append_citation(
            record_family="case",
            record_id=snapshot.record_id,
            claim="Reviewed case lifecycle and scope remain anchored on the case record.",
            evidence_id=None,
            reviewed_context_field=None,
        )
    elif snapshot.record_family == "alert":
        append_citation(
            record_family="alert",
            record_id=snapshot.record_id,
            claim="Reviewed alert lifecycle remains anchored on the alert record.",
            evidence_id=None,
            reviewed_context_field=None,
        )

    for alert_id in snapshot.linked_alert_ids:
        append_citation(
            record_family="alert",
            record_id=alert_id,
            claim="Reviewed alert linkage preserves the bounded live assistant chain.",
            evidence_id=None,
            reviewed_context_field=None,
        )
    for case_id in snapshot.linked_case_ids:
        append_citation(
            record_family="case",
            record_id=case_id,
            claim="Reviewed case linkage preserves the bounded live assistant chain.",
            evidence_id=None,
            reviewed_context_field=None,
        )
    for evidence_id in snapshot.linked_evidence_ids:
        append_citation(
            record_family="evidence",
            record_id=evidence_id,
            claim="Linked reviewed evidence supports the live assistant summary.",
            evidence_id=evidence_id,
            reviewed_context_field=None,
        )

    for context_field in ("asset", "identity", "privilege", "source", "provenance"):
        if context_field in snapshot.reviewed_context:
            append_citation(
                record_family=snapshot.record_family,
                record_id=snapshot.record_id,
                claim=(
                    f"Reviewed context field {context_field} remains within the reviewed record chain."
                ),
                evidence_id=None,
                reviewed_context_field=context_field,
            )

    return tuple(citations)


def _phase24_live_assistant_follow_up(status: str) -> str:
    if status == "ready":
        return (
            "Review the cited records before any approval, delegation, execution, or policy decision."
        )
    return (
        "Review the unresolved reasons against the cited records before any approval, delegation, execution, or policy decision."
    )


def _phase24_live_assistant_snapshot(
    *,
    workflow_task: str,
    summary: str,
    citations: tuple[dict[str, object], ...],
    unresolved_reasons: tuple[str, ...],
) -> LiveAssistantWorkflowSnapshot:
    status = "unresolved" if unresolved_reasons else "ready"
    return LiveAssistantWorkflowSnapshot(
        workflow_family=_PHASE24_WORKFLOW_FAMILY,
        workflow_task=workflow_task,
        status=status,
        summary=summary,
        citations=citations,
        unresolved_reasons=unresolved_reasons,
        operator_follow_up=_phase24_live_assistant_follow_up(status),
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
        self._assistant_provider_adapter = AssistantProviderAdapter(
            provider_identity="reviewed_local",
            model_identity="bounded_reviewed_summary",
            prompt_version=_PHASE24_WORKFLOW_PROMPT_VERSIONS["case_summary"],
            request_timeout_seconds=5.0,
            max_attempts=1,
            transport=_ReviewedSummaryTransport(),
        )
        self._reviewed_slice_policy = ReviewedSlicePolicy(
            self,
            normalize_admission_provenance=_normalize_admission_provenance,
        )
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
        self._osquery_host_context_adapter = OsqueryHostContextAdapter()
        self._runtime_boundary_service = RuntimeBoundaryService(
            config=self._config,
            store=self._store,
            reconciliation_adapter=self._reconciliation,
            shuffle_adapter=self._shuffle,
            isolated_executor_adapter=self._isolated_executor,
            runtime_snapshot_factory=RuntimeSnapshot,
            authenticated_principal_factory=AuthenticatedRuntimePrincipal,
        )
        self._restore_readiness_service = RestoreReadinessService(
            config=self._config,
            store=self._store,
            runtime_boundary_service=self._runtime_boundary_service,
            startup_status_snapshot_factory=StartupStatusSnapshot,
            readiness_diagnostics_snapshot_factory=ReadinessDiagnosticsSnapshot,
            restore_drill_snapshot_factory=RestoreDrillSnapshot,
            restore_summary_snapshot_factory=RestoreSummarySnapshot,
            record_to_dict=_record_to_dict,
            json_ready=_json_ready,
            redacted_reconciliation_payload=_redacted_reconciliation_payload,
            collect_readiness_review_snapshots=self._collect_readiness_review_snapshots,
            build_readiness_review_path_health=self._build_readiness_review_path_health,
            build_readiness_source_health=self._build_readiness_source_health,
            build_readiness_automation_substrate_health=(
                self._build_readiness_automation_substrate_health
            ),
            build_shutdown_status_snapshot=_build_shutdown_status_snapshot,
            derive_readiness_status=_derive_readiness_status,
            record_from_backup_payload=_record_from_backup_payload,
            authoritative_record_chain_record_types=(
                AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES
            ),
            authoritative_record_chain_backup_schema_version=(
                AUTHORITATIVE_RECORD_CHAIN_BACKUP_SCHEMA_VERSION
            ),
            authoritative_primary_id_field_by_family=(
                _AUTHORITATIVE_PRIMARY_ID_FIELD_BY_FAMILY
            ),
            record_types_by_family=RECORD_TYPES_BY_FAMILY,
            find_duplicate_strings=_find_duplicate_strings,
            synthesize_lifecycle_transition_record=(
                lambda record, initial_transitioned_at_fallback=None: self._build_lifecycle_transition_record(
                    record,
                    existing_record=None,
                    initial_transitioned_at_fallback=initial_transitioned_at_fallback,
                )
            ),
            assistant_ids_from_mapping=self._assistant_ids_from_mapping,
            inspect_case_detail=lambda case_id: self.inspect_case_detail(case_id),
            inspect_assistant_context=(
                lambda record_family, record_id: self.inspect_assistant_context(
                    record_family,
                    record_id,
                )
            ),
            inspect_reconciliation_status=lambda: self.inspect_reconciliation_status(),
        )

    def describe_runtime(self) -> RuntimeSnapshot:
        return self._runtime_boundary_service.describe_runtime()

    def persist_record(
        self,
        record: RecordT,
        *,
        transitioned_at: datetime | None = None,
    ) -> RecordT:
        if isinstance(record, LifecycleTransitionRecord):
            raise ValueError(
                "persist_record does not accept direct lifecycle transition records"
            )
        if transitioned_at is not None:
            transitioned_at = self._require_aware_datetime(
                transitioned_at,
                "transitioned_at",
            )
        with self._store.transaction():
            lineage_lock_subject = self._linked_alert_case_lifecycle_lock_subject(record)
            if lineage_lock_subject is not None:
                self._lock_lifecycle_transition_subject(*lineage_lock_subject)
            self._lock_lifecycle_transition_subject(
                record.record_family,
                record.record_id,
            )
            existing_record = self._store.get(type(record), record.record_id)
            persisted_record = self._store.save(record)
            transition_records = self._build_lifecycle_transition_records(
                persisted_record,
                existing_record=existing_record,
                transitioned_at=transitioned_at,
            )
            for transition_record in transition_records:
                self._store.save(transition_record)
            return persisted_record

    def _lock_lifecycle_transition_subject(
        self,
        record_family: str,
        record_id: str,
    ) -> None:
        lock_subject = getattr(self._store, "lock_lifecycle_transition_subject", None)
        if callable(lock_subject):
            lock_subject(record_family, record_id)

    @staticmethod
    def _linked_alert_case_lifecycle_lock_subject(
        record: ControlPlaneRecord,
    ) -> tuple[str, str] | None:
        if isinstance(record, AlertRecord):
            alert_id = record.alert_id
            case_id = record.case_id
        elif isinstance(record, CaseRecord):
            alert_id = record.alert_id
            case_id = record.case_id
        else:
            return None

        if not isinstance(alert_id, str) or not alert_id.strip():
            return None
        if not isinstance(case_id, str) or not case_id.strip():
            return None

        # Serialize linked alert/case lifecycle mutations on one shared key so
        # opposite record-specific update orders cannot deadlock.
        return (
            _LINKED_ALERT_CASE_LIFECYCLE_LOCK_FAMILY,
            f"alert:{alert_id}|case:{case_id}",
        )

    def _build_lifecycle_transition_record(
        self,
        record: ControlPlaneRecord,
        *,
        existing_record: ControlPlaneRecord | None,
        transitioned_at: datetime | None = None,
        initial_transitioned_at_fallback: datetime | None = None,
        must_precede_transitioned_at: datetime | None = None,
        latest_transition: LifecycleTransitionRecord | None | object = (
            _LATEST_LIFECYCLE_TRANSITION_UNSET
        ),
    ) -> LifecycleTransitionRecord | None:
        if isinstance(record, LifecycleTransitionRecord):
            return None
        if not hasattr(record, "lifecycle_state"):
            return None

        existing_lifecycle_state = (
            getattr(existing_record, "lifecycle_state", None)
            if existing_record is not None
            else None
        )
        next_lifecycle_state = getattr(record, "lifecycle_state", None)
        if not isinstance(next_lifecycle_state, str) or not next_lifecycle_state.strip():
            return None
        if latest_transition is _LATEST_LIFECYCLE_TRANSITION_UNSET:
            latest_transition = self._latest_lifecycle_transition(
                record.record_family,
                record.record_id,
            )
        previous_lifecycle_state = existing_lifecycle_state
        if latest_transition is not None:
            if existing_record is None:
                raise ValueError(
                    f"{record.record_family} record {record.record_id!r} has orphaned "
                    "lifecycle transition history without a current-state record"
                )
            if (
                existing_record is not None
                and existing_lifecycle_state != latest_transition.lifecycle_state
            ):
                raise ValueError(
                    f"{record.record_family} record {record.record_id!r} lifecycle_state "
                    f"{existing_lifecycle_state!r} does not match latest lifecycle "
                    f"transition {latest_transition.transition_id!r} state "
                    f"{latest_transition.lifecycle_state!r}"
                )
            previous_lifecycle_state = latest_transition.lifecycle_state
        if previous_lifecycle_state == next_lifecycle_state:
            return None

        explicit_transitioned_at = transitioned_at is not None
        resolved_transitioned_at = (
            transitioned_at
            if transitioned_at is not None
            else (
                self._initial_lifecycle_transitioned_at(
                    record,
                    fallback=initial_transitioned_at_fallback,
                )
                if existing_record is None
                else datetime.now(timezone.utc)
            )
        )
        if (
            must_precede_transitioned_at is not None
            and resolved_transitioned_at >= must_precede_transitioned_at
        ):
            resolved_transitioned_at = must_precede_transitioned_at - timedelta(
                microseconds=1
            )
        if (
            latest_transition is not None
            and resolved_transitioned_at < latest_transition.transitioned_at
        ):
            if explicit_transitioned_at:
                raise ValueError(
                    "transitioned_at must not precede the latest lifecycle transition "
                    f"for {record.record_family} record {record.record_id!r}"
                )
            resolved_transitioned_at = latest_transition.transitioned_at + timedelta(
                microseconds=1
            )
        transition_timestamp = resolved_transitioned_at.astimezone(
            timezone.utc
        ).strftime("%Y%m%dT%H%M%S.%fZ")
        return LifecycleTransitionRecord(
            transition_id=self._lifecycle_transition_id(
                transition_timestamp=transition_timestamp,
                transitioned_at=resolved_transitioned_at,
                latest_transition=latest_transition,
            ),
            subject_record_family=record.record_family,
            subject_record_id=record.record_id,
            previous_lifecycle_state=(
                previous_lifecycle_state
                if isinstance(previous_lifecycle_state, str)
                and previous_lifecycle_state.strip()
                else None
            ),
            lifecycle_state=next_lifecycle_state,
            transitioned_at=resolved_transitioned_at,
            attribution=self._lifecycle_transition_attribution(record),
        )

    def _lifecycle_transition_id(
        self,
        *,
        transition_timestamp: str,
        transitioned_at: datetime,
        latest_transition: LifecycleTransitionRecord | None,
    ) -> str:
        if (
            latest_transition is None
            or transitioned_at != latest_transition.transitioned_at
        ):
            return f"{transition_timestamp}:{uuid.uuid4()}"

        sequence = 1
        prefix = (
            f"{_SAME_TIMESTAMP_LIFECYCLE_TRANSITION_ID_PREFIX}{transition_timestamp}:"
        )
        if latest_transition.transition_id.startswith(prefix):
            sequence_text = latest_transition.transition_id[len(prefix) :].split(":", 1)[
                0
            ]
            if sequence_text.isdigit():
                sequence = int(sequence_text) + 1
        return f"{prefix}{sequence:06d}:{uuid.uuid4()}"

    def _build_lifecycle_transition_records(
        self,
        record: ControlPlaneRecord,
        *,
        existing_record: ControlPlaneRecord | None,
        transitioned_at: datetime | None = None,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        if isinstance(record, LifecycleTransitionRecord):
            return ()
        if not hasattr(record, "lifecycle_state"):
            return ()

        latest_transition = self._latest_lifecycle_transition(
            record.record_family,
            record.record_id,
        )
        transition_records: list[LifecycleTransitionRecord] = []
        if latest_transition is None and existing_record is not None:
            anchor_transition = self._build_lifecycle_transition_record(
                existing_record,
                existing_record=None,
                must_precede_transitioned_at=transitioned_at,
                latest_transition=None,
            )
            if anchor_transition is not None:
                transition_records.append(anchor_transition)
                latest_transition = anchor_transition

        transition_record = self._build_lifecycle_transition_record(
            record,
            existing_record=existing_record,
            transitioned_at=transitioned_at,
            latest_transition=latest_transition,
        )
        if transition_record is not None:
            transition_records.append(transition_record)
        return tuple(transition_records)

    def _initial_lifecycle_transitioned_at(
        self,
        record: ControlPlaneRecord,
        *,
        fallback: datetime | None = None,
    ) -> datetime:
        if isinstance(record, AnalyticSignalRecord):
            if record.first_seen_at is not None:
                return record.first_seen_at
            if record.last_seen_at is not None:
                return record.last_seen_at
        elif isinstance(record, EvidenceRecord):
            return record.acquired_at
        elif isinstance(record, ObservationRecord):
            return record.observed_at
        elif isinstance(record, HuntRecord):
            return record.opened_at
        elif isinstance(record, HuntRunRecord):
            for candidate in (record.started_at, record.completed_at):
                if candidate is not None:
                    return candidate
        elif isinstance(record, (AlertRecord, CaseRecord)):
            reviewed_transitioned_at = self._reviewed_context_transitioned_at(record)
            if reviewed_transitioned_at is not None:
                return reviewed_transitioned_at
        elif isinstance(record, ApprovalDecisionRecord):
            if record.decided_at is not None:
                return record.decided_at
        elif isinstance(record, ActionRequestRecord):
            return record.requested_at
        elif isinstance(record, ActionExecutionRecord):
            return record.delegated_at
        elif isinstance(record, AITraceRecord):
            return record.generated_at
        elif isinstance(record, ReconciliationRecord):
            for candidate in (
                record.first_seen_at,
                record.last_seen_at,
                record.compared_at,
            ):
                if candidate is not None:
                    return candidate
        return fallback if fallback is not None else datetime.now(timezone.utc)

    @staticmethod
    def _reviewed_context_transitioned_at(
        record: AlertRecord | CaseRecord,
    ) -> datetime | None:
        reviewed_context = getattr(record, "reviewed_context", None)
        if not isinstance(reviewed_context, Mapping):
            return None
        triage = reviewed_context.get("triage")
        if not isinstance(triage, Mapping):
            return None
        if not AegisOpsControlPlaneService._triage_disposition_matches_current_state(
            record,
            triage.get("disposition"),
        ):
            return None
        raw_recorded_at = triage.get("recorded_at")
        if not isinstance(raw_recorded_at, str) or not raw_recorded_at.strip():
            return None
        try:
            parsed = datetime.fromisoformat(raw_recorded_at)
        except ValueError:
            return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed

    @staticmethod
    def _triage_disposition_matches_current_state(
        record: AlertRecord | CaseRecord,
        disposition: object,
    ) -> bool:
        triage_lifecycle_state = (
            AegisOpsControlPlaneService._case_lifecycle_state_for_triage_disposition(
                disposition
            )
        )
        if triage_lifecycle_state is None:
            return False
        if isinstance(record, AlertRecord):
            return record.lifecycle_state == "closed" and triage_lifecycle_state == "closed"
        return record.lifecycle_state == triage_lifecycle_state

    @staticmethod
    def _case_lifecycle_state_for_triage_disposition(
        disposition: object,
    ) -> str | None:
        if not isinstance(disposition, str) or not disposition.strip():
            return None
        return _CASE_LIFECYCLE_STATE_BY_TRIAGE_DISPOSITION.get(disposition)

    def _latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        return self._store.latest_lifecycle_transition(record_family, record_id)

    def _lifecycle_transition_attribution(
        self,
        record: ControlPlaneRecord,
    ) -> dict[str, object]:
        actor_identities: tuple[str, ...] = ()
        source = "aegisops-control-plane"

        if isinstance(record, ObservationRecord):
            actor_identities = self._merge_linked_ids((), record.author_identity)
            source = "observation-author"
        elif isinstance(record, LeadRecord):
            actor_identities = self._merge_linked_ids((), record.triage_owner)
            source = "lead-triage-owner"
        elif isinstance(record, RecommendationRecord):
            actor_identities = self._merge_linked_ids((), record.review_owner)
            source = "recommendation-review-owner"
        elif isinstance(record, ActionRequestRecord):
            actor_identities = self._merge_linked_ids((), record.requester_identity)
            source = "action-request"
        elif isinstance(record, ApprovalDecisionRecord):
            actor_identities = self._merge_linked_ids(
                record.approver_identities,
                None,
            )
            source = "approval-decision"
        elif isinstance(record, HuntRecord):
            actor_identities = self._merge_linked_ids((), record.owner_identity)
            source = "hunt-owner"
        elif isinstance(record, AITraceRecord):
            actor_identities = self._merge_linked_ids((), record.reviewer_identity)
            source = "ai-trace-reviewer"

        return {
            "source": source,
            "actor_identities": actor_identities,
        }

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        normalized_record_family = self._require_non_empty_string(
            record_family,
            "record_family",
        )
        normalized_record_id = self._require_non_empty_string(record_id, "record_id")
        return self._store.list_lifecycle_transitions(
            normalized_record_family,
            normalized_record_id,
        )

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
        self._runtime_boundary_service.validate_wazuh_ingest_runtime()

    def validate_protected_surface_runtime(self) -> None:
        self._runtime_boundary_service.validate_protected_surface_runtime()

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
        return self._runtime_boundary_service.authenticate_protected_surface_request(
            peer_addr=peer_addr,
            forwarded_proto=forwarded_proto,
            reverse_proxy_secret_header=reverse_proxy_secret_header,
            proxy_service_account_header=proxy_service_account_header,
            authenticated_identity_header=authenticated_identity_header,
            authenticated_role_header=authenticated_role_header,
            allowed_roles=allowed_roles,
        )

    def require_admin_bootstrap_token(self, supplied_token: str | None) -> None:
        self._runtime_boundary_service.require_admin_bootstrap_token(supplied_token)

    def require_break_glass_token(self, supplied_token: str | None) -> None:
        self._runtime_boundary_service.require_break_glass_token(supplied_token)

    def ingest_wazuh_alert(
        self,
        *,
        raw_alert: Mapping[str, object],
        authorization_header: str | None,
        forwarded_proto: str | None,
        reverse_proxy_secret_header: str | None,
        peer_addr: str | None,
    ) -> FindingAlertIngestResult:
        self._runtime_boundary_service.validate_wazuh_ingest_runtime()

        if not self._runtime_boundary_service.is_trusted_wazuh_ingest_peer(peer_addr):
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
        if source_family not in REVIEWED_LIVE_SOURCE_FAMILIES:
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
        return self._runtime_boundary_service.listener_is_loopback()

    def _is_trusted_wazuh_ingest_peer(self, peer_addr: str | None) -> bool:
        return self._runtime_boundary_service.is_trusted_wazuh_ingest_peer(peer_addr)

    def _is_trusted_protected_surface_peer(self, peer_addr: str | None) -> bool:
        return self._runtime_boundary_service.is_trusted_protected_surface_peer(
            peer_addr
        )

    def _is_trusted_peer_for_proxy_cidrs(
        self,
        peer_addr: str | None,
        trusted_proxy_cidrs: tuple[str, ...],
    ) -> bool:
        return self._runtime_boundary_service.is_trusted_peer_for_proxy_cidrs(
            peer_addr,
            trusted_proxy_cidrs,
        )

    @staticmethod
    def _peer_addr_is_loopback(peer_addr: str | None) -> bool:
        return RuntimeBoundaryService.peer_addr_is_loopback(peer_addr)

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
            records=tuple(
                _redacted_reconciliation_payload(record) for record in records
            ),
        )

    def describe_startup_status(self) -> StartupStatusSnapshot:
        return self._restore_readiness_service.describe_startup_status()

    def describe_shutdown_status(self) -> ShutdownStatusSnapshot:
        return self._restore_readiness_service.describe_shutdown_status()

    def inspect_readiness_diagnostics(self) -> ReadinessDiagnosticsSnapshot:
        return self._restore_readiness_service.inspect_readiness_diagnostics()

    def _inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
        return self._restore_readiness_service.inspect_readiness_aggregates()

    def export_authoritative_record_chain_backup(self) -> dict[str, object]:
        return self._restore_readiness_service.export_authoritative_record_chain_backup()

    def restore_authoritative_record_chain_backup(
        self,
        backup_payload: Mapping[str, object],
    ) -> RestoreSummarySnapshot:
        return self._restore_readiness_service.restore_authoritative_record_chain_backup(
            backup_payload
        )

    @contextmanager
    def _restore_drill_snapshot_transaction(self) -> Iterator[None]:
        with self._restore_readiness_service.restore_drill_snapshot_transaction():
            yield

    def run_authoritative_restore_drill(self) -> RestoreDrillSnapshot:
        return self._restore_readiness_service.run_authoritative_restore_drill()

    def _run_authoritative_restore_drill_snapshot(self) -> RestoreDrillSnapshot:
        return self._restore_readiness_service.run_authoritative_restore_drill_snapshot()

    def _build_action_review_record_index(self) -> _ActionReviewRecordIndex:
        def _freeze_grouped_records(
            grouped_records: defaultdict[object, list[object]],
        ) -> dict[object, tuple[object, ...]]:
            return {
                key: tuple(records)
                for key, records in grouped_records.items()
            }

        action_requests = self._store.list(ActionRequestRecord)
        if not action_requests:
            return _ActionReviewRecordIndex(
                requests_by_case_id={},
                requests_by_alert_id={},
                requests_by_scope={},
                approvals_by_id={},
                approvals_by_action_request_id={},
                executions_by_action_request_id={},
                reconciliations_by_action_request_id={},
                reconciliations_by_approval_decision_id={},
                reconciliations_by_action_execution_id={},
                reconciliations_by_delegation_id={},
            )
        approvals = self._store.list(ApprovalDecisionRecord)
        action_executions = self._store.list(ActionExecutionRecord)
        reconciliations = self._store.list(ReconciliationRecord)

        requests_by_case_id: defaultdict[str, list[ActionRequestRecord]] = defaultdict(list)
        requests_by_alert_id: defaultdict[str, list[ActionRequestRecord]] = defaultdict(list)
        requests_by_scope: defaultdict[
            tuple[str | None, str | None],
            list[ActionRequestRecord],
        ] = defaultdict(list)
        for action_request in action_requests:
            requests_by_scope[
                (action_request.case_id, action_request.alert_id)
            ].append(action_request)
            if action_request.case_id is not None:
                requests_by_case_id[action_request.case_id].append(action_request)
            if action_request.alert_id is not None:
                requests_by_alert_id[action_request.alert_id].append(action_request)

        approvals_by_action_request_id: defaultdict[
            str,
            list[ApprovalDecisionRecord],
        ] = defaultdict(list)
        approvals_by_id = {
            approval.approval_decision_id: approval for approval in approvals
        }
        for approval in approvals:
            approvals_by_action_request_id[approval.action_request_id].append(approval)

        executions_by_action_request_id: defaultdict[
            str,
            list[ActionExecutionRecord],
        ] = defaultdict(list)
        for action_execution in action_executions:
            executions_by_action_request_id[action_execution.action_request_id].append(
                action_execution
            )

        reconciliations_by_action_request_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_approval_decision_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_action_execution_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_delegation_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        for reconciliation in reconciliations:
            for action_request_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_request_ids",
            ):
                reconciliations_by_action_request_id[action_request_id].append(
                    reconciliation
                )
            for approval_decision_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            ):
                reconciliations_by_approval_decision_id[approval_decision_id].append(
                    reconciliation
                )
            for action_execution_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            ):
                reconciliations_by_action_execution_id[action_execution_id].append(
                    reconciliation
                )
            for delegation_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "delegation_ids",
            ):
                reconciliations_by_delegation_id[delegation_id].append(reconciliation)

        return _ActionReviewRecordIndex(
            requests_by_case_id=_freeze_grouped_records(requests_by_case_id),
            requests_by_alert_id=_freeze_grouped_records(requests_by_alert_id),
            requests_by_scope=_freeze_grouped_records(requests_by_scope),
            approvals_by_id=approvals_by_id,
            approvals_by_action_request_id=_freeze_grouped_records(
                approvals_by_action_request_id
            ),
            executions_by_action_request_id=_freeze_grouped_records(
                executions_by_action_request_id
            ),
            reconciliations_by_action_request_id=_freeze_grouped_records(
                reconciliations_by_action_request_id
            ),
            reconciliations_by_approval_decision_id=_freeze_grouped_records(
                reconciliations_by_approval_decision_id
            ),
            reconciliations_by_action_execution_id=_freeze_grouped_records(
                reconciliations_by_action_execution_id
            ),
            reconciliations_by_delegation_id=_freeze_grouped_records(
                reconciliations_by_delegation_id
            ),
        )

    def _action_review_chains_for_scope(
        self,
        *,
        case_id: str | None,
        alert_id: str | None,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> tuple[dict[str, object], ...]:
        if record_index is not None:
            matching_requests = list(
                record_index.matching_requests(case_id=case_id, alert_id=alert_id)
            )
        else:
            matching_requests = [
                record
                for record in self._store.list(ActionRequestRecord)
                if (
                    (case_id is not None and record.case_id == case_id)
                    or (alert_id is not None and record.alert_id == alert_id)
                )
            ]
        matching_requests = [
            record
            for record in matching_requests
            if self._action_request_is_review_bound(record)
        ]
        chains = [
            self._build_action_review_chain_snapshot(
                action_request,
                record_index=record_index,
            )
            for action_request in matching_requests
        ]
        chains.sort(
            key=lambda chain: (
                chain.get("requested_at") or datetime.min.replace(tzinfo=timezone.utc),
                self._action_review_priority(chain),
                chain.get("action_request_id") or "",
            ),
            reverse=True,
        )
        return tuple(chains)

    @staticmethod
    def _action_review_priority(chain: Mapping[str, object]) -> int:
        review_state = chain.get("review_state")
        if review_state == "pending":
            return 5
        if review_state in {"approved", "executing"}:
            return 4
        if review_state in {"expired", "rejected"}:
            return 3
        if review_state == "superseded":
            return 2
        return 1

    def _build_action_review_chain_snapshot(
        self,
        action_request: ActionRequestRecord,
        *,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> dict[str, object]:
        approval_decision = self._action_review_approval_decision(
            action_request,
            record_index=record_index,
        )
        action_execution = self._action_review_execution(
            action_request,
            record_index=record_index,
        )
        reconciliation = self._latest_action_review_reconciliation(
            action_request=action_request,
            approval_decision=approval_decision,
            action_execution=action_execution,
            record_index=record_index,
        )
        approval_state = self._action_review_approval_state(
            action_request=action_request,
            approval_decision=approval_decision,
        )
        review_state = self._action_review_state(
            action_request=action_request,
            approval_state=approval_state,
            action_execution=action_execution,
        )
        timeline = self._action_review_timeline(
            action_request=action_request,
            approval_state=approval_state,
            approval_decision=approval_decision,
            action_execution=action_execution,
            reconciliation=reconciliation,
        )
        mismatch_inspection = self._action_review_mismatch_inspection(reconciliation)
        replacement_action_request = self._replacement_action_request(
            action_request,
            record_index=record_index,
        )
        requested_payload = dict(action_request.requested_payload)
        runtime_visibility = self._action_review_runtime_visibility(
            action_request=action_request,
            approval_decision=approval_decision,
            review_state=review_state,
            record_index=record_index,
        )
        path_health_as_of = datetime.now(timezone.utc)
        path_health = self._action_review_path_health(
            action_request=action_request,
            approval_decision=approval_decision,
            action_execution=action_execution,
            reconciliation=reconciliation,
            review_state=review_state,
            as_of=path_health_as_of,
        )
        coordination_ticket_outcome = self._action_review_coordination_ticket_outcome(
            action_request=action_request,
            approval_decision=approval_decision,
            action_execution=action_execution,
            reconciliation=reconciliation,
            runtime_visibility=runtime_visibility,
            path_health=path_health,
            review_state=review_state,
        )

        return {
            "review_state": review_state,
            "next_expected_action": self._next_expected_action_for_review_state(
                review_state
            ),
            "action_request_id": action_request.action_request_id,
            "action_request_state": action_request.lifecycle_state,
            "approval_decision_id": (
                approval_decision.approval_decision_id if approval_decision is not None else None
            ),
            "approval_state": approval_state,
            "requester_identity": action_request.requester_identity,
            "approver_identities": (
                approval_decision.approver_identities if approval_decision is not None else ()
            ),
            "decision_rationale": (
                approval_decision.decision_rationale
                if approval_decision is not None
                else None
            ),
            "requested_at": action_request.requested_at,
            "expires_at": action_request.expires_at,
            "target_scope": dict(action_request.target_scope),
            "requested_payload": requested_payload,
            "recommendation_id": requested_payload.get("recommendation_id"),
            "recipient_identity": requested_payload.get("recipient_identity"),
            "message_intent": requested_payload.get("message_intent"),
            "escalation_reason": requested_payload.get("escalation_reason"),
            "runtime_visibility": runtime_visibility,
            "path_health": path_health,
            "coordination_ticket_outcome": coordination_ticket_outcome,
            "execution_surface_type": (
                action_execution.execution_surface_type
                if action_execution is not None
                else action_request.policy_evaluation.get("execution_surface_type")
            ),
            "execution_surface_id": (
                action_execution.execution_surface_id
                if action_execution is not None
                else action_request.policy_evaluation.get("execution_surface_id")
            ),
            "timeline": timeline,
            "mismatch_inspection": mismatch_inspection,
            "action_execution_id": (
                action_execution.action_execution_id if action_execution is not None else None
            ),
            "action_execution_state": (
                action_execution.lifecycle_state if action_execution is not None else None
            ),
            "delegation_id": (
                action_execution.delegation_id if action_execution is not None else None
            ),
            "execution_run_id": (
                action_execution.execution_run_id if action_execution is not None else None
            ),
            "reconciliation_id": (
                reconciliation.reconciliation_id if reconciliation is not None else None
            ),
            "reconciliation_state": (
                reconciliation.lifecycle_state if reconciliation is not None else None
            ),
            "replacement_action_request_id": (
                replacement_action_request.action_request_id
                if replacement_action_request is not None
                else None
            ),
            "replacement_approval_decision_id": (
                replacement_action_request.approval_decision_id
                if replacement_action_request is not None
                else None
            ),
        }

    def _action_review_path_health(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        reconciliation: ReconciliationRecord | None,
        review_state: str,
        as_of: datetime,
    ) -> dict[str, object]:
        if action_execution is None and reconciliation is None:
            if review_state in {"rejected", "expired", "superseded", "canceled"}:
                paths = self._action_review_terminal_non_delegated_path_health()
            elif (
                review_state == "unresolved"
                and approval_decision is not None
                and approval_decision.lifecycle_state == "approved"
            ):
                paths = self._action_review_unresolved_without_execution_path_health()
            else:
                paths = {
                    "ingest": self._action_review_ingest_path_health(reconciliation),
                    "delegation": self._action_review_delegation_path_health(
                        action_request=action_request,
                        approval_decision=approval_decision,
                        action_execution=action_execution,
                        review_state=review_state,
                    ),
                    "provider": self._action_review_provider_path_health(action_execution),
                    "persistence": self._action_review_persistence_path_health(
                        reconciliation
                    ),
                }
        elif action_execution is None:
            paths = self._action_review_reconciliation_without_execution_path_health(
                action_request=action_request,
                approval_decision=approval_decision,
                reconciliation=reconciliation,
                review_state=review_state,
            )
        else:
            paths = {
                "ingest": self._action_review_ingest_path_health(reconciliation),
                "delegation": self._action_review_delegation_path_health(
                    action_request=action_request,
                    approval_decision=approval_decision,
                    action_execution=action_execution,
                    review_state=review_state,
                ),
                "provider": self._action_review_provider_path_health(action_execution),
                "persistence": self._action_review_persistence_path_health(reconciliation),
            }
        deadline = self._action_review_visibility_deadline(
            action_request=action_request,
            approval_decision=approval_decision,
            action_execution=action_execution,
        )
        if deadline is not None and deadline <= as_of:
            paths = self._action_review_overdue_path_health(
                review_state=review_state,
                action_execution=action_execution,
                paths=paths,
            )
        overall_state = self._action_review_overall_path_state(paths.values())
        return {
            "overall_state": overall_state,
            "summary": self._action_review_path_health_summary(
                overall_state=overall_state,
                paths=paths,
            ),
            "paths": paths,
        }

    @staticmethod
    def _action_review_terminal_non_delegated_path_health() -> dict[str, dict[str, str]]:
        return {
            "ingest": {
                "state": "healthy",
                "reason": "review_closed_before_ingest",
            },
            "delegation": {
                "state": "healthy",
                "reason": "review_closed_without_delegation",
            },
            "provider": {
                "state": "healthy",
                "reason": "review_closed_before_provider",
            },
            "persistence": {
                "state": "healthy",
                "reason": "review_closed_before_reconciliation",
            },
        }

    @staticmethod
    def _action_review_unresolved_without_execution_path_health() -> (
        dict[str, dict[str, str]]
    ):
        return {
            "ingest": {
                "state": "degraded",
                "reason": "ingest_signal_missing_after_approval",
            },
            "delegation": {
                "state": "degraded",
                "reason": "reviewed_delegation_missing_after_approval",
            },
            "provider": {
                "state": "degraded",
                "reason": "provider_signal_missing_after_approval",
            },
            "persistence": {
                "state": "degraded",
                "reason": "reconciliation_missing_after_approval",
            },
        }

    def _action_review_reconciliation_without_execution_path_health(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        reconciliation: ReconciliationRecord,
        review_state: str,
    ) -> dict[str, dict[str, str]]:
        delegation_path = self._action_review_delegation_path_health(
            action_request=action_request,
            approval_decision=approval_decision,
            action_execution=None,
            review_state=review_state,
        )
        if delegation_path["state"] != "healthy":
            delegation_path = {
                "state": "degraded",
                "reason": "reviewed_delegation_record_missing",
            }
        return {
            "ingest": self._action_review_ingest_path_health(reconciliation),
            "delegation": delegation_path,
            "provider": {
                "state": "degraded",
                "reason": "provider_execution_record_missing",
            },
            "persistence": {
                "state": "degraded",
                "reason": "reconciliation_execution_lineage_missing",
            },
        }

    @staticmethod
    def _action_review_visibility_deadline(
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
    ) -> datetime | None:
        return min(
            (
                candidate
                for candidate in (
                    None if action_execution is None else action_execution.expires_at,
                    (
                        None
                        if approval_decision is None
                        else approval_decision.approved_expires_at
                    ),
                    action_request.expires_at,
                )
                if candidate is not None
            ),
            default=None,
        )

    @classmethod
    def _action_review_overdue_path_health(
        cls,
        *,
        review_state: str,
        action_execution: ActionExecutionRecord | None,
        paths: Mapping[str, Mapping[str, str]],
    ) -> dict[str, dict[str, str]]:
        if action_execution is None:
            if review_state in {"approved", "executing"}:
                return cls._action_review_unresolved_without_execution_path_health()
            return {path_name: dict(path) for path_name, path in paths.items()}

        overdue_paths = {path_name: dict(path) for path_name, path in paths.items()}
        if overdue_paths["ingest"].get("reason") == "awaiting_ingest_signal":
            overdue_paths["ingest"] = {
                "state": "degraded",
                "reason": "ingest_signal_timeout",
            }
        if overdue_paths["delegation"].get("reason") == "awaiting_receipt":
            overdue_paths["delegation"] = {
                "state": "degraded",
                "reason": "delegation_receipt_timeout",
            }
        if overdue_paths["provider"].get("reason") == "awaiting_provider_receipt":
            overdue_paths["provider"] = {
                "state": "degraded",
                "reason": "provider_receipt_timeout",
            }
        elif overdue_paths["provider"].get("reason") == "awaiting_authoritative_outcome":
            overdue_paths["provider"] = {
                "state": "degraded",
                "reason": "authoritative_outcome_timeout",
            }
        if overdue_paths["persistence"].get("reason") == "awaiting_reconciliation":
            overdue_paths["persistence"] = {
                "state": "degraded",
                "reason": "reconciliation_timeout",
            }
        return overdue_paths

    @staticmethod
    def _action_review_ingest_path_health(
        reconciliation: ReconciliationRecord | None,
    ) -> dict[str, str]:
        if reconciliation is None:
            return {
                "state": "delayed",
                "reason": "awaiting_ingest_signal",
            }
        return {
            "matched": {
                "state": "healthy",
                "reason": "observations_current",
            },
            "missing": {
                "state": "delayed",
                "reason": "observation_missing",
            },
            "stale": {
                "state": "degraded",
                "reason": "stale_observation",
            },
            "duplicate": {
                "state": "degraded",
                "reason": "duplicate_observations",
            },
            "mismatch": {
                "state": "degraded",
                "reason": "mismatch_detected",
            },
        }.get(
            reconciliation.ingest_disposition,
            {
                "state": "degraded",
                "reason": "ingest_anomaly",
            },
        )

    @staticmethod
    def _action_review_delegation_path_health(
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        review_state: str,
    ) -> dict[str, str]:
        if action_execution is not None:
            if action_execution.lifecycle_state == "dispatching":
                return {
                    "state": "delayed",
                    "reason": "awaiting_receipt",
                }
            return {
                "state": "healthy",
                "reason": "delegated",
            }
        if approval_decision is not None and approval_decision.lifecycle_state == "approved":
            return {
                "state": "delayed",
                "reason": "awaiting_reviewed_delegation",
            }
        if review_state == "approved" or action_request.lifecycle_state == "approved":
            return {
                "state": "delayed",
                "reason": "awaiting_reviewed_delegation",
            }
        return {
            "state": "delayed",
            "reason": "awaiting_approval",
        }

    @staticmethod
    def _action_review_provider_path_health(
        action_execution: ActionExecutionRecord | None,
    ) -> dict[str, str]:
        if action_execution is None:
            return {
                "state": "delayed",
                "reason": "awaiting_delegation",
            }
        return {
            "dispatching": {
                "state": "delayed",
                "reason": "awaiting_provider_receipt",
            },
            "queued": {
                "state": "delayed",
                "reason": "awaiting_authoritative_outcome",
            },
            "running": {
                "state": "delayed",
                "reason": "awaiting_authoritative_outcome",
            },
            "succeeded": {
                "state": "healthy",
                "reason": "execution_succeeded",
            },
            "failed": {
                "state": "failed",
                "reason": "execution_failed",
            },
            "canceled": {
                "state": "failed",
                "reason": "execution_canceled",
            },
            "unresolved": {
                "state": "degraded",
                "reason": "execution_unresolved",
            },
            "expired": {
                "state": "failed",
                "reason": "execution_expired",
            },
            "rejected": {
                "state": "failed",
                "reason": "execution_rejected",
            },
            "superseded": {
                "state": "degraded",
                "reason": "execution_superseded",
            },
        }.get(
            action_execution.lifecycle_state,
            {
                "state": "degraded",
                "reason": "provider_anomaly",
            },
        )

    @staticmethod
    def _action_review_persistence_path_health(
        reconciliation: ReconciliationRecord | None,
    ) -> dict[str, str]:
        if reconciliation is None:
            return {
                "state": "delayed",
                "reason": "awaiting_reconciliation",
            }
        return {
            "matched": {
                "state": "healthy",
                "reason": "reconciliation_matched",
            },
            "pending": {
                "state": "delayed",
                "reason": "reconciliation_pending",
            },
            "mismatched": {
                "state": "degraded",
                "reason": "reconciliation_mismatched",
            },
            "stale": {
                "state": "degraded",
                "reason": "reconciliation_stale",
            },
        }.get(
            reconciliation.lifecycle_state,
            {
                "state": "degraded",
                "reason": "persistence_anomaly",
            },
        )

    @staticmethod
    def _action_review_overall_path_state(
        paths: Iterable[Mapping[str, str]],
    ) -> str:
        severity = {
            "healthy": 0,
            "delayed": 1,
            "degraded": 2,
            "failed": 3,
        }
        highest = max(
            (
                severity.get(path.get("state", "degraded"), severity["degraded"])
                for path in paths
            ),
            default=severity["healthy"],
        )
        for state, rank in severity.items():
            if rank == highest:
                return state
        return "degraded"

    @staticmethod
    def _action_review_path_health_summary(
        *,
        overall_state: str,
        paths: Mapping[str, Mapping[str, str]],
    ) -> str:
        active_paths = [
            f"{path_name} {path['reason'].replace('_', ' ')}"
            for path_name, path in paths.items()
            if path.get("state") != "healthy"
        ]
        if not active_paths:
            return "all reviewed execution visibility paths are healthy"
        primary = active_paths[:2]
        joined = "; ".join(primary)
        return f"{overall_state} path visibility: {joined}"

    def _build_readiness_review_path_health(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
        readiness_review_snapshots: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        if readiness_review_snapshots is None:
            readiness_review_snapshots = self._collect_readiness_review_snapshots(
                readiness_aggregates
            )
        review_path_health = [
            snapshot["path_health"] for snapshot in readiness_review_snapshots
        ]

        if not review_path_health:
            return {
                "review_count": 0,
                "overall_state": "healthy",
                "summary": "no active reviewed execution visibility gaps",
                "paths": {
                    path_name: {
                        "state": "healthy",
                        "reason": "no_reviewed_paths_tracked",
                        "affected_reviews": 0,
                        "by_state": {
                            "healthy": 0,
                            "delayed": 0,
                            "degraded": 0,
                            "failed": 0,
                        },
                    }
                    for path_name in ("ingest", "delegation", "provider", "persistence")
                },
            }

        paths = {
            path_name: self._aggregate_readiness_path_health(
                path_name=path_name,
                review_path_health=review_path_health,
            )
            for path_name in ("ingest", "delegation", "provider", "persistence")
        }
        overall_state = self._action_review_overall_path_state(paths.values())
        return {
            "review_count": len(review_path_health),
            "overall_state": overall_state,
            "summary": self._action_review_path_health_summary(
                overall_state=overall_state,
                paths=paths,
            ),
            "paths": paths,
        }

    def _collect_readiness_review_snapshots(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
    ) -> list[dict[str, object]]:
        execution_ids = set(readiness_aggregates.active_action_execution_ids)
        execution_ids.update(readiness_aggregates.terminal_action_execution_ids)
        candidate_action_request_ids: set[str] = set()
        unresolved_delegation_ids: set[str] = set()

        for action_request_id in readiness_aggregates.active_action_request_ids:
            action_request = self._store.get(ActionRequestRecord, action_request_id)
            if action_request is None:
                continue
            if action_request.lifecycle_state in {
                "approved",
                "executing",
                "unresolved",
            }:
                candidate_action_request_ids.add(action_request_id)

        for action_request_id in (
            readiness_aggregates.terminal_review_outcome_action_request_ids
        ):
            action_request = self._store.get(ActionRequestRecord, action_request_id)
            if (
                action_request is not None
                and action_request.approval_decision_id is not None
                and self._action_request_is_review_bound(action_request)
            ):
                candidate_action_request_ids.add(action_request_id)

        for reconciliation_id in readiness_aggregates.unresolved_reconciliation_ids:
            reconciliation = self._store.get(ReconciliationRecord, reconciliation_id)
            if reconciliation is None:
                continue
            candidate_action_request_ids.update(
                self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    "action_request_ids",
                )
            )
            for approval_decision_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            ):
                approval_decision = self._store.get(
                    ApprovalDecisionRecord,
                    approval_decision_id,
                )
                if approval_decision is not None:
                    candidate_action_request_ids.add(approval_decision.action_request_id)
            execution_ids.update(
                self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    "action_execution_ids",
                )
            )
            unresolved_delegation_ids.update(
                self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    "delegation_ids",
                )
            )

        candidate_action_request_ids.update(
            self._readiness_candidate_action_request_ids_for_delegations(
                unresolved_delegation_ids
            )
        )

        executions_by_action_request_id: dict[str, ActionExecutionRecord] = {}
        for action_execution_id in execution_ids:
            action_execution = self._store.get(ActionExecutionRecord, action_execution_id)
            if action_execution is None:
                continue
            candidate_action_request_ids.add(action_execution.action_request_id)
            existing_execution = executions_by_action_request_id.get(
                action_execution.action_request_id
            )
            if existing_execution is None or (
                action_execution.delegated_at,
                action_execution.action_execution_id,
            ) > (
                existing_execution.delegated_at,
                existing_execution.action_execution_id,
            ):
                executions_by_action_request_id[action_execution.action_request_id] = (
                    action_execution
                )

        candidate_action_requests: dict[str, ActionRequestRecord] = {}
        approval_decisions_by_action_request_id: dict[str, ApprovalDecisionRecord] = {}
        for action_request_id in sorted(candidate_action_request_ids):
            action_request = self._store.get(ActionRequestRecord, action_request_id)
            if action_request is None or not self._action_request_is_review_bound(
                action_request
            ):
                continue
            candidate_action_requests[action_request_id] = action_request
            if action_request.approval_decision_id is None:
                continue
            approval_decision = self._store.get(
                ApprovalDecisionRecord,
                action_request.approval_decision_id,
            )
            if approval_decision is not None:
                approval_decisions_by_action_request_id[action_request_id] = (
                    approval_decision
                )

        targeted_record_index = self._build_readiness_review_record_index(
            action_requests=tuple(candidate_action_requests.values()),
            approval_decisions=tuple(approval_decisions_by_action_request_id.values()),
        )
        reconciliations_by_action_request_id: dict[str, ReconciliationRecord] = {}
        if targeted_record_index is not None:
            executions_by_action_request_id = {}
            for action_request_id, execution_records in (
                targeted_record_index.executions_by_action_request_id.items()
            ):
                executions_by_action_request_id[action_request_id] = max(
                    execution_records,
                    key=lambda record: (
                        record.delegated_at,
                        record.action_execution_id,
                    ),
                )
            for action_request_id, action_request in candidate_action_requests.items():
                approval_decision = approval_decisions_by_action_request_id.get(
                    action_request_id
                )
                action_execution = executions_by_action_request_id.get(action_request_id)
                reconciliation = self._latest_action_review_reconciliation(
                    action_request=action_request,
                    approval_decision=approval_decision,
                    action_execution=action_execution,
                    record_index=targeted_record_index,
                )
                if reconciliation is not None:
                    reconciliations_by_action_request_id[action_request_id] = reconciliation

        if targeted_record_index is None and candidate_action_requests:
            current_execution_request_ids_by_execution_id: dict[str, str] = {}
            current_execution_request_ids_by_delegation_id: dict[str, str] = {}
            approval_action_request_ids_by_id = {
                approval_decision.approval_decision_id: action_request_id
                for action_request_id, approval_decision in (
                    approval_decisions_by_action_request_id.items()
                )
            }
            for action_execution in self._store.list(ActionExecutionRecord):
                if action_execution.action_request_id not in candidate_action_requests:
                    continue
                existing_execution = executions_by_action_request_id.get(
                    action_execution.action_request_id
                )
                if existing_execution is None or (
                    action_execution.delegated_at,
                    action_execution.action_execution_id,
                ) > (
                    existing_execution.delegated_at,
                    existing_execution.action_execution_id,
                ):
                    executions_by_action_request_id[action_execution.action_request_id] = (
                        action_execution
                    )

            for action_request_id, action_execution in executions_by_action_request_id.items():
                current_execution_request_ids_by_execution_id[
                    action_execution.action_execution_id
                ] = action_request_id
                current_execution_request_ids_by_delegation_id[
                    action_execution.delegation_id
                ] = action_request_id

            for reconciliation in self._store.list(ReconciliationRecord):
                matched_action_request_ids = {
                    action_request_id
                    for action_request_id in self._assistant_ids_from_mapping(
                        reconciliation.subject_linkage,
                        "action_request_ids",
                    )
                    if action_request_id in candidate_action_requests
                }
                matched_action_request_ids.update(
                    approval_action_request_ids_by_id[approval_decision_id]
                    for approval_decision_id in self._assistant_ids_from_mapping(
                        reconciliation.subject_linkage,
                        "approval_decision_ids",
                    )
                    if approval_decision_id in approval_action_request_ids_by_id
                )
                matched_action_request_ids.update(
                    current_execution_request_ids_by_execution_id[action_execution_id]
                    for action_execution_id in self._assistant_ids_from_mapping(
                        reconciliation.subject_linkage,
                        "action_execution_ids",
                    )
                    if action_execution_id in current_execution_request_ids_by_execution_id
                )
                matched_action_request_ids.update(
                    current_execution_request_ids_by_delegation_id[delegation_id]
                    for delegation_id in self._assistant_ids_from_mapping(
                        reconciliation.subject_linkage,
                        "delegation_ids",
                    )
                    if delegation_id in current_execution_request_ids_by_delegation_id
                )
                for action_request_id in matched_action_request_ids:
                    existing_reconciliation = reconciliations_by_action_request_id.get(
                        action_request_id
                    )
                    if existing_reconciliation is None or (
                        reconciliation.compared_at,
                        reconciliation.reconciliation_id,
                    ) > (
                        existing_reconciliation.compared_at,
                        existing_reconciliation.reconciliation_id,
                    ):
                        reconciliations_by_action_request_id[action_request_id] = (
                            reconciliation
                        )

        readiness_review_snapshots: list[dict[str, object]] = []
        path_health_as_of = datetime.now(timezone.utc)
        for action_request_id, action_request in sorted(candidate_action_requests.items()):
            approval_decision = approval_decisions_by_action_request_id.get(action_request_id)
            action_execution = executions_by_action_request_id.get(action_request_id)
            reconciliation = reconciliations_by_action_request_id.get(action_request_id)
            approval_state = self._action_review_approval_state(
                action_request=action_request,
                approval_decision=approval_decision,
            )
            review_state = self._action_review_state(
                action_request=action_request,
                approval_state=approval_state,
                action_execution=action_execution,
            )
            reviewed_context = self._action_review_visibility_context(action_request)
            path_health = self._action_review_path_health(
                action_request=action_request,
                approval_decision=approval_decision,
                action_execution=action_execution,
                reconciliation=reconciliation,
                review_state=review_state,
                as_of=path_health_as_of,
            )
            readiness_review_snapshots.append(
                {
                    "action_request_id": action_request_id,
                    "source_family": (
                        self._reviewed_operator_source_family(reviewed_context)
                        if reviewed_context is not None
                        else None
                    ),
                    "ingest_expected": (
                        action_execution is not None or reconciliation is not None
                    ),
                    "execution_surface_type": (
                        action_execution.execution_surface_type
                        if action_execution is not None
                        else action_request.policy_evaluation.get("execution_surface_type")
                    ),
                    "execution_surface_id": (
                        action_execution.execution_surface_id
                        if action_execution is not None
                        else action_request.policy_evaluation.get("execution_surface_id")
                    ),
                    "path_health": path_health,
                }
            )
        return readiness_review_snapshots

    def _build_readiness_source_health(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
        readiness_review_snapshots: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        if readiness_review_snapshots is None:
            readiness_review_snapshots = self._collect_readiness_review_snapshots(
                readiness_aggregates
            )
        source_reviews: defaultdict[str, list[Mapping[str, object]]] = defaultdict(list)
        for snapshot in readiness_review_snapshots:
            if not snapshot.get("ingest_expected", False):
                continue
            source_family = snapshot.get("source_family")
            normalized_source_family = (
                str(source_family).strip()
                if isinstance(source_family, str) and source_family.strip()
                else "unknown_reviewed_source"
            )
            source_reviews[normalized_source_family].append(snapshot["path_health"])

        if not source_reviews:
            return {
                "tracked_sources": 0,
                "overall_state": "healthy",
                "summary": "no reviewed source health tracked",
                "sources": {},
            }

        sources: dict[str, dict[str, object]] = {}
        for source_family, review_path_health in sorted(source_reviews.items()):
            ingest_path = self._aggregate_readiness_path_health(
                path_name="ingest",
                review_path_health=review_path_health,
            )
            sources[source_family] = {
                "state": ingest_path["state"],
                "reason": ingest_path["reason"],
                "tracked_reviews": len(review_path_health),
                "affected_reviews": ingest_path["affected_reviews"],
                "by_state": ingest_path["by_state"],
            }

        overall_state = self._action_review_overall_path_state(sources.values())
        return {
            "tracked_sources": len(sources),
            "overall_state": overall_state,
            "summary": self._readiness_surface_health_summary(
                overall_state=overall_state,
                entries=sources,
                kind="source",
            ),
            "sources": sources,
        }

    def _build_readiness_automation_substrate_health(
        self,
        readiness_aggregates: ReadinessDiagnosticsAggregates,
        readiness_review_snapshots: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        if readiness_review_snapshots is None:
            readiness_review_snapshots = self._collect_readiness_review_snapshots(
                readiness_aggregates
            )
        surface_reviews: defaultdict[str, list[dict[str, object]]] = defaultdict(list)
        surface_metadata: dict[str, tuple[str, str]] = {}
        for snapshot in readiness_review_snapshots:
            execution_surface_type = snapshot.get("execution_surface_type")
            if execution_surface_type != "automation_substrate":
                continue
            execution_surface_id = snapshot.get("execution_surface_id")
            normalized_surface_id = (
                str(execution_surface_id).strip()
                if isinstance(execution_surface_id, str) and execution_surface_id.strip()
                else "unknown"
            )
            surface_key = f"automation_substrate:{normalized_surface_id}"
            surface_reviews[surface_key].append(snapshot)
            surface_metadata[surface_key] = ("automation_substrate", normalized_surface_id)

        if not surface_reviews:
            return {
                "tracked_surfaces": 0,
                "overall_state": "healthy",
                "summary": "no reviewed automation substrate health tracked",
                "surfaces": {},
            }

        surfaces: dict[str, dict[str, object]] = {}
        for surface_key, surface_review_snapshots in sorted(surface_reviews.items()):
            review_path_health = [
                snapshot["path_health"] for snapshot in surface_review_snapshots
            ]
            aggregated_paths = {
                path_name: self._aggregate_readiness_path_health(
                    path_name=path_name,
                    review_path_health=review_path_health,
                )
                for path_name in ("delegation", "provider", "persistence")
            }
            overall_state = self._action_review_overall_path_state(
                aggregated_paths.values()
            )
            execution_surface_type, execution_surface_id = surface_metadata[surface_key]
            surfaces[surface_key] = {
                "execution_surface_type": execution_surface_type,
                "execution_surface_id": execution_surface_id,
                "state": overall_state,
                "reason": self._readiness_dominant_reason(
                    aggregated_paths.values(),
                    overall_state=overall_state,
                ),
                "tracked_reviews": len(surface_review_snapshots),
                "affected_reviews": self._count_readiness_affected_reviews(
                    surface_review_snapshots,
                    path_names=("delegation", "provider", "persistence"),
                ),
                "paths": aggregated_paths,
            }

        overall_state = self._action_review_overall_path_state(surfaces.values())
        return {
            "tracked_surfaces": len(surfaces),
            "overall_state": overall_state,
            "summary": self._readiness_surface_health_summary(
                overall_state=overall_state,
                entries=surfaces,
                kind="automation substrate",
            ),
            "surfaces": surfaces,
        }

    @staticmethod
    def _readiness_dominant_reason(
        paths: Iterable[Mapping[str, object]],
        *,
        overall_state: str,
    ) -> str:
        reason_counts: Counter[str] = Counter()
        for path in paths:
            if path.get("state") != overall_state:
                continue
            by_state = path.get("by_state")
            weight = (
                int(by_state.get(overall_state, 0))
                if isinstance(by_state, Mapping)
                else int(path.get("affected_reviews", 0))
            )
            reason_counts[str(path["reason"])] += max(weight, 1)
        return sorted(
            reason_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[0][0]

    def _readiness_surface_health_summary(
        self,
        *,
        overall_state: str,
        entries: Mapping[str, Mapping[str, object]],
        kind: str,
    ) -> str:
        active_entries = [
            f"{entry_name} {entry['reason'].replace('_', ' ')}"
            for entry_name, entry in entries.items()
            if entry.get("state") != "healthy"
        ]
        if not active_entries:
            return f"all reviewed {kind} health surfaces are healthy"
        return f"{overall_state} {kind} health: {'; '.join(active_entries[:2])}"

    def _readiness_candidate_action_request_ids_for_delegations(
        self,
        delegation_ids: set[str],
    ) -> set[str]:
        if not delegation_ids:
            return set()

        record_reader = getattr(self._store, "inspect_readiness_review_path_records", None)
        if callable(record_reader):
            readiness_records: ReadinessReviewPathRecords = record_reader(
                action_request_ids=(),
                approval_decision_ids=(),
                delegation_ids=tuple(sorted(delegation_ids)),
            )
            return {
                action_execution.action_request_id
                for action_execution in readiness_records.action_executions
            }

        pending_delegation_ids = set(delegation_ids)
        candidate_action_request_ids: set[str] = set()
        for action_execution in self._store.list(ActionExecutionRecord):
            if action_execution.delegation_id not in pending_delegation_ids:
                continue
            candidate_action_request_ids.add(action_execution.action_request_id)
            pending_delegation_ids.discard(action_execution.delegation_id)
            if not pending_delegation_ids:
                break
        return candidate_action_request_ids

    def _build_readiness_review_record_index(
        self,
        *,
        action_requests: tuple[ActionRequestRecord, ...],
        approval_decisions: tuple[ApprovalDecisionRecord, ...],
    ) -> _ActionReviewRecordIndex | None:
        if not action_requests:
            return None
        record_reader = getattr(self._store, "inspect_readiness_review_path_records", None)
        if not callable(record_reader):
            return None
        readiness_records: ReadinessReviewPathRecords = record_reader(
            action_request_ids=tuple(
                sorted(
                    {
                        action_request.action_request_id
                        for action_request in action_requests
                    }
                )
            ),
            approval_decision_ids=tuple(
                sorted(
                    {
                        approval_decision.approval_decision_id
                        for approval_decision in approval_decisions
                    }
                )
            ),
        )
        executions_by_action_request_id: defaultdict[
            str,
            list[ActionExecutionRecord],
        ] = defaultdict(list)
        for action_execution in readiness_records.action_executions:
            executions_by_action_request_id[action_execution.action_request_id].append(
                action_execution
            )

        reconciliations_by_action_request_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_approval_decision_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_action_execution_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        reconciliations_by_delegation_id: defaultdict[
            str,
            list[ReconciliationRecord],
        ] = defaultdict(list)
        for reconciliation in readiness_records.reconciliations:
            for action_request_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_request_ids",
            ):
                reconciliations_by_action_request_id[action_request_id].append(
                    reconciliation
                )
            for approval_decision_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "approval_decision_ids",
            ):
                reconciliations_by_approval_decision_id[approval_decision_id].append(
                    reconciliation
                )
            for action_execution_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            ):
                reconciliations_by_action_execution_id[action_execution_id].append(
                    reconciliation
                )
            for delegation_id in self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "delegation_ids",
            ):
                reconciliations_by_delegation_id[delegation_id].append(reconciliation)

        return _ActionReviewRecordIndex(
            requests_by_case_id={},
            requests_by_alert_id={},
            requests_by_scope={},
            approvals_by_id={
                approval_decision.approval_decision_id: approval_decision
                for approval_decision in approval_decisions
            },
            approvals_by_action_request_id={},
            executions_by_action_request_id={
                key: tuple(records)
                for key, records in executions_by_action_request_id.items()
            },
            reconciliations_by_action_request_id={
                key: tuple(records)
                for key, records in reconciliations_by_action_request_id.items()
            },
            reconciliations_by_approval_decision_id={
                key: tuple(records)
                for key, records in reconciliations_by_approval_decision_id.items()
            },
            reconciliations_by_action_execution_id={
                key: tuple(records)
                for key, records in reconciliations_by_action_execution_id.items()
            },
            reconciliations_by_delegation_id={
                key: tuple(records)
                for key, records in reconciliations_by_delegation_id.items()
            },
        )

    def _aggregate_readiness_path_health(
        self,
        *,
        path_name: str,
        review_path_health: Iterable[Mapping[str, object]],
    ) -> dict[str, object]:
        path_snapshots = [
            path_health["paths"][path_name]
            for path_health in review_path_health
        ]
        state_counts = Counter(
            str(path_snapshot["state"]) for path_snapshot in path_snapshots
        )
        overall_state = self._action_review_overall_path_state(path_snapshots)
        reason_counts = Counter(
            str(path_snapshot["reason"])
            for path_snapshot in path_snapshots
            if path_snapshot["state"] == overall_state
        )
        reason = sorted(
            reason_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )[0][0]
        return {
            "state": overall_state,
            "reason": reason,
            "affected_reviews": sum(
                count for state, count in state_counts.items() if state != "healthy"
            ),
            "by_state": {
                "healthy": state_counts.get("healthy", 0),
                "delayed": state_counts.get("delayed", 0),
                "degraded": state_counts.get("degraded", 0),
                "failed": state_counts.get("failed", 0),
            },
        }

    @staticmethod
    def _count_readiness_affected_reviews(
        readiness_review_snapshots: Iterable[Mapping[str, object]],
        *,
        path_names: Iterable[str],
    ) -> int:
        relevant_path_names = tuple(path_names)
        return len(
            {
                str(snapshot["action_request_id"])
                for snapshot in readiness_review_snapshots
                if any(
                    snapshot["path_health"]["paths"][path_name]["state"] != "healthy"
                    for path_name in relevant_path_names
                )
            }
        )

    def _action_review_runtime_visibility(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        review_state: str,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> dict[str, object] | None:
        reviewed_context = self._action_review_visibility_context(action_request)
        if reviewed_context is None:
            return None

        allow_unscoped_action_visibility = self._case_has_single_review_bound_action_request(
            action_request.case_id,
            record_index=record_index,
        )
        visibility: dict[str, object] = {}
        after_hours_handoff = self._action_review_after_hours_handoff_visibility(
            reviewed_context=reviewed_context,
            review_state=review_state,
        )
        if after_hours_handoff is not None:
            visibility["after_hours_handoff"] = after_hours_handoff

        manual_fallback = self._action_review_manual_fallback_visibility(
            reviewed_context=reviewed_context,
            action_request=action_request,
            approval_decision=approval_decision,
            review_state=review_state,
            allow_unscoped_context=allow_unscoped_action_visibility,
        )
        if manual_fallback is not None:
            visibility["manual_fallback"] = manual_fallback

        escalation_notes = self._action_review_escalation_visibility(
            reviewed_context=reviewed_context,
            action_request=action_request,
            approval_decision=approval_decision,
            review_state=review_state,
            allow_unscoped_context=allow_unscoped_action_visibility,
        )
        if escalation_notes is not None:
            visibility["escalation_notes"] = escalation_notes

        return visibility or None

    @staticmethod
    def _action_review_after_hours_handoff_visibility(
        *,
        reviewed_context: Mapping[str, object],
        review_state: str,
    ) -> dict[str, object] | None:
        if review_state in {"completed", "failed", "canceled"}:
            return None
        handoff = reviewed_context.get("handoff")
        triage = reviewed_context.get("triage")
        triage_disposition = triage.get("disposition") if isinstance(triage, Mapping) else None
        if (
            not isinstance(handoff, Mapping)
            and triage_disposition not in _AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS
        ):
            return None

        visibility: dict[str, object] = {}
        if isinstance(handoff, Mapping):
            for source_key, target_key in (
                ("handoff_at", "handoff_at"),
                ("handoff_owner", "handoff_owner"),
                ("note", "note"),
                ("follow_up_evidence_ids", "follow_up_evidence_ids"),
            ):
                value = handoff.get(source_key)
                if value is not None:
                    visibility[target_key] = value
        if (
            isinstance(triage, Mapping)
            and triage_disposition in _AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS
        ):
            for source_key, target_key in (
                ("disposition", "disposition"),
                ("recorded_at", "recorded_at"),
            ):
                value = triage.get(source_key)
                if value is not None:
                    visibility[target_key] = value
            rationale = triage.get("closure_rationale")
            if rationale is None:
                rationale = triage.get("rationale")
            if rationale is not None:
                visibility["rationale"] = rationale
        return visibility or None

    def _action_review_visibility_context(
        self,
        action_request: ActionRequestRecord,
    ) -> Mapping[str, object] | None:
        case = (
            self._store.get(CaseRecord, action_request.case_id)
            if action_request.case_id is not None
            else None
        )
        alert = (
            self._store.get(AlertRecord, action_request.alert_id)
            if action_request.alert_id is not None
            else None
        )
        if case is not None and isinstance(case.reviewed_context, Mapping):
            return case.reviewed_context
        if alert is not None and isinstance(alert.reviewed_context, Mapping):
            return alert.reviewed_context
        return None

    @staticmethod
    def _action_review_manual_fallback_visibility(
        *,
        reviewed_context: Mapping[str, object],
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        review_state: str,
        allow_unscoped_context: bool,
    ) -> dict[str, object] | None:
        manual_fallback = AegisOpsControlPlaneService._action_review_visibility_entry(
            reviewed_context=reviewed_context,
            action_request_id=action_request.action_request_id,
            context_key="manual_fallback",
        )
        if not isinstance(manual_fallback, Mapping):
            return None

        approval_decision_id = (
            approval_decision.approval_decision_id
            if approval_decision is not None
            else action_request.approval_decision_id
        )
        if (
            approval_decision is None
            or approval_decision.lifecycle_state != "approved"
            or review_state in {"pending", "rejected", "expired", "superseded"}
        ):
            return None
        if not AegisOpsControlPlaneService._action_review_context_matches_lineage(
            visibility_context=manual_fallback,
            action_request_id=action_request.action_request_id,
            approval_decision_id=approval_decision_id,
            allow_unscoped_context=allow_unscoped_context,
        ):
            return None

        visibility: dict[str, object] = {}
        for source_key in ("action_request_id", "approval_decision_id"):
            value = manual_fallback.get(source_key)
            if value is not None:
                visibility[source_key] = value
        for source_key, target_key in (
            ("fallback_at", "fallback_at"),
            ("performed_at", "fallback_at"),
            ("fallback_actor_identity", "fallback_actor_identity"),
            ("authority_boundary", "authority_boundary"),
            ("reason", "reason"),
            ("action_taken", "action_taken"),
            ("verification_evidence_ids", "verification_evidence_ids"),
            ("residual_uncertainty", "residual_uncertainty"),
        ):
            value = manual_fallback.get(source_key)
            if value is None:
                continue
            if source_key == "performed_at" and target_key in visibility:
                continue
            visibility[target_key] = value
        return visibility

    @staticmethod
    def _action_review_escalation_visibility(
        *,
        reviewed_context: Mapping[str, object],
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        review_state: str,
        allow_unscoped_context: bool,
    ) -> dict[str, object] | None:
        requested_payload = action_request.requested_payload
        escalation_context = AegisOpsControlPlaneService._action_review_visibility_entry(
            reviewed_context=reviewed_context,
            action_request_id=action_request.action_request_id,
            context_key="escalation",
        )
        if not isinstance(escalation_context, Mapping):
            return None

        approval_decision_id = (
            approval_decision.approval_decision_id
            if approval_decision is not None
            else action_request.approval_decision_id
        )
        if not AegisOpsControlPlaneService._action_review_context_matches_lineage(
            visibility_context=escalation_context,
            action_request_id=action_request.action_request_id,
            approval_decision_id=approval_decision_id,
            allow_unscoped_context=allow_unscoped_context,
        ):
            return None

        recorded_review_state = escalation_context.get("review_state")
        visibility: dict[str, object] = {
            "action_request_id": action_request.action_request_id,
            "approval_decision_id": approval_decision_id,
            "requester_identity": action_request.requester_identity,
            "review_state": (
                recorded_review_state
                if isinstance(recorded_review_state, str) and recorded_review_state.strip()
                else review_state
            ),
        }
        escalation_reason = requested_payload.get("escalation_reason")
        if escalation_reason is not None:
            visibility["escalation_reason"] = escalation_reason
        for source_key, target_key in (
            ("escalated_at", "escalated_at"),
            ("escalated_to", "escalated_to"),
            ("escalated_by_identity", "escalated_by_identity"),
            ("note", "note"),
        ):
            value = escalation_context.get(source_key)
            if value is not None:
                visibility[target_key] = value
        return visibility

    @staticmethod
    def _action_review_context_matches_lineage(
        *,
        visibility_context: Mapping[str, object],
        action_request_id: str,
        approval_decision_id: str | None,
        allow_unscoped_context: bool,
    ) -> bool:
        scoped_action_request_id = visibility_context.get("action_request_id")
        scoped_approval_decision_id = visibility_context.get("approval_decision_id")

        if scoped_action_request_id is None:
            if scoped_approval_decision_id is not None:
                return (
                    approval_decision_id is not None
                    and scoped_approval_decision_id == approval_decision_id
                )
            return allow_unscoped_context

        if scoped_action_request_id != action_request_id:
            return False
        if scoped_approval_decision_id is not None:
            return (
                approval_decision_id is not None
                and scoped_approval_decision_id == approval_decision_id
            )
        return True

    @staticmethod
    def _action_review_visibility_entry(
        *,
        reviewed_context: Mapping[str, object],
        action_request_id: str,
        context_key: str,
    ) -> Mapping[str, object] | None:
        action_review_visibility = reviewed_context.get("action_review_visibility")
        if isinstance(action_review_visibility, Mapping):
            scoped_visibility = action_review_visibility.get(action_request_id)
            if isinstance(scoped_visibility, Mapping):
                scoped_entry = scoped_visibility.get(context_key)
                if isinstance(scoped_entry, Mapping):
                    return scoped_entry
        legacy_entry = reviewed_context.get(context_key)
        if isinstance(legacy_entry, Mapping):
            return legacy_entry
        return None

    @staticmethod
    def _action_review_visibility_update(
        *,
        action_request_id: str,
        context_key: str,
        context_value: Mapping[str, object],
    ) -> dict[str, object]:
        return {
            "action_review_visibility": {
                action_request_id: {
                    context_key: dict(context_value),
                }
            }
        }

    def _case_has_single_review_bound_action_request(
        self,
        case_id: str | None,
        *,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> bool:
        if case_id is None:
            return False
        if record_index is not None:
            matching_requests = record_index.requests_by_case_id.get(case_id, ())
        else:
            matching_requests = tuple(
                record
                for record in self._store.list(ActionRequestRecord)
                if record.case_id == case_id
            )
        review_bound_count = sum(
            1
            for record in matching_requests
            if self._action_request_is_review_bound(record)
        )
        return review_bound_count == 1

    def _action_review_approval_decision(
        self,
        action_request: ActionRequestRecord,
        *,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> ApprovalDecisionRecord | None:
        if record_index is not None and action_request.approval_decision_id:
            decision = record_index.approvals_by_id.get(action_request.approval_decision_id)
            if decision is not None:
                return decision
        if action_request.approval_decision_id:
            decision = self._store.get(
                ApprovalDecisionRecord,
                action_request.approval_decision_id,
            )
            if decision is not None:
                return decision
        if record_index is not None:
            matches = list(
                record_index.approvals_by_action_request_id.get(
                    action_request.action_request_id,
                    (),
                )
            )
        else:
            matches = [
                record
                for record in self._store.list(ApprovalDecisionRecord)
                if record.action_request_id == action_request.action_request_id
            ]
        if not matches:
            return None
        matches.sort(
            key=lambda record: (
                record.decided_at or datetime.min.replace(tzinfo=timezone.utc),
                record.approval_decision_id,
            ),
            reverse=True,
        )
        return matches[0]

    def _action_review_execution(
        self,
        action_request: ActionRequestRecord,
        *,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> ActionExecutionRecord | None:
        if record_index is not None:
            matches = list(
                record_index.executions_by_action_request_id.get(
                    action_request.action_request_id,
                    (),
                )
            )
        else:
            matches = [
                record
                for record in self._store.list(ActionExecutionRecord)
                if record.action_request_id == action_request.action_request_id
            ]
        if not matches:
            return None
        matches.sort(
            key=lambda record: (
                record.delegated_at,
                record.action_execution_id,
            ),
            reverse=True,
        )
        return matches[0]

    def _latest_action_review_reconciliation(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> ReconciliationRecord | None:
        def _dedupe(
            reconciliations: tuple[ReconciliationRecord, ...] | list[ReconciliationRecord],
        ) -> list[ReconciliationRecord]:
            by_id: dict[str, ReconciliationRecord] = {}
            for reconciliation in reconciliations:
                by_id[reconciliation.reconciliation_id] = reconciliation
            return list(by_id.values())

        def _matches_current_execution_lineage(
            reconciliation: ReconciliationRecord,
        ) -> bool:
            if action_execution is None:
                return False
            subject_action_execution_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_execution_ids",
            )
            if action_execution.action_execution_id in subject_action_execution_ids:
                return True
            subject_delegation_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "delegation_ids",
            )
            return action_execution.delegation_id in subject_delegation_ids

        def _matches_review_lineage(reconciliation: ReconciliationRecord) -> bool:
            if _matches_current_execution_lineage(reconciliation):
                return True
            if approval_decision is not None:
                subject_approval_decision_ids = self._assistant_ids_from_mapping(
                    reconciliation.subject_linkage,
                    "approval_decision_ids",
                )
                if approval_decision.approval_decision_id in subject_approval_decision_ids:
                    return True
            subject_action_request_ids = self._assistant_ids_from_mapping(
                reconciliation.subject_linkage,
                "action_request_ids",
            )
            return action_request.action_request_id in subject_action_request_ids

        matches: list[ReconciliationRecord] = []
        if record_index is not None:
            indexed_matches: list[ReconciliationRecord] = list(
                record_index.reconciliations_by_action_request_id.get(
                    action_request.action_request_id,
                    (),
                )
            )
            if approval_decision is not None:
                indexed_matches += list(
                    record_index.reconciliations_by_approval_decision_id.get(
                        approval_decision.approval_decision_id,
                        (),
                    )
                )
            if action_execution is not None:
                indexed_matches += list(
                    record_index.reconciliations_by_action_execution_id.get(
                        action_execution.action_execution_id,
                        (),
                    )
                )
                indexed_matches += list(
                    record_index.reconciliations_by_delegation_id.get(
                        action_execution.delegation_id,
                        (),
                    )
                )
            matches = _dedupe(indexed_matches)
        else:
            for reconciliation in self._store.list(ReconciliationRecord):
                if _matches_review_lineage(reconciliation):
                    matches.append(reconciliation)
        if not matches:
            return None
        matches.sort(
            key=lambda record: (
                1 if _matches_current_execution_lineage(record) else 0,
                record.compared_at or record.last_seen_at or record.first_seen_at,
                record.reconciliation_id,
            ),
            reverse=True,
        )
        return matches[0]

    @staticmethod
    def _action_review_approval_state(
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
    ) -> str | None:
        if approval_decision is not None:
            return approval_decision.lifecycle_state
        if action_request.lifecycle_state == "pending_approval":
            return "pending"
        if action_request.lifecycle_state in {"rejected", "expired", "superseded", "canceled"}:
            return action_request.lifecycle_state
        return None

    @staticmethod
    def _action_review_state(
        *,
        action_request: ActionRequestRecord,
        approval_state: str | None,
        action_execution: ActionExecutionRecord | None,
    ) -> str:
        lifecycle_state = action_request.lifecycle_state
        execution_state = (
            action_execution.lifecycle_state if action_execution is not None else None
        )
        terminal_execution_review_states = {
            "succeeded": "completed",
            "failed": "failed",
            "canceled": "canceled",
            "superseded": "superseded",
            "unresolved": "unresolved",
            "expired": "expired",
            "rejected": "rejected",
        }
        if lifecycle_state in {"expired", "rejected", "superseded", "canceled"}:
            return lifecycle_state
        if lifecycle_state in {"completed", "failed", "unresolved"}:
            return lifecycle_state
        if execution_state in terminal_execution_review_states:
            return terminal_execution_review_states[execution_state]
        if execution_state is not None:
            return "executing"
        if lifecycle_state == "executing":
            return "executing"
        if approval_state in {"expired", "rejected", "superseded", "canceled"}:
            return approval_state
        if approval_state == "approved":
            return "approved"
        if lifecycle_state == "approved":
            return "approved"
        if lifecycle_state == "pending_approval" or approval_state == "pending":
            return "pending"
        return lifecycle_state

    def _replacement_action_request(
        self,
        action_request: ActionRequestRecord,
        *,
        record_index: _ActionReviewRecordIndex | None = None,
    ) -> ActionRequestRecord | None:
        if action_request.lifecycle_state != "superseded":
            return None
        requested_payload = dict(action_request.requested_payload)
        recommendation_id = requested_payload.get("recommendation_id")
        action_type = requested_payload.get("action_type")
        if record_index is not None:
            candidate_requests = record_index.matching_requests(
                case_id=action_request.case_id,
                alert_id=action_request.alert_id,
            )
            matches = [
                record
                for record in candidate_requests
                if record.action_request_id != action_request.action_request_id
                and self._action_request_is_review_bound(record)
                and record.requested_at >= action_request.requested_at
                and record.lifecycle_state != "superseded"
                and dict(record.requested_payload).get("action_type") == action_type
                and (
                    recommendation_id is None
                    or dict(record.requested_payload).get("recommendation_id")
                    == recommendation_id
                )
            ]
        else:
            matches = [
                record
                for record in self._store.list(ActionRequestRecord)
                if record.action_request_id != action_request.action_request_id
                and self._action_request_is_review_bound(record)
                and (
                    (
                        action_request.case_id is not None
                        and record.case_id == action_request.case_id
                    )
                    or (
                        action_request.alert_id is not None
                        and record.alert_id == action_request.alert_id
                    )
                )
                and record.requested_at >= action_request.requested_at
                and record.lifecycle_state != "superseded"
                and dict(record.requested_payload).get("action_type") == action_type
                and (
                    recommendation_id is None
                    or dict(record.requested_payload).get("recommendation_id")
                    == recommendation_id
                )
            ]
        if not matches:
            return None
        matches.sort(
            key=lambda record: (record.requested_at, record.action_request_id),
            reverse=True,
        )
        return matches[0]

    @staticmethod
    def _action_request_is_review_bound(action_request: ActionRequestRecord) -> bool:
        return not (
            action_request.policy_evaluation.get("approval_requirement")
            == "policy_authorized"
            and action_request.approval_decision_id is None
        )

    @staticmethod
    def _next_expected_action_for_review_state(review_state: str) -> str | None:
        return {
            "pending": "await_approver_decision",
            "approved": "await_reviewed_delegation",
            "executing": "await_execution_reconciliation",
            "expired": "create_replacement_or_close_case",
            "rejected": "review_rejection_and_record_follow_up",
            "canceled": "investigate_execution_cancellation",
            "superseded": "inspect_replacing_review_record",
            "completed": "review_execution_outcome",
            "failed": "investigate_execution_failure",
            "unresolved": "investigate_reconciliation_gap",
        }.get(review_state)

    @staticmethod
    def _action_review_stage_snapshot(
        *,
        stage: str,
        record_family: str,
        record_id: str | None,
        state: str,
        occurred_at: datetime | None,
        actor_identities: tuple[str, ...] = (),
        details: Mapping[str, object] | None = None,
    ) -> dict[str, object]:
        snapshot = {
            "stage": stage,
            "record_family": record_family,
            "record_id": record_id,
            "state": state,
            "occurred_at": occurred_at,
            "actor_identities": actor_identities,
        }
        if details:
            snapshot["details"] = dict(details)
        return snapshot

    def _action_review_timeline(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_state: str | None,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        reconciliation: ReconciliationRecord | None,
    ) -> tuple[dict[str, object], ...]:
        delegation_details: dict[str, object] = {}
        action_execution_details: dict[str, object] = {}
        execution_actor_identities: tuple[str, ...] = ()
        action_execution_occurred_at: datetime | None = None
        if action_execution is not None:
            delegation_details["delegation_id"] = action_execution.delegation_id
            execution_actor_identities = self._assistant_merge_ids(
                action_execution.provenance.get("initiated_by"),
                action_execution.provenance.get("delegation_issuer"),
            )
            downstream_binding = action_execution.provenance.get("downstream_binding")
            if isinstance(downstream_binding, Mapping):
                delegation_details["downstream_binding"] = dict(downstream_binding)
            adapter = action_execution.provenance.get("adapter")
            if isinstance(adapter, str) and adapter.strip():
                action_execution_details["adapter"] = adapter
            adapter_base_url = action_execution.provenance.get("adapter_base_url")
            if isinstance(adapter_base_url, str) and adapter_base_url.strip():
                action_execution_details["adapter_base_url"] = adapter_base_url
        timeline = (
            self._action_review_stage_snapshot(
                stage="action_request",
                record_family="action_request",
                record_id=action_request.action_request_id,
                state=action_request.lifecycle_state,
                occurred_at=action_request.requested_at,
                actor_identities=(
                    ()
                    if action_request.requester_identity is None
                    else (action_request.requester_identity,)
                ),
                details={
                    "recipient_identity": action_request.requested_payload.get(
                        "recipient_identity"
                    ),
                    "execution_surface_type": action_request.policy_evaluation.get(
                        "execution_surface_type"
                    ),
                    "execution_surface_id": action_request.policy_evaluation.get(
                        "execution_surface_id"
                    ),
                },
            ),
            self._action_review_stage_snapshot(
                stage="approval_decision",
                record_family="approval_decision",
                record_id=(
                    None
                    if approval_decision is None
                    else approval_decision.approval_decision_id
                ),
                state=(
                    approval_decision.lifecycle_state
                    if approval_decision is not None
                    else (approval_state or "pending")
                ),
                occurred_at=(
                    None if approval_decision is None else approval_decision.decided_at
                ),
                actor_identities=(
                    ()
                    if approval_decision is None
                    else approval_decision.approver_identities
                ),
                details=(
                    {}
                    if approval_decision is None
                    or approval_decision.decision_rationale is None
                    else {
                        "decision_rationale": approval_decision.decision_rationale,
                    }
                ),
            ),
            self._action_review_stage_snapshot(
                stage="delegation",
                record_family="action_execution",
                record_id=(
                    None
                    if action_execution is None
                    else action_execution.action_execution_id
                ),
                state=(
                    "awaiting_delegation"
                    if action_execution is None
                    else "delegated"
                ),
                occurred_at=(
                    None if action_execution is None else action_execution.delegated_at
                ),
                actor_identities=(
                    ()
                    if action_execution is None
                    else self._assistant_ids_from_mapping(
                        action_execution.provenance,
                        "delegation_issuer",
                    )
                ),
                details=delegation_details,
            ),
            self._action_review_stage_snapshot(
                stage="action_execution",
                record_family="action_execution",
                record_id=(
                    None
                    if action_execution is None
                    else action_execution.action_execution_id
                ),
                state=(
                    "awaiting_execution"
                    if action_execution is None
                    else action_execution.lifecycle_state
                ),
                occurred_at=action_execution_occurred_at,
                actor_identities=execution_actor_identities,
                details=(
                    {}
                    if action_execution is None
                    else {
                        "execution_run_id": action_execution.execution_run_id,
                        "execution_surface_type": action_execution.execution_surface_type,
                        "execution_surface_id": action_execution.execution_surface_id,
                        **action_execution_details,
                    }
                ),
            ),
            self._action_review_stage_snapshot(
                stage="reconciliation",
                record_family="reconciliation",
                record_id=(
                    None if reconciliation is None else reconciliation.reconciliation_id
                ),
                state=(
                    "awaiting_reconciliation"
                    if reconciliation is None
                    else reconciliation.lifecycle_state
                ),
                occurred_at=(
                    None if reconciliation is None else reconciliation.compared_at
                ),
                details=(
                    {}
                    if reconciliation is None
                    else {
                        "ingest_disposition": reconciliation.ingest_disposition,
                        "execution_run_id": reconciliation.execution_run_id,
                    }
                ),
            ),
        )
        return timeline

    @staticmethod
    def _action_review_mismatch_inspection(
        reconciliation: ReconciliationRecord | None,
    ) -> dict[str, object] | None:
        if reconciliation is None:
            return None
        if reconciliation.lifecycle_state not in {"pending", "mismatched", "stale"}:
            return None
        return {
            "reconciliation_id": reconciliation.reconciliation_id,
            "lifecycle_state": reconciliation.lifecycle_state,
            "ingest_disposition": reconciliation.ingest_disposition,
            "mismatch_summary": reconciliation.mismatch_summary,
            "correlation_key": reconciliation.correlation_key,
            "execution_run_id": reconciliation.execution_run_id,
            "linked_execution_run_ids": reconciliation.linked_execution_run_ids,
            "subject_linkage": dict(reconciliation.subject_linkage),
            "first_seen_at": reconciliation.first_seen_at,
            "last_seen_at": reconciliation.last_seen_at,
            "compared_at": reconciliation.compared_at,
        }

    def _action_review_coordination_ticket_outcome(
        self,
        *,
        action_request: ActionRequestRecord,
        approval_decision: ApprovalDecisionRecord | None,
        action_execution: ActionExecutionRecord | None,
        reconciliation: ReconciliationRecord | None,
        runtime_visibility: Mapping[str, object] | None,
        path_health: Mapping[str, object],
        review_state: str,
    ) -> dict[str, object] | None:
        requested_payload = action_request.requested_payload
        if requested_payload.get("action_type") != "create_tracking_ticket":
            return None
        if (
            action_execution is None
            and reconciliation is None
            and review_state in {"rejected", "expired", "superseded", "canceled"}
        ):
            return None

        downstream_binding = self._action_review_downstream_binding(action_execution)
        mismatch = self._action_review_coordination_ticket_mismatch(reconciliation)
        terminal_issue = self._action_review_coordination_ticket_terminal_issue(
            action_execution=action_execution,
            path_health=path_health,
        )
        manual_fallback = None
        if isinstance(runtime_visibility, Mapping):
            manual_fallback_entry = runtime_visibility.get("manual_fallback")
            if isinstance(manual_fallback_entry, Mapping):
                manual_fallback = dict(manual_fallback_entry)

        if (
            reconciliation is not None
            and reconciliation.lifecycle_state == "matched"
            and action_execution is not None
            and action_execution.lifecycle_state == "succeeded"
        ):
            status = "created"
            summary = (
                "reviewed create-ticket outcome recorded from authoritative "
                "execution and reconciliation"
            )
        elif manual_fallback is not None:
            status = "manual_fallback"
            summary = str(
                manual_fallback.get("action_taken")
                or manual_fallback.get("reason")
                or "reviewed create-ticket outcome recorded as manual fallback"
            )
        elif mismatch is not None:
            status = "mismatch"
            summary = str(mismatch["mismatch_summary"])
        elif terminal_issue is not None and terminal_issue["category"] == "timeout":
            status = "timeout"
            summary = str(terminal_issue["reason"]).replace("_", " ")
        elif terminal_issue is not None:
            status = "timeout"
            summary = str(terminal_issue["reason"]).replace("_", " ")
        else:
            status = "pending"
            summary = "reviewed create-ticket outcome still awaiting authoritative result"

        outcome = {
            "authority": "authoritative_aegisops_review",
            "status": status,
            "summary": summary,
            "action_request_id": action_request.action_request_id,
            "approval_decision_id": (
                None if approval_decision is None else approval_decision.approval_decision_id
            ),
            "action_execution_id": (
                None if action_execution is None else action_execution.action_execution_id
            ),
            "execution_run_id": (
                None if action_execution is None else action_execution.execution_run_id
            ),
            "reconciliation_id": (
                None if reconciliation is None else reconciliation.reconciliation_id
            ),
            "coordination_reference_id": (
                action_request.target_scope.get("coordination_reference_id")
                if isinstance(action_request.target_scope.get("coordination_reference_id"), str)
                else requested_payload.get("coordination_reference_id")
            ),
            "coordination_target_type": (
                action_request.target_scope.get("coordination_target_type")
                if isinstance(action_request.target_scope.get("coordination_target_type"), str)
                else requested_payload.get("coordination_target_type")
            ),
            "coordination_target_id": (
                None
                if downstream_binding is None
                else downstream_binding.get("coordination_target_id")
            ),
            "external_receipt_id": (
                None
                if downstream_binding is None
                else downstream_binding.get("external_receipt_id")
            ),
            "ticket_reference_url": (
                None
                if downstream_binding is None
                else downstream_binding.get("ticket_reference_url")
            ),
        }
        if terminal_issue is not None and terminal_issue["category"] == "timeout":
            timeout = {
                key: value
                for key, value in terminal_issue.items()
                if key != "category"
            }
            outcome["timeout"] = timeout
        elif terminal_issue is not None:
            timeout = {
                key: value
                for key, value in terminal_issue.items()
                if key != "category"
            }
            outcome["timeout"] = timeout
        if mismatch is not None:
            outcome["mismatch"] = mismatch
        if manual_fallback is not None:
            outcome["manual_fallback"] = manual_fallback
        return outcome

    @staticmethod
    def _action_review_downstream_binding(
        action_execution: ActionExecutionRecord | None,
    ) -> Mapping[str, object] | None:
        if action_execution is None or not isinstance(action_execution.provenance, Mapping):
            return None
        downstream_binding = action_execution.provenance.get("downstream_binding")
        if not isinstance(downstream_binding, Mapping):
            return None
        return downstream_binding

    @staticmethod
    def _action_review_coordination_ticket_mismatch(
        reconciliation: ReconciliationRecord | None,
    ) -> dict[str, object] | None:
        mismatch = AegisOpsControlPlaneService._action_review_mismatch_inspection(
            reconciliation
        )
        if mismatch is None:
            return None
        if (
            mismatch["lifecycle_state"] != "mismatched"
            and mismatch["ingest_disposition"] != "mismatch"
        ):
            return None
        return mismatch

    @staticmethod
    def _action_review_coordination_ticket_terminal_issue(
        *,
        action_execution: ActionExecutionRecord | None,
        path_health: Mapping[str, object],
    ) -> dict[str, object] | None:
        if (
            action_execution is not None
            and isinstance(action_execution.provenance, Mapping)
            and isinstance(action_execution.provenance.get("dispatch_failure"), Mapping)
        ):
            dispatch_failure = action_execution.provenance["dispatch_failure"]
            if dispatch_failure.get("error_type") == "TimeoutError":
                timeout = {
                    "category": "timeout",
                    "path": "provider",
                    "reason": "dispatch_timeout",
                }
                error = dispatch_failure.get("error")
                if isinstance(error, str) and error:
                    timeout["error"] = error
                return timeout

        paths = path_health.get("paths")
        if not isinstance(paths, Mapping):
            return None
        timeout_reasons = {
            "ingest_signal_timeout",
            "delegation_receipt_timeout",
            "provider_receipt_timeout",
            "authoritative_outcome_timeout",
            "reconciliation_timeout",
        }
        terminal_failure_reasons = {
            "execution_failed",
            "execution_canceled",
            "execution_expired",
            "execution_rejected",
        }
        provider_path = paths.get("provider")
        if isinstance(provider_path, Mapping):
            provider_reason = provider_path.get("reason")
            if (
                isinstance(provider_reason, str)
                and provider_reason in terminal_failure_reasons
            ):
                return {
                    "category": "failed",
                    "path": "provider",
                    "reason": provider_reason,
                }
        for path_name in ("ingest", "delegation", "provider", "persistence"):
            path = paths.get(path_name)
            if not isinstance(path, Mapping):
                continue
            reason = path.get("reason")
            if not isinstance(reason, str):
                continue
            if reason in timeout_reasons:
                return {
                    "category": "timeout",
                    "path": path_name,
                    "reason": reason,
                }
        return None

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
        action_review_index = self._build_action_review_record_index()
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
            action_reviews = self._action_review_chains_for_scope(
                case_id=alert.case_id,
                alert_id=alert.alert_id,
                record_index=action_review_index,
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
                    "current_action_review": (
                        dict(action_reviews[0]) if action_reviews else None
                    ),
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

    def _build_alert_external_ticket_reference_surface(
        self,
        *,
        alert: AlertRecord,
        case_record: CaseRecord | None,
    ) -> dict[str, object]:
        alert_reference = _coordination_reference_payload(alert)
        case_reference = _coordination_reference_payload(case_record)
        if alert_reference is None and case_reference is None:
            status = "missing"
        elif alert_reference is None:
            status = "linked_case_reference_only"
        elif case_record is None:
            status = "present"
        elif case_reference is None:
            status = "linked_case_reference_missing"
        elif _coordination_reference_signature(
            alert
        ) != _coordination_reference_signature(case_record):
            status = "linked_case_reference_mismatch"
        else:
            status = "present"
        return {
            "authority": "non_authoritative",
            "status": status,
            "coordination_reference_id": (
                alert_reference["coordination_reference_id"]
                if alert_reference is not None
                else None
            ),
            "coordination_target_type": (
                alert_reference["coordination_target_type"]
                if alert_reference is not None
                else None
            ),
            "coordination_target_id": (
                alert_reference["coordination_target_id"]
                if alert_reference is not None
                else None
            ),
            "ticket_reference_url": (
                alert_reference["ticket_reference_url"]
                if alert_reference is not None
                else None
            ),
            "linked_case_id": case_record.case_id if case_record is not None else None,
            "linked_case_reference": case_reference,
        }

    def _build_case_external_ticket_reference_surface(
        self,
        *,
        case: CaseRecord,
        linked_alert_records: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        case_reference = _coordination_reference_payload(case)
        linked_alert_references = tuple(
            {
                "alert_id": str(record.get("alert_id")),
                **reference,
            }
            for record in linked_alert_records
            for reference in (_coordination_reference_payload(record),)
            if reference is not None
        )
        linked_alert_signatures = {
            (
                reference["coordination_reference_id"],
                reference["coordination_target_type"],
                reference["coordination_target_id"],
                reference["ticket_reference_url"],
            )
            for reference in linked_alert_references
        }
        linked_alert_ids = {
            str(record.get("alert_id"))
            for record in linked_alert_records
            if isinstance(record.get("alert_id"), str)
        }
        linked_alert_ids_with_reference = {
            reference["alert_id"] for reference in linked_alert_references
        }
        missing_linked_alert_ids = linked_alert_ids - linked_alert_ids_with_reference
        if case_reference is None and not linked_alert_references:
            status = "missing"
        elif case_reference is None and missing_linked_alert_ids:
            status = "linked_alert_reference_missing"
        elif case_reference is None and len(linked_alert_signatures) > 1:
            status = "linked_alert_reference_mismatch"
        elif case_reference is None:
            status = "linked_alert_reference_only"
        else:
            if missing_linked_alert_ids:
                status = "linked_alert_reference_missing"
            elif linked_alert_signatures and linked_alert_signatures != {
                _coordination_reference_signature(case)
            }:
                status = "linked_alert_reference_mismatch"
            else:
                status = "present"

        return {
            "authority": "non_authoritative",
            "status": status,
            "coordination_reference_id": (
                case_reference["coordination_reference_id"]
                if case_reference is not None
                else None
            ),
            "coordination_target_type": (
                case_reference["coordination_target_type"]
                if case_reference is not None
                else None
            ),
            "coordination_target_id": (
                case_reference["coordination_target_id"]
                if case_reference is not None
                else None
            ),
            "ticket_reference_url": (
                case_reference["ticket_reference_url"]
                if case_reference is not None
                else None
            ),
            "linked_alert_references": linked_alert_references,
        }

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
        action_reviews = self._action_review_chains_for_scope(
            case_id=alert.case_id,
            alert_id=alert.alert_id,
            record_index=self._build_action_review_record_index(),
        )

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
            lifecycle_transitions=tuple(
                _record_to_dict(transition)
                for transition in self.list_lifecycle_transitions("alert", alert.alert_id)
            ),
            current_action_review=dict(action_reviews[0]) if action_reviews else None,
            action_reviews=action_reviews,
            external_ticket_reference=self._build_alert_external_ticket_reference_surface(
                alert=alert,
                case_record=case_record,
            ),
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
        case = self._require_reviewed_operator_case(case_id)
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
        action_reviews = self._action_review_chains_for_scope(
            case_id=case_id,
            alert_id=case.alert_id,
            record_index=self._build_action_review_record_index(),
        )
        cross_source_timeline, provenance_summary = (
            self._build_case_cross_source_surfaces(
                case=case,
                linked_alert_records=context_snapshot.linked_alert_records,
                linked_evidence_records=context_snapshot.linked_evidence_records,
                linked_observation_records=observation_records,
            )
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
            lifecycle_transitions=context_snapshot.lifecycle_transitions,
            cross_source_timeline=cross_source_timeline,
            provenance_summary=provenance_summary,
            current_action_review=dict(action_reviews[0]) if action_reviews else None,
            action_reviews=action_reviews,
            external_ticket_reference=self._build_case_external_ticket_reference_surface(
                case=case,
                linked_alert_records=context_snapshot.linked_alert_records,
            ),
        )

    def _build_case_cross_source_surfaces(
        self,
        *,
        case: CaseRecord,
        linked_alert_records: tuple[dict[str, object], ...],
        linked_evidence_records: tuple[dict[str, object], ...],
        linked_observation_records: tuple[dict[str, object], ...],
    ) -> tuple[tuple[dict[str, object], ...], dict[str, object]]:
        anchor = self._build_case_cross_source_anchor(
            case=case,
            linked_alert_records=linked_alert_records,
        )
        attached_entries = [
            entry
            for entry in (
                *(
                    self._build_case_cross_source_attached_entry(
                        record_family="evidence",
                        record=record,
                        case_id=case.case_id,
                    )
                    for record in linked_evidence_records
                ),
                *(
                    self._build_case_cross_source_attached_entry(
                        record_family="observation",
                        record=record,
                        case_id=case.case_id,
                    )
                    for record in linked_observation_records
                ),
            )
            if entry is not None
        ]
        attached_entries.sort(
            key=lambda entry: (
                entry.get("_sort_occurred_at")
                or datetime.max.replace(tzinfo=timezone.utc),
                str(entry["record_family"]),
                str(entry["record_id"]),
            )
        )
        timeline = tuple(
            self._case_cross_source_public_entry(entry)
            for entry in (anchor, *attached_entries)
        )
        source_families = _dedupe_strings(
            str(source_family)
            for source_family in (
                entry.get("source_family") for entry in (anchor, *attached_entries)
            )
            if isinstance(source_family, str) and source_family.strip()
        )
        provenance_summary = {
            "authoritative_anchor": {
                "record_family": anchor["record_family"],
                "record_id": anchor["record_id"],
                "source_family": anchor["source_family"],
                "provenance_classification": anchor["provenance_classification"],
                "reviewed_linkage": anchor["reviewed_linkage"],
            },
            "source_families": source_families,
            "attached_records": tuple(
                {
                    "record_family": entry["record_family"],
                    "record_id": entry["record_id"],
                    "source_family": entry["source_family"],
                    "evidence_origin": entry["evidence_origin"],
                    "provenance_classification": entry["provenance_classification"],
                    "ambiguity_badge": entry["ambiguity_badge"],
                    "reviewed_linkage": entry["reviewed_linkage"],
                    "blocking_reason": entry["blocking_reason"],
                }
                for entry in attached_entries
            ),
        }
        return timeline, provenance_summary

    def _build_case_cross_source_anchor(
        self,
        *,
        case: CaseRecord,
        linked_alert_records: tuple[dict[str, object], ...],
    ) -> dict[str, object]:
        anchor_record = next(
            (
                dict(record)
                for record in linked_alert_records
                if record.get("alert_id") == case.alert_id
            ),
            {
                "alert_id": case.alert_id,
                "case_id": case.case_id,
                "reviewed_context": dict(case.reviewed_context),
            },
        )
        source_family = self._reviewed_operator_source_family(
            anchor_record.get("reviewed_context")
        ) or self._reviewed_operator_source_family(case.reviewed_context)
        return {
            "record_family": "alert",
            "record_id": case.alert_id,
            "source_family": source_family or "unknown",
            "evidence_origin": case.alert_id,
            "provenance_classification": "authoritative-anchor",
            "ambiguity_badge": None,
            "reviewed_linkage": {
                "case_id": case.case_id,
                "alert_id": case.alert_id,
            },
            "blocking_reason": None,
            "occurred_at": None,
            "_sort_occurred_at": None,
        }

    def _build_case_cross_source_attached_entry(
        self,
        *,
        record_family: str,
        record: Mapping[str, object],
        case_id: str,
    ) -> dict[str, object] | None:
        raw_provenance = record.get("provenance")
        provenance_missing = not isinstance(raw_provenance, Mapping) or not raw_provenance
        provenance = raw_provenance if isinstance(raw_provenance, Mapping) else {}

        def _safe_optional_string(value: object, field_name: str) -> str | None:
            if isinstance(value, str):
                value = value.strip()
            try:
                return self._normalize_optional_string(value, field_name)
            except ValueError:
                return None

        record_id_field = f"{record_family}_id"
        record_id = self._normalize_optional_string(record.get(record_id_field), record_id_field)
        if record_id is None:
            return None

        explicit_source_family = _safe_optional_string(
            provenance.get("source_family"),
            f"{record_family}.provenance.source_family",
        )
        source_system = _safe_optional_string(
            provenance.get("source_system"),
            f"{record_family}.provenance.source_system",
        ) or _safe_optional_string(
            record.get("source_system"),
            f"{record_family}.source_system",
        )
        source_family = explicit_source_family or source_system or "unknown"

        classification = _safe_optional_string(
            provenance.get("classification"),
            f"{record_family}.provenance.classification",
        )
        source_id = _safe_optional_string(
            provenance.get("source_id"),
            f"{record_family}.provenance.source_id",
        )
        timestamp = _safe_optional_string(
            provenance.get("timestamp"),
            f"{record_family}.provenance.timestamp",
        )
        reviewed_by = _safe_optional_string(
            provenance.get("reviewed_by"),
            f"{record_family}.provenance.reviewed_by",
        )
        blocking_reason = _safe_optional_string(
            provenance.get("blocking_reason"),
            f"{record_family}.provenance.blocking_reason",
        )
        if None in (classification, source_id, timestamp, reviewed_by):
            classification = "unresolved-linkage"
            if blocking_reason is None:
                blocking_reason = (
                    "missing_provenance"
                    if provenance_missing
                    else "missing_or_invalid_required_provenance_fields"
                )

        ambiguity_badge = _safe_optional_string(
            provenance.get("ambiguity_badge"),
            f"{record_family}.provenance.ambiguity_badge",
        )
        if ambiguity_badge not in {"same-entity", "related-entity", "unresolved"}:
            ambiguity_badge = "unresolved"

        occurred_at = None
        if isinstance(record.get("acquired_at"), _DATETIME_TYPE):
            occurred_at = record.get("acquired_at")
        elif isinstance(record.get("observed_at"), _DATETIME_TYPE):
            occurred_at = record.get("observed_at")

        reviewed_linkage: dict[str, object] = {"case_id": case_id}
        if record_family == "observation":
            supporting_evidence_ids = tuple(record.get("supporting_evidence_ids", ()))
            reviewed_linkage["supporting_evidence_ids"] = supporting_evidence_ids

        evidence_origin = self._normalize_optional_string(
            record.get("source_record_id"),
            f"{record_family}.source_record_id",
        ) or source_id

        return {
            "record_family": record_family,
            "record_id": record_id,
            "source_family": source_family,
            "evidence_origin": evidence_origin,
            "provenance_classification": classification,
            "ambiguity_badge": ambiguity_badge,
            "reviewed_linkage": reviewed_linkage,
            "blocking_reason": blocking_reason,
            "occurred_at": occurred_at,
            "_sort_occurred_at": occurred_at,
        }

    @staticmethod
    def _case_cross_source_public_entry(entry: Mapping[str, object]) -> dict[str, object]:
        return {
            "record_family": entry["record_family"],
            "record_id": entry["record_id"],
            "occurred_at": entry["occurred_at"],
            "source_family": entry["source_family"],
            "evidence_origin": entry["evidence_origin"],
            "provenance_classification": entry["provenance_classification"],
            "ambiguity_badge": entry["ambiguity_badge"],
            "reviewed_linkage": entry["reviewed_linkage"],
            "blocking_reason": entry["blocking_reason"],
        }

    def attach_osquery_host_context(
        self,
        *,
        case_id: str,
        host_identifier: str,
        query_name: str,
        query_sql: str,
        result_kind: str,
        rows: tuple[Mapping[str, object], ...],
        collected_at: datetime,
        reviewed_by: str,
        source_id: str,
        collection_path: str,
        query_context: Mapping[str, object] | None = None,
        evidence_id: str | None = None,
        observation_scope_statement: str | None = None,
        observation_id: str | None = None,
    ) -> tuple[EvidenceRecord, ObservationRecord | None]:
        case_id = self._require_non_empty_string(case_id, "case_id")
        normalized_scope_statement = self._normalize_optional_string(
            observation_scope_statement,
            "observation_scope_statement",
        )
        if normalized_scope_statement is None and observation_id is not None:
            raise ValueError(
                "observation_id requires observation_scope_statement for osquery attachment"
            )
        with self._store.transaction(isolation_level="SERIALIZABLE"):
            case = self._require_reviewed_operator_case(case_id)
            authoritative_host_identifier = self._require_case_host_identifier(case)
            attachment = self._osquery_host_context_adapter.build_attachment(
                case_id=case.case_id,
                alert_id=case.alert_id,
                authoritative_host_identifier=authoritative_host_identifier,
                host_identifier=host_identifier,
                query_name=query_name,
                query_sql=query_sql,
                result_kind=result_kind,
                rows=rows,
                collected_at=collected_at,
                reviewed_by=reviewed_by,
                source_id=source_id,
                collection_path=collection_path,
                query_context=query_context,
            )
            resolved_evidence_id = self._resolve_new_record_identifier(
                EvidenceRecord,
                evidence_id,
                "evidence_id",
                "evidence",
            )
            evidence = self.persist_record(
                EvidenceRecord(
                    evidence_id=resolved_evidence_id,
                    source_record_id=attachment.source_record_id,
                    alert_id=case.alert_id,
                    case_id=case.case_id,
                    source_system=attachment.source_system,
                    collector_identity=attachment.collector_identity,
                    acquired_at=attachment.acquired_at,
                    derivation_relationship=attachment.derivation_relationship,
                    lifecycle_state="linked",
                    provenance=attachment.provenance,
                    content=attachment.content,
                )
            )
            current_case = self._require_reviewed_operator_case(case.case_id)
            merged_case_evidence_ids = self._merge_linked_ids(
                current_case.evidence_ids,
                evidence.evidence_id,
            )
            if merged_case_evidence_ids != current_case.evidence_ids:
                self.persist_record(
                    replace(
                        current_case,
                        evidence_ids=merged_case_evidence_ids,
                    )
                )

            observation: ObservationRecord | None = None
            if normalized_scope_statement is not None:
                resolved_observation_id = self._resolve_new_record_identifier(
                    ObservationRecord,
                    observation_id,
                    "observation_id",
                    "observation",
                )
                observation = self.persist_record(
                    ObservationRecord(
                        observation_id=resolved_observation_id,
                        hunt_id=None,
                        hunt_run_id=None,
                        alert_id=current_case.alert_id,
                        case_id=current_case.case_id,
                        supporting_evidence_ids=(evidence.evidence_id,),
                        author_identity=self._require_non_empty_string(
                            reviewed_by,
                            "reviewed_by",
                        ),
                        observed_at=self._require_aware_datetime(
                            collected_at,
                            "collected_at",
                        ),
                        scope_statement=normalized_scope_statement,
                        lifecycle_state="confirmed",
                        provenance=attachment.observation_provenance,
                        content={
                            **attachment.observation_content,
                            "host_context_evidence_id": evidence.evidence_id,
                        },
                    )
                )
            return evidence, observation

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
            case = self._require_reviewed_operator_case(case_id)
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
            case = self._require_reviewed_operator_case(case_id)
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
            case = self._require_reviewed_operator_case(case_id)
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
            case = self._require_reviewed_operator_case(case_id)
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
                replace(
                    case,
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
            case = self._require_reviewed_operator_case(case_id)
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
                replace(
                    case,
                    lifecycle_state=lifecycle_state,
                    reviewed_context=updated_reviewed_context,
                ),
                transitioned_at=recorded_at,
            )
            if case.alert_id is not None and lifecycle_state == "closed":
                alert = self._store.get(AlertRecord, case.alert_id)
                if alert is not None:
                    self.persist_record(
                        replace(
                            alert,
                            lifecycle_state="closed",
                            reviewed_context=_merge_reviewed_context(
                                alert.reviewed_context,
                                {"triage": updated_reviewed_context.get("triage", {})},
                            ),
                        ),
                        transitioned_at=recorded_at,
                    )
        return updated_case

    def record_action_review_manual_fallback(
        self,
        *,
        action_request_id: str,
        fallback_at: datetime,
        fallback_actor_identity: str,
        authority_boundary: str,
        reason: str,
        action_taken: str,
        verification_evidence_ids: tuple[str, ...] = (),
        residual_uncertainty: str | None = None,
    ) -> CaseRecord | AlertRecord:
        fallback_at = self._require_aware_datetime(fallback_at, "fallback_at")
        fallback_actor_identity = self._require_non_empty_string(
            fallback_actor_identity,
            "fallback_actor_identity",
        )
        authority_boundary = self._require_non_empty_string(
            authority_boundary,
            "authority_boundary",
        )
        reason = self._require_non_empty_string(reason, "reason")
        action_taken = self._require_non_empty_string(action_taken, "action_taken")
        normalized_evidence_ids = self._normalize_linked_record_ids(
            verification_evidence_ids,
            "verification_evidence_ids",
        )
        normalized_residual_uncertainty = self._normalize_optional_string(
            residual_uncertainty,
            "residual_uncertainty",
        )
        with self._store.transaction():
            action_request = self._require_review_bound_action_request(action_request_id)
            approval_decision = self._action_review_approval_decision(action_request)
            approval_state = self._action_review_approval_state(
                action_request=action_request,
                approval_decision=approval_decision,
            )
            review_state = self._action_review_state(
                action_request=action_request,
                approval_state=approval_state,
                action_execution=self._action_review_execution(action_request),
            )
            if (
                approval_decision is None
                or approval_decision.lifecycle_state != "approved"
                or review_state in {"pending", "rejected", "expired", "superseded"}
            ):
                raise ValueError(
                    "manual fallback requires an approved action review in a live post-approval state"
                )
            context_record = self._require_action_review_visibility_context_record(
                action_request
            )
            if isinstance(context_record, CaseRecord):
                self._validate_case_evidence_linkage(
                    case=context_record,
                    evidence_ids=normalized_evidence_ids,
                    field_name="verification_evidence_ids",
                )
            else:
                self._validate_alert_evidence_linkage(
                    alert=context_record,
                    evidence_ids=normalized_evidence_ids,
                    field_name="verification_evidence_ids",
                )
            manual_fallback_context: dict[str, object] = {
                "action_request_id": action_request.action_request_id,
                "approval_decision_id": approval_decision.approval_decision_id,
                "fallback_at": fallback_at.isoformat(),
                "fallback_actor_identity": fallback_actor_identity,
                "authority_boundary": authority_boundary,
                "reason": reason,
                "action_taken": action_taken,
                "verification_evidence_ids": normalized_evidence_ids,
            }
            if normalized_residual_uncertainty is not None:
                manual_fallback_context["residual_uncertainty"] = (
                    normalized_residual_uncertainty
                )
            return self._persist_action_review_visibility_context_record(
                context_record=context_record,
                reviewed_context_update=self._action_review_visibility_update(
                    action_request_id=action_request.action_request_id,
                    context_key="manual_fallback",
                    context_value=manual_fallback_context,
                ),
            )

    def record_action_review_escalation_note(
        self,
        *,
        action_request_id: str,
        escalated_at: datetime,
        escalated_by_identity: str,
        escalated_to: str,
        note: str,
    ) -> CaseRecord | AlertRecord:
        escalated_at = self._require_aware_datetime(escalated_at, "escalated_at")
        escalated_by_identity = self._require_non_empty_string(
            escalated_by_identity,
            "escalated_by_identity",
        )
        escalated_to = self._require_non_empty_string(escalated_to, "escalated_to")
        note = self._require_non_empty_string(note, "note")
        with self._store.transaction():
            action_request = self._require_review_bound_action_request(action_request_id)
            approval_decision = self._action_review_approval_decision(action_request)
            approval_state = self._action_review_approval_state(
                action_request=action_request,
                approval_decision=approval_decision,
            )
            review_state = self._action_review_state(
                action_request=action_request,
                approval_state=approval_state,
                action_execution=self._action_review_execution(action_request),
            )
            context_record = self._require_action_review_visibility_context_record(
                action_request
            )
            escalation_context: dict[str, object] = {
                "action_request_id": action_request.action_request_id,
                "escalated_at": escalated_at.isoformat(),
                "escalated_by_identity": escalated_by_identity,
                "escalated_to": escalated_to,
                "note": note,
                "review_state": review_state,
            }
            if approval_decision is not None:
                escalation_context["approval_decision_id"] = (
                    approval_decision.approval_decision_id
                )
            return self._persist_action_review_visibility_context_record(
                context_record=context_record,
                reviewed_context_update=self._action_review_visibility_update(
                    action_request_id=action_request.action_request_id,
                    context_key="escalation",
                    context_value=escalation_context,
                ),
            )

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

    def run_live_assistant_workflow(
        self,
        *,
        workflow_task: str,
        record_family: str,
        record_id: str,
    ) -> LiveAssistantWorkflowSnapshot:
        workflow_task = self._require_non_empty_string(workflow_task, "workflow_task")
        record_family = self._require_non_empty_string(record_family, "record_family")
        record_id = self._require_non_empty_string(record_id, "record_id")

        expected_record_family = {
            "case_summary": "case",
            "queue_triage_summary": "alert",
        }.get(workflow_task)
        if expected_record_family is None:
            raise ValueError(
                "workflow_task must be one of: case_summary, queue_triage_summary"
            )
        if record_family != expected_record_family:
            raise ValueError(
                f"workflow_task {workflow_task!r} requires record_family {expected_record_family!r}"
            )

        context_snapshot = self.inspect_assistant_context(record_family, record_id)
        if workflow_task == "queue_triage_summary":
            self._require_reviewed_alert_scoped_queue_summary_read(context_snapshot)
        else:
            self._require_reviewed_case_scoped_advisory_read(context_snapshot)

        advisory_output = dict(context_snapshot.advisory_output)
        reviewed_input_refs = _dedupe_strings(
            (
                record_id,
                *context_snapshot.linked_alert_ids,
                *context_snapshot.linked_case_ids,
                *context_snapshot.linked_evidence_ids,
                *context_snapshot.linked_recommendation_ids,
                *context_snapshot.linked_reconciliation_ids,
            )
        )
        citations = _phase24_live_assistant_citations_from_context(context_snapshot)
        trusted_summary = str(
            advisory_output.get("cited_summary", {}).get("text")
            or f"Reviewed {workflow_task.replace('_', ' ')} for {record_id} remains unresolved."
        )
        adapter = self._live_assistant_adapter_for_workflow_task(workflow_task)
        if advisory_output.get("status") != "ready":
            unresolved_reasons = _phase24_live_assistant_unresolved_reasons(
                advisory_output.get("uncertainty_flags", ())
            )
            if not unresolved_reasons:
                unresolved_reasons = ("required citations are missing",)
            snapshot = _phase24_live_assistant_snapshot(
                workflow_task=workflow_task,
                summary=trusted_summary,
                citations=citations,
                unresolved_reasons=unresolved_reasons,
            )
            self._persist_live_assistant_feedback_loop(
                record_family=record_family,
                record_id=record_id,
                context_snapshot=context_snapshot,
                workflow_snapshot=snapshot,
                provider_result=None,
                reviewed_input_refs=reviewed_input_refs,
                adapter=adapter,
            )
            return snapshot

        if adapter is None:
            raise ValueError("live assistant provider is not configured")

        transcript_payload = _json_ready(
            {
                "record_family": record_family,
                "record_id": record_id,
                "reviewed_context": context_snapshot.reviewed_context,
                "linked_alert_ids": context_snapshot.linked_alert_ids,
                "linked_case_ids": context_snapshot.linked_case_ids,
                "linked_evidence_ids": context_snapshot.linked_evidence_ids,
                "linked_recommendation_ids": context_snapshot.linked_recommendation_ids,
                "linked_reconciliation_ids": context_snapshot.linked_reconciliation_ids,
                "advisory_output": advisory_output,
            }
        )
        provider_result = None
        unresolved_reasons: list[str] = []
        try:
            provider_result = adapter.generate(
                workflow_family=_PHASE24_WORKFLOW_FAMILY,
                workflow_task=workflow_task,
                transcript=[
                    {
                        "role": "system",
                        "content": (
                            "Return a concise reviewed-only summary. Do not add approval, delegation, execution, or policy language."
                        ),
                    },
                    {
                        "role": "user",
                        "content": json.dumps(transcript_payload, sort_keys=True),
                    },
                ],
                reviewed_input_refs=reviewed_input_refs,
                metadata={
                    "record_family": record_family,
                    "record_id": record_id,
                    "bounded_summary_text": trusted_summary,
                },
            )
        except Exception:  # noqa: BLE001
            unresolved_reasons.extend(
                _phase24_live_assistant_unresolved_reasons(
                    ("provider_generation_failed",)
                )
            )
        candidate_summary = trusted_summary
        provider_output_text: str | None = None
        if provider_result is not None:
            if provider_result.status != "ready":
                unresolved_reasons.extend(
                    _phase24_live_assistant_unresolved_reasons(
                        ("provider_generation_failed",)
                    )
                )
            elif (
                isinstance(provider_result.output_text, str)
                and provider_result.output_text.strip()
            ):
                provider_output_text = provider_result.output_text.strip()
                candidate_summary = provider_output_text
            else:
                unresolved_reasons.extend(
                    _phase24_live_assistant_unresolved_reasons(
                        ("provider_generation_failed",)
                    )
                )
        if provider_output_text is not None:
            unresolved_reasons.extend(
                _phase24_live_assistant_unresolved_reasons(
                    _phase24_live_assistant_prompt_injection_flags(provider_output_text)
                )
            )
        unresolved_reasons.extend(
            _phase24_live_assistant_unresolved_reasons(
                _advisory_text_claims_authority_or_scope_expansion(candidate_summary)
            )
        )
        if not citations:
            unresolved_reasons.extend(
                _phase24_live_assistant_unresolved_reasons(
                    ("missing_supporting_citations",)
                )
            )
        unresolved_reasons = _dedupe_strings(tuple(unresolved_reasons))
        summary = trusted_summary if unresolved_reasons else candidate_summary
        snapshot = _phase24_live_assistant_snapshot(
            workflow_task=workflow_task,
            summary=summary,
            citations=citations,
            unresolved_reasons=unresolved_reasons,
        )
        self._persist_live_assistant_feedback_loop(
            record_family=record_family,
            record_id=record_id,
            context_snapshot=context_snapshot,
            workflow_snapshot=snapshot,
            provider_result=provider_result,
            reviewed_input_refs=reviewed_input_refs,
            adapter=adapter,
        )
        return snapshot

    def _live_assistant_adapter_for_workflow_task(
        self,
        workflow_task: str,
    ) -> object | None:
        adapter = self._assistant_provider_adapter
        if adapter is None:
            return None
        adapter_prompt_version = _PHASE24_WORKFLOW_PROMPT_VERSIONS[workflow_task]
        if (
            isinstance(adapter, AssistantProviderAdapter)
            and getattr(adapter, "_prompt_version", None) != adapter_prompt_version
        ):
            return AssistantProviderAdapter(
                provider_identity=getattr(adapter, "_provider_identity", "reviewed_local"),
                model_identity=getattr(
                    adapter, "_model_identity", "bounded_reviewed_summary"
                ),
                prompt_version=adapter_prompt_version,
                request_timeout_seconds=float(
                    getattr(adapter, "_request_timeout_seconds", 5.0)
                ),
                max_attempts=int(getattr(adapter, "_max_attempts", 1)),
                transport=getattr(adapter, "_transport"),
            )
        return adapter

    def _persist_live_assistant_feedback_loop(
        self,
        *,
        record_family: str,
        record_id: str,
        context_snapshot: AnalystAssistantContextSnapshot,
        workflow_snapshot: LiveAssistantWorkflowSnapshot,
        provider_result: AssistantProviderResult | AssistantProviderFailure | None,
        reviewed_input_refs: tuple[str, ...],
        adapter: object,
    ) -> None:
        with self._store.transaction():
            ai_trace_record = self._build_live_assistant_ai_trace_record(
                record_family=record_family,
                record_id=record_id,
                context_snapshot=context_snapshot,
                workflow_snapshot=workflow_snapshot,
                provider_result=provider_result,
                reviewed_input_refs=reviewed_input_refs,
                adapter=adapter,
            )
            persisted_ai_trace = self.persist_record(ai_trace_record)
            recommendation_record = self._build_live_assistant_recommendation_record(
                context_snapshot=context_snapshot,
                workflow_snapshot=workflow_snapshot,
                ai_trace_record=persisted_ai_trace,
            )
            persisted_recommendation = self.persist_record(recommendation_record)

            updated_subject_linkage = dict(persisted_ai_trace.subject_linkage)
            updated_subject_linkage["recommendation_ids"] = self._assistant_merge_ids(
                self._assistant_ids_from_mapping(
                    persisted_ai_trace.subject_linkage,
                    "recommendation_ids",
                ),
                persisted_recommendation.recommendation_id,
            )
            updated_advisory_draft = dict(persisted_ai_trace.assistant_advisory_draft)
            updated_advisory_draft["subject_linkage"] = updated_subject_linkage
            self.persist_record(
                replace(
                    persisted_ai_trace,
                    subject_linkage=updated_subject_linkage,
                    assistant_advisory_draft=updated_advisory_draft,
                )
            )

    def _build_live_assistant_ai_trace_record(
        self,
        *,
        record_family: str,
        record_id: str,
        context_snapshot: AnalystAssistantContextSnapshot,
        workflow_snapshot: LiveAssistantWorkflowSnapshot,
        provider_result: AssistantProviderResult | AssistantProviderFailure | None,
        reviewed_input_refs: tuple[str, ...],
        adapter: object,
    ) -> AITraceRecord:
        subject_linkage = {
            "source_record_family": record_family,
            "source_record_id": record_id,
            "alert_ids": context_snapshot.linked_alert_ids,
            "case_ids": context_snapshot.linked_case_ids,
            "evidence_ids": context_snapshot.linked_evidence_ids,
            "recommendation_ids": context_snapshot.linked_recommendation_ids,
            "reconciliation_ids": context_snapshot.linked_reconciliation_ids,
            "output_contract": {
                "workflow_family": workflow_snapshot.workflow_family,
                "workflow_task": workflow_snapshot.workflow_task,
                "status": workflow_snapshot.status,
            },
        }
        build_ai_trace_record = getattr(adapter, "build_ai_trace_record", None)
        ai_trace_record: AITraceRecord | None = None
        if provider_result is not None and callable(build_ai_trace_record):
            candidate_record = build_ai_trace_record(
                ai_trace_id=self._resolve_new_record_identifier(
                    AITraceRecord,
                    None,
                    "ai_trace_id",
                    "ai-trace",
                ),
                reviewer_identity="system://bounded-live-assistant",
                generated_at=provider_result.generated_at,
                result=provider_result,
                subject_linkage=subject_linkage,
            )
            if isinstance(candidate_record, AITraceRecord):
                ai_trace_record = candidate_record

        if ai_trace_record is None:
            generated_at = (
                provider_result.generated_at
                if provider_result is not None
                else datetime.now(timezone.utc)
            )
            ai_trace_record = AITraceRecord(
                ai_trace_id=self._resolve_new_record_identifier(
                    AITraceRecord,
                    None,
                    "ai_trace_id",
                    "ai-trace",
                ),
                subject_linkage=subject_linkage,
                model_identity=(
                    (
                        f"{provider_result.provider_identity}/"
                        f"{provider_result.model_identity}"
                    )
                    if provider_result is not None
                    else (
                        f"{getattr(adapter, '_provider_identity', 'reviewed_local')}/"
                        f"{getattr(adapter, '_model_identity', 'bounded_reviewed_summary')}"
                    )
                ),
                prompt_version=(
                    provider_result.prompt_version
                    if provider_result is not None
                    else str(
                        getattr(
                            adapter,
                            "_prompt_version",
                            _PHASE24_WORKFLOW_PROMPT_VERSIONS[
                                workflow_snapshot.workflow_task
                            ],
                        )
                    )
                ),
                generated_at=generated_at,
                material_input_refs=reviewed_input_refs,
                reviewer_identity="system://bounded-live-assistant",
                lifecycle_state="under_review",
            )

        canonical_subject_linkage = dict(ai_trace_record.subject_linkage)
        canonical_subject_linkage.update(subject_linkage)

        return replace(
            ai_trace_record,
            subject_linkage=canonical_subject_linkage,
            material_input_refs=reviewed_input_refs,
            lifecycle_state="under_review",
            assistant_advisory_draft={
                **workflow_snapshot.to_dict(),
                "source_record_family": record_family,
                "source_record_id": record_id,
                "review_lifecycle_state": "under_review",
                "subject_linkage": canonical_subject_linkage,
                "reviewed_input_refs": reviewed_input_refs,
            },
        )

    def _build_live_assistant_recommendation_record(
        self,
        *,
        context_snapshot: AnalystAssistantContextSnapshot,
        workflow_snapshot: LiveAssistantWorkflowSnapshot,
        ai_trace_record: AITraceRecord,
    ) -> RecommendationRecord:
        source_alert_id = (
            context_snapshot.record_id
            if context_snapshot.record_family == "alert"
            else self._assistant_primary_linked_id(context_snapshot.linked_alert_ids)
        )
        source_case_id = (
            context_snapshot.record_id
            if context_snapshot.record_family == "case"
            else self._assistant_primary_linked_id(context_snapshot.linked_case_ids)
        )
        return RecommendationRecord(
            recommendation_id=self._resolve_new_record_identifier(
                RecommendationRecord,
                None,
                "recommendation_id",
                "recommendation",
            ),
            lead_id=None,
            hunt_run_id=None,
            alert_id=source_alert_id,
            case_id=source_case_id,
            ai_trace_id=ai_trace_record.ai_trace_id,
            review_owner="system://bounded-live-assistant",
            intended_outcome=workflow_snapshot.summary,
            lifecycle_state="under_review",
            reviewed_context=context_snapshot.reviewed_context,
            assistant_advisory_draft={
                "workflow_family": workflow_snapshot.workflow_family,
                "workflow_task": workflow_snapshot.workflow_task,
                "status": workflow_snapshot.status,
                "cited_summary": {"text": workflow_snapshot.summary},
                "citations": workflow_snapshot.citations,
                "unresolved_reasons": workflow_snapshot.unresolved_reasons,
                "operator_follow_up": workflow_snapshot.operator_follow_up,
                "source_record_family": context_snapshot.record_family,
                "source_record_id": context_snapshot.record_id,
                "source_ai_trace_id": ai_trace_record.ai_trace_id,
                "review_lifecycle_state": "under_review",
                "linked_alert_ids": context_snapshot.linked_alert_ids,
                "linked_case_ids": context_snapshot.linked_case_ids,
                "linked_evidence_ids": context_snapshot.linked_evidence_ids,
                "linked_recommendation_ids": context_snapshot.linked_recommendation_ids,
                "linked_reconciliation_ids": context_snapshot.linked_reconciliation_ids,
            },
        )

    @staticmethod
    def _assistant_primary_linked_id(linked_ids: tuple[str, ...]) -> str | None:
        return linked_ids[0] if linked_ids else None

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

    def record_action_approval_decision(
        self,
        *,
        action_request_id: str,
        approver_identity: str,
        authenticated_approver_identity: str | None = None,
        decision: str,
        decision_rationale: str,
        decided_at: datetime,
        approval_decision_id: str | None = None,
    ) -> ApprovalDecisionRecord:
        approver_identity = self._require_non_empty_string(
            approver_identity,
            "approver_identity",
        )
        normalized_decision = self._require_non_empty_string(
            decision,
            "decision",
        ).lower()
        if normalized_decision not in {"grant", "reject"}:
            raise ValueError("decision must be 'grant' or 'reject'")
        decision_rationale = self._require_non_empty_string(
            decision_rationale,
            "decision_rationale",
        )
        decided_at = self._require_aware_datetime(decided_at, "decided_at")
        if authenticated_approver_identity is not None:
            authenticated_approver_identity = self._require_non_empty_string(
                authenticated_approver_identity,
                "authenticated_approver_identity",
            )
            if authenticated_approver_identity != approver_identity:
                raise PermissionError(
                    "authenticated approver identity must match the asserted control-plane approver identity"
                )

        approval_decision: ApprovalDecisionRecord | None = None
        request_expired = False
        with self._store.transaction(isolation_level="SERIALIZABLE"):
            action_request = self._require_review_bound_action_request(action_request_id)
            if action_request.lifecycle_state != "pending_approval":
                raise ValueError(
                    "approval decisions can only be recorded for pending reviewed action requests"
                )
            if action_request.approval_decision_id is not None:
                raise ValueError(
                    f"action request {action_request.action_request_id!r} already has an approval decision"
                )
            if (
                action_request.requester_identity is not None
                and action_request.requester_identity == approver_identity
            ):
                raise PermissionError(
                    "approver identity must be distinct from requester identity"
                )
            if decided_at < action_request.requested_at:
                raise ValueError("decided_at must be on or after requested_at")

            policy_evaluation = self._apply_action_policy_evaluation_overrides(
                computed_policy_evaluation=self._determine_action_policy(
                    self._normalize_action_policy_basis(action_request.policy_basis)
                ),
                persisted_policy_evaluation=action_request.policy_evaluation,
            )
            if policy_evaluation.get("approval_requirement") == "policy_authorized":
                raise PermissionError(
                    "reviewed approval decisions are not authorized when the re-evaluated action policy is policy_authorized"
                )
            if policy_evaluation.get("approval_requirement") != "human_required":
                raise PermissionError(
                    "reviewed approval decisions require a human-required action policy"
                )
            self._require_reviewed_action_approver_policy(
                action_request=action_request,
                approver_identity=approver_identity,
            )

            now = datetime.now(timezone.utc)
            if action_request.expires_at is not None and (
                now > action_request.expires_at or decided_at > action_request.expires_at
            ):
                self.persist_record(
                    replace(action_request, lifecycle_state="expired"),
                    transitioned_at=action_request.expires_at,
                )
                request_expired = True
            else:
                resolved_approval_decision_id = self._resolve_new_record_identifier(
                    ApprovalDecisionRecord,
                    approval_decision_id,
                    "approval_decision_id",
                    "approval-decision",
                )
                decision_state = (
                    "approved" if normalized_decision == "grant" else "rejected"
                )
                approval_decision = self.persist_record(
                    ApprovalDecisionRecord(
                        approval_decision_id=resolved_approval_decision_id,
                        action_request_id=action_request.action_request_id,
                        approver_identities=(approver_identity,),
                        target_snapshot=dict(action_request.target_scope),
                        payload_hash=action_request.payload_hash,
                        decided_at=decided_at,
                        lifecycle_state=decision_state,
                        decision_rationale=decision_rationale,
                        approved_expires_at=(
                            action_request.expires_at
                            if decision_state == "approved"
                            else None
                        ),
                    ),
                    transitioned_at=decided_at,
                )
                self.persist_record(
                    replace(
                        action_request,
                        approval_decision_id=approval_decision.approval_decision_id,
                        lifecycle_state=decision_state,
                        policy_evaluation=policy_evaluation,
                    ),
                    transitioned_at=decided_at,
                )
        if request_expired:
            raise PermissionError(
                "reviewed action request expired before the approval decision was recorded"
            )
        if approval_decision is None:
            raise RuntimeError(
                "approval decision transaction completed without recording a decision"
            )
        self._emit_structured_event(
            logging.INFO,
            "action_approval_decision_recorded",
            approval_decision_id=approval_decision.approval_decision_id,
            action_request_id=approval_decision.action_request_id,
            decision=normalized_decision,
            approver_identity=approver_identity,
            lifecycle_state=approval_decision.lifecycle_state,
        )
        return approval_decision

    def _require_reviewed_action_approver_policy(
        self,
        *,
        action_request: ActionRequestRecord,
        approver_identity: str,
    ) -> None:
        action_class = self._reviewed_action_class_for_request(action_request)
        if action_class not in {"notify", "soft_write"}:
            raise PermissionError(
                "approval decisions are not authorized for the reviewed action class"
            )

        authorized_approver_identities = self._authorized_approver_identities_for_request(
            action_request
        )
        if (
            authorized_approver_identities is not None
            and approver_identity not in authorized_approver_identities
        ):
            raise PermissionError(
                "approver identity is not authorized by the reviewed action approver policy"
            )

    @staticmethod
    def _reviewed_action_class_for_request(action_request: ActionRequestRecord) -> str:
        action_type = action_request.requested_payload.get("action_type")
        if action_type == "notify_identity_owner":
            return "notify"
        if action_type == "create_tracking_ticket":
            return "soft_write"
        raise PermissionError(
            "approval decisions are not authorized for the reviewed action class"
        )

    def _authorized_approver_identities_for_request(
        self,
        action_request: ActionRequestRecord,
    ) -> tuple[str, ...] | None:
        configured_identities = action_request.policy_evaluation.get(
            "authorized_approver_identities"
        )
        if configured_identities is None:
            return None
        if not isinstance(configured_identities, (list, tuple)):
            raise ValueError(
                "policy_evaluation.authorized_approver_identities must be a sequence of identities"
            )

        normalized_identities: list[str] = []
        for index, identity in enumerate(configured_identities):
            normalized_identity = self._require_non_empty_string(
                identity,
                f"policy_evaluation.authorized_approver_identities[{index}]",
            )
            if normalized_identity not in normalized_identities:
                normalized_identities.append(normalized_identity)
        if not normalized_identities:
            raise ValueError(
                "policy_evaluation.authorized_approver_identities must contain at least one identity"
            )
        return tuple(normalized_identities)

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
        if not isinstance(value, _DATETIME_TYPE):
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

    def _require_case_host_identifier(self, case: CaseRecord) -> str:
        asset = case.reviewed_context.get("asset")
        if not isinstance(asset, Mapping):
            raise ValueError(
                "reviewed case asset.host_identifier must explicitly bind osquery host context"
            )
        host_identifier = asset.get("host_identifier")
        if not isinstance(host_identifier, str) or not host_identifier.strip():
            raise ValueError(
                "reviewed case asset.host_identifier must explicitly bind osquery host context"
            )
        return host_identifier

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
                        provenance=evidence.provenance,
                        content=evidence.content,
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
                replace(
                    existing_case,
                    alert_id=alert.alert_id,
                    finding_id=alert.finding_id,
                    evidence_ids=merged_case_evidence_ids,
                    reviewed_context=_merge_reviewed_context(
                        existing_case.reviewed_context,
                        alert.reviewed_context,
                    ),
                )
                if existing_case is not None
                else CaseRecord(
                    case_id=resolved_case_id,
                    alert_id=alert.alert_id,
                    finding_id=alert.finding_id,
                    evidence_ids=merged_case_evidence_ids,
                    lifecycle_state=case_lifecycle_state,
                    reviewed_context=alert.reviewed_context,
                )
            )
            promoted_alert = self.persist_record(
                replace(
                    alert,
                    case_id=promoted_case.case_id,
                    lifecycle_state="escalated_to_case",
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
                    replace(
                        alert,
                        finding_id=finding_id,
                        analytic_signal_id=analytic_signal_id,
                        reviewed_context=merged_reviewed_context,
                    )
                )
                disposition = "updated"
            elif merged_reviewed_context != alert.reviewed_context:
                alert = self.persist_record(
                    replace(
                        alert,
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
                            replace(
                                existing_case,
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
                provenance={},
                content={},
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
                        replace(
                            existing_case,
                            evidence_ids=merged_case_evidence_ids,
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
        self._restore_readiness_service.require_empty_authoritative_restore_target()

    def _validate_authoritative_record_chain_restore(
        self,
        records_by_family: Mapping[str, tuple[ControlPlaneRecord, ...]],
        *,
        restored_record_counts: Mapping[str, int] | None = None,
    ) -> None:
        self._restore_readiness_service.validate_authoritative_record_chain_restore(
            records_by_family,
            restored_record_counts=restored_record_counts,
        )

    def _require_case_record(self, case_id: str) -> CaseRecord:
        case_id = self._require_non_empty_string(case_id, "case_id")
        case = self._store.get(CaseRecord, case_id)
        if case is None:
            raise LookupError(f"Missing case {case_id!r}")
        return case

    def _require_action_request_record(self, action_request_id: str) -> ActionRequestRecord:
        action_request_id = self._require_non_empty_string(
            action_request_id,
            "action_request_id",
        )
        action_request = self._store.get(ActionRequestRecord, action_request_id)
        if action_request is None:
            raise LookupError(f"Missing action request {action_request_id!r}")
        return action_request

    def _require_review_bound_action_request(
        self,
        action_request_id: str,
    ) -> ActionRequestRecord:
        action_request = self._require_action_request_record(action_request_id)
        if not self._action_request_is_review_bound(action_request):
            raise ValueError(
                "action_request_id must reference a reviewed action request"
            )
        return action_request

    def _require_action_review_visibility_context_record(
        self,
        action_request: ActionRequestRecord,
    ) -> CaseRecord | AlertRecord:
        if action_request.case_id is not None:
            return self._require_reviewed_operator_case(action_request.case_id)
        if action_request.alert_id is None:
            raise ValueError(
                "reviewed action request must be linked to a case or alert before "
                "recording runtime visibility"
            )
        alert = self._store.get(AlertRecord, action_request.alert_id)
        if alert is None:
            raise LookupError(f"Missing alert {action_request.alert_id!r}")
        return alert

    def _persist_action_review_visibility_context_record(
        self,
        *,
        context_record: CaseRecord | AlertRecord,
        reviewed_context_update: Mapping[str, object],
    ) -> CaseRecord | AlertRecord:
        updated_reviewed_context = _merge_reviewed_context(
            context_record.reviewed_context,
            reviewed_context_update,
        )
        return self.persist_record(
            replace(
                context_record,
                reviewed_context=updated_reviewed_context,
            )
        )

    def _require_reviewed_operator_case(self, case_id: str) -> CaseRecord:
        return self._reviewed_slice_policy.require_operator_case(case_id)

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

    def _require_reviewed_case_scoped_advisory_read(
        self,
        context_snapshot: AnalystAssistantContextSnapshot,
    ) -> None:
        self._reviewed_slice_policy.require_case_scoped_advisory_read(context_snapshot)

    def _require_reviewed_alert_scoped_queue_summary_read(
        self,
        context_snapshot: AnalystAssistantContextSnapshot,
    ) -> None:
        self._reviewed_slice_policy.require_alert_scoped_queue_summary_read(
            context_snapshot
        )

    @staticmethod
    def _reviewed_case_scoped_read_error(record_family: str, record_id: str) -> str:
        return ReviewedSlicePolicy.case_scoped_read_error(record_family, record_id)

    def _require_reviewed_case_scoped_recommendation_payload(
        self,
        payload: Mapping[str, object],
        *,
        approved_cases: Mapping[str, CaseRecord],
        error_message: str,
    ) -> None:
        self._reviewed_slice_policy.require_case_scoped_recommendation_payload(
            payload,
            approved_cases=approved_cases,
            error_message=error_message,
        )

    @staticmethod
    def _reviewed_operator_source_family(context: object) -> str | None:
        return ReviewedSlicePolicy.source_family(context)

    @staticmethod
    def _reviewed_context_explicitly_declares_provenance(context: object) -> bool:
        return ReviewedSlicePolicy.context_explicitly_declares_provenance(context)

    def _require_reviewed_operator_case_record(self, case: CaseRecord) -> CaseRecord:
        return self._reviewed_slice_policy.require_operator_case_record(case)

    def _require_reviewed_operator_alert_record(self, alert: AlertRecord) -> AlertRecord:
        return self._reviewed_slice_policy.require_operator_alert_record(alert)

    def _case_is_in_reviewed_operator_slice(self, case: CaseRecord) -> bool:
        return self._reviewed_slice_policy.case_is_in_operator_slice(case)

    def _alert_is_in_reviewed_operator_slice(self, alert: AlertRecord) -> bool:
        return self._reviewed_slice_policy.alert_is_in_operator_slice(alert)

    def _reviewed_context_declares_out_of_scope_provenance(self, context: object) -> bool:
        return self._reviewed_slice_policy.context_declares_out_of_scope_provenance(
            context
        )

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

    def _validate_alert_evidence_linkage(
        self,
        *,
        alert: AlertRecord,
        evidence_ids: tuple[str, ...],
        field_name: str,
    ) -> None:
        for evidence_id in evidence_ids:
            evidence = self._store.get(EvidenceRecord, evidence_id)
            if evidence is None:
                raise LookupError(f"Missing evidence {evidence_id!r}")
            shares_alert = evidence.alert_id == alert.alert_id
            shares_case = alert.case_id is not None and evidence.case_id == alert.case_id
            if not shares_alert and not shares_case:
                raise ValueError(
                    f"{field_name} contains evidence {evidence_id!r} that is not "
                    f"linked to alert {alert.alert_id!r}"
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
        lifecycle_state = (
            AegisOpsControlPlaneService._case_lifecycle_state_for_triage_disposition(
                disposition
            )
        )
        if lifecycle_state is not None:
            return lifecycle_state
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
