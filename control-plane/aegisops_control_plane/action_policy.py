from __future__ import annotations

from typing import Mapping

from .models import ActionRequestRecord

ACTION_POLICY_ALLOWED_VALUES: dict[str, tuple[str, ...]] = {
    "severity": ("low", "medium", "high", "critical"),
    "target_scope": (
        "single_identity",
        "single_asset",
        "multi_identity",
        "multi_asset",
        "fleet",
        "organization",
    ),
    "action_reversibility": (
        "reversible",
        "bounded_reversible",
        "irreversible",
    ),
    "asset_criticality": ("standard", "elevated", "high", "critical"),
    "identity_criticality": ("standard", "elevated", "high", "critical"),
    "blast_radius": (
        "single_target",
        "bounded_group",
        "multi_target",
        "organization",
    ),
    "execution_constraint": (
        "routine_allowed",
        "isolated_preferred",
        "requires_isolated_executor",
    ),
}

ACTION_POLICY_RANKS: dict[str, dict[str, int]] = {
    field_name: {
        allowed_value: index for index, allowed_value in enumerate(allowed_values)
    }
    for field_name, allowed_values in ACTION_POLICY_ALLOWED_VALUES.items()
}


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def normalize_action_policy_basis(
    policy_basis: Mapping[str, object],
) -> dict[str, str]:
    normalized: dict[str, str] = {}
    for field_name, allowed_values in ACTION_POLICY_ALLOWED_VALUES.items():
        raw_value = policy_basis.get(field_name)
        value = _require_non_empty_string(raw_value, f"policy_basis.{field_name}")
        if value not in allowed_values:
            raise ValueError(
                f"policy_basis.{field_name} must be one of {list(allowed_values)!r}"
            )
        normalized[field_name] = value
    return normalized


def determine_action_policy(
    policy_basis: Mapping[str, str],
) -> dict[str, str]:
    severity_rank = ACTION_POLICY_RANKS["severity"][policy_basis["severity"]]
    target_scope_rank = ACTION_POLICY_RANKS["target_scope"][
        policy_basis["target_scope"]
    ]
    reversibility_rank = ACTION_POLICY_RANKS["action_reversibility"][
        policy_basis["action_reversibility"]
    ]
    blast_radius_rank = ACTION_POLICY_RANKS["blast_radius"][
        policy_basis["blast_radius"]
    ]
    highest_criticality_rank = max(
        ACTION_POLICY_RANKS["asset_criticality"][policy_basis["asset_criticality"]],
        ACTION_POLICY_RANKS["identity_criticality"][
            policy_basis["identity_criticality"]
        ],
    )
    execution_constraint = policy_basis["execution_constraint"]

    requires_isolated_executor = any(
        (
            execution_constraint == "requires_isolated_executor",
            severity_rank >= ACTION_POLICY_RANKS["severity"]["critical"],
            reversibility_rank
            >= ACTION_POLICY_RANKS["action_reversibility"]["irreversible"],
            blast_radius_rank >= ACTION_POLICY_RANKS["blast_radius"]["organization"],
            highest_criticality_rank
            >= ACTION_POLICY_RANKS["asset_criticality"]["critical"],
            target_scope_rank >= ACTION_POLICY_RANKS["target_scope"]["organization"],
        )
    )
    if execution_constraint == "isolated_preferred" and any(
        (
            severity_rank >= ACTION_POLICY_RANKS["severity"]["high"],
            blast_radius_rank >= ACTION_POLICY_RANKS["blast_radius"]["multi_target"],
            highest_criticality_rank
            >= ACTION_POLICY_RANKS["asset_criticality"]["high"],
        )
    ):
        requires_isolated_executor = True

    approval_required = any(
        (
            requires_isolated_executor,
            severity_rank >= ACTION_POLICY_RANKS["severity"]["high"],
            target_scope_rank >= ACTION_POLICY_RANKS["target_scope"]["multi_identity"],
            reversibility_rank
            >= ACTION_POLICY_RANKS["action_reversibility"]["bounded_reversible"],
            blast_radius_rank >= ACTION_POLICY_RANKS["blast_radius"]["multi_target"],
            highest_criticality_rank >= ACTION_POLICY_RANKS["asset_criticality"]["high"],
        )
    )

    if requires_isolated_executor:
        execution_surface_type = "executor"
        execution_surface_id = "isolated-executor"
    else:
        execution_surface_type = "automation_substrate"
        execution_surface_id = "shuffle"

    return {
        "approval_requirement": (
            "human_required" if approval_required else "policy_authorized"
        ),
        "routing_target": (
            "approval"
            if approval_required
            else (
                "shuffle"
                if execution_surface_type == "automation_substrate"
                else "executor"
            )
        ),
        "execution_surface_type": execution_surface_type,
        "execution_surface_id": execution_surface_id,
    }


def apply_action_policy_evaluation_overrides(
    *,
    computed_policy_evaluation: Mapping[str, str],
    persisted_policy_evaluation: Mapping[str, object],
) -> dict[str, str]:
    merged = dict(computed_policy_evaluation)
    approval_requirement_override = persisted_policy_evaluation.get(
        "approval_requirement_override"
    )
    if approval_requirement_override is None:
        return merged

    normalized_override = _require_non_empty_string(
        approval_requirement_override,
        "policy_evaluation.approval_requirement_override",
    )
    if normalized_override != "human_required":
        raise ValueError(
            "policy_evaluation.approval_requirement_override must be "
            "'human_required'"
        )

    merged["approval_requirement"] = "human_required"
    merged["routing_target"] = "approval"
    merged["approval_requirement_override"] = normalized_override
    return merged


def evaluate_action_policy_record(
    action_request: ActionRequestRecord,
) -> ActionRequestRecord:
    normalized_policy_basis = normalize_action_policy_basis(action_request.policy_basis)
    policy_evaluation = apply_action_policy_evaluation_overrides(
        computed_policy_evaluation=determine_action_policy(normalized_policy_basis),
        persisted_policy_evaluation=action_request.policy_evaluation,
    )
    return ActionRequestRecord(
        action_request_id=action_request.action_request_id,
        approval_decision_id=action_request.approval_decision_id,
        case_id=action_request.case_id,
        alert_id=action_request.alert_id,
        finding_id=action_request.finding_id,
        idempotency_key=action_request.idempotency_key,
        target_scope=action_request.target_scope,
        payload_hash=action_request.payload_hash,
        requested_at=action_request.requested_at,
        expires_at=action_request.expires_at,
        lifecycle_state=action_request.lifecycle_state,
        requester_identity=action_request.requester_identity,
        requested_payload=action_request.requested_payload,
        policy_basis=normalized_policy_basis,
        policy_evaluation=policy_evaluation,
    )
