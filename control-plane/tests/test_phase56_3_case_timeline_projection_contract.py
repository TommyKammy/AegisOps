from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT_PATH = (
    REPO_ROOT / "docs/deployment/case-timeline-authority-projection-contract.md"
)
ARTIFACT_PATH = (
    REPO_ROOT
    / "docs/deployment/profiles/smb-single-node/case-timeline-projection.yaml"
)
README_PATH = REPO_ROOT / "README.md"


class Phase563CaseTimelineProjectionContractTests(unittest.TestCase):
    @staticmethod
    def _read(path: pathlib.Path) -> str:
        if not path.exists():
            raise AssertionError(f"expected file at {path.relative_to(REPO_ROOT)}")
        return path.read_text(encoding="utf-8")

    def test_contract_names_segments_states_and_authority_boundary(self) -> None:
        text = self._read(CONTRACT_PATH)

        for term in (
            "Phase 56.3 Case Timeline Authority Projection Contract",
            "wazuh_signal",
            "aegisops_alert",
            "evidence",
            "ai_summary",
            "recommendation",
            "action_request",
            "approval",
            "shuffle_receipt",
            "reconciliation",
            "normal",
            "missing",
            "degraded",
            "stale",
            "mismatch",
            "unsupported",
            "Only AegisOps control-plane records carry",
            "reject inferred linkage from sibling records",
            "Missing, degraded, stale, mismatch, and unsupported segments remain visible",
        ):
            self.assertIn(term, text)

    def test_artifact_names_segments_authority_postures_and_negative_cases(self) -> None:
        text = self._read(ARTIFACT_PATH)

        for term in (
            "case_timeline_projection_contract_version: 2026-05-04",
            "projection_owner: aegisops-control-plane",
            "workflow_truth_source: aegisops-record-chain-only",
            "projection_authority_allowed: false",
            "inferred_linkage_allowed: false",
            "authoritative_aegisops_record",
            "subordinate_context",
            "missing-backend-record-binding",
            "inferred-sibling-linkage",
            "wazuh-shuffle-ai-ticket-report-truth-overreach",
            "stale-projection-as-current-truth",
        ):
            self.assertIn(term, text)

        for segment in (
            "wazuh_signal",
            "aegisops_alert",
            "evidence",
            "ai_summary",
            "recommendation",
            "action_request",
            "approval",
            "shuffle_receipt",
            "reconciliation",
        ):
            self.assertRegex(text, rf"(?m)^  - {segment}$")

        for state in ("normal", "missing", "degraded", "stale", "mismatch", "unsupported"):
            self.assertRegex(text, rf"(?m)^  - {state}$")

    def test_readme_links_phase563_contract(self) -> None:
        self.assertIn(
            "docs/deployment/case-timeline-authority-projection-contract.md",
            self._read(README_PATH),
        )


if __name__ == "__main__":
    unittest.main()
