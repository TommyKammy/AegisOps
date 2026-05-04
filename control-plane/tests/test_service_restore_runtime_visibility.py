from __future__ import annotations

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _restore_readiness_test_support as support

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value


class RestoreRuntimeVisibilityTests(ServicePersistenceTestBase):
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
