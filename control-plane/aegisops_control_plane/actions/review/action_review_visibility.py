from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from .action_review_index import (
    _ActionReviewRecordIndex,
    _action_request_is_review_bound,
)
from ...models import (
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
)

if TYPE_CHECKING:
    from ...service import AegisOpsControlPlaneService


_AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS = frozenset(
    {
        "business_hours_handoff",
        "awaiting_business_hours_review",
    }
)


def _action_review_after_hours_handoff_visibility(
    *,
    reviewed_context: Mapping[str, object],
    review_state: str,
) -> dict[str, object] | None:
    if review_state in {"completed", "failed", "canceled"}:
        return None
    handoff = reviewed_context.get("handoff")
    triage = reviewed_context.get("triage")
    triage_disposition = triage.get("disposition") if isinstance(triage, Mapping) else None
    if (
        not isinstance(handoff, Mapping)
        and triage_disposition not in _AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS
    ):
        return None

    visibility: dict[str, object] = {}
    if isinstance(handoff, Mapping):
        for source_key, target_key in (
            ("handoff_at", "handoff_at"),
            ("handoff_owner", "handoff_owner"),
            ("note", "note"),
            ("follow_up_evidence_ids", "follow_up_evidence_ids"),
        ):
            value = handoff.get(source_key)
            if value is not None:
                visibility[target_key] = value
    if (
        isinstance(triage, Mapping)
        and triage_disposition in _AFTER_HOURS_HANDOFF_TRIAGE_DISPOSITIONS
    ):
        for source_key, target_key in (
            ("disposition", "disposition"),
            ("recorded_at", "recorded_at"),
        ):
            value = triage.get(source_key)
            if value is not None:
                visibility[target_key] = value
        rationale = triage.get("closure_rationale")
        if rationale is None:
            rationale = triage.get("rationale")
        if rationale is not None:
            visibility["rationale"] = rationale
    return visibility or None


def _action_review_visibility_context(
    service: AegisOpsControlPlaneService,
    action_request: ActionRequestRecord,
) -> Mapping[str, object] | None:
    case = (
        service._store.get(CaseRecord, action_request.case_id)
        if action_request.case_id is not None
        else None
    )
    alert = (
        service._store.get(AlertRecord, action_request.alert_id)
        if action_request.alert_id is not None
        else None
    )
    if case is not None and isinstance(case.reviewed_context, Mapping):
        return case.reviewed_context
    if alert is not None and isinstance(alert.reviewed_context, Mapping):
        return alert.reviewed_context
    return None


def _action_review_manual_fallback_visibility(
    *,
    reviewed_context: Mapping[str, object],
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    review_state: str,
    allow_unscoped_context: bool,
) -> dict[str, object] | None:
    manual_fallback = _action_review_visibility_entry(
        reviewed_context=reviewed_context,
        action_request_id=action_request.action_request_id,
        context_key="manual_fallback",
    )
    if not isinstance(manual_fallback, Mapping):
        return None

    approval_decision_id = (
        approval_decision.approval_decision_id
        if approval_decision is not None
        else action_request.approval_decision_id
    )
    if (
        approval_decision is None
        or approval_decision.lifecycle_state != "approved"
        or review_state in {"pending", "rejected", "expired", "superseded"}
    ):
        return None
    if not _action_review_context_matches_lineage(
        visibility_context=manual_fallback,
        action_request_id=action_request.action_request_id,
        approval_decision_id=approval_decision_id,
        allow_unscoped_context=allow_unscoped_context,
    ):
        return None

    visibility: dict[str, object] = {}
    for source_key in ("action_request_id", "approval_decision_id"):
        value = manual_fallback.get(source_key)
        if value is not None:
            visibility[source_key] = value
    for source_key, target_key in (
        ("fallback_at", "fallback_at"),
        ("performed_at", "fallback_at"),
        ("fallback_actor_identity", "fallback_actor_identity"),
        ("authority_boundary", "authority_boundary"),
        ("reason", "reason"),
        ("action_taken", "action_taken"),
        ("verification_evidence_ids", "verification_evidence_ids"),
        ("residual_uncertainty", "residual_uncertainty"),
    ):
        value = manual_fallback.get(source_key)
        if value is None:
            continue
        if source_key == "performed_at" and target_key in visibility:
            continue
        visibility[target_key] = value
    return visibility


def _action_review_escalation_visibility(
    *,
    reviewed_context: Mapping[str, object],
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    review_state: str,
    allow_unscoped_context: bool,
) -> dict[str, object] | None:
    requested_payload = action_request.requested_payload
    escalation_context = _action_review_visibility_entry(
        reviewed_context=reviewed_context,
        action_request_id=action_request.action_request_id,
        context_key="escalation",
    )
    if not isinstance(escalation_context, Mapping):
        return None

    approval_decision_id = (
        approval_decision.approval_decision_id
        if approval_decision is not None
        else action_request.approval_decision_id
    )
    if not _action_review_context_matches_lineage(
        visibility_context=escalation_context,
        action_request_id=action_request.action_request_id,
        approval_decision_id=approval_decision_id,
        allow_unscoped_context=allow_unscoped_context,
    ):
        return None

    recorded_review_state = escalation_context.get("review_state")
    visibility: dict[str, object] = {
        "action_request_id": action_request.action_request_id,
        "approval_decision_id": approval_decision_id,
        "requester_identity": action_request.requester_identity,
        "review_state": (
            recorded_review_state
            if isinstance(recorded_review_state, str) and recorded_review_state.strip()
            else review_state
        ),
    }
    escalation_reason = requested_payload.get("escalation_reason")
    if escalation_reason is not None:
        visibility["escalation_reason"] = escalation_reason
    for source_key, target_key in (
        ("escalated_at", "escalated_at"),
        ("escalated_to", "escalated_to"),
        ("escalated_by_identity", "escalated_by_identity"),
        ("note", "note"),
    ):
        value = escalation_context.get(source_key)
        if value is not None:
            visibility[target_key] = value
    return visibility


def _action_review_context_matches_lineage(
    *,
    visibility_context: Mapping[str, object],
    action_request_id: str,
    approval_decision_id: str | None,
    allow_unscoped_context: bool,
) -> bool:
    scoped_action_request_id = visibility_context.get("action_request_id")
    scoped_approval_decision_id = visibility_context.get("approval_decision_id")

    if scoped_action_request_id is None:
        if scoped_approval_decision_id is not None:
            return (
                approval_decision_id is not None
                and scoped_approval_decision_id == approval_decision_id
            )
        return allow_unscoped_context

    if scoped_action_request_id != action_request_id:
        return False
    if scoped_approval_decision_id is not None:
        return (
            approval_decision_id is not None
            and scoped_approval_decision_id == approval_decision_id
        )
    return True


def _action_review_visibility_entry(
    *,
    reviewed_context: Mapping[str, object],
    action_request_id: str,
    context_key: str,
) -> Mapping[str, object] | None:
    action_review_visibility = reviewed_context.get("action_review_visibility")
    if isinstance(action_review_visibility, Mapping):
        scoped_visibility = action_review_visibility.get(action_request_id)
        if isinstance(scoped_visibility, Mapping):
            scoped_entry = scoped_visibility.get(context_key)
            if isinstance(scoped_entry, Mapping):
                return scoped_entry
    legacy_entry = reviewed_context.get(context_key)
    if isinstance(legacy_entry, Mapping):
        return legacy_entry
    return None


def _action_review_visibility_update(
    *,
    action_request_id: str,
    context_key: str,
    context_value: Mapping[str, object],
) -> dict[str, object]:
    return {
        "action_review_visibility": {
            action_request_id: {
                context_key: dict(context_value),
            }
        }
    }


def _case_has_single_review_bound_action_request(
    service: AegisOpsControlPlaneService,
    case_id: str | None,
    *,
    record_index: _ActionReviewRecordIndex | None = None,
) -> bool:
    if case_id is None:
        return False
    if record_index is not None:
        matching_requests = record_index.requests_by_case_id.get(case_id, ())
    else:
        matching_requests = tuple(
            record
            for record in service._store.list(ActionRequestRecord)
            if record.case_id == case_id
        )
    review_bound_count = sum(
        1
        for record in matching_requests
        if _action_request_is_review_bound(record)
    )
    return review_bound_count == 1


def action_review_runtime_visibility(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    review_state: str,
    record_index: _ActionReviewRecordIndex | None = None,
) -> dict[str, object] | None:
    reviewed_context = _action_review_visibility_context(service, action_request)
    if reviewed_context is None:
        return None

    allow_unscoped_action_visibility = _case_has_single_review_bound_action_request(
        service,
        action_request.case_id,
        record_index=record_index,
    )
    visibility: dict[str, object] = {}
    after_hours_handoff = _action_review_after_hours_handoff_visibility(
        reviewed_context=reviewed_context,
        review_state=review_state,
    )
    if after_hours_handoff is not None:
        visibility["after_hours_handoff"] = after_hours_handoff

    manual_fallback = _action_review_manual_fallback_visibility(
        reviewed_context=reviewed_context,
        action_request=action_request,
        approval_decision=approval_decision,
        review_state=review_state,
        allow_unscoped_context=allow_unscoped_action_visibility,
    )
    if manual_fallback is not None:
        visibility["manual_fallback"] = manual_fallback

    escalation_notes = _action_review_escalation_visibility(
        reviewed_context=reviewed_context,
        action_request=action_request,
        approval_decision=approval_decision,
        review_state=review_state,
        allow_unscoped_context=allow_unscoped_action_visibility,
    )
    if escalation_notes is not None:
        visibility["escalation_notes"] = escalation_notes

    return visibility or None
