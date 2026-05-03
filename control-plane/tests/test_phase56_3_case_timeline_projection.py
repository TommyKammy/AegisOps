from __future__ import annotations

from dataclasses import replace
from datetime import timedelta

from _service_persistence_support import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    ApprovalDecisionRecord,
    EvidenceRecord,
    ReconciliationRecord,
    RecommendationRecord,
    ServicePersistenceTestBase,
    _approved_binding_hash,
    _phase20_notify_identity_owner_payload,
)


class Phase563CaseTimelineProjectionTests(ServicePersistenceTestBase):
    def test_case_detail_projects_required_segments_with_authority_posture(self) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase563-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-phase563-001",
                review_owner="analyst-001",
                intended_outcome="Ask an approver to notify the identity owner.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase563-001",
                subject_linkage={
                    "case_ids": (promoted_case.case_id,),
                    "alert_ids": (promoted_case.alert_id,),
                    "recommendation_ids": (recommendation.recommendation_id,),
                    "evidence_ids": (evidence_id,),
                },
                model_identity="gpt-5.4",
                prompt_version="phase-56-3-test",
                generated_at=reviewed_at,
                material_input_refs=(evidence_id,),
                reviewer_identity="analyst-001",
                lifecycle_state="under_review",
            )
        )
        target_scope = {"asset_id": "asset-phase563-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="identity-owner-phase563-001",
            case_id=promoted_case.case_id,
            alert_id=promoted_case.alert_id,
            finding_id=promoted_case.finding_id,
            source_record_id=recommendation.recommendation_id,
            recommendation_id=recommendation.recommendation_id,
            linked_evidence_ids=(evidence_id,),
        )
        payload_hash = _approved_binding_hash(
            target_scope=target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase563-001",
                action_request_id="action-request-phase563-001",
                approver_identities=("approver-001",),
                target_snapshot=target_scope,
                payload_hash=payload_hash,
                decided_at=reviewed_at,
                lifecycle_state="approved",
            )
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-phase563-001",
                approval_decision_id=approval.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key="idempotency-phase563-001",
                target_scope=target_scope,
                payload_hash=payload_hash,
                requested_at=reviewed_at,
                expires_at=None,
                lifecycle_state="approved",
                requester_identity="analyst-001",
                requested_payload=approved_payload,
                policy_evaluation={
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        execution = service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase563-001",
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase563-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="shuffle-run-phase563-001",
                idempotency_key="execution-idempotency-phase563-001",
                target_scope=target_scope,
                approved_payload=approved_payload,
                payload_hash=payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=None,
                provenance={
                    "adapter": "shuffle",
                    "downstream_binding": {
                        "system": "shuffle",
                        "execution_run_id": "shuffle-run-phase563-001",
                    },
                },
                lifecycle_state="succeeded",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase563-001",
                subject_linkage={
                    "case_ids": (promoted_case.case_id,),
                    "alert_ids": (promoted_case.alert_id,),
                    "action_request_ids": (action_request.action_request_id,),
                    "approval_decision_ids": (approval.approval_decision_id,),
                    "action_execution_ids": (execution.action_execution_id,),
                    "evidence_ids": (evidence_id,),
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=execution.execution_run_id,
                linked_execution_run_ids=(execution.execution_run_id,),
                correlation_key="phase563-reconciliation",
                first_seen_at=reviewed_at,
                last_seen_at=reviewed_at + timedelta(minutes=2),
                ingest_disposition="matched",
                mismatch_summary="",
                compared_at=reviewed_at + timedelta(minutes=3),
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase563-sibling",
                lead_id=None,
                hunt_run_id=None,
                alert_id="alert-phase563-sibling",
                case_id=None,
                ai_trace_id="ai-trace-phase563-001",
                review_owner="analyst-002",
                intended_outcome="Do not infer this sibling into the case timeline.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        detail = service.inspect_case_detail(promoted_case.case_id)
        projection = detail.case_timeline_projection
        segments = {segment["segment"]: segment for segment in projection["segments"]}

        self.assertEqual(projection["case_id"], promoted_case.case_id)
        self.assertFalse(projection["projection_authority_allowed"])
        self.assertEqual(
            tuple(segments),
            (
                "wazuh_signal",
                "aegisops_alert",
                "evidence",
                "ai_summary",
                "recommendation",
                "action_request",
                "approval",
                "shuffle_receipt",
                "reconciliation",
            ),
        )
        self.assertEqual(
            segments["aegisops_alert"]["authority_posture"],
            "authoritative_aegisops_record",
        )
        self.assertEqual(
            segments["wazuh_signal"]["authority_posture"],
            "subordinate_context",
        )
        self.assertEqual(
            segments["shuffle_receipt"]["authority_posture"],
            "subordinate_context",
        )
        self.assertEqual(segments["reconciliation"]["state"], "normal")
        self.assertEqual(
            segments["recommendation"]["backend_record_binding"]["record_id"],
            recommendation.recommendation_id,
        )
        self.assertEqual(
            segments["action_request"]["backend_record_binding"]["record_id"],
            action_request.action_request_id,
        )
        self.assertEqual(
            segments["approval"]["backend_record_binding"]["record_id"],
            approval.approval_decision_id,
        )
        self.assertNotIn(
            "recommendation-phase563-sibling",
            {
                segment["backend_record_binding"].get("record_id")
                for segment in projection["segments"]
            },
        )

    def test_case_timeline_keeps_missing_and_degraded_segments_visible(self) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        degraded_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase563-degraded",
                source_record_id="source-phase563-degraded",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="wazuh",
                collector_identity="collector://wazuh/replay",
                acquired_at=_reviewed_at,
                derivation_relationship="reviewed_case_attachment",
                lifecycle_state="collected",
                provenance={},
            )
        )
        promoted_case = service.persist_record(
            replace(
                promoted_case,
                evidence_ids=(
                    *promoted_case.evidence_ids,
                    degraded_evidence.evidence_id,
                ),
            )
        )

        projection = service.inspect_case_detail(
            promoted_case.case_id
        ).case_timeline_projection
        segments = {segment["segment"]: segment for segment in projection["segments"]}

        self.assertEqual(segments["ai_summary"]["state"], "missing")
        self.assertEqual(segments["recommendation"]["state"], "missing")
        self.assertEqual(segments["action_request"]["state"], "missing")
        self.assertEqual(segments["approval"]["state"], "missing")
        self.assertEqual(segments["shuffle_receipt"]["state"], "missing")
        self.assertEqual(segments["evidence"]["state"], "degraded")
        self.assertTrue(segments["evidence"]["operator_visible"])
        self.assertEqual(
            segments["evidence"]["incomplete_reason"],
            "missing_provenance",
        )

    def test_case_timeline_rejects_sibling_timestamp_and_ai_output_inference(self) -> None:
        store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        sibling_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase563-sibling",
                source_record_id="source-phase563-sibling",
                alert_id="alert-phase563-sibling",
                case_id=None,
                source_system="wazuh",
                collector_identity="collector://wazuh/replay",
                acquired_at=reviewed_at,
                derivation_relationship="same_timestamp_only",
                lifecycle_state="collected",
                provenance={
                    "classification": "reviewed-derived",
                    "source_id": "source-phase563-sibling",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "source_family": "wazuh",
                },
            )
        )
        service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase563-ai-only",
                lead_id=None,
                hunt_run_id=None,
                alert_id="alert-phase563-ai-only",
                case_id=None,
                ai_trace_id=None,
                review_owner="assistant",
                intended_outcome="AI text mentions the case title but has no binding.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        projection = service.inspect_case_detail(
            promoted_case.case_id
        ).case_timeline_projection
        bindings = {
            segment["backend_record_binding"].get("record_id")
            for segment in projection["segments"]
        }

        self.assertNotIn(sibling_evidence.evidence_id, bindings)
        self.assertNotIn("recommendation-phase563-ai-only", bindings)
        self.assertEqual(
            store.list(EvidenceRecord)[-1].evidence_id,
            sibling_evidence.evidence_id,
        )


if __name__ == "__main__":
    import unittest

    unittest.main()
