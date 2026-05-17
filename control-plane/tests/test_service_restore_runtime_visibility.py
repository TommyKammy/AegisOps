from __future__ import annotations

# ruff: noqa: E402

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _restore_readiness_test_support import (
    AegisOpsControlPlaneService,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    RuntimeConfig,
    ServicePersistenceTestBase,
    datetime,
    make_store,
    replace,
    timedelta,
    timezone,
)
from aegisops.control_plane.actions.review.action_review_visibility import (
    action_review_runtime_visibility,
)


class RestoreRuntimeVisibilityTests(ServicePersistenceTestBase):
    def test_manual_fallback_runtime_write_uses_phase62_validation(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep legacy manual fallback timestamps auditable after restore.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback must preserve the authority boundary.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-runtime-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-runtime-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "operator_note_promotes_authority",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=action_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=45),
                fallback_actor_identity="analyst-003",
                authority_boundary="approved_human_fallback",
                reason="The reviewed automation path was unavailable after approval.",
                action_taken="Manual fallback note proves execution.",
                verification_evidence_ids=(evidence_id,),
                residual_uncertainty="Awaiting written owner acknowledgement.",
            )

        case_after_rejection = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(case_after_rejection)
        assert case_after_rejection is not None
        action_review_visibility = dict(
            case_after_rejection.reviewed_context.get("action_review_visibility", {})
        )
        scoped_visibility = dict(
            action_review_visibility.get(action_request.action_request_id, {})
        )
        self.assertNotIn("manual_fallback", scoped_visibility)

    def test_manual_fallback_rejects_ambiguous_failure_reason(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep manual fallback classification explicit.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback classification must not infer a missing receipt.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-ambiguous-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-ambiguous-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "blocked_reason_missing_failure_category",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=action_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=45),
                fallback_actor_identity="analyst-003",
                authority_boundary="approved_human_fallback",
                reason="Investigate later with the operator on duty.",
                action_taken="Documented manual follow-up under the approved procedure.",
                verification_evidence_ids=(evidence_id,),
                residual_uncertainty="Awaiting reconciliation review.",
            )

        case_after_rejection = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(case_after_rejection)
        assert case_after_rejection is not None
        action_review_visibility = dict(
            case_after_rejection.reviewed_context.get("action_review_visibility", {})
        )
        scoped_visibility = dict(
            action_review_visibility.get(action_request.action_request_id, {})
        )
        self.assertNotIn("manual_fallback", scoped_visibility)

    def test_manual_fallback_rejects_standalone_timed_scheduling_note(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep scheduling notes from masquerading as Shuffle outages.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback classification must require a real failure category.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-timed-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-timed-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "blocked_reason_missing_failure_category",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=action_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=45),
                fallback_actor_identity="analyst-003",
                authority_boundary="approved_human_fallback",
                reason="Manual follow-up timed for Monday with the operator on duty.",
                action_taken="Documented manual follow-up under the approved procedure.",
                verification_evidence_ids=(evidence_id,),
                residual_uncertainty="Awaiting reconciliation review.",
            )

        case_after_rejection = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(case_after_rejection)
        assert case_after_rejection is not None
        action_review_visibility = dict(
            case_after_rejection.reviewed_context.get("action_review_visibility", {})
        )
        scoped_visibility = dict(
            action_review_visibility.get(action_request.action_request_id, {})
        )
        self.assertNotIn("manual_fallback", scoped_visibility)

    def test_manual_fallback_state_uses_failure_reason_not_uncertainty(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep manual fallback classification tied to the reason.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback classification must not be inferred from notes.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-state-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-state-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed Shuffle execution was rejected by the approved route.",
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty=(
                "A later stale receipt warning remains unresolved for reconciliation."
            ),
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "repo-owner-001",
        )
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_state"],
            "execution_rejected",
        )
        self.assertIn(
            "execution rejected",
            scoped_visibility["manual_fallback"]["blocked_reason"],
        )
        refreshed_action_request = service.get_record(
            ActionRequestRecord,
            action_request.action_request_id,
        )
        self.assertIsNotNone(refreshed_action_request)
        assert refreshed_action_request is not None
        runtime_visibility = action_review_runtime_visibility(
            service,
            action_request=refreshed_action_request,
            approval_decision=approval,
            review_state="unresolved",
        )
        self.assertIsNotNone(runtime_visibility)
        assert runtime_visibility is not None
        runtime_manual_fallback = runtime_visibility["manual_fallback"]
        for required_key in (
            "fallback_owner_id",
            "operator_note",
            "affected_action",
            "fallback_state",
            "blocked_reason",
            "expected_evidence",
            "follow_up_state",
        ):
            with self.subTest(required_key=required_key):
                self.assertIn(required_key, runtime_manual_fallback)
        self.assertEqual(
            runtime_manual_fallback["fallback_state"],
            "execution_rejected",
        )
        inspected_manual_fallback = service.inspect_case_detail(
            promoted_case.case_id
        ).current_action_review["runtime_visibility"]["manual_fallback"]
        for required_key in (
            "fallback_owner_id",
            "operator_note",
            "affected_action",
            "fallback_state",
            "blocked_reason",
            "expected_evidence",
            "follow_up_state",
        ):
            with self.subTest(inspected_required_key=required_key):
                self.assertIn(required_key, inspected_manual_fallback)

    def test_manual_fallback_owner_defaults_to_declared_action_target(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep manual fallback ownership tied to the action target.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-fallback-target-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback ownership must not come from the logging actor.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-owner-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-owner-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement.",
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "repo-owner-fallback-target-001",
        )
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )

    def test_manual_fallback_owner_prefers_reviewed_target_scope_over_payload(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep fallback owner attribution anchored to reviewed scope.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="reviewed-recipient-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback owner must follow the reviewed target.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-target-owner-001",
        )
        action_request = service.persist_record(
            replace(
                action_request,
                requested_payload={
                    **dict(action_request.requested_payload),
                    "recipient_identity": "payload-recipient-stale-001",
                },
            )
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-target-owner-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement.",
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "reviewed-recipient-001",
        )
        self.assertNotEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "payload-recipient-stale-001",
        )

    def test_tracking_ticket_manual_fallback_owner_uses_requester_before_reference(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before ticket coordination.",
            lead_id=lead.lead_id,
        )
        action_request = service.create_reviewed_tracking_ticket_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            coordination_reference_id="coordination-ref-phase62-fallback-owner-001",
            coordination_target_type="zammad",
            ticket_title="Review repository owner change",
            ticket_description="Coordinate reviewed follow-up without making ticket state authoritative.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-ticket-fallback-owner-001",
        )
        action_request = service.persist_record(
            replace(
                action_request,
                requested_payload={
                    **dict(action_request.requested_payload),
                    "requester_identity": "stale-payload-requester-001",
                },
            )
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-ticket-fallback-owner-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed Shuffle execution was rejected by the approved route.",
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting ticket requester follow-up.",
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "analyst-001",
        )
        self.assertNotEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "coordination-ref-phase62-fallback-owner-001",
        )
        self.assertNotEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "stale-payload-requester-001",
        )

    def test_manual_escalation_fallback_owner_uses_reviewed_target_scope(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-phase62-escalation-fallback-owner-001",
                approval_decision_id=None,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key="manual-escalation-fallback-owner-001",
                target_scope={
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "escalation_owner_ref": "reviewed-escalation-owner-001",
                },
                payload_hash="payload-hash-phase62-escalation-fallback-owner-001",
                requested_at=reviewed_at,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
                lifecycle_state="pending_approval",
                requester_identity="analyst-001",
                requested_payload={
                    "action_type": "manual_escalation_request",
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "escalation_owner_id": "payload-escalation-owner-stale-001",
                },
                policy_evaluation={
                    "approval_requirement": "human_required_for_protected_follow_up",
                },
            ),
            transitioned_at=reviewed_at,
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-escalation-fallback-owner-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed Shuffle execution was rejected by the approved route.",
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting escalation owner follow-up.",
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "reviewed-escalation-owner-001",
        )
        self.assertNotEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "payload-escalation-owner-stale-001",
        )

    def test_enrichment_lookup_fallback_owner_uses_reviewed_lookup_subject(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-phase62-lookup-fallback-owner-001",
                approval_decision_id=None,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key="lookup-fallback-owner-001",
                target_scope={
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "lookup_subject_ref": "reviewed-lookup-subject-001",
                },
                payload_hash="payload-hash-phase62-lookup-fallback-owner-001",
                requested_at=reviewed_at,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
                lifecycle_state="pending_approval",
                requester_identity=None,
                requested_payload={
                    "action_type": "enrichment_only_lookup",
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "lookup_subject_id": "payload-lookup-subject-stale-001",
                },
                policy_evaluation={"approval_requirement": "policy_not_required"},
            ),
            transitioned_at=reviewed_at,
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-lookup-fallback-owner-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The bound AegisOps execution receipt was missing after handoff.",
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting lookup reconciliation review.",
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "reviewed-lookup-subject-001",
        )
        self.assertNotEqual(
            scoped_visibility["manual_fallback"]["fallback_owner_id"],
            "payload-lookup-subject-stale-001",
        )

    def test_manual_fallback_state_ignores_negated_failure_terms(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep negated failure terms out of fallback classification.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback classification must reject negated failure hints.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-negation-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-negation-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason=(
                "The reviewed route was not unavailable but receipt missing "
                "after approved dispatch."
            ),
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting reconciliation review.",
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_state"],
            "missing_receipt",
        )
        self.assertIn(
            "receipt missing",
            scoped_visibility["manual_fallback"]["blocked_reason"],
        )

    def test_manual_fallback_state_limits_negation_at_conjunction_boundary(
        self,
    ) -> None:
        from aegisops.control_plane.actions.review.action_review_write_surface import (
            _phase62_fallback_state_from_text,
        )

        for reason in (
            "The reviewed route was not unavailable but receipt missing after dispatch.",
            "The reviewed route was not unavailable. receipt missing after dispatch.",
            "The reviewed route was not unavailable, receipt missing after dispatch.",
            "The reviewed route was not unavailable or receipt missing after dispatch.",
            "The reviewed route wasn\u2019t unavailable but receipt missing after dispatch.",
            (
                "The reviewed route was not under exceptionally constrained "
                "external conditions unavailable but receipt missing after dispatch."
            ),
            "The reviewed route was not unavailable whereas receipt missing after dispatch.",
            "The reviewed route was not unavailable while receipt missing after dispatch.",
        ):
            with self.subTest(reason=reason):
                self.assertEqual(
                    _phase62_fallback_state_from_text(reason),
                    "missing_receipt",
                )

        self.assertEqual(
            _phase62_fallback_state_from_text(
                "The reviewed route was not only unavailable after dispatch."
            ),
            "shuffle_unavailable",
        )
        self.assertEqual(
            _phase62_fallback_state_from_text(
                "The reviewed route was not only rejected before receipt emission."
            ),
            "execution_rejected",
        )

        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Keep conjunction-separated failure terms available for fallback "
                "classification."
            ),
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback classification must respect conjunction boundaries.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-and-negation-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-and-negation-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason=(
                "The reviewed route was not unavailable and receipt missing "
                "after approved dispatch."
            ),
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting reconciliation review.",
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_state"],
            "missing_receipt",
        )
        self.assertIn(
            "receipt missing",
            scoped_visibility["manual_fallback"]["blocked_reason"],
        )

    def test_manual_fallback_state_requires_receipt_context_for_absent_terms(
        self,
    ) -> None:
        from aegisops.control_plane.actions.review.action_review_write_surface import (
            _phase62_fallback_state_from_text,
        )

        for reason in (
            "operator missed handoff window",
            "fallback owner absent from calendar rotation",
        ):
            with self.subTest(generic_absent_reason=reason):
                self.assertIsNone(_phase62_fallback_state_from_text(reason))

        for reason in (
            "bound AegisOps receipt absent after dispatch",
            "bound AegisOps receipt was missed after dispatch",
        ):
            with self.subTest(receipt_absent_reason=reason):
                self.assertEqual(
                    _phase62_fallback_state_from_text(reason),
                    "missing_receipt",
                )

    def test_manual_fallback_state_recognizes_rejection_variants(self) -> None:
        from aegisops.control_plane.actions.review.action_review_write_surface import (
            _phase62_fallback_state_from_text,
        )

        for reason in (
            "The reviewed Shuffle execution was canceled before receipt emission.",
            "The reviewed Shuffle execution was cancelled before receipt emission.",
            "The reviewed Shuffle execution cancellation blocked the route.",
        ):
            with self.subTest(reason=reason):
                self.assertEqual(
                    _phase62_fallback_state_from_text(reason),
                    "execution_rejected",
                )

        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Manual fallback classification must cover rejection variants.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase62-manual-fallback-rejection-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase62-manual-fallback-rejection-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        updated_case = service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed Shuffle execution was canceled before receipt emission.",
            action_taken="Documented manual follow-up under the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting reconciliation review.",
        )

        scoped_visibility = updated_case.reviewed_context["action_review_visibility"][
            action_request.action_request_id
        ]
        self.assertEqual(
            scoped_visibility["manual_fallback"]["fallback_state"],
            "execution_rejected",
        )
        self.assertIn(
            "execution rejected",
            scoped_visibility["manual_fallback"]["blocked_reason"],
        )

    def test_service_phase21_restore_prefers_canonical_manual_fallback_timestamp(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep legacy manual fallback timestamps auditable after restore.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Legacy fallback timestamps must not rewrite the reviewed record.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-restore-fallback-alias-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-restore-fallback-alias-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Notified the accountable repository owner using the approved manual procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement.",
        )

        case_with_fallback = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(case_with_fallback)
        assert case_with_fallback is not None
        action_review_visibility = dict(
            case_with_fallback.reviewed_context["action_review_visibility"]
        )
        scoped_visibility = dict(action_review_visibility[action_request.action_request_id])
        manual_fallback = dict(scoped_visibility["manual_fallback"])
        manual_fallback["performed_at"] = (
            reviewed_at + timedelta(minutes=50)
        ).isoformat()
        scoped_visibility["manual_fallback"] = manual_fallback
        action_review_visibility[action_request.action_request_id] = scoped_visibility
        service.persist_record(
            replace(
                case_with_fallback,
                reviewed_context={
                    **dict(case_with_fallback.reviewed_context),
                    "action_review_visibility": action_review_visibility,
                },
            )
        )

        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=restored_store,
        )

        restored_service.restore_authoritative_record_chain_backup(backup)
        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        runtime_visibility = restored_case_detail.current_action_review["runtime_visibility"]

        self.assertEqual(
            runtime_visibility["manual_fallback"]["fallback_at"],
            (reviewed_at + timedelta(minutes=45)).isoformat(),
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )

    def test_manual_fallback_rejects_unrelated_alert_scoped_evidence(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep alert-scoped fallback evidence linked to the correct alert.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Record the approved alert-scoped fallback without borrowing other alerts' evidence.",
            escalation_reason="The approved alert-scoped follow-up cannot wait for the next shift.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-alert-scoped-fallback-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-alert-scoped-fallback-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        action_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                case_id=None,
                lifecycle_state="unresolved",
            )
        )

        unrelated_admission = service.ingest_finding_alert(
            finding_id="finding-phase21-alert-scoped-fallback-unrelated-001",
            analytic_signal_id="signal-phase21-alert-scoped-fallback-unrelated-001",
            substrate_detection_record_id=(
                "substrate-detection-phase21-alert-scoped-fallback-unrelated-001"
            ),
            correlation_key="claim:asset-phase21-alert-scoped-fallback-unrelated-001:synthetic",
            first_seen_at=reviewed_at + timedelta(minutes=1),
            last_seen_at=reviewed_at + timedelta(minutes=1),
            reviewed_context={
                "asset": {"asset_id": "asset-phase21-alert-scoped-fallback-unrelated-001"},
                "identity": {
                    "identity_id": "principal-phase21-alert-scoped-fallback-unrelated-001"
                },
                "source": {
                    "source_family": "synthetic_review_fixture",
                    "admission_kind": "synthetic",
                },
            },
        )
        unrelated_evidence_id = "evidence-phase21-alert-scoped-fallback-unrelated-001"
        service.persist_record(
            EvidenceRecord(
                evidence_id=unrelated_evidence_id,
                source_record_id=unrelated_admission.alert.finding_id,
                alert_id=unrelated_admission.alert.alert_id,
                case_id=None,
                source_system="synthetic",
                collector_identity="collector://synthetic/fixture",
                acquired_at=reviewed_at + timedelta(minutes=1),
                derivation_relationship="finding_alert",
                lifecycle_state="collected",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            f"verification_evidence_ids contains evidence {unrelated_evidence_id!r} that is not linked to alert {promoted_case.alert_id!r}",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=action_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=15),
                fallback_actor_identity="analyst-001",
                authority_boundary="approved_human_fallback",
                reason="Only evidence from the same alert or a real shared case should be allowed.",
                action_taken="No manual fallback should be recorded with unrelated evidence.",
                verification_evidence_ids=(evidence_id, unrelated_evidence_id),
            )

        current_action_review = service.inspect_case_detail(promoted_case.case_id).current_action_review
        self.assertNotIn(
            "manual_fallback",
            current_action_review["runtime_visibility"] or {},
        )

    def test_manual_fallback_requires_approved_post_approval_action_review(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep manual fallback approval-bound.",
        )
        pending_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Review before any fallback path is used.",
            escalation_reason="Pending approval must not masquerade as manual fallback.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-manual-fallback-pending-001",
        )

        with self.assertRaisesRegex(
            ValueError,
            "manual fallback requires an approved action review in a live post-approval state",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=pending_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=15),
                fallback_actor_identity="analyst-001",
                authority_boundary="approved_human_fallback",
                reason="Pending approvals must not write fallback visibility.",
                action_taken="No manual action should be recorded.",
                verification_evidence_ids=(evidence_id,),
            )

        rejected_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-manual-fallback-rejected-001",
                action_request_id=pending_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(pending_request.target_scope),
                payload_hash=pending_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=20),
                lifecycle_state="rejected",
            )
        )
        rejected_request = service.persist_record(
            replace(
                pending_request,
                approval_decision_id=rejected_decision.approval_decision_id,
                lifecycle_state="rejected",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "manual fallback requires an approved action review in a live post-approval state",
        ):
            service.record_action_review_manual_fallback(
                action_request_id=rejected_request.action_request_id,
                fallback_at=reviewed_at + timedelta(minutes=25),
                fallback_actor_identity="analyst-001",
                authority_boundary="approved_human_fallback",
                reason="Rejected approvals must not write fallback visibility.",
                action_taken="No manual action should be recorded.",
                verification_evidence_ids=(evidence_id,),
            )

        current_action_review = service.inspect_case_detail(promoted_case.case_id).current_action_review
        self.assertNotIn(
            "manual_fallback",
            current_action_review["runtime_visibility"] or {},
        )

    def test_service_phase21_restore_preserves_handoff_and_manual_fallback_runtime_visibility(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Waiting until the next business-hours cycle is unsafe for this repository owner change.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-restore-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-restore-visibility-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        promoted_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the unresolved approval review at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        promoted_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Keep the unresolved action visible for the next analyst handoff.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )
        service.record_action_review_manual_fallback(
            action_request_id=action_request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Notified the accountable repository owner using the approved manual procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement.",
        )
        service.record_action_review_escalation_note(
            action_request_id=action_request.action_request_id,
            escalated_at=reviewed_at + timedelta(minutes=15),
            escalated_by_identity="analyst-004",
            escalated_to="on-call-manager-001",
            note="On-call manager notified because the unresolved action could not be left unattended.",
        )

        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restored_service.restore_authoritative_record_chain_backup(backup)
        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        runtime_visibility = restored_case_detail.current_action_review["runtime_visibility"]

        self.assertEqual(
            runtime_visibility["after_hours_handoff"]["handoff_owner"],
            "analyst-002",
        )
        self.assertEqual(
            runtime_visibility["after_hours_handoff"]["recorded_at"],
            (reviewed_at + timedelta(hours=8)).isoformat(),
        )
        self.assertEqual(
            runtime_visibility["after_hours_handoff"]["rationale"],
            "Keep the unresolved action visible for the next analyst handoff.",
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["fallback_owner_id"],
            "repo-owner-001",
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["fallback_state"],
            "shuffle_unavailable",
        )
        self.assertIn(
            "shuffle unavailable",
            runtime_visibility["manual_fallback"]["blocked_reason"],
        )
        self.assertEqual(
            runtime_visibility["manual_fallback"]["follow_up_state"],
            "manual_follow_up_pending",
        )
        self.assertEqual(
            runtime_visibility["escalation_notes"]["escalated_to"],
            "on-call-manager-001",
        )
        self.assertEqual(
            runtime_visibility["escalation_notes"]["escalated_by_identity"],
            "analyst-004",
        )

    def test_escalation_visibility_requires_recorded_note_and_preserves_recorded_state(self) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep escalation visibility record-driven.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Escalate the reviewed request if waiting is unsafe.",
            escalation_reason="The pending review cannot wait for the next shift.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase21-escalation-state-001",
        )

        initial_review = service.inspect_case_detail(promoted_case.case_id).current_action_review
        self.assertNotIn("escalation_notes", initial_review["runtime_visibility"] or {})

        service.record_action_review_escalation_note(
            action_request_id=action_request.action_request_id,
            escalated_at=reviewed_at + timedelta(minutes=10),
            escalated_by_identity="analyst-009",
            escalated_to="on-call-manager-001",
            note="Pending review escalated before any approval decision existed.",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-escalation-state-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=20),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        runtime_visibility = service.inspect_case_detail(promoted_case.case_id).current_action_review[
            "runtime_visibility"
        ]
        self.assertEqual(runtime_visibility["escalation_notes"]["review_state"], "pending")
        self.assertEqual(
            runtime_visibility["escalation_notes"]["escalated_by_identity"],
            "analyst-009",
        )
