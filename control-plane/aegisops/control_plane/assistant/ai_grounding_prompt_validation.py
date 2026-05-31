from __future__ import annotations

import re

from .assistant_context import _advisory_text_claims_authority_or_scope_expansion
from .live_assistant_workflow import phase24_live_assistant_prompt_injection_flags
from ..evidence.bounded_enrichment_adapter import _scan_for_endpoint_command_language

_AUTHORITY_PRESSURE_TERMS = (
    "treat evidence as case truth",
    "evidence as case truth",
    "evidence as workflow truth",
    "evidence is authoritative",
    "promote evidence to truth",
    "approve action",
    "approve the action",
    "execute the action",
    "reconcile the receipt",
    "close case",
    "close the case",
    "activate detectors",
    "activate detector",
    "create source truth",
    "create evidence truth",
    "resolve conflict",
    "resolve this conflict",
    "conflict resolution",
    "advance workflow",
    "advance the workflow",
    "workflow progress",
    "write to production",
    "production write",
    "bypass policy",
    "policy bypass",
    "quarantine host",
    "delete file",
    "remediate endpoint",
    "contain host",
    "kill process",
    "mutate protected target",
)
_READINESS_PRESSURE_TERMS = (
    "mark this release ready",
    "mark release ready",
    "release ready",
    "release truth",
    "readiness truth",
    "workflow truth",
    "mark this gate ready",
    "mark gate ready",
    "gate release",
    "gate this release",
    "gate ready",
    "gate is ready",
    "gate truth",
    "closeout truth",
    "production truth",
)
_PROMPT_DETERMINER_PATTERN = r"(?:a|all|an|any|the|this|that|these|those)\s+"
_PROMPT_OBJECT_MODIFIER_PATTERN = r"(?:[\w-]+\s+){0,3}"
_AUTHORITY_PRESSURE_PATTERNS = (
    rf"promote\s+(?:{_PROMPT_DETERMINER_PATTERN})?evidence\s+to\s+truth",
    rf"approve\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}actions?",
    rf"execute\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}actions?",
    rf"reconcile\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}receipts?",
    rf"close\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}cases?",
    rf"activate\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}detectors?",
    rf"create\s+(?:{_PROMPT_DETERMINER_PATTERN})?source\s+truth",
    rf"create\s+(?:{_PROMPT_DETERMINER_PATTERN})?evidence\s+truth",
    rf"resolve\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}conflicts?",
    rf"advance\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}workflows?",
    r"write\s+to\s+production",
    rf"bypass\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}polic(?:y|ies)",
)
_READINESS_PRESSURE_PATTERNS = (
    rf"mark\s+(?:{_PROMPT_DETERMINER_PATTERN})?gates?\s+ready",
    rf"mark\s+(?:{_PROMPT_DETERMINER_PATTERN})?releases?\s+ready",
    rf"gate\s+(?:{_PROMPT_DETERMINER_PATTERN})?{_PROMPT_OBJECT_MODIFIER_PATTERN}releases?",
    rf"create\s+(?:{_PROMPT_DETERMINER_PATTERN})?release\s+truth",
    rf"create\s+(?:{_PROMPT_DETERMINER_PATTERN})?workflow\s+truth",
    r"gate\s+is\s+ready",
    r"release\s+is\s+ready",
)
_UNCERTAINTY_SUPPRESSION_TERMS = (
    "hide citations",
    "hide citation",
    "suppress citations",
    "suppress citation",
    "hide uncertainty",
    "hide uncertainties",
    "suppress uncertainty",
    "hide stale",
    "suppress stale",
    "hide conflicts",
    "hide conflicting",
    "suppress conflicts",
)


def prompt_pressure_flags(prompt_text: object) -> tuple[str, ...]:
    flags = list(_advisory_text_claims_authority_or_scope_expansion(prompt_text))
    flags.extend(phase24_live_assistant_prompt_injection_flags(prompt_text))
    if not isinstance(prompt_text, str):
        flags.append("malformed_prompt_payload")
        return _dedupe_strings(tuple(flags))
    if _contains_any_term(prompt_text, _UNCERTAINTY_SUPPRESSION_TERMS):
        flags.append("citation_suppression_attempt")
    if (
        _contains_any_term(prompt_text, _AUTHORITY_PRESSURE_TERMS)
        or _contains_any_pattern(prompt_text, _AUTHORITY_PRESSURE_PATTERNS)
        or _scan_for_endpoint_command_language(prompt_text)
    ):
        flags.append("authority_overreach")
    if _contains_any_term(prompt_text, _READINESS_PRESSURE_TERMS) or (
        _contains_any_pattern(prompt_text, _READINESS_PRESSURE_PATTERNS)
    ):
        flags.append("readiness_truth_attempt")
    return _dedupe_strings(tuple(flags))


def _contains_any_term(text: str, terms: tuple[str, ...]) -> bool:
    normalized = re.sub(r"[\W_]+", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    for term in terms:
        normalized_term = re.sub(r"[\W_]+", " ", term.lower()).strip()
        pattern = rf"(?<!\w){re.escape(normalized_term)}(?!\w)"
        if re.search(pattern, normalized) is not None:
            return True
    return False


def _contains_any_pattern(text: str, patterns: tuple[str, ...]) -> bool:
    normalized = re.sub(r"[\W_]+", " ", text.lower())
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return any(
        re.search(rf"(?<!\w){pattern}(?!\w)", normalized) is not None
        for pattern in patterns
    )


def _dedupe_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value not in deduped:
            deduped.append(value)
    return tuple(deduped)
