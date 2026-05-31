from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from .action_policy_catalog import (
    ACTION_TYPE_POLICY_ALIASES,
    PHASE62_ACTION_POLICIES,
    PHASE62_MANUAL_FALLBACK_REQUIREMENTS,
    PHASE62_SHUFFLE_WORKFLOW_MAPPINGS,
    PHASE62_SIMULATOR_CONTRACTS,
    _LEGACY_ACTION_TYPE_SHUFFLE_MAPPINGS,
)
from .action_policy_manual_fallback import (
    require_phase62_manual_fallback_record,
    validate_phase62_manual_fallback_record,
)
from .action_policy_simulator_validation import (
    require_phase62_simulator_output,
    validate_phase62_simulator_output,
)
from .action_policy_types import (
    ActionPolicy,
    ActionPolicyDecision,
    ManualFallbackRequirement,
    ManualFallbackValidationErrors,
    ShuffleWorkflowMapping,
    SimulatorContract,
    SimulatorValidationErrors,
)


_ROLE_ALIASES = {
    "read-only-auditor": "read_only_auditor",
    "readonly-auditor": "read_only_auditor",
    "read-only": "read_only_auditor",
    "platform-admin": "platform_admin",
    "platform": "platform_admin",
}
_KNOWN_ROLE_PREFIXES = (
    ("read-only-auditor-", "read_only_auditor"),
    ("readonly-auditor-", "read_only_auditor"),
    ("platform-admin-", "platform_admin"),
    ("analyst-", "analyst"),
    ("approver-", "approver"),
)


def reviewed_shuffle_workflow_mapping_for_action_type(
    action_type: str,
) -> ShuffleWorkflowMapping | None:
    if action_type in _LEGACY_ACTION_TYPE_SHUFFLE_MAPPINGS:
        return _LEGACY_ACTION_TYPE_SHUFFLE_MAPPINGS[action_type]
    catalog_action = ACTION_TYPE_POLICY_ALIASES.get(action_type, action_type)
    return PHASE62_SHUFFLE_WORKFLOW_MAPPINGS.get(catalog_action)


def validate_phase62_shuffle_workflow_mapping(
    *,
    catalog_action: str,
    workflow_template_id: str,
    reviewed_template_version: str,
    family: str,
    required_inputs: tuple[str, ...],
    expected_outputs: tuple[str, ...],
    correlation_fields: tuple[str, ...],
    policy_registry_id: str,
    review_status: str,
    import_eligible: bool,
) -> tuple[str, ...]:
    reviewed_mapping = PHASE62_SHUFFLE_WORKFLOW_MAPPINGS.get(catalog_action)
    reviewed_policy = PHASE62_ACTION_POLICIES.get(catalog_action)
    errors: list[str] = []
    if reviewed_mapping is None or reviewed_policy is None:
        return ("unsupported_action",)
    if not workflow_template_id:
        errors.append("missing_template")
    elif workflow_template_id != reviewed_mapping.workflow_template_id:
        errors.append("template_mismatch")
    if reviewed_template_version != reviewed_mapping.reviewed_template_version:
        errors.append("version_mismatch")
    if review_status != "reviewed" or not import_eligible:
        errors.append("unreviewed_template")
    if family != reviewed_policy.family:
        errors.append("family_mismatch")
    if policy_registry_id != reviewed_policy.registry_id:
        errors.append("policy_incompatibility")
    reviewed_required_inputs = set(reviewed_mapping.required_inputs)
    candidate_required_inputs = set(required_inputs)
    if reviewed_required_inputs - candidate_required_inputs:
        errors.append("missing_required_input")
    if candidate_required_inputs - reviewed_required_inputs:
        errors.append("unexpected_required_input")
    reviewed_expected_outputs = set(reviewed_mapping.expected_outputs)
    candidate_expected_outputs = set(expected_outputs)
    if reviewed_expected_outputs - candidate_expected_outputs:
        errors.append("missing_expected_output")
    if candidate_expected_outputs - reviewed_expected_outputs:
        errors.append("unexpected_expected_output")
    reviewed_correlation_fields = set(reviewed_policy.correlation_fields)
    candidate_correlation_fields = set(correlation_fields)
    if reviewed_correlation_fields - candidate_correlation_fields:
        errors.append("missing_correlation")
    if candidate_correlation_fields - reviewed_correlation_fields:
        errors.append("unexpected_correlation")
    return tuple(dict.fromkeys(errors))


def requester_role_from_identity(identity: str) -> str:
    normalized = identity.strip().lower()
    if not normalized:
        return ""
    for prefix, role in _KNOWN_ROLE_PREFIXES:
        if normalized.startswith(prefix):
            return role
    role_hint = normalized.rsplit("-", 1)[0]
    return _ROLE_ALIASES.get(role_hint, role_hint.replace("-", "_"))


def evaluate_phase62_action_policy(
    *,
    action_type: str,
    requester_identity: str,
    target_scope: Mapping[str, object],
    expires_at: datetime | None,
    idempotency_key: str | None,
    now: datetime | None = None,
) -> ActionPolicyDecision:
    catalog_action = ACTION_TYPE_POLICY_ALIASES.get(action_type, action_type)
    policy = PHASE62_ACTION_POLICIES.get(catalog_action)
    if policy is None:
        policy = ActionPolicy(
            catalog_action=catalog_action,
            family="unreviewed",
            approval_requirement="denied",
            allowed_requester_roles=(),
            allowed_reviewer_roles=(),
            allowed_target_scope="none",
            idempotency_required=True,
            protected_target_posture="denied",
            expected_receipt_fields=(),
            correlation_fields=(),
            reconciliation_outcomes=("manual_review",),
            registry_id=f"phase62.2:{catalog_action}:missing",
            denied_by_default=True,
        )

    requester_role = requester_role_from_identity(requester_identity)
    denial_reasons: list[str] = []
    if policy.denied_by_default:
        denial_reasons.append("missing_reviewed_policy")
    if requester_role not in policy.allowed_requester_roles:
        denial_reasons.append("requester_role_not_allowed")
    if expires_at is None:
        denial_reasons.append("missing_expiry")
    else:
        comparison_now = now or datetime.now(timezone.utc)
        if expires_at <= comparison_now:
            denial_reasons.append("policy_expired")
    if policy.idempotency_required and not idempotency_key:
        denial_reasons.append("missing_idempotency_key")
    denial_reasons.extend(_target_scope_denial_reasons(policy, target_scope))

    return ActionPolicyDecision(
        policy=policy,
        requester_role=requester_role,
        decision="denied" if denial_reasons else "allowed",
        denial_reasons=tuple(denial_reasons),
    )


def _target_scope_denial_reasons(
    policy: ActionPolicy,
    target_scope: Mapping[str, object],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if (
        target_scope.get("protected_target") is True
        and policy.protected_target_posture != "approval_required_for_follow_up"
    ):
        reasons.append("protected_target_misuse")

    if policy.catalog_action == "create_tracking_ticket":
        if target_scope.get("coordination_target_type") not in ("zammad", "glpi"):
            reasons.append("target_scope_not_allowed")
        if not target_scope.get("coordination_reference_id"):
            reasons.append("target_scope_not_allowed")
    elif policy.catalog_action == "operator_notification":
        if not target_scope.get("recipient_identity"):
            reasons.append("target_scope_not_allowed")
    elif policy.catalog_action == "manual_escalation_request":
        if not target_scope.get("escalation_owner_ref"):
            reasons.append("target_scope_not_allowed")
    elif policy.catalog_action == "enrichment_only_lookup":
        if not target_scope.get("lookup_subject_ref"):
            reasons.append("target_scope_not_allowed")

    return tuple(dict.fromkeys(reasons))
