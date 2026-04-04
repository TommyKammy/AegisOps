from __future__ import annotations

from datetime import datetime, timezone
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.adapters.postgres import PostgresControlPlaneStore
from aegisops_control_plane.models import (
    AITraceRecord,
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)


class PostgresControlPlaneStoreTests(unittest.TestCase):
    def test_store_reports_current_in_process_persistence_mode(self) -> None:
        store = PostgresControlPlaneStore("postgresql://control-plane.local/aegisops")

        self.assertEqual(store.persistence_mode, "in_memory")
        self.assertEqual(store.dsn, "postgresql://control-plane.local/aegisops")

    def test_store_round_trips_reviewed_record_families_by_aegisops_ids(self) -> None:
        store = PostgresControlPlaneStore("postgresql://control-plane.local/aegisops")
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        records = [
            AlertRecord(
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                case_id="case-001",
                lifecycle_state="investigating",
            ),
            CaseRecord(
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                evidence_ids=("evidence-001",),
                lifecycle_state="investigating",
            ),
            EvidenceRecord(
                evidence_id="evidence-001",
                source_record_id="artifact-001",
                alert_id="alert-001",
                case_id="case-001",
                source_system="opensearch",
                collector_identity="collector-001",
                acquired_at=timestamp,
                derivation_relationship="original",
                lifecycle_state="linked",
            ),
            ObservationRecord(
                observation_id="observation-001",
                hunt_id="hunt-001",
                hunt_run_id="hunt-run-001",
                alert_id="alert-001",
                case_id="case-001",
                supporting_evidence_ids=("evidence-001",),
                author_identity="analyst-001",
                observed_at=timestamp,
                scope_statement="bounded triage observation",
                lifecycle_state="confirmed",
            ),
            LeadRecord(
                lead_id="lead-001",
                observation_id="observation-001",
                finding_id="finding-001",
                hunt_run_id="hunt-run-001",
                alert_id="alert-001",
                case_id="case-001",
                triage_owner="analyst-001",
                triage_rationale="requires follow-up",
                lifecycle_state="triaged",
            ),
            RecommendationRecord(
                recommendation_id="recommendation-001",
                lead_id="lead-001",
                hunt_run_id="hunt-run-001",
                alert_id="alert-001",
                case_id="case-001",
                ai_trace_id="ai-trace-001",
                review_owner="reviewer-001",
                intended_outcome="escalate for action review",
                lifecycle_state="under_review",
            ),
            ApprovalDecisionRecord(
                approval_decision_id="approval-001",
                action_request_id="action-request-001",
                approver_identities=("approver-001",),
                target_snapshot={"asset_id": "asset-001"},
                payload_hash="payload-hash-001",
                decided_at=timestamp,
                lifecycle_state="approved",
            ),
            ActionRequestRecord(
                action_request_id="action-request-001",
                approval_decision_id="approval-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-001",
                target_scope={"asset_id": "asset-001"},
                payload_hash="payload-hash-001",
                requested_at=timestamp,
                expires_at=None,
                lifecycle_state="approved",
            ),
            HuntRecord(
                hunt_id="hunt-001",
                hypothesis_statement="suspicious persistence attempt",
                hypothesis_version="v1",
                owner_identity="hunter-001",
                scope_boundary="prod-endpoints",
                opened_at=timestamp,
                alert_id="alert-001",
                case_id="case-001",
                lifecycle_state="active",
            ),
            HuntRunRecord(
                hunt_run_id="hunt-run-001",
                hunt_id="hunt-001",
                scope_snapshot={"window": "24h"},
                execution_plan_reference="hunt-plan-001",
                output_linkage={"lead_ids": ["lead-001"]},
                started_at=timestamp,
                completed_at=None,
                lifecycle_state="running",
            ),
            AITraceRecord(
                ai_trace_id="ai-trace-001",
                subject_linkage={"recommendation_ids": ["recommendation-001"]},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=timestamp,
                material_input_refs=("evidence-001",),
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-001",
                subject_linkage={"action_request_ids": ["action-request-001"]},
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                workflow_execution_id="n8n-exec-001",
                linked_execution_ids=("n8n-exec-001",),
                correlation_key="action-request-001:idempotency-001",
                mismatch_summary="matched execution",
                compared_at=timestamp,
                lifecycle_state="matched",
            ),
        ]

        for record in records:
            store.save(record)

        self.assertEqual(store.get(AlertRecord, "alert-001"), records[0])
        self.assertEqual(store.get(CaseRecord, "case-001"), records[1])
        self.assertEqual(store.get(EvidenceRecord, "evidence-001"), records[2])
        self.assertEqual(store.get(ObservationRecord, "observation-001"), records[3])
        self.assertEqual(store.get(LeadRecord, "lead-001"), records[4])
        self.assertEqual(store.get(RecommendationRecord, "recommendation-001"), records[5])
        self.assertEqual(store.get(ApprovalDecisionRecord, "approval-001"), records[6])
        self.assertEqual(store.get(ActionRequestRecord, "action-request-001"), records[7])
        self.assertEqual(store.get(HuntRecord, "hunt-001"), records[8])
        self.assertEqual(store.get(HuntRunRecord, "hunt-run-001"), records[9])
        self.assertEqual(store.get(AITraceRecord, "ai-trace-001"), records[10])
        self.assertEqual(store.get(ReconciliationRecord, "reconciliation-001"), records[11])

        self.assertIsNone(store.get(AlertRecord, "finding-001"))
        self.assertIsNone(store.get(ActionRequestRecord, "approval-001"))
        self.assertIsNone(store.get(ReconciliationRecord, "n8n-exec-001"))


if __name__ == "__main__":
    unittest.main()
