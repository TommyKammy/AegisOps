from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _cli_inspection_support import *  # noqa: F403
from _cli_inspection_support import _approved_payload_binding_hash, _load_wazuh_fixture


class CliInspectionActionReviewTests(ControlPlaneCliInspectionTestBase):
    def test_cli_renders_recommendation_draft_view_for_a_case(self) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-draft-cli-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "render-recommendation-draft",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["record_family"], "case")
        self.assertEqual(payload["record_id"], promoted_case.case_id)
        self.assertEqual(payload["reviewed_context"], promoted_case.reviewed_context)
        self.assertEqual(
            payload["recommendation_draft"]["source_output_kind"],
            "case_summary",
        )
        self.assertEqual(payload["recommendation_draft"]["status"], "ready")
        self.assertTrue(payload["recommendation_draft"]["candidate_recommendations"])
        self.assertIn(
            evidence_id,
            payload["recommendation_draft"]["citations"],
        )
        self.assertIn(
            "advisory_only",
            payload["recommendation_draft"]["uncertainty_flags"],
        )
        self.assertEqual(payload["linked_evidence_ids"], [evidence_id])
        self.assertIn(promoted_case.alert_id, payload["linked_alert_ids"])
        self.assertIn(recommendation.recommendation_id, payload["linked_recommendation_ids"])
        self.assertTrue(payload["linked_reconciliation_ids"])

    def test_cli_creates_reviewed_action_request_from_recommendation_context(self) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-cli-action-request-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "create-reviewed-action-request",
                "--family",
                "recommendation",
                "--record-id",
                recommendation.recommendation_id,
                "--requester-identity",
                "analyst-001",
                "--recipient-identity",
                "repo-owner-001",
                "--message-intent",
                "Notify the accountable repository owner about the reviewed permission change.",
                "--escalation-reason",
                "Reviewed GitHub audit evidence requires bounded owner notification.",
                "--expires-at",
                (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
                "--action-request-id",
                "action-request-cli-reviewed-001",
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["action_request_id"], "action-request-cli-reviewed-001")
        self.assertEqual(payload["case_id"], promoted_case.case_id)
        self.assertEqual(payload["alert_id"], promoted_case.alert_id)
        self.assertEqual(payload["requester_identity"], "analyst-001")
        self.assertEqual(payload["lifecycle_state"], "pending_approval")
        self.assertEqual(
            payload["policy_evaluation"],
            {
                "approval_requirement": "human_required",
                "approval_requirement_override": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )
        self.assertEqual(
            payload["requested_payload"]["action_type"],
            "notify_identity_owner",
        )
        self.assertEqual(
            payload["requested_payload"]["recommendation_id"],
            recommendation.recommendation_id,
        )

    def test_cli_inspect_case_detail_renders_action_review_states(self) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_states_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["current_action_review"]["review_state"], "pending")
        self.assertEqual(
            payload["current_action_review"]["action_request_id"],
            seeded["replacement_request"].action_request_id,
        )
        action_reviews_by_id = {
            record["action_request_id"]: record for record in payload["action_reviews"]
        }
        self.assertEqual(
            action_reviews_by_id[seeded["pending_request"].action_request_id]["review_state"],
            "pending",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["rejected_request"].action_request_id][
                "review_state"
            ],
            "rejected",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["rejected_request"].action_request_id][
                "approver_identities"
            ],
            ["approver-rejected-001"],
        )
        self.assertEqual(
            action_reviews_by_id[seeded["expired_request"].action_request_id]["review_state"],
            "expired",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["superseded_request"].action_request_id][
                "review_state"
            ],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["superseded_request"].action_request_id][
                "replacement_action_request_id"
            ],
            seeded["replacement_request"].action_request_id,
        )

    def test_cli_inspect_case_detail_classifies_terminal_non_delegated_review_path_health(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_states_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        action_reviews_by_id = {
            record["action_request_id"]: record for record in payload["action_reviews"]
        }
        expected_paths = {
            "ingest": {
                "state": "healthy",
                "reason": "review_closed_before_ingest",
            },
            "delegation": {
                "state": "healthy",
                "reason": "review_closed_without_delegation",
            },
            "provider": {
                "state": "healthy",
                "reason": "review_closed_before_provider",
            },
            "persistence": {
                "state": "healthy",
                "reason": "review_closed_before_reconciliation",
            },
        }

        for action_request in (
            seeded["rejected_request"],
            seeded["expired_request"],
            seeded["superseded_request"],
        ):
            review = action_reviews_by_id[action_request.action_request_id]
            self.assertEqual(review["path_health"]["overall_state"], "healthy")
            self.assertEqual(review["path_health"]["paths"], expected_paths)

    def test_cli_inspect_case_detail_renders_review_timeline_and_mismatch_details(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self._assert_review_timeline_snapshot(review, seeded)

    def test_cli_inspect_case_detail_renders_handoff_and_manual_fallback_visibility(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Waiting until the next business-hours cycle is unsafe for this repository owner change.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-visibility-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=request.expires_at,
            )
        )
        service.persist_record(
            replace(
                request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        promoted_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the approval and fallback review at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        promoted_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="The reviewed action remains unresolved and must stay visible for the next analyst.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )
        fallback_stdout = io.StringIO()
        main.main(
            [
                "record-action-review-manual-fallback",
                "--action-request-id",
                request.action_request_id,
                "--fallback-at",
                (reviewed_at + timedelta(minutes=45)).isoformat(),
                "--fallback-actor-identity",
                "analyst-003",
                "--authority-boundary",
                "approved_human_fallback",
                "--reason",
                "The reviewed automation path was unavailable after approval.",
                "--action-taken",
                "Notified the accountable repository owner using the approved manual procedure.",
                "--verification-evidence-id",
                evidence_id,
                "--residual-uncertainty",
                "Awaiting written owner acknowledgement in the next review window.",
            ],
            stdout=fallback_stdout,
            service=service,
        )
        escalation_stdout = io.StringIO()
        main.main(
            [
                "record-action-review-escalation-note",
                "--action-request-id",
                request.action_request_id,
                "--escalated-at",
                (reviewed_at + timedelta(minutes=15)).isoformat(),
                "--escalated-by-identity",
                "analyst-003",
                "--escalated-to",
                "on-call-manager-001",
                "--note",
                "On-call manager notified because the open approval could not be left unattended.",
            ],
            stdout=escalation_stdout,
            service=service,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["review_state"], "unresolved")
        self.assertEqual(
            review["runtime_visibility"]["after_hours_handoff"]["handoff_owner"],
            "analyst-002",
        )
        self.assertEqual(
            review["runtime_visibility"]["after_hours_handoff"]["disposition"],
            "business_hours_handoff",
        )
        self.assertEqual(
            review["runtime_visibility"]["after_hours_handoff"]["rationale"],
            "The reviewed action remains unresolved and must stay visible for the next analyst.",
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["action_request_id"],
            request.action_request_id,
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["fallback_at"],
            (reviewed_at + timedelta(minutes=45)).isoformat(),
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalation_reason"],
            "Waiting until the next business-hours cycle is unsafe for this repository owner change.",
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-001",
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalated_by_identity"],
            "analyst-003",
        )

    def test_cli_inspect_case_detail_scopes_runtime_visibility_to_the_matching_action_review(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep unresolved ownership explicit across multiple reviewed action requests.",
        )
        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the first reviewed permission change.",
            escalation_reason="First reviewed request remains approval-bound.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-visibility-scope-001",
        )
        first_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-visibility-scope-001",
                action_request_id=first_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(first_request.target_scope),
                payload_hash=first_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=first_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                first_request,
                approval_decision_id=first_approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-002",
            message_intent="Notify the accountable repository owner about the second reviewed permission change.",
            escalation_reason="Second reviewed request remains approval-bound.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-visibility-scope-002",
        )
        second_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-visibility-scope-002",
                action_request_id=second_request.action_request_id,
                approver_identities=("approver-002",),
                target_snapshot=dict(second_request.target_scope),
                payload_hash=second_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=10),
                lifecycle_state="approved",
                approved_expires_at=second_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                second_request,
                approval_decision_id=second_approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        promoted_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the approval review at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        promoted_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Keep the unresolved action review explicit for the next analyst.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )
        main.main(
            [
                "record-action-review-manual-fallback",
                "--action-request-id",
                first_request.action_request_id,
                "--fallback-at",
                (reviewed_at + timedelta(minutes=30)).isoformat(),
                "--fallback-actor-identity",
                "analyst-002",
                "--authority-boundary",
                "approved_human_fallback",
                "--reason",
                "The first reviewed automation path was unavailable after approval.",
                "--action-taken",
                "Used the approved manual procedure for the first request only.",
                "--verification-evidence-id",
                evidence_id,
            ],
            stdout=io.StringIO(),
            service=service,
        )
        main.main(
            [
                "record-action-review-escalation-note",
                "--action-request-id",
                first_request.action_request_id,
                "--escalated-at",
                (reviewed_at + timedelta(minutes=12)).isoformat(),
                "--escalated-by-identity",
                "analyst-002",
                "--escalated-to",
                "on-call-manager-000",
                "--note",
                "On-call manager notified because the first open approval could not be left unattended.",
            ],
            stdout=io.StringIO(),
            service=service,
        )
        main.main(
            [
                "record-action-review-manual-fallback",
                "--action-request-id",
                second_request.action_request_id,
                "--fallback-at",
                (reviewed_at + timedelta(minutes=45)).isoformat(),
                "--fallback-actor-identity",
                "analyst-003",
                "--authority-boundary",
                "approved_human_fallback",
                "--reason",
                "The reviewed automation path was unavailable after approval.",
                "--action-taken",
                "Used the approved manual procedure for the second request only.",
                "--verification-evidence-id",
                evidence_id,
                "--residual-uncertainty",
                "Awaiting written owner acknowledgement in the next review window.",
            ],
            stdout=io.StringIO(),
            service=service,
        )
        main.main(
            [
                "record-action-review-escalation-note",
                "--action-request-id",
                second_request.action_request_id,
                "--escalated-at",
                (reviewed_at + timedelta(minutes=15)).isoformat(),
                "--escalated-by-identity",
                "analyst-003",
                "--escalated-to",
                "on-call-manager-001",
                "--note",
                "On-call manager notified because the second open approval could not be left unattended.",
            ],
            stdout=io.StringIO(),
            service=service,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        reviews_by_id = {
            review["action_request_id"]: review for review in payload["action_reviews"]
        }
        first_review = reviews_by_id[first_request.action_request_id]
        second_review = reviews_by_id[second_request.action_request_id]

        self.assertEqual(
            first_review["runtime_visibility"]["after_hours_handoff"]["rationale"],
            "Keep the unresolved action review explicit for the next analyst.",
        )
        self.assertEqual(
            first_review["runtime_visibility"]["manual_fallback"]["action_request_id"],
            first_request.action_request_id,
        )
        self.assertEqual(
            first_review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            first_approval.approval_decision_id,
        )
        self.assertEqual(
            first_review["runtime_visibility"]["manual_fallback"]["fallback_actor_identity"],
            "analyst-002",
        )
        self.assertEqual(
            first_review["runtime_visibility"]["escalation_notes"]["escalation_reason"],
            "First reviewed request remains approval-bound.",
        )
        self.assertEqual(
            first_review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-000",
        )
        self.assertEqual(
            first_review["runtime_visibility"]["escalation_notes"]["escalated_by_identity"],
            "analyst-002",
        )
        self.assertEqual(
            second_review["runtime_visibility"]["manual_fallback"]["action_request_id"],
            second_request.action_request_id,
        )
        self.assertEqual(
            second_review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            second_approval.approval_decision_id,
        )
        self.assertEqual(
            second_review["runtime_visibility"]["escalation_notes"]["escalation_reason"],
            "Second reviewed request remains approval-bound.",
        )
        self.assertEqual(
            second_review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-001",
        )
        self.assertEqual(
            second_review["runtime_visibility"]["escalation_notes"]["escalated_by_identity"],
            "analyst-003",
        )

    def test_cli_inspect_case_detail_hides_after_hours_handoff_for_completed_review_history(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep only live unresolved review chains marked as after-hours handoff.",
        )
        completed_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the completed reviewed change.",
            escalation_reason="Completed reviewed request should not inherit the active handoff note.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-handoff-history-001",
        )
        unresolved_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-002",
            message_intent="Notify the accountable repository owner about the unresolved reviewed change.",
            escalation_reason="Unresolved reviewed request should retain the active handoff note.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-handoff-history-002",
        )
        service.persist_record(
            replace(
                completed_request,
                lifecycle_state="completed",
                requested_at=completed_request.requested_at - timedelta(minutes=10),
            )
        )
        service.persist_record(replace(unresolved_request, lifecycle_state="unresolved"))
        service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the unresolved approval review at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Keep only the unresolved reviewed action visible for the next analyst handoff.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        reviews_by_id = {
            review["action_request_id"]: review for review in payload["action_reviews"]
        }
        completed_visibility = (
            reviews_by_id[completed_request.action_request_id]["runtime_visibility"] or {}
        )
        self.assertNotIn("after_hours_handoff", completed_visibility)
        self.assertEqual(
            reviews_by_id[unresolved_request.action_request_id]["runtime_visibility"][
                "after_hours_handoff"
            ]["handoff_owner"],
            "analyst-002",
        )

    def test_cli_runtime_visibility_ignores_non_handoff_triage_dispositions(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep routine pending approval triage from being mislabeled as a handoff.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Routine approval follow-up remains open.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-non-handoff-triage-001",
        )
        service.persist_record(replace(action_request, lifecycle_state="unresolved"))
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="pending_approval",
            rationale="Approval is still pending, but no after-hours handoff has been recorded.",
            recorded_at=reviewed_at + timedelta(minutes=20),
        )

        case_stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=case_stdout,
            service=service,
        )
        case_payload = json.loads(case_stdout.getvalue())

        queue_stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=queue_stdout, service=service)
        queue_payload = json.loads(queue_stdout.getvalue())

        self.assertIsNone(case_payload["current_action_review"]["runtime_visibility"])
        self.assertEqual(queue_payload["total_records"], 1)
        self.assertIsNone(queue_payload["records"][0]["current_action_review"]["runtime_visibility"])

    def test_cli_inspect_case_detail_keeps_preapproval_unresolved_review_path_health_delayed(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, _reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep pre-approval follow-up visible without overstating it as a post-approval silent failure.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Approval follow-up remains open.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-preapproval-unresolved-path-health-001",
        )
        service.persist_record(replace(action_request, lifecycle_state="unresolved"))

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]

        self.assertEqual(review["review_state"], "unresolved")
        self.assertEqual(review["path_health"]["overall_state"], "delayed")
        self.assertEqual(
            review["path_health"]["paths"],
            {
                "ingest": {
                    "state": "delayed",
                    "reason": "awaiting_ingest_signal",
                },
                "delegation": {
                    "state": "delayed",
                    "reason": "awaiting_approval",
                },
                "provider": {
                    "state": "delayed",
                    "reason": "awaiting_delegation",
                },
                "persistence": {
                    "state": "delayed",
                    "reason": "awaiting_reconciliation",
                },
            },
        )

    def test_cli_inspect_case_detail_classifies_stale_delegation_receipt_timeout(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Show overdue delegation receipt gaps as degraded path-health signals.",
        )
        base_now = datetime.now(timezone.utc)
        requested_at = base_now - timedelta(hours=2)
        delegated_at = base_now - timedelta(hours=1, minutes=50)
        expired_at = base_now - timedelta(hours=1)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep overdue delegation receipt gaps explicit in operator inspection.",
            escalation_reason="Delegation receipt timeouts must be visible without external dashboards.",
            expires_at=base_now + timedelta(hours=4),
            action_request_id="action-request-cli-stale-dispatching-path-health-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-stale-dispatching-path-health-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expired_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                requested_at=requested_at,
                expires_at=expired_at,
                lifecycle_state="executing",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-cli-stale-dispatching-path-health-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-cli-stale-dispatching-path-health-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-cli-stale-dispatching-path-health-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=delegated_at,
                expires_at=expired_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="dispatching",
            )
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]

        self.assertEqual(review["review_state"], "executing")
        self.assertEqual(review["path_health"]["overall_state"], "degraded")
        self.assertEqual(
            review["path_health"]["paths"],
            {
                "ingest": {
                    "state": "degraded",
                    "reason": "ingest_signal_timeout",
                },
                "delegation": {
                    "state": "degraded",
                    "reason": "delegation_receipt_timeout",
                },
                "provider": {
                    "state": "degraded",
                    "reason": "provider_receipt_timeout",
                },
                "persistence": {
                    "state": "degraded",
                    "reason": "reconciliation_timeout",
                },
            },
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_outcome(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        requested_at = reviewed_at + timedelta(minutes=10)
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        approved_target_scope = {
            "case_id": promoted_case.case_id,
            "alert_id": promoted_case.alert_id,
            "finding_id": promoted_case.finding_id,
            "coordination_reference_id": "coord-ref-cli-create-ticket-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = phase26_create_tracking_ticket_payload(
            case_id=promoted_case.case_id,
            alert_id=promoted_case.alert_id,
            finding_id=promoted_case.finding_id,
            coordination_reference_id="coord-ref-cli-create-ticket-001",
        )
        payload_hash = _approved_payload_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-create-ticket-outcome-001",
                action_request_id="action-request-cli-create-ticket-outcome-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=reviewed_at + timedelta(hours=4),
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-cli-create-ticket-outcome-001",
                approval_decision_id=approval.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key="idempotency-cli-create-ticket-outcome-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=reviewed_at + timedelta(hours=4),
                lifecycle_state="approved",
                requested_payload=approved_payload,
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-cli-create-ticket-outcome-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id="action-request-cli-create-ticket-outcome-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-cli-create-ticket-outcome-001",
                    "approval_decision_id": approval.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": payload_hash,
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": downstream_binding["external_receipt_id"],
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=reviewed_at + timedelta(hours=1),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]

        self.assertEqual(
            review["coordination_ticket_outcome"]["status"],
            "created",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["coordination_reference_id"],
            "coord-ref-cli-create-ticket-001",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["coordination_target_type"],
            "zammad",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["external_receipt_id"],
            downstream_binding["external_receipt_id"],
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["ticket_reference_url"],
            downstream_binding["ticket_reference_url"],
        )

    def test_cli_inspect_case_detail_repairs_nested_create_tracking_ticket_approval_linkage(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="repaired-approval-001",
            coordination_reference_id="coord-ref-cli-create-ticket-repaired-approval-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id=seeded["action_request"].action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": seeded["action_request"].idempotency_key,
                    "approval_decision_id": seeded["approval"].approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": seeded["payload_hash"],
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": downstream_binding["external_receipt_id"],
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=reviewed_at + timedelta(hours=1),
        )
        service.persist_record(
            replace(seeded["action_request"], approval_decision_id=None)
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(
            review["approval_decision_id"],
            seeded["approval"].approval_decision_id,
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["approval_decision_id"],
            seeded["approval"].approval_decision_id,
        )
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "created")

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_mismatch(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="mismatch-001",
            coordination_reference_id="coord-ref-cli-create-ticket-mismatch-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id=seeded["action_request"].action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": seeded["action_request"].idempotency_key,
                    "approval_decision_id": seeded["approval"].approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": seeded["payload_hash"],
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": "shuffle-receipt-cli-drifted-001",
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=reviewed_at + timedelta(hours=1),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "mismatch")
        self.assertEqual(
            review["coordination_ticket_outcome"]["mismatch"]["mismatch_summary"],
            "coordination receipt mismatch between authoritative action execution "
            "and observed downstream execution",
        )

    def test_cli_inspect_case_detail_omits_create_tracking_ticket_outcome_for_terminal_non_delegated_reviews(
        self,
    ) -> None:
        for review_state in ("rejected", "expired", "superseded", "canceled"):
            with self.subTest(review_state=review_state):
                _, service, promoted_case, _evidence_id, reviewed_at = (
                    self._build_phase19_in_scope_case()
                )
                seeded = self._seed_create_tracking_ticket_request(
                    service=service,
                    promoted_case=promoted_case,
                    reviewed_at=reviewed_at,
                    suffix=f"closed-without-delegation-{review_state}",
                    coordination_reference_id=(
                        f"coord-ref-cli-create-ticket-closed-without-delegation-{review_state}"
                    ),
                )
                if review_state in {"rejected", "expired"}:
                    service.persist_record(
                        replace(seeded["approval"], lifecycle_state=review_state)
                    )
                service.persist_record(
                    replace(seeded["action_request"], lifecycle_state=review_state)
                )

                stdout = io.StringIO()
                main.main(
                    ["inspect-case-detail", "--case-id", promoted_case.case_id],
                    stdout=stdout,
                    service=service,
                )

                payload = json.loads(stdout.getvalue())
                review = payload["current_action_review"]
                self.assertEqual(review["review_state"], review_state)
                self.assertIsNone(review["coordination_ticket_outcome"])

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_timeout(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = datetime.now(timezone.utc)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="timeout-001",
            coordination_reference_id="coord-ref-cli-create-ticket-timeout-001",
        )

        with mock.patch.object(
            type(service._shuffle),
            "dispatch_approved_action",
            autospec=True,
            side_effect=TimeoutError("synthetic create-tracking-ticket timeout"),
        ):
            with self.assertRaisesRegex(
                TimeoutError,
                "synthetic create-tracking-ticket timeout",
            ):
                service.delegate_approved_action_to_shuffle(
                    action_request_id=seeded["action_request"].action_request_id,
                    approved_payload=seeded["approved_payload"],
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "timeout")
        self.assertEqual(
            review["coordination_ticket_outcome"]["timeout"]["reason"],
            "dispatch_timeout",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["timeout"]["path"],
            "provider",
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_provider_failure(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="failure-001",
            coordination_reference_id="coord-ref-cli-create-ticket-failure-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        service.persist_record(replace(execution, lifecycle_state="failed"))

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "failed")
        self.assertEqual(
            review["coordination_ticket_outcome"]["terminal_issue"]["reason"],
            "execution_failed",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["terminal_issue"]["path"],
            "provider",
        )
        self.assertNotIn("timeout", review["coordination_ticket_outcome"])

    def test_cli_inspect_case_detail_prefers_provider_failure_over_derived_timeouts(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        overdue_requested_at = datetime.now(timezone.utc) - timedelta(hours=2)
        overdue_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="failure-precedence-001",
            coordination_reference_id="coord-ref-cli-create-ticket-failure-precedence-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        service.persist_record(
            replace(
                seeded["approval"],
                decided_at=overdue_requested_at + timedelta(minutes=5),
                approved_expires_at=overdue_expires_at,
            )
        )
        action_request = service.get_record(
            ActionRequestRecord, seeded["action_request"].action_request_id
        )
        service.persist_record(
            replace(
                action_request,
                requested_at=overdue_requested_at,
                expires_at=overdue_expires_at,
            )
        )
        service.persist_record(
            replace(
                execution,
                delegated_at=overdue_requested_at + timedelta(minutes=10),
                expires_at=overdue_expires_at,
                lifecycle_state="failed",
            )
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(
            review["path_health"]["paths"]["ingest"]["reason"],
            "ingest_signal_timeout",
        )
        self.assertEqual(
            review["path_health"]["paths"]["persistence"]["reason"],
            "reconciliation_timeout",
        )
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "failed")
        self.assertEqual(
            review["coordination_ticket_outcome"]["terminal_issue"]["reason"],
            "execution_failed",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["terminal_issue"]["path"],
            "provider",
        )
        self.assertNotIn("timeout", review["coordination_ticket_outcome"])

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_manual_fallback(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="manual-fallback-001",
            coordination_reference_id="coord-ref-cli-create-ticket-manual-fallback-001",
        )
        service.persist_record(
            replace(
                seeded["action_request"],
                lifecycle_state="unresolved",
            )
        )
        service.record_action_review_manual_fallback(
            action_request_id=seeded["action_request"].action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed create-ticket automation path was unavailable after approval.",
            action_taken="Opened the reviewed tracking ticket manually using the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting downstream operator acknowledgement in the next review window.",
        )
        service.persist_record(
            replace(
                service.get_record(AlertRecord, promoted_case.alert_id),
                coordination_reference_id=(
                    "coord-ref-cli-create-ticket-manual-fallback-001"
                ),
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                service.get_record(CaseRecord, promoted_case.case_id),
                coordination_reference_id=(
                    "coord-ref-cli-create-ticket-manual-fallback-001"
                ),
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(payload["external_ticket_reference"]["status"], "present")
        self.assertEqual(
            review["coordination_ticket_outcome"]["status"],
            "manual_fallback",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["manual_fallback"]["action_taken"],
            "Opened the reviewed tracking ticket manually using the approved procedure.",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["manual_fallback"][
                "fallback_actor_identity"
            ],
            "analyst-003",
        )

    def test_cli_inspect_case_detail_keeps_created_status_when_manual_fallback_is_recorded_after_success(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="created-with-fallback-001",
            coordination_reference_id="coord-ref-cli-create-ticket-created-with-fallback-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id=seeded["action_request"].action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": seeded["action_request"].idempotency_key,
                    "approval_decision_id": seeded["approval"].approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": seeded["payload_hash"],
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": downstream_binding["external_receipt_id"],
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=reviewed_at + timedelta(hours=1),
        )
        service.record_action_review_manual_fallback(
            action_request_id=seeded["action_request"].action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-004",
            authority_boundary="approved_human_fallback",
            reason="Business-hours operator added manual fallback notes after a completed create-ticket review.",
            action_taken="Captured manual ticket fallback instructions for the reviewed coordination flow.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting operator acknowledgement during the next review window.",
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "created")
        self.assertEqual(
            review["coordination_ticket_outcome"]["manual_fallback"]["action_taken"],
            "Captured manual ticket fallback instructions for the reviewed coordination flow.",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["manual_fallback"][
                "fallback_actor_identity"
            ],
            "analyst-004",
        )

    def test_cli_inspect_case_detail_keeps_after_hours_handoff_visible_for_non_executed_review_states(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_states_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )
        service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-visibility-001",
            handoff_note="Keep non-executed review states explicit for the next analyst handoff.",
            follow_up_evidence_ids=(evidence_id,),
        )
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Expired, rejected, and superseded reviewed requests must remain visibly handed off.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        reviews_by_id = {
            review["action_request_id"]: review for review in payload["action_reviews"]
        }

        for action_request in (
            seeded["expired_request"],
            seeded["rejected_request"],
            seeded["superseded_request"],
        ):
            visibility = (
                reviews_by_id[action_request.action_request_id]["runtime_visibility"] or {}
            )
            self.assertEqual(
                visibility["after_hours_handoff"]["handoff_owner"],
                "analyst-visibility-001",
            )
            self.assertEqual(
                visibility["after_hours_handoff"]["disposition"],
                "business_hours_handoff",
            )
            self.assertEqual(
                visibility["after_hours_handoff"]["rationale"],
                "Expired, rejected, and superseded reviewed requests must remain visibly handed off.",
            )

    def test_cli_inspect_alert_detail_renders_alert_scoped_runtime_visibility(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep alert-scoped follow-up explicit when case linkage is absent.",
        )
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="The alert-scoped reviewed request cannot wait for the next shift.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-alert-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-alert-visibility-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=request.expires_at,
            )
        )
        request = service.persist_record(
            replace(
                request,
                approval_decision_id=approval.approval_decision_id,
                case_id=None,
                lifecycle_state="unresolved",
            )
        )
        service.record_action_review_manual_fallback(
            action_request_id=request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Used the approved manual procedure while the alert remained unlinked to casework.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement in the next review window.",
        )
        service.record_action_review_escalation_note(
            action_request_id=request.action_request_id,
            escalated_at=reviewed_at + timedelta(minutes=15),
            escalated_by_identity="analyst-004",
            escalated_to="on-call-manager-001",
            note="On-call manager notified because the alert-scoped approval could not be left unattended.",
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", promoted_case.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["action_request_id"], request.action_request_id)
        self.assertEqual(review["review_state"], "unresolved")
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-001",
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalated_by_identity"],
            "analyst-004",
        )

    def test_cli_inspect_alert_detail_classifies_unresolved_review_without_execution(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep post-approval silent failures visible on the reviewed action path.",
        )
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="The alert-scoped reviewed request cannot stay implicit after approval.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-alert-unresolved-path-health-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-alert-unresolved-path-health-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=request.expires_at,
            )
        )
        service.persist_record(
            replace(
                request,
                approval_decision_id=approval.approval_decision_id,
                case_id=None,
                lifecycle_state="unresolved",
            )
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", promoted_case.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["review_state"], "unresolved")
        self.assertEqual(review["path_health"]["overall_state"], "degraded")
        self.assertEqual(
            review["path_health"]["paths"],
            {
                "ingest": {
                    "state": "degraded",
                    "reason": "ingest_signal_missing_after_approval",
                },
                "delegation": {
                    "state": "degraded",
                    "reason": "reviewed_delegation_missing_after_approval",
                },
                "provider": {
                    "state": "degraded",
                    "reason": "provider_signal_missing_after_approval",
                },
                "persistence": {
                    "state": "degraded",
                    "reason": "reconciliation_missing_after_approval",
                },
            },
        )

    def test_cli_inspect_case_detail_keeps_reconciliation_bound_to_selected_execution(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_retried_execution_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(
            review["action_execution_id"],
            seeded["selected_action_execution"].action_execution_id,
        )
        self.assertEqual(
            review["delegation_id"],
            seeded["selected_action_execution"].delegation_id,
        )
        self.assertEqual(
            review["reconciliation_id"],
            seeded["selected_reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["mismatch_inspection"],
            None,
        )
        self.assertEqual(
            review["timeline"][3]["occurred_at"],
            None,
        )
        self.assertEqual(
            review["timeline"][4]["record_id"],
            seeded["selected_reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["timeline"][4]["details"]["execution_run_id"],
            seeded["selected_action_execution"].execution_run_id,
        )

    def test_cli_inspect_case_detail_preserves_predelegation_reconciliation_visibility(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_predelegation_reconciliation_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(
            review["action_execution_id"],
            seeded["action_execution"].action_execution_id,
        )
        self.assertEqual(
            review["reconciliation_id"],
            seeded["reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["timeline"][4]["record_id"],
            seeded["reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["timeline"][4]["state"],
            "pending",
        )
        self.assertEqual(
            review["mismatch_inspection"]["reconciliation_id"],
            seeded["reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["mismatch_inspection"]["lifecycle_state"],
            "pending",
        )

    def test_cli_inspect_alert_detail_renders_review_timeline_and_mismatch_details(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", promoted_case.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self._assert_review_timeline_snapshot(payload["current_action_review"], seeded)

    def test_cli_inspect_alert_detail_classifies_path_health_for_mismatched_review(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", promoted_case.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["path_health"]["overall_state"], "degraded")
        self.assertTrue(review["path_health"]["summary"])
        self.assertEqual(
            review["path_health"]["paths"],
            {
                "ingest": {
                    "state": "degraded",
                    "reason": "mismatch_detected",
                },
                "delegation": {
                    "state": "healthy",
                    "reason": "delegated",
                },
                "provider": {
                    "state": "delayed",
                    "reason": "awaiting_authoritative_outcome",
                },
                "persistence": {
                    "state": "degraded",
                    "reason": "reconciliation_mismatched",
                },
            },
        )

    def test_cli_inspect_analyst_queue_renders_review_timeline_and_mismatch_details(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["total_records"], 1)
        self._assert_review_timeline_snapshot(
            payload["records"][0]["current_action_review"],
            seeded,
        )



if __name__ == "__main__":
    unittest.main()
