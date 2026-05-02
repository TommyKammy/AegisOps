from __future__ import annotations

import pathlib
import sys
import unittest
from datetime import datetime, timezone


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTROL_PLANE_ROOT = REPO_ROOT / "control-plane"
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


class ServiceSnapshotExtractionTests(unittest.TestCase):
    def test_service_preserves_legacy_snapshot_imports_from_dto_module(self) -> None:
        from aegisops.control_plane import service
        from aegisops.control_plane import service_snapshots

        snapshot_names = (
            "RuntimeSnapshot",
            "AuthenticatedRuntimePrincipal",
            "RecordInspectionSnapshot",
            "ReconciliationStatusSnapshot",
            "AnalystQueueSnapshot",
            "AlertDetailSnapshot",
            "CaseDetailSnapshot",
            "ActionReviewDetailSnapshot",
            "AnalystAssistantContextSnapshot",
            "AdvisoryInspectionSnapshot",
            "RecommendationDraftSnapshot",
            "LiveAssistantWorkflowSnapshot",
            "StartupStatusSnapshot",
            "ShutdownStatusSnapshot",
            "RestoreDrillSnapshot",
            "RestoreSummarySnapshot",
            "ReadinessDiagnosticsSnapshot",
        )

        for snapshot_name in snapshot_names:
            with self.subTest(snapshot_name=snapshot_name):
                snapshot_class = getattr(service_snapshots, snapshot_name)
                self.assertIs(getattr(service, snapshot_name), snapshot_class)
                self.assertEqual(snapshot_class.__module__, service_snapshots.__name__)

    def test_snapshot_to_dict_preserves_tuple_and_datetime_json_shape(self) -> None:
        from aegisops.control_plane.service import ReconciliationStatusSnapshot

        compared_at = datetime(2026, 4, 30, 12, 34, 56, tzinfo=timezone.utc)
        snapshot = ReconciliationStatusSnapshot(
            read_only=True,
            total_records=1,
            latest_compared_at=compared_at,
            by_lifecycle_state={"open": 1},
            by_ingest_disposition={"promoted": 1},
            records=(
                {
                    "record_id": "reconciliation-1",
                    "observed_at": compared_at,
                    "linked_ids": ("case-1", "alert-1"),
                },
            ),
        )

        self.assertEqual(
            snapshot.to_dict(),
            {
                "read_only": True,
                "total_records": 1,
                "latest_compared_at": "2026-04-30T12:34:56+00:00",
                "by_lifecycle_state": {"open": 1},
                "by_ingest_disposition": {"promoted": 1},
                "records": [
                    {
                        "record_id": "reconciliation-1",
                        "observed_at": "2026-04-30T12:34:56+00:00",
                        "linked_ids": ["case-1", "alert-1"],
                    },
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
