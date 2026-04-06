from __future__ import annotations

from datetime import datetime, timezone
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import (
    ActionRequestRecord,
    AnalyticSignalRecord,
    AlertRecord,
    ReconciliationRecord,
)
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


class ControlPlaneServicePersistenceTests(unittest.TestCase):
    def test_runtime_snapshot_reports_postgresql_authoritative_persistence_mode(self) -> None:
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops")
        )

        snapshot = service.describe_runtime()

        self.assertEqual(snapshot.persistence_mode, "postgresql")
        self.assertEqual(snapshot.postgres_dsn, "postgresql://control-plane.local/aegisops")

    def test_service_round_trips_records_by_control_plane_identifier(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        action_request = ActionRequestRecord(
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
        )
        reconciliation = ReconciliationRecord(
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
        )

        service.persist_record(action_request)
        service.persist_record(reconciliation)

        self.assertEqual(
            service.get_record(ActionRequestRecord, "action-request-001"),
            action_request,
        )
        self.assertEqual(
            service.get_record(ReconciliationRecord, "reconciliation-001"),
            reconciliation,
        )
        self.assertIsNone(service.get_record(ActionRequestRecord, "approval-001"))
        self.assertIsNone(service.get_record(ReconciliationRecord, "n8n-exec-001"))

    def test_service_accepts_injected_store_for_runtime_snapshot(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://ignored.local/aegisops"),
            store=store,
        )

        snapshot = service.describe_runtime()

        self.assertEqual(snapshot.postgres_dsn, "postgresql://control-plane.local/aegisops")
        self.assertEqual(snapshot.persistence_mode, "postgresql")

    def test_service_exposes_read_only_record_and_reconciliation_inspection(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        first_compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        latest_compared_at = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        alert = AlertRecord(
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            case_id=None,
            lifecycle_state="triaged",
        )
        matched = ReconciliationRecord(
            reconciliation_id="reconciliation-001",
            subject_linkage={"alert_ids": ("alert-001",), "finding_ids": ("finding-001",)},
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            workflow_execution_id=None,
            linked_execution_ids=(),
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_compared_at,
            last_seen_at=first_compared_at,
            ingest_disposition="matched",
            mismatch_summary="matched upstream signal into alert lifecycle",
            compared_at=first_compared_at,
            lifecycle_state="matched",
        )
        stale = ReconciliationRecord(
            reconciliation_id="reconciliation-002",
            subject_linkage={"alert_ids": ("alert-001",), "finding_ids": ("finding-001",)},
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            workflow_execution_id="exec-001",
            linked_execution_ids=("exec-001",),
            correlation_key="action-request-001:workflow-remediate-host:idempotency-001",
            first_seen_at=first_compared_at,
            last_seen_at=latest_compared_at,
            ingest_disposition="stale",
            mismatch_summary="stale downstream execution observation requires refresh",
            compared_at=latest_compared_at,
            lifecycle_state="stale",
        )

        service.persist_record(alert)
        service.persist_record(matched)
        service.persist_record(stale)

        records_view = service.inspect_records("alert")
        status_view = service.inspect_reconciliation_status()

        self.assertTrue(records_view.read_only)
        self.assertEqual(records_view.record_family, "alert")
        self.assertEqual(records_view.total_records, 1)
        self.assertEqual(records_view.records[0]["alert_id"], "alert-001")
        self.assertEqual(records_view.records[0]["lifecycle_state"], "triaged")

        self.assertTrue(status_view.read_only)
        self.assertEqual(status_view.total_records, 2)
        self.assertEqual(status_view.by_lifecycle_state, {"matched": 1, "stale": 1})
        self.assertEqual(status_view.by_ingest_disposition, {"matched": 1, "stale": 1})
        self.assertEqual(status_view.latest_compared_at, latest_compared_at)
        self.assertEqual(
            tuple(record["reconciliation_id"] for record in status_view.records),
            ("reconciliation-001", "reconciliation-002"),
        )

    def test_service_rejects_schema_invalid_records_before_they_are_inspectable(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            service.persist_record(
                AlertRecord(
                    alert_id="alert-invalid",
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    case_id=None,
                    lifecycle_state="invalid",
                )
            )

        with self.assertRaises(ValueError):
            service.persist_record(
                ReconciliationRecord(
                    reconciliation_id="reconciliation-invalid",
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
                )
            )

        alert_snapshot = service.inspect_records("alert")
        reconciliation_snapshot = service.inspect_records("reconciliation")

        self.assertEqual(alert_snapshot.total_records, 0)
        self.assertEqual(alert_snapshot.records, ())
        self.assertIsNone(service.get_record(AlertRecord, "alert-invalid"))
        self.assertEqual(reconciliation_snapshot.total_records, 0)
        self.assertEqual(reconciliation_snapshot.records, ())
        self.assertIsNone(
            service.get_record(ReconciliationRecord, "reconciliation-invalid")
        )

    def test_service_upserts_alert_lifecycle_from_upstream_signals(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        first_seen = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        restated_seen = datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc)
        updated_seen = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        duplicate_seen = datetime(2026, 4, 5, 12, 45, tzinfo=timezone.utc)

        created = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=first_seen,
        )
        restated = service.ingest_finding_alert(
            finding_id="finding-002",
            analytic_signal_id="signal-002",
            substrate_detection_record_id="substrate-detection-002",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=restated_seen,
        )
        updated = service.ingest_finding_alert(
            finding_id="finding-003",
            analytic_signal_id="signal-003",
            substrate_detection_record_id="substrate-detection-003",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=updated_seen,
            last_seen_at=updated_seen,
            materially_new_work=True,
        )
        deduplicated = service.ingest_finding_alert(
            finding_id="finding-003",
            analytic_signal_id="signal-003",
            substrate_detection_record_id="substrate-detection-003",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=updated_seen,
            last_seen_at=duplicate_seen,
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(updated.disposition, "updated")
        self.assertEqual(deduplicated.disposition, "deduplicated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(updated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(deduplicated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.finding_id, "finding-001")
        self.assertEqual(restated.alert.analytic_signal_id, "signal-001")
        self.assertEqual(updated.alert.finding_id, "finding-003")
        self.assertEqual(updated.alert.analytic_signal_id, "signal-003")
        self.assertEqual(deduplicated.alert.finding_id, "finding-003")
        self.assertEqual(deduplicated.alert.analytic_signal_id, "signal-003")

        stored_alert = service.get_record(AlertRecord, created.alert.alert_id)
        self.assertEqual(stored_alert, updated.alert)
        self.assertEqual(stored_alert.lifecycle_state, "new")

        created_reconciliation = service.get_record(
            ReconciliationRecord, created.reconciliation.reconciliation_id
        )
        restated_reconciliation = service.get_record(
            ReconciliationRecord, restated.reconciliation.reconciliation_id
        )
        updated_reconciliation = service.get_record(
            ReconciliationRecord, updated.reconciliation.reconciliation_id
        )
        deduplicated_reconciliation = service.get_record(
            ReconciliationRecord, deduplicated.reconciliation.reconciliation_id
        )
        self.assertEqual(created_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(created_reconciliation.ingest_disposition, "created")
        self.assertEqual(created_reconciliation.first_seen_at, first_seen)
        self.assertEqual(created_reconciliation.last_seen_at, first_seen)
        self.assertEqual(restated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(restated_reconciliation.ingest_disposition, "restated")
        self.assertEqual(restated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(restated_reconciliation.last_seen_at, restated_seen)
        self.assertEqual(
            restated_reconciliation.subject_linkage["finding_ids"],
            ["finding-001", "finding-002"],
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["analytic_signal_ids"],
            ["signal-001", "signal-002"],
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ["substrate-detection-001", "substrate-detection-002"],
        )
        self.assertEqual(updated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(updated_reconciliation.ingest_disposition, "updated")
        self.assertEqual(updated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(updated_reconciliation.last_seen_at, updated_seen)
        self.assertEqual(
            updated_reconciliation.subject_linkage["finding_ids"],
            ["finding-001", "finding-002", "finding-003"],
        )
        self.assertEqual(
            updated_reconciliation.subject_linkage["analytic_signal_ids"],
            ["signal-001", "signal-002", "signal-003"],
        )
        self.assertEqual(
            updated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            [
                "substrate-detection-001",
                "substrate-detection-002",
                "substrate-detection-003",
            ],
        )
        self.assertEqual(deduplicated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(
            deduplicated_reconciliation.ingest_disposition, "deduplicated"
        )
        self.assertEqual(deduplicated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(deduplicated_reconciliation.last_seen_at, duplicate_seen)
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["finding_ids"],
            ["finding-001", "finding-002", "finding-003"],
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["analytic_signal_ids"],
            ["signal-001", "signal-002", "signal-003"],
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            [
                "substrate-detection-001",
                "substrate-detection-002",
                "substrate-detection-003",
            ],
        )

        signal_one = service.get_record(AnalyticSignalRecord, "signal-001")
        signal_two = service.get_record(AnalyticSignalRecord, "signal-002")
        signal_three = service.get_record(AnalyticSignalRecord, "signal-003")

        self.assertEqual(signal_one.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_one.case_ids, ())
        self.assertEqual(signal_one.finding_id, "finding-001")
        self.assertEqual(
            signal_one.substrate_detection_record_id,
            "substrate-detection-001",
        )
        self.assertEqual(signal_one.correlation_key, "claim:host-001:privilege-escalation")
        self.assertEqual(signal_one.first_seen_at, first_seen)
        self.assertEqual(signal_one.last_seen_at, first_seen)

        self.assertEqual(signal_two.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_two.finding_id, "finding-002")
        self.assertEqual(
            signal_two.substrate_detection_record_id,
            "substrate-detection-002",
        )
        self.assertEqual(signal_two.first_seen_at, first_seen)
        self.assertEqual(signal_two.last_seen_at, restated_seen)

        self.assertEqual(signal_three.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_three.finding_id, "finding-003")
        self.assertEqual(
            signal_three.substrate_detection_record_id,
            "substrate-detection-003",
        )
        self.assertEqual(signal_three.first_seen_at, updated_seen)
        self.assertEqual(signal_three.last_seen_at, duplicate_seen)

    def test_service_inspects_analytic_signal_records_as_first_class_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        analytic_signal = AnalyticSignalRecord(
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            finding_id="finding-001",
            alert_ids=("alert-001",),
            case_ids=("case-001",),
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
            lifecycle_state="active",
        )

        service.persist_record(analytic_signal)

        self.assertEqual(
            service.get_record(AnalyticSignalRecord, "signal-001"),
            analytic_signal,
        )

        inspection = service.inspect_records("analytic_signal")

        self.assertTrue(inspection.read_only)
        self.assertEqual(inspection.record_family, "analytic_signal")
        self.assertEqual(inspection.total_records, 1)
        self.assertEqual(
            inspection.records[0]["analytic_signal_id"],
            "signal-001",
        )
        self.assertEqual(
            inspection.records[0]["substrate_detection_record_id"],
            "substrate-detection-001",
        )

    def test_service_records_execution_correlation_mismatch_states_separately(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        stale_cutoff = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        missing = service.reconcile_action_execution(
            action_request_id="action-request-001",
            workflow_id="workflow-remediate-host",
            observed_executions=(),
            compared_at=requested_at,
            stale_after=stale_cutoff,
        )
        duplicate = service.reconcile_action_execution(
            action_request_id="action-request-001",
            workflow_id="workflow-remediate-host",
            observed_executions=(
                {
                    "workflow_execution_id": "exec-001",
                    "workflow_id": "workflow-remediate-host",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                    "status": "running",
                },
                {
                    "workflow_execution_id": "exec-002",
                    "workflow_id": "workflow-remediate-host",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
                    "status": "running",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )
        mismatched = service.reconcile_action_execution(
            action_request_id="action-request-001",
            workflow_id="workflow-remediate-host",
            observed_executions=(
                {
                    "workflow_execution_id": "exec-003",
                    "workflow_id": "workflow-remediate-host-v2",
                    "idempotency_key": "idempotency-999",
                    "observed_at": datetime(2026, 4, 5, 12, 10, tzinfo=timezone.utc),
                    "status": "failed",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 10, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )
        stale = service.reconcile_action_execution(
            action_request_id="action-request-001",
            workflow_id="workflow-remediate-host",
            observed_executions=(
                {
                    "workflow_execution_id": "exec-004",
                    "workflow_id": "workflow-remediate-host",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
                    "status": "success",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 45, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )

        self.assertEqual(missing.lifecycle_state, "pending")
        self.assertEqual(missing.ingest_disposition, "missing")
        self.assertEqual(missing.workflow_execution_id, None)
        self.assertIn("missing downstream execution", missing.mismatch_summary)
        self.assertEqual(
            missing.subject_linkage["action_request_ids"], ("action-request-001",)
        )
        self.assertEqual(
            missing.subject_linkage["workflow_ids"], ("workflow-remediate-host",)
        )

        self.assertEqual(duplicate.lifecycle_state, "mismatched")
        self.assertEqual(duplicate.ingest_disposition, "duplicate")
        self.assertEqual(duplicate.workflow_execution_id, "exec-002")
        self.assertEqual(duplicate.linked_execution_ids, ("exec-001", "exec-002"))
        self.assertIn("duplicate downstream executions", duplicate.mismatch_summary)

        self.assertEqual(mismatched.lifecycle_state, "mismatched")
        self.assertEqual(mismatched.ingest_disposition, "mismatch")
        self.assertEqual(mismatched.workflow_execution_id, "exec-003")
        self.assertIn("workflow/idempotency mismatch", mismatched.mismatch_summary)

        self.assertEqual(stale.lifecycle_state, "stale")
        self.assertEqual(stale.ingest_disposition, "stale")
        self.assertEqual(stale.workflow_execution_id, "exec-004")
        self.assertIn("stale downstream execution observation", stale.mismatch_summary)

        stored_reconciliations = store.list(ReconciliationRecord)
        self.assertEqual(len(stored_reconciliations), 4)
        self.assertEqual(
            sorted(record.ingest_disposition for record in stored_reconciliations),
            ["duplicate", "mismatch", "missing", "stale"],
        )
        self.assertEqual(
            service.get_record(ActionRequestRecord, "action-request-001"),
            action_request,
        )

    def test_service_reconcile_action_execution_rejects_non_approved_requests(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-pending",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="pending_approval",
        )
        service.persist_record(action_request)

        with self.assertRaisesRegex(ValueError, "is not approved"):
            service.reconcile_action_execution(
                action_request_id="action-request-pending",
                workflow_id="workflow-remediate-host",
                observed_executions=(),
                compared_at=requested_at,
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

    def test_service_reconcile_action_execution_requires_aware_datetimes(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        with self.assertRaisesRegex(ValueError, "compared_at must be timezone-aware"):
            service.reconcile_action_execution(
                action_request_id="action-request-001",
                workflow_id="workflow-remediate-host",
                observed_executions=(),
                compared_at=datetime(2026, 4, 5, 12, 0),
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

        with self.assertRaisesRegex(ValueError, "observed_at must be timezone-aware"):
            service.reconcile_action_execution(
                action_request_id="action-request-001",
                workflow_id="workflow-remediate-host",
                observed_executions=(
                    {
                        "workflow_execution_id": "exec-001",
                        "workflow_id": "workflow-remediate-host",
                        "idempotency_key": "idempotency-001",
                        "observed_at": datetime(2026, 4, 5, 12, 5),
                    },
                ),
                compared_at=requested_at,
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

    def test_service_reconcile_action_execution_ignores_repeated_polls_of_same_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-001",
            workflow_id="workflow-remediate-host",
            observed_executions=(
                {
                    "workflow_execution_id": "exec-001",
                    "workflow_id": "workflow-remediate-host",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
                {
                    "workflow_execution_id": "exec-001",
                    "workflow_id": "workflow-remediate-host",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.workflow_execution_id, "exec-001")
        self.assertEqual(reconciliation.linked_execution_ids, ("exec-001", "exec-001"))


if __name__ == "__main__":
    unittest.main()
