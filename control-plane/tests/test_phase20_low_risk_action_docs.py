from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase20LowRiskActionDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return (
            REPO_ROOT
            / "docs"
            / "phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
        )

    @staticmethod
    def _validation_doc() -> pathlib.Path:
        return (
            REPO_ROOT
            / "docs"
            / "phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary-validation.md"
        )

    def test_phase20_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 20 design doc at {design_doc}")

    def test_phase20_design_doc_defines_one_approved_low_risk_action_and_boundary(
        self,
    ) -> None:
        design_doc = self._design_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 20 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 20 First Live Low-Risk Action and Reviewed Delegation Boundary",
            "Approved First Live Low-Risk Action",
            "notify_identity_owner",
            "single-recipient owner-notification path",
            "Operator-to-Approval-to-Delegation Boundary",
            "Human-Owned Steps",
            "Shuffle-Delegated Steps",
            "approval_decision_id",
            "delegation_id",
            "payload_hash",
            "approved expiry window",
            "fail closed",
            "broader action catalog",
            "policy-authorized unattended low-risk execution",
            "high-risk live executor wiring",
        ):
            self.assertIn(term, text)

    def test_phase20_validation_doc_exists_and_records_alignment_caveat(self) -> None:
        validation_doc = self._validation_doc()
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 20 validation doc at {validation_doc}",
        )
        text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "Phase 20 First Live Low-Risk Action and Reviewed Delegation Boundary Validation",
            "Validation status: PASS",
            "notify_identity_owner",
            "Shuffle only as the approved low-risk execution substrate",
            "payload binding, approval expiry, and mismatch handling remain fail closed",
            "Phase 16-21 Epic Roadmap.md",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
