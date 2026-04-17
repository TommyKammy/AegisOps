from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase23SubstrateSimplificationValidationTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_reviewed_security_mainline_declares_shuffle_as_single_routine_substrate(
        self,
    ) -> None:
        expected_terms = {
            "README.md": (
                "Shuffle",
                "reviewed routine automation substrate",
                "n8n",
                "optional, transitional, or experimental orchestration substrate",
            ),
            "docs/architecture.md": (
                "The initial standard routine automation substrate is Shuffle.",
                "n8n may still be used as an optional, transitional, or experimental executor or orchestration substrate outside the reviewed security mainline.",
            ),
            "docs/automation-substrate-contract.md": (
                "reviewed Shuffle automation substrate",
                "reviewed downstream execution surface",
            ),
            "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md": (
                "reviewed Shuffle delegation",
                "Shuffle is delegated only the bounded transport task",
                "the request is routed to any execution surface other than `automation_substrate` on `shuffle`",
            ),
        }

        for relative_path, terms in expected_terms.items():
            with self.subTest(path=relative_path):
                text = self._read(relative_path)
                for term in terms:
                    self.assertIn(term, text)

    def test_phase23_validation_note_records_single_reviewed_security_substrate(self) -> None:
        text = self._read("docs/phase-23-substrate-simplification-validation.md")

        for term in (
            "Phase 23 Substrate Simplification Validation",
            "Validation status: PASS",
            "Shuffle is the single reviewed routine-automation substrate for the security mainline.",
            "n8n remains optional, experimental, or transitional and is not part of the reviewed security authority path.",
            "README.md",
            "docs/architecture.md",
            "docs/automation-substrate-contract.md",
            "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md",
        ):
            self.assertIn(term, text)

    def test_requirements_baseline_keeps_approval_authority_on_reviewed_control_plane_path(
        self,
    ) -> None:
        text = self._read("docs/requirements-baseline.md")

        self.assertIn(
            "AegisOps is the reviewed control plane for approval, evidence, and reconciliation governance",
            text,
        )
        self.assertIn(
            "other explicitly approved AegisOps-reviewed approval interfaces",
            text,
        )
        self.assertNotIn("* n8n UI when n8n is the approved execution substrate", text)


if __name__ == "__main__":
    unittest.main()
