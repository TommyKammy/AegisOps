from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase31OperatorUiValidationTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase31_validation_doc_locks_browser_hardening_boundary(self) -> None:
        text = self._read("docs/phase-31-product-grade-hardening-boundary-validation.md")

        for term in (
            "# Phase 31 Product-Grade Hardening Boundary Validation",
            "Validation status: PASS",
            "route, menu, and page-level gating remain posture controls while backend authorization stays authoritative",
            "deep-link and `returnTo` handling remain bounded to reviewed operator route families",
            "unauthorized, forbidden, invalid-session, empty, error, and degraded shell states remain explicit and non-interchangeable",
            "browser-rendered convenience surfaces remain distinct from backend-authoritative workflow truth",
            "client-event logging remains bounded, audit-friendly, and subordinate to backend audit records",
            "caching, refetch, reload, and fixed-theme guardrails remain product-grade browser behavior rather than workflow authority expansion",
            "control-plane/tests/test_phase31_operator_ui_validation.py",
            "apps/operator-ui/src/app/OperatorRoutes.test.tsx",
            "python3 -m unittest control-plane.tests.test_phase31_operator_ui_validation",
            "npm --prefix apps/operator-ui test -- --run src/app/OperatorRoutes.test.tsx",
            "npm --prefix apps/operator-ui run build",
        ):
            self.assertIn(term, text)

    def test_phase31_frontend_route_tests_lock_fail_closed_access_semantics(self) -> None:
        operator_routes_tests = self._read("apps/operator-ui/src/app/OperatorRoutes.test.tsx")

        for term in (
            "redirects unauthenticated users to the reviewed login route",
            "Return path: /operator/queue",
            "routes unsupported backend roles to the forbidden page",
            "fails closed on malformed reviewed session responses",
            "uses the configured base path for reviewed operator navigation links",
            "allows analyst deep links into reviewed action-review detail as read-only inspection",
            "honors allowed-role extensions for reviewed action-review detail routes",
            "fails closed on unsupported assistant advisory route families",
            "renders a case-anchored assistant advisory route from reviewed advisory output",
            "keeps no-authority semantics explicit for cited advisory output without a recommendation draft",
        ):
            self.assertIn(term, operator_routes_tests)

    def test_phase31_shell_and_route_sources_expose_reviewed_gating_and_binding_points(
        self,
    ) -> None:
        operator_routes = self._read("apps/operator-ui/src/app/OperatorRoutes.tsx")
        operator_shell = self._read("apps/operator-ui/src/app/OperatorShell.tsx")

        for term in (
            'params.get("returnTo") ?? config.basePath',
            'setStatus("forbidden")',
            'setStatus("invalid_session")',
            'setStatus("unauthenticated")',
            "CircularProgress aria-label=\"Checking operator session\"",
        ):
            self.assertIn(term, operator_routes)

        for term in (
            "function buildOperatorShellPath(basePath: string, path = \"\")",
            'to={buildOperatorShellPath(basePath, "action-review")}',
            'to={buildOperatorShellPath(basePath, "forbidden")}',
            'path="assistant/:recordFamily/:recordId"',
            'path="action-review/:actionRequestId"',
            'path="*"',
            "Unsupported operator route",
            "Open provenance from alert or case detail so the page stays anchored to an authoritative record.",
        ):
            self.assertIn(term, operator_shell)


if __name__ == "__main__":
    unittest.main()
