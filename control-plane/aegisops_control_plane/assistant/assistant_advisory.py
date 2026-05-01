from __future__ import annotations

from typing import Any, Protocol

from ..models import AITraceRecord, RecommendationRecord
from ..service_snapshots import (
    AdvisoryInspectionSnapshot,
    AnalystAssistantContextSnapshot,
    RecommendationDraftSnapshot,
)


def advisory_inspection_snapshot_from_context(
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


def recommendation_draft_snapshot_from_context(
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


class AssistantAdvisoryAssembler(Protocol):
    def inspect_advisory_output(self, record_family: str, record_id: str) -> Any:
        ...

    def render_recommendation_draft(self, record_family: str, record_id: str) -> Any:
        ...

    def attach_assistant_advisory_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationRecord | AITraceRecord:
        ...


class AssistantAdvisoryCoordinator:
    """Coordinates advisory-only assembly behind the service API."""

    def __init__(self, assembler: AssistantAdvisoryAssembler) -> None:
        self._assembler = assembler

    def inspect_advisory_output(self, record_family: str, record_id: str) -> Any:
        return self._assembler.inspect_advisory_output(record_family, record_id)

    def render_recommendation_draft(self, record_family: str, record_id: str) -> Any:
        return self._assembler.render_recommendation_draft(record_family, record_id)

    def attach_assistant_advisory_draft(
        self,
        record_family: str,
        record_id: str,
    ) -> RecommendationRecord | AITraceRecord:
        return self._assembler.attach_assistant_advisory_draft(record_family, record_id)
