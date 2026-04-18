from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase26CoordinationSubstrateBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase26_design_doc_exists_and_names_first_reviewed_coordination_substrate(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary.md"
        )

        for term in (
            "AegisOps Phase 26 First Coordination Substrate and Non-Authoritative Ticket Boundary",
            "Zammad is the preferred first reviewed coordination substrate for Phase 26.",
            "GLPI remains the reviewed fallback only if Zammad proves unsuitable",
            "link-first ticket reference",
            "future reviewed create-ticket soft-write path",
            "non-authoritative coordination target",
            "AegisOps remains authoritative for alert, case, approval, execution, and reconciliation truth",
            "`coordination_reference_id`",
            "`coordination_target_type`",
            "`coordination_target_id`",
            "`ticket_reference_url`",
            "`external_receipt_id`",
            "`delegation_id`",
            "ticket state must not become case truth",
        ):
            self.assertIn(term, text)

    def test_phase26_validation_note_records_alignment_with_roadmap_and_boundary_docs(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary-validation.md"
        )

        for term in (
            "Phase 26 First Coordination Substrate and Non-Authoritative Ticket Boundary Validation",
            "Validation status: PASS",
            "ObsidianVault/Dev/AegisOps/Plan&Roadmap/Revised Phase23-29 Epic Roadmap.md",
            "docs/requirements-baseline.md",
            "docs/response-action-safety-model.md",
            "docs/control-plane-state-model.md",
            "Zammad is the preferred first reviewed coordination substrate.",
            "GLPI remains the reviewed fallback only if implementation review rejects Zammad.",
            "non-authoritative coordination target",
        ):
            self.assertIn(term, text)

        self.assertNotIn("docs/Revised Phase23-20 Epic Roadmap.md", text)

    def test_baseline_docs_keep_ticketing_subordinate_to_aegisops_authority(self) -> None:
        expected_terms = {
            "docs/requirements-baseline.md": (
                "The first reviewed external coordination substrate for Phase 26 is Zammad, with GLPI retained only as a reviewed fallback option.",
                "External coordination substrates must remain subordinate coordination targets rather than becoming the authority for alert, case, approval, action-execution, or reconciliation truth.",
                "Link-first external ticket references may be recorded without promoting external ticket lifecycle into control-plane truth.",
            ),
            "docs/response-action-safety-model.md": (
                "A link-only ticket reference does not become approval-free workflow authority.",
                "The future reviewed create-ticket path remains a `Soft Write` coordination action, not a transfer of case, approval, execution, or reconciliation authority into the external ticket system.",
                "External ticket status, assignee changes, comments, or queue movement must not be treated as approval proof, execution proof, or case closure on their own.",
            ),
            "docs/control-plane-state-model.md": (
                "Reviewed coordination substrates may contribute ticket identifiers, URLs, assignee metadata, comments, queue movement, and other coordination receipts, but those artifacts remain subordinate evidence rather than authoritative control-plane lifecycle state.",
                "External coordination receipts must not replace `Case`, `Approval Decision`, `Action Execution`, or `Reconciliation` records.",
                "`coordination_reference_id`, `coordination_target_type`, `coordination_target_id`, `ticket_reference_url`, and any `external_receipt_id` must remain explicit linkage fields rather than borrowed lifecycle owners.",
            ),
        }

        for relative_path, terms in expected_terms.items():
            with self.subTest(path=relative_path):
                text = self._read(relative_path)
                for term in terms:
                    self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
