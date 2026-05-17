from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.actions.action_policy_registry import (  # noqa: E402
    PHASE62_ACTION_POLICIES,
    PHASE62_MANUAL_FALLBACK_REQUIREMENTS,
    PHASE62_SHUFFLE_WORKFLOW_MAPPINGS,
    evaluate_phase62_action_policy,
    validate_phase62_manual_fallback_record,
    validate_phase62_shuffle_workflow_mapping,
)


class Phase62ActionPolicyRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 5, 17, 8, 30, tzinfo=timezone.utc)

    def test_registry_contains_reviewed_phase62_actions(self) -> None:
        self.assertEqual(
            set(PHASE62_ACTION_POLICIES),
            {
                "enrichment_only_lookup",
                "operator_notification",
                "manual_escalation_request",
                "create_tracking_ticket",
            },
        )
        self.assertEqual(
            PHASE62_ACTION_POLICIES["create_tracking_ticket"].registry_id,
            "phase62.2:create_tracking_ticket",
        )
        self.assertEqual(
            PHASE62_ACTION_POLICIES["create_tracking_ticket"].allowed_reviewer_roles,
            ("approver",),
        )
        for policy in PHASE62_ACTION_POLICIES.values():
            self.assertIn("correlation_id", policy.expected_receipt_fields)
            self.assertIn("expected_execution_receipt_id", policy.correlation_fields)
            self.assertEqual(
                policy.reconciliation_outcomes,
                (
                    "success",
                    "failure",
                    "missing",
                    "stale",
                    "mismatched",
                    "duplicate",
                    "wrong_correlation",
                    "manual_review",
                ),
            )

    def test_manual_fallback_requirements_cover_every_reviewed_action(self) -> None:
        self.assertEqual(
            set(PHASE62_MANUAL_FALLBACK_REQUIREMENTS),
            set(PHASE62_ACTION_POLICIES),
        )

        for action, requirement in PHASE62_MANUAL_FALLBACK_REQUIREMENTS.items():
            self.assertEqual(requirement.catalog_action, action)
            self.assertEqual(requirement.affected_action, action)
            self.assertEqual(
                requirement.fallback_states,
                (
                    "shuffle_unavailable",
                    "execution_rejected",
                    "missing_receipt",
                    "stale_receipt",
                    "mismatched_receipt",
                ),
            )
            self.assertEqual(
                requirement.required_record_fields,
                (
                    "fallback_owner_id",
                    "operator_note",
                    "affected_action",
                    "blocked_reason",
                    "expected_evidence",
                    "follow_up_state",
                ),
            )
            self.assertEqual(requirement.manual_fallback_role, "subordinate_guidance")
            self.assertEqual(requirement.approval_bypass, "forbidden")
            self.assertEqual(requirement.execution_truth, "execution_receipt_required")
            self.assertEqual(
                requirement.reconciliation_truth,
                "aegisops_reconciliation_required",
            )

    def test_manual_fallback_validation_rejects_missing_and_authority_bypass_fields(
        self,
    ) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "shuffle_unavailable",
            "blocked_reason": "reviewed Shuffle route unavailable",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }
        blocked_reasons = {
            "shuffle_unavailable": "reviewed Shuffle route unavailable",
            "execution_rejected": "reviewed Shuffle execution rejected",
            "missing_receipt": "bound AegisOps execution receipt missing",
            "stale_receipt": "bound AegisOps execution receipt stale",
            "mismatched_receipt": "bound AegisOps execution receipt mismatched",
        }

        for fallback_state in (
            "shuffle_unavailable",
            "execution_rejected",
            "missing_receipt",
            "stale_receipt",
            "mismatched_receipt",
        ):
            with self.subTest(valid_fallback_state=fallback_state):
                self.assertEqual(
                    validate_phase62_manual_fallback_record(
                        catalog_action="operator_notification",
                        record={
                            **valid_record,
                            "fallback_state": fallback_state,
                            "blocked_reason": blocked_reasons[fallback_state],
                        },
                    ),
                    (),
                )

        cases = {
            "shuffle_unavailable": {"fallback_owner_id": ""},
            "execution_rejected": {"operator_note": ""},
            "missing_receipt": {"expected_evidence": ""},
            "stale_receipt": {"affected_action": "create_tracking_ticket"},
            "mismatched_receipt": {"fallback_state": "success"},
            "missing_operator_note": {
                "operator_note": "This note bypasses approval and proves execution.",
            },
            "missing_follow_up_state": {"follow_up_state": ""},
            "fallback_as_reconciliation_truth": {
                "operator_note": "Operator note is reconciliation truth.",
            },
        }

        for label, override in cases.items():
            with self.subTest(label=label):
                candidate = {**valid_record, **override}
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record=candidate,
                )
                self.assertTrue(errors, label)

    def test_manual_fallback_validation_rejects_non_authoritative_evidence_claims(
        self,
    ) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "missing_receipt",
            "blocked_reason": "bound AegisOps execution receipt missing",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }

        for expected_evidence in (
            "ticket state confirms execution",
            "issue-lint output is authoritative",
            "Shuffle workflow state is execution truth",
            "UI cache proves receipt",
            "browser state confirms reconciliation",
            "AI output is authoritative for receipt proof",
            "verifier output proves execution",
            "operator note is reconciliation truth",
            "ticket output is authoritative",
            "Shuffle result is truth",
            "workflow result confirms receipt",
            "issue lint report is receipt proof",
        ):
            with self.subTest(expected_evidence=expected_evidence):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={
                        **valid_record,
                        "expected_evidence": expected_evidence,
                    },
                )
                self.assertIn(
                    "expected_evidence_promotes_non_authoritative_truth",
                    errors,
                )

    def test_manual_fallback_validation_rejects_closure_readiness_follow_up_state(
        self,
    ) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "missing_receipt",
            "blocked_reason": "bound AegisOps execution receipt missing",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }

        for follow_up_state in (
            "ticket_closure_ready",
            "case_closed",
            "ga_ready",
            "beta_readiness_claimed",
            "rc_ready",
            "commercial_replacement_readiness",
            "reconciliation_complete",
        ):
            with self.subTest(follow_up_state=follow_up_state):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "follow_up_state": follow_up_state},
                )
                self.assertIn("follow_up_state_promotes_completion", errors)

    def test_manual_fallback_validation_requires_blocked_reason_category(self) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "missing_receipt",
            "blocked_reason": "bound AegisOps execution receipt missing",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }

        cases = {
            "shuffle_unavailable": "investigate later",
            "execution_rejected": "operator needs to review",
            "missing_receipt": "investigate later",
            "stale_receipt": "operator needs to review",
            "mismatched_receipt": "investigate later",
        }
        for fallback_state, blocked_reason in cases.items():
            with self.subTest(fallback_state=fallback_state):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={
                        **valid_record,
                        "fallback_state": fallback_state,
                        "blocked_reason": blocked_reason,
                    },
                )
                self.assertIn("blocked_reason_missing_failure_category", errors)

    def test_shuffle_mapping_contains_reviewed_catalog_actions(self) -> None:
        self.assertEqual(
            set(PHASE62_SHUFFLE_WORKFLOW_MAPPINGS),
            set(PHASE62_ACTION_POLICIES),
        )

        tracking_ticket = PHASE62_SHUFFLE_WORKFLOW_MAPPINGS[
            "create_tracking_ticket"
        ]
        self.assertEqual(tracking_ticket.workflow_template_id, "create_tracking_ticket")
        self.assertEqual(
            tracking_ticket.reviewed_template_version,
            "create_tracking_ticket-v1-reviewed-2026-05-03",
        )
        self.assertEqual(tracking_ticket.family, "Soft Write")
        self.assertIn("correlation_id", tracking_ticket.correlation_fields)
        self.assertIn(
            "expected_execution_receipt_id",
            tracking_ticket.correlation_fields,
        )

        validation = validate_phase62_shuffle_workflow_mapping(
            catalog_action="create_tracking_ticket",
            workflow_template_id="create_tracking_ticket",
            reviewed_template_version="create_tracking_ticket-v1-reviewed-2026-05-03",
            family="Soft Write",
            required_inputs=tracking_ticket.required_inputs,
            expected_outputs=tracking_ticket.expected_outputs,
            correlation_fields=tracking_ticket.correlation_fields,
            policy_registry_id="phase62.2:create_tracking_ticket",
            review_status=tracking_ticket.review_status,
            import_eligible=tracking_ticket.import_eligible,
        )

        self.assertEqual(validation, ())

    def test_shuffle_mapping_validation_fails_closed_for_drift(self) -> None:
        reviewed_mapping = PHASE62_SHUFFLE_WORKFLOW_MAPPINGS["operator_notification"]

        missing_template = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        version_mismatch = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version="operator_notification-v2-unreviewed",
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        unreviewed_template = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:operator_notification",
            review_status="draft",
            import_eligible=False,
        )
        family_mismatch = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family="Hard Write",
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        missing_correlation = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=("action_request_id",),
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        unexpected_contract_fields = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs
            + ("unreviewed_operator_hint",),
            expected_outputs=reviewed_mapping.expected_outputs
            + ("unreviewed_delivery_receipt",),
            correlation_fields=reviewed_mapping.correlation_fields
            + ("unreviewed_correlation_hint",),
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        policy_incompatibility = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:create_tracking_ticket",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        unsupported_action = validate_phase62_shuffle_workflow_mapping(
            catalog_action="disable_account",
            workflow_template_id="disable_account",
            reviewed_template_version="disable_account-v1-reviewed",
            family="Hard Write",
            required_inputs=("action_request_id",),
            expected_outputs=("execution_receipt_id",),
            correlation_fields=("correlation_id",),
            policy_registry_id="phase62.2:disable_account",
            review_status="reviewed",
            import_eligible=True,
        )

        self.assertIn("missing_template", missing_template)
        self.assertIn("version_mismatch", version_mismatch)
        self.assertIn("unreviewed_template", unreviewed_template)
        self.assertIn("family_mismatch", family_mismatch)
        self.assertIn("missing_correlation", missing_correlation)
        self.assertIn("unexpected_required_input", unexpected_contract_fields)
        self.assertIn("unexpected_expected_output", unexpected_contract_fields)
        self.assertIn("unexpected_correlation", unexpected_contract_fields)
        self.assertIn("policy_incompatibility", policy_incompatibility)
        self.assertIn("unsupported_action", unsupported_action)

    def test_shuffle_mapping_validation_rejects_action_specific_contract_drift(
        self,
    ) -> None:
        reviewed_mapping = PHASE62_SHUFFLE_WORKFLOW_MAPPINGS["create_tracking_ticket"]

        validation = validate_phase62_shuffle_workflow_mapping(
            catalog_action="create_tracking_ticket",
            workflow_template_id=reviewed_mapping.workflow_template_id,
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=tuple(
                field
                for field in reviewed_mapping.required_inputs
                if field not in {"ticket_pointer_id", "ticket_system_id"}
            ),
            expected_outputs=tuple(
                field
                for field in reviewed_mapping.expected_outputs
                if field not in {"ticket_pointer_id", "ticket_system_id"}
            ),
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id=reviewed_mapping.policy_registry_id,
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )

        self.assertIn("missing_required_input", validation)
        self.assertIn("missing_expected_output", validation)

        unexpected_validation = validate_phase62_shuffle_workflow_mapping(
            catalog_action="create_tracking_ticket",
            workflow_template_id=reviewed_mapping.workflow_template_id,
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs
            + ("unreviewed_ticket_priority",),
            expected_outputs=reviewed_mapping.expected_outputs
            + ("unreviewed_ticket_url",),
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id=reviewed_mapping.policy_registry_id,
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )

        self.assertIn("unexpected_required_input", unexpected_validation)
        self.assertIn("unexpected_expected_output", unexpected_validation)

    def test_validation_allows_reviewed_tracking_ticket_policy(self) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="create_tracking_ticket",
            requester_identity="analyst-phase62-001",
            target_scope={
                "case_id": "case-001",
                "coordination_reference_id": "coordination-ref-001",
                "coordination_target_type": "zammad",
            },
            expires_at=self.now + timedelta(hours=4),
            idempotency_key="create-tracking-ticket:abc",
            now=self.now,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.decision, "allowed")
        self.assertEqual(decision.denial_reasons, ())

    def test_validation_denies_missing_policy(self) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="disable_account",
            requester_identity="analyst-001",
            target_scope={"case_id": "case-001"},
            expires_at=self.now + timedelta(hours=4),
            idempotency_key="disable-account:abc",
            now=self.now,
        )

        self.assertFalse(decision.allowed)
        self.assertIn("missing_reviewed_policy", decision.denial_reasons)

    def test_validation_denies_expired_wrong_role_wrong_scope_and_missing_idempotency(
        self,
    ) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="create_tracking_ticket",
            requester_identity="read-only-auditor-001",
            target_scope={
                "case_id": "case-001",
                "coordination_reference_id": "coordination-ref-001",
                "coordination_target_type": "unreviewed-ticket-system",
            },
            expires_at=self.now - timedelta(minutes=1),
            idempotency_key=None,
            now=self.now,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(
            decision.denial_reasons,
            (
                "requester_role_not_allowed",
                "policy_expired",
                "missing_idempotency_key",
                "target_scope_not_allowed",
            ),
        )

    def test_validation_denies_protected_target_misuse(self) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="operator_notification",
            requester_identity="analyst-001",
            target_scope={
                "recipient_identity": "operator-001",
                "protected_target": True,
            },
            expires_at=self.now + timedelta(hours=4),
            idempotency_key="operator-notification:abc",
            now=self.now,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.denial_reasons, ("protected_target_misuse",))

    def test_validation_routes_protected_manual_escalation_to_approval(self) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="manual_escalation_request",
            requester_identity="analyst-001",
            target_scope={
                "escalation_owner_ref": "it-operations-duty-owner",
                "protected_target": True,
            },
            expires_at=self.now + timedelta(hours=4),
            idempotency_key="manual-escalation:abc",
            now=self.now,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.denial_reasons, ())
        self.assertEqual(
            decision.as_policy_evaluation()["approval_requirement"],
            "human_required_for_protected_follow_up",
        )
        self.assertEqual(decision.as_policy_evaluation()["routing_target"], "approval")


if __name__ == "__main__":
    unittest.main()
