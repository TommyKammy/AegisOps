from __future__ import annotations

from datetime import datetime, timezone
import contextlib
import io
import json
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

import main
from aegisops_control_plane.adapters.postgres import PostgresControlPlaneStore
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import AlertRecord, ReconciliationRecord
from aegisops_control_plane.service import AegisOpsControlPlaneService


class ControlPlaneCliInspectionTests(unittest.TestCase):
    def test_cli_renders_read_only_record_and_reconciliation_views(self) -> None:
        store = PostgresControlPlaneStore("postgresql://control-plane.local/aegisops")
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
            ReconciliationRecord(
                reconciliation_id="reconciliation-001",
                subject_linkage={"alert_ids": ("alert-001",)},
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                workflow_execution_id=None,
                linked_execution_ids=(),
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
        self.assertEqual(records_payload["records"][0]["alert_id"], "alert-001")

        self.assertTrue(status_payload["read_only"])
        self.assertEqual(status_payload["total_records"], 1)
        self.assertEqual(status_payload["by_ingest_disposition"], {"created": 1})
        self.assertEqual(
            status_payload["latest_compared_at"],
            "2026-04-05T12:00:00+00:00",
        )

    def test_cli_rejects_unknown_record_family_as_usage_error(self) -> None:
        store = PostgresControlPlaneStore("postgresql://control-plane.local/aegisops")
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

    def test_cli_rejects_standalone_inspection_against_in_memory_runtime(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc_info:
                main.main(["inspect-records", "--family", "alert"])

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("require a persisted control-plane store", stderr.getvalue())
        self.assertIn("persistence_mode='in_memory'", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
