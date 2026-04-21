from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30CBoundedWriteActionsDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-30c-bounded-write-actions-ui-boundary.md"

    def test_phase30c_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 30C design doc at {design_doc}")

    def test_phase30c_design_doc_defines_task_boundary_and_refresh_contract(self) -> None:
        design_doc = self._design_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 30C design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 30C Bounded Write Actions UI Boundary",
            "Reviewed Phase 30C Boundary",
            "bounded write actions",
            "task-oriented client",
            "must not inherit generic create and edit semantics from React-Admin",
            "Generic CRUD fallback remains prohibited",
            "Approved bounded write-action ceiling",
            "alert-to-case promotion",
            "case observation",
            "case lead",
            "case recommendation",
            "reviewed action-request creation",
            "manual fallback or escalation notes",
            "task forms",
            "confirmation affordances",
            "actor and provenance visibility",
            "browser-owned workflow truth",
            "authoritative re-read",
            "authoritative refresh sequence",
            "optimistic authority shortcuts",
            "role-gating",
            "route protection",
            "reviewed backend authorization",
            "bounded task-action layer",
            "shared write-action clients",
            "dataProvider",
            "Generic React-Admin mutations stay disabled by default",
            "degraded",
            "unauthorized",
            "stale",
            "conflict",
            "failed-submit",
            "approval decisions",
            "execution controls",
            "reconciliation mutation",
            "substrate-owned forms",
            "assistant-owned authority",
            "Safe implementation sequence",
            "shared primitives",
            "core casework actions",
            "action-request and fallback flows",
            "validation",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
