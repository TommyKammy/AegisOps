from __future__ import annotations

from dataclasses import replace
import re
from urllib.parse import urlparse

from .models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    AnalyticSignalRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    LifecycleTransitionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)


_TICKET_REFERENCE_URL_PATTERN = re.compile(
    r"^https://[^/?#\s]+([/?#][^\s]*)?$",
    re.IGNORECASE,
)

_LIFECYCLE_STATES_BY_FAMILY: dict[str, frozenset[str]] = {
    "alert": frozenset(
        {
            "new",
            "triaged",
            "investigating",
            "escalated_to_case",
            "closed",
            "reopened",
            "superseded",
        }
    ),
    "analytic_signal": frozenset({"active", "superseded", "withdrawn"}),
    "case": frozenset(
        {
            "open",
            "investigating",
            "pending_action",
            "contained_pending_validation",
            "closed",
            "reopened",
            "superseded",
        }
    ),
    "evidence": frozenset(
        {"collected", "validated", "linked", "superseded", "withdrawn"}
    ),
    "observation": frozenset(
        {"captured", "confirmed", "challenged", "superseded", "withdrawn"}
    ),
    "lead": frozenset(
        {
            "open",
            "triaged",
            "promoted_to_alert",
            "promoted_to_case",
            "closed",
            "superseded",
        }
    ),
    "lifecycle_transition": frozenset(
        {
            "new",
            "triaged",
            "investigating",
            "escalated_to_case",
            "closed",
            "reopened",
            "superseded",
            "active",
            "withdrawn",
            "open",
            "pending_action",
            "contained_pending_validation",
            "collected",
            "validated",
            "linked",
            "captured",
            "confirmed",
            "challenged",
            "promoted_to_alert",
            "promoted_to_case",
            "proposed",
            "under_review",
            "accepted",
            "rejected",
            "materialized",
            "pending",
            "approved",
            "expired",
            "canceled",
            "draft",
            "pending_approval",
            "executing",
            "completed",
            "failed",
            "unresolved",
            "dispatching",
            "queued",
            "running",
            "succeeded",
            "on_hold",
            "concluded",
            "planned",
            "generated",
            "accepted_for_reference",
            "rejected_for_reference",
            "matched",
            "mismatched",
            "stale",
            "resolved",
        }
    ),
    "recommendation": frozenset(
        {
            "proposed",
            "under_review",
            "accepted",
            "rejected",
            "materialized",
            "superseded",
            "withdrawn",
        }
    ),
    "approval_decision": frozenset(
        {"pending", "approved", "rejected", "expired", "canceled", "superseded"}
    ),
    "action_request": frozenset(
        {
            "draft",
            "pending_approval",
            "approved",
            "rejected",
            "expired",
            "canceled",
            "superseded",
            "executing",
            "completed",
            "failed",
            "unresolved",
        }
    ),
    "action_execution": frozenset(
        {
            "dispatching",
            "queued",
            "running",
            "succeeded",
            "failed",
            "canceled",
            "superseded",
        }
    ),
    "hunt": frozenset(
        {"draft", "active", "on_hold", "concluded", "closed", "superseded"}
    ),
    "hunt_run": frozenset(
        {"planned", "running", "completed", "canceled", "superseded", "unresolved"}
    ),
    "ai_trace": frozenset(
        {
            "generated",
            "under_review",
            "accepted_for_reference",
            "rejected_for_reference",
            "superseded",
            "withdrawn",
        }
    ),
    "reconciliation": frozenset(
        {"pending", "matched", "mismatched", "stale", "resolved", "superseded"}
    ),
}

_RECONCILIATION_INGEST_DISPOSITIONS = frozenset(
    {
        "created",
        "updated",
        "deduplicated",
        "restated",
        "matched",
        "missing",
        "duplicate",
        "mismatch",
        "stale",
    }
)
_REVIEWED_COORDINATION_TARGET_TYPES = frozenset({"glpi", "zammad"})
_COORDINATION_REFERENCE_FIELD_MAX_LENGTHS = {
    "coordination_reference_id": 128,
    "coordination_target_type": 32,
    "coordination_target_id": 256,
    "ticket_reference_url": 2048,
}

_LIFECYCLE_TRANSITION_SUBJECT_FAMILIES = frozenset(
    family
    for family in _LIFECYCLE_STATES_BY_FAMILY
    if family != LifecycleTransitionRecord.record_family
)


def _validate_lifecycle_state(record: ControlPlaneRecord) -> None:
    if isinstance(record, LifecycleTransitionRecord):
        allowed_states = _LIFECYCLE_STATES_BY_FAMILY.get(record.subject_record_family)
        if (
            record.subject_record_family
            not in _LIFECYCLE_TRANSITION_SUBJECT_FAMILIES
        ):
            raise ValueError(
                "lifecycle_transition record "
                f"{record.record_id!r} has unsupported subject_record_family "
                f"{record.subject_record_family!r}; expected one of "
                f"{sorted(_LIFECYCLE_TRANSITION_SUBJECT_FAMILIES)!r}"
            )
        if allowed_states is None:
            raise ValueError(
                "lifecycle_transition record "
                f"{record.record_id!r} has unsupported subject_record_family "
                f"{record.subject_record_family!r}"
            )
        if record.lifecycle_state not in allowed_states:
            raise ValueError(
                "lifecycle_transition record "
                f"{record.record_id!r} has invalid lifecycle_state {record.lifecycle_state!r} "
                f"for subject_record_family {record.subject_record_family!r}; expected one of "
                f"{sorted(allowed_states)!r}"
            )
        if (
            record.previous_lifecycle_state is not None
            and record.previous_lifecycle_state not in allowed_states
        ):
            raise ValueError(
                "lifecycle_transition record "
                f"{record.record_id!r} has invalid previous_lifecycle_state "
                f"{record.previous_lifecycle_state!r} for subject_record_family "
                f"{record.subject_record_family!r}; expected one of {sorted(allowed_states)!r}"
            )
        return
    allowed_states = _LIFECYCLE_STATES_BY_FAMILY.get(record.record_family)
    if allowed_states is None:
        raise TypeError(
            f"Unsupported control-plane record type: {type(record).__name__}"
        )
    if record.lifecycle_state not in allowed_states:  # type: ignore[attr-defined]
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} has invalid lifecycle_state "
            f"{record.lifecycle_state!r}; expected one of {sorted(allowed_states)!r}"  # type: ignore[attr-defined]
        )


def _require_any_linkage(
    record: ControlPlaneRecord,
    field_names: tuple[str, ...],
) -> None:
    if any(_has_linkage_value(getattr(record, field_name)) for field_name in field_names):
        return
    required_fields = ", ".join(field_names)
    raise ValueError(
        f"{record.record_family} record {record.record_id!r} requires at least one linkage field: "
        f"{required_fields}"
    )


def _has_linkage_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _require_non_empty_tuple(
    record: ControlPlaneRecord,
    field_name: str,
) -> None:
    values = getattr(record, field_name)
    if len(values) >= 1:
        return
    raise ValueError(
        f"{record.record_family} record {record.record_id!r} requires non-empty {field_name}"
    )


def _require_non_blank_fields(
    record: ControlPlaneRecord,
    field_names: tuple[str, ...],
) -> None:
    for field_name in field_names:
        if _has_linkage_value(getattr(record, field_name)):
            continue
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} requires non-blank {field_name}"
        )


def _validate_record(record: ControlPlaneRecord) -> None:
    _validate_lifecycle_state(record)

    if isinstance(record, AnalyticSignalRecord):
        _require_any_linkage(
            record,
            ("substrate_detection_record_id", "finding_id"),
        )
        if record.first_seen_at is not None and record.last_seen_at is not None:
            if record.first_seen_at > record.last_seen_at:
                raise ValueError(
                    f"analytic_signal record {record.record_id!r} requires first_seen_at <= last_seen_at"
                )
        return
    if isinstance(record, CaseRecord):
        _validate_coordination_reference_fields(record)
        _require_any_linkage(record, ("finding_id", "alert_id"))
        _require_non_empty_tuple(record, "evidence_ids")
        return
    if isinstance(record, EvidenceRecord):
        _require_any_linkage(record, ("alert_id", "case_id"))
        return
    if isinstance(record, ObservationRecord):
        _require_any_linkage(record, ("hunt_id", "hunt_run_id", "alert_id", "case_id"))
        _require_non_empty_tuple(record, "supporting_evidence_ids")
        return
    if isinstance(record, LeadRecord):
        _require_any_linkage(record, ("observation_id", "finding_id", "hunt_run_id"))
        return
    if isinstance(record, RecommendationRecord):
        _require_any_linkage(record, ("lead_id", "hunt_run_id", "alert_id", "case_id"))
        return
    if isinstance(record, LifecycleTransitionRecord):
        _require_non_blank_fields(
            record,
            ("transition_id", "subject_record_family", "subject_record_id"),
        )
        return
    if isinstance(record, ApprovalDecisionRecord):
        _require_non_empty_tuple(record, "approver_identities")
        return
    if isinstance(record, ActionRequestRecord):
        _require_any_linkage(record, ("case_id", "alert_id", "finding_id"))
        return
    if isinstance(record, ActionExecutionRecord):
        _require_non_blank_fields(
            record,
            (
                "action_execution_id",
                "action_request_id",
                "approval_decision_id",
                "delegation_id",
                "execution_surface_type",
                "execution_surface_id",
                "execution_run_id",
                "idempotency_key",
                "payload_hash",
            ),
        )
        if record.expires_at is not None and record.expires_at < record.delegated_at:
            raise ValueError(
                f"action_execution record {record.record_id!r} requires expires_at >= delegated_at"
            )
        return
    if isinstance(record, ReconciliationRecord):
        _require_any_linkage(
            record,
            ("finding_id", "analytic_signal_id", "execution_run_id"),
        )
        if record.ingest_disposition not in _RECONCILIATION_INGEST_DISPOSITIONS:
            raise ValueError(
                f"reconciliation record {record.record_id!r} has invalid ingest_disposition "
                f"{record.ingest_disposition!r}; expected one of "
                f"{sorted(_RECONCILIATION_INGEST_DISPOSITIONS)!r}"
            )
        if (
            record.first_seen_at is not None
            and record.last_seen_at is not None
            and record.first_seen_at > record.last_seen_at
        ):
            raise ValueError(
                f"reconciliation record {record.record_id!r} requires first_seen_at <= last_seen_at"
            )
        return
    if isinstance(
        record,
        (HuntRecord, HuntRunRecord, AITraceRecord),
    ):
        return
    if isinstance(record, AlertRecord):
        _validate_coordination_reference_fields(record)
        return
    raise TypeError(f"Unsupported control-plane record type: {type(record).__name__}")


def _validate_coordination_reference_fields(
    record: AlertRecord | CaseRecord,
) -> None:
    _normalize_coordination_reference_record(record)


def _normalize_coordination_reference_record(
    record: AlertRecord | CaseRecord,
) -> AlertRecord | CaseRecord:
    normalized_values: dict[str, str | None] = {}
    present_fields: list[str] = []
    for field_name, max_length in _COORDINATION_REFERENCE_FIELD_MAX_LENGTHS.items():
        raw_value = getattr(record, field_name)
        if raw_value is None:
            normalized_values[field_name] = None
            continue
        if not isinstance(raw_value, str):
            raise ValueError(
                f"{record.record_family} record {record.record_id!r} requires "
                f"{field_name} to be a string when provided"
            )
        normalized_value = raw_value.strip()
        if not normalized_value:
            raise ValueError(
                f"{record.record_family} record {record.record_id!r} requires "
                f"{field_name} to be non-blank when provided"
            )
        if len(normalized_value) > max_length:
            raise ValueError(
                f"{record.record_family} record {record.record_id!r} requires "
                f"{field_name} length <= {max_length}"
            )
        normalized_values[field_name] = normalized_value
        present_fields.append(field_name)

    if not present_fields:
        return record

    missing_fields = tuple(
        field_name
        for field_name in _COORDINATION_REFERENCE_FIELD_MAX_LENGTHS
        if normalized_values[field_name] is None
    )
    if missing_fields:
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} requires a complete "
            f"external ticket reference when any coordination field is present; "
            f"missing {missing_fields!r}"
        )

    coordination_target_type = normalized_values["coordination_target_type"]
    assert coordination_target_type is not None
    if coordination_target_type not in _REVIEWED_COORDINATION_TARGET_TYPES:
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} has unsupported "
            f"coordination_target_type {coordination_target_type!r}; expected one of "
            f"{sorted(_REVIEWED_COORDINATION_TARGET_TYPES)!r}"
        )

    ticket_reference_url = normalized_values["ticket_reference_url"]
    assert ticket_reference_url is not None
    if _TICKET_REFERENCE_URL_PATTERN.fullmatch(ticket_reference_url) is None:
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} requires "
            "ticket_reference_url to be an https URL with a network location"
        )
    parsed_ticket_reference_url = urlparse(ticket_reference_url)
    if (
        parsed_ticket_reference_url.scheme != "https"
        or not parsed_ticket_reference_url.netloc
    ):
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} requires "
            "ticket_reference_url to be an https URL with a network location"
        )

    return replace(record, **normalized_values)


__all__ = [
    "_normalize_coordination_reference_record",
    "_validate_lifecycle_state",
    "_validate_record",
]
