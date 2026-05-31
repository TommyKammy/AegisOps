from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


ManualFallbackValidationErrors = tuple[str, ...]
SimulatorValidationErrors = tuple[str, ...]


@dataclass(frozen=True)
class ActionPolicy:
    catalog_action: str
    family: str
    approval_requirement: str
    allowed_requester_roles: tuple[str, ...]
    allowed_reviewer_roles: tuple[str, ...]
    allowed_target_scope: str
    idempotency_required: bool
    protected_target_posture: str
    expected_receipt_fields: tuple[str, ...]
    correlation_fields: tuple[str, ...]
    reconciliation_outcomes: tuple[str, ...]
    registry_id: str
    denied_by_default: bool = False


@dataclass(frozen=True)
class ShuffleWorkflowMapping:
    catalog_action: str
    workflow_template_id: str
    reviewed_template_version: str
    family: str
    required_inputs: tuple[str, ...]
    expected_outputs: tuple[str, ...]
    correlation_fields: tuple[str, ...]
    policy_registry_id: str
    review_status: str = "reviewed"
    import_eligible: bool = True


@dataclass(frozen=True)
class ManualFallbackRequirement:
    catalog_action: str
    fallback_owner: str
    operator_note_requirement: str
    affected_action: str
    fallback_states: tuple[str, ...]
    blocked_reason_requirement: str
    expected_evidence_requirement: str
    follow_up_state_requirement: str
    required_record_fields: tuple[str, ...]
    manual_fallback_role: str = "subordinate_guidance"
    approval_bypass: str = "forbidden"
    execution_truth: str = "execution_receipt_required"
    reconciliation_truth: str = "aegisops_reconciliation_required"


@dataclass(frozen=True)
class SimulatorContract:
    catalog_action: str
    allowed_modes: tuple[str, ...]
    reviewed_template_version: str
    required_output_fields: tuple[str, ...]
    allowed_statuses: tuple[str, ...]
    authority_posture: str = "non_authoritative_demo_test_evidence"
    production_exclusion: str = (
        "excluded_from_production_execution_receipt_and_reconciliation_truth"
    )
    secret_posture: str = "live_secrets_forbidden"
    data_posture: str = "synthetic_or_sanitized_only"


@dataclass(frozen=True)
class ActionPolicyDecision:
    policy: ActionPolicy
    requester_role: str
    decision: str
    denial_reasons: tuple[str, ...]

    @property
    def allowed(self) -> bool:
        return self.decision == "allowed"

    def as_policy_basis(self) -> dict[str, object]:
        return {
            "policy_registry_id": self.policy.registry_id,
            "catalog_action": self.policy.catalog_action,
            "family": self.policy.family,
            "allowed_requester_roles": self.policy.allowed_requester_roles,
            "allowed_reviewer_roles": self.policy.allowed_reviewer_roles,
            "allowed_target_scope": self.policy.allowed_target_scope,
            "idempotency_required": self.policy.idempotency_required,
            "protected_target_posture": self.policy.protected_target_posture,
            "expected_receipt_fields": self.policy.expected_receipt_fields,
            "correlation_fields": self.policy.correlation_fields,
            "reconciliation_outcomes": self.policy.reconciliation_outcomes,
        }

    def as_policy_evaluation(self) -> dict[str, object]:
        routing_target = (
            "approval"
            if self.policy.approval_requirement.startswith("human_required")
            else "request"
        )
        return {
            "policy_registry_id": self.policy.registry_id,
            "policy_decision": self.decision,
            "denial_reasons": self.denial_reasons,
            "requester_role": self.requester_role,
            "approval_requirement": self.policy.approval_requirement,
            "approval_requirement_override": self.policy.approval_requirement,
            "routing_target": routing_target,
            "execution_surface_type": "automation_substrate",
            "execution_surface_id": "shuffle",
        }
