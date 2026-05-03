from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CONTRACT_PATH = REPO_ROOT / "docs/deployment/today-view-backend-projection-contract.md"
ARTIFACT_PATH = (
    REPO_ROOT
    / "docs/deployment/profiles/smb-single-node/today-view-projection.yaml"
)


class Phase561TodayProjectionContractTests(unittest.TestCase):
    @staticmethod
    def _read(path: pathlib.Path) -> str:
        if not path.exists():
            raise AssertionError(f"expected file at {path.relative_to(REPO_ROOT)}")
        return path.read_text(encoding="utf-8")

    def test_contract_names_required_lanes_states_and_authority_boundary(self) -> None:
        text = self._read(CONTRACT_PATH)

        for term in (
            "Phase 56.1 Today View Backend Projection Contract",
            "priority",
            "stale_work",
            "pending_approvals",
            "degraded_sources",
            "reconciliation_mismatches",
            "evidence_gaps",
            "ai_suggested_focus",
            "empty",
            "normal",
            "degraded",
            "stale",
            "mismatch",
            "evidence_gap",
            "advisory-only",
            "AegisOps control-plane records remain authoritative",
            "Stale or cached Today projection output cannot satisfy authority, approval, execution, or reconciliation truth.",
        ):
            self.assertIn(term, text)

    def test_artifact_names_required_lanes_states_and_negative_cases(self) -> None:
        text = self._read(ARTIFACT_PATH)

        for term in (
            "today_view_projection_contract_version: 2026-05-04",
            "projection_owner: aegisops-control-plane",
            "workflow_truth_source: aegisops-record-chain-only",
            "authority_mutation_allowed: false",
            "cached_projection_authority_allowed: false",
            "ai_focus_authority_allowed: false",
            "lanes:",
            "states:",
            "negative_validation_tests:",
            "stale-projection-as-current-truth",
            "ai-focus-as-authority",
            "wazuh-shuffle-ticket-closeout-shortcut",
            "today-summary-as-approval-execution-reconciliation-truth",
        ):
            self.assertIn(term, text)

        for lane in (
            "priority",
            "stale_work",
            "pending_approvals",
            "degraded_sources",
            "reconciliation_mismatches",
            "evidence_gaps",
            "ai_suggested_focus",
        ):
            self.assertRegex(text, rf"(?m)^  - {lane}$")

        for state in ("empty", "normal", "degraded", "stale", "mismatch", "evidence_gap"):
            self.assertRegex(text, rf"(?m)^  - {state}$")


if __name__ == "__main__":
    unittest.main()
