from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase19OperatorSurfaceDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-19-thin-operator-surface-and-daily-analyst-workflow.md"

    @staticmethod
    def _validation_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md"

    def test_phase19_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 19 design doc at {design_doc}")

    def test_phase19_design_doc_defines_operator_surface_workflow_and_deferred_scope(self) -> None:
        design_doc = self._design_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 19 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 19 Thin Operator Surface and First Daily Analyst Workflow",
            "Approved Phase 19 Thin Operator Surface",
            "Daily queue review",
            "Alert inspection",
            "Casework entry",
            "Evidence review",
            "Cited advisory review",
            "GitHub audit",
            "Wazuh-backed",
            "AegisOps remains the primary daily work surface",
            "read-only evidence access",
            "bounded analyst actions",
            "deferred beyond Phase 19",
            "broader dashboarding",
            "full interactive assistant behavior",
            "medium-risk or high-risk live action wiring",
        ):
            self.assertIn(term, text)

    def test_phase19_validation_doc_exists_and_records_alignment_caveat(self) -> None:
        validation_doc = self._validation_doc()
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 19 validation doc at {validation_doc}",
        )
        text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "Phase 19 Thin Operator Surface and First Daily Analyst Workflow Validation",
            "Validation status: PASS",
            "Phase 18 live-path baseline",
            "AegisOps as the primary daily work surface",
            "queue review through alert inspection, casework entry, evidence review, and cited advisory review",
            "deferred surfaces and actions remain visibly out of scope",
            "Phase 16-21 Epic Roadmap.md",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
