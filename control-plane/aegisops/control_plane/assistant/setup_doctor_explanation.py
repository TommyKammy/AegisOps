from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .assistant_context import _advisory_text_claims_authority_or_scope_expansion
from .live_assistant_workflow import phase24_live_assistant_prompt_injection_flags
from ..runtime.doctor_contract import build_doctor_snapshot

_AGENT_NAME = "setup_doctor_explanation_agent"
_TOOL_NAME = "doctor_explanation"
_AUTHORITY_CEILING = "advisory_only"
_NEGATIVE_AUTHORITY = (
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "automatic_repair",
    "secret_mutation",
    "service_restart",
    "workflow_truth",
    "release_truth",
    "gate_truth",
)
_REGISTRY_CITATIONS = (
    "docs/automation/ai-agent-registry.json",
    "docs/automation/ai-tool-registry.json",
    "docs/automation/ai-disabled-degraded-mode-contract.json",
)
_REQUIRED_METRIC_MAPPINGS = (
    "alerts",
    "cases",
    "action_requests",
    "action_executions",
    "reconciliations",
    "source_health",
)
_POLICY_PRESSURE_TERMS = (
    "bypass policy",
    "bypass policies",
    "bypass the policy",
    "bypass tool policy",
    "disable policy",
    "disable the policy",
    "ignore policy",
    "ignore the policy",
    "override policy",
    "override the policy",
    "policy bypass",
)
_SETUP_REPAIR_PRESSURE_TERMS = (
    "repair",
    "repaired",
    "restart",
    "restarted",
    "rotate secret",
    "rotate secrets",
    "rotated secret",
    "rotated secrets",
    "mark the source posture healthy",
    "changed source posture",
)


def build_setup_doctor_explanation(
    *,
    config: Any,
    readiness_payload: Mapping[str, object],
    prompt_text: object = "",
) -> dict[str, object]:
    doctor = build_doctor_snapshot(
        config=config,
        readiness_payload=readiness_payload,
    ).to_dict()
    base = _base_payload(doctor)
    prompt_flags = _prompt_pressure_flags(prompt_text)
    if prompt_flags:
        return {
            **base,
            "decision": "blocked",
            "mode": "prompt_pressure_blocked",
            "unresolved_reasons": prompt_flags,
            "ai_generation_allowed": False,
            "trace_creation_allowed": False,
            "automatic_repair_allowed": False,
            "support_output_is_workflow_truth": False,
            "explanations": (),
        }

    ai_state = _doctor_state(doctor, "ai_enablement")
    ai_reason = ai_state.get("reason")
    if ai_reason == "ai_disabled":
        return {
            **base,
            "decision": "fallback",
            "mode": "ai_disabled",
            "unresolved_reasons": ("ai_advisory_disabled",),
            "ai_generation_allowed": False,
            "trace_creation_allowed": False,
            "non_ai_workflow_available": True,
            "explanations": _fallback_explanations(doctor, families=("ai_enablement",)),
        }
    if ai_reason == "ai_degraded":
        return {
            **base,
            "decision": "fallback",
            "mode": "ai_degraded",
            "unresolved_reasons": ("ai_advisory_degraded",),
            "ai_generation_allowed": False,
            "trace_creation_allowed": False,
            "non_ai_workflow_available": True,
            "explanations": _fallback_explanations(doctor, families=("ai_enablement",)),
        }
    if ai_reason != "ai_enabled":
        unresolved_reason = (
            ai_reason
            if isinstance(ai_reason, str) and ai_reason
            else "untrusted_ai_enablement_posture"
        )
        return {
            **base,
            "decision": "fallback",
            "mode": "ai_enablement_untrusted",
            "unresolved_reasons": (unresolved_reason,),
            "ai_generation_allowed": False,
            "trace_creation_allowed": False,
            "non_ai_workflow_available": True,
            "explanations": _fallback_explanations(doctor, families=("ai_enablement",)),
        }

    evidence_reasons = _doctor_evidence_unresolved_reasons(readiness_payload)
    if evidence_reasons:
        return {
            **base,
            "decision": "fallback",
            "mode": "doctor_evidence_missing",
            "unresolved_reasons": evidence_reasons,
            "ai_generation_allowed": False,
            "trace_creation_allowed": False,
            "non_ai_workflow_available": True,
            "explanations": _fallback_explanations(
                doctor,
                families=("control_plane", "database", "evidence_availability"),
            ),
        }

    explained_families = tuple(
        entry["state_family"]
        for entry in doctor.get("recommended_next_steps", ())
        if isinstance(entry, Mapping)
    )
    return {
        **base,
        "decision": "explain",
        "mode": "doctor_explanation",
        "unresolved_reasons": (),
        "ai_generation_allowed": True,
        "trace_creation_allowed": False,
        "non_ai_workflow_available": True,
        "explained_state_families": explained_families,
        "explanations": _fallback_explanations(doctor, families=explained_families),
    }


def _base_payload(doctor: Mapping[str, object]) -> dict[str, object]:
    states = doctor.get("states")
    state_families = tuple(states.keys()) if isinstance(states, Mapping) else ()
    citations = _dedupe_strings(
        (
            *_REGISTRY_CITATIONS,
            "docs/phase-58-1-aegisops-doctor-contract.md",
            "docs/phase-59-2-tool-registry-contract.md",
            "docs/phase-59-4-ai-disabled-degraded-mode-contract.md",
            *(f"doctor:{family}" for family in state_families),
        )
    )
    return {
        "read_only": True,
        "agent_name": _AGENT_NAME,
        "registered_tool_name": _TOOL_NAME,
        "record_families": ("doctor", "source_health", "runbook", "ai_trace"),
        "authority_ceiling": _AUTHORITY_CEILING,
        "authority_boundary": "cited_advisory_setup_doctor_explanation_only",
        "authoritative_workflow_truth": False,
        "mutates_authoritative_records": False,
        "automatic_repair_allowed": False,
        "support_output_is_workflow_truth": False,
        "negative_authority": _NEGATIVE_AUTHORITY,
        "citations": citations,
        "doctor_summary": doctor.get("summary", {}),
    }


def _doctor_state(
    doctor: Mapping[str, object],
    family: str,
) -> Mapping[str, object]:
    states = doctor.get("states")
    if not isinstance(states, Mapping):
        return {}
    state = states.get(family)
    return state if isinstance(state, Mapping) else {}


def _fallback_explanations(
    doctor: Mapping[str, object],
    *,
    families: tuple[object, ...],
) -> tuple[dict[str, object], ...]:
    explanations: list[dict[str, object]] = []
    for family in families:
        if not isinstance(family, str):
            continue
        state = _doctor_state(doctor, family)
        if not state:
            continue
        explanations.append(
            {
                "state_family": family,
                "posture": state.get("posture"),
                "reason": state.get("reason"),
                "explanation": state.get("explanation"),
                "safe_next_steps": state.get("safe_next_steps", ()),
                "support_link": state.get("support_link"),
                "citation_ids": (f"doctor:{family}",),
                "advisory_only": True,
            }
        )
    return tuple(explanations)


def _doctor_evidence_unresolved_reasons(
    readiness_payload: Mapping[str, object],
) -> tuple[str, ...]:
    metrics = readiness_payload.get("metrics")
    if not isinstance(metrics, Mapping):
        return ("missing_doctor_evidence",)
    if any(
        not isinstance(metrics.get(field), Mapping)
        for field in _REQUIRED_METRIC_MAPPINGS
    ):
        return ("malformed_doctor_metrics",)
    source_health = metrics.get("source_health")
    if (
        isinstance(source_health, Mapping)
        and "sources" in source_health
        and not isinstance(source_health.get("sources"), Mapping)
    ):
        return ("malformed_doctor_metrics",)
    return ()


def _prompt_pressure_flags(prompt_text: object) -> tuple[str, ...]:
    if not isinstance(prompt_text, str):
        return ("malformed_prompt_payload",)
    flags = _dedupe_strings(
        (
            *phase24_live_assistant_prompt_injection_flags(prompt_text),
            *_advisory_text_claims_authority_or_scope_expansion(prompt_text),
        )
    )
    lowered = prompt_text.lower()
    if any(term in lowered for term in _POLICY_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "tool_scope_expansion_attempt"))
    if any(term in lowered for term in _SETUP_REPAIR_PRESSURE_TERMS):
        flags = _dedupe_strings((*flags, "authority_overreach"))
    return flags


def _dedupe_strings(values: tuple[object, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value and value not in deduped:
            deduped.append(value)
    return tuple(deduped)


__all__ = ["build_setup_doctor_explanation"]
