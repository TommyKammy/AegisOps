from __future__ import annotations

from dataclasses import dataclass, field
from typing import Type, TypeVar

from ..models import (
    AITraceRecord,
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)

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


def _validate_lifecycle_state(record: ControlPlaneRecord) -> None:
    allowed_states = _LIFECYCLE_STATES_BY_FAMILY[record.record_family]
    if record.lifecycle_state not in allowed_states:  # type: ignore[attr-defined]
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} has invalid lifecycle_state "
            f"{record.lifecycle_state!r}; expected one of {sorted(allowed_states)!r}"  # type: ignore[attr-defined]
        )


def _require_any_linkage(
    record: ControlPlaneRecord,
    field_names: tuple[str, ...],
) -> None:
    if any(getattr(record, field_name) is not None for field_name in field_names):
        return
    required_fields = ", ".join(field_names)
    raise ValueError(
        f"{record.record_family} record {record.record_id!r} requires at least one linkage field: "
        f"{required_fields}"
    )


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


def _validate_record(record: ControlPlaneRecord) -> None:
    _validate_lifecycle_state(record)

    if isinstance(record, CaseRecord):
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
    if isinstance(record, ApprovalDecisionRecord):
        _require_non_empty_tuple(record, "approver_identities")
        return
    if isinstance(record, ActionRequestRecord):
        _require_any_linkage(record, ("case_id", "alert_id", "finding_id"))
        return
    if isinstance(record, ReconciliationRecord):
        _require_any_linkage(
            record,
            ("finding_id", "analytic_signal_id", "workflow_execution_id"),
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
        (AlertRecord, HuntRecord, HuntRunRecord, AITraceRecord),
    ):
        return
    raise TypeError(f"Unsupported control-plane record type: {type(record).__name__}")


@dataclass
class PostgresControlPlaneStore:
    """In-process authoritative store for reviewed control-plane record families."""

    dsn: str
    persistence_mode: str = field(default="in_memory", init=False)
    _records: dict[str, dict[str, ControlPlaneRecord]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def save(self, record: RecordT) -> RecordT:
        _validate_record(record)
        family_records = self._records.setdefault(record.record_family, {})
        family_records[record.record_id] = record
        return record

    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        family_records = self._records.get(record_type.record_family, {})
        record = family_records.get(record_id)
        if record is None:
            return None
        if not isinstance(record, record_type):
            raise TypeError(
                f"Stored {record.record_family} record did not match requested type {record_type.__name__}"
            )
        return record

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        family_records = self._records.get(record_type.record_family, {})
        return tuple(
            record
            for record in family_records.values()
            if isinstance(record, record_type)
        )
