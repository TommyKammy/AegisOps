from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import ClassVar, Mapping, Union


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType(dict(value))


@dataclass(frozen=True)
class ControlPlaneRecord:
    record_family: ClassVar[str]
    identifier_field: ClassVar[str]

    @property
    def record_id(self) -> str:
        return getattr(self, self.identifier_field)


@dataclass(frozen=True)
class AlertRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "alert"
    identifier_field: ClassVar[str] = "alert_id"

    alert_id: str
    finding_id: str
    analytic_signal_id: str | None
    case_id: str | None
    lifecycle_state: str


@dataclass(frozen=True)
class AnalyticSignalRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "analytic_signal"
    identifier_field: ClassVar[str] = "analytic_signal_id"

    analytic_signal_id: str
    substrate_detection_record_id: str | None
    finding_id: str | None
    alert_ids: tuple[str, ...]
    case_ids: tuple[str, ...]
    correlation_key: str
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    lifecycle_state: str


@dataclass(frozen=True)
class NativeDetectionRecord:
    substrate_key: str
    native_record_id: str
    record_kind: str
    correlation_key: str
    first_seen_at: datetime
    last_seen_at: datetime
    metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", _freeze_mapping(self.metadata))


@dataclass(frozen=True)
class AnalyticSignalAdmission:
    finding_id: str
    analytic_signal_id: str | None
    substrate_detection_record_id: str | None
    correlation_key: str
    first_seen_at: datetime
    last_seen_at: datetime
    materially_new_work: bool = False


@dataclass(frozen=True)
class CaseRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "case"
    identifier_field: ClassVar[str] = "case_id"

    case_id: str
    alert_id: str | None
    finding_id: str | None
    evidence_ids: tuple[str, ...]
    lifecycle_state: str


@dataclass(frozen=True)
class EvidenceRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "evidence"
    identifier_field: ClassVar[str] = "evidence_id"

    evidence_id: str
    source_record_id: str
    alert_id: str | None
    case_id: str | None
    source_system: str
    collector_identity: str
    acquired_at: datetime
    derivation_relationship: str | None
    lifecycle_state: str


@dataclass(frozen=True)
class ObservationRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "observation"
    identifier_field: ClassVar[str] = "observation_id"

    observation_id: str
    hunt_id: str | None
    hunt_run_id: str | None
    alert_id: str | None
    case_id: str | None
    supporting_evidence_ids: tuple[str, ...]
    author_identity: str
    observed_at: datetime
    scope_statement: str
    lifecycle_state: str


@dataclass(frozen=True)
class LeadRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "lead"
    identifier_field: ClassVar[str] = "lead_id"

    lead_id: str
    observation_id: str | None
    finding_id: str | None
    hunt_run_id: str | None
    alert_id: str | None
    case_id: str | None
    triage_owner: str
    triage_rationale: str
    lifecycle_state: str


@dataclass(frozen=True)
class RecommendationRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "recommendation"
    identifier_field: ClassVar[str] = "recommendation_id"

    recommendation_id: str
    lead_id: str | None
    hunt_run_id: str | None
    alert_id: str | None
    case_id: str | None
    ai_trace_id: str | None
    review_owner: str
    intended_outcome: str
    lifecycle_state: str


@dataclass(frozen=True)
class ApprovalDecisionRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "approval_decision"
    identifier_field: ClassVar[str] = "approval_decision_id"

    approval_decision_id: str
    action_request_id: str
    approver_identities: tuple[str, ...]
    target_snapshot: Mapping[str, object]
    payload_hash: str
    decided_at: datetime | None
    lifecycle_state: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_snapshot", _freeze_mapping(self.target_snapshot))


@dataclass(frozen=True)
class ActionRequestRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "action_request"
    identifier_field: ClassVar[str] = "action_request_id"

    action_request_id: str
    approval_decision_id: str | None
    case_id: str | None
    alert_id: str | None
    finding_id: str | None
    idempotency_key: str
    target_scope: Mapping[str, object]
    payload_hash: str
    requested_at: datetime
    expires_at: datetime | None
    lifecycle_state: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "target_scope", _freeze_mapping(self.target_scope))


@dataclass(frozen=True)
class HuntRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "hunt"
    identifier_field: ClassVar[str] = "hunt_id"

    hunt_id: str
    hypothesis_statement: str
    hypothesis_version: str
    owner_identity: str
    scope_boundary: str
    opened_at: datetime
    alert_id: str | None
    case_id: str | None
    lifecycle_state: str


@dataclass(frozen=True)
class HuntRunRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "hunt_run"
    identifier_field: ClassVar[str] = "hunt_run_id"

    hunt_run_id: str
    hunt_id: str
    scope_snapshot: Mapping[str, object]
    execution_plan_reference: str
    output_linkage: Mapping[str, object]
    started_at: datetime | None
    completed_at: datetime | None
    lifecycle_state: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "scope_snapshot", _freeze_mapping(self.scope_snapshot))
        object.__setattr__(self, "output_linkage", _freeze_mapping(self.output_linkage))


@dataclass(frozen=True)
class AITraceRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "ai_trace"
    identifier_field: ClassVar[str] = "ai_trace_id"

    ai_trace_id: str
    subject_linkage: Mapping[str, object]
    model_identity: str
    prompt_version: str
    generated_at: datetime
    material_input_refs: tuple[str, ...]
    reviewer_identity: str
    lifecycle_state: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_linkage", _freeze_mapping(self.subject_linkage))


@dataclass(frozen=True)
class ReconciliationRecord(ControlPlaneRecord):
    record_family: ClassVar[str] = "reconciliation"
    identifier_field: ClassVar[str] = "reconciliation_id"

    reconciliation_id: str
    subject_linkage: Mapping[str, object]
    alert_id: str | None
    finding_id: str | None
    analytic_signal_id: str | None
    workflow_execution_id: str | None
    linked_execution_ids: tuple[str, ...]
    correlation_key: str
    first_seen_at: datetime | None
    last_seen_at: datetime | None
    ingest_disposition: str
    mismatch_summary: str
    compared_at: datetime
    lifecycle_state: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "subject_linkage", _freeze_mapping(self.subject_linkage))


AnyControlPlaneRecord = Union[
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
]
