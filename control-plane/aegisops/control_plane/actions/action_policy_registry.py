from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


ManualFallbackValidationErrors = tuple[str, ...]

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
    "fallback_state",
    "blocked_reason",
    "expected_evidence",
    "follow_up_state",  # required alongside fallback_state for schema checklists
)
_MANUAL_FALLBACK_BLOCKED_REASON_CATEGORIES = {
    "shuffle_unavailable": (("unavailable",),),
    "execution_rejected": (("rejected",),),
    "missing_receipt": (("missing",),),
    "stale_receipt": (("stale",),),
    "mismatched_receipt": (("mismatched",), ("mismatch",)),
}
_NON_AUTHORITATIVE_EVIDENCE_SOURCE_TERMS = (
    ("shuffle", "result"),
    ("shuffle", "state"),
    ("shuffle", "output"),
    ("workflow", "result"),
    ("workflow", "state"),
    ("workflow", "output"),
    ("ticket", "output"),
    ("ticket", "state"),
    ("ticket", "report"),
    ("ui", "cache"),
    ("ui", "state"),
    ("ui", "output"),
    ("browser", "state"),
    ("browser", "output"),
    ("ai", "output"),
    ("ai", "result"),
    ("verifier", "output"),
    ("verifier", "result"),
    ("issue", "lint", "output"),
    ("issue", "lint", "report"),
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
    ("validates", "execution"),
    ("validates", "receipt"),
    ("validates", "reconciliation"),
    ("execution", "proof"),
    ("receipt", "proof"),
    ("reconciliation", "proof"),
)
_AUTHORITY_PROMOTING_TERM_GROUPS = (
    ("bypass",),
    ("confirms", "execution"),
    ("confirms", "receipt"),
    ("confirms", "reconciliation"),
    ("proves", "execution"),
    ("proves", "receipt"),
    ("proves", "reconciliation"),
    ("validates", "execution"),
    ("validates", "receipt"),
    ("validates", "reconciliation"),
    ("execution", "authority"),
    ("execution", "truth"),
    ("receipt", "truth"),
    ("reconciliation", "truth"),  # manual fallback notes cannot become truth records
    ("approval", "truth"),
    ("execution", "proof"),
    ("receipt", "proof"),
    ("reconciliation", "proof"),
    ("closes", "case"),
    ("successful", "execution"),
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
_NEGATION_TERMS = ("not", "no", "never", "cannot", "cant", "wont", "without")


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
) -> ManualFallbackValidationErrors:
    """Return fail-closed Phase 62.5 errors for a candidate fallback record."""
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

    operator_note_terms = _text_terms(operator_note)
    expected_evidence_terms = _text_terms(expected_evidence)
    if _contains_unnegated_term_group(
        operator_note_terms,
        _AUTHORITY_PROMOTING_TERM_GROUPS,
    ):
        errors.append("operator_note_promotes_authority")
    if _contains_unnegated_term_group(
        expected_evidence_terms,
        _AUTHORITY_PROMOTING_TERM_GROUPS,
    ):
        errors.append("expected_evidence_promotes_authority")
    if _promotes_non_authoritative_evidence(expected_evidence):
        errors.append("expected_evidence_promotes_non_authoritative_truth")
    follow_up_terms = _text_terms(follow_up_state)
    if _contains_unnegated_single_term(
        follow_up_terms,
        _FOLLOW_UP_COMPLETION_OR_READINESS_TERMS,
    ):
        errors.append("follow_up_state_promotes_completion")
    blocked_reason_terms = _text_terms(blocked_reason)
    if _contains_unnegated_term_group(
        blocked_reason_terms,
        (("success",), ("successful",)),
    ):
        errors.append("blocked_reason_promotes_success")
    if (
        isinstance(fallback_state, str)
        and fallback_state in _MANUAL_FALLBACK_BLOCKED_REASON_CATEGORIES
        and _non_blank_string(record.get("blocked_reason"))
        and not _blocked_reason_matches_declared_failure_category(
            fallback_state=fallback_state,
            blocked_reason=blocked_reason,
        )
    ):
        errors.append("blocked_reason_missing_failure_category")

    return tuple(dict.fromkeys(errors))


def require_phase62_manual_fallback_record(
    *,
    catalog_action: str,
    record: Mapping[str, object],
) -> None:
    errors = validate_phase62_manual_fallback_record(
        catalog_action=catalog_action,
        record=record,
    )
    if errors:
        raise ValueError(
            "manual fallback violates Phase 62.5 contract: " + ", ".join(errors)
        )


def _non_blank_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _promotes_non_authoritative_evidence(value: str) -> bool:
    terms = _text_terms(value)
    for source_terms in _NON_AUTHORITATIVE_EVIDENCE_SOURCE_TERMS:
        source_indexes = _term_group_starts(terms, source_terms)
        if not source_indexes:
            continue
        for authority_terms in _NON_AUTHORITATIVE_EVIDENCE_AUTHORITY_TERMS:
            authority_indexes = _term_group_starts(terms, authority_terms)
            if not authority_indexes:
                continue
            if any(
                not _has_recent_negation(terms, authority_index, window=3)
                for authority_index in authority_indexes
            ):
                return True
    return False


def _blocked_reason_matches_declared_failure_category(
    *,
    fallback_state: str,
    blocked_reason: str,
) -> bool:
    terms = _text_terms(blocked_reason)
    return any(
        _contains_unnegated_term_group(
            terms,
            (category_terms,),
        )
        for category_terms in _MANUAL_FALLBACK_BLOCKED_REASON_CATEGORIES[
            fallback_state
        ]
    )


def _contains_unnegated_term_group(
    terms: tuple[str, ...],
    term_groups: tuple[tuple[str, ...], ...],
) -> bool:
    for term_group in term_groups:
        if any(
            not _has_recent_negation(terms, index, window=4)
            for index in _term_group_starts(terms, term_group)
        ):
            return True
    return False


def _contains_unnegated_single_term(
    terms: tuple[str, ...],
    target_terms: tuple[str, ...],
) -> bool:
    for index, term in enumerate(terms):
        if term in target_terms and not _has_recent_negation(terms, index, window=4):
            return True
    return False


def _term_group_starts(
    terms: tuple[str, ...],
    required_terms: tuple[str, ...],
) -> tuple[int, ...]:
    if not required_terms or len(required_terms) > len(terms):
        return ()
    indexes: list[int] = []
    for index, term in enumerate(terms):
        if term != required_terms[0]:
            continue
        search_from = index + 1
        matched = True
        for required_term in required_terms[1:]:
            try:
                next_index = terms.index(required_term, search_from)
            except ValueError:
                matched = False
                break
            if next_index - search_from > 4:
                matched = False
                break
            search_from = next_index + 1
        if matched:
            indexes.append(index)
    return tuple(indexes)


def _has_recent_negation(
    terms: tuple[str, ...],
    index: int,
    *,
    window: int,
) -> bool:
    start = max(0, index - window)
    return any(term in _NEGATION_TERMS for term in terms[start:index])


def _text_terms(value: str) -> tuple[str, ...]:
    normalized = (
        value.replace("can't", "cant")
        .replace("Can't", "Cant")
        .replace("won't", "wont")
        .replace("Won't", "Wont")
    )
    return tuple(
        "".join(char if char.isalnum() else " " for char in normalized).split()
    )


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
