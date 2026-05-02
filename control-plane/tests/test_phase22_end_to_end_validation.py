from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import io
import json
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import main
from aegisops.control_plane.models import ApprovalDecisionRecord
import test_cli_inspection as cli_inspection_tests


class Phase22EndToEndValidationTests(unittest.TestCase):
    def _helpers(self) -> cli_inspection_tests.ControlPlaneCliInspectionTests:
        return cli_inspection_tests.ControlPlaneCliInspectionTests()

    def test_phase22_end_to_end_keeps_review_states_and_visibility_explicit(self) -> None:
        helpers = self._helpers()
        _, service, promoted_case, evidence_id, reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        seeded = helpers._seed_action_review_states_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-phase22-001",
            intended_outcome="Keep unresolved approval review, fallback, and handoff state explicit.",
        )
        unresolved_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-phase22-001",
            recipient_identity="repo-owner-phase22-001",
            message_intent="Notify the accountable repository owner using the reviewed path.",
            escalation_reason="The unresolved reviewed request cannot be allowed to disappear between shifts.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase22-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase22-visibility-001",
                action_request_id=unresolved_request.action_request_id,
                approver_identities=("approver-phase22-001",),
                target_snapshot=dict(unresolved_request.target_scope),
                payload_hash=unresolved_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=unresolved_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                unresolved_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-phase22-002",
            handoff_note="Resume the unresolved reviewed approval and fallback chain at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Keep the unresolved reviewed action visible for the next operator review window.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )
        service.record_action_review_manual_fallback(
            action_request_id=unresolved_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-phase22-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Used the approved manual procedure while preserving the reviewed approval lineage.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement in the next review window.",
        )
        service.record_action_review_escalation_note(
            action_request_id=unresolved_request.action_request_id,
            escalated_at=reviewed_at + timedelta(minutes=15),
            escalated_by_identity="analyst-phase22-003",
            escalated_to="on-call-manager-phase22-001",
            note="On-call manager notified because the unresolved reviewed approval could not be left unattended.",
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        action_reviews_by_id = {
            review["action_request_id"]: review for review in payload["action_reviews"]
        }

        self.assertEqual(
            action_reviews_by_id[seeded["pending_request"].action_request_id]["review_state"],
            "pending",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["rejected_request"].action_request_id]["review_state"],
            "rejected",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["expired_request"].action_request_id]["review_state"],
            "expired",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["superseded_request"].action_request_id]["review_state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["superseded_request"].action_request_id][
                "replacement_action_request_id"
            ],
            seeded["replacement_request"].action_request_id,
        )
        for request_key in ("rejected_request", "expired_request", "superseded_request"):
            runtime_visibility = (
                action_reviews_by_id[seeded[request_key].action_request_id]["runtime_visibility"]
                or {}
            )
            self.assertEqual(
                runtime_visibility["after_hours_handoff"]["handoff_owner"],
                "analyst-phase22-002",
            )
            self.assertEqual(
                runtime_visibility["after_hours_handoff"]["disposition"],
                "business_hours_handoff",
            )
            self.assertEqual(
                runtime_visibility["after_hours_handoff"]["rationale"],
                "Keep the unresolved reviewed action visible for the next operator review window.",
            )
            self.assertNotIn("manual_fallback", runtime_visibility)

        unresolved_review = action_reviews_by_id[unresolved_request.action_request_id]
        self.assertEqual(unresolved_review["review_state"], "unresolved")
        self.assertEqual(
            unresolved_review["runtime_visibility"]["after_hours_handoff"]["handoff_owner"],
            "analyst-phase22-002",
        )
        self.assertEqual(
            unresolved_review["runtime_visibility"]["after_hours_handoff"]["disposition"],
            "business_hours_handoff",
        )
        self.assertEqual(
            unresolved_review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            unresolved_review["runtime_visibility"]["manual_fallback"][
                "fallback_actor_identity"
            ],
            "analyst-phase22-003",
        )
        self.assertEqual(
            unresolved_review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-phase22-001",
        )
        self.assertEqual(
            unresolved_review["runtime_visibility"]["escalation_notes"][
                "escalated_by_identity"
            ],
            "analyst-phase22-003",
        )

    def test_phase22_end_to_end_keeps_success_claims_non_authoritative_until_reconciliation_matches(
        self,
    ) -> None:
        helpers = self._helpers()
        _, service, promoted_case, evidence_id, reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        seeded = helpers._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )
        approved_request = seeded["action_request"]
        execution = seeded["action_execution"]
        requested_at = approved_request.requested_at
        service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": "shuffle-run-phase22-unexpected-001",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": requested_at + timedelta(minutes=19),
                    "status": "success",
                },
            ),
            compared_at=requested_at + timedelta(minutes=20),
            stale_after=requested_at + timedelta(minutes=40),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["action_request_id"], approved_request.action_request_id)
        self.assertEqual(review["review_state"], "executing")
        self.assertEqual(review["next_expected_action"], "await_execution_reconciliation")
        self.assertEqual(review["action_execution_state"], "queued")
        self.assertEqual(review["reconciliation_state"], "mismatched")
        self.assertNotEqual(review["review_state"], "completed")
        self.assertEqual(
            [stage["stage"] for stage in review["timeline"]],
            [
                "action_request",
                "approval_decision",
                "delegation",
                "action_execution",
                "reconciliation",
            ],
        )
        self.assertEqual(review["timeline"][2]["state"], "delegated")
        self.assertEqual(review["timeline"][3]["state"], "queued")
        self.assertEqual(review["timeline"][4]["state"], "mismatched")
        self.assertEqual(
            review["timeline"][4]["details"]["execution_run_id"],
            "shuffle-run-phase22-unexpected-001",
        )
        self.assertEqual(
            review["mismatch_inspection"]["execution_run_id"],
            "shuffle-run-phase22-unexpected-001",
        )
        self.assertIn(
            "run identity mismatch",
            review["mismatch_inspection"]["mismatch_summary"],
        )


if __name__ == "__main__":
    unittest.main()
