from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .assistant_context import _advisory_text_claims_authority_or_scope_expansion
from .live_assistant_workflow import phase24_live_assistant_prompt_injection_flags

_AGENT_REGISTRY_REFERENCE = "docs/automation/ai-agent-registry.json"
_REGISTERED_AGENT_NAME = "case_timeline_summary_agent"
_AGENT_NAME = _REGISTERED_AGENT_NAME
_TOOL_NAME = "case_timeline_summary"
_AUTHORITY_CEILING = "advisory_only"
_CONTRACT_VERSION = "phase-56-3"
_REGISTRY_CITATIONS = (
    _AGENT_REGISTRY_REFERENCE,
    "docs/automation/ai-tool-registry.json",
    "docs/automation/ai-disabled-degraded-mode-contract.json",
)
_SEGMENT_ORDER = (
    "wazuh_signal",
    "aegisops_alert",
    "evidence",
    "ai_summary",
    "recommendation",
    "action_request",
    "approval",
    "shuffle_receipt",
    "reconciliation",
)
_SUPPORTED_STATES = (
    "normal",
    "missing",
    "degraded",
    "stale",
    "mismatch",
    "unsupported",
)
_SUPPORTED_AUTHORITY_POSTURES = (
    "authoritative_aegisops_record",
    "subordinate_context",
)
_NEGATIVE_AUTHORITY = (
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "timeline_completion",
    "workflow_truth",
)
_AUTHORITY_PRESSURE_TERMS = (
    "approve action",
    "approve the action",
    "approve it",
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
_TIMELINE_COMPLETION_PRESSURE_TERMS = (
    "complete timeline",
    "complete the timeline",
    "mark timeline complete",
    "mark the timeline complete",
    "resolve timeline",
    "resolve the timeline",
)
_UNCERTAINTY_SUPPRESSION_TERMS = (
    "hide missing",
    "hide stale",
    "hide degraded",
    "hide conflicts",
    "hide conflicting",
    "hide gaps",
    "suppress missing",
    "suppress stale",
    "suppress degraded",
    "suppress conflicts",
    "suppress uncertainty",
)
_UNCERTAINTY_BY_STATE = {
    "missing": "missing_timeline_segment",
    "degraded": "degraded_timeline_segment",
    "stale": "stale_timeline_segment",
    "mismatch": "conflicting_timeline_segment",
    "unsupported": "unsupported_timeline_segment",
}


def build_case_timeline_summary(
    *,
    case_detail_payload: object,
    ai_enablement_posture: str = "enabled",
    prompt_text: object = "",
) -> dict[str, object]:
    base = _base_payload()
    prompt_flags = _prompt_pressure_flags(prompt_text)
    if prompt_flags:
        return _blocked_payload(base, prompt_flags)

    validation = _validated_timeline(case_detail_payload)
    if validation["reasons"]:
        return _fallback_payload(
            base,
            mode="timeline_evidence_missing",
            unresolved_reasons=validation["reasons"],
        )

    base = _base_payload(
        case_id=validation["case_id"],
        segments=validation["segments"],
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

    summary_segments = tuple(
        _summary_segment(segment) for segment in validation["segments"]
    )
    uncertainty_flags = _summary_uncertainty_flags(summary_segments)
    return {
        **base,
        "decision": "summarize",
        "mode": "case_timeline_summary",
        "unresolved_reasons": uncertainty_flags,
        "uncertainty_flags": uncertainty_flags,
        "ai_generation_allowed": True,
        "trace_creation_allowed": False,
        "non_ai_case_workflow_available": True,
        "summary_segments": summary_segments,
    }


def _base_payload(
    *,
    case_id: str | None = None,
    segments: tuple[Mapping[str, object], ...] = (),
) -> dict[str, object]:
    citations = _dedupe_strings(
        (
            *_REGISTRY_CITATIONS,
            "docs/phase-56-closeout-evaluation.md",
            "docs/phase-59-closeout-evaluation.md",
            *(("case:" + case_id,) if case_id is not None else ()),
            *(
                citation
                for segment in segments
                for citation in _segment_citations(segment)
            ),
        )
    )
    return {
        "read_only": True,
        "agent_name": _AGENT_NAME,
        "registered_tool_name": _TOOL_NAME,
        "record_families": (
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
        ),
        "authority_ceiling": _AUTHORITY_CEILING,
        "authority_boundary": "cited_advisory_case_timeline_summary_only",
        "authoritative_workflow_truth": False,
        "mutates_authoritative_records": False,
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
        "non_ai_case_workflow_available": True,
        "summary_segments": (),
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
        "non_ai_case_workflow_available": True,
        "summary_segments": (),
    }


def _validated_timeline(case_detail_payload: object) -> dict[str, object]:
    if not isinstance(case_detail_payload, Mapping):
        return _invalid(("malformed_case_detail_payload",))
    case_id = _string(case_detail_payload.get("case_id"))
    projection = case_detail_payload.get("case_timeline_projection")
    if case_id is None or not isinstance(projection, Mapping):
        return _invalid(("missing_reviewed_case_timeline_projection",))
    projection_case_id = _string(projection.get("case_id"))
    contract_version = _string(projection.get("contract_version"))
    if projection_case_id != case_id:
        return _invalid(("timeline_case_id_mismatch",))
    if contract_version != _CONTRACT_VERSION:
        return _invalid(("unsupported_timeline_contract_version",))
    projection_source = _string(projection.get("projection_source"))
    if (
        projection.get("projection_authority_allowed") is not False
        or projection.get("inferred_linkage_allowed") is not False
    ):
        return _invalid(("timeline_projection_authority_untrusted",))
    if (
        (projection.get("cache_sourced") is not None and projection.get("cache_sourced") is not False)
        or (projection.get("stale_cache") is not None and projection.get("stale_cache") is not False)
        or projection_source in {"browser_cache", "ui_cache", "cache"}
    ):
        return _invalid(("cache_sourced_timeline_truth",))
    raw_segments = projection.get("segments")
    if not isinstance(raw_segments, Sequence) or isinstance(raw_segments, (str, bytes)):
        return _invalid(("malformed_timeline_segments",))
    if len(raw_segments) != len(_SEGMENT_ORDER):
        return _invalid(("incomplete_timeline_segments",))

    reasons: list[str] = []
    segments: list[Mapping[str, object]] = []
    for index, raw_segment in enumerate(raw_segments):
        if not isinstance(raw_segment, Mapping):
            reasons.append("malformed_timeline_segment")
            continue
        segment_name = _string(raw_segment.get("segment"))
        state = _string(raw_segment.get("state"))
        authority_posture = _string(raw_segment.get("authority_posture"))
        binding = raw_segment.get("backend_record_binding")
        if segment_name != _SEGMENT_ORDER[index]:
            reasons.append("unsupported_timeline_segment_order")
        if state not in _SUPPORTED_STATES:
            reasons.append("unsupported_timeline_segment_state")
        if authority_posture not in _SUPPORTED_AUTHORITY_POSTURES:
            reasons.append("unsupported_timeline_authority_posture")
        if not isinstance(binding, Mapping):
            reasons.append("missing_timeline_backend_binding")
            continue
        record_family = _string(binding.get("record_family"))
        record_id = _string(binding.get("record_id"))
        incomplete_reason = _string(raw_segment.get("incomplete_reason"))
        if binding.get("direct_binding_required") is not True:
            reasons.append("timeline_segment_without_direct_binding")
        if raw_segment.get("operator_visible") is not True:
            reasons.append("timeline_segment_not_operator_visible")
        if raw_segment.get("projection_can_complete_segment") is not False:
            reasons.append("timeline_projection_completion_untrusted")
        if record_family is None:
            reasons.append("missing_timeline_record_family")
        if record_id is None and incomplete_reason is None:
            reasons.append("uncited_timeline_segment")
        segments.append(raw_segment)
    if reasons:
        return _invalid(_dedupe_strings(tuple(reasons)))
    return {
        "case_id": case_id,
        "segments": tuple(segments),
        "reasons": (),
    }


def _invalid(reasons: tuple[str, ...]) -> dict[str, object]:
    return {
        "case_id": None,
        "segments": (),
        "reasons": reasons,
    }


def _summary_segment(segment: Mapping[str, object]) -> dict[str, object]:
    segment_name = _string(segment.get("segment"))
    state = _string(segment.get("state"))
    authority_posture = _string(segment.get("authority_posture"))
    return {
        "segment": segment_name,
        "state": state,
        "authority_label": authority_posture,
        "summary": _segment_summary(segment_name, state, authority_posture),
        "citation_ids": _segment_citations(segment),
        "uncertainty_flags": _segment_uncertainty_flags(segment),
        "advisory_only": True,
        "can_complete_workflow": False,
    }


def _segment_summary(
    segment_name: str | None,
    state: str | None,
    authority_posture: str | None,
) -> str:
    label = segment_name or "unknown"
    posture = authority_posture or "unknown_authority"
    segment_state = state or "unknown"
    return (
        f"{label} is {segment_state} as {posture}; "
        "review authoritative records before changing workflow state."
    )


def _segment_citations(segment: Mapping[str, object]) -> tuple[str, ...]:
    binding = segment.get("backend_record_binding")
    if not isinstance(binding, Mapping):
        return ()
    record_family = _string(binding.get("record_family"))
    record_id = _string(binding.get("record_id"))
    segment_name = _string(segment.get("segment"))
    citations: list[str] = []
    if record_family is not None and record_id is not None:
        citations.append(f"{record_family}:{record_id}")
    if record_id is None and segment_name is not None:
        citations.append(f"timeline_gap:{segment_name}")
    return _dedupe_strings(tuple(citations))


def _summary_uncertainty_flags(
    summary_segments: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    return _dedupe_strings(
        tuple(
            flag
            for item in summary_segments
            for flag in _string_tuple(item.get("uncertainty_flags"))
        )
    )


def _segment_uncertainty_flags(
    segment: Mapping[str, object],
) -> tuple[str, ...]:
    state = _string(segment.get("state"))
    flags: list[str] = []
    if state in _UNCERTAINTY_BY_STATE:
        flags.append(_UNCERTAINTY_BY_STATE[state])
    if not _segment_citations(segment):
        flags.append("uncited_timeline_segment")
    return _dedupe_strings(tuple(flags))


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
    if _contains_prompt_pressure_term(lowered, _TIMELINE_COMPLETION_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "timeline_completion_attempt"))
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


def _string_tuple(value: object) -> tuple[str, ...]:
    if isinstance(value, str):
        return (value,) if value else ()
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _dedupe_strings(values: tuple[object, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


__all__ = ["build_case_timeline_summary"]
