from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase30EAssistantAdvisoryUiBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase30e_design_doc_exists_and_defines_assistant_ui_boundary(self) -> None:
        text = self._read("docs/phase-30e-assistant-advisory-integration-boundary.md")

        for term in (
            "AegisOps Phase 30E Assistant and Advisory UI Boundary",
            "Reviewed Phase 30E Boundary",
            "advisory output detail",
            "assistant context inspection",
            "recommendation draft rendering",
            "citation-first rendering",
            "missing-citation failure",
            "conflicting context",
            "unresolved",
            "no-authority posture",
            "non-authoritative",
            "must not present assistant output as a final answer",
            "must not present assistant output as an approved decision",
            "must not present assistant output as an execution fact",
            "must not present assistant output as a reconciliation fact",
            "authoritative anchor record",
            "assistant context snapshot",
            "browser may show",
            "browser must not",
            "Safe implementation sequence",
            "advisory detail route",
            "assistant context panel",
            "recommendation draft card",
            "validation",
        ):
            self.assertIn(term, text)

    def test_phase30e_validation_doc_records_alignment_and_validation_scope(self) -> None:
        text = self._read("docs/phase-30e-assistant-advisory-integration-validation.md")

        for term in (
            "Phase 30E Assistant and Advisory UI Validation",
            "Validation status: PASS",
            "docs/phase-30e-assistant-advisory-integration-boundary.md",
            "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md",
            "docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md",
            "docs/phase-30d-approval-execution-reconciliation-ui-boundary.md",
            "citation-first rendering",
            "ambiguity visibility",
            "draft-versus-authoritative split",
            "no-authority posture",
            "python3 -m unittest control-plane.tests.test_phase30e_assistant_advisory_ui_boundary_docs",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
