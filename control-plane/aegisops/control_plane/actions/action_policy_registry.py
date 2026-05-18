from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Mapping


ManualFallbackValidationErrors = tuple[str, ...]
SimulatorValidationErrors = tuple[str, ...]

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
    "shuffle_unavailable": (("unavailable",), ("timeout",), ("timed", "out")),
    "execution_rejected": (
        ("reject",),
        ("rejects",),
        ("rejected",),
        ("rejection",),
        ("rejecting",),
        ("cancel",),
        ("cancels",),
        ("canceled",),
        ("cancelled",),
        ("canceling",),
        ("cancelling",),
        ("cancellation",),
    ),
    "missing_receipt": (
        ("receipt", "missing"),
        ("missing", "receipt"),
        ("receipt", "absent"),
        ("absent", "receipt"),
        ("receipt", "missed"),
        ("missed", "receipt"),
    ),
    "stale_receipt": (("receipt", "stale"), ("stale", "receipt")),
    "mismatched_receipt": (
        ("receipt", "mismatched"),
        ("mismatched", "receipt"),
        ("receipt", "mismatch"),
        ("mismatch", "receipt"),
    ),
}
_NON_AUTHORITATIVE_EVIDENCE_SOURCE_BASE_TERMS = (
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
_NON_AUTHORITATIVE_EVIDENCE_SOURCE_TERMS = tuple(
    dict.fromkeys(
        (
            *_NON_AUTHORITATIVE_EVIDENCE_SOURCE_BASE_TERMS,
            *(
                (source_terms[-1], *source_terms[:-1])
                for source_terms in _NON_AUTHORITATIVE_EVIDENCE_SOURCE_BASE_TERMS
                if len(source_terms) > 1
            ),
        )
    )
)
_AUTHORITY_PROOF_VERBS = (
    "confirm",
    "confirms",
    "confirmed",
    "confirming",
    "prove",
    "proves",
    "proved",
    "proven",
    "proving",
    "validate",
    "validates",
    "validated",
    "validating",
)
_AUTHORITY_PROOF_OBJECTS = ("execution", "receipt", "reconciliation")
_AUTHORITY_PROOF_NOUNS = ("proof", "confirmation", "validation")
_APPROVAL_BYPASS_TERMS = ("bypass", "bypasses", "bypassed", "bypassing")
_CLOSURE_AUTHORITY_TERM_GROUPS = (
    ("close", "case"),
    ("closed", "case"),
    ("closes", "case"),
    ("closing", "case"),
    ("case", "close"),
    ("case", "closed"),
    ("case", "closes"),
    ("case", "closing"),
    ("case", "closure"),
    ("closure", "case"),
    ("close", "cases"),
    ("closed", "cases"),
    ("closes", "cases"),
    ("closing", "cases"),
    ("case", "closures"),
    ("cases", "close"),
    ("cases", "closed"),
    ("cases", "closes"),
    ("cases", "closing"),
    ("cases", "closure"),
    ("cases", "closures"),
    ("closure", "cases"),
    ("closures", "case"),
    ("closures", "cases"),
    ("close", "ticket"),
    ("closed", "ticket"),
    ("closes", "ticket"),
    ("closing", "ticket"),
    ("ticket", "close"),
    ("ticket", "closes"),
    ("ticket", "closed"),
    ("ticket", "closing"),
    ("ticket", "closure"),
    ("closure", "ticket"),
    ("close", "tickets"),
    ("closed", "tickets"),
    ("closes", "tickets"),
    ("closing", "tickets"),
    ("ticket", "closures"),
    ("tickets", "close"),
    ("tickets", "closed"),
    ("tickets", "closes"),
    ("tickets", "closing"),
    ("tickets", "closure"),
    ("tickets", "closures"),
    ("closure", "tickets"),
    ("closures", "ticket"),
    ("closures", "tickets"),
)
_AUTHORITY_PROOF_TERM_GROUPS = tuple(
    dict.fromkeys(
        (
            *(
                (verb, proof_object)
                for verb in _AUTHORITY_PROOF_VERBS
                for proof_object in _AUTHORITY_PROOF_OBJECTS
            ),
            *(
                (proof_object, verb)
                for verb in _AUTHORITY_PROOF_VERBS
                for proof_object in _AUTHORITY_PROOF_OBJECTS
            ),
            *(
                (proof_noun, proof_object)
                for proof_noun in _AUTHORITY_PROOF_NOUNS
                for proof_object in _AUTHORITY_PROOF_OBJECTS
            ),
            *(
                (proof_object, proof_noun)
                for proof_noun in _AUTHORITY_PROOF_NOUNS
                for proof_object in _AUTHORITY_PROOF_OBJECTS
            ),
        )
    )
)
_EXECUTION_SUCCESS_TERM_GROUPS = (
    ("execution", "succeed"),
    ("execution", "succeeds"),
    ("execution", "succeeding"),
    ("execution", "success"),
    ("execution", "successful"),
    ("execution", "succeeded"),
    ("succeed", "execution"),
    ("succeeds", "execution"),
    ("succeeding", "execution"),
    ("success", "execution"),
    ("successful", "execution"),
    ("succeeded", "execution"),
)
_NON_AUTHORITATIVE_EVIDENCE_AUTHORITY_TERMS = (
    ("authoritative",),
    ("authority",),
    ("truth",),
    *_AUTHORITY_PROOF_TERM_GROUPS,
    ("execution", "proof"),
    ("receipt", "proof"),
    ("reconciliation", "proof"),
)
_AUTHORITY_PROMOTING_TERM_GROUPS = (
    *((term,) for term in _APPROVAL_BYPASS_TERMS),
    *_AUTHORITY_PROOF_TERM_GROUPS,
    ("execution", "authority"),
    ("execution", "authoritative"),
    ("authority", "execution"),
    ("authoritative", "execution"),
    ("execution", "truth"),
    ("receipt", "truth"),
    ("reconciliation", "truth"),  # manual fallback notes cannot become truth records
    ("approval", "truth"),
    ("execution", "proof"),
    ("receipt", "proof"),
    ("reconciliation", "proof"),
    *_CLOSURE_AUTHORITY_TERM_GROUPS,
    *_EXECUTION_SUCCESS_TERM_GROUPS,
)
_FOLLOW_UP_LAUNCH_READINESS_TERMS = (
    "commercial",
    "beta",
    "rc",
    "ga",
)
_FOLLOW_UP_COMPLETION_OR_READINESS_TERMS = (
    "complete",
    "completes",
    "completed",
    "completing",
    "succeed",
    "succeeds",
    "succeeded",
    "succeeding",
    "success",
    "successful",
    "closes",
    "closure",
    "closed",
    "close",
    "closing",
    "ready",
    "readiness",
    "reconcile",
    "reconciles",
    "reconciled",
    "reconciling",
    "reconciliation",
    *_FOLLOW_UP_LAUNCH_READINESS_TERMS,
)
_NEGATION_TERMS = (
    "not",
    "no",
    "never",
    "cannot",
    "cant",
    "wont",
    "isnt",
    "arent",
    "wasnt",
    "werent",
    "dont",
    "doesnt",
    "didnt",
    "hasnt",
    "havent",
    "hadnt",
    "couldnt",
    "shouldnt",
    "wouldnt",
    "without",
)
_TERM_BOUNDARY = "boundary"
_TERM_COMMA_BOUNDARY = "comma_boundary"
_NEGATION_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    "and",
    "but",
    "however",
    "though",
    "although",
    "yet",
    "whereas",
    "while",
    "instead",
    "then",
    "or",
}
_TERM_GROUP_MAX_INTERVENING_TERMS = 6
_NEGATION_SCAN_WINDOW = 8
_SOURCE_AUTHORITY_ASSERTION_LINK_TERMS = {
    "is",
    "are",
    "was",
    "were",
    "be",
    "being",
    "been",
    "become",
    "becomes",
    "became",
    "can",
    "could",
    "show",
    "showed",
    "shows",
    "shown",
    "say",
    "said",
    "says",
    "state",
    "stated",
    "states",
    "will",
    "would",
}
_NEGATION_HARD_BOUNDARY_TERMS = {_TERM_BOUNDARY}
_NEGATION_CONTRAST_BOUNDARY_TERMS = {
    "although",
    "but",
    "however",
    "instead",
    "then",
    "though",
    "whereas",
    "while",
    "yet",
}
_NEGATION_LIST_BOUNDARY_TERMS = {"and", "or"}
_AUTHORITY_LINK_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    _TERM_COMMA_BOUNDARY,
    *_NEGATION_BOUNDARY_TERMS,
}
_AUTHORITY_CLAIM_CLAUSE_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    _TERM_COMMA_BOUNDARY,
    *_NEGATION_CONTRAST_BOUNDARY_TERMS,
}
_NEGATION_LIST_SUBJECT_TERMS = tuple(
    dict.fromkeys(
        term
        for term_group in (
            *_NON_AUTHORITATIVE_EVIDENCE_SOURCE_BASE_TERMS,
            ("approval",),
            ("case",),
            ("execution",),
            ("receipt",),
            ("reconciliation",),
            ("ticket",),
        )
        for term in term_group
    )
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

_SIMULATOR_OUTPUT_FIELDS = (
    "mode",
    "catalog_action",
    "action_request_id",
    "simulation_run_id",
    "reviewed_template_version",
    "correlation_id",
    "simulated_started_at",
    "simulated_finished_at",
    "simulated_status",
    "demo_test_label",
    "production_exclusion",
    "authority_posture",
    "live_secret_ref",
    "customer_data_classification",
    "simulated_evidence_ref",
)
_SIMULATOR_ALLOWED_STATUSES = (
    "simulated_success",
    "simulated_failure",
    "simulated_missing_receipt",
    "simulated_stale_receipt",
    "simulated_mismatched_receipt",
    "simulated_manual_review",
)
_SIMULATOR_ALLOWED_DATA_CLASSIFICATIONS = (
    "synthetic_only",
    "sanitized_demo_only",
)
_SIMULATOR_PRODUCTION_ARTIFACT_TRUTH_TERMS = (
    ("production", "execution", "receipt", "truth"),
    ("production", "execution", "receipt"),
    ("production", "reconciliation", "truth"),
    ("production", "receipt"),
    ("production", "reconciliation", "state"),
    ("execution", "receipt", "truth"),
    ("reconciliation", "truth"),
    ("production", "truth"),
)
_SIMULATOR_AUTHORITY_TRUTH_TERMS = (
    ("authority",),
    ("authoritative",),
    ("authoritatively",),
    ("authoritative", "execution"),
    ("authoritative", "receipt"),
    ("authoritative", "reconciliation"),
    ("authoritative", "truth"),
)
_SIMULATOR_CLOSURE_TRUTH_TERMS = (
    ("closure",),
    ("closed",),
    ("case", "truth"),
    ("case", "closure"),
    ("close", "case"),
    ("closes", "case"),
    ("closed", "case"),
    ("case", "closed"),
    ("ticket", "truth"),
    ("ticket", "closure"),
    ("close", "ticket"),
    ("closes", "ticket"),
    ("closed", "ticket"),
    ("ticket", "closed"),
)
_SIMULATOR_WORKFLOW_TRUTH_TERMS = (
    ("production", "workflow", "delegation"),
    ("production", "workflow", "delegate"),
    ("production", "workflow", "delegated"),
    ("delegation", "production", "workflow"),
    ("delegate", "production", "workflow"),
    ("delegate", "workflow", "production"),
    ("delegated", "production", "workflow"),
    ("delegated", "workflow", "production"),
    ("production", "workflow", "launch"),
    ("launch", "production", "workflow"),
    ("launch", "workflow", "production"),
    ("workflow", "launch", "production"),
)
_SIMULATOR_AD_HOC_EXECUTION_TRUTH_TERMS = (
    ("direct", "ad", "hoc", "execution"),
    ("ad", "hoc", "execution"),
    ("execution", "ad", "hoc"),
    ("direct", "execution"),
)
_SIMULATOR_READINESS_TRUTH_TERMS = (
    ("ready",),
    ("readiness",),
)
_SIMULATOR_PRODUCTION_TRUTH_TERMS = (
    *_SIMULATOR_PRODUCTION_ARTIFACT_TRUTH_TERMS,
    *_SIMULATOR_AUTHORITY_TRUTH_TERMS,
    *_SIMULATOR_CLOSURE_TRUTH_TERMS,
    *_SIMULATOR_WORKFLOW_TRUTH_TERMS,
    *_SIMULATOR_AD_HOC_EXECUTION_TRUTH_TERMS,
    *_SIMULATOR_READINESS_TRUTH_TERMS,
)
_SIMULATOR_EXCLUDABLE_PRODUCTION_TRUTH_TERMS = (
    ("production", "execution", "receipt", "truth"),
    ("production", "execution", "receipt"),
    ("production", "reconciliation", "truth"),
    ("production", "receipt"),
    ("execution", "receipt", "truth"),
    ("reconciliation", "truth"),
    ("production", "truth"),
)
_SIMULATOR_EXCLUSION_CONTEXT_TERMS = (
    "exclude",
    "excludes",
    "excluded",
    "excluding",
    "exclusion",
)
_SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS = (
    ("production", "execution", "receipt"),
    ("reconciliation", "truth"),
)
_SIMULATOR_EXCLUSION_CLAIM_BOUNDARY_TERMS = {
    _TERM_BOUNDARY,
    _TERM_COMMA_BOUNDARY,
    *_NEGATION_CONTRAST_BOUNDARY_TERMS,
    "therefore",
    "thus",
}

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

PHASE62_SIMULATOR_CONTRACTS: Mapping[str, SimulatorContract] = {
    catalog_action: SimulatorContract(
        catalog_action=catalog_action,
        allowed_modes=("demo", "test"),
        reviewed_template_version=mapping.reviewed_template_version,
        required_output_fields=_SIMULATOR_OUTPUT_FIELDS,
        allowed_statuses=_SIMULATOR_ALLOWED_STATUSES,
    )
    for catalog_action, mapping in PHASE62_SHUFFLE_WORKFLOW_MAPPINGS.items()
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
        (
            ("succeed",),
            ("succeeds",),
            ("succeeding",),
            ("success",),
            ("successful",),
            ("succeeded",),
        ),
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


def validate_phase62_simulator_output(
    *,
    catalog_action: str,
    output: Mapping[str, object],
) -> SimulatorValidationErrors:
    """Return fail-closed Phase 62.6 errors for demo/test simulator output."""
    contract = PHASE62_SIMULATOR_CONTRACTS.get(catalog_action)
    if contract is None:
        return ("unsupported_action",)

    errors: list[str] = []
    for field in contract.required_output_fields:
        if not _non_blank_string(output.get(field)):
            errors.append(f"missing_{field}")

    mode = output.get("mode")
    if _non_blank_string(mode):
        if mode not in contract.allowed_modes:
            errors.append("unsupported_mode")

    output_catalog_action = output.get("catalog_action")
    if _non_blank_string(output_catalog_action):
        if output_catalog_action != contract.catalog_action:
            errors.append("catalog_action_mismatch")

    reviewed_template_version = output.get("reviewed_template_version")
    if _non_blank_string(reviewed_template_version):
        if reviewed_template_version != contract.reviewed_template_version:
            errors.append("reviewed_template_version_mismatch")

    simulated_status = output.get("simulated_status")
    if _non_blank_string(simulated_status):
        if simulated_status not in contract.allowed_statuses:
            errors.append("unsupported_simulated_status")
        if _contains_unnegated_term_group(
            _text_terms(str(simulated_status)),
            _SIMULATOR_PRODUCTION_TRUTH_TERMS,
        ):
            errors.append("simulated_status_promotes_production_truth")

    demo_test_label = output.get("demo_test_label")
    if _non_blank_string(demo_test_label):
        label_terms = _text_terms(str(demo_test_label))
        if not (
            {"demo", "test"} & set(label_terms)
            and "evidence" in label_terms
            and any(term in {"only", "non", "non_authoritative"} for term in label_terms)
        ):
            errors.append("missing_demo_test_label")
        if _contains_simulator_production_truth_overclaim(label_terms):
            errors.append("demo_test_label_promotes_production_truth")

    production_exclusion = output.get("production_exclusion")
    if _non_blank_string(production_exclusion):
        exclusion_terms = _text_terms(str(production_exclusion))
        has_unnegated_exclusion_term = any(
            term in _SIMULATOR_EXCLUSION_CONTEXT_TERMS
            and not _has_recent_negation(
                exclusion_terms,
                index,
                window=_NEGATION_SCAN_WINDOW,
            )
            for index, term in enumerate(exclusion_terms)
        )
        has_production_exclusion_context = (
            has_unnegated_exclusion_term
            and "production" in exclusion_terms
            and all(
                _contains_unnegated_term_group(exclusion_terms, (term_group,))
                for term_group in _SIMULATOR_REQUIRED_PRODUCTION_EXCLUSION_TERM_GROUPS
            )
        )
        if not has_production_exclusion_context:
            errors.append("missing_production_exclusion")
        if _contains_simulator_production_truth_overclaim(exclusion_terms):
            errors.append("production_exclusion_promotes_production_truth")

    authority_posture = output.get("authority_posture")
    if _non_blank_string(authority_posture):
        if authority_posture != contract.authority_posture:
            errors.append("authority_posture_mismatch")

    live_secret_ref = output.get("live_secret_ref")
    if _non_blank_string(live_secret_ref) and live_secret_ref != "not_used":
        errors.append("live_secret_ref_forbidden")

    customer_data_classification = output.get("customer_data_classification")
    if _non_blank_string(customer_data_classification):
        if customer_data_classification not in _SIMULATOR_ALLOWED_DATA_CLASSIFICATIONS:
            errors.append("customer_data_forbidden")

    return tuple(dict.fromkeys(errors))


def require_phase62_simulator_output(
    *,
    catalog_action: str,
    output: Mapping[str, object],
) -> None:
    errors = validate_phase62_simulator_output(
        catalog_action=catalog_action,
        output=output,
    )
    if errors:
        raise ValueError(
            "simulator output violates Phase 62.6 contract: " + ", ".join(errors)
        )


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
        source_matches = _term_group_matches(terms, source_terms)
        if not source_matches:
            continue
        if any(
            _source_promotes_non_authoritative_evidence(
                terms=terms,
                source_match=source_match,
            )
            for source_match in source_matches
        ):
            return True
    return False


def _source_promotes_non_authoritative_evidence(
    *,
    terms: tuple[str, ...],
    source_match: tuple[int, ...],
) -> bool:
    source_index = source_match[0]
    source_end = source_match[-1] + 1
    for authority_terms in _NON_AUTHORITATIVE_EVIDENCE_AUTHORITY_TERMS:
        for authority_match in _term_group_matches(terms, authority_terms):
            authority_index = authority_match[0]
            if any(
                _has_recent_negation(terms, match_index, window=3)
                for match_index in authority_match
            ):
                continue
            if _has_source_scoped_negation_before_authority(
                terms=terms,
                source_index=source_index,
                source_end=source_end,
                authority_index=authority_index,
            ):
                continue
            if _authority_claim_matches_source(
                terms=terms,
                source_index=source_index,
                source_end=source_end,
                authority_index=authority_index,
                authority_terms=authority_terms,
            ):
                return True
    return False


def _has_source_scoped_negation_before_authority(
    *,
    terms: tuple[str, ...],
    source_index: int,
    source_end: int,
    authority_index: int,
) -> bool:
    if authority_index <= source_end:
        return False
    for negation_index in range(authority_index - 1, source_end - 1, -1):
        term = terms[negation_index]
        if term in _NEGATION_BOUNDARY_TERMS:
            return False
        if term in _NEGATION_TERMS:
            return not _is_not_only_phrase(terms, negation_index, authority_index)
    return False


def _authority_claim_matches_source(
    *,
    terms: tuple[str, ...],
    source_index: int,
    source_end: int,
    authority_index: int,
    authority_terms: tuple[str, ...],
) -> bool:
    authority_end = authority_index + len(authority_terms)
    if source_index <= authority_index:
        between = terms[source_end:authority_index]
        if any(term in _AUTHORITY_CLAIM_CLAUSE_BOUNDARY_TERMS for term in between):
            return False
        list_boundaries = [
            index for index, term in enumerate(between) if term in {"and", "or"}
        ]
        if list_boundaries and any(
            term in _NEGATION_LIST_SUBJECT_TERMS
            for term in between[list_boundaries[-1] + 1 :]
        ):
            return False
        targets_aegisops_receipt = _authority_claim_targets_aegisops_receipt(
            terms=terms,
            source_end=source_end,
            authority_index=authority_index,
            authority_end=authority_end,
        )
        if targets_aegisops_receipt and not _source_is_directly_asserted_as_authority(
            between
        ):
            return False
        if source_end == authority_index:
            return True
        if list_boundaries:
            return True
        return _source_is_directly_asserted_as_authority(between)

    between = terms[authority_end:source_index]
    if any(
        term in {_TERM_COMMA_BOUNDARY, *_NEGATION_BOUNDARY_TERMS}
        for term in between
    ):
        return False
    if source_index - authority_end <= 3 and not any(
        term in {"aegisops", "bound"} for term in terms[authority_index:source_end]
    ):
        return True
    return any(
        term
        in {
            "from",
            "via",
            "using",
            "through",
            "by",
            "based",
            "comes",
            "come",
            "coming",
            "derived",
        }
        for term in between
    )


def _authority_claim_targets_aegisops_receipt(
    *,
    terms: tuple[str, ...],
    source_end: int,
    authority_index: int,
    authority_end: int,
) -> bool:
    authority_anchor_start = max(source_end, authority_index - 3)
    authority_anchor = terms[
        authority_anchor_start : min(len(terms), authority_end + 4)
    ]
    return any(term in {"aegisops", "bound"} for term in authority_anchor)


def _source_is_directly_asserted_as_authority(
    between_source_and_authority: tuple[str, ...],
) -> bool:
    if any(
        term in _AUTHORITY_LINK_BOUNDARY_TERMS
        for term in between_source_and_authority
    ):
        return False
    return any(
        term in _SOURCE_AUTHORITY_ASSERTION_LINK_TERMS
        for term in between_source_and_authority
    )


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
            not any(
                _has_recent_negation(terms, index, window=_NEGATION_SCAN_WINDOW)
                for index in match
            )
            for match in _term_group_matches(terms, term_group)
        ):
            return True
    return False


def _contains_simulator_production_truth_overclaim(terms: tuple[str, ...]) -> bool:
    for term_group in _SIMULATOR_PRODUCTION_TRUTH_TERMS:
        for match in _term_group_matches(terms, term_group):
            if any(
                _has_recent_negation(terms, index, window=_NEGATION_SCAN_WINDOW)
                for index in match
            ):
                continue
            if term_group in {
                ("authority",),
                ("authoritative",),
            } and _has_non_authoritative_prefix(terms, match[0]):
                continue
            if (
                term_group in _SIMULATOR_EXCLUDABLE_PRODUCTION_TRUTH_TERMS
                and _has_recent_simulator_exclusion_context(terms, match[0])
            ):
                continue
            return True
    return False


def _has_non_authoritative_prefix(
    terms: tuple[str, ...],
    target_index: int,
) -> bool:
    return target_index > 0 and terms[target_index - 1] == "non"


def _has_recent_simulator_exclusion_context(
    terms: tuple[str, ...],
    target_index: int,
) -> bool:
    start = max(0, target_index - _NEGATION_SCAN_WINDOW)
    for context_index in range(target_index - 1, start - 1, -1):
        term = terms[context_index]
        if term == _TERM_COMMA_BOUNDARY:
            if any(
                link_term in _SOURCE_AUTHORITY_ASSERTION_LINK_TERMS
                for link_term in terms[context_index + 1 : target_index]
            ):
                return False
            continue
        if term in _SIMULATOR_EXCLUSION_CLAIM_BOUNDARY_TERMS:
            return False
        if term in _SIMULATOR_EXCLUSION_CONTEXT_TERMS:
            if any(
                link_term in _SOURCE_AUTHORITY_ASSERTION_LINK_TERMS
                for link_term in terms[context_index + 1 : target_index]
            ):
                return False
            return True
    return False


def _contains_unnegated_single_term(
    terms: tuple[str, ...],
    target_terms: tuple[str, ...],
) -> bool:
    for index, term in enumerate(terms):
        if term in target_terms and not _has_recent_negation(
            terms,
            index,
            window=_NEGATION_SCAN_WINDOW,
        ):
            return True
    return False


def _term_group_starts(
    terms: tuple[str, ...],
    required_terms: tuple[str, ...],
) -> tuple[int, ...]:
    return tuple(match[0] for match in _term_group_matches(terms, required_terms))


def _term_group_matches(
    terms: tuple[str, ...],
    required_terms: tuple[str, ...],
) -> tuple[tuple[int, ...], ...]:
    if not required_terms or len(required_terms) > len(terms):
        return ()
    matches: list[tuple[int, ...]] = []

    def matches_from(
        term_index: int,
        required_index: int,
        matched_indexes: tuple[int, ...],
    ) -> None:
        if required_index == len(required_terms):
            matches.append(matched_indexes)
            return
        next_term = required_terms[required_index]
        max_next_index = min(
            len(terms),
            term_index + _TERM_GROUP_MAX_INTERVENING_TERMS + 2,
        )
        for next_index in range(term_index + 1, max_next_index):
            if terms[next_index] in {_TERM_BOUNDARY, _TERM_COMMA_BOUNDARY}:
                break
            if _term_matches_required(terms[next_index], next_term):
                matches_from(
                    next_index,
                    required_index + 1,
                    (*matched_indexes, next_index),
                )

    for index, term in enumerate(terms):
        if not _term_matches_required(term, required_terms[0]):
            continue
        matches_from(index, 1, (index,))
    return tuple(matches)


def _term_matches_required(term: str, required_term: str) -> bool:
    if term == required_term:
        return True
    if len(required_term) <= 2 or required_term.endswith("s"):
        return False
    if term == f"{required_term}s":
        return True
    if required_term.endswith(("s", "x", "ch", "sh")) and term == f"{required_term}es":
        return True
    if required_term.endswith("y") and term == f"{required_term[:-1]}ies":
        return True
    return False


def _has_recent_negation(
    terms: tuple[str, ...],
    index: int,
    *,
    window: int,
) -> bool:
    start = max(0, index - window)
    for negation_index in range(index - 1, start - 1, -1):
        term = terms[negation_index]
        if term in _NEGATION_HARD_BOUNDARY_TERMS:
            return False
        if term in _NEGATION_CONTRAST_BOUNDARY_TERMS:
            return False
        if (
            term in {_TERM_COMMA_BOUNDARY, *_NEGATION_LIST_BOUNDARY_TERMS}
            and _list_boundary_starts_new_subject(
                terms=terms,
                boundary_index=negation_index,
                target_index=index,
            )
        ):
            return False
        if term in _NEGATION_TERMS:
            if _is_not_only_phrase(terms, negation_index, index):
                continue
            return True
    return False


def _is_not_only_phrase(
    terms: tuple[str, ...],
    negation_index: int,
    target_index: int,
) -> bool:
    return (
        terms[negation_index] == "not"
        and negation_index + 1 < target_index
        and terms[negation_index + 1] == "only"
    )


def _list_boundary_starts_new_subject(
    *,
    terms: tuple[str, ...],
    boundary_index: int,
    target_index: int,
) -> bool:
    if terms[boundary_index] == "and" and _TERM_COMMA_BOUNDARY not in terms[
        max(0, boundary_index - _NEGATION_SCAN_WINDOW) : boundary_index
    ]:
        return True
    if any(
        term in {_TERM_COMMA_BOUNDARY, *_NEGATION_LIST_BOUNDARY_TERMS}
        for term in terms[boundary_index + 1 : target_index]
    ):
        return False
    return any(
        term in _NEGATION_LIST_SUBJECT_TERMS
        for term in terms[boundary_index + 1 : target_index + 1]
    )


def _text_terms(value: str) -> tuple[str, ...]:
    normalized = (
        value.lower()
        .replace("n't", " not")
        .replace("n\u2019t", " not")
        .replace("n\u2018t", " not")
    )
    return _tokenize_with_boundaries(normalized)


def _tokenize_with_boundaries(value: str) -> tuple[str, ...]:
    characters: list[str] = []
    for char in value:
        if char.isalnum():
            characters.append(char)
        elif char == ",":
            characters.append(f" {_TERM_COMMA_BOUNDARY} ")
        elif char in ".;:!?":
            characters.append(f" {_TERM_BOUNDARY} ")
        else:
            characters.append(" ")
    return tuple("".join(characters).split())


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
