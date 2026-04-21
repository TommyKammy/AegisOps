from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30COperatorUiValidationTests(unittest.TestCase):
    def test_phase30c_validation_doc_covers_authoritative_reread_and_failure_visibility(self) -> None:
        text = self._read("docs/phase-30c-bounded-write-actions-validation.md")

        for term in (
            "# Phase 30C Bounded Write Actions Validation",
            "Validation status: PASS",
            "authoritative re-read",
            "no optimistic authority",
            "task-oriented bounded write actions",
            "promote",
            "casework updates",
            "reviewed action-request creation",
            "manual fallback",
            "escalation notes",
            "degraded",
            "unauthorized",
            "conflict",
            "failed-submit",
            "actor, provenance, binding, lifecycle, and reviewed authorization signals",
            "python3 -m unittest control-plane.tests.test_phase30c_operator_ui_validation",
            "npm --prefix apps/operator-ui test",
            "npm --prefix apps/operator-ui run build",
        ):
            self.assertIn(term, text)

    def test_phase30c_frontend_tests_lock_authoritative_refresh_and_bounded_write_metadata(self) -> None:
        primitives_tests = self._read("apps/operator-ui/src/taskActions/taskActionPrimitives.test.tsx")
        card_tests = self._read("apps/operator-ui/src/taskActions/caseworkActionCards.test.tsx")

        for term in (
            "submits through the bounded task-action client and re-reads authoritative state",
            "keeps uncertainty explicit when the authoritative reread fails after submit",
            "classifies unauthorized submit failures without implying success",
            "classifies conflict submit failures without implying success",
            "keeps failed-submit outcomes explicit when the backend returns a server error",
            "Authoritative refresh completed from the reviewed backend record.",
            "Authoritative re-read did not complete after submit",
            "Reviewed backend authorization denied the task action.",
        ):
            self.assertIn(term, primitives_tests)

        for term in (
            "renders task-oriented metadata for promote, casework, action-request, and fallback flows",
            "Promote alert into case",
            "Record case observation",
            "Record case lead",
            "Record case recommendation",
            "Create reviewed action request",
            "Record manual fallback",
            "Record escalation note",
            "reviewed operator promote endpoint",
            "reviewed operator observation endpoint",
            "reviewed operator lead endpoint",
            "reviewed operator recommendation endpoint",
            "reviewed operator action-request endpoint",
            "reviewed operator manual-fallback endpoint",
            "reviewed operator escalation-note endpoint",
            "Current review state",
            "Next expected action",
        ):
            self.assertIn(term, card_tests)

    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
