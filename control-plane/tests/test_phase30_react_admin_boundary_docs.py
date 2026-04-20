from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30ReactAdminBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return (
            REPO_ROOT
            / "docs"
            / "phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md"
        )

    def test_phase30_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 30 design doc at {design_doc}")

    def test_phase30_design_doc_defines_boundary_auth_adapter_and_sequence(self) -> None:
        design_doc = self._design_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 30 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 30 React-Admin Foundation and Read-Only Operator Console Boundary",
            "Reviewed Phase 30 Boundary",
            "thin React-Admin client",
            "AegisOps backend responses remain the sole authority source",
            "Authentik and OIDC Authentication Boundary",
            "`authProvider`",
            "protected routes",
            "login",
            "logout",
            "role-aware navigation",
            "Adapter and `dataProvider` Contract",
            "resource and route semantics",
            "must not force generic create or edit behavior",
            "queue",
            "alert",
            "case",
            "provenance",
            "readiness",
            "reconciliation",
            "advisory output",
            "action review",
            "authoritative anchor records",
            "subordinate Wazuh",
            "Shuffle",
            "Read-Only Sequencing",
            "shell and auth",
            "adapter and `dataProvider`",
            "read-only pages",
            "validation",
            "write actions",
            "approval decisions",
            "optimistic updates",
            "UI-owned authority",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
