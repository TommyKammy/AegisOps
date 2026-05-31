from __future__ import annotations

from typing import Mapping

from .action_policy_types import (
    ActionPolicy,
    ManualFallbackRequirement,
    ShuffleWorkflowMapping,
    SimulatorContract,
)


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
