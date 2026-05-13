from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .assistant_context import _advisory_text_claims_authority_or_scope_expansion
from .live_assistant_workflow import phase24_live_assistant_prompt_injection_flags

_AGENT_NAME = "cited_recommendation_draft_agent"
_TOOL_NAME = "recommendation_draft"
_AUTHORITY_CEILING = "advisory_only"
_CONTRACT_VERSION = "phase-60-6"
_REGISTRY_CITATIONS = (
    "docs/automation/ai-agent-registry.json",
    "docs/automation/ai-tool-registry.json",
    "docs/automation/ai-disabled-degraded-mode-contract.json",
)
_SUPPORTED_RECORD_FAMILIES = (
    "case",
    "queue",
    "alert",
    "evidence",
    "recommendation",
    "runbook",
    "source_health",
    "ai_trace",
)
_SUPPORTED_FEEDBACK_POSTURES = (
    "accepted",
    "rejected",
    "corrected",
    "unresolved",
)
_NEGATIVE_AUTHORITY = (
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "recommendation_truth",
    "workflow_completion",
    "workflow_truth",
)
_AUTHORITY_PRESSURE_TERMS = (
    "approve action",
    "approve the action",
    "execute action",
    "execute the action",
    "reconcile receipt",
    "reconcile the receipt",
    "close case",
    "close the case",
    "activate detector",
    "activate detectors",
    "create source truth",
    "bypass policy",
    "bypass the policy",
)
_FEEDBACK_COERCION_TERMS = (
    "accept every recommendation",
    "accept all recommendations",
    "force acceptance",
    "force accept",
    "hide rejected",
    "hide corrected",
)
_WORKFLOW_COMPLETION_TERMS = (
    "mark workflow complete",
    "mark the workflow complete",
    "complete workflow",
    "complete the workflow",
)
_UNCERTAINTY_SUPPRESSION_TERMS = (
    "hide citations",
    "hide uncertainty",
    "hide stale",
    "hide conflicts",
    "hide conflicting",
    "suppress uncertainty",
    "suppress stale",
    "suppress conflicts",
)


def build_cited_recommendation_draft(
    *,
    recommendation_context_payload: object,
    ai_enablement_posture: str = "enabled",
    prompt_text: object = "",
) -> dict[str, object]:
    validation = _validated_recommendation_payload(recommendation_context_payload)
    if validation["reasons"]:
        return _fallback_payload(
            _base_payload(),
            mode="recommendation_draft_untrusted",
            unresolved_reasons=validation["reasons"],
        )

    records = validation["records"]
    drafts = validation["draft_requests"]
    base = _base_payload(
        anchor_id=validation["anchor_id"],
        records=records,
    )
    prompt_flags = _prompt_pressure_flags(prompt_text)
    if prompt_flags:
        return _blocked_payload(base, prompt_flags)

    global_uncertainty = _record_uncertainty_flags(records)
    if ai_enablement_posture == "disabled":
        return _fallback_payload(
            base,
            mode="ai_disabled",
            unresolved_reasons=("ai_advisory_disabled",),
        )
    if ai_enablement_posture == "degraded":
        return _fallback_payload(
            base,
            mode="ai_degraded",
            unresolved_reasons=("ai_advisory_degraded",),
        )
    if ai_enablement_posture != "enabled":
        return _fallback_payload(
            base,
            mode="ai_enablement_untrusted",
            unresolved_reasons=("malformed_ai_enablement_posture",),
        )

    recommendation_drafts = tuple(
        _recommendation_draft(draft, global_uncertainty=global_uncertainty)
        for draft in drafts
    )
    unresolved_reasons = _dedupe_strings(
        (
            *global_uncertainty,
            *(
                reason
                for draft in recommendation_drafts
                for reason in _string_tuple(draft.get("unresolved_reasons"))
            ),
        )
    )
    return {
        **base,
        "decision": "draft",
        "mode": "cited_recommendation_draft",
        "unresolved_reasons": unresolved_reasons,
        "uncertainty_flags": unresolved_reasons,
        "ai_generation_allowed": True,
        "trace_creation_allowed": False,
        "non_ai_recommendation_workflow_available": True,
        "recommendation_drafts": recommendation_drafts,
    }


def _base_payload(
    *,
    anchor_id: str | None = None,
    records: tuple[Mapping[str, object], ...] = (),
) -> dict[str, object]:
    citations = _dedupe_strings(
        (
            *_REGISTRY_CITATIONS,
            "docs/phase-56-closeout-evaluation.md",
            "docs/phase-58-closeout-evaluation.md",
            "docs/phase-59-closeout-evaluation.md",
            *(("case:" + anchor_id,) if anchor_id is not None else ()),
            *(
                citation
                for record in records
                for citation in _reviewed_record_citations(record)
            ),
        )
    )
    return {
        "read_only": True,
        "agent_name": _AGENT_NAME,
        "registered_tool_name": _TOOL_NAME,
        "record_families": _SUPPORTED_RECORD_FAMILIES,
        "authority_ceiling": _AUTHORITY_CEILING,
        "authority_boundary": "cited_advisory_recommendation_draft_only",
        "authoritative_workflow_truth": False,
        "mutates_authoritative_records": False,
        "approval_authority": False,
        "execution_authority": False,
        "reconciliation_authority": False,
        "case_closure_authority": False,
        "negative_authority": _NEGATIVE_AUTHORITY,
        "citations": citations,
    }


def _blocked_payload(
    base: Mapping[str, object],
    prompt_flags: tuple[str, ...],
) -> dict[str, object]:
    return {
        **base,
        "decision": "blocked",
        "mode": "prompt_pressure_blocked",
        "unresolved_reasons": prompt_flags,
        "uncertainty_flags": prompt_flags,
        "ai_generation_allowed": False,
        "trace_creation_allowed": False,
        "non_ai_recommendation_workflow_available": True,
        "recommendation_drafts": (),
    }


def _fallback_payload(
    base: Mapping[str, object],
    *,
    mode: str,
    unresolved_reasons: tuple[str, ...],
) -> dict[str, object]:
    return {
        **base,
        "decision": "fallback",
        "mode": mode,
        "unresolved_reasons": unresolved_reasons,
        "uncertainty_flags": unresolved_reasons,
        "ai_generation_allowed": False,
        "trace_creation_allowed": False,
        "non_ai_recommendation_workflow_available": True,
        "recommendation_drafts": (),
    }


def _validated_recommendation_payload(
    recommendation_context_payload: object,
) -> dict[str, object]:
    if not isinstance(recommendation_context_payload, Mapping):
        return _invalid(("malformed_recommendation_context_payload",))
    if recommendation_context_payload.get("contract_version") != _CONTRACT_VERSION:
        return _invalid(("unsupported_recommendation_draft_contract_version",))
    anchor = recommendation_context_payload.get("review_anchor")
    if not isinstance(anchor, Mapping):
        return _invalid(("missing_review_anchor",))
    if anchor.get("direct_binding_required") is not True:
        return _invalid(("review_anchor_without_direct_binding",))
    anchor_family = _string(anchor.get("record_family"))
    anchor_id = _string(anchor.get("record_id"))
    if anchor_family != "case" or anchor_id is None:
        return _invalid(("unsupported_review_anchor",))

    raw_records = recommendation_context_payload.get("reviewed_records")
    if not isinstance(raw_records, Sequence) or isinstance(raw_records, (str, bytes)):
        return _invalid(("malformed_reviewed_records",))
    raw_drafts = recommendation_context_payload.get("draft_requests")
    if not isinstance(raw_drafts, Sequence) or isinstance(raw_drafts, (str, bytes)):
        return _invalid(("malformed_draft_requests",))
    if not raw_drafts:
        return _invalid(("missing_reviewable_draft_requests",))

    reasons: list[str] = []
    records: list[Mapping[str, object]] = []
    for raw_record in raw_records:
        if not isinstance(raw_record, Mapping):
            reasons.append("malformed_reviewed_record")
            continue
        record_family = _string(raw_record.get("record_family"))
        record_id = _string(raw_record.get("record_id"))
        if record_family not in _SUPPORTED_RECORD_FAMILIES:
            reasons.append("unsupported_reviewed_record_family")
        if record_id is None:
            reasons.append("missing_reviewed_record_id")
        if not _record_bound_to_review_anchor(raw_record, anchor_family, anchor_id):
            reasons.append("record_not_bound_to_review_anchor")
        if _normalized_string(raw_record.get("created_by")) == "ai":
            reasons.append("ai_created_recommendation_context")
        if not _citation_matches(raw_record.get("citation"), raw_record):
            reasons.append("missing_reviewed_record_citation")
        records.append(raw_record)

    reviewed_citations = _reviewed_record_citation_set(
        tuple(records),
        anchor_family=anchor_family,
        anchor_id=anchor_id,
    )
    drafts: list[Mapping[str, object]] = []
    for raw_draft in raw_drafts:
        if not isinstance(raw_draft, Mapping):
            reasons.append("malformed_draft_request")
            continue
        if _string(raw_draft.get("draft_id")) is None:
            reasons.append("missing_draft_id")
        if _normalized_string(raw_draft.get("draft_text")) is None:
            reasons.append("missing_draft_text")
        posture = _string(raw_draft.get("operator_feedback_posture"))
        if posture not in _SUPPORTED_FEEDBACK_POSTURES:
            reasons.append("unsupported_operator_feedback_posture")
        if (
            posture == "corrected"
            and _normalized_string(raw_draft.get("operator_correction")) is None
        ):
            reasons.append("missing_operator_correction")
        citation_ids = _string_tuple(raw_draft.get("citation_ids"))
        if not _has_required_draft_citations(citation_ids):
            reasons.append("missing_required_draft_citation")
        if not set(citation_ids).issubset(reviewed_citations):
            reasons.append("untrusted_draft_citation")
        drafts.append(raw_draft)

    if not any(
        _string(record.get("record_family")) == "case"
        and _string(record.get("record_id")) == anchor_id
        for record in records
    ):
        reasons.append("missing_anchor_case_record")
    if reasons:
        return _invalid(_dedupe_strings(tuple(reasons)))
    return {
        "anchor_id": anchor_id,
        "records": tuple(records),
        "draft_requests": tuple(drafts),
        "reasons": (),
    }


def _invalid(reasons: tuple[str, ...]) -> dict[str, object]:
    return {
        "anchor_id": None,
        "records": (),
        "draft_requests": (),
        "reasons": reasons,
    }


def _recommendation_draft(
    draft: Mapping[str, object],
    *,
    global_uncertainty: tuple[str, ...],
) -> dict[str, object]:
    requested_posture = _string(draft.get("operator_feedback_posture")) or "unresolved"
    unresolved_reasons = list(global_uncertainty)
    if requested_posture == "unresolved":
        unresolved_reasons.append("operator_unresolved")
    operator_feedback_posture = (
        "unresolved" if unresolved_reasons else requested_posture
    )
    return {
        "draft_id": _string(draft.get("draft_id")),
        "draft_text": _string(draft.get("draft_text")),
        "operator_feedback_posture": operator_feedback_posture,
        "requested_feedback_posture": requested_posture,
        "operator_correction": _string(draft.get("operator_correction")),
        "unresolved_reasons": _dedupe_strings(tuple(unresolved_reasons)),
        "citation_ids": _string_tuple(draft.get("citation_ids")),
        "advisory_only": True,
        "counts_as_workflow_truth": False,
        "can_approve_action": False,
        "can_execute_action": False,
        "can_reconcile": False,
        "can_close_case": False,
    }


def _record_uncertainty_flags(
    records: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    flags: list[str] = []
    conflict_values: dict[str, set[str]] = {}
    for record in records:
        if _string(record.get("record_family")) != "evidence":
            continue
        if _normalized_string(record.get("evidence_status")) == "stale":
            flags.append("stale_evidence")
        conflict_group = _string(record.get("conflict_group"))
        reviewed_value = _string(record.get("reviewed_value"))
        if conflict_group is not None and reviewed_value is not None:
            conflict_values.setdefault(conflict_group, set()).add(reviewed_value)
    if any(len(values) > 1 for values in conflict_values.values()):
        flags.append("conflicting_evidence")
    return _dedupe_strings(tuple(flags))


def _has_required_draft_citations(citation_ids: tuple[str, ...]) -> bool:
    if not any(citation_id.startswith("case:") for citation_id in citation_ids):
        return False
    return any(
        citation_id.startswith(
            ("evidence:", "recommendation:", "runbook:", "queue:")
        )
        for citation_id in citation_ids
    )


def _reviewed_record_citations(record: Mapping[str, object]) -> tuple[str, ...]:
    if not _citation_matches(record.get("citation"), record):
        return ()
    record_family = _string(record.get("record_family"))
    record_id = _string(record.get("record_id"))
    if record_family is None or record_id is None:
        return ()
    return (f"{record_family}:{record_id}",)


def _reviewed_record_citation_set(
    records: tuple[Mapping[str, object], ...],
    *,
    anchor_family: str,
    anchor_id: str,
) -> set[str]:
    return {
        citation
        for record in records
        if _record_bound_to_review_anchor(record, anchor_family, anchor_id)
        for citation in _reviewed_record_citations(record)
    }


def _record_bound_to_review_anchor(
    record: Mapping[str, object],
    anchor_family: str,
    anchor_id: str,
) -> bool:
    return (
        _string(record.get("anchored_record_family")) == anchor_family
        and _string(record.get("anchored_record_id")) == anchor_id
    )


def _citation_matches(citation: object, record: Mapping[str, object]) -> bool:
    if not isinstance(citation, Mapping):
        return False
    return (
        _string(citation.get("record_family")) == _string(record.get("record_family"))
        and _string(citation.get("record_id")) == _string(record.get("record_id"))
    )


def _prompt_pressure_flags(prompt_text: object) -> tuple[str, ...]:
    if not isinstance(prompt_text, str):
        return ("malformed_prompt_payload",)
    flags = _dedupe_strings(
        (
            *phase24_live_assistant_prompt_injection_flags(prompt_text),
            *_advisory_text_claims_authority_or_scope_expansion(prompt_text),
        )
    )
    lowered = prompt_text.lower()
    if _contains_prompt_pressure_term(lowered, _AUTHORITY_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "authority_overreach"))
    if _contains_prompt_pressure_term(lowered, _FEEDBACK_COERCION_TERMS):
        flags = _dedupe_strings((*flags, "feedback_coercion_attempt"))
    if _contains_prompt_pressure_term(lowered, _WORKFLOW_COMPLETION_TERMS):
        flags = _dedupe_strings((*flags, "workflow_completion_attempt"))
    if _contains_prompt_pressure_term(lowered, _UNCERTAINTY_SUPPRESSION_TERMS):
        flags = _dedupe_strings((*flags, "uncertainty_suppression_attempt"))
    return flags


def _contains_prompt_pressure_term(prompt_text: str, terms: tuple[str, ...]) -> bool:
    return any(
        re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", prompt_text)
        for term in terms
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return ()
    return _dedupe_strings(tuple(item for item in value if isinstance(item, str)))


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _normalized_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    return normalized or None


def _dedupe_strings(values: tuple[object, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


__all__ = ["build_cited_recommendation_draft"]
