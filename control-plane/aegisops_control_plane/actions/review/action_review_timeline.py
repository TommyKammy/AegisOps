from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Mapping

from ...models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ReconciliationRecord,
)

if TYPE_CHECKING:
    from ...service import AegisOpsControlPlaneService


def _action_review_stage_snapshot(
    *,
    stage: str,
    record_family: str,
    record_id: str | None,
    state: str,
    occurred_at: datetime | None,
    actor_identities: tuple[str, ...] = (),
    details: Mapping[str, object] | None = None,
) -> dict[str, object]:
    snapshot = {
        "stage": stage,
        "record_family": record_family,
        "record_id": record_id,
        "state": state,
        "occurred_at": occurred_at,
        "actor_identities": actor_identities,
    }
    if details:
        snapshot["details"] = dict(details)
    return snapshot


def action_review_timeline(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_state: str | None,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    reconciliation: ReconciliationRecord | None,
) -> tuple[dict[str, object], ...]:
    delegation_details: dict[str, object] = {}
    action_execution_details: dict[str, object] = {}
    execution_actor_identities: tuple[str, ...] = ()
    if action_execution is not None:
        delegation_details["delegation_id"] = action_execution.delegation_id
        execution_actor_identities = service._ai_trace_lifecycle_service.merge_ids(
            action_execution.provenance.get("initiated_by"),
            action_execution.provenance.get("delegation_issuer"),
        )
        downstream_binding = action_execution.provenance.get("downstream_binding")
        if isinstance(downstream_binding, Mapping):
            delegation_details["downstream_binding"] = dict(downstream_binding)
        adapter = action_execution.provenance.get("adapter")
        if isinstance(adapter, str) and adapter.strip():
            action_execution_details["adapter"] = adapter
        adapter_base_url = action_execution.provenance.get("adapter_base_url")
        if isinstance(adapter_base_url, str) and adapter_base_url.strip():
            action_execution_details["adapter_base_url"] = adapter_base_url
    timeline = (
        _action_review_stage_snapshot(
            stage="action_request",
            record_family="action_request",
            record_id=action_request.action_request_id,
            state=action_request.lifecycle_state,
            occurred_at=action_request.requested_at,
            actor_identities=(
                ()
                if action_request.requester_identity is None
                else (action_request.requester_identity,)
            ),
            details={
                "recipient_identity": action_request.requested_payload.get(
                    "recipient_identity"
                ),
                "execution_surface_type": action_request.policy_evaluation.get(
                    "execution_surface_type"
                ),
                "execution_surface_id": action_request.policy_evaluation.get(
                    "execution_surface_id"
                ),
            },
        ),
        _action_review_stage_snapshot(
            stage="approval_decision",
            record_family="approval_decision",
            record_id=(
                None
                if approval_decision is None
                else approval_decision.approval_decision_id
            ),
            state=(
                approval_decision.lifecycle_state
                if approval_decision is not None
                else (approval_state or "pending")
            ),
            occurred_at=(
                None if approval_decision is None else approval_decision.decided_at
            ),
            actor_identities=(
                ()
                if approval_decision is None
                else approval_decision.approver_identities
            ),
            details=(
                {}
                if approval_decision is None
                or approval_decision.decision_rationale is None
                else {
                    "decision_rationale": approval_decision.decision_rationale,
                }
            ),
        ),
        _action_review_stage_snapshot(
            stage="delegation",
            record_family="action_execution",
            record_id=(
                None
                if action_execution is None
                else action_execution.action_execution_id
            ),
            state=(
                "awaiting_delegation"
                if action_execution is None
                else "delegated"
            ),
            occurred_at=(
                None if action_execution is None else action_execution.delegated_at
            ),
            actor_identities=(
                ()
                if action_execution is None
                else service._ai_trace_lifecycle_service.ids_from_mapping(
                    action_execution.provenance,
                    "delegation_issuer",
                )
            ),
            details=delegation_details,
        ),
        _action_review_stage_snapshot(
            stage="action_execution",
            record_family="action_execution",
            record_id=(
                None
                if action_execution is None
                else action_execution.action_execution_id
            ),
            state=(
                "awaiting_execution"
                if action_execution is None
                else action_execution.lifecycle_state
            ),
            occurred_at=None,
            actor_identities=execution_actor_identities,
            details=(
                {}
                if action_execution is None
                else {
                    "execution_run_id": action_execution.execution_run_id,
                    "execution_surface_type": action_execution.execution_surface_type,
                    "execution_surface_id": action_execution.execution_surface_id,
                    **action_execution_details,
                }
            ),
        ),
        _action_review_stage_snapshot(
            stage="reconciliation",
            record_family="reconciliation",
            record_id=(
                None if reconciliation is None else reconciliation.reconciliation_id
            ),
            state=(
                "awaiting_reconciliation"
                if reconciliation is None
                else reconciliation.lifecycle_state
            ),
            occurred_at=(
                None if reconciliation is None else reconciliation.compared_at
            ),
            details=(
                {}
                if reconciliation is None
                else {
                    "ingest_disposition": reconciliation.ingest_disposition,
                    "execution_run_id": reconciliation.execution_run_id,
                }
            ),
        ),
    )
    return timeline


def action_review_mismatch_inspection(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, object] | None:
    if reconciliation is None:
        return None
    if reconciliation.lifecycle_state not in {"pending", "mismatched", "stale"}:
        return None
    return {
        "reconciliation_id": reconciliation.reconciliation_id,
        "lifecycle_state": reconciliation.lifecycle_state,
        "ingest_disposition": reconciliation.ingest_disposition,
        "mismatch_summary": reconciliation.mismatch_summary,
        "correlation_key": reconciliation.correlation_key,
        "execution_run_id": reconciliation.execution_run_id,
        "linked_execution_run_ids": reconciliation.linked_execution_run_ids,
        "subject_linkage": dict(reconciliation.subject_linkage),
        "first_seen_at": reconciliation.first_seen_at,
        "last_seen_at": reconciliation.last_seen_at,
        "compared_at": reconciliation.compared_at,
    }


def action_review_reconciliation_detail(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, object]:
    if reconciliation is None:
        return {
            "authority": "aegisops_reconciliation_record",
            "expected_aegisops_state": "matched",
            "authoritative_aegisops_state": "missing",
            "received_receipt": {
                "ingest_disposition": "missing",
                "execution_run_id": None,
                "linked_execution_run_ids": (),
                "correlation_key": None,
                "first_seen_at": None,
                "last_seen_at": None,
            },
            "closeout_evidence": {
                "reconciliation_id": None,
                "compared_at": None,
                "mismatch_summary": (
                    "No authoritative reconciliation record is visible for this "
                    "reviewed request yet."
                ),
            },
            "action_required": True,
            "next_step": "obtain_authoritative_receipt_before_closeout",
        }

    action_required = reconciliation.lifecycle_state != "matched"
    if reconciliation.lifecycle_state == "matched":
        next_step = "record_closeout_evidence"
    elif (
        reconciliation.lifecycle_state == "stale"
        or reconciliation.ingest_disposition == "stale"
    ):
        next_step = "refresh_downstream_receipt_before_closeout"
    elif (
        reconciliation.lifecycle_state == "mismatched"
        or reconciliation.ingest_disposition == "mismatch"
    ):
        next_step = "review_mismatch_before_closeout"
    else:
        next_step = "obtain_authoritative_receipt_before_closeout"

    return {
        "authority": "aegisops_reconciliation_record",
        "expected_aegisops_state": "matched",
        "authoritative_aegisops_state": reconciliation.lifecycle_state,
        "received_receipt": {
            "ingest_disposition": reconciliation.ingest_disposition,
            "execution_run_id": reconciliation.execution_run_id,
            "linked_execution_run_ids": reconciliation.linked_execution_run_ids,
            "correlation_key": reconciliation.correlation_key,
            "first_seen_at": reconciliation.first_seen_at,
            "last_seen_at": reconciliation.last_seen_at,
        },
        "closeout_evidence": {
            "reconciliation_id": reconciliation.reconciliation_id,
            "compared_at": reconciliation.compared_at,
            "mismatch_summary": reconciliation.mismatch_summary,
        },
        "action_required": action_required,
        "next_step": next_step,
    }
