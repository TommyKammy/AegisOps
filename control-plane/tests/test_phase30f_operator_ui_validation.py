from __future__ import annotations

import pathlib
import sys
import unittest


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from support.operator_ui_sources import read_operator_routes_test_bundle


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30FOperatorUiValidationTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase30f_validation_doc_locks_taxonomy_and_subordinate_status_semantics(
        self,
    ) -> None:
        text = self._read("docs/phase-30f-optional-extension-visibility-validation.md")

        for term in (
            "# Phase 30F Optional-Extension Visibility Validation",
            "Validation status: PASS",
            "disabled-by-default posture remains distinct from unavailable posture",
            "enabled posture still fails closed unless backend-owned availability is explicit",
            "optional-extension visibility remains subordinate context rather than authoritative lifecycle truth",
            "mainline expectation messaging remains explicit when optional paths are absent",
            "control-plane/tests/test_phase30f_operator_ui_validation.py",
            "apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx",
            "apps/operator-ui/src/app/OperatorRoutes.test.tsx",
            "python3 -m unittest control-plane.tests.test_phase30f_operator_ui_validation",
            "npm --prefix apps/operator-ui test -- --run src/app/optionalExtensionVisibility.test.tsx src/app/OperatorRoutes.test.tsx",
            "npm --prefix apps/operator-ui run build",
        ):
            self.assertIn(term, text)

    def test_phase30f_readiness_defaults_keep_optional_extension_status_subordinate(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        readiness = service.inspect_readiness_diagnostics()
        optional_extensions = readiness.metrics["optional_extensions"]["extensions"]

        self.assertEqual(
            optional_extensions["assistant"]["enablement"],
            "enabled",
        )
        self.assertEqual(
            optional_extensions["assistant"]["authority_mode"],
            "advisory_only",
        )

        for extension_name, authority_mode in (
            ("endpoint_evidence", "augmenting_evidence"),
            ("network_evidence", "augmenting_evidence"),
            ("ml_shadow", "shadow_only"),
        ):
            with self.subTest(extension=extension_name):
                self.assertEqual(
                    optional_extensions[extension_name]["enablement"],
                    "disabled_by_default",
                )
                self.assertEqual(
                    optional_extensions[extension_name]["mainline_dependency"],
                    "non_blocking",
                )
                self.assertEqual(
                    optional_extensions[extension_name]["authority_mode"],
                    authority_mode,
                )

    def test_phase30f_frontend_tests_lock_taxonomy_and_non_authority_rendering(
        self,
    ) -> None:
        mapper_tests = self._read(
            "apps/operator-ui/src/app/optionalExtensionVisibility.test.tsx"
        )
        route_tests = read_operator_routes_test_bundle(REPO_ROOT)

        for term in (
            "keeps disabled-by-default posture distinct from unavailable",
            "fails closed when enablement says enabled but availability is missing",
            "keeps degraded posture primary over other optional signals",
        ):
            self.assertIn(term, mapper_tests)

        for term in (
            "keeps disabled-by-default endpoint and network evidence posture visible",
            "fails closed when optional enablement is present without backend availability",
            "Optional extension visibility",
            "Optional evidence posture",
            "Disabled By Default",
            "Optional-path posture stays subordinate to authoritative workflow pages and reviewed runtime truth.",
            "Missing optional paths do not imply a control-plane failure when the mainline reviewed workflow remains healthy.",
        ):
            self.assertIn(term, route_tests)


if __name__ == "__main__":
    unittest.main()
