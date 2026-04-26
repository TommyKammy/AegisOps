from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import mock
from copy import deepcopy
from datetime import datetime, timezone


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from support.fixtures import load_wazuh_fixture


class OperatorInspectionBoundaryTests(unittest.TestCase):
    def _build_service(self) -> AegisOpsControlPlaneService:
        store, _ = make_store()
        return AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )

    def _ingest_queue_fixture(
        self,
        service: AegisOpsControlPlaneService,
        *,
        timestamp: datetime,
        native_id: str,
    ):
        alert = deepcopy(load_wazuh_fixture("github-audit-alert.json"))
        alert["id"] = native_id
        alert["timestamp"] = timestamp.isoformat()
        return service.ingest_wazuh_alert(
            raw_alert=alert,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="127.0.0.1",
        )

    def test_service_initializes_dedicated_operator_inspection_read_surface(
        self,
    ) -> None:
        service = self._build_service()

        self.assertTrue(
            hasattr(service, "_operator_inspection_read_surface"),
            "expected AegisOpsControlPlaneService to compose a dedicated operator inspection read surface",
        )

    def test_service_delegates_operator_inspection_entrypoints_to_read_surface(
        self,
    ) -> None:
        service = self._build_service()
        queue_snapshot = object()
        alert_detail = object()
        case_detail = object()
        inspection_read_surface = mock.Mock()
        inspection_read_surface.inspect_analyst_queue.return_value = queue_snapshot
        inspection_read_surface.inspect_alert_detail.return_value = alert_detail
        inspection_read_surface.inspect_case_detail.return_value = case_detail
        service._operator_inspection_read_surface = inspection_read_surface

        self.assertIs(service.inspect_analyst_queue(), queue_snapshot)
        self.assertIs(
            service.inspect_alert_detail("alert-inspection-001"),
            alert_detail,
        )
        self.assertIs(
            service.inspect_case_detail("case-inspection-001"),
            case_detail,
        )

        inspection_read_surface.inspect_analyst_queue.assert_called_once_with()
        inspection_read_surface.inspect_alert_detail.assert_called_once_with(
            "alert-inspection-001"
        )
        inspection_read_surface.inspect_case_detail.assert_called_once_with(
            "case-inspection-001"
        )

    def test_analyst_queue_projection_includes_backend_derived_daily_priority_fields(
        self,
    ) -> None:
        service = self._build_service()
        observed_at = datetime.now(timezone.utc).replace(microsecond=0)
        admitted = self._ingest_queue_fixture(
            service,
            timestamp=observed_at,
            native_id="queue-projection-normal-001",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-queue-001",
            triage_rationale="Keep daily queue ownership derived from AegisOps lead records.",
        )
        service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-review-001",
            intended_outcome="Review the queue projection before any approval-bound response.",
        )

        snapshot = service.inspect_analyst_queue()

        self.assertEqual(snapshot.total_records, 1)
        record = snapshot.records[0]
        self.assertEqual(record["owner"], "analyst-review-001")
        self.assertGreaterEqual(record["age_seconds"], 0)
        self.assertEqual(record["age_bucket"], "fresh")
        self.assertEqual(record["severity"], "high")
        self.assertGreaterEqual(record["last_activity_at"], observed_at)
        self.assertEqual(
            record["next_action"],
            "Review the queue projection before any approval-bound response.",
        )

    def test_analyst_queue_projection_keeps_empty_stale_and_missing_owner_states_visible(
        self,
    ) -> None:
        empty_service = self._build_service()
        empty_snapshot = empty_service.inspect_analyst_queue()
        self.assertEqual(empty_snapshot.total_records, 0)
        self.assertEqual(empty_snapshot.records, ())

        service = self._build_service()
        stale_at = datetime(2026, 4, 1, 9, 30, tzinfo=timezone.utc)
        admitted = self._ingest_queue_fixture(
            service,
            timestamp=stale_at,
            native_id="queue-projection-stale-001",
        )

        snapshot = service.inspect_analyst_queue()

        self.assertEqual(snapshot.total_records, 1)
        record = snapshot.records[0]
        self.assertEqual(record["alert_id"], admitted.alert.alert_id)
        self.assertIsNone(record["owner"])
        self.assertGreaterEqual(record["age_seconds"], 24 * 60 * 60)
        self.assertEqual(record["age_bucket"], "stale")
        self.assertEqual(record["severity"], "high")
        self.assertGreaterEqual(record["last_activity_at"], stale_at)
        self.assertEqual(record["next_action"], "Promote alert to case")


if __name__ == "__main__":
    unittest.main()
