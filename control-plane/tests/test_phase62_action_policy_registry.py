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
    evaluate_phase62_action_policy,
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
