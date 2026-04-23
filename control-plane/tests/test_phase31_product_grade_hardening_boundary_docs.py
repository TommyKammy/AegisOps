from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase31ProductGradeHardeningBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase31_design_doc_exists_and_defines_browser_hardening_boundary(
        self,
    ) -> None:
        text = self._read("docs/phase-31-product-grade-hardening-boundary.md")

        for term in (
            "AegisOps Phase 31 Product-Grade Hardening Boundary",
            "Reviewed Phase 31 Boundary",
            "route-gating",
            "menu-gating",
            "page-gating",
            "backend authorization",
            "Reviewed Deep-Link Policy",
            "returnTo",
            "queue and operator overview entry routes",
            "alert detail routes",
            "case detail routes",
            "assistant advisory routes",
            "action-review routes",
            "unauthorized",
            "forbidden",
            "invalid-session",
            "empty",
            "error",
            "degraded",
            "shared shell-state taxonomy",
            "browser-rendered convenience surfaces",
            "backend-authoritative workflow truth",
            "Client-Event Logging Boundary",
            "route entry and route denial outcomes",
            "raw session tokens",
            "browser-local audit conclusions",
            "Product-Grade Browser Guardrails",
            "caching and session scope",
            "authoritative refetch",
            "fixed theming decisions",
            "Safe implementation sequence",
            "deep-link normalization and return-path policy",
            "bounded client-event logging",
            "validation",
            "dev-only mock identities",
            "generic CRUD expansion",
            "browser-owned workflow authority",
        ):
            self.assertIn(term, text)

    def test_phase31_validation_doc_records_alignment_and_verification_scope(
        self,
    ) -> None:
        text = self._read("docs/phase-31-product-grade-hardening-boundary-validation.md")

        for term in (
            "Phase 31 Product-Grade Hardening Boundary Validation",
            "Validation status: PASS",
            "docs/phase-31-product-grade-hardening-boundary.md",
            "docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md",
            "docs/phase-30d-approval-execution-reconciliation-ui-boundary.md",
            "docs/phase-30e-assistant-advisory-integration-boundary.md",
            "docs/phase-30f-optional-extension-visibility-boundary.md",
            "apps/operator-ui/src/app/OperatorRoutes.tsx",
            "apps/operator-ui/src/app/OperatorShell.tsx",
            "apps/operator-ui/src/app/OperatorRoutes.test.tsx",
            "apps/operator-ui/e2e/operator-workflows.spec.ts",
            "playwright.config.ts",
            "route, menu, and page-level gating remain posture controls while backend authorization stays authoritative",
            "deep-link and `returnTo` handling remain bounded",
            "unauthorized, forbidden, invalid-session, empty, error, and degraded shell states remain explicit and non-interchangeable",
            "client-event logging remains bounded, audit-friendly, and subordinate to backend audit records",
            "python3 -m unittest control-plane.tests.test_phase31_product_grade_hardening_boundary_docs",
            "python3 -m unittest control-plane.tests.test_phase31_operator_ui_validation",
            "npm --prefix apps/operator-ui exec playwright test",
            "npm --prefix apps/operator-ui test -- --run src/app/OperatorRoutes.test.tsx",
            "npm --prefix apps/operator-ui run build",
            "issue-lint 712",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
