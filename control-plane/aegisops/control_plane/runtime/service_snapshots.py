from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Mapping

_DATETIME_TYPE = datetime


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
class AuthenticatedRuntimePrincipal:
    identity: str
    role: str
    access_path: str
    proxy_service_account: str | None = None
    identity_provider: str | None = None
    subject: str | None = None


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
    lane_counts: dict[str, int]
    records: tuple[dict[str, object], ...]

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "queue_name": self.queue_name,
                "total_records": self.total_records,
                "lane_counts": self.lane_counts,
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
    case_timeline_projection: dict[str, object]
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
                "case_timeline_projection": self.case_timeline_projection,
                "provenance_summary": self.provenance_summary,
                "current_action_review": self.current_action_review,
                "action_reviews": self.action_reviews,
                "external_ticket_reference": self.external_ticket_reference,
            }
        )


@dataclass(frozen=True)
class ActionReviewDetailSnapshot:
    read_only: bool
    action_request_id: str
    action_review: dict[str, object]
    current_action_review: dict[str, object] | None
    case_record: dict[str, object] | None
    alert_record: dict[str, object] | None

    def to_dict(self) -> dict[str, object]:
        return _json_ready(
            {
                "read_only": self.read_only,
                "action_request_id": self.action_request_id,
                "action_review": self.action_review,
                "current_action_review": self.current_action_review,
                "case_record": self.case_record,
                "alert_record": self.alert_record,
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


__all__ = [
    "ActionReviewDetailSnapshot",
    "AdvisoryInspectionSnapshot",
    "AlertDetailSnapshot",
    "AnalystAssistantContextSnapshot",
    "AnalystQueueSnapshot",
    "AuthenticatedRuntimePrincipal",
    "CaseDetailSnapshot",
    "LiveAssistantWorkflowSnapshot",
    "ReadinessDiagnosticsSnapshot",
    "RecommendationDraftSnapshot",
    "ReconciliationStatusSnapshot",
    "RecordInspectionSnapshot",
    "RestoreDrillSnapshot",
    "RestoreSummarySnapshot",
    "RuntimeSnapshot",
    "ShutdownStatusSnapshot",
    "StartupStatusSnapshot",
    "_json_ready",
]
