from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

from .cited_recommendation_draft import build_cited_recommendation_draft
from ..models import AITraceRecord, RecommendationRecord
from ..runtime.service_snapshots import (
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
    cited_recommendation_draft = build_cited_recommendation_draft(
        recommendation_context_payload=_cited_recommendation_context_payload(snapshot),
        prompt_text=_recommendation_prompt_text(snapshot),
    )
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
            "cited_recommendation_draft": cited_recommendation_draft,
        },
        reviewed_context=dict(snapshot.reviewed_context),
        linked_alert_ids=snapshot.linked_alert_ids,
        linked_case_ids=snapshot.linked_case_ids,
        linked_evidence_ids=snapshot.linked_evidence_ids,
        linked_recommendation_ids=snapshot.linked_recommendation_ids,
        linked_reconciliation_ids=snapshot.linked_reconciliation_ids,
    )


def _cited_recommendation_context_payload(
    snapshot: AnalystAssistantContextSnapshot,
) -> dict[str, object]:
    anchor_case_id = _anchor_case_id_from_snapshot(snapshot)
    reviewed_records = _cited_reviewed_records(snapshot, anchor_case_id=anchor_case_id)
    return {
        "contract_version": "phase-60-6",
        "review_anchor": {
            "record_family": "case",
            "record_id": anchor_case_id,
            "direct_binding_required": True,
        },
        "reviewed_records": reviewed_records,
        "draft_requests": _cited_draft_requests(
            snapshot,
            anchor_case_id=anchor_case_id,
            reviewed_records=reviewed_records,
        ),
    }


def _anchor_case_id_from_snapshot(
    snapshot: AnalystAssistantContextSnapshot,
) -> str | None:
    if snapshot.record_family == "case":
        return snapshot.record_id
    record_case_id = _normalized_string(snapshot.record.get("case_id"))
    if record_case_id is not None:
        return record_case_id
    if len(snapshot.linked_case_ids) == 1:
        return snapshot.linked_case_ids[0]
    return None


def _cited_reviewed_records(
    snapshot: AnalystAssistantContextSnapshot,
    *,
    anchor_case_id: str | None,
) -> tuple[dict[str, object], ...]:
    records: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()

    for record_family, record in (
        (snapshot.record_family, snapshot.record),
        *(("case", record) for record in snapshot.linked_case_records),
        *(("alert", record) for record in snapshot.linked_alert_records),
        *(("evidence", record) for record in snapshot.linked_evidence_records),
        *(("recommendation", record) for record in snapshot.linked_recommendation_records),
    ):
        if not isinstance(record, Mapping):
            continue
        record_id = _record_id_for_family(record, record_family)
        if record_id is None:
            continue
        if _record_anchor_case_id(record, record_family) != anchor_case_id:
            continue
        key = (record_family, record_id)
        if key in seen:
            continue
        seen.add(key)
        records.append(
            {
                "record_family": record_family,
                "record_id": record_id,
                "anchored_record_family": "case",
                "anchored_record_id": anchor_case_id,
                "created_by": "aegisops",
                "citation": {
                    "record_family": record_family,
                    "record_id": record_id,
                },
            }
        )
    return tuple(records)


def _cited_draft_requests(
    snapshot: AnalystAssistantContextSnapshot,
    *,
    anchor_case_id: str | None,
    reviewed_records: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    citation_by_record_id = {
        record["record_id"]: f"{record['record_family']}:{record['record_id']}"
        for record in reviewed_records
        if isinstance(record.get("record_family"), str)
        and isinstance(record.get("record_id"), str)
    }
    reviewed_citations = tuple(citation_by_record_id.values())
    posture, operator_correction = _operator_feedback_from_snapshot(snapshot)
    draft_requests: list[dict[str, object]] = []
    for index, candidate in enumerate(
        _mapping_sequence(snapshot.advisory_output.get("candidate_recommendations")),
        start=1,
    ):
        draft_text = _normalized_string(candidate.get("text"))
        if draft_text is None:
            continue
        citation_ids = _normalized_candidate_citations(
            candidate.get("citations"),
            anchor_case_id=anchor_case_id,
            citation_by_record_id=citation_by_record_id,
            reviewed_citations=reviewed_citations,
        )
        draft_requests.append(
            {
                "draft_id": (
                    f"recommendation-draft:{snapshot.record_family}:"
                    f"{snapshot.record_id}:{index}"
                ),
                "draft_text": draft_text,
                "operator_feedback_posture": posture,
                "operator_correction": operator_correction,
                "citation_ids": citation_ids,
            }
        )
    return tuple(draft_requests)


def _operator_feedback_from_snapshot(
    snapshot: AnalystAssistantContextSnapshot,
) -> tuple[str, str | None]:
    attached_draft = snapshot.record.get("assistant_advisory_draft")
    if isinstance(attached_draft, Mapping):
        attached_state = _normalized_string(
            attached_draft.get("operator_feedback_posture")
        ) or _normalized_string(attached_draft.get("review_state"))
        operator_correction = (
            _normalized_string(attached_draft.get("operator_correction"))
            or _normalized_string(attached_draft.get("correction"))
            or _normalized_string(attached_draft.get("reviewer_note"))
        )
        if attached_state in {"accepted", "rejected", "unresolved"}:
            return attached_state, None
        if attached_state == "corrected":
            return "corrected", operator_correction

    lifecycle_state = _normalized_string(snapshot.record.get("lifecycle_state"))
    if lifecycle_state in {"accepted", "accepted_for_reference"}:
        return "accepted", None
    if lifecycle_state in {"rejected", "rejected_for_reference"}:
        return "rejected", None
    return "unresolved", None


def _normalized_candidate_citations(
    candidate_citations: object,
    *,
    anchor_case_id: str | None,
    citation_by_record_id: Mapping[str, str],
    reviewed_citations: tuple[str, ...],
) -> tuple[str, ...]:
    citations: list[str] = []
    if anchor_case_id is not None:
        citations.append(f"case:{anchor_case_id}")
    for citation in _string_sequence(candidate_citations):
        if citation in reviewed_citations:
            citations.append(citation)
            continue
        mapped_citation = citation_by_record_id.get(citation)
        if mapped_citation is not None:
            citations.append(mapped_citation)
    return _dedupe_string_sequence(tuple(citations))


def _recommendation_prompt_text(snapshot: AnalystAssistantContextSnapshot) -> object:
    intended_outcome = snapshot.record.get("intended_outcome")
    if isinstance(intended_outcome, str):
        return intended_outcome
    return ""


def _record_anchor_case_id(record: Mapping[str, object], record_family: str) -> str | None:
    if record_family == "case":
        return _record_id_for_family(record, "case")
    record_case_id = _normalized_string(record.get("case_id"))
    if record_case_id is not None:
        return record_case_id
    subject_linkage = record.get("subject_linkage")
    if isinstance(subject_linkage, Mapping):
        return _normalized_string(subject_linkage.get("source_case_id"))
    return None


def _record_id_for_family(record: Mapping[str, object], record_family: str) -> str | None:
    identifier_field = "ai_trace_id" if record_family == "ai_trace" else f"{record_family}_id"
    return _normalized_string(record.get(identifier_field))


def _mapping_sequence(value: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _string_sequence(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return _dedupe_string_sequence(tuple(item for item in value if isinstance(item, str)))


def _dedupe_string_sequence(values: tuple[str, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


def _normalized_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


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
