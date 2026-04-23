from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from support.operator_ui_sources import read_operator_routes_test_bundle


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30EOperatorUiValidationTests(unittest.TestCase):
    def test_phase30e_validation_doc_locks_citations_ambiguity_and_no_authority_boundary(
        self,
    ) -> None:
        text = self._read("docs/phase-30e-assistant-advisory-integration-validation.md")

        for term in (
            "# Phase 30E Assistant and Advisory UI Validation",
            "Validation status: PASS",
            "citation-first rendering remains mandatory",
            "ambiguity visibility remains explicit",
            "draft-versus-authoritative split remains explicit",
            "missing citations or malformed citation support must render as a missing-citation failure",
            "advisory output remains non-authoritative",
            "does not imply approval, execution, or reconciliation outcome",
            "control-plane/tests/test_phase30e_operator_ui_validation.py",
            "apps/operator-ui/src/app/OperatorRoutes.test.tsx",
            "python3 -m unittest control-plane.tests.test_phase30e_operator_ui_validation",
            "npm --prefix apps/operator-ui test -- src/app/OperatorRoutes.test.tsx",
            "npm --prefix apps/operator-ui run build",
        ):
            self.assertIn(term, text)

    def test_phase30e_frontend_tests_lock_citations_ambiguity_and_no_authority_semantics(
        self,
    ) -> None:
        operator_routes_tests = read_operator_routes_test_bundle(REPO_ROOT)

        for term in (
            "renders a case-anchored assistant advisory route from reviewed advisory output",
            "keeps no-authority semantics explicit for cited advisory output without a recommendation draft",
            "renders cited recommendation draft output with explicit assistant-only framing",
            "renders explicit citation-failure and reviewed-context visibility for unresolved advisory output",
            "Assistant output does not approve, execute, or reconcile workflow state.",
            "Missing citation support is visible here",
            "Conflicting reviewed context remains visible here",
            "Assistant advisory remains unresolved because required citation or reviewed-context checks failed.",
            "Assistant context explorer",
            "Recommendation draft",
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
