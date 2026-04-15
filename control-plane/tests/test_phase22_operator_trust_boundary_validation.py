from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase22OperatorTrustBoundaryValidationTests(unittest.TestCase):
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

    def test_phase22_validation_artifacts_cross_reference_governing_contracts(self) -> None:
        design_doc = self._design_doc()
        validation_doc = self._validation_doc()
        end_to_end_test = (
            REPO_ROOT / "control-plane" / "tests" / "test_phase22_end_to_end_validation.py"
        )
        self.assertTrue(design_doc.exists(), f"expected Phase 22 design doc at {design_doc}")
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 22 validation doc at {validation_doc}",
        )
        self.assertTrue(
            end_to_end_test.exists(),
            f"expected Phase 22 end-to-end validation tests at {end_to_end_test}",
        )

        design_text = design_doc.read_text(encoding="utf-8")
        validation_text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md",
            "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md",
            "docs/phase-21-production-like-hardening-boundary-and-sequence.md",
            "docs/control-plane-state-model.md",
            "docs/automation-substrate-contract.md",
            "docs/response-action-safety-model.md",
            "docs/secops-business-hours-operating-model.md",
            "docs/architecture.md",
        ):
            self.assertIn(term, design_text)
            self.assertIn(term, validation_text)

        for term in (
            "control-plane/tests/test_phase22_end_to_end_validation.py",
            "python3 -m unittest control-plane.tests.test_phase22_end_to_end_validation control-plane.tests.test_phase22_operator_trust_boundary_docs control-plane.tests.test_phase22_operator_trust_boundary_validation",
            "Reviewed Approval State Semantics",
            "Mismatch Taxonomy and Inspection Expectations",
            "manual fallback",
            "after-hours handoff",
            "reviewed Phase 20 approval / delegation / reconciliation binding guarantees",
            "Phase 22 end-to-end validation keeps pending, expired, rejected, superseded, delegation, execution, reconciliation, manual fallback, after-hours handoff, and escalation-note trust surfaces explicit without weakening Phase 19-21 fail-closed behavior.",
        ):
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
