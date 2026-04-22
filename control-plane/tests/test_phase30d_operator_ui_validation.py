from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30DOperatorUiValidationTests(unittest.TestCase):
    def test_phase30d_validation_doc_locks_lifecycle_and_visibility_semantics(self) -> None:
        text = self._read("docs/phase-30d-approval-execution-reconciliation-ui-validation.md")

        for term in (
            "# Phase 30D Approval, Execution, and Reconciliation UI Validation",
            "Validation status: PASS",
            "approval lifecycle stays explicit",
            "`pending`, `approved`, `rejected`, `expired`, `superseded`, `unresolved`, and `degraded`",
            "execution receipt visibility remains separate from approval outcome and reconciliation outcome",
            "reconciliation mismatch visibility stays explicit",
            "coordination or Shuffle-derived context stays subordinate",
            "approval is not a toggle",
            "execution success is not reconciliation success",
            "authoritative re-read remains required",
            "route-gating and role-gating stay posture controls while backend authorization remains the enforcement boundary",
            "degraded, forbidden, expired, unresolved, and mismatch states stay explicit",
            "control-plane/tests/test_phase30d_operator_ui_validation.py",
            "apps/operator-ui/src/app/OperatorRoutes.test.tsx",
            "keeping expired approval lifecycle state explicit without implying execution or reconciliation success",
            "python3 -m unittest control-plane.tests.test_phase30d_operator_ui_validation",
            "python3 -m unittest control-plane.tests.test_phase30d_approval_execution_reconciliation_docs",
            "npm --prefix apps/operator-ui test",
            "npm --prefix apps/operator-ui run build",
        ):
            self.assertIn(term, text)

    def test_phase30d_frontend_tests_cover_authoritative_split_and_explicit_failure_states(
        self,
    ) -> None:
        operator_routes_tests = self._read("apps/operator-ui/src/app/OperatorRoutes.test.tsx")

        for term in (
            "renders the reviewed action-review detail route from backend-authoritative action review data",
            "renders execution receipt, reconciliation mismatch, and coordination visibility on action-review detail",
            "submits a reviewed approval decision and waits for the authoritative reread before rendering the approved lifecycle",
            "keeps expired approval lifecycle state explicit without implying execution or reconciliation success",
            "Execution receipt",
            "Reconciliation visibility",
            "Coordination visibility",
            "Expired means the reviewed approval window no longer authorizes this request.",
            "No authoritative execution receipt is attached to this reviewed request yet.",
            "No authoritative reconciliation record is visible for this reviewed request yet.",
        ):
            self.assertIn(term, operator_routes_tests)

    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
