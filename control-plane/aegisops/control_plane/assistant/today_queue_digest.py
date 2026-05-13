from __future__ import annotations

from collections.abc import Mapping, Sequence
import re

from .assistant_context import _advisory_text_claims_authority_or_scope_expansion
from .live_assistant_workflow import phase24_live_assistant_prompt_injection_flags

_AGENT_REGISTRY_REFERENCE = "docs/automation/ai-agent-registry.json"
_REGISTERED_AGENT_NAME = "today_queue_digest_agent"
_AGENT_NAME = _REGISTERED_AGENT_NAME
_TOOL_NAME = "today_queue_digest"
_AUTHORITY_CEILING = "advisory_only"
_REGISTRY_CITATIONS = (
    _AGENT_REGISTRY_REFERENCE,
    "docs/automation/ai-tool-registry.json",
    "docs/automation/ai-disabled-degraded-mode-contract.json",
)
_NEGATIVE_AUTHORITY = (
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "queue_priority_mutation",
    "task_completion",
    "workflow_truth",
)
_QUEUE_MUTATION_PRESSURE_TERMS = (
    "change queue priority",
    "change priority",
    "mark task complete",
    "mark tasks complete",
    "complete the task",
    "complete tasks",
)
_UNCERTAINTY_SUPPRESSION_TERMS = (
    "suppress stale",
    "suppress degraded",
    "suppress stale degraded",
    "hide stale",
    "hide degraded",
    "hide gaps",
    "hide missing evidence",
    "suppress uncertainty",
)
_AUTHORITY_PRESSURE_TERMS = (
    "approve it",
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


def build_today_queue_digest(
    *,
    queue_payload: object,
    ai_enablement_posture: str = "enabled",
    prompt_text: object = "",
) -> dict[str, object]:
    base = _base_payload()
    prompt_flags = _prompt_pressure_flags(prompt_text)
    if prompt_flags:
        return _blocked_payload(base, prompt_flags)

    queue_reasons = _queue_payload_unresolved_reasons(queue_payload)
    if queue_reasons:
        return _fallback_payload(
            base,
            mode="queue_evidence_missing",
            unresolved_reasons=queue_reasons,
        )

    base = _base_payload(queue_payload)
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

    records = _queue_records(queue_payload)
    digest_items = tuple(_digest_item(record) for record in records)
    return {
        **base,
        "decision": "digest",
        "mode": "today_queue_digest",
        "unresolved_reasons": _digest_unresolved_reasons(digest_items),
        "ai_generation_allowed": True,
        "trace_creation_allowed": False,
        "non_ai_today_workflow_available": True,
        "digest_items": digest_items,
    }


def _base_payload(queue_payload: object | None = None) -> dict[str, object]:
    citations = _dedupe_strings(
        (
            *_REGISTRY_CITATIONS,
            "docs/deployment/today-view-backend-projection-contract.md",
            "docs/phase-56-closeout-evaluation.md",
            "docs/phase-59-closeout-evaluation.md",
            "queue:analyst_review",
            *(
                _queue_record_citations(queue_payload)
                if queue_payload is not None
                else ()
            ),
        )
    )
    return {
        "read_only": True,
        "agent_name": _AGENT_NAME,
        "registered_tool_name": _TOOL_NAME,
        "record_families": (
            "alert",
            "case",
            "evidence",
            "action_review",
            "reconciliation",
            "source_health",
            "handoff",
            "ai_trace",
        ),
        "authority_ceiling": _AUTHORITY_CEILING,
        "authority_boundary": "cited_advisory_today_queue_digest_only",
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
        "ai_generation_allowed": False,
        "trace_creation_allowed": False,
        "non_ai_today_workflow_available": True,
        "digest_items": (),
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
        "ai_generation_allowed": False,
        "trace_creation_allowed": False,
        "non_ai_today_workflow_available": True,
        "digest_items": (),
    }


def _queue_payload_unresolved_reasons(queue_payload: object) -> tuple[str, ...]:
    if not isinstance(queue_payload, Mapping):
        return ("malformed_queue_payload",)
    if queue_payload.get("read_only") is not True:
        return ("queue_payload_not_reviewed_read_only",)
    if queue_payload.get("queue_name") != "analyst_review":
        return ("untrusted_queue_name",)
    raw_records = queue_payload.get("records")
    if not isinstance(raw_records, Sequence) or isinstance(raw_records, (str, bytes)):
        return ("malformed_queue_records",)

    reasons: list[str] = []
    for record in raw_records:
        if not isinstance(record, Mapping):
            reasons.append("malformed_queue_record")
            continue
        alert_id = _string(record.get("alert_id"))
        reviewed_context = record.get("reviewed_context")
        if alert_id is None or not isinstance(reviewed_context, Mapping):
            reasons.append("missing_reviewed_queue_citation")
    return _dedupe_strings(tuple(reasons))


def _queue_records(queue_payload: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(queue_payload, Mapping):
        return ()
    raw_records = queue_payload.get("records")
    if not isinstance(raw_records, Sequence) or isinstance(raw_records, (str, bytes)):
        return ()
    return tuple(record for record in raw_records if isinstance(record, Mapping))


def _digest_item(record: Mapping[str, object]) -> dict[str, object]:
    alert_id = _string(record.get("alert_id"))
    case_id = _string(record.get("case_id"))
    evidence_ids = _string_tuple(record.get("evidence_ids"))
    queue_lanes = _string_tuple(record.get("queue_lanes"))
    citation_ids = _queue_record_citations({"records": (record,)})
    unresolved = _record_unresolved_reasons(record)
    return {
        "alert_id": alert_id,
        "case_id": case_id,
        "review_state": _string(record.get("review_state")),
        "severity": _string(record.get("severity")),
        "owner": _string(record.get("owner")),
        "next_action": _string(record.get("next_action")),
        "queue_lanes": queue_lanes,
        "evidence_posture": "present" if evidence_ids else "missing",
        "unresolved_reasons": unresolved,
        "citation_ids": citation_ids,
        "advisory_only": True,
    }


def _digest_unresolved_reasons(
    digest_items: tuple[Mapping[str, object], ...],
) -> tuple[str, ...]:
    reasons: list[str] = []
    for item in digest_items:
        reasons.extend(_string_tuple(item.get("unresolved_reasons")))
    return _dedupe_strings(tuple(reasons))


def _record_unresolved_reasons(record: Mapping[str, object]) -> tuple[str, ...]:
    reasons: list[str] = []
    lanes = set(_string_tuple(record.get("queue_lanes")))
    if not _string_tuple(record.get("evidence_ids")):
        reasons.append("missing_evidence")
    if "stale_receipt" in lanes:
        reasons.append("stale_work")
    if _record_has_degraded_source(record):
        reasons.append("degraded_source")
    if "reconciliation_mismatch" in lanes:
        reasons.append("reconciliation_mismatch")
    return _dedupe_strings(tuple(reasons))


def _queue_record_citations(queue_payload: object) -> tuple[str, ...]:
    citations: list[str] = []
    for record in _queue_records(queue_payload):
        alert_id = _string(record.get("alert_id"))
        case_id = _string(record.get("case_id"))
        correlation_key = _string(record.get("correlation_key"))
        if alert_id is not None:
            citations.append(f"alert:{alert_id}")
            if _record_has_handoff_context(record):
                citations.append(f"handoff:{alert_id}")
        if case_id is not None:
            citations.append(f"case:{case_id}")
        for evidence_id in _string_tuple(record.get("evidence_ids")):
            citations.append(f"evidence:{evidence_id}")
        if alert_id is not None and not _string_tuple(record.get("evidence_ids")):
            citations.append(f"missing_evidence:{alert_id}")
        for source_system in _degraded_extension_sources(record):
            citations.append(f"source_health:{source_system}")
        if correlation_key is not None:
            citations.append(f"reconciliation:{correlation_key}")
        current_action_review = record.get("current_action_review")
        if isinstance(current_action_review, Mapping):
            review_id = _string(
                current_action_review.get("review_id")
                or current_action_review.get("action_request_id")
            )
            if review_id is not None:
                citations.append(f"action_review:{review_id}")
    return _dedupe_strings(tuple(citations))


def _record_has_degraded_source(record: Mapping[str, object]) -> bool:
    if "optional_extension_degraded" in _string_tuple(record.get("queue_lanes")):
        return True
    return bool(_degraded_extension_sources(record))


def _degraded_extension_sources(record: Mapping[str, object]) -> tuple[str, ...]:
    details = record.get("queue_lane_details")
    if not isinstance(details, Mapping):
        return ()
    degraded_details = details.get("optional_extension_degraded")
    if not isinstance(degraded_details, Mapping):
        return ()
    return _dedupe_strings(
        tuple(source for source in degraded_details if isinstance(source, str))
    )


def _record_has_handoff_context(record: Mapping[str, object]) -> bool:
    reviewed_context = record.get("reviewed_context")
    if not isinstance(reviewed_context, Mapping):
        return False
    return isinstance(reviewed_context.get("handoff"), Mapping)


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
    if _contains_prompt_pressure_term(lowered, _QUEUE_MUTATION_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "queue_priority_mutation_attempt"))
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


__all__ = ["build_today_queue_digest"]
