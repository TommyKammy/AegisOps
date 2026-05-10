from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .doctor_contract import build_doctor_snapshot

_SUPPORTABILITY_ROLES = {"support_operator"}
_SUMMARY_NEGATIVE_AUTHORITY = (
    "workflow_truth",
    "release_truth",
    "gate_truth",
    "restore_truth",
    "closeout_truth",
    "automatic_repair",
    "live_restore_execution",
    "live_upgrade_execution",
    "live_rollback_execution",
    "phase59_or_later_completion",
)
_POSTURE_SEVERITY = {
    "healthy": 0,
    "degraded": 1,
    "stale": 2,
    "unavailable": 3,
    "denied": 4,
}


def build_supportability_summary(
    *,
    service: Any,
    role: str,
    restore_backup_payload: Mapping[str, object] | None = None,
    restore_expected_source_revision: str | None = None,
    restore_expected_profile: str | None = None,
    restore_max_age_hours: int | None = None,
) -> dict[str, object]:
    normalized_role = role.strip().lower()
    if normalized_role not in _SUPPORTABILITY_ROLES:
        return _denied_summary(normalized_role or "missing")

    doctor = _doctor_state(service)
    backup = _backup_state(service)
    restore = _restore_dry_run_state(
        service=service,
        restore_backup_payload=restore_backup_payload,
        restore_expected_source_revision=restore_expected_source_revision,
        restore_expected_profile=restore_expected_profile,
        restore_max_age_hours=restore_max_age_hours,
    )
    states = {
        "doctor": doctor,
        "backup": backup,
        "restore_dry_run": restore,
        "upgrade_rollback_plan": _contract_only_state(
            reason="phase58_5_contract_only_no_reviewed_plan_input",
            support_link="docs/phase-58-5-upgrade-rollback-plan-contract.md",
            safe_next_step="supply_reviewed_upgrade_or_rollback_plan_evidence_before_maintenance_review",
        ),
        "support_bundle_redaction": _contract_only_state(
            reason="phase58_6_contract_only_no_redaction_manifest_input",
            support_link="docs/phase-58-6-support-bundle-redaction-contract.md",
            safe_next_step="supply_reviewed_redaction_manifest_before_retaining_support_bundle",
        ),
    }
    overall_posture = _worst_posture(state["posture"] for state in states.values())
    return {
        "read_only": True,
        "contract": "phase58_7_supportability_summary",
        "authority_boundary": "operator_diagnostic_context_only",
        "mutates_authoritative_records": False,
        "access": {
            "role": normalized_role,
            "decision": "allowed",
            "support_diagnostics": "read_only",
        },
        "summary": {
            "overall_posture": overall_posture,
            "operator_action": (
                "review_bounded_safe_next_actions_without_mutation"
                if overall_posture != "healthy"
                else "continue_observing_without_mutation"
            ),
        },
        "states": states,
        "safe_next_actions": _safe_next_actions(states),
        "summary_claims": {
            "workflow_truth": False,
            "release_truth": False,
            "gate_truth": False,
            "restore_truth": False,
            "closeout_truth": False,
            "phase59_or_later_completion": False,
        },
        "negative_authority": _SUMMARY_NEGATIVE_AUTHORITY,
    }


def _denied_summary(role: str) -> dict[str, object]:
    states = {
        state: _state(
            "denied",
            "role_not_allowed_for_supportability_summary",
            "Supportability summary access requires the reviewed support diagnostics role.",
            "request_reviewed_support_operator_access",
            "docs/phase-57-1-rbac-role-matrix-contract.md",
        )
        for state in (
            "doctor",
            "backup",
            "restore_dry_run",
            "upgrade_rollback_plan",
            "support_bundle_redaction",
        )
    }
    return {
        "read_only": True,
        "contract": "phase58_7_supportability_summary",
        "authority_boundary": "operator_diagnostic_context_only",
        "mutates_authoritative_records": False,
        "access": {
            "role": role,
            "decision": "denied",
            "support_diagnostics": "denied",
        },
        "summary": {
            "overall_posture": "denied",
            "operator_action": "request_reviewed_support_diagnostics_access",
        },
        "states": states,
        "safe_next_actions": _safe_next_actions(states),
        "summary_claims": {
            "workflow_truth": False,
            "release_truth": False,
            "gate_truth": False,
            "restore_truth": False,
            "closeout_truth": False,
            "phase59_or_later_completion": False,
        },
        "negative_authority": _SUMMARY_NEGATIVE_AUTHORITY,
    }


def _doctor_state(service: Any) -> dict[str, object]:
    try:
        doctor = build_doctor_snapshot(
            config=service._config,
            readiness_payload=service.inspect_readiness_diagnostics().to_dict(),
        ).to_dict()
    except (LookupError, ValueError, AttributeError, TypeError) as exc:
        return _state(
            "unavailable",
            "doctor_snapshot_unavailable",
            "Doctor state could not be reread from the reviewed backend surface.",
            "restore_doctor_prerequisites_before_treating_supportability_as_available",
            "docs/phase-58-1-aegisops-doctor-contract.md",
            detail=str(exc),
        )
    posture = str(doctor.get("summary", {}).get("overall_posture", "unavailable"))
    return _state(
        _doctor_posture(posture),
        f"doctor_{posture}",
        "Doctor state was reread from current readiness diagnostics.",
        "review_doctor_recommendations_without_mutation",
        "docs/phase-58-1-aegisops-doctor-contract.md",
        detail={
            "doctor_contract": doctor.get("contract"),
            "doctor_operator_action": doctor.get("summary", {}).get("operator_action"),
        },
    )


def _backup_state(service: Any) -> dict[str, object]:
    try:
        backup = service.export_authoritative_record_chain_backup()
    except (LookupError, ValueError, AttributeError, TypeError) as exc:
        return _state(
            "unavailable",
            "backup_manifest_unavailable",
            "Backup posture could not be reread from the reviewed backup command path.",
            "repair_backup_prerequisites_before_claiming_custody_evidence",
            "docs/phase-58-3-backup-command-contract.md",
            detail=str(exc),
        )
    manifest = backup.get("backup_manifest") if isinstance(backup, Mapping) else None
    if not isinstance(manifest, Mapping):
        return _state(
            "unavailable",
            "missing_backup_manifest",
            "Backup posture is missing the reviewed custody manifest.",
            "rerun_backup_command_and_preserve_custody_manifest",
            "docs/phase-58-3-backup-command-contract.md",
        )
    return _state(
        "healthy",
        "backup_manifest_available",
        "Backup custody posture is available as subordinate recovery evidence.",
        "retain_backup_manifest_as_custody_evidence_only",
        "docs/phase-58-3-backup-command-contract.md",
        detail={
            "authority_boundary": manifest.get("authority_boundary"),
            "total_record_count": manifest.get("total_record_count"),
        },
    )


def _restore_dry_run_state(
    *,
    service: Any,
    restore_backup_payload: Mapping[str, object] | None,
    restore_expected_source_revision: str | None,
    restore_expected_profile: str | None,
    restore_max_age_hours: int | None,
) -> dict[str, object]:
    if restore_backup_payload is None:
        return _state(
            "unavailable",
            "missing_restore_dry_run_input",
            "Restore dry-run posture requires an explicit reviewed backup payload input.",
            "provide_reviewed_backup_payload_before_restore_preflight_summary",
            "docs/phase-58-4-restore-dry-run-contract.md",
        )
    try:
        diagnostics_service = service._runtime_restore_readiness_diagnostics_service
        dry_run = diagnostics_service.dry_run_authoritative_record_chain_restore(
            restore_backup_payload,
            expected_source_revision=restore_expected_source_revision,
            expected_profile=restore_expected_profile,
            max_age_hours=restore_max_age_hours,
        )
    except ValueError as exc:
        reason = str(exc)
        return _state(
            "stale" if "stale" in reason else "unavailable",
            _restore_failure_reason(reason),
            "Restore dry-run posture failed closed before any durable write.",
            "refresh_reviewed_backup_or_restore_prerequisites_before_live_restore_review",
            "docs/phase-58-4-restore-dry-run-contract.md",
            detail=reason,
        )
    except (LookupError, AttributeError, TypeError) as exc:
        return _state(
            "unavailable",
            "restore_dry_run_unavailable",
            "Restore dry-run posture could not be evaluated through the reviewed diagnostics path.",
            "restore_dry_run_prerequisites_before_claiming_restore_readiness",
            "docs/phase-58-4-restore-dry-run-contract.md",
            detail=str(exc),
        )
    return _state(
        "healthy",
        "restore_dry_run_clean",
        "Restore dry-run posture is clean subordinate preflight evidence.",
        "retain_dry_run_output_as_preflight_evidence_only",
        "docs/phase-58-4-restore-dry-run-contract.md",
        detail={
            "dry_run_state": dry_run.get("dry_run_state"),
            "can_prove_live_restore_completion": dry_run.get(
                "can_prove_live_restore_completion"
            ),
        },
    )


def _contract_only_state(
    *,
    reason: str,
    support_link: str,
    safe_next_step: str,
) -> dict[str, object]:
    return _state(
        "unavailable",
        reason,
        "Only the reviewed Phase 58 contract exists; no runtime evidence input was supplied.",
        safe_next_step,
        support_link,
    )


def _state(
    posture: str,
    reason: str,
    explanation: str,
    safe_next_step: str,
    support_link: str,
    *,
    detail: object | None = None,
) -> dict[str, object]:
    state = {
        "posture": posture,
        "reason": reason,
        "explanation": explanation,
        "safe_next_steps": (safe_next_step, "do_not_mutate_authoritative_records"),
        "support_link": support_link,
        "authoritative": False,
    }
    if detail is not None:
        state["detail"] = detail
    return state


def _safe_next_actions(
    states: Mapping[str, Mapping[str, object]],
) -> tuple[dict[str, object], ...]:
    return tuple(
        {
            "state": name,
            "posture": state["posture"],
            "actions": state["safe_next_steps"],
            "support_link": state["support_link"],
        }
        for name, state in states.items()
        if state["posture"] != "healthy"
    )


def _doctor_posture(posture: str) -> str:
    if posture == "available":
        return "healthy"
    if posture in {"degraded", "unavailable"}:
        return posture
    return "unavailable"


def _restore_failure_reason(reason: str) -> str:
    if "stale" in reason:
        return "restore_dry_run_snapshot_stale"
    if reason:
        return "restore_dry_run_failed_closed"
    return "restore_dry_run_unavailable"


def _worst_posture(postures: Iterable[object]) -> str:
    return max(
        (str(posture) for posture in postures),
        key=lambda posture: _POSTURE_SEVERITY.get(posture, 3),
        default="unavailable",
    )
