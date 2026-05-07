from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .runtime_boundary import _is_missing_runtime_binding
from .service_snapshots import DoctorSnapshot

DOCTOR_POSTURE_SEMANTICS = (
    "available",
    "degraded",
    "unavailable",
    "not_applicable",
)

DOCTOR_STATE_FAMILIES = (
    "control_plane",
    "wazuh",
    "shuffle",
    "database",
    "proxy",
    "stale_source",
    "ai_enablement",
    "evidence_availability",
    "workflow_template",
    "execution_receipt",
)

_NEGATIVE_AUTHORITY = (
    "automatic_repair",
    "workflow_truth",
    "release_truth",
    "restore_truth",
    "gate_truth",
    "authoritative_record_mutation",
)

_POSTURE_SEVERITY = {
    "available": 0,
    "not_applicable": 0,
    "degraded": 1,
    "unavailable": 2,
}


def build_doctor_snapshot(
    *,
    config: Any,
    readiness_payload: Mapping[str, object],
) -> DoctorSnapshot:
    metrics = _mapping(readiness_payload.get("metrics"))
    states = {
        "control_plane": _control_plane_state(readiness_payload),
        "wazuh": _wazuh_state(config, metrics),
        "shuffle": _shuffle_state(config, metrics),
        "database": _database_state(readiness_payload),
        "proxy": _proxy_state(config),
        "stale_source": _stale_source_state(metrics),
        "ai_enablement": _ai_enablement_state(config),
        "evidence_availability": _evidence_availability_state(metrics),
        "workflow_template": _workflow_template_state(config, metrics),
        "execution_receipt": _execution_receipt_state(metrics),
    }
    overall_posture = _worst_posture(
        state["posture"] for state in states.values()
    )
    return DoctorSnapshot(
        read_only=True,
        contract="phase58_1_aegisops_doctor",
        authority_boundary="explanatory_subordinate",
        mutates_authoritative_records=False,
        posture_semantics=DOCTOR_POSTURE_SEMANTICS,
        summary={
            "overall_posture": overall_posture,
            "state_family_count": len(states),
            "source": "current_readiness_diagnostics_snapshot",
            "operator_action": (
                "review_degraded_or_unavailable_state_recommendations"
                if overall_posture in {"degraded", "unavailable"}
                else "continue_observing_without_mutation"
            ),
        },
        states=states,
        negative_authority=_NEGATIVE_AUTHORITY,
        recommended_next_steps=tuple(
            {
                "state_family": family,
                "posture": state["posture"],
                "action": state["recommended_action"],
            }
            for family, state in states.items()
            if state["posture"] in {"degraded", "unavailable"}
        ),
    )


def _control_plane_state(readiness_payload: Mapping[str, object]) -> dict[str, object]:
    status = readiness_payload.get("status")
    if status == "ready":
        return _state(
            "available",
            "readiness_ready",
            "Control-plane readiness admits runtime traffic.",
            "continue_observing_without_mutation",
        )
    if status in {"degraded", "stale"}:
        return _state(
            "degraded",
            f"readiness_{status}",
            "Control-plane readiness is degraded or stale.",
            "inspect_readiness_diagnostics_and_resolve_blockers",
        )
    return _state(
        "unavailable",
        "missing_or_untrusted_readiness_status",
        "Control-plane readiness is missing, malformed, or failing closed.",
        "restore_trusted_readiness_prerequisites_before_progression",
    )


def _wazuh_state(config: Any, metrics: Mapping[str, object]) -> dict[str, object]:
    source_health = _mapping(metrics.get("source_health"))
    sources = _mapping(source_health.get("sources"))
    wazuh_source = _mapping(sources.get("wazuh"))
    tracked_sources = _int_value(source_health.get("tracked_sources"))
    if _missing_config(config, "wazuh_ingest_shared_secret") or _missing_config(
        config,
        "wazuh_ingest_reverse_proxy_secret",
    ):
        return _state(
            "unavailable",
            "missing_wazuh_ingest_secret_or_proxy_secret",
            "Wazuh ingest cannot be trusted without both reviewed secrets.",
            "wire_reviewed_wazuh_secret_bindings",
        )
    if wazuh_source:
        source_state = str(wazuh_source.get("state", "")).strip()
        if source_state in {"degraded", "stale", "unresolved"}:
            return _state(
                "degraded",
                f"wazuh_source_{source_state}",
                "Wazuh source health is visible but degraded.",
                "refresh_wazuh_source_health_evidence",
            )
    return _state(
        "available",
        "wazuh_ingest_contract_configured",
        (
            "Wazuh ingest prerequisites are configured; no stale Wazuh source is currently reported."
            if tracked_sources
            else "Wazuh ingest prerequisites are configured"
        ),
        "continue_observing_without_mutation",
    )


def _shuffle_state(config: Any, metrics: Mapping[str, object]) -> dict[str, object]:
    executions = _mapping(metrics.get("action_executions"))
    active_count = sum(
        _int_value(executions.get(name)) for name in ("dispatching", "queued", "running")
    )
    if _missing_config(config, "shuffle_base_url"):
        if active_count:
            return _state(
                "unavailable",
                "missing_shuffle_binding_for_active_execution",
                "Active execution receipt review needs a configured Shuffle boundary.",
                "wire_reviewed_shuffle_binding_before_receipt_review",
            )
        return _state(
            "not_applicable",
            "no_active_shuffle_execution",
            "No active Shuffle execution is currently being diagnosed.",
            "no_operator_action",
        )
    return _state(
        "available",
        "shuffle_binding_configured",
        "Shuffle boundary is configured for execution receipt visibility.",
        "continue_observing_without_mutation",
    )


def _database_state(readiness_payload: Mapping[str, object]) -> dict[str, object]:
    if not isinstance(readiness_payload.get("metrics"), Mapping):
        return _state(
            "unavailable",
            "missing_readiness_metrics",
            "Database-backed readiness metrics are missing or malformed.",
            "restore_database_readiness_snapshot_before_progression",
        )
    return _state(
        "available",
        "readiness_metrics_loaded",
        "Database-backed readiness metrics were read without mutation.",
        "continue_observing_without_mutation",
    )


def _proxy_state(config: Any) -> dict[str, object]:
    host = str(getattr(config, "host", "")).strip()
    if host in {"127.0.0.1", "localhost", "::1"}:
        return _state(
            "available",
            "loopback_operator_surface",
            "Runtime surface is bound to loopback for local operation.",
            "continue_observing_without_mutation",
        )
    if _missing_config(config, "protected_surface_reverse_proxy_secret"):
        return _state(
            "unavailable",
            "missing_protected_surface_proxy_secret",
            "Non-loopback runtime access requires a reviewed proxy boundary.",
            "wire_reviewed_proxy_secret_before_exposure",
        )
    return _state(
        "available",
        "protected_surface_proxy_configured",
        "Protected-surface proxy boundary is configured.",
        "continue_observing_without_mutation",
    )


def _stale_source_state(metrics: Mapping[str, object]) -> dict[str, object]:
    source_health = _mapping(metrics.get("source_health"))
    tracked_sources = _int_value(source_health.get("tracked_sources"))
    overall_state = str(source_health.get("overall_state", "")).strip()
    if not tracked_sources:
        return _state(
            "not_applicable",
            "no_source_health_records",
            "No source-health records are currently tracked.",
            "no_operator_action",
        )
    if overall_state in {"degraded", "stale", "failed", "unknown"}:
        return _state(
            "degraded",
            f"source_health_{overall_state}",
            "Tracked source health is degraded, stale, or ambiguous.",
            "refresh_source_health_or_preserve_degraded_visibility",
        )
    return _state(
        "available",
        "source_health_current",
        "Tracked source health is current enough for visibility.",
        "continue_observing_without_mutation",
    )


def _ai_enablement_state(config: Any) -> dict[str, object]:
    posture = str(getattr(config, "ai_enablement_posture", "")).strip()
    if posture == "enabled":
        return _state(
            "available",
            "ai_enabled",
            "AI enablement posture is enabled.",
            "continue_observing_without_mutation",
        )
    if posture == "disabled":
        return _state(
            "not_applicable",
            "ai_disabled",
            "AI assistance is intentionally disabled.",
            "keep_ai_paths_subordinate_and_disabled",
        )
    if posture == "degraded":
        return _state(
            "degraded",
            "ai_degraded",
            "AI assistance is configured as degraded.",
            "preserve_manual_review_and_subordinate_ai_visibility",
        )
    return _state(
        "unavailable",
        "malformed_ai_enablement_posture",
        "AI posture is missing or malformed.",
        "correct_reviewed_ai_enablement_configuration",
    )


def _evidence_availability_state(metrics: Mapping[str, object]) -> dict[str, object]:
    alerts = _mapping(metrics.get("alerts"))
    cases = _mapping(metrics.get("cases"))
    tracked_records = _int_value(alerts.get("total")) + _int_value(cases.get("total"))
    if tracked_records:
        return _state(
            "available",
            "authoritative_records_have_evidence_surface",
            "Authoritative case or alert records are available for evidence inspection.",
            "continue_observing_without_mutation",
        )
    return _state(
        "not_applicable",
        "no_authoritative_records_requiring_evidence",
        "No case or alert records currently require evidence availability diagnosis.",
        "no_operator_action",
    )


def _workflow_template_state(config: Any, metrics: Mapping[str, object]) -> dict[str, object]:
    action_requests = _mapping(metrics.get("action_requests"))
    active_count = sum(
        _int_value(action_requests.get(name))
        for name in ("pending_approval", "approved", "executing", "unresolved")
    )
    if _missing_config(config, "n8n_base_url"):
        if active_count:
            return _state(
                "degraded",
                "missing_workflow_template_binding_for_active_review",
                "Active reviewed work exists without a configured workflow-template surface.",
                "verify_reviewed_workflow_template_binding",
            )
        return _state(
            "not_applicable",
            "no_active_workflow_template_review",
            "No active workflow template mismatch is currently diagnosed.",
            "no_operator_action",
        )
    return _state(
        "available",
        "workflow_template_surface_configured",
        "Workflow template surface is configured for reviewed checks.",
        "continue_observing_without_mutation",
    )


def _execution_receipt_state(metrics: Mapping[str, object]) -> dict[str, object]:
    executions = _mapping(metrics.get("action_executions"))
    reconciliations = _mapping(metrics.get("reconciliations"))
    active_execution_count = sum(
        _int_value(executions.get(name)) for name in ("dispatching", "queued", "running")
    )
    terminal_execution_count = _int_value(executions.get("terminal"))
    unresolved_reconciliation_count = sum(
        _int_value(reconciliations.get(name)) for name in ("pending", "mismatched", "stale")
    )
    if (
        _int_value(reconciliations.get("pending"))
        or _int_value(reconciliations.get("stale"))
        or _int_value(reconciliations.get("mismatched"))
    ):
        return _state(
            "degraded",
            "receipt_reconciliation_degraded",
            "Execution receipt reconciliation is pending, stale, or mismatched.",
            "obtain_authoritative_receipt_before_closeout",
        )
    if active_execution_count and not terminal_execution_count:
        return _state(
            "unavailable",
            "missing_execution_receipt_signal",
            "Execution is active without a terminal receipt signal.",
            "wait_for_or_collect_reviewed_execution_receipt",
        )
    if terminal_execution_count and not unresolved_reconciliation_count:
        return _state(
            "available",
            "execution_receipts_reconciled",
            "Execution receipts have no unresolved reconciliation state.",
            "continue_observing_without_mutation",
        )
    return _state(
        "not_applicable",
        "no_execution_receipt_under_review",
        "No execution receipt is currently under review.",
        "no_operator_action",
    )


def _state(
    posture: str,
    reason: str,
    explanation: str,
    recommended_action: str,
) -> dict[str, object]:
    if posture not in DOCTOR_POSTURE_SEMANTICS:
        posture = "unavailable"
        reason = "malformed_doctor_posture"
        recommended_action = "repair_doctor_contract_before_use"
    return {
        "posture": posture,
        "reason": reason,
        "explanation": explanation,
        "recommended_action": recommended_action,
        "authoritative": False,
    }


def _mapping(value: object) -> Mapping[str, object]:
    return value if isinstance(value, Mapping) else {}


def _int_value(value: object) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _missing_config(config: Any, field_name: str) -> bool:
    return _is_missing_runtime_binding(getattr(config, field_name, ""))


def _worst_posture(postures: object) -> str:
    normalized = [
        posture
        for posture in postures
        if isinstance(posture, str) and posture in DOCTOR_POSTURE_SEMANTICS
    ]
    if not normalized:
        return "unavailable"
    return max(
        normalized,
        key=lambda posture: _POSTURE_SEVERITY.get(posture, 2),
    )


__all__ = [
    "DOCTOR_POSTURE_SEMANTICS",
    "DOCTOR_STATE_FAMILIES",
    "build_doctor_snapshot",
]
