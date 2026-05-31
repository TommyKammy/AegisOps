from __future__ import annotations

from collections.abc import Mapping

from .ai_grounding_validation import (
    _AGENT_NAME,
    _AUTHORITY_CEILING,
    _NEGATIVE_AUTHORITY,
    _REGISTRY_CITATIONS,
    _SUPPORTED_RECORD_FAMILIES,
    _TOOL_NAME,
    _dedupe_strings,
    _projection_citation_ids,
    _string,
)


def build_base_payload(
    *,
    anchor_id: str | None = None,
    projections: tuple[Mapping[str, object], ...] = (),
) -> dict[str, object]:
    citations = _dedupe_strings(
        (
            *_REGISTRY_CITATIONS,
            *(("case:" + anchor_id,) if anchor_id is not None else ()),
            *(
                citation
                for projection in projections
                for citation in _projection_citation_ids(projection, anchor_id)
            ),
        )
    )
    return {
        "read_only": True,
        "agent_name": _AGENT_NAME,
        "registered_tool_name": _TOOL_NAME,
        "record_families": _SUPPORTED_RECORD_FAMILIES,
        "authority_ceiling": _AUTHORITY_CEILING,
        "authority_boundary": "phase63_cited_evidence_grounding_only",
        "authoritative_workflow_truth": False,
        "mutates_authoritative_records": False,
        "approval_authority": False,
        "execution_authority": False,
        "reconciliation_authority": False,
        "case_closure_authority": False,
        "detector_activation_authority": False,
        "negative_authority": _NEGATIVE_AUTHORITY,
        "citations": citations,
    }


def build_blocked_payload(
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
        "non_ai_evidence_review_available": True,
        "grounding_items": (),
    }


def build_fallback_payload(
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
        "non_ai_evidence_review_available": True,
        "grounding_items": (),
    }


def build_grounded_payload(
    base: Mapping[str, object],
    *,
    anchor_id: str,
    projections: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        **base,
        "decision": "ground",
        "mode": "phase63_evidence_grounding",
        "unresolved_reasons": unresolved_reasons_for(projections),
        "uncertainty_flags": uncertainty_flags_for(projections),
        "ai_generation_allowed": True,
        "trace_creation_allowed": False,
        "non_ai_evidence_review_available": True,
        "grounding_items": tuple(
            build_grounding_item(projection, anchor_id) for projection in projections
        ),
    }


def build_grounding_item(
    projection: Mapping[str, object],
    anchor_id: str,
) -> dict[str, object]:
    uncertainty_label = (
        _string(projection.get("uncertainty_label"))
        or "missing_grounding_uncertainty"
    )
    return {
        "evidence_request_id": _string(projection.get("evidence_request_id")),
        "case_id": _string(projection.get("case_id")),
        "source_id": _string(projection.get("source_id")),
        "status": projection.get("status"),
        "freshness_state": projection.get("freshness_state"),
        "custody_state": projection.get("custody_state"),
        "provenance_state": projection.get("provenance_state"),
        "confidence_state": projection.get("confidence_state"),
        "conflict_state": projection.get("conflict_state"),
        "source_state": projection.get("source_state"),
        "uncertainty_label": uncertainty_label,
        "uncertainty_required": uncertainty_label != "related_entity_not_authoritative",
        "citation_ids": _projection_citation_ids(projection, anchor_id),
        "advisory_only": True,
        "counts_as_workflow_truth": False,
        "can_approve_action": False,
        "can_execute_action": False,
        "can_reconcile": False,
        "can_close_case": False,
        "can_activate_detector": False,
    }


def uncertainty_flags_for(
    projections: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    return _dedupe_strings(
        tuple(
            label
            for projection in projections
            if (label := _string(projection.get("uncertainty_label"))) is not None
        )
    )


def unresolved_reasons_for(
    projections: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for projection in projections:
        if projection.get("freshness_state") == "stale":
            reasons.append("stale_evidence")
        if projection.get("conflict_state") == "conflicting":
            reasons.append("conflicting_evidence")
        if (
            projection.get("status") == "unavailable"
            or projection.get("source_state") == "unavailable"
        ):
            reasons.append("unavailable_evidence_source")
        if projection.get("uncertainty_label") != "related_entity_not_authoritative":
            reasons.append("uncertainty_required")
    return _dedupe_strings(tuple(reasons))
