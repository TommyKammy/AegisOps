from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase25MultiSourceCaseAdmissionDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase25_design_doc_exists_and_defines_case_admission_taxonomy(self) -> None:
        text = self._read(
            "docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md"
        )

        for term in (
            "AegisOps Phase 25 Reviewed Multi-Source Case Admission and Ambiguity Taxonomy",
            "reviewed multi-source case admission",
            "GitHub audit context",
            "approved second reviewed source family for this slice (`entra_id`)",
            "osquery-backed host evidence",
            "`same-entity`",
            "`related-entity`",
            "`unresolved`",
            "must fail closed",
            "must not stitch entities automatically",
        ):
            self.assertIn(term, text)

    def test_phase25_design_doc_defines_admission_provenance_and_display_rules(self) -> None:
        text = self._read(
            "docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md"
        )

        for term in (
            "Case Admission Contract",
            "authoritative anchor record",
            "stable identifiers",
            "provenance classification",
            "`record.provenance`",
            "`record.provenance.classification`",
            "`record.provenance.source_id`",
            "`record.provenance.timestamp`",
            "`reviewed_context.provenance_classification`",
            "provenance badge",
            "Each attached record must surface exactly one provenance badge.",
            "Each non-anchor attached record must also surface exactly one ambiguity badge.",
            "The ambiguity badge applies only to non-anchor attached records",
            "same-entity / related-entity / unresolved taxonomy",
            "operator-facing ambiguity display",
            "substrate-local UI",
            "reviewed case chain",
            "Phase 24 trusted output contract",
        ):
            self.assertIn(term, text)

    def test_phase25_validation_doc_records_alignment_with_roadmap_readme_architecture_and_phase24(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy-validation.md"
        )

        for term in (
            "Phase 25 Reviewed Multi-Source Case Admission and Ambiguity Taxonomy Validation",
            "Validation status: PASS",
            "Old Revised Phase23-20 Epic Roadmap.md",
            "README.md",
            "docs/architecture.md",
            "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md",
            "advisory-only",
            "unresolved model",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
