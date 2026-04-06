from __future__ import annotations

import contextlib
from datetime import datetime, timezone
import io
import json
import pathlib
import sys
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

import main
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops_control_plane.models import (
    AlertRecord,
    AnalyticSignalRecord,
    ReconciliationRecord,
)
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


FIXTURES_ROOT = pathlib.Path(__file__).resolve().parent / "fixtures" / "wazuh"


def _load_wazuh_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


class ControlPlaneCliInspectionTests(unittest.TestCase):
    def test_runtime_command_uses_runtime_service_builder_when_not_injected(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stdout = io.StringIO()

        with mock.patch.object(
            main,
            "build_runtime_service",
            return_value=service,
        ) as build_runtime_service:
            main.main(["runtime"], stdout=stdout)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["persistence_mode"], "postgresql")
        build_runtime_service.assert_called_once_with()

    def test_runtime_command_honors_injected_service_snapshot(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=9411,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        stdout = io.StringIO()

        main.main(["runtime"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["bind_host"], "127.0.0.1")
        self.assertEqual(payload["bind_port"], 9411)
        self.assertEqual(payload["postgres_dsn"], "postgresql://control-plane.local/aegisops")
        self.assertEqual(payload["persistence_mode"], "postgresql")

    def test_cli_renders_read_only_record_and_reconciliation_views(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            AlertRecord(
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            AnalyticSignalRecord(
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                finding_id="finding-001",
                alert_ids=("alert-001",),
                case_ids=(),
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                lifecycle_state="active",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-001",
                subject_linkage={"alert_ids": ("alert-001",)},
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                ingest_disposition="created",
                mismatch_summary="created upstream analytic signal into alert lifecycle",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )

        records_stdout = io.StringIO()
        analytic_signals_stdout = io.StringIO()
        status_stdout = io.StringIO()

        main.main(
            ["inspect-records", "--family", "alert"],
            stdout=records_stdout,
            service=service,
        )
        main.main(
            ["inspect-records", "--family", "analytic_signal"],
            stdout=analytic_signals_stdout,
            service=service,
        )
        main.main(
            ["inspect-reconciliation-status"],
            stdout=status_stdout,
            service=service,
        )

        records_payload = json.loads(records_stdout.getvalue())
        analytic_signals_payload = json.loads(analytic_signals_stdout.getvalue())
        status_payload = json.loads(status_stdout.getvalue())

        self.assertTrue(records_payload["read_only"])
        self.assertEqual(records_payload["record_family"], "alert")
        self.assertEqual(records_payload["records"][0]["alert_id"], "alert-001")

        self.assertTrue(analytic_signals_payload["read_only"])
        self.assertEqual(analytic_signals_payload["record_family"], "analytic_signal")
        self.assertEqual(
            analytic_signals_payload["records"][0]["analytic_signal_id"],
            "signal-001",
        )
        self.assertEqual(
            analytic_signals_payload["records"][0]["substrate_detection_record_id"],
            "substrate-detection-001",
        )

        self.assertTrue(status_payload["read_only"])
        self.assertEqual(status_payload["total_records"], 1)
        self.assertEqual(status_payload["by_ingest_disposition"], {"created": 1})
        self.assertEqual(
            status_payload["latest_compared_at"],
            "2026-04-05T12:00:00+00:00",
        )

    def test_cli_renders_wazuh_business_hours_analyst_queue_view(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        service.persist_record(
            AlertRecord(
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                analytic_signal_id=admitted.alert.analytic_signal_id,
                case_id="case-queue-001",
                lifecycle_state="escalated_to_case",
            )
        )

        stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["queue_name"], "analyst_review")
        self.assertEqual(payload["total_records"], 1)
        self.assertEqual(payload["records"][0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(
            payload["records"][0]["queue_selection"],
            "business_hours_triage",
        )
        self.assertEqual(payload["records"][0]["review_state"], "case_required")
        self.assertEqual(payload["records"][0]["source_system"], "wazuh")
        self.assertEqual(
            payload["records"][0]["accountable_source_identities"],
            ["agent:007"],
        )
        self.assertEqual(
            payload["records"][0]["native_rule"]["description"],
            "SSH brute force attempt",
        )
        self.assertEqual(
            payload["records"][0]["substrate_detection_record_ids"],
            ["wazuh:1731594986.4931506"],
        )

    def test_cli_rejects_unknown_record_family_as_usage_error(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc_info:
                main.main(
                    ["inspect-records", "--family", "unknown-family"],
                    service=service,
                )

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("Unsupported control-plane record family", stderr.getvalue())

    def test_cli_renders_inspection_views_against_empty_postgresql_store(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        records_stdout = io.StringIO()
        status_stdout = io.StringIO()

        main.main(
            ["inspect-records", "--family", "alert"],
            stdout=records_stdout,
            service=service,
        )
        main.main(
            ["inspect-reconciliation-status"],
            stdout=status_stdout,
            service=service,
        )

        records_payload = json.loads(records_stdout.getvalue())
        status_payload = json.loads(status_stdout.getvalue())

        self.assertTrue(records_payload["read_only"])
        self.assertEqual(records_payload["record_family"], "alert")
        self.assertEqual(records_payload["total_records"], 0)
        self.assertEqual(records_payload["records"], [])

        self.assertTrue(status_payload["read_only"])
        self.assertEqual(status_payload["total_records"], 0)
        self.assertIsNone(status_payload["latest_compared_at"])
        self.assertEqual(status_payload["by_lifecycle_state"], {})
        self.assertEqual(status_payload["by_ingest_disposition"], {})
        self.assertEqual(status_payload["records"], [])


if __name__ == "__main__":
    unittest.main()
