from __future__ import annotations

from dataclasses import dataclass
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
    AnalyticSignalRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from postgres_test_support import FakePostgresBackend, make_store


@dataclass(frozen=True)
class UnsupportedRecord(ControlPlaneRecord):
    record_family = "unsupported"
    identifier_field = "unsupported_id"

    unsupported_id: str
    lifecycle_state: str


class PostgresControlPlaneStoreTests(unittest.TestCase):
    def test_store_reports_postgresql_authoritative_persistence_mode(self) -> None:
        store = PostgresControlPlaneStore("postgresql://control-plane.local/aegisops")

        self.assertEqual(store.persistence_mode, "postgresql")
        self.assertEqual(store.dsn, "postgresql://control-plane.local/aegisops")

    def test_store_round_trips_reviewed_record_families_by_aegisops_ids(self) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        records = [
            AlertRecord(
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                case_id="case-001",
                lifecycle_state="investigating",
            ),
            AnalyticSignalRecord(
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                finding_id="finding-001",
                alert_ids=("alert-001",),
                case_ids=("case-001",),
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=timestamp,
                last_seen_at=timestamp,
                lifecycle_state="active",
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
                alert_id=None,
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                workflow_execution_id="n8n-exec-001",
                linked_execution_ids=("n8n-exec-001",),
                correlation_key="action-request-001:idempotency-001",
                first_seen_at=timestamp,
                last_seen_at=timestamp,
                ingest_disposition="matched",
                mismatch_summary="matched execution",
                compared_at=timestamp,
                lifecycle_state="matched",
            ),
        ]

        for record in records:
            store.save(record)

        expected_records = [
            (AlertRecord, "alert-001", records[0]),
            (AnalyticSignalRecord, "signal-001", records[1]),
            (CaseRecord, "case-001", records[2]),
            (EvidenceRecord, "evidence-001", records[3]),
            (ObservationRecord, "observation-001", records[4]),
            (LeadRecord, "lead-001", records[5]),
            (RecommendationRecord, "recommendation-001", records[6]),
            (ApprovalDecisionRecord, "approval-001", records[7]),
            (ActionRequestRecord, "action-request-001", records[8]),
            (HuntRecord, "hunt-001", records[9]),
            (HuntRunRecord, "hunt-run-001", records[10]),
            (AITraceRecord, "ai-trace-001", records[11]),
            (ReconciliationRecord, "reconciliation-001", records[12]),
        ]

        for record_type, record_id, expected_record in expected_records:
            with self.subTest(record_type=record_type.__name__, record_id=record_id):
                self.assertEqual(store.get(record_type, record_id), expected_record)

        self.assertIsNone(store.get(AlertRecord, "finding-001"))
        self.assertIsNone(store.get(ActionRequestRecord, "approval-001"))
        self.assertIsNone(store.get(ReconciliationRecord, "n8n-exec-001"))

    def test_store_copies_mapping_fields_before_persistence(self) -> None:
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        target_scope = {"asset_id": "asset-001"}
        record = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope=target_scope,
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )

        target_scope["asset_id"] = "asset-002"

        self.assertEqual(record.target_scope["asset_id"], "asset-001")
        with self.assertRaises(TypeError):
            record.target_scope["asset_id"] = "asset-003"  # type: ignore[index]

    def test_store_lists_execution_reconciliation_records_separately(self) -> None:
        store, _ = make_store()
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        records = (
            ReconciliationRecord(
                reconciliation_id="reconciliation-001",
                subject_linkage={
                    "action_request_ids": ["action-request-001"],
                    "workflow_ids": ["workflow-remediate-host"],
                },
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id=None,
                workflow_execution_id=None,
                linked_execution_ids=(),
                correlation_key=(
                    "action-request-001:workflow-remediate-host:idempotency-001"
                ),
                first_seen_at=requested_at,
                last_seen_at=requested_at,
                ingest_disposition="missing",
                mismatch_summary=(
                    "missing downstream execution for approved action request correlation"
                ),
                compared_at=compared_at,
                lifecycle_state="pending",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-002",
                subject_linkage={
                    "action_request_ids": ["action-request-001"],
                    "workflow_ids": ["workflow-remediate-host"],
                },
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id=None,
                workflow_execution_id="exec-002",
                linked_execution_ids=("exec-001", "exec-002"),
                correlation_key=(
                    "action-request-001:workflow-remediate-host:idempotency-001"
                ),
                first_seen_at=requested_at,
                last_seen_at=compared_at,
                ingest_disposition="duplicate",
                mismatch_summary=(
                    "duplicate downstream executions observed for one approved request"
                ),
                compared_at=compared_at,
                lifecycle_state="mismatched",
            ),
        )

        for record in records:
            store.save(record)

        stored_records = store.list(ReconciliationRecord)

        self.assertEqual(stored_records, records)
        self.assertEqual(
            tuple(record.ingest_disposition for record in stored_records),
            ("missing", "duplicate"),
        )
        self.assertIsNone(store.get(ReconciliationRecord, "exec-002"))
        self.assertEqual(
            store.get(ReconciliationRecord, "reconciliation-002"),
            records[1],
        )

    def test_store_rejects_schema_invalid_records_before_persistence(self) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        invalid_cases = (
            (
                "invalid alert lifecycle",
                AlertRecord(
                    alert_id="alert-invalid",
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    case_id=None,
                    lifecycle_state="invalid",
                ),
                AlertRecord,
                "alert-invalid",
            ),
            (
                "empty case evidence linkage",
                CaseRecord(
                    case_id="case-invalid",
                    alert_id="alert-001",
                    finding_id=None,
                    evidence_ids=(),
                    lifecycle_state="open",
                ),
                CaseRecord,
                "case-invalid",
            ),
            (
                "reconciliation timestamps out of order",
                ReconciliationRecord(
                    reconciliation_id="reconciliation-invalid",
                    subject_linkage={"action_request_ids": ["action-request-001"]},
                    alert_id=None,
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    workflow_execution_id=None,
                    linked_execution_ids=(),
                    correlation_key="action-request-001:idempotency-001",
                    first_seen_at=datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                    last_seen_at=timestamp,
                    ingest_disposition="matched",
                    mismatch_summary="invalid ordering",
                    compared_at=timestamp,
                    lifecycle_state="matched",
                ),
                ReconciliationRecord,
                "reconciliation-invalid",
            ),
            (
                "invalid reconciliation ingest disposition",
                ReconciliationRecord(
                    reconciliation_id="reconciliation-invalid-disposition",
                    subject_linkage={"action_request_ids": ["action-request-001"]},
                    alert_id=None,
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    workflow_execution_id=None,
                    linked_execution_ids=(),
                    correlation_key="action-request-001:idempotency-001",
                    first_seen_at=timestamp,
                    last_seen_at=timestamp,
                    ingest_disposition="invalid",
                    mismatch_summary="invalid disposition",
                    compared_at=timestamp,
                    lifecycle_state="matched",
                ),
                ReconciliationRecord,
                "reconciliation-invalid-disposition",
            ),
        )

        for label, record, record_type, record_id in invalid_cases:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    store.save(record)
                self.assertIsNone(store.get(record_type, record_id))
                self.assertEqual(store.list(record_type), ())

    def test_store_rejects_unsupported_record_family_with_type_error(self) -> None:
        store, _ = make_store()

        with self.assertRaisesRegex(
            TypeError,
            "Unsupported control-plane record type: UnsupportedRecord",
        ):
            store.save(
                UnsupportedRecord(
                    unsupported_id="unsupported-001",
                    lifecycle_state="new",
                )
            )

    def test_store_persists_records_across_store_instances_sharing_postgres_backend(
        self,
    ) -> None:
        backend = FakePostgresBackend()
        first_store, _ = make_store(backend)
        second_store, _ = make_store(backend)
        record = AlertRecord(
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            case_id=None,
            lifecycle_state="new",
        )

        first_store.save(record)

        self.assertEqual(second_store.get(AlertRecord, "alert-001"), record)


if __name__ == "__main__":
    unittest.main()
