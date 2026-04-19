from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


class OperatorInspectionBoundaryTests(unittest.TestCase):
    def _build_service(self) -> AegisOpsControlPlaneService:
        store, _ = make_store()
        return AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
            ),
            store=store,
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


if __name__ == "__main__":
    unittest.main()
