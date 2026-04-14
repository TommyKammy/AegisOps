from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase22OperatorTrustBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return (
            REPO_ROOT
            / "docs"
            / "phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md"
        )

    @staticmethod
    def _validation_doc() -> pathlib.Path:
        return (
            REPO_ROOT
            / "docs"
            / "phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence-validation.md"
        )

    def test_phase22_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 22 design doc at {design_doc}")

    def test_phase22_design_doc_defines_state_semantics_mismatch_taxonomy_and_boundary(
        self,
    ) -> None:
        design_doc = self._design_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 22 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 22 Operator Trust and Workflow Ergonomics Boundary and Sequence",
            "Reviewed Phase 22 Boundary",
            "Operator Visibility Contract",
            "Reviewed Approval State Semantics",
            "pending",
            "expired",
            "rejected",
            "superseded",
            "Mismatch Taxonomy and Inspection Expectations",
            "delegation mismatch",
            "execution mismatch",
            "reconciliation mismatch",
            "manual fallback",
            "after-hours handoff",
            "escalation notes",
            "actor identity display",
            "Phase 22 does not approve",
            "new live action class",
            "browser-first redesign",
            "AI authority expansion",
            "reviewed Phase 20 approval / delegation / reconciliation binding guarantees",
        ):
            self.assertIn(term, text)

    def test_phase22_validation_doc_exists_and_records_required_review_outcomes(self) -> None:
        validation_doc = self._validation_doc()
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 22 validation doc at {validation_doc}",
        )
        text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "Phase 22 Operator Trust and Workflow Ergonomics Boundary and Sequence Validation",
            "Validation status: PASS",
            "state semantics",
            "mismatch taxonomy",
            "manual fallback",
            "after-hours handoff",
            "actor identity display",
            "Phase 19-21 fail-closed boundaries",
            "Phase 16-21 Epic Roadmap.md",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
