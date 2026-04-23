from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from support.operator_ui_sources import read_operator_routes_test_bundle


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30OperatorUiValidationTests(unittest.TestCase):
    def test_phase30_validation_doc_covers_auth_read_only_and_degraded_flows(self) -> None:
        text = self._read(
            "docs/phase-30-react-admin-foundation-and-read-only-operator-console-validation.md"
        )

        for term in (
            "# Phase 30 React-Admin Foundation and Read-Only Operator Console Validation",
            "Validation status: PASS",
            "auth-aligned, read-only, role-aware, and visibly non-authoritative",
            "Role-aware navigation is derived from reviewed backend role assertions",
            "Action-review navigation stays hidden for analyst-only sessions and appears for reviewed approver sessions",
            "The React-Admin adapter remains read-only and explicitly rejects mutation verbs",
            "Queue and detail surfaces keep degraded, missing-anchor, mismatch, and unresolved state visible",
            "python3 -m unittest control-plane.tests.test_phase30_operator_ui_validation",
            "npm --prefix apps/operator-ui run test -- src/auth/authProvider.test.ts src/auth/session.test.ts src/dataProvider.test.ts src/app/OperatorRoutes.test.tsx",
            "npm --prefix apps/operator-ui run build",
        ):
            self.assertIn(term, text)

    def test_phase30_frontend_tests_lock_auth_role_and_read_only_behaviors(self) -> None:
        route_tests = read_operator_routes_test_bundle(REPO_ROOT)
        data_provider_tests = self._read("apps/operator-ui/src/dataProvider.test.ts")
        auth_navigation = self._read("apps/operator-ui/src/auth/navigation.ts")

        for term in (
            "hides action-review navigation for analyst-only sessions",
            "shows action-review navigation for reviewed approver sessions",
            "keeps degraded and missing-anchor queue warnings explicit",
            "redirects unauthenticated users to the reviewed login route",
            "routes unsupported backend roles to the forbidden page",
        ):
            self.assertIn(term, route_tests)

        for term in (
            "rejects all mutation verbs so the adapter remains read-only",
            "requires authoritative scope metadata before advisory output reads",
            "fails closed when a reviewed queue record is missing its authoritative anchor",
        ):
            self.assertIn(term, data_provider_tests)

        self.assertIn("Window location is unavailable for auth redirects.", auth_navigation)

    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
