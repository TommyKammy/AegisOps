from __future__ import annotations

from typing import Mapping

from ..models import KnownLimitationOwnershipRecord
from ..record_validation import _validate_record


_ALLOWED_CONSUMERS = frozenset({"inspection", "service_snapshot"})
_NO_WORKFLOW_AUTHORITY = "none"
_SUBORDINATE_AUTHORITY_POSTURE = "subordinate_limitation_context_only"


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _readonly_strings(record: KnownLimitationOwnershipRecord) -> dict[str, str]:
    return {
        "limitation_id": record.limitation_id,
        "title": record.title,
        "severity": record.severity,
        "affected_surface": record.affected_surface,
        "owner": record.owner,
        "mitigation": record.mitigation,
        "review_state": record.review_state,
        "accepted_risk_posture": record.accepted_risk_posture,
        "phase66_handoff_posture": record.phase66_handoff_posture,
        "authority_boundary": record.authority_boundary,
    }


def project_limitation_ownership_context(
    record: KnownLimitationOwnershipRecord,
    *,
    consumer: str,
    requested_authority: str = _NO_WORKFLOW_AUTHORITY,
) -> Mapping[str, object]:
    if not isinstance(record, KnownLimitationOwnershipRecord):
        raise TypeError("record must be a known_limitation_ownership record")
    normalized_consumer = _require_non_empty_string(consumer, "consumer")
    if normalized_consumer not in _ALLOWED_CONSUMERS:
        raise ValueError(
            "known limitation ownership projection has unsupported consumer "
            f"{normalized_consumer!r}"
        )
    if requested_authority != _NO_WORKFLOW_AUTHORITY:
        raise ValueError(
            "known limitation ownership projection cannot provide workflow authority"
        )

    _validate_record(record)

    return {
        **_readonly_strings(record),
        "consumer": normalized_consumer,
        "evidence_references": record.evidence_references,
        "review_cadence": record.review_cadence,
        "due_date": record.due_date,
        "authority_posture": _SUBORDINATE_AUTHORITY_POSTURE,
        "readiness_truth": False,
        "release_truth": False,
        "gate_truth": False,
        "workflow_truth": False,
        "workflow_authority": _NO_WORKFLOW_AUTHORITY,
    }


__all__ = ["project_limitation_ownership_context"]
