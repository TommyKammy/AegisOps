from __future__ import annotations

import ast
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase49ServiceDecompositionCloseoutTests(unittest.TestCase):
    def _path(self, relative_path: str) -> pathlib.Path:
        path = REPO_ROOT / relative_path
        if path.exists():
            return path
        canonical_relative_path = relative_path.replace(
            "control-plane/aegisops_control_plane/",
            "control-plane/aegisops/control_plane/",
            1,
        )
        return REPO_ROOT / canonical_relative_path

    def _read(self, relative_path: str) -> str:
        path = self._path(relative_path)
        if not path.exists():
            raise AssertionError(f"expected Phase 49.0 closeout artifact at {path}")
        return path.read_text(encoding="utf-8")

    def _defined_test_names(self, *relative_paths: str) -> set[str]:
        defined_names: set[str] = set()
        for relative_path in relative_paths:
            source = self._read(relative_path)
            tree = ast.parse(source, filename=relative_path)
            defined_names.update(
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            )
        return defined_names

    def _facade_method_count(self, class_name: str) -> int:
        tree = ast.parse(
            self._read("control-plane/aegisops_control_plane/service.py"),
            filename="control-plane/aegisops_control_plane/service.py",
        )
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                return sum(
                    1
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                )
        raise AssertionError(f"{class_name} class not found")

    def _effective_line_count(self, text: str) -> int:
        return sum(
            1
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

    def _baseline_metadata(self) -> dict[str, str]:
        for line in self._read("docs/maintainability-hotspot-baseline.txt").splitlines():
            stripped = line.strip()
            if stripped.startswith("control-plane/aegisops/control_plane/service.py"):
                metadata: dict[str, str] = {}
                for part in stripped.split()[1:]:
                    key, value = part.split("=", 1)
                    metadata[key] = value
                return metadata
        raise AssertionError("service.py hotspot baseline entry not found")

    def test_closeout_baseline_records_adr_exception_and_current_facade_limits(
        self,
    ) -> None:
        service_text = self._read("control-plane/aegisops_control_plane/service.py")
        metadata = self._baseline_metadata()

        self.assertEqual(metadata["adr_exception"], "ADR-0003")
        self.assertEqual(metadata["phase"], "50.13.5")
        self.assertEqual(metadata["issue"], "#1035")
        self.assertEqual(metadata["facade_class"], "AegisOpsControlPlaneService")
        self.assertLessEqual(len(service_text.splitlines()), int(metadata["max_lines"]))
        self.assertLessEqual(
            self._effective_line_count(service_text),
            int(metadata["max_effective_lines"]),
        )
        self.assertLessEqual(
            self._facade_method_count(metadata["facade_class"]),
            int(metadata["max_facade_methods"]),
        )
        self.assertLessEqual(int(metadata["max_lines"]), 1500)
        self.assertGreater(int(metadata["max_facade_methods"]), 50)

        adr = self._read("docs/adr/0003-phase-49-service-decomposition-boundaries.md")
        self.assertIn("ADR-approved exception", adr)
        self.assertIn("1,500-line target", adr)
        self.assertIn("50-method target", adr)

    def test_phase49_extracted_boundary_modules_remain_present(self) -> None:
        expected_modules = (
            "control-plane/aegisops_control_plane/detection_lifecycle.py",
            "control-plane/aegisops_control_plane/case_workflow.py",
            "control-plane/aegisops_control_plane/evidence_linkage.py",
            "control-plane/aegisops_control_plane/ai_trace_lifecycle.py",
            "control-plane/aegisops_control_plane/action_reconciliation_orchestration.py",
            "control-plane/aegisops_control_plane/runtime_boundary.py",
            "control-plane/aegisops_control_plane/restore_readiness.py",
            "control-plane/aegisops_control_plane/runtime_restore_readiness_diagnostics.py",
        )

        for relative_path in expected_modules:
            self.assertTrue(self._path(relative_path).is_file(), relative_path)

    def test_phase49_focused_regression_suites_cover_extracted_boundaries(self) -> None:
        defined_tests = self._defined_test_names(
            "control-plane/tests/test_service_persistence_ingest_case_lifecycle.py",
            "control-plane/tests/test_service_persistence_assistant_advisory.py",
            "control-plane/tests/test_execution_coordinator_boundary.py",
            "control-plane/tests/test_phase21_runtime_auth_validation.py",
            "control-plane/tests/test_service_persistence_restore_readiness.py",
        )

        for test_name in (
            "test_service_initializes_dedicated_detection_intake_boundary",
            "test_service_delegates_detection_intake_and_triage_operations",
            "test_service_initializes_dedicated_case_workflow_and_evidence_linkage_boundaries",
            "test_service_delegates_assistant_context_to_assembler_and_advisory_to_coordinator",
            "test_service_initializes_focused_action_and_reconciliation_boundaries",
            "test_operational_runtime_surfaces_are_extracted_into_dedicated_collaborators",
            "test_service_routes_runtime_restore_and_readiness_through_diagnostics_boundary",
            "test_service_wires_restore_readiness_internal_collaborators",
        ):
            self.assertIn(test_name, defined_tests)


if __name__ == "__main__":
    unittest.main()
