from __future__ import annotations

import re

from ..models import ControlPlaneRecord, KnownLimitationOwnershipRecord
from .phase61_record_validators import (
    _has_linkage_value,
    _require_non_blank_fields,
    _require_non_empty_tuple,
    _validate_non_blank_sequence_entries,
)


_KNOWN_LIMITATION_REVIEW_STATES: frozenset[str] = frozenset(
    {
        "identified",
        "under_review",
        "accepted_risk",
        "mitigation_planned",
        "mitigation_in_progress",
        "closed",
    }
)
_KNOWN_LIMITATION_SEVERITIES: frozenset[str] = frozenset(
    {"low", "medium", "material", "high", "blocking"}
)
_KNOWN_LIMITATION_HANDOFF_POSTURES: frozenset[str] = frozenset(
    {
        "not_ready_for_handoff",
        "handoff_required",
        "handoff_ready_as_subordinate_evidence",
        "blocked_until_mitigated",
    }
)
_KNOWN_LIMITATION_AUTHORITY_BOUNDARY = "reviewed_evidence_input_only"
_FORBIDDEN_READINESS_CLAIM_PATTERN = re.compile(
    r"\b("
    r"rc\s+ready|rc\s+readiness|ga\s+ready|ga\s+readiness|"
    r"beta\s+ready|beta\s+readiness|commercial\s+replacement|"
    r"self-service\s+commercial|readiness\s+truth|release\s+truth|"
    r"verifier\s+output\s+is\s+readiness\s+truth|"
    r"issue-lint\s+output\s+is\s+readiness\s+truth"
    r")\b",
    re.IGNORECASE,
)


def is_phase64_record_family(record: ControlPlaneRecord) -> bool:
    return isinstance(record, KnownLimitationOwnershipRecord)


def validate_phase64_record(record: ControlPlaneRecord) -> bool:
    if isinstance(record, KnownLimitationOwnershipRecord):
        _validate_known_limitation_ownership_record(record)
        return True
    return False


def _validate_known_limitation_ownership_record(
    record: KnownLimitationOwnershipRecord,
) -> None:
    _require_non_blank_fields(
        record,
        (
            "limitation_id",
            "title",
            "severity",
            "affected_surface",
            "owner",
            "mitigation",
            "review_state",
            "accepted_risk_posture",
            "phase66_handoff_posture",
            "authority_boundary",
        ),
    )
    _require_non_empty_tuple(record, "evidence_references")
    _validate_non_blank_sequence_entries(
        record,
        record.evidence_references,
        "evidence_references",
    )
    if record.severity not in _KNOWN_LIMITATION_SEVERITIES:
        raise ValueError(
            "known_limitation_ownership record "
            f"{record.record_id!r} has unsupported severity {record.severity!r}; "
            f"expected one of {sorted(_KNOWN_LIMITATION_SEVERITIES)!r}"
        )
    if record.review_state not in _KNOWN_LIMITATION_REVIEW_STATES:
        raise ValueError(
            "known_limitation_ownership record "
            f"{record.record_id!r} has unsupported review_state {record.review_state!r}; "
            f"expected one of {sorted(_KNOWN_LIMITATION_REVIEW_STATES)!r}"
        )
    if not (
        _has_linkage_value(record.review_cadence)
        or _has_linkage_value(record.due_date)
    ):
        raise ValueError(
            "known_limitation_ownership record "
            f"{record.record_id!r} requires review_cadence or due_date"
        )
    if record.phase66_handoff_posture not in _KNOWN_LIMITATION_HANDOFF_POSTURES:
        raise ValueError(
            "known_limitation_ownership record "
            f"{record.record_id!r} has unsupported phase66_handoff_posture "
            f"{record.phase66_handoff_posture!r}; expected one of "
            f"{sorted(_KNOWN_LIMITATION_HANDOFF_POSTURES)!r}"
        )
    if record.authority_boundary != _KNOWN_LIMITATION_AUTHORITY_BOUNDARY:
        raise ValueError(
            "known_limitation_ownership record "
            f"{record.record_id!r} requires authority_boundary "
            f"{_KNOWN_LIMITATION_AUTHORITY_BOUNDARY!r}"
        )
    if _contains_forbidden_readiness_claim(record.readiness_claim):
        raise ValueError(
            "known_limitation_ownership record "
            f"{record.record_id!r} cannot include readiness or release claims"
        )
    for field_name in (
        "title",
        "mitigation",
        "accepted_risk_posture",
        "phase66_handoff_posture",
    ):
        value = getattr(record, field_name)
        if _contains_forbidden_readiness_claim(value):
            raise ValueError(
                "known_limitation_ownership record "
                f"{record.record_id!r} cannot include readiness or release claims "
                f"in {field_name}"
            )


def _contains_forbidden_readiness_claim(value: object) -> bool:
    return isinstance(value, str) and bool(_FORBIDDEN_READINESS_CLAIM_PATTERN.search(value))


__all__ = [
    "is_phase64_record_family",
    "validate_phase64_record",
]
