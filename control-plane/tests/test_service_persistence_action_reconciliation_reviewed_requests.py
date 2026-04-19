from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _service_persistence_support as support
from _service_persistence_support import ServicePersistenceTestBase

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value




class ReviewedActionRequestPersistenceTests(ServicePersistenceTestBase):
    def test_service_creates_approval_bound_action_request_from_reviewed_recommendation(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
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
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertIsNone(action_request.approval_decision_id)
        self.assertEqual(action_request.case_id, promoted_case.case_id)
        self.assertEqual(action_request.alert_id, promoted_case.alert_id)
        self.assertEqual(action_request.finding_id, promoted_case.finding_id)
        self.assertEqual(action_request.requester_identity, "analyst-001")
        self.assertEqual(
            action_request.target_scope,
            {
                "record_family": "recommendation",
                "record_id": recommendation.recommendation_id,
                "case_id": promoted_case.case_id,
                "alert_id": promoted_case.alert_id,
                "finding_id": promoted_case.finding_id,
                "recipient_identity": "repo-owner-001",
            },
        )
        self.assertEqual(
            action_request.requested_payload,
            {
                "action_type": "notify_identity_owner",
                "recipient_identity": "repo-owner-001",
                "message_intent": "Notify the accountable repository owner about the reviewed permission change.",
                "escalation_reason": "Reviewed GitHub audit evidence requires bounded owner notification.",
                "source_record_family": "recommendation",
                "source_record_id": recommendation.recommendation_id,
                "recommendation_id": recommendation.recommendation_id,
                "case_id": promoted_case.case_id,
                "alert_id": promoted_case.alert_id,
                "finding_id": promoted_case.finding_id,
                "linked_evidence_ids": (evidence_id,),
            },
        )
        self.assertEqual(
            action_request.payload_hash,
            _approved_binding_hash(
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
            ),
        )
        self.assertEqual(action_request.expires_at, expires_at)
        self.assertEqual(action_request.lifecycle_state, "pending_approval")
        self.assertEqual(
            action_request.policy_evaluation,
            {
                "approval_requirement": "human_required",
                "approval_requirement_override": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )
        self.assertEqual(
            service.get_record(ActionRequestRecord, action_request.action_request_id),
            action_request,
        )
        self.assertEqual(store.list(ActionExecutionRecord), ())
    def test_service_does_not_emit_action_request_created_log_before_commit(
        self,
    ) -> None:
        base_store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Prepare a reviewed owner notification request.",
        )
        failing_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=_CommitFailingStore(base_store),
        )
        baseline_requests = base_store.list(ActionRequestRecord)

        with mock.patch.object(failing_service, "_emit_structured_event") as emit_event:
            with self.assertRaisesRegex(RuntimeError, "synthetic commit failure"):
                failing_service.create_reviewed_action_request_from_advisory(
                    record_family="recommendation",
                    record_id=recommendation.recommendation_id,
                    requester_identity="analyst-001",
                    recipient_identity="repo-owner-001",
                    message_intent="Notify the repository owner about the reviewed change.",
                    escalation_reason="Reviewed low-risk action remains approval-bound.",
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
                )

        emit_event.assert_not_called()
        self.assertEqual(base_store.list(ActionRequestRecord), baseline_requests)
    def test_service_executes_phase20_first_live_action_end_to_end_from_reviewed_recommendation(
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
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-e2e-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertEqual(
            approved_request.requested_payload["action_type"],
            "notify_identity_owner",
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "succeeded")
        self.assertEqual(stored_execution.approval_decision_id, "approval-phase20-e2e-001")
        self.assertEqual(stored_execution.execution_surface_type, "automation_substrate")
        self.assertEqual(stored_execution.execution_surface_id, "shuffle")
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.execution_run_id, execution.execution_run_id)
        self.assertEqual(
            reconciliation.subject_linkage["action_request_ids"],
            (approved_request.action_request_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["approval_decision_ids"],
            ("approval-phase20-e2e-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["delegation_ids"],
            (execution.delegation_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["evidence_ids"],
            (evidence_id,),
        )
    def test_service_phase20_first_live_action_fail_closes_on_downstream_execution_surface_mismatch(
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
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-mismatch-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "n8n",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(stored_execution.execution_surface_id, "shuffle")
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(
            reconciliation.mismatch_summary,
            "execution surface/idempotency mismatch between approved request and observed execution",
        )
        self.assertEqual(
            reconciliation.subject_linkage["approval_decision_ids"],
            ("approval-phase20-mismatch-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
    def test_service_reconciliation_rolls_back_execution_state_when_reconciliation_write_fails(
        self,
    ) -> None:
        base_store, seed_service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = seed_service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = seed_service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = seed_service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-reconciliation-atomic-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = seed_service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        execution = seed_service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        existing_reconciliation_ids = {
            record.reconciliation_id for record in base_store.list(ReconciliationRecord)
        }
        failing_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=_RecordTypeSaveFailingStore(
                inner=base_store,
                record_type=ReconciliationRecord,
                message="synthetic reconciliation save failure",
            ),
        )

        with mock.patch.object(failing_service, "_emit_structured_event") as emit_event:
            with self.assertRaisesRegex(
                RuntimeError,
                "synthetic reconciliation save failure",
            ):
                failing_service.reconcile_action_execution(
                    action_request_id=approved_request.action_request_id,
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    observed_executions=(
                        {
                            "execution_run_id": execution.execution_run_id,
                            "execution_surface_id": "shuffle",
                            "idempotency_key": approved_request.idempotency_key,
                            "approval_decision_id": execution.approval_decision_id,
                            "delegation_id": execution.delegation_id,
                            "payload_hash": execution.payload_hash,
                            "observed_at": observed_at,
                            "status": "success",
                        },
                    ),
                    compared_at=compared_at,
                    stale_after=stale_after,
                )

        emit_event.assert_not_called()
        stored_execution = base_store.get(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(
            {
                record.reconciliation_id
                for record in base_store.list(ReconciliationRecord)
            },
            existing_reconciliation_ids,
        )
    def test_service_reconciliation_does_not_downgrade_authoritative_execution_lifecycle(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-reconciliation-monotonic-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        service.persist_record(replace(execution, lifecycle_state="running"))

        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": "queued",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "running")
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(
            service._execution_coordinator._action_execution_lifecycle_from_status(
                "running",
                "succeeded",
            ),
            "succeeded",
        )
    def test_service_phase20_reconciliation_rejects_downstream_evidence_missing_binding_identifiers(
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
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-missing-binding-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )

        with self.assertRaisesRegex(
            ValueError,
            "observed execution must include string approval_decision_id",
        ):
            service.reconcile_action_execution(
                action_request_id=approved_request.action_request_id,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=(
                    {
                        "execution_run_id": execution.execution_run_id,
                        "execution_surface_id": "shuffle",
                        "idempotency_key": approved_request.idempotency_key,
                        "observed_at": observed_at,
                        "status": "success",
                    },
                ),
                compared_at=compared_at,
                stale_after=stale_after,
            )
    def test_service_rejects_reviewed_action_request_creation_when_malformed_or_out_of_scope(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        future_expiry = datetime.now(timezone.utc) + timedelta(hours=4)

        with self.assertRaisesRegex(
            ValueError,
            "recipient_identity must be a non-empty string",
        ):
            service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=future_expiry,
            )

        replay_service, replay_case, _, _ = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )
        replay_recommendation = replay_service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase20-out-of-scope-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=replay_case.alert_id,
                case_id=replay_case.case_id,
                ai_trace_id=None,
                review_owner="analyst-001",
                intended_outcome="Synthetic advisory reads must fail closed.",
                lifecycle_state="under_review",
                reviewed_context=replay_case.reviewed_context,
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            replay_service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=replay_recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=future_expiry,
            )
    def test_service_reuses_reviewed_action_request_for_matching_idempotency_key(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertEqual(second_request, first_request)
        self.assertEqual(store.list(ActionRequestRecord), (first_request,))

    def test_service_reuses_reviewed_action_request_for_equivalent_expiry_instants(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at_utc = datetime.now(timezone.utc) + timedelta(hours=4)
        expires_at_plus_two = expires_at_utc.astimezone(
            timezone(timedelta(hours=2))
        )

        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at_utc,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at_plus_two,
        )

        self.assertEqual(second_request, first_request)
        self.assertEqual(store.list(ActionRequestRecord), (first_request,))


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str,
) -> unittest.TestSuite:
    return unittest.TestSuite()
    def test_service_reuses_reviewed_action_request_for_equivalent_expiry_instants(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at_utc = datetime.now(timezone.utc) + timedelta(hours=4)
        expires_at_plus_two = expires_at_utc.astimezone(
            timezone(timedelta(hours=2))
        )

        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at_utc,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at_plus_two,
        )

        self.assertEqual(second_request, first_request)
        self.assertEqual(store.list(ActionRequestRecord), (first_request,))
