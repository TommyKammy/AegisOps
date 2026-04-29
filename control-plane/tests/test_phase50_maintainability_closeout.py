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

    def test_baseline_records_phase50_closeout_ceiling(self) -> None:
        service_text = self._read("control-plane/aegisops_control_plane/service.py")
        metadata = self._baseline_metadata()

        self.assertEqual(metadata["adr_exception"], "ADR-0003")
        self.assertEqual(metadata["phase"], "50.8.6")
        self.assertEqual(metadata["issue"], "#967")
        self.assertEqual(metadata["facade_class"], "AegisOpsControlPlaneService")
        self.assertEqual(int(metadata["max_lines"]), len(service_text.splitlines()))
        self.assertEqual(
            int(metadata["max_effective_lines"]),
            self._effective_line_count(service_text),
        )
        self.assertEqual(
            int(metadata["max_facade_methods"]),
            self._facade_method_count(metadata["facade_class"]),
        )

    def test_closeout_notes_preserve_remaining_hotspot_and_trigger(self) -> None:
        closeout = self._read("docs/phase-50-maintainability-closeout.md")

        for required in (
            "Phase 50.8.6",
            "control-plane/aegisops_control_plane/service.py",
            "AegisOpsControlPlaneService",
            "max_lines=3505",
            "max_effective_lines=3182",
            "max_facade_methods=185",
            "ADR-0004",
            "ADR-0003",
            "#967",
            "remaining accepted hotspot",
            "action review projection and visibility helper cluster",
            "intake and authoritative-state guard helpers",
            "silent re-growth",
            "another decomposition decision",
            "bash scripts/verify-maintainability-hotspots.sh",
            "bash scripts/test-verify-maintainability-hotspots.sh",
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
            "Maintainability hotspot baseline limits were exceeded",
            "lines=960 exceeds max_lines=959",
            "effective_lines=960 exceeds max_effective_lines=959",
            "max_facade_methods=0",
        ):
            self.assertIn(required, verifier_test)


if __name__ == "__main__":
    unittest.main()
