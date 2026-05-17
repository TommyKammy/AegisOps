from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


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


_COMMON_RECEIPT_FIELDS = (
    "action_request_id",
    "catalog_action",
    "family",
    "reviewed_template_version",
    "correlation_id",
    "idempotency_key",
    "execution_run_id",
    "started_at",
    "finished_at",
    "status",
)
_COMMON_CORRELATION_FIELDS = (
    "action_request_id",
    "approval_decision_id",
    "delegation_id",
    "execution_run_id",
    "correlation_id",
    "expected_execution_receipt_id",
    "idempotency_key",
)
_COMMON_RECONCILIATION_OUTCOMES = (
    "success",
    "failure",
    "missing",
    "stale",
    "mismatched",
    "duplicate",
    "wrong_correlation",
    "manual_review",
)


PHASE62_ACTION_POLICIES: Mapping[str, ActionPolicy] = {
    "enrichment_only_lookup": ActionPolicy(
        catalog_action="enrichment_only_lookup",
        family="Read",
        approval_requirement="policy_not_required",
        allowed_requester_roles=("analyst", "approver"),
        allowed_reviewer_roles=("approver",),
        allowed_target_scope="single_lookup_subject",
        idempotency_required=True,
        protected_target_posture="mutation_forbidden",
        expected_receipt_fields=_COMMON_RECEIPT_FIELDS
        + ("lookup_subject_ref", "lookup_evidence_ref"),
        correlation_fields=_COMMON_CORRELATION_FIELDS + ("lookup_subject_ref",),
        reconciliation_outcomes=_COMMON_RECONCILIATION_OUTCOMES,
        registry_id="phase62.2:enrichment_only_lookup",
    ),
    "operator_notification": ActionPolicy(
        catalog_action="operator_notification",
        family="Notify",
        approval_requirement="policy_not_required",
        allowed_requester_roles=("analyst", "approver"),
        allowed_reviewer_roles=("approver",),
        allowed_target_scope="single_recipient",
        idempotency_required=True,
        protected_target_posture="mutation_forbidden",
        expected_receipt_fields=_COMMON_RECEIPT_FIELDS
        + ("recipient_ref", "delivery_attempt_status", "normalized_receipt_ref"),
        correlation_fields=_COMMON_CORRELATION_FIELDS + ("recipient_ref",),
        reconciliation_outcomes=_COMMON_RECONCILIATION_OUTCOMES,
        registry_id="phase62.2:operator_notification",
    ),
    "manual_escalation_request": ActionPolicy(
        catalog_action="manual_escalation_request",
        family="Notify",
        approval_requirement="human_required_for_protected_follow_up",
        allowed_requester_roles=("analyst", "approver"),
        allowed_reviewer_roles=("approver",),
        allowed_target_scope="single_escalation_owner",
        idempotency_required=True,
        protected_target_posture="approval_required_for_follow_up",
        expected_receipt_fields=_COMMON_RECEIPT_FIELDS
        + ("escalation_owner_ref", "delivery_attempt_status", "fallback_needed"),
        correlation_fields=_COMMON_CORRELATION_FIELDS + ("escalation_owner_ref",),
        reconciliation_outcomes=_COMMON_RECONCILIATION_OUTCOMES,
        registry_id="phase62.2:manual_escalation_request",
    ),
    "create_tracking_ticket": ActionPolicy(
        catalog_action="create_tracking_ticket",
        family="Soft Write",
        approval_requirement="human_required",
        allowed_requester_roles=("analyst", "approver"),
        allowed_reviewer_roles=("approver",),
        allowed_target_scope="single_external_ticket",
        idempotency_required=True,
        protected_target_posture="mutation_forbidden",
        expected_receipt_fields=_COMMON_RECEIPT_FIELDS
        + (
            "approval_decision_id",
            "ticket_pointer_id",
            "ticket_system_id",
            "ticket_pointer_custody",
            "delivery_status",
            "normalized_receipt_ref",
        ),
        correlation_fields=_COMMON_CORRELATION_FIELDS
        + ("coordination_reference_id", "coordination_target_type"),
        reconciliation_outcomes=_COMMON_RECONCILIATION_OUTCOMES,
        registry_id="phase62.2:create_tracking_ticket",
    ),
}

ACTION_TYPE_POLICY_ALIASES = {
    "notify_identity_owner": "operator_notification",
}

_COMMON_SHUFFLE_REQUIRED_INPUTS = (
    "action_request_id",
    "approval_decision_id",
    "correlation_id",
    "reviewed_template_version",
    "requested_by",
    "callback_url",
    "callback_secret_ref",
)
_COMMON_SHUFFLE_EXPECTED_OUTPUTS = (
    "action_request_id",
    "approval_decision_id",
    "correlation_id",
    "execution_receipt_id",
    "normalized_receipt_ref",
    "reviewed_template_version",
    "execution_status",
    "execution_started_at",
    "execution_finished_at",
)

PHASE62_SHUFFLE_WORKFLOW_MAPPINGS: Mapping[str, ShuffleWorkflowMapping] = {
    "enrichment_only_lookup": ShuffleWorkflowMapping(
        catalog_action="enrichment_only_lookup",
        workflow_template_id="enrichment_only_lookup",
        reviewed_template_version="enrichment_only_lookup-v1-reviewed-2026-05-03",
        family="Read",
        required_inputs=_COMMON_SHUFFLE_REQUIRED_INPUTS
        + ("lookup_subject_id", "enrichment_scope"),
        expected_outputs=_COMMON_SHUFFLE_EXPECTED_OUTPUTS + ("lookup_result_ref",),
        correlation_fields=PHASE62_ACTION_POLICIES[
            "enrichment_only_lookup"
        ].correlation_fields,
        policy_registry_id="phase62.2:enrichment_only_lookup",
    ),
    "operator_notification": ShuffleWorkflowMapping(
        catalog_action="operator_notification",
        workflow_template_id="operator_notification",
        reviewed_template_version="operator_notification-v1-reviewed-2026-05-03",
        family="Notify",
        required_inputs=_COMMON_SHUFFLE_REQUIRED_INPUTS
        + ("operator_recipient_id", "notification_scope"),
        expected_outputs=_COMMON_SHUFFLE_EXPECTED_OUTPUTS
        + ("notification_delivery_ref",),
        correlation_fields=PHASE62_ACTION_POLICIES[
            "operator_notification"
        ].correlation_fields,
        policy_registry_id="phase62.2:operator_notification",
    ),
    "manual_escalation_request": ShuffleWorkflowMapping(
        catalog_action="manual_escalation_request",
        workflow_template_id="manual_escalation_request",
        reviewed_template_version="manual_escalation_request-v1-reviewed-2026-05-03",
        family="Notify",
        required_inputs=_COMMON_SHUFFLE_REQUIRED_INPUTS
        + ("escalation_subject_id", "escalation_owner_id", "escalation_scope"),
        expected_outputs=_COMMON_SHUFFLE_EXPECTED_OUTPUTS
        + ("manual_escalation_request_ref",),
        correlation_fields=PHASE62_ACTION_POLICIES[
            "manual_escalation_request"
        ].correlation_fields,
        policy_registry_id="phase62.2:manual_escalation_request",
    ),
    "create_tracking_ticket": ShuffleWorkflowMapping(
        catalog_action="create_tracking_ticket",
        workflow_template_id="create_tracking_ticket",
        reviewed_template_version="create_tracking_ticket-v1-reviewed-2026-05-03",
        family="Soft Write",
        required_inputs=_COMMON_SHUFFLE_REQUIRED_INPUTS
        + (
            "ticket_pointer_id",
            "ticket_system_id",
            "ticket_pointer_custody",
            "ticket_coordination_scope",
        ),
        expected_outputs=_COMMON_SHUFFLE_EXPECTED_OUTPUTS
        + ("ticket_pointer_id", "ticket_system_id", "ticket_pointer_custody"),
        correlation_fields=PHASE62_ACTION_POLICIES[
            "create_tracking_ticket"
        ].correlation_fields,
        policy_registry_id="phase62.2:create_tracking_ticket",
    ),
}

_LEGACY_ACTION_TYPE_SHUFFLE_MAPPINGS: Mapping[str, ShuffleWorkflowMapping] = {
    "notify_identity_owner": ShuffleWorkflowMapping(
        catalog_action="operator_notification",
        workflow_template_id="notify_identity_owner",
        reviewed_template_version="notify_identity_owner-v1-reviewed-2026-05-03",
        family="Notify",
        required_inputs=_COMMON_SHUFFLE_REQUIRED_INPUTS
        + ("recipient_identity_owner_id", "message_scope"),
        expected_outputs=_COMMON_SHUFFLE_EXPECTED_OUTPUTS,
        correlation_fields=PHASE62_ACTION_POLICIES[
            "operator_notification"
        ].correlation_fields,
        policy_registry_id="phase62.2:operator_notification",
    ),
}


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
    for field_name in reviewed_mapping.required_inputs:
        if field_name not in required_inputs:
            errors.append("missing_required_input")
            break
    for field_name in reviewed_mapping.expected_outputs:
        if field_name not in expected_outputs:
            errors.append("missing_expected_output")
            break
    for field_name in reviewed_policy.correlation_fields:
        if field_name not in correlation_fields:
            errors.append("missing_correlation")
            break
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
