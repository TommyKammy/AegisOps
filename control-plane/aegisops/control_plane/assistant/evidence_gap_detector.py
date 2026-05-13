from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .assistant_context import _advisory_text_claims_authority_or_scope_expansion
from .live_assistant_workflow import phase24_live_assistant_prompt_injection_flags

_AGENT_REGISTRY_REFERENCE = "docs/automation/ai-agent-registry.json"
_REGISTERED_AGENT_NAME = "evidence_gap_detector_agent"
_AGENT_NAME = _REGISTERED_AGENT_NAME
_TOOL_NAME = "evidence_gap_detector"
_AUTHORITY_CEILING = "advisory_only"
_CONTRACT_VERSION = "phase-60-4"
_REGISTRY_CITATIONS = (
    _AGENT_REGISTRY_REFERENCE,
    "docs/automation/ai-tool-registry.json",
    "docs/automation/ai-disabled-degraded-mode-contract.json",
)
_SUPPORTED_RECORD_FAMILIES = (
    "case",
    "alert",
    "evidence",
    "recommendation",
    "action_request",
    "approval_decision",
    "action_execution",
    "reconciliation",
    "source_health",
    "ai_trace",
)
_NEGATIVE_AUTHORITY = (
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "evidence_truth_creation",
    "conflict_resolution",
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
    "create evidence truth",
    "bypass policy",
    "bypass the policy",
)
_TRUTH_SELECTION_PRESSURE_TERMS = (
    "choose authoritative truth",
    "choose truth",
    "resolve conflict",
    "resolve conflicts",
    "mark source health current",
    "mark the source health current",
)
_GAP_RESOLUTION_PRESSURE_TERMS = (
    "mark evidence gaps resolved",
    "mark the evidence gaps resolved",
    "resolve evidence gap",
    "resolve evidence gaps",
)
_UNCERTAINTY_SUPPRESSION_TERMS = (
    "hide missing",
    "hide stale",
    "hide conflicts",
    "hide conflicting",
    "hide gaps",
    "hide citations",
    "suppress missing",
    "suppress stale",
    "suppress conflicts",
    "suppress uncertainty",
)


def build_evidence_gap_detector(
    *,
    evidence_review_payload: object,
    ai_enablement_posture: str = "enabled",
    prompt_text: object = "",
) -> dict[str, object]:
    base = _base_payload(anchor_id=_anchor_case_id(evidence_review_payload))
    prompt_flags = _prompt_pressure_flags(prompt_text)
    if prompt_flags:
        return _blocked_payload(base, prompt_flags)

    validation = _validated_review_payload(evidence_review_payload)
    if validation["reasons"]:
        return _fallback_payload(
            base,
            mode="evidence_gap_review_untrusted",
            unresolved_reasons=validation["reasons"],
        )

    records = validation["records"]
    base = _base_payload(
        anchor_id=validation["anchor_id"],
        records=records,
        gap_types=_detected_gap_types(records),
    )
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

    gap_items = _gap_items(records)
    unresolved_reasons = _dedupe_strings(
        tuple(gap["gap_type"] for gap in gap_items)
    )
    return {
        **base,
        "decision": "detect",
        "mode": "evidence_gap_detection",
        "unresolved_reasons": unresolved_reasons,
        "uncertainty_flags": unresolved_reasons,
        "ai_generation_allowed": True,
        "trace_creation_allowed": False,
        "non_ai_review_workflow_available": True,
        "gap_items": gap_items,
    }


def _base_payload(
    *,
    anchor_id: str | None = None,
    records: tuple[Mapping[str, object], ...] = (),
    gap_types: tuple[str, ...] = (),
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
            *(f"gap:{gap_type}" for gap_type in gap_types),
        )
    )
    return {
        "read_only": True,
        "agent_name": _AGENT_NAME,
        "registered_tool_name": _TOOL_NAME,
        "record_families": _SUPPORTED_RECORD_FAMILIES,
        "authority_ceiling": _AUTHORITY_CEILING,
        "authority_boundary": "cited_advisory_evidence_gap_detector_only",
        "authoritative_workflow_truth": False,
        "mutates_authoritative_records": False,
        "creates_evidence_truth": False,
        "advances_reconciliation": False,
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
        "non_ai_review_workflow_available": True,
        "gap_items": (),
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
        "non_ai_review_workflow_available": True,
        "gap_items": (),
    }


def _validated_review_payload(evidence_review_payload: object) -> dict[str, object]:
    if not isinstance(evidence_review_payload, Mapping):
        return _invalid(("malformed_evidence_review_payload",))
    if evidence_review_payload.get("contract_version") != _CONTRACT_VERSION:
        return _invalid(("unsupported_evidence_gap_contract_version",))
    anchor = evidence_review_payload.get("review_anchor")
    if not isinstance(anchor, Mapping):
        return _invalid(("missing_review_anchor",))
    if anchor.get("direct_binding_required") is not True:
        return _invalid(("review_anchor_without_direct_binding",))
    anchor_family = _string(anchor.get("record_family"))
    anchor_id = _string(anchor.get("record_id"))
    if anchor_family != "case" or anchor_id is None:
        return _invalid(("unsupported_review_anchor",))

    raw_records = evidence_review_payload.get("reviewed_records")
    if not isinstance(raw_records, Sequence) or isinstance(raw_records, (str, bytes)):
        return _invalid(("malformed_reviewed_records",))

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
        anchored_family = _string(raw_record.get("anchored_record_family"))
        anchored_id = _string(raw_record.get("anchored_record_id"))
        if anchored_family != record_family or anchored_id != record_id:
            reasons.append("mismatched_record_family")
        if _string(raw_record.get("created_by")) == "ai":
            reasons.append("ai_created_evidence_truth")
        citation = raw_record.get("citation")
        if citation is None and record_family != "recommendation":
            reasons.append("missing_reviewed_record_citation")
        elif citation is not None and not _citation_matches(citation, raw_record):
            reasons.append("mismatched_reviewed_record_citation")
        records.append(raw_record)

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
        "reasons": (),
    }


def _invalid(reasons: tuple[str, ...]) -> dict[str, object]:
    return {
        "anchor_id": None,
        "records": (),
        "reasons": reasons,
    }


def _anchor_case_id(evidence_review_payload: object) -> str | None:
    if not isinstance(evidence_review_payload, Mapping):
        return None
    anchor = evidence_review_payload.get("review_anchor")
    if not isinstance(anchor, Mapping):
        return None
    return _string(anchor.get("record_id")) if anchor.get("record_family") == "case" else None


def _gap_items(
    records: tuple[Mapping[str, object], ...],
) -> tuple[dict[str, object], ...]:
    return tuple(_gap_item(gap_type, records) for gap_type in _detected_gap_types(records))


def _detected_gap_types(
    records: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    gap_types: list[str] = []
    if any(
        _string(record.get("record_family")) == "case"
        and _string(record.get("identity_owner")) is None
        for record in records
    ):
        gap_types.append("missing_identity_owner")
    if any(
        _string(record.get("record_family")) == "source_health"
        and _string(record.get("source_health")) in {"stale", "outdated", "degraded"}
        for record in records
    ):
        gap_types.append("stale_source_health")
    if any(
        _string(record.get("record_family")) == "action_execution"
        and _string(record.get("receipt_id")) is not None
        and _string(record.get("reconciliation_id")) is None
        for record in records
    ):
        gap_types.append("receipt_without_reconciliation")
    if _has_evidence_conflict(records):
        gap_types.append("evidence_conflict")
    if any(record.get("citation") is None for record in records):
        gap_types.append("missing_citation")
    return _dedupe_strings(tuple(gap_types))


def _gap_item(
    gap_type: str,
    records: tuple[Mapping[str, object], ...],
) -> dict[str, object]:
    return {
        "gap_type": gap_type,
        "operator_posture": "review_needed",
        "suggested_safe_next_steps": _safe_next_steps(gap_type),
        "citation_ids": _dedupe_strings(
            (
                f"gap:{gap_type}",
                *_gap_record_citations(gap_type, records),
            )
        ),
        "advisory_only": True,
        "can_create_truth": False,
        "can_resolve_conflict": False,
        "can_advance_reconciliation": False,
    }


def _safe_next_steps(gap_type: str) -> tuple[str, ...]:
    return {
        "missing_identity_owner": (
            "Ask an operator to bind the reviewed identity owner before relying on identity context.",
        ),
        "stale_source_health": (
            "Ask an operator to refresh the source-health review before treating source posture as current.",
        ),
        "receipt_without_reconciliation": (
            "Route the receipt to reconciliation review without marking the execution matched.",
        ),
        "evidence_conflict": (
            "Escalate the conflicting reviewed evidence records for operator comparison.",
        ),
        "missing_citation": (
            "Require a reviewed citation before using the claim in advisory output.",
        ),
    }.get(gap_type, ("Route the unresolved evidence gap to operator review.",))


def _gap_record_citations(
    gap_type: str,
    records: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    citations: list[str] = []
    for record in records:
        record_family = _string(record.get("record_family"))
        if gap_type == "missing_identity_owner" and record_family != "case":
            continue
        if gap_type == "stale_source_health" and record_family != "source_health":
            continue
        if gap_type == "receipt_without_reconciliation" and record_family != "action_execution":
            continue
        if gap_type == "evidence_conflict" and record_family != "evidence":
            continue
        if gap_type == "missing_citation" and record.get("citation") is not None:
            continue
        citations.extend(_reviewed_record_citations(record))
    return _dedupe_strings(tuple(citations))


def _has_evidence_conflict(records: tuple[Mapping[str, object], ...]) -> bool:
    values_by_group: dict[str, set[str]] = {}
    for record in records:
        if _string(record.get("record_family")) != "evidence":
            continue
        conflict_group = _string(record.get("conflict_group"))
        reviewed_value = _string(record.get("reviewed_value"))
        if conflict_group is None or reviewed_value is None:
            continue
        values_by_group.setdefault(conflict_group, set()).add(reviewed_value)
    return any(len(values) > 1 for values in values_by_group.values())


def _reviewed_record_citations(record: Mapping[str, object]) -> tuple[str, ...]:
    citation = record.get("citation")
    record_family = _string(record.get("record_family"))
    record_id = _string(record.get("record_id"))
    if record_family is None or record_id is None:
        return ()
    if citation is None and record_family == "recommendation":
        return (f"{record_family}:{record_id}",)
    if not _citation_matches(citation, record):
        return ()
    return (f"{record_family}:{record_id}",)


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
    if _contains_prompt_pressure_term(lowered, _TRUTH_SELECTION_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "truth_selection_attempt"))
    if _contains_prompt_pressure_term(lowered, _GAP_RESOLUTION_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "evidence_gap_resolution_attempt"))
    if _contains_prompt_pressure_term(lowered, _UNCERTAINTY_SUPPRESSION_TERMS):
        flags = _dedupe_strings((*flags, "uncertainty_suppression_attempt"))
    return flags


def _contains_prompt_pressure_term(prompt_text: str, terms: tuple[str, ...]) -> bool:
    return any(
        re.search(rf"(?<![a-z0-9_]){re.escape(term)}(?![a-z0-9_])", prompt_text)
        for term in terms
    )


def _string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _dedupe_strings(values: tuple[object, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


__all__ = ["build_evidence_gap_detector"]
