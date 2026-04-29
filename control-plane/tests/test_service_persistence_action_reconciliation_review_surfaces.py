from __future__ import annotations
# ruff: noqa: E402

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _service_persistence_support as support
from aegisops_control_plane import action_review_projection
from _service_persistence_support import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AegisOpsControlPlaneService,
    ApprovalDecisionRecord,
    RecommendationRecord,
    RuntimeConfig,
    ServicePersistenceTestBase,
    _ListCountingStore,
    _TransactionMutationStore,
    _approved_payload_binding_hash,
    datetime,
    make_store,
    replace,
    timedelta,
    timezone,
)

class ActionReviewSurfacePersistenceTests(ServicePersistenceTestBase):
    def test_action_review_path_health_preserves_overdue_reconciliation_without_execution(
        self,
    ) -> None:
        requested_at = datetime(2026, 4, 27, 9, 0, tzinfo=timezone.utc)
        expires_at = requested_at + timedelta(minutes=30)
        action_request = ActionRequestRecord(
            action_request_id="action-request-path-health-reconciliation-no-execution-001",
            approval_decision_id="approval-path-health-reconciliation-no-execution-001",
            case_id="case-path-health-reconciliation-no-execution-001",
            alert_id="alert-path-health-reconciliation-no-execution-001",
            finding_id="finding-path-health-reconciliation-no-execution-001",
            idempotency_key="idempotency-path-health-reconciliation-no-execution-001",
            target_scope={
                "record_family": "recommendation",
                "record_id": "recommendation-path-health-reconciliation-no-execution-001",
                "case_id": "case-path-health-reconciliation-no-execution-001",
                "alert_id": "alert-path-health-reconciliation-no-execution-001",
                "finding_id": "finding-path-health-reconciliation-no-execution-001",
                "recipient_identity": "repo-owner-001",
            },
            payload_hash="payload-hash-path-health-reconciliation-no-execution-001",
            requested_at=requested_at,
            expires_at=expires_at,
            lifecycle_state="approved",
            requester_identity="analyst-001",
            requested_payload={
                "action_type": "notify_identity_owner",
                "recipient_identity": "repo-owner-001",
            },
        )
        approval = ApprovalDecisionRecord(
            approval_decision_id="approval-path-health-reconciliation-no-execution-001",
            action_request_id=action_request.action_request_id,
            approver_identities=("approver-001",),
            target_snapshot=dict(action_request.target_scope),
            payload_hash=action_request.payload_hash,
            decided_at=requested_at + timedelta(minutes=5),
            lifecycle_state="approved",
            approved_expires_at=expires_at,
        )
        reconciliation = support.ReconciliationRecord(
            reconciliation_id="reconciliation-path-health-no-execution-001",
            subject_linkage={
                "action_request_ids": (action_request.action_request_id,),
                "approval_decision_ids": (approval.approval_decision_id,),
            },
            alert_id=action_request.alert_id,
            finding_id=action_request.finding_id,
            analytic_signal_id=None,
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key=f"reconciliation-no-execution:{action_request.action_request_id}",
            first_seen_at=requested_at + timedelta(minutes=10),
            last_seen_at=requested_at + timedelta(minutes=10),
            ingest_disposition="matched",
            mismatch_summary="reconciliation observed without persisted execution",
            compared_at=requested_at + timedelta(minutes=11),
            lifecycle_state="matched",
        )

        path_health = action_review_projection.action_review_path_health(
            service=None,
            action_request=action_request,
            approval_decision=approval,
            action_execution=None,
            reconciliation=reconciliation,
            review_state="approved",
            as_of=expires_at + timedelta(minutes=5),
        )

        self.assertEqual(path_health["overall_state"], "degraded")
        self.assertEqual(
            path_health["paths"]["ingest"]["reason"],
            "observations_current",
        )
        self.assertEqual(
            path_health["paths"]["delegation"]["reason"],
            "reviewed_delegation_record_missing",
        )
        self.assertEqual(
            path_health["paths"]["provider"]["reason"],
            "provider_execution_record_missing",
        )
        self.assertEqual(
            path_health["paths"]["persistence"]["reason"],
            "reconciliation_execution_lineage_missing",
        )

    def test_action_review_path_health_treats_executing_without_execution_as_reviewed(
        self,
    ) -> None:
        requested_at = datetime(2026, 4, 27, 9, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-path-health-executing-no-execution-001",
            approval_decision_id=None,
            case_id="case-path-health-executing-no-execution-001",
            alert_id="alert-path-health-executing-no-execution-001",
            finding_id="finding-path-health-executing-no-execution-001",
            idempotency_key="idempotency-path-health-executing-no-execution-001",
            target_scope={
                "record_family": "recommendation",
                "record_id": "recommendation-path-health-executing-no-execution-001",
                "case_id": "case-path-health-executing-no-execution-001",
                "alert_id": "alert-path-health-executing-no-execution-001",
                "finding_id": "finding-path-health-executing-no-execution-001",
                "recipient_identity": "repo-owner-001",
            },
            payload_hash="payload-hash-path-health-executing-no-execution-001",
            requested_at=requested_at,
            expires_at=requested_at + timedelta(hours=1),
            lifecycle_state="executing",
            requester_identity="analyst-001",
            requested_payload={
                "action_type": "notify_identity_owner",
                "recipient_identity": "repo-owner-001",
            },
        )

        path_health = action_review_projection.action_review_path_health(
            service=None,
            action_request=action_request,
            approval_decision=None,
            action_execution=None,
            reconciliation=None,
            review_state="executing",
            as_of=requested_at + timedelta(minutes=10),
        )

        self.assertEqual(path_health["overall_state"], "delayed")
        self.assertEqual(
            path_health["paths"]["delegation"]["reason"],
            "awaiting_reviewed_delegation",
        )

    def test_action_review_reconciliation_detail_names_expected_received_and_closeout_guidance(
        self,
    ) -> None:
        compared_at = datetime(2026, 4, 27, 9, 0, tzinfo=timezone.utc)
        mismatch_detail = action_review_projection.action_review_reconciliation_detail(
            support.ReconciliationRecord(
                reconciliation_id="reconciliation-detail-mismatch-001",
                subject_linkage={
                    "action_request_ids": ("action-request-detail-mismatch-001",),
                    "action_execution_ids": ("action-execution-detail-mismatch-001",),
                },
                alert_id="alert-detail-mismatch-001",
                finding_id="finding-detail-mismatch-001",
                analytic_signal_id=None,
                execution_run_id="execution-run-observed-mismatch-001",
                linked_execution_run_ids=("execution-run-observed-mismatch-001",),
                correlation_key="correlation-detail-mismatch-001",
                first_seen_at=compared_at - timedelta(minutes=5),
                last_seen_at=compared_at - timedelta(minutes=1),
                ingest_disposition="mismatch",
                mismatch_summary="receipt payload disagrees with AegisOps expected ticket state",
                compared_at=compared_at,
                lifecycle_state="mismatched",
            )
        )
        stale_detail = action_review_projection.action_review_reconciliation_detail(
            support.ReconciliationRecord(
                reconciliation_id="reconciliation-detail-stale-001",
                subject_linkage={
                    "action_request_ids": ("action-request-detail-stale-001",),
                    "action_execution_ids": ("action-execution-detail-stale-001",),
                },
                alert_id="alert-detail-stale-001",
                finding_id="finding-detail-stale-001",
                analytic_signal_id=None,
                execution_run_id="execution-run-observed-stale-001",
                linked_execution_run_ids=("execution-run-observed-stale-001",),
                correlation_key="correlation-detail-stale-001",
                first_seen_at=compared_at - timedelta(minutes=10),
                last_seen_at=compared_at - timedelta(minutes=9),
                ingest_disposition="stale",
                mismatch_summary="receipt is older than the reviewed action state",
                compared_at=compared_at,
                lifecycle_state="stale",
            )
        )
        matched_detail = action_review_projection.action_review_reconciliation_detail(
            support.ReconciliationRecord(
                reconciliation_id="reconciliation-detail-matched-001",
                subject_linkage={
                    "action_request_ids": ("action-request-detail-matched-001",),
                    "action_execution_ids": ("action-execution-detail-matched-001",),
                },
                alert_id="alert-detail-matched-001",
                finding_id="finding-detail-matched-001",
                analytic_signal_id=None,
                execution_run_id="execution-run-observed-matched-001",
                linked_execution_run_ids=("execution-run-observed-matched-001",),
                correlation_key="correlation-detail-matched-001",
                first_seen_at=compared_at - timedelta(minutes=3),
                last_seen_at=compared_at - timedelta(minutes=1),
                ingest_disposition="matched",
                mismatch_summary="receipt matches the reviewed action state",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )
        missing_detail = action_review_projection.action_review_reconciliation_detail(None)

        self.assertEqual(
            mismatch_detail["expected_aegisops_state"],
            "matched",
        )
        self.assertEqual(
            mismatch_detail["authoritative_aegisops_state"],
            "mismatched",
        )
        self.assertEqual(
            mismatch_detail["received_receipt"]["ingest_disposition"],
            "mismatch",
        )
        self.assertTrue(mismatch_detail["action_required"])
        self.assertEqual(
            mismatch_detail["next_step"],
            "review_mismatch_before_closeout",
        )
        self.assertEqual(
            mismatch_detail["closeout_evidence"]["reconciliation_id"],
            "reconciliation-detail-mismatch-001",
        )

        self.assertEqual(
            stale_detail["next_step"],
            "refresh_downstream_receipt_before_closeout",
        )
        self.assertTrue(stale_detail["action_required"])
        self.assertEqual(matched_detail["next_step"], "record_closeout_evidence")
        self.assertFalse(matched_detail["action_required"])
        self.assertEqual(missing_detail["authoritative_aegisops_state"], "missing")
        self.assertEqual(
            missing_detail["next_step"],
            "obtain_authoritative_receipt_before_closeout",
        )
        self.assertTrue(missing_detail["action_required"])

    def test_service_inspect_action_review_detail_anchors_selected_and_current_review(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-detail-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-detail-surface-001",
        )

        detail = service.inspect_action_review_detail(action_request.action_request_id).to_dict()

        self.assertTrue(detail["read_only"])
        self.assertEqual(detail["action_request_id"], action_request.action_request_id)
        self.assertEqual(
            detail["action_review"]["action_request_id"],
            action_request.action_request_id,
        )
        self.assertEqual(
            detail["current_action_review"]["action_request_id"],
            action_request.action_request_id,
        )
        self.assertEqual(detail["case_record"]["case_id"], promoted_case.case_id)
        self.assertEqual(detail["alert_record"]["alert_id"], promoted_case.alert_id)

    def test_service_inspect_action_review_detail_keeps_case_scope_when_optional_alert_link_is_missing(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-detail-002",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-detail-surface-002",
        )
        service.persist_record(
            replace(
                action_request,
                alert_id="missing-alert-record",
            )
        )

        detail = service.inspect_action_review_detail(
            action_request.action_request_id
        ).to_dict()

        self.assertEqual(detail["action_request_id"], action_request.action_request_id)
        self.assertEqual(detail["case_record"]["case_id"], promoted_case.case_id)
        self.assertIsNone(detail["alert_record"])

    def test_service_delegates_action_review_chain_snapshot_to_projection_module(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-projection-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-projection-delegation-001",
        )
        record_index = service._build_action_review_record_index()
        sentinel = {"review_state": "delegated-to-module"}

        with support.mock.patch.object(
            action_review_projection,
            "build_action_review_chain_snapshot",
            autospec=True,
            return_value=sentinel,
        ) as build_snapshot:
            result = service._build_action_review_chain_snapshot(
                action_request,
                record_index=record_index,
            )

        self.assertIs(result, sentinel)
        build_snapshot.assert_called_once_with(
            service,
            action_request,
            record_index=record_index,
        )

    def test_service_inspects_action_review_states_on_queue_alert_and_case_surfaces(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        base_requested_at = datetime.now(timezone.utc)
        pending_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-pending-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=base_requested_at + timedelta(hours=4),
            action_request_id="action-request-surface-pending-001",
        )
        base_requested_at = pending_request.requested_at
        rejected_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-rejected-001",
                action_request_id="action-request-surface-rejected-001",
                approver_identities=("approver-rejected-001",),
                target_snapshot=dict(pending_request.target_scope),
                payload_hash=pending_request.payload_hash,
                decided_at=base_requested_at + timedelta(minutes=10),
                lifecycle_state="rejected",
            )
        )
        rejected_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-surface-rejected-001",
                approval_decision_id=rejected_decision.approval_decision_id,
                idempotency_key="idempotency-surface-rejected-001",
                requested_at=base_requested_at + timedelta(minutes=5),
                lifecycle_state="rejected",
                requester_identity="analyst-002",
            )
        )
        expired_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-expired-001",
                action_request_id="action-request-surface-expired-001",
                approver_identities=("approver-expired-001",),
                target_snapshot=dict(pending_request.target_scope),
                payload_hash=pending_request.payload_hash,
                decided_at=base_requested_at + timedelta(minutes=20),
                lifecycle_state="expired",
                approved_expires_at=base_requested_at + timedelta(minutes=30),
            )
        )
        expired_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-surface-expired-001",
                approval_decision_id=expired_decision.approval_decision_id,
                idempotency_key="idempotency-surface-expired-001",
                requested_at=base_requested_at + timedelta(minutes=15),
                expires_at=base_requested_at + timedelta(minutes=30),
                lifecycle_state="expired",
                requester_identity="analyst-003",
            )
        )
        superseded_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-surface-superseded-001",
                idempotency_key="idempotency-surface-superseded-001",
                requested_at=base_requested_at + timedelta(minutes=25),
                lifecycle_state="superseded",
                requester_identity="analyst-004",
            )
        )
        replacement_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-surface-replacement-001",
                idempotency_key="idempotency-surface-replacement-001",
                requested_at=base_requested_at + timedelta(minutes=35),
                requester_identity="analyst-005",
            )
        )

        queue_snapshot = service.inspect_analyst_queue().to_dict()
        alert_snapshot = service.inspect_alert_detail(promoted_case.alert_id).to_dict()
        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()

        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["action_request_id"],
            replacement_request.action_request_id,
        )
        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["review_state"],
            "pending",
        )
        self.assertEqual(alert_snapshot["current_action_review"]["review_state"], "pending")
        self.assertEqual(case_snapshot["current_action_review"]["review_state"], "pending")
        action_reviews_by_id = {
            record["action_request_id"]: record for record in case_snapshot["action_reviews"]
        }
        self.assertEqual(
            action_reviews_by_id[pending_request.action_request_id]["review_state"],
            "pending",
        )
        self.assertEqual(
            action_reviews_by_id[rejected_request.action_request_id]["review_state"],
            "rejected",
        )
        self.assertEqual(
            action_reviews_by_id[rejected_request.action_request_id]["approver_identities"],
            ["approver-rejected-001"],
        )
        self.assertEqual(
            action_reviews_by_id[expired_request.action_request_id]["review_state"],
            "expired",
        )
        self.assertEqual(
            action_reviews_by_id[superseded_request.action_request_id]["review_state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[superseded_request.action_request_id]["approval_state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[superseded_request.action_request_id]["timeline"][1]["state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[superseded_request.action_request_id][
                "replacement_action_request_id"
            ],
            replacement_request.action_request_id,
        )
    def test_service_action_review_surfaces_keep_execution_linked_reconciliation_when_approval_lookup_is_missing(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-indexed-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=support.datetime.now(support.timezone.utc)
            + support.timedelta(hours=4),
            action_request_id="action-request-surface-indexed-lineage-001",
        )
        action_request = service.persist_record(
            support.replace(
                action_request,
                approval_decision_id="approval-surface-missing-indexed-001",
                lifecycle_state="approved",
            )
        )
        action_execution = service.persist_record(
            support.ActionExecutionRecord(
                action_execution_id="action-execution-surface-indexed-lineage-001",
                action_request_id=action_request.action_request_id,
                approval_decision_id="approval-surface-missing-indexed-001",
                delegation_id="delegation-surface-indexed-lineage-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-surface-indexed-lineage-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=action_request.requested_at
                + support.timedelta(minutes=10),
                expires_at=action_request.expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="queued",
            )
        )
        reconciliation = service.persist_record(
            support.ReconciliationRecord(
                reconciliation_id="reconciliation-surface-indexed-lineage-001",
                subject_linkage={
                    "case_ids": (promoted_case.case_id,),
                    "action_execution_ids": (action_execution.action_execution_id,),
                    "delegation_ids": (action_execution.delegation_id,),
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id="execution-run-surface-indexed-lineage-observed-001",
                linked_execution_run_ids=(
                    "execution-run-surface-indexed-lineage-observed-001",
                ),
                correlation_key="surface-indexed-lineage-001",
                first_seen_at=action_execution.delegated_at
                + support.timedelta(minutes=1),
                last_seen_at=action_execution.delegated_at
                + support.timedelta(minutes=2),
                ingest_disposition="mismatch",
                mismatch_summary="execution lineage should remain visible without approval lookup",
                compared_at=action_execution.delegated_at
                + support.timedelta(minutes=3),
                lifecycle_state="mismatched",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_review = case_snapshot["current_action_review"]

        self.assertEqual(
            action_review["action_request_id"],
            action_request.action_request_id,
        )
        self.assertEqual(
            action_review["action_execution_id"],
            action_execution.action_execution_id,
        )
        self.assertEqual(
            action_review["reconciliation_id"],
            reconciliation.reconciliation_id,
        )
        self.assertEqual(
            action_review["timeline"][4]["record_id"],
            reconciliation.reconciliation_id,
        )
        self.assertEqual(
            action_review["mismatch_inspection"]["reconciliation_id"],
            reconciliation.reconciliation_id,
        )
    def test_service_analyst_queue_prefetches_action_review_records_once_per_inspection(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
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
            requester_identity="analyst-002",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        store.list_calls = 0
        store.reconciliation_list_calls = 0
        queue_snapshot = service.inspect_analyst_queue().to_dict()

        self.assertEqual(queue_snapshot["total_records"], 1)
        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["action_request_id"],
            second_request.action_request_id,
        )
        self.assertLessEqual(store.list_calls, 7)
        self.assertEqual(store.reconciliation_list_calls, 2)
        self.assertNotEqual(first_request.action_request_id, second_request.action_request_id)
    def test_service_action_review_surfaces_prefer_live_approval_and_execution_records(
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
        approved_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-approved-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-stale-approved-001",
        )
        approved_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-stale-approved-001",
                action_request_id=approved_request.action_request_id,
                approver_identities=("approver-approved-001",),
                target_snapshot=dict(approved_request.target_scope),
                payload_hash=approved_request.payload_hash,
                decided_at=approved_request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            replace(
                approved_request,
                approval_decision_id=approved_decision.approval_decision_id,
                lifecycle_state="pending_approval",
            )
        )

        executing_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-002",
            recipient_identity="repo-owner-executing-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-stale-executing-001",
        )
        executing_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-stale-executing-001",
                action_request_id=executing_request.action_request_id,
                approver_identities=("approver-executing-001",),
                target_snapshot=dict(executing_request.target_scope),
                payload_hash=executing_request.payload_hash,
                decided_at=executing_request.requested_at + timedelta(minutes=10),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            replace(
                executing_request,
                approval_decision_id=executing_decision.approval_decision_id,
                lifecycle_state="pending_approval",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-surface-stale-executing-001",
                action_request_id=executing_request.action_request_id,
                approval_decision_id=executing_decision.approval_decision_id,
                delegation_id="delegation-surface-stale-executing-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                execution_run_id="execution-run-surface-stale-executing-001",
                idempotency_key=executing_request.idempotency_key,
                target_scope=dict(executing_request.target_scope),
                approved_payload=dict(executing_request.requested_payload),
                payload_hash=executing_request.payload_hash,
                delegated_at=executing_request.requested_at + timedelta(minutes=15),
                expires_at=expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="queued",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_reviews_by_id = {
            record["action_request_id"]: record for record in case_snapshot["action_reviews"]
        }

        self.assertEqual(
            action_reviews_by_id[approved_request.action_request_id]["review_state"],
            "approved",
        )
        self.assertEqual(
            action_reviews_by_id[approved_request.action_request_id]["next_expected_action"],
            "await_reviewed_delegation",
        )
        self.assertEqual(
            action_reviews_by_id[approved_request.action_request_id]["approval_state"],
            "approved",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id]["review_state"],
            "executing",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id][
                "next_expected_action"
            ],
            "await_execution_reconciliation",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id][
                "action_execution_id"
            ],
            "action-execution-surface-stale-executing-001",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id][
                "execution_surface_type"
            ],
            "automation_substrate",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id][
                "execution_surface_id"
            ],
            "n8n",
        )
    def test_service_action_review_surfaces_keep_policy_authorized_requests_out_of_review_chains(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        reviewed_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-reviewed-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-surface-reviewed-superseded-001",
        )
        reviewed_request = service.persist_record(
            replace(
                reviewed_request,
                lifecycle_state="superseded",
            )
        )
        reviewed_replacement = service.persist_record(
            replace(
                reviewed_request,
                action_request_id="action-request-surface-reviewed-replacement-001",
                idempotency_key="idempotency-surface-reviewed-replacement-001",
                requested_at=reviewed_request.requested_at + timedelta(minutes=10),
                lifecycle_state="pending_approval",
                requester_identity="analyst-002",
            )
        )
        policy_authorized_request = service.persist_record(
            replace(
                reviewed_request,
                action_request_id="action-request-surface-policy-authorized-001",
                approval_decision_id=None,
                idempotency_key="idempotency-surface-policy-authorized-001",
                requested_at=reviewed_request.requested_at + timedelta(minutes=20),
                lifecycle_state="approved",
                requester_identity="policy-engine",
                policy_evaluation={
                    "approval_requirement": "policy_authorized",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        queue_snapshot = service.inspect_analyst_queue().to_dict()
        alert_snapshot = service.inspect_alert_detail(promoted_case.alert_id).to_dict()
        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_reviews_by_id = {
            record["action_request_id"]: record for record in case_snapshot["action_reviews"]
        }

        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["action_request_id"],
            reviewed_replacement.action_request_id,
        )
        self.assertEqual(
            alert_snapshot["current_action_review"]["action_request_id"],
            reviewed_replacement.action_request_id,
        )
        self.assertEqual(
            case_snapshot["current_action_review"]["action_request_id"],
            reviewed_replacement.action_request_id,
        )
        self.assertNotIn(
            policy_authorized_request.action_request_id,
            action_reviews_by_id,
        )
        self.assertEqual(
            action_reviews_by_id[reviewed_request.action_request_id][
                "replacement_action_request_id"
            ],
            reviewed_replacement.action_request_id,
        )
    def test_service_action_review_surfaces_preserve_terminal_execution_states(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-completed-execution-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-completed-execution-001",
        )
        decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-completed-execution-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-completed-execution-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        request = service.persist_record(
            replace(
                request,
                approval_decision_id=decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-surface-completed-001",
                action_request_id=request.action_request_id,
                approval_decision_id=decision.approval_decision_id,
                delegation_id="delegation-surface-completed-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-surface-completed-001",
                idempotency_key=request.idempotency_key,
                target_scope=dict(request.target_scope),
                approved_payload=dict(request.requested_payload),
                payload_hash=request.payload_hash,
                delegated_at=request.requested_at + timedelta(minutes=10),
                expires_at=expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="succeeded",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_review = case_snapshot["current_action_review"]

        self.assertEqual(
            action_review["action_request_id"],
            request.action_request_id,
        )
        self.assertEqual(action_review["review_state"], "completed")
        self.assertEqual(
            action_review["action_execution_state"],
            "succeeded",
        )
        self.assertEqual(
            action_review["next_expected_action"],
            "review_execution_outcome",
        )
    def test_service_action_review_surfaces_preserve_canceled_execution_state(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-canceled-execution-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-canceled-execution-001",
        )
        decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-canceled-execution-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-canceled-execution-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        request = service.persist_record(
            replace(
                request,
                approval_decision_id=decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-surface-canceled-001",
                action_request_id=request.action_request_id,
                approval_decision_id=decision.approval_decision_id,
                delegation_id="delegation-surface-canceled-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-surface-canceled-001",
                idempotency_key=request.idempotency_key,
                target_scope=dict(request.target_scope),
                approved_payload=dict(request.requested_payload),
                payload_hash=request.payload_hash,
                delegated_at=request.requested_at + timedelta(minutes=10),
                expires_at=expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="canceled",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_review = case_snapshot["current_action_review"]

        self.assertEqual(
            action_review["action_request_id"],
            request.action_request_id,
        )
        self.assertEqual(action_review["review_state"], "canceled")
        self.assertEqual(
            action_review["action_execution_state"],
            "canceled",
        )
        self.assertEqual(
            action_review["next_expected_action"],
            "investigate_execution_cancellation",
        )
    def test_service_action_review_surfaces_preserve_failed_execution_state(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-failed-execution-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-failed-execution-001",
        )
        decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-failed-execution-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-failed-execution-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        request = service.persist_record(
            replace(
                request,
                approval_decision_id=decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-surface-failed-001",
                action_request_id=request.action_request_id,
                approval_decision_id=decision.approval_decision_id,
                delegation_id="delegation-surface-failed-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-surface-failed-001",
                idempotency_key=request.idempotency_key,
                target_scope=dict(request.target_scope),
                approved_payload=dict(request.requested_payload),
                payload_hash=request.payload_hash,
                delegated_at=request.requested_at + timedelta(minutes=10),
                expires_at=expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="failed",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_review = case_snapshot["current_action_review"]

        self.assertEqual(
            action_review["action_request_id"],
            request.action_request_id,
        )
        self.assertEqual(action_review["review_state"], "failed")
        self.assertEqual(
            action_review["action_execution_state"],
            "failed",
        )
        self.assertEqual(
            action_review["next_expected_action"],
            "investigate_execution_failure",
        )
    def test_service_action_review_surfaces_use_newest_review_as_current(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        rejected_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-rejected-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-current-rejected-001",
        )
        rejected_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-current-rejected-001",
                action_request_id=rejected_request.action_request_id,
                approver_identities=("approver-rejected-001",),
                target_snapshot=dict(rejected_request.target_scope),
                payload_hash=rejected_request.payload_hash,
                decided_at=rejected_request.requested_at + timedelta(minutes=5),
                lifecycle_state="rejected",
            )
        )
        rejected_request = service.persist_record(
            replace(
                rejected_request,
                approval_decision_id=rejected_decision.approval_decision_id,
                lifecycle_state="rejected",
            )
        )

        completed_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-002",
            recipient_identity="repo-owner-completed-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-current-completed-001",
        )
        completed_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-current-completed-001",
                action_request_id=completed_request.action_request_id,
                approver_identities=("approver-completed-001",),
                target_snapshot=dict(completed_request.target_scope),
                payload_hash=completed_request.payload_hash,
                decided_at=completed_request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        completed_request = service.persist_record(
            replace(
                completed_request,
                approval_decision_id=completed_decision.approval_decision_id,
                lifecycle_state="completed",
            )
        )

        queue_snapshot = service.inspect_analyst_queue().to_dict()
        alert_snapshot = service.inspect_alert_detail(promoted_case.alert_id).to_dict()
        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()

        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["action_request_id"],
            completed_request.action_request_id,
        )
        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["review_state"],
            "completed",
        )
        self.assertEqual(
            alert_snapshot["current_action_review"]["action_request_id"],
            completed_request.action_request_id,
        )
        self.assertEqual(
            case_snapshot["current_action_review"]["action_request_id"],
            completed_request.action_request_id,
        )
        self.assertEqual(
            case_snapshot["action_reviews"][0]["action_request_id"],
            completed_request.action_request_id,
        )
        self.assertEqual(
            case_snapshot["action_reviews"][1]["action_request_id"],
            rejected_request.action_request_id,
        )
    def test_service_action_review_surfaces_find_cross_scope_replacement_requests(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        alert_scoped_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-superseded-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-surface-alert-superseded-001",
        )
        alert_scoped_request = service.persist_record(
            replace(
                alert_scoped_request,
                case_id=None,
                lifecycle_state="superseded",
            )
        )
        replacement_request = service.persist_record(
            replace(
                alert_scoped_request,
                action_request_id="action-request-surface-case-replacement-001",
                case_id=promoted_case.case_id,
                idempotency_key="idempotency-surface-case-replacement-001",
                requested_at=alert_scoped_request.requested_at + timedelta(minutes=15),
                lifecycle_state="pending_approval",
                requester_identity="analyst-002",
            )
        )

        alert_snapshot = service.inspect_alert_detail(promoted_case.alert_id).to_dict()
        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_reviews_by_id = {
            record["action_request_id"]: record for record in case_snapshot["action_reviews"]
        }

        self.assertEqual(
            case_snapshot["current_action_review"]["action_request_id"],
            replacement_request.action_request_id,
        )
        self.assertEqual(
            alert_snapshot["current_action_review"]["action_request_id"],
            replacement_request.action_request_id,
        )
        self.assertEqual(
            action_reviews_by_id[alert_scoped_request.action_request_id]["review_state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[alert_scoped_request.action_request_id][
                "replacement_action_request_id"
            ],
            replacement_request.action_request_id,
        )

    def test_service_action_review_surfaces_require_exact_case_and_alert_scope_match(
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
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep case detail scoped to the authoritative case and alert pair.",
            lead_id=lead.lead_id,
        )
        matching_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-exact-scope-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-surface-exact-scope-001",
        )
        service.persist_record(
            replace(
                matching_request,
                action_request_id="action-request-surface-exact-scope-sibling-001",
                alert_id="alert-surface-exact-scope-sibling-001",
                idempotency_key="idempotency-surface-exact-scope-sibling-001",
                requested_at=matching_request.requested_at + timedelta(minutes=15),
            )
        )
        service.persist_record(
            replace(
                matching_request,
                action_request_id="action-request-surface-exact-scope-sibling-002",
                case_id="case-surface-exact-scope-sibling-001",
                idempotency_key="idempotency-surface-exact-scope-sibling-002",
                requested_at=matching_request.requested_at + timedelta(minutes=30),
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()

        self.assertEqual(
            case_snapshot["current_action_review"]["action_request_id"],
            matching_request.action_request_id,
        )
        self.assertEqual(
            [record["action_request_id"] for record in case_snapshot["action_reviews"]],
            [matching_request.action_request_id],
        )

    def test_approved_payload_binding_hash_normalizes_equivalent_datetime_offsets(
        self,
    ) -> None:
        scheduled_for_utc = datetime.now(timezone.utc) + timedelta(hours=4)
        scheduled_for_plus_two = scheduled_for_utc.astimezone(
            timezone(timedelta(hours=2))
        )

        binding_hash_utc = _approved_payload_binding_hash(
            target_scope={
                "asset_id": "critical-host-001",
                "scheduled_for": scheduled_for_utc,
            },
            approved_payload={
                "action_type": "disable_identity",
                "scheduled_for": scheduled_for_utc,
            },
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        binding_hash_plus_two = _approved_payload_binding_hash(
            target_scope={
                "asset_id": "critical-host-001",
                "scheduled_for": scheduled_for_plus_two,
            },
            approved_payload={
                "action_type": "disable_identity",
                "scheduled_for": scheduled_for_plus_two,
            },
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )

        self.assertEqual(binding_hash_plus_two, binding_hash_utc)
    def test_service_keeps_requester_identity_inside_reviewed_action_request_deduplication(
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
            requester_identity="analyst-002",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertNotEqual(second_request.action_request_id, first_request.action_request_id)
        self.assertEqual(first_request.requester_identity, "analyst-001")
        self.assertEqual(second_request.requester_identity, "analyst-002")
        self.assertNotEqual(second_request.idempotency_key, first_request.idempotency_key)
        persisted_by_requester = {
            record.requester_identity: record
            for record in store.list(ActionRequestRecord)
        }
        self.assertEqual(
            persisted_by_requester,
            {
                "analyst-001": first_request,
                "analyst-002": second_request,
            },
        )
    def test_service_rechecks_reviewed_action_request_context_inside_transaction(
        self,
    ) -> None:
        inner_store, _ = make_store()
        (
            _,
            base_service,
            promoted_case,
            evidence_id,
            reviewed_at,
        ) = self._build_phase19_in_scope_case(store=inner_store)
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = base_service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = base_service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        store = _TransactionMutationStore(
            inner=inner_store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(
                    transactional_store.get(
                        RecommendationRecord,
                        recommendation.recommendation_id,
                    ),
                    intended_outcome=(
                        "Execute an organization-wide response immediately without waiting "
                        "for approval."
                    ),
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "reviewed advisory context is not ready for approval-bound action requests",
        ):
            service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            )

        self.assertEqual(inner_store.list(ActionRequestRecord), ())


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str,
) -> unittest.TestSuite:
    del loader, pattern
    return tests
