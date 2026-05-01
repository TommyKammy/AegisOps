from __future__ import annotations

from typing import TYPE_CHECKING, Mapping

from .action_review_timeline import action_review_mismatch_inspection
from ...models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ReconciliationRecord,
)

if TYPE_CHECKING:
    from ...service import AegisOpsControlPlaneService


def action_review_coordination_ticket_outcome(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    reconciliation: ReconciliationRecord | None,
    runtime_visibility: Mapping[str, object] | None,
    path_health: Mapping[str, object],
    review_state: str,
) -> dict[str, object] | None:
    requested_payload = action_request.requested_payload
    if requested_payload.get("action_type") != "create_tracking_ticket":
        return None
    if (
        action_execution is None
        and reconciliation is None
        and review_state in {"rejected", "expired", "superseded", "canceled"}
    ):
        return None

    downstream_binding = action_review_downstream_binding(action_execution)
    mismatch = action_review_coordination_ticket_mismatch(reconciliation)
    terminal_issue = action_review_coordination_ticket_terminal_issue(
        action_execution=action_execution,
        path_health=path_health,
    )
    manual_fallback = None
    if isinstance(runtime_visibility, Mapping):
        manual_fallback_entry = runtime_visibility.get("manual_fallback")
        if isinstance(manual_fallback_entry, Mapping):
            manual_fallback = dict(manual_fallback_entry)

    if (
        reconciliation is not None
        and reconciliation.lifecycle_state == "matched"
        and action_execution is not None
        and action_execution.lifecycle_state == "succeeded"
    ):
        status = "created"
        summary = (
            "reviewed create-ticket outcome recorded from authoritative "
            "execution and reconciliation"
        )
    elif manual_fallback is not None:
        status = "manual_fallback"
        summary = str(
            manual_fallback.get("action_taken")
            or manual_fallback.get("reason")
            or "reviewed create-ticket outcome recorded as manual fallback"
        )
    elif mismatch is not None:
        status = "mismatch"
        summary = str(mismatch["mismatch_summary"])
    elif terminal_issue is not None and terminal_issue["category"] == "timeout":
        status = "timeout"
        summary = str(terminal_issue["reason"]).replace("_", " ")
    elif terminal_issue is not None:
        status = "failed"
        summary = str(terminal_issue["reason"]).replace("_", " ")
    else:
        status = "pending"
        summary = "reviewed create-ticket outcome still awaiting authoritative result"

    outcome = {
        "authority": "authoritative_aegisops_review",
        "status": status,
        "summary": summary,
        "action_request_id": action_request.action_request_id,
        "approval_decision_id": (
            None if approval_decision is None else approval_decision.approval_decision_id
        ),
        "action_execution_id": (
            None if action_execution is None else action_execution.action_execution_id
        ),
        "execution_run_id": (
            None if action_execution is None else action_execution.execution_run_id
        ),
        "reconciliation_id": (
            None if reconciliation is None else reconciliation.reconciliation_id
        ),
        "coordination_reference_id": (
            action_request.target_scope.get("coordination_reference_id")
            if isinstance(action_request.target_scope.get("coordination_reference_id"), str)
            else requested_payload.get("coordination_reference_id")
        ),
        "coordination_target_type": (
            action_request.target_scope.get("coordination_target_type")
            if isinstance(action_request.target_scope.get("coordination_target_type"), str)
            else requested_payload.get("coordination_target_type")
        ),
        "coordination_target_id": (
            None
            if downstream_binding is None
            else downstream_binding.get("coordination_target_id")
        ),
        "external_receipt_id": (
            None
            if downstream_binding is None
            else downstream_binding.get("external_receipt_id")
        ),
        "ticket_reference_url": (
            None
            if downstream_binding is None
            else downstream_binding.get("ticket_reference_url")
        ),
    }
    if terminal_issue is not None:
        issue_payload = {
            key: value
            for key, value in terminal_issue.items()
            if key != "category"
        }
        if terminal_issue["category"] == "timeout":
            outcome["timeout"] = issue_payload
        else:
            outcome["terminal_issue"] = issue_payload
    if mismatch is not None:
        outcome["mismatch"] = mismatch
    if manual_fallback is not None:
        outcome["manual_fallback"] = manual_fallback
    return outcome


def action_review_downstream_binding(
    action_execution: ActionExecutionRecord | None,
) -> Mapping[str, object] | None:
    if action_execution is None or not isinstance(action_execution.provenance, Mapping):
        return None
    downstream_binding = action_execution.provenance.get("downstream_binding")
    if not isinstance(downstream_binding, Mapping):
        return None
    return downstream_binding


def action_review_coordination_ticket_mismatch(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, object] | None:
    mismatch = action_review_mismatch_inspection(reconciliation)
    if mismatch is None:
        return None
    if (
        mismatch["lifecycle_state"] != "mismatched"
        and mismatch["ingest_disposition"] != "mismatch"
    ):
        return None
    return mismatch


def action_review_coordination_ticket_terminal_issue(
    *,
    action_execution: ActionExecutionRecord | None,
    path_health: Mapping[str, object],
) -> dict[str, object] | None:
    if (
        action_execution is not None
        and isinstance(action_execution.provenance, Mapping)
        and isinstance(action_execution.provenance.get("dispatch_failure"), Mapping)
    ):
        dispatch_failure = action_execution.provenance["dispatch_failure"]
        if dispatch_failure.get("error_type") == "TimeoutError":
            timeout = {
                "category": "timeout",
                "path": "provider",
                "reason": "dispatch_timeout",
            }
            error = dispatch_failure.get("error")
            if isinstance(error, str) and error:
                timeout["error"] = error
            return timeout

    paths = path_health.get("paths")
    if not isinstance(paths, Mapping):
        return None
    timeout_reasons = {
        "ingest_signal_timeout",
        "delegation_receipt_timeout",
        "provider_receipt_timeout",
        "authoritative_outcome_timeout",
        "reconciliation_timeout",
    }
    terminal_failure_reasons = {
        "execution_failed",
        "execution_canceled",
        "execution_expired",
        "execution_rejected",
    }
    provider_path = paths.get("provider")
    if isinstance(provider_path, Mapping):
        provider_reason = provider_path.get("reason")
        if (
            isinstance(provider_reason, str)
            and provider_reason in terminal_failure_reasons
        ):
            return {
                "category": "failed",
                "path": "provider",
                "reason": provider_reason,
            }
    for path_name in ("ingest", "delegation", "provider", "persistence"):
        path = paths.get(path_name)
        if not isinstance(path, Mapping):
            continue
        reason = path.get("reason")
        if not isinstance(reason, str):
            continue
        if reason in timeout_reasons:
            return {
                "category": "timeout",
                "path": path_name,
                "reason": reason,
            }
    return None
