from __future__ import annotations

import json
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANDIDATE_DIR = (
    REPO_ROOT
    / "docs"
    / "source-families"
    / "github-audit"
    / "detector-activation-candidates"
)
FIXTURE_PATH = REPO_ROOT / "control-plane" / "tests" / "fixtures" / "wazuh" / "github-audit-alert.json"
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-github-audit-detector-activation-candidate.sh"


class GitHubAuditDetectorActivationCandidateDocsTests(unittest.TestCase):
    def test_single_github_audit_activation_candidate_is_reviewable_and_bounded(self) -> None:
        self.assertTrue(CANDIDATE_DIR.exists(), f"missing candidate directory: {CANDIDATE_DIR}")
        candidates = sorted(CANDIDATE_DIR.glob("*.md"))
        self.assertEqual(
            [path.name for path in candidates],
            ["repository-admin-membership-change.md"],
        )

        text = candidates[0].read_text(encoding="utf-8")

        for term in (
            "Lifecycle state: `candidate`",
            "Candidate scope: GitHub audit repository administrator membership changes",
            "Candidate Rule Review Criteria",
            "Fixture And Parser Evidence",
            "`control-plane/tests/fixtures/wazuh/github-audit-alert.json`",
            "`decoder.name` is `github_audit`",
            "`data.audit_action` is `member.added`",
            "`data.privilege.permission` is `admin`",
            "Staging Activation Expectations",
            "False-Positive Review Expectations",
            "Rollback Expectations",
            "GitHub audit remains source evidence only",
            "does not authorize direct GitHub API actioning",
            "does not make GitHub the authority for AegisOps case state, approval state, action state, execution state, or reconciliation outcomes",
        ):
            self.assertIn(term, text)

    def test_candidate_fixture_preserves_required_parser_and_privilege_evidence(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(fixture["decoder"]["name"], "github_audit")
        self.assertEqual(fixture["rule"]["id"], "github-audit-privilege-change")
        self.assertEqual(fixture["rule"]["description"], "GitHub audit repository privilege change")
        self.assertEqual(fixture["data"]["source_family"], "github_audit")
        self.assertEqual(fixture["data"]["audit_action"], "member.added")
        self.assertEqual(fixture["data"]["privilege"]["change_type"], "membership_change")
        self.assertEqual(fixture["data"]["privilege"]["scope"], "repository_admin")
        self.assertEqual(fixture["data"]["privilege"]["permission"], "admin")
        self.assertEqual(fixture["data"]["privilege"]["role"], "maintainer")
        self.assertEqual(fixture["data"]["repository"]["full_name"], "TommyKammy/AegisOps")
        self.assertEqual(fixture["manager"]["name"], "wazuh-manager-github-1")
        self.assertEqual(fixture["data"]["request_id"], "GH-REQ-0001")

    def test_candidate_verifier_is_available_for_source_family_review(self) -> None:
        self.assertTrue(VERIFIER_PATH.exists(), f"missing verifier: {VERIFIER_PATH}")


if __name__ == "__main__":
    unittest.main()
