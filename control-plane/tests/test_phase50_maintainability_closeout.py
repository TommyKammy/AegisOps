from __future__ import annotations

import ast
import pathlib
import shutil
import subprocess
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase50MaintainabilityCloseoutTests(unittest.TestCase):
    def _read(self, relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected Phase 50 closeout artifact at {path}")
        return path.read_text(encoding="utf-8")

    def _effective_line_count(self, text: str) -> int:
        return sum(
            1
            for line in text.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

    def _facade_method_count(self, class_name: str) -> int:
        service_text = self._read("control-plane/aegisops_control_plane/service.py")
        tree = ast.parse(
            service_text,
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

    def _baseline_metadata(self) -> dict[str, str]:
        for line in self._read("docs/maintainability-hotspot-baseline.txt").splitlines():
            stripped = line.strip()
            if stripped.startswith("control-plane/aegisops_control_plane/service.py"):
                metadata: dict[str, str] = {}
                for part in stripped.split()[1:]:
                    key, value = part.split("=", 1)
                    metadata[key] = value
                return metadata
        raise AssertionError("service.py hotspot baseline entry not found")

    def test_baseline_records_current_phase50_closeout_measurements(self) -> None:
        service_text = self._read("control-plane/aegisops_control_plane/service.py")
        metadata = self._baseline_metadata()
        physical_lines = len(service_text.splitlines())
        effective_lines = self._effective_line_count(service_text)
        facade_methods = self._facade_method_count(metadata["facade_class"])

        self.assertEqual(metadata["adr_exception"], "ADR-0003")
        self.assertEqual(metadata["phase"], "50.13.3")
        self.assertEqual(metadata["issue"], "#1033")
        self.assertEqual(metadata["facade_class"], "AegisOpsControlPlaneService")
        self.assertEqual(int(metadata["max_lines"]), physical_lines)
        self.assertEqual(int(metadata["max_effective_lines"]), effective_lines)
        self.assertEqual(int(metadata["max_facade_methods"]), facade_methods)
        self.assertEqual(physical_lines, 1393)
        self.assertEqual(effective_lines, 1241)
        self.assertEqual(facade_methods, 95)
        self.assertLess(int(metadata["max_lines"]), 1812)
        self.assertLess(int(metadata["max_effective_lines"]), 1632)
        self.assertLess(int(metadata["max_facade_methods"]), 125)
        self.assertLessEqual(int(metadata["max_lines"]), 1500)
        self.assertLessEqual(int(metadata["max_effective_lines"]), 1350)
        self.assertLessEqual(int(metadata["max_facade_methods"]), 95)

    def test_closeout_notes_preserve_phase50_10_hotspot_and_trigger(self) -> None:
        closeout = self._read("docs/phase-50-maintainability-closeout.md")

        for required in (
            "Phase 50.11.7",
            "Phase 50.12.2",
            "Phase 50.12.3",
            "Phase 50.12.4",
            "Phase 50.12.5",
            "Phase 50.12.6",
            "Phase 50.12.7",
            "Phase 50.13.3",
            "control-plane/aegisops_control_plane/service.py",
            "control-plane/aegisops_control_plane/case_workflow.py",
            "control-plane/aegisops_control_plane/action_review_write_surface.py",
            "control-plane/aegisops_control_plane/operator_inspection.py",
            "control-plane/aegisops_control_plane/execution_coordinator_action_requests.py",
            "control-plane/aegisops_control_plane/action_review_projection.py",
            "control-plane/aegisops_control_plane/external_evidence_boundary.py",
            "control-plane/aegisops_control_plane/ai_trace_lifecycle.py",
            "AegisOpsControlPlaneService",
            "max_lines=1393",
            "max_effective_lines=1241",
            "max_facade_methods=95",
            "physical_lines=1393",
            "effective_lines=1241",
            "max_lines <= 1500",
            "max_effective_lines <= 1350",
            "max_facade_methods <= 95",
            "ADR-0007",
            "ADR-0008",
            "ADR-0009",
            "ADR-0004",
            "ADR-0003",
            "#1007",
            "#1017",
            "#1021",
            "#1022",
            "#1033",
            "#1018",
            "#1019",
            "#1020",
            "remaining accepted hotspot",
            "facade dispatch, compatibility entrypoints, runtime-boundary guards, and lifecycle/write-path delegates",
            "reviewed action approval policy helpers",
            "casework write compatibility delegates",
            "reviewed action-request binding guards",
            "projection split does not require a baseline entry",
            "external-evidence split does not require a baseline entry",
            "silent re-growth",
            "another decomposition decision",
            "bash scripts/verify-maintainability-hotspots.sh",
            "bash scripts/test-verify-maintainability-hotspots.sh",
            "bash scripts/verify-phase-50-12-service-facade-pressure-contract.sh",
            "bash scripts/test-verify-phase-50-12-service-facade-pressure-contract.sh",
        ):
            self.assertIn(required, closeout)

    def test_verifier_reports_only_phase50_accepted_hotspot(self) -> None:
        bash_executable = shutil.which("bash")
        if bash_executable is None:
            self.fail("bash executable not found")

        result = subprocess.run(
            [bash_executable, "scripts/verify-maintainability-hotspots.sh"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=30,
        )

        self.assertIn("Known maintainability hotspot baseline remains present", result.stdout)
        self.assertIn("control-plane/aegisops_control_plane/service.py", result.stdout)
        self.assertNotIn("baseline limits were exceeded", result.stderr)

    def test_negative_verifier_coverage_keeps_regrowth_path(self) -> None:
        verifier_test = self._read("scripts/test-verify-maintainability-hotspots.sh")

        for required in (
            "regrowth_repo",
            "phase50_11_regrowth_repo",
            "phase50_12_final_regrowth_repo",
            "Maintainability hotspot baseline limits were exceeded",
            "lines=960 exceeds max_lines=959",
            "effective_lines=960 exceeds max_effective_lines=959",
            "lines=1774 exceeds max_lines=1773",
            "effective_lines=1774 exceeds max_effective_lines=1589",
            "lines=1452 exceeds max_lines=1451",
            "effective_lines=1452 exceeds max_effective_lines=1294",
            "max_facade_methods=0",
        ):
            self.assertIn(required, verifier_test)


if __name__ == "__main__":
    unittest.main()
