from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping

from .models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    ReconciliationRecord,
)


def _action_review_path_health_entry(path: Mapping[str, str]) -> dict[str, str]:
    normalized = dict(path)
    normalized.setdefault("health", normalized.get("state", "degraded"))
    return normalized


def _action_review_path_health_entries(
    paths: Mapping[str, Mapping[str, str]],
) -> dict[str, dict[str, str]]:
    return {
        path_name: _action_review_path_health_entry(path)
        for path_name, path in paths.items()
    }


def _action_review_terminal_non_delegated_path_health() -> dict[str, dict[str, str]]:
    return _action_review_path_health_entries(
        {
            "ingest": {
                "state": "healthy",
                "reason": "review_closed_before_ingest",
            },
            "delegation": {
                "state": "healthy",
                "reason": "review_closed_without_delegation",
            },
            "provider": {
                "state": "healthy",
                "reason": "review_closed_before_provider",
            },
            "persistence": {
                "state": "healthy",
                "reason": "review_closed_before_reconciliation",
            },
        }
    )


def _action_review_unresolved_without_execution_path_health() -> (
    dict[str, dict[str, str]]
):
    return _action_review_path_health_entries(
        {
            "ingest": {
                "state": "degraded",
                "reason": "ingest_signal_missing_after_approval",
            },
            "delegation": {
                "state": "degraded",
                "reason": "reviewed_delegation_missing_after_approval",
            },
            "provider": {
                "state": "degraded",
                "reason": "provider_signal_missing_after_approval",
            },
            "persistence": {
                "state": "degraded",
                "reason": "reconciliation_missing_after_approval",
            },
        }
    )


def _action_review_reconciliation_without_execution_path_health(
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    reconciliation: ReconciliationRecord,
    review_state: str,
) -> dict[str, dict[str, str]]:
    delegation_path = _action_review_delegation_path_health(
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=None,
        review_state=review_state,
    )
    if delegation_path["state"] != "healthy":
        delegation_path = _action_review_path_health_entry(
            {
                "state": "degraded",
                "reason": "reviewed_delegation_record_missing",
            }
        )
    return _action_review_path_health_entries(
        {
            "ingest": _action_review_ingest_path_health(reconciliation),
            "delegation": delegation_path,
            "provider": {
                "state": "degraded",
                "reason": "provider_execution_record_missing",
            },
            "persistence": {
                "state": "degraded",
                "reason": "reconciliation_execution_lineage_missing",
            },
        }
    )


def _action_review_visibility_deadline(
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
) -> datetime | None:
    return min(
        (
            candidate
            for candidate in (
                None if action_execution is None else action_execution.expires_at,
                (
                    None
                    if approval_decision is None
                    else approval_decision.approved_expires_at
                ),
                action_request.expires_at,
            )
            if candidate is not None
        ),
        default=None,
    )


def _action_review_overdue_path_health(
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    review_state: str,
    action_execution: ActionExecutionRecord | None,
    reconciliation: ReconciliationRecord | None,
    paths: Mapping[str, Mapping[str, str]],
) -> dict[str, dict[str, str]]:
    if action_execution is None:
        if review_state in {"approved", "executing"}:
            if reconciliation is not None:
                return _action_review_reconciliation_without_execution_path_health(
                    action_request=action_request,
                    approval_decision=approval_decision,
                    reconciliation=reconciliation,
                    review_state=review_state,
                )
            return _action_review_unresolved_without_execution_path_health()
        return _action_review_path_health_entries(paths)

    overdue_paths = {path_name: dict(path) for path_name, path in paths.items()}
    if overdue_paths["ingest"].get("reason") == "awaiting_ingest_signal":
        overdue_paths["ingest"] = _action_review_path_health_entry(
            {
                "state": "degraded",
                "reason": "ingest_signal_timeout",
            }
        )
    if overdue_paths["delegation"].get("reason") == "awaiting_receipt":
        overdue_paths["delegation"] = _action_review_path_health_entry(
            {
                "state": "degraded",
                "reason": "delegation_receipt_timeout",
            }
        )
    if overdue_paths["provider"].get("reason") == "awaiting_provider_receipt":
        overdue_paths["provider"] = _action_review_path_health_entry(
            {
                "state": "degraded",
                "reason": "provider_receipt_timeout",
            }
        )
    elif overdue_paths["provider"].get("reason") == "awaiting_authoritative_outcome":
        overdue_paths["provider"] = _action_review_path_health_entry(
            {
                "state": "degraded",
                "reason": "authoritative_outcome_timeout",
            }
        )
    if overdue_paths["persistence"].get("reason") == "awaiting_reconciliation":
        overdue_paths["persistence"] = _action_review_path_health_entry(
            {
                "state": "degraded",
                "reason": "reconciliation_timeout",
            }
        )
    return _action_review_path_health_entries(overdue_paths)


def _action_review_ingest_path_health(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, str]:
    if reconciliation is None:
        return _action_review_path_health_entry(
            {
                "state": "delayed",
                "reason": "awaiting_ingest_signal",
            }
        )
    return _action_review_path_health_entry(
        {
            "matched": {
                "state": "healthy",
                "reason": "observations_current",
            },
            "missing": {
                "state": "delayed",
                "reason": "observation_missing",
            },
            "stale": {
                "state": "degraded",
                "reason": "stale_observation",
            },
            "duplicate": {
                "state": "degraded",
                "reason": "duplicate_observations",
            },
            "mismatch": {
                "state": "degraded",
                "reason": "mismatch_detected",
            },
        }.get(
            reconciliation.ingest_disposition,
            {
                "state": "degraded",
                "reason": "ingest_anomaly",
            },
        )
    )


def _action_review_delegation_path_health(
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    review_state: str,
) -> dict[str, str]:
    if action_execution is not None:
        if action_execution.lifecycle_state == "dispatching":
            return _action_review_path_health_entry(
                {
                    "state": "delayed",
                    "reason": "awaiting_receipt",
                }
            )
        return _action_review_path_health_entry(
            {
                "state": "healthy",
                "reason": "delegated",
            }
        )
    if approval_decision is not None and approval_decision.lifecycle_state == "approved":
        return _action_review_path_health_entry(
            {
                "state": "delayed",
                "reason": "awaiting_reviewed_delegation",
            }
        )
    if (
        review_state in {"approved", "executing"}
        or action_request.lifecycle_state == "approved"
    ):
        return _action_review_path_health_entry(
            {
                "state": "delayed",
                "reason": "awaiting_reviewed_delegation",
            }
        )
    return _action_review_path_health_entry(
        {
            "state": "delayed",
            "reason": "awaiting_approval",
        }
    )


def _action_review_provider_path_health(
    action_execution: ActionExecutionRecord | None,
) -> dict[str, str]:
    if action_execution is None:
        return _action_review_path_health_entry(
            {
                "state": "delayed",
                "reason": "awaiting_delegation",
            }
        )
    return _action_review_path_health_entry(
        {
            "dispatching": {
                "state": "delayed",
                "reason": "awaiting_provider_receipt",
            },
            "queued": {
                "state": "delayed",
                "reason": "awaiting_authoritative_outcome",
            },
            "running": {
                "state": "delayed",
                "reason": "awaiting_authoritative_outcome",
            },
            "succeeded": {
                "state": "healthy",
                "reason": "execution_succeeded",
            },
            "failed": {
                "state": "failed",
                "reason": "execution_failed",
            },
            "canceled": {
                "state": "failed",
                "reason": "execution_canceled",
            },
            "unresolved": {
                "state": "degraded",
                "reason": "execution_unresolved",
            },
            "expired": {
                "state": "failed",
                "reason": "execution_expired",
            },
            "rejected": {
                "state": "failed",
                "reason": "execution_rejected",
            },
            "superseded": {
                "state": "degraded",
                "reason": "execution_superseded",
            },
        }.get(
            action_execution.lifecycle_state,
            {
                "state": "degraded",
                "reason": "provider_anomaly",
            },
        )
    )


def _action_review_persistence_path_health(
    reconciliation: ReconciliationRecord | None,
) -> dict[str, str]:
    if reconciliation is None:
        return _action_review_path_health_entry(
            {
                "state": "delayed",
                "reason": "awaiting_reconciliation",
            }
        )
    return _action_review_path_health_entry(
        {
            "matched": {
                "state": "healthy",
                "reason": "reconciliation_matched",
            },
            "pending": {
                "state": "delayed",
                "reason": "reconciliation_pending",
            },
            "mismatched": {
                "state": "degraded",
                "reason": "reconciliation_mismatched",
            },
            "stale": {
                "state": "degraded",
                "reason": "reconciliation_stale",
            },
        }.get(
            reconciliation.lifecycle_state,
            {
                "state": "degraded",
                "reason": "persistence_anomaly",
            },
        )
    )


def _action_review_overall_path_state(
    paths: Iterable[Mapping[str, str]],
) -> str:
    severity = {
        "healthy": 0,
        "delayed": 1,
        "degraded": 2,
        "failed": 3,
    }
    highest = max(
        (
            severity.get(path.get("state", "degraded"), severity["degraded"])
            for path in paths
        ),
        default=severity["healthy"],
    )
    for state, rank in severity.items():
        if rank == highest:
            return state
    return "degraded"


def _action_review_path_health_summary(
    *,
    overall_state: str,
    paths: Mapping[str, Mapping[str, str]],
) -> str:
    active_paths = [
        f"{path_name} {path['reason'].replace('_', ' ')}"
        for path_name, path in paths.items()
        if path.get("state") != "healthy"
    ]
    if not active_paths:
        return "all reviewed execution visibility paths are healthy"
    primary = active_paths[:2]
    joined = "; ".join(primary)
    return f"{overall_state} path visibility: {joined}"


def action_review_path_health(
    service: AegisOpsControlPlaneService,
    *,
    action_request: ActionRequestRecord,
    approval_decision: ApprovalDecisionRecord | None,
    action_execution: ActionExecutionRecord | None,
    reconciliation: ReconciliationRecord | None,
    review_state: str,
    as_of: datetime,
) -> dict[str, object]:
    if action_execution is None and reconciliation is None:
        if review_state in {"rejected", "expired", "superseded", "canceled"}:
            paths = _action_review_terminal_non_delegated_path_health()
        elif (
            review_state == "unresolved"
            and approval_decision is not None
            and approval_decision.lifecycle_state == "approved"
        ):
            paths = _action_review_unresolved_without_execution_path_health()
        else:
            paths = {
                "ingest": _action_review_ingest_path_health(reconciliation),
                "delegation": _action_review_delegation_path_health(
                    action_request=action_request,
                    approval_decision=approval_decision,
                    action_execution=action_execution,
                    review_state=review_state,
                ),
                "provider": _action_review_provider_path_health(action_execution),
                "persistence": _action_review_persistence_path_health(reconciliation),
            }
    elif action_execution is None:
        paths = _action_review_reconciliation_without_execution_path_health(
            action_request=action_request,
            approval_decision=approval_decision,
            reconciliation=reconciliation,
            review_state=review_state,
        )
    else:
        paths = {
            "ingest": _action_review_ingest_path_health(reconciliation),
            "delegation": _action_review_delegation_path_health(
                action_request=action_request,
                approval_decision=approval_decision,
                action_execution=action_execution,
                review_state=review_state,
            ),
            "provider": _action_review_provider_path_health(action_execution),
            "persistence": _action_review_persistence_path_health(reconciliation),
        }
    deadline = _action_review_visibility_deadline(
        action_request=action_request,
        approval_decision=approval_decision,
        action_execution=action_execution,
    )
    if deadline is not None and deadline <= as_of:
        paths = _action_review_overdue_path_health(
            action_request=action_request,
            approval_decision=approval_decision,
            review_state=review_state,
            action_execution=action_execution,
            reconciliation=reconciliation,
            paths=paths,
        )
    overall_state = _action_review_overall_path_state(paths.values())
    return {
        "overall_state": overall_state,
        "summary": _action_review_path_health_summary(
            overall_state=overall_state,
            paths=paths,
        ),
        "paths": paths,
    }
