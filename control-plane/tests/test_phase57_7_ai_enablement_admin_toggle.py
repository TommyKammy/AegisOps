from __future__ import annotations

from dataclasses import replace
import pathlib
import sys
import unittest


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from support.service_persistence import ServicePersistenceTestBase


class Phase57_7AIEnablementAdminToggleTests(ServicePersistenceTestBase):
    def _service_with_ai_posture(
        self,
        posture: str,
    ) -> AegisOpsControlPlaneService:
        store, _ = make_store()
        return AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                ai_enablement_posture=posture,
            ),
            store=store,
        )

    def test_ai_enablement_admin_postures_are_visible_and_advisory_only(self) -> None:
        expected = {
            "enabled": (
                "available",
                "ready",
                "bounded_reviewed_summary_provider_available",
            ),
            "disabled": (
                "unavailable",
                "not_applicable",
                "ai_advisory_disabled_by_admin",
            ),
            "degraded": ("unavailable", "degraded", "ai_advisory_degraded_by_admin"),
        }

        for posture, (availability, readiness, reason) in expected.items():
            with self.subTest(posture=posture):
                service = self._service_with_ai_posture(posture)

                diagnostics = service.inspect_readiness_diagnostics()
                optional_extensions = diagnostics.metrics["optional_extensions"]
                assistant = optional_extensions["extensions"]["assistant"]

                self.assertEqual(assistant["enablement"], posture)
                self.assertEqual(assistant["availability"], availability)
                self.assertEqual(assistant["readiness"], readiness)
                self.assertEqual(assistant["reason"], reason)
                self.assertEqual(assistant["authority_mode"], "advisory_only")
                self.assertEqual(assistant["mainline_dependency"], "non_blocking")

    def test_ai_disabled_mode_preserves_non_ai_workflow_surfaces(self) -> None:
        store, base_service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        service = AegisOpsControlPlaneService(
            replace(
                base_service._config,
                ai_enablement_posture="disabled",
            ),
            store=store,
        )

        queue_view = service.inspect_analyst_queue()
        case_detail = service.inspect_case_detail(promoted_case.case_id)
        diagnostics = service.inspect_readiness_diagnostics()
        assistant = diagnostics.metrics["optional_extensions"]["extensions"][
            "assistant"
        ]

        self.assertEqual(queue_view.records[0]["case_id"], promoted_case.case_id)
        self.assertEqual(case_detail.case_id, promoted_case.case_id)
        self.assertEqual(
            diagnostics.metrics["optional_extensions"]["overall_state"],
            "ready",
        )
        self.assertEqual(assistant["enablement"], "disabled")
        self.assertEqual(assistant["authority_mode"], "advisory_only")

        with self.assertRaisesRegex(
            PermissionError,
            "AI advisory path is disabled by platform-admin posture",
        ):
            service.inspect_advisory_output("case", promoted_case.case_id)

    def test_ai_enablement_env_rejects_feature_expansion_values(self) -> None:
        self.assertEqual(
            RuntimeConfig.from_env(
                {"AEGISOPS_CONTROL_PLANE_AI_ENABLEMENT_POSTURE": "degraded"}
            ).ai_enablement_posture,
            "degraded",
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_AI_ENABLEMENT_POSTURE must be one of",
        ):
            RuntimeConfig.from_env(
                {"AEGISOPS_CONTROL_PLANE_AI_ENABLEMENT_POSTURE": "execute"}
            )


if __name__ == "__main__":
    unittest.main()
