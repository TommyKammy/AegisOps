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
    PHASE62_SHUFFLE_WORKFLOW_MAPPINGS,
    evaluate_phase62_action_policy,
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
