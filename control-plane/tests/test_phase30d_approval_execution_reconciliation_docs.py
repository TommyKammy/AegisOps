from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30DApprovalExecutionReconciliationDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return (
            REPO_ROOT
            / "docs"
            / "phase-30d-approval-execution-reconciliation-ui-boundary.md"
        )

    def test_phase30d_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 30D design doc at {design_doc}")

    def test_phase30d_design_doc_defines_boundary_lifecycle_and_visibility(self) -> None:
        design_doc = self._design_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 30D design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 30D Approval, Execution, and Reconciliation UI Boundary",
            "Reviewed Phase 30D Boundary",
            "action request detail",
            "approval decision surface",
            "action review timeline",
            "execution receipt summary",
            "reconciliation mismatch visibility",
            "coordination reference panel",
            "approval is not a toggle",
            "execution success is not reconciliation success",
            "mismatch must remain visible",
            "pending",
            "approved",
            "rejected",
            "expired",
            "superseded",
            "unresolved",
            "degraded",
            "approval outcome",
            "execution outcome",
            "reconciliation outcome",
            "Shuffle-derived state",
            "subordinate context",
            "backend authorization",
            "role-gating",
            "authoritative re-read",
            "lifecycle reread",
            "browser may show",
            "browser may submit",
            "browser must not",
            "backend-owned lifecycle truth",
            "authoritative record chain",
            "AegisOps remains authoritative",
            "Safe implementation sequence",
            "action-review read support",
            "approval decision surfaces",
            "execution and reconciliation visibility",
            "validation",
            "browser-owned workflow truth",
            "approval-by-toggle shortcuts",
            "substrate-owned approval decisions",
            "generic CRUD expansion",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
