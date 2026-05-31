from __future__ import annotations

from typing import Mapping

from .action_policy_authority_scanning import (
    _AUTHORITY_PROMOTING_TERM_GROUPS,
    _FOLLOW_UP_COMPLETION_OR_READINESS_TERMS,
    contains_unnegated_single_term,
    contains_unnegated_term_group,
    promotes_non_authoritative_evidence,
    text_terms,
)
from .action_policy_catalog import (
    _MANUAL_FALLBACK_BLOCKED_REASON_CATEGORIES,
    PHASE62_MANUAL_FALLBACK_REQUIREMENTS,
)
from .action_policy_types import ManualFallbackValidationErrors


def _non_blank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def validate_phase62_manual_fallback_record(
    *,
    catalog_action: str,
    record: Mapping[str, object],
) -> ManualFallbackValidationErrors:
    """Return fail-closed Phase 62.5 errors for a candidate fallback record."""
    requirement = PHASE62_MANUAL_FALLBACK_REQUIREMENTS.get(catalog_action)
    if requirement is None:
        return ("unsupported_action",)

    errors: list[str] = []
    for field in requirement.required_record_fields:
        if not _non_blank_string(record.get(field)):
            errors.append(f"missing_{field}")

    affected_action = record.get("affected_action")
    if (
        _non_blank_string(affected_action)
        and affected_action != requirement.affected_action
    ):
        errors.append("affected_action_mismatch")

    fallback_state = record.get("fallback_state")
    if not _non_blank_string(fallback_state):
        errors.append("missing_fallback_state")
    elif fallback_state not in requirement.fallback_states:
        errors.append("unsupported_fallback_state")

    operator_note = str(record.get("operator_note") or "").lower()
    expected_evidence = str(record.get("expected_evidence") or "").lower()
    follow_up_state = str(record.get("follow_up_state") or "").lower()
    blocked_reason = str(record.get("blocked_reason") or "").lower()

    operator_note_terms = text_terms(operator_note)
    expected_evidence_terms = text_terms(expected_evidence)
    if contains_unnegated_term_group(
        operator_note_terms,
        _AUTHORITY_PROMOTING_TERM_GROUPS,
    ):
        errors.append("operator_note_promotes_authority")
    if contains_unnegated_term_group(
        expected_evidence_terms,
        _AUTHORITY_PROMOTING_TERM_GROUPS,
    ):
        errors.append("expected_evidence_promotes_authority")
    if promotes_non_authoritative_evidence(expected_evidence):
        errors.append("expected_evidence_promotes_non_authoritative_truth")
    follow_up_terms = text_terms(follow_up_state)
    if contains_unnegated_single_term(
        follow_up_terms,
        _FOLLOW_UP_COMPLETION_OR_READINESS_TERMS,
    ):
        errors.append("follow_up_state_promotes_completion")
    blocked_reason_terms = text_terms(blocked_reason)
    if contains_unnegated_term_group(
        blocked_reason_terms,
        (
            ("succeed",),
            ("succeeds",),
            ("succeeding",),
            ("success",),
            ("successful",),
            ("succeeded",),
        ),
    ):
        errors.append("blocked_reason_promotes_success")
    if (
        isinstance(fallback_state, str)
        and fallback_state in _MANUAL_FALLBACK_BLOCKED_REASON_CATEGORIES
        and _non_blank_string(record.get("blocked_reason"))
        and not _blocked_reason_matches_declared_failure_category(
            fallback_state=fallback_state,
            blocked_reason=blocked_reason,
        )
    ):
        errors.append("blocked_reason_missing_failure_category")

    return tuple(dict.fromkeys(errors))


def require_phase62_manual_fallback_record(
    *,
    catalog_action: str,
    record: Mapping[str, object],
) -> None:
    errors = validate_phase62_manual_fallback_record(
        catalog_action=catalog_action,
        record=record,
    )
    if errors:
        raise ValueError(
            "manual fallback violates Phase 62.5 contract: " + ", ".join(errors)
        )


def _blocked_reason_matches_declared_failure_category(
    *,
    fallback_state: str,
    blocked_reason: str,
) -> bool:
    terms = text_terms(blocked_reason)
    return any(
        contains_unnegated_term_group(
            terms,
            (category_terms,),
        )
        for category_terms in _MANUAL_FALLBACK_BLOCKED_REASON_CATEGORIES[
            fallback_state
        ]
    )
