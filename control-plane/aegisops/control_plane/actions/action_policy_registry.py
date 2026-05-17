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
_MANUAL_FALLBACK_STATES = (
    "shuffle_unavailable",
    "execution_rejected",
    "missing_receipt",
    "stale_receipt",
    "mismatched_receipt",
)
_MANUAL_FALLBACK_RECORD_FIELDS = (
    "fallback_owner_id",
    "operator_note",
    "affected_action",
    "blocked_reason",
    "expected_evidence",
    "follow_up_state",
)
_MANUAL_FALLBACK_BLOCKED_REASON_TERMS = {
    "shuffle_unavailable": ("unavailable",),
    "execution_rejected": ("rejected",),
    "missing_receipt": ("missing",),
    "stale_receipt": ("stale",),
    "mismatched_receipt": ("mismatched", "mismatch"),
}
_NON_AUTHORITATIVE_EVIDENCE_SOURCE_TERMS = (
    ("shuffle",),
    ("workflow",),
    ("ticket",),
    ("ui",),
    ("browser",),
    ("ai",),
    ("verifier",),
    ("issue", "lint"),
    ("operator", "note"),
)
_NON_AUTHORITATIVE_EVIDENCE_AUTHORITY_TERMS = (
    ("authoritative",),
    ("authority",),
    ("truth",),
    ("confirms", "execution"),
    ("confirms", "receipt"),
    ("confirms", "reconciliation"),
    ("proves", "execution"),
    ("proves", "receipt"),
    ("proves", "reconciliation"),
    ("execution", "proof"),
    ("receipt", "proof"),
    ("reconciliation", "proof"),
)
_FOLLOW_UP_COMPLETION_OR_READINESS_TERMS = (
    "complete",
    "completed",
    "succeeded",
    "success",
    "successful",
    "closure",
    "closed",
    "close",
    "ready",
    "readiness",
    "reconciled",
    "reconciliation",
    "commercial",
    "replacement",
    "beta",
    "rc",
    "ga",
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

PHASE62_MANUAL_FALLBACK_REQUIREMENTS: Mapping[str, ManualFallbackRequirement] = {
    catalog_action: ManualFallbackRequirement(
        catalog_action=catalog_action,
        fallback_owner="explicit fallback owner required",
        operator_note_requirement=(
            "explicit operator note required; note remains subordinate guidance"
        ),
        affected_action=catalog_action,
        fallback_states=_MANUAL_FALLBACK_STATES,
        blocked_reason_requirement=(
            "explicit unavailable, rejected, missing, stale, or mismatched reason required"
        ),
        expected_evidence_requirement=(
            "bound AegisOps execution receipt and reconciliation review required"
        ),
        follow_up_state_requirement=(
            "explicit follow-up posture required; fallback cannot mark execution complete"
        ),
        required_record_fields=_MANUAL_FALLBACK_RECORD_FIELDS,
    )
    for catalog_action in PHASE62_ACTION_POLICIES
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


def validate_phase62_manual_fallback_record(
    *,
    catalog_action: str,
    record: Mapping[str, object],
) -> tuple[str, ...]:
    requirement = PHASE62_MANUAL_FALLBACK_REQUIREMENTS.get(catalog_action)
    if requirement is None:
        return ("unsupported_action",)

    errors: list[str] = []
    for field in requirement.required_record_fields:
        if not _non_blank_string(record.get(field)):
            errors.append(f"missing_{field}")

    affected_action = record.get("affected_action")
    if _non_blank_string(affected_action) and affected_action != requirement.affected_action:
        errors.append("affected_action_mismatch")

    fallback_state = record.get("fallback_state")
    if not _non_blank_string(fallback_state):
        errors.append("missing_fallback_state")
    elif fallback_state not in requirement.fallback_states:
        errors.append("unsupported_fallback_state")

    operator_note = str(record.get("operator_note") or "").lower()
    expected_evidence = str(record.get("expected_evidence") or "").lower()
    follow_up_state = str(record.get("follow_up_state") or "").lower()
    blocked_reason = str(record.get("blocked_reason") or "").lower()

    authority_promoting_terms = (
        "bypass",
        "proves execution",
        "execution truth",
        "reconciliation truth",
        "approval truth",
        "closes case",
        "successful execution",
    )
    if any(term in operator_note for term in authority_promoting_terms):
        errors.append("operator_note_promotes_authority")
    if any(term in expected_evidence for term in authority_promoting_terms):
        errors.append("expected_evidence_promotes_authority")
    if _promotes_non_authoritative_evidence(expected_evidence):
        errors.append("expected_evidence_promotes_non_authoritative_truth")
    follow_up_terms = _text_terms(follow_up_state)
    if any(
        term in follow_up_terms
        for term in _FOLLOW_UP_COMPLETION_OR_READINESS_TERMS
    ):
        errors.append("follow_up_state_promotes_completion")
    if "success" in blocked_reason:
        errors.append("blocked_reason_promotes_success")
    if (
        isinstance(fallback_state, str)
        and fallback_state in _MANUAL_FALLBACK_BLOCKED_REASON_TERMS
        and _non_blank_string(record.get("blocked_reason"))
        and not any(
            term in blocked_reason
            for term in _MANUAL_FALLBACK_BLOCKED_REASON_TERMS[fallback_state]
        )
    ):
        errors.append("blocked_reason_missing_failure_category")

    return tuple(dict.fromkeys(errors))


def _non_blank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _promotes_non_authoritative_evidence(value: str) -> bool:
    terms = _text_terms(value)
    has_untrusted_source = any(
        _contains_term_group(terms, source_terms)
        for source_terms in _NON_AUTHORITATIVE_EVIDENCE_SOURCE_TERMS
    )
    has_authority_claim = any(
        _contains_term_group(terms, authority_terms)
        for authority_terms in _NON_AUTHORITATIVE_EVIDENCE_AUTHORITY_TERMS
    )
    return has_untrusted_source and has_authority_claim


def _contains_term_group(terms: tuple[str, ...], required_terms: tuple[str, ...]) -> bool:
    return all(term in terms for term in required_terms)


def _text_terms(value: str) -> tuple[str, ...]:
    return tuple("".join(char if char.isalnum() else " " for char in value).split())


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
