from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase24LiveAssistantWorkflowDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase24_design_doc_exists_and_bounds_first_live_workflow_family(self) -> None:
        text = self._read(
            "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md"
        )

        for term in (
            "AegisOps Phase 24 First Live Assistant Workflow Family and Trusted Output Contract",
            "first live assistant workflow family",
            "queue triage summary",
            "case summary",
            "advisory-only",
            "must force `unresolved`",
            "approval, delegation, execution, and policy authority outside the assistant boundary",
        ):
            self.assertIn(term, text)

    def test_phase24_design_doc_defines_trusted_output_contract_and_fail_closed_conditions(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md"
        )

        for term in (
            "Trusted Output Contract",
            "`workflow_family`",
            "`workflow_task`",
            "`status`",
            "`summary`",
            "`citations`",
            "`unresolved_reasons`",
            "reviewed record inputs",
            "required citation fields",
            "allowed fields",
            "If required citations are missing",
            "If reviewed records conflict",
            "If the operator request asks for approval, delegation, execution, or policy interpretation",
        ):
            self.assertIn(term, text)

    def test_phase24_validation_doc_records_alignment_with_roadmap_readme_and_phase15_boundary(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract-validation.md"
        )

        for term in (
            "Phase 24 First Live Assistant Workflow Family and Trusted Output Contract Validation",
            "Validation status: PASS",
            "docs/Revised Phase23-20 Epic Roadmap.md",
            "README.md",
            "docs/phase-15-identity-grounded-analyst-assistant-boundary.md",
            "workflow contract",
            "authority model",
            "advisory-only",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
