from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .assistant_context import _advisory_text_claims_authority_or_scope_expansion
from .live_assistant_workflow import phase24_live_assistant_prompt_injection_flags

_AGENT_REGISTRY_REFERENCE = "docs/automation/ai-agent-registry.json"
_REGISTERED_AGENT_NAME = "runbook_guidance_agent"
_AGENT_NAME = _REGISTERED_AGENT_NAME
_TOOL_NAME = "runbook_guidance"
_AUTHORITY_CEILING = "advisory_only"
_CONTRACT_VERSION = "phase-60-5"
_REGISTRY_CITATIONS = (
    _AGENT_REGISTRY_REFERENCE,
    "docs/automation/ai-tool-registry.json",
    "docs/automation/ai-disabled-degraded-mode-contract.json",
)
_SUPPORTED_RECORD_FAMILIES = (
    "runbook",
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
_SUPPORTED_OPERATOR_POSTURES = (
    "suggested",
    "skipped",
    "completed",
    "blocked",
    "needs_review",
)
_NEGATIVE_AUTHORITY = (
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "runbook_completion",
    "workflow_progress",
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
_RUNBOOK_COMPLETION_PRESSURE_TERMS = (
    "mark runbook complete",
    "mark the runbook complete",
    "complete workflow",
    "complete the workflow",
    "mark workflow complete",
    "mark the workflow complete",
    "mark step complete",
    "mark the step complete",
)
_RUNBOOK_EXECUTION_PRESSURE_TERMS = (
    "execute runbook action",
    "execute the runbook action",
    "run runbook action",
    "perform runbook action",
)
_UNCERTAINTY_SUPPRESSION_TERMS = (
    "hide citations",
    "hide stale",
    "hide blocked",
    "hide needs review",
    "hide uncertainty",
    "suppress uncertainty",
    "suppress stale",
    "suppress blocked",
    "suppress needs review",
)


def build_runbook_guidance(
    *,
    runbook_context_payload: object,
    ai_enablement_posture: str = "enabled",
    prompt_text: object = "",
) -> dict[str, object]:
    base = _base_payload(anchor_id=_anchor_case_id(runbook_context_payload))
    prompt_flags = _prompt_pressure_flags(prompt_text)
    if prompt_flags:
        return _blocked_payload(base, prompt_flags)

    validation = _validated_runbook_payload(runbook_context_payload)
    if validation["reasons"]:
        return _fallback_payload(
            base,
            mode="runbook_guidance_untrusted",
            unresolved_reasons=validation["reasons"],
        )

    records = validation["records"]
    steps = validation["steps"]
    base = _base_payload(
        anchor_id=validation["anchor_id"],
        records=records,
        steps=steps,
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

    guidance_steps = tuple(_guidance_step(step) for step in steps)
    unresolved_reasons = _dedupe_strings(
        tuple(
            reason
            for step in guidance_steps
            for reason in _string_tuple(step.get("unresolved_reasons"))
        )
    )
    return {
        **base,
        "decision": "suggest",
        "mode": "runbook_guidance",
        "unresolved_reasons": unresolved_reasons,
        "uncertainty_flags": unresolved_reasons,
        "ai_generation_allowed": True,
        "trace_creation_allowed": False,
        "non_ai_runbook_workflow_available": True,
        "guidance_steps": guidance_steps,
    }


def _base_payload(
    *,
    anchor_id: str | None = None,
    records: tuple[Mapping[str, object], ...] = (),
    steps: tuple[Mapping[str, object], ...] = (),
) -> dict[str, object]:
    citations = _dedupe_strings(
        (
            *_REGISTRY_CITATIONS,
            "docs/runbook.md",
            "docs/phase-56-closeout-evaluation.md",
            "docs/phase-58-closeout-evaluation.md",
            "docs/phase-59-closeout-evaluation.md",
            *(("case:" + anchor_id,) if anchor_id is not None else ()),
            *(
                citation
                for record in records
                for citation in _reviewed_record_citations(record)
            ),
            *(
                citation
                for step in steps
                for citation in _runbook_step_citations(step)
            ),
        )
    )
    return {
        "read_only": True,
        "agent_name": _AGENT_NAME,
        "registered_tool_name": _TOOL_NAME,
        "record_families": _SUPPORTED_RECORD_FAMILIES,
        "authority_ceiling": _AUTHORITY_CEILING,
        "authority_boundary": "cited_advisory_runbook_guidance_only",
        "authoritative_workflow_truth": False,
        "mutates_authoritative_records": False,
        "ai_completion_owner": False,
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
        "non_ai_runbook_workflow_available": True,
        "guidance_steps": (),
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
        "non_ai_runbook_workflow_available": True,
        "guidance_steps": (),
    }


def _validated_runbook_payload(
    runbook_context_payload: object,
) -> dict[str, object]:
    if not isinstance(runbook_context_payload, Mapping):
        return _invalid(("malformed_runbook_context_payload",))
    if runbook_context_payload.get("contract_version") != _CONTRACT_VERSION:
        return _invalid(("unsupported_runbook_guidance_contract_version",))
    anchor = runbook_context_payload.get("review_anchor")
    if not isinstance(anchor, Mapping):
        return _invalid(("missing_review_anchor",))
    if anchor.get("direct_binding_required") is not True:
        return _invalid(("review_anchor_without_direct_binding",))
    anchor_family = _string(anchor.get("record_family"))
    anchor_id = _string(anchor.get("record_id"))
    if anchor_family != "case" or anchor_id is None:
        return _invalid(("unsupported_review_anchor",))

    raw_records = runbook_context_payload.get("reviewed_records")
    if not isinstance(raw_records, Sequence) or isinstance(raw_records, (str, bytes)):
        return _invalid(("malformed_reviewed_records",))

    raw_steps = runbook_context_payload.get("runbook_steps")
    if not isinstance(raw_steps, Sequence) or isinstance(raw_steps, (str, bytes)):
        return _invalid(("malformed_runbook_steps",))
    if not raw_steps:
        return _invalid(("missing_reviewed_runbook_steps",))

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
            reasons.append("ai_created_source_truth")
        if not _citation_matches(raw_record.get("citation"), raw_record):
            reasons.append("missing_reviewed_record_citation")
        records.append(raw_record)

    reviewed_record_citations = _reviewed_record_citation_set(
        tuple(records),
        anchor_family=anchor_family,
        anchor_id=anchor_id,
    )
    steps: list[Mapping[str, object]] = []
    for raw_step in raw_steps:
        if not isinstance(raw_step, Mapping):
            reasons.append("malformed_runbook_step")
            continue
        if _string(raw_step.get("step_id")) is None:
            reasons.append("missing_runbook_step_id")
        if _normalized_string(raw_step.get("title")) is None:
            reasons.append("missing_runbook_step_title")
        if _normalized_string(raw_step.get("reviewed_source")) != "docs/runbook.md":
            reasons.append("unreviewed_runbook_source")
        posture = _string(raw_step.get("operator_posture"))
        if posture not in _SUPPORTED_OPERATOR_POSTURES:
            reasons.append("unsupported_operator_posture")
        completion_owner = _normalized_string(raw_step.get("completion_owner"))
        if completion_owner != "operator":
            reasons.append("ai_owned_completion_truth")
        if posture == "completed" and completion_owner != "operator":
            reasons.append("ai_owned_completion_truth")
        reviewed_status = _normalized_string(raw_step.get("reviewed_status"))
        if reviewed_status not in {"current", "stale"}:
            reasons.append("unsupported_runbook_review_status")
        if not _runbook_step_citations(raw_step):
            reasons.append("missing_runbook_step_citation")
        linked_record_citations = _string_tuple(raw_step.get("linked_record_citations"))
        if not linked_record_citations:
            reasons.append("missing_linked_record_citation")
        elif not set(linked_record_citations).issubset(reviewed_record_citations):
            reasons.append("untrusted_linked_record_citation")
        blocked_by = _string_tuple(raw_step.get("blocked_by"))
        if posture == "blocked" and not blocked_by:
            reasons.append("missing_blocked_by_degraded_source")
        if blocked_by:
            if not set(blocked_by).issubset(reviewed_record_citations):
                reasons.append("untrusted_blocked_by_citation")
            if not all(
                _reviewed_degraded_source(
                    blocked,
                    tuple(records),
                    anchor_family=anchor_family,
                    anchor_id=anchor_id,
                )
                for blocked in blocked_by
            ):
                reasons.append("blocked_by_without_degraded_source")
        steps.append(raw_step)

    if not any(
        _string(record.get("record_family")) == "case"
        and _string(record.get("record_id")) == anchor_id
        for record in records
    ):
        reasons.append("missing_anchor_case_record")
    if not any(
        _string(record.get("record_family")) == "runbook"
        and _string(record.get("record_id")) == "docs/runbook.md"
        for record in records
    ):
        reasons.append("missing_reviewed_runbook_record")
    if reasons:
        return _invalid(_dedupe_strings(tuple(reasons)))
    return {
        "anchor_id": anchor_id,
        "records": tuple(records),
        "steps": tuple(steps),
        "reasons": (),
    }


def _invalid(reasons: tuple[str, ...]) -> dict[str, object]:
    return {
        "anchor_id": None,
        "records": (),
        "steps": (),
        "reasons": reasons,
    }


def _anchor_case_id(runbook_context_payload: object) -> str | None:
    if not isinstance(runbook_context_payload, Mapping):
        return None
    anchor = runbook_context_payload.get("review_anchor")
    if not isinstance(anchor, Mapping):
        return None
    return _string(anchor.get("record_id")) if anchor.get("record_family") == "case" else None


def _guidance_step(step: Mapping[str, object]) -> dict[str, object]:
    reviewed_status = _normalized_string(step.get("reviewed_status"))
    operator_posture = _string(step.get("operator_posture")) or "needs_review"
    unresolved_reasons: list[str] = []
    if reviewed_status == "stale":
        unresolved_reasons.append("stale_runbook_step")
        operator_posture = "needs_review"
    if _string_tuple(step.get("blocked_by")):
        unresolved_reasons.append("blocked_by_degraded_source")
        operator_posture = "blocked"
    return {
        "step_id": _string(step.get("step_id")),
        "title": _string(step.get("title")),
        "operator_posture": operator_posture,
        "completion_owner": "operator",
        "unresolved_reasons": _dedupe_strings(tuple(unresolved_reasons)),
        "citation_ids": _dedupe_strings(
            (
                *_runbook_step_citations(step),
                *_string_tuple(step.get("linked_record_citations")),
                *_string_tuple(step.get("blocked_by")),
            )
        ),
        "advisory_only": True,
        "counts_as_workflow_progress": False,
        "can_mark_complete": False,
        "can_execute": False,
    }


def _runbook_step_citations(step: Mapping[str, object]) -> tuple[str, ...]:
    citation = step.get("citation")
    if not isinstance(citation, Mapping):
        return ()
    citation_id = _string(citation.get("citation_id"))
    source_path = _string(citation.get("source_path"))
    if citation_id is None or source_path != "docs/runbook.md":
        return ()
    if not citation_id.startswith("docs/runbook.md#"):
        return ()
    return (citation_id,)


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


def _reviewed_degraded_source(
    citation_id: str,
    records: tuple[Mapping[str, object], ...],
    *,
    anchor_family: str,
    anchor_id: str,
) -> bool:
    for record in records:
        if not _record_bound_to_review_anchor(record, anchor_family, anchor_id):
            continue
        if citation_id not in _reviewed_record_citations(record):
            continue
        return (
            _string(record.get("record_family")) == "source_health"
            and _normalized_string(record.get("source_health")) == "degraded"
        )
    return False


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
    if _contains_prompt_pressure_term(lowered, _RUNBOOK_COMPLETION_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "runbook_completion_attempt"))
    if _contains_prompt_pressure_term(lowered, _RUNBOOK_EXECUTION_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "runbook_execution_attempt"))
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


__all__ = ["build_runbook_guidance"]
