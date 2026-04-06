from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import (
    ActionRequestRecord,
    AnalyticSignalAdmission,
    AnalyticSignalRecord,
    AlertRecord,
    CaseRecord,
    NativeDetectionRecord,
    ReconciliationRecord,
)
from aegisops_control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    NativeDetectionRecordAdapter,
)
from postgres_test_support import make_store


FIXTURES_ROOT = pathlib.Path(__file__).resolve().parent / "fixtures" / "wazuh"


def _load_wazuh_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


class ControlPlaneServicePersistenceTests(unittest.TestCase):
    def test_service_admits_wazuh_fixture_through_substrate_adapter_boundary(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("agent-origin-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        self.assertEqual(admitted.disposition, "created")
        self.assertIsNotNone(admitted.alert.analytic_signal_id)
        self.assertEqual(
            admitted.alert.finding_id,
            "finding:wazuh:rule:5710:source:agent:007:alert:1731594986.4931506",
        )
        self.assertTrue(
            admitted.alert.analytic_signal_id.startswith("analytic-signal-")
        )

        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].substrate_detection_record_id,
            "wazuh:1731594986.4931506",
        )
        self.assertEqual(
            signals[0].correlation_key,
            "wazuh:rule:5710:source:agent:007",
        )
        self.assertEqual(
            signals[0].first_seen_at,
            datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            signals[0].last_seen_at,
            datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(signals[0].alert_ids, (admitted.alert.alert_id,))

        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(reconciliation.ingest_disposition, "created")
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731594986.4931506",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            (admitted.alert.analytic_signal_id,),
        )

    def test_service_extends_promoted_wazuh_alert_with_existing_case_linkage(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        created = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        service.persist_record(
            AlertRecord(
                alert_id=created.alert.alert_id,
                finding_id=created.alert.finding_id,
                analytic_signal_id=created.alert.analytic_signal_id,
                case_id="case-001",
                lifecycle_state="escalated_to_case",
            )
        )
        service.persist_record(
            CaseRecord(
                case_id="case-001",
                alert_id=created.alert.alert_id,
                finding_id=created.alert.finding_id,
                evidence_ids=("evidence-001",),
                lifecycle_state="investigating",
            )
        )

        restated_payload = _load_wazuh_fixture("agent-origin-alert.json")
        restated_payload["id"] = "1731595888.5000001"
        restated_payload["timestamp"] = "2026-04-05T12:15:00+00:00"
        restated = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(restated_payload),
        )

        restated_signal = service.get_record(
            AnalyticSignalRecord,
            restated.alert.analytic_signal_id,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            restated.reconciliation.reconciliation_id,
        )

        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.case_id, "case-001")
        self.assertIsNotNone(restated_signal)
        self.assertEqual(restated_signal.case_ids, ("case-001",))
        self.assertIsNotNone(reconciliation)
        self.assertEqual(reconciliation.subject_linkage["case_ids"], ("case-001",))

    def test_service_admits_native_detection_records_via_substrate_adapter_boundary(self) -> None:
        @dataclass(frozen=True)
        class TestNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id=f"finding::{record.native_record_id}",
                    analytic_signal_id=f"signal::{record.native_record_id}",
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        admitted = service.ingest_native_detection_record(
            TestNativeRecordAdapter(),
            NativeDetectionRecord(
                substrate_key="test-substrate",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                metadata={"vendor": "test"},
            ),
        )

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.finding_id, "finding::native-001")
        self.assertEqual(admitted.alert.analytic_signal_id, "signal::native-001")
        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].substrate_detection_record_id,
            "test-substrate:native-001",
        )

    def test_service_namespaces_fallback_substrate_detection_ids_by_substrate(self) -> None:
        @dataclass(frozen=True)
        class FallbackNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id=None,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        first = service.ingest_native_detection_record(
            FallbackNativeRecordAdapter(substrate_key="substrate-a"),
            NativeDetectionRecord(
                substrate_key="substrate-a",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
                metadata={"vendor": "a"},
            ),
        )
        second = service.ingest_native_detection_record(
            FallbackNativeRecordAdapter(substrate_key="substrate-b"),
            NativeDetectionRecord(
                substrate_key="substrate-b",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                metadata={"vendor": "b"},
            ),
        )

        self.assertEqual(first.disposition, "created")
        self.assertEqual(second.disposition, "restated")
        self.assertIsNotNone(first.reconciliation.analytic_signal_id)
        self.assertIsNotNone(second.reconciliation.analytic_signal_id)
        self.assertNotEqual(
            first.reconciliation.analytic_signal_id,
            second.reconciliation.analytic_signal_id,
        )
        self.assertEqual(
            second.reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-a:native-001", "substrate-b:native-001"),
        )
        self.assertEqual(
            second.reconciliation.subject_linkage["analytic_signal_ids"],
            (
                first.reconciliation.analytic_signal_id,
                second.reconciliation.analytic_signal_id,
            ),
        )
        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 2)

    def test_service_rejects_blank_substrate_keys_at_native_detection_boundary(self) -> None:
        @dataclass(frozen=True)
        class BlankSubstrateAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "   "

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "adapter\\.substrate_key must be a non-empty string",
        ):
            service.ingest_native_detection_record(
                BlankSubstrateAdapter(),
                NativeDetectionRecord(
                    substrate_key="   ",
                    native_record_id="native-001",
                    record_kind="alert",
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                    last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                    metadata={"vendor": "test"},
                ),
            )

    def test_service_rejects_blank_detection_id_at_native_detection_boundary(self) -> None:
        @dataclass(frozen=True)
        class BlankDetectionIdAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id="   ",
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "substrate_detection_record_id/native_record_id must be a non-empty string",
        ):
            service.ingest_native_detection_record(
                BlankDetectionIdAdapter(),
                NativeDetectionRecord(
                    substrate_key="test-substrate",
                    native_record_id="native-001",
                    record_kind="alert",
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                    last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                    metadata={"vendor": "test"},
                ),
            )

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
            execution_run_id="n8n-exec-001",
            linked_execution_run_ids=("n8n-exec-001",),
            correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
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

    def test_service_returns_nested_immutable_json_backed_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        record = ActionRequestRecord(
            action_request_id="action-request-immutable-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={
                "asset_ids": ["asset-001"],
                "filters": {"environment": "prod"},
            },
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )

        service.persist_record(record)
        persisted = service.get_record(
            ActionRequestRecord, "action-request-immutable-001"
        )

        assert persisted is not None
        with self.assertRaises(TypeError):
            persisted.target_scope["asset_ids"] += ("asset-002",)
        with self.assertRaises(TypeError):
            persisted.target_scope["filters"]["environment"] = "dev"  # type: ignore[index]

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
            execution_run_id=None,
            linked_execution_run_ids=(),
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
            subject_linkage={
                "alert_ids": ("alert-001",),
                "finding_ids": ("finding-001",),
                "execution_surface_types": ("automation_substrate",),
                "execution_surface_ids": ("n8n",),
            },
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id="exec-001",
            linked_execution_run_ids=("exec-001",),
            correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
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
                    execution_run_id=None,
                    linked_execution_run_ids=(),
                    correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
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
            ("finding-001", "finding-002"),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002"),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-detection-001", "substrate-detection-002"),
        )
        self.assertEqual(updated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(updated_reconciliation.ingest_disposition, "updated")
        self.assertEqual(updated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(updated_reconciliation.last_seen_at, updated_seen)
        self.assertEqual(
            updated_reconciliation.subject_linkage["finding_ids"],
            ("finding-001", "finding-002", "finding-003"),
        )
        self.assertEqual(
            updated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002", "signal-003"),
        )
        self.assertEqual(
            updated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            (
                "substrate-detection-001",
                "substrate-detection-002",
                "substrate-detection-003",
            ),
        )
        self.assertEqual(deduplicated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(
            deduplicated_reconciliation.ingest_disposition, "deduplicated"
        )
        self.assertEqual(deduplicated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(deduplicated_reconciliation.last_seen_at, duplicate_seen)
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["finding_ids"],
            ("finding-001", "finding-002", "finding-003"),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002", "signal-003"),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            (
                "substrate-detection-001",
                "substrate-detection-002",
                "substrate-detection-003",
            ),
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

    def test_service_restates_when_repeated_finding_adds_new_signal_identity(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        second_seen = datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc)

        created = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=first_seen,
        )
        restated = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-002",
            substrate_detection_record_id="substrate-detection-002",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=second_seen,
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)

        reconciliation = service.get_record(
            ReconciliationRecord, restated.reconciliation.reconciliation_id
        )
        self.assertEqual(reconciliation.ingest_disposition, "restated")
        self.assertEqual(
            reconciliation.subject_linkage["finding_ids"],
            ("finding-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002"),
        )
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-detection-001", "substrate-detection-002"),
        )

    def test_service_rejects_naive_intake_timestamps(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(ValueError, "first_seen_at must be timezone-aware"):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0),
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
            )

        with self.assertRaisesRegex(ValueError, "last_seen_at must be timezone-aware"):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 15),
            )

    def test_service_rejects_inverted_intake_timestamps(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "last_seen_at must be greater than or equal to first_seen_at",
        ):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
            )

    def test_service_rejects_blank_required_admission_identities(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        with self.assertRaisesRegex(ValueError, "finding_id must be a non-empty string"):
            service.ingest_finding_alert(
                finding_id="   ",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
            )

        with self.assertRaisesRegex(
            ValueError,
            "correlation_key must be a non-empty string",
        ):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key=" \t ",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
            )

    def test_service_mints_analytic_signal_identity_when_admission_leaves_it_blank(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="   ",
            substrate_detection_record_id="",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
        )

        self.assertEqual(admitted.disposition, "created")
        self.assertIsNotNone(admitted.alert.analytic_signal_id)
        self.assertTrue(admitted.alert.analytic_signal_id.startswith("analytic-signal-"))

        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].analytic_signal_id, admitted.alert.analytic_signal_id)
        self.assertIsNone(signals[0].substrate_detection_record_id)
        self.assertEqual(signals[0].finding_id, "finding-001")

        reconciliation = service.get_record(
            ReconciliationRecord, admitted.reconciliation.reconciliation_id
        )
        self.assertEqual(
            reconciliation.analytic_signal_id,
            admitted.alert.analytic_signal_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            (admitted.alert.analytic_signal_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            (),
        )

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
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(),
            compared_at=requested_at,
            stale_after=stale_cutoff,
        )
        duplicate = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                    "status": "running",
                },
                {
                    "execution_run_id": "exec-002",
                    "execution_surface_id": "n8n",
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
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-003",
                    "execution_surface_id": "shuffle",
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
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-004",
                    "execution_surface_id": "n8n",
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
        self.assertEqual(missing.execution_run_id, None)
        self.assertIn("missing downstream execution", missing.mismatch_summary)
        self.assertEqual(
            missing.subject_linkage["action_request_ids"], ("action-request-001",)
        )
        self.assertEqual(
            missing.subject_linkage["execution_surface_types"],
            ("automation_substrate",),
        )
        self.assertEqual(
            missing.subject_linkage["execution_surface_ids"], ("n8n",)
        )

        self.assertEqual(duplicate.lifecycle_state, "mismatched")
        self.assertEqual(duplicate.ingest_disposition, "duplicate")
        self.assertEqual(duplicate.execution_run_id, "exec-002")
        self.assertEqual(
            duplicate.linked_execution_run_ids,
            ("exec-001", "exec-002"),
        )
        self.assertIn("duplicate downstream executions", duplicate.mismatch_summary)

        self.assertEqual(mismatched.lifecycle_state, "mismatched")
        self.assertEqual(mismatched.ingest_disposition, "mismatch")
        self.assertEqual(mismatched.execution_run_id, "exec-003")
        self.assertIn(
            "execution surface/idempotency mismatch",
            mismatched.mismatch_summary,
        )

        self.assertEqual(stale.lifecycle_state, "stale")
        self.assertEqual(stale.ingest_disposition, "stale")
        self.assertEqual(stale.execution_run_id, "exec-004")
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
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
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
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                observed_executions=(),
                compared_at=datetime(2026, 4, 5, 12, 0),
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

        with self.assertRaisesRegex(ValueError, "observed_at must be timezone-aware"):
            service.reconcile_action_execution(
                action_request_id="action-request-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                observed_executions=(
                    {
                        "execution_run_id": "exec-001",
                        "execution_surface_id": "n8n",
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
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.execution_run_id, "exec-001")
        self.assertEqual(
            reconciliation.linked_execution_run_ids,
            ("exec-001", "exec-001"),
        )

    def test_service_reconcile_action_execution_supports_generic_execution_surfaces(
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
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
            observed_executions=(
                {
                    "execution_run_id": "executor-run-001",
                    "execution_surface_id": "isolated-executor",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.execution_run_id, "executor-run-001")
        self.assertEqual(
            reconciliation.linked_execution_run_ids,
            ("executor-run-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["execution_surface_types"],
            ("executor",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["execution_surface_ids"],
            ("isolated-executor",),
        )


if __name__ == "__main__":
    unittest.main()
