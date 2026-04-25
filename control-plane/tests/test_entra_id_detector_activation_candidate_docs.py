from __future__ import annotations

import json
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANDIDATE_DIR = (
    REPO_ROOT
    / "docs"
    / "source-families"
    / "entra-id"
    / "detector-activation-candidates"
)
FIXTURE_PATH = REPO_ROOT / "control-plane" / "tests" / "fixtures" / "wazuh" / "entra-id-alert.json"
VERIFIER_PATH = REPO_ROOT / "scripts" / "verify-entra-id-detector-activation-candidate.sh"


class EntraIdDetectorActivationCandidateDocsTests(unittest.TestCase):
    def test_single_entra_id_activation_candidate_is_reviewable_and_bounded(self) -> None:
        self.assertTrue(CANDIDATE_DIR.exists(), f"missing candidate directory: {CANDIDATE_DIR}")
        candidates = sorted(CANDIDATE_DIR.glob("*.md"))
        self.assertEqual(
            [path.name for path in candidates],
            ["privileged-role-assignment.md"],
        )

        text = candidates[0].read_text(encoding="utf-8")

        for term in (
            "Lifecycle state: `candidate`",
            "Candidate scope: Entra ID privileged directory role assignments",
            "Candidate Rule Review Criteria",
            "Fixture And Parser Evidence",
            "`control-plane/tests/fixtures/wazuh/entra-id-alert.json`",
            "`decoder.name` is `entra_id`",
            "`data.audit_action` is `Add member to role`",
            "`data.privilege.scope` is `directory_role`",
            "`data.privilege.permission` is `Global Administrator`",
            "Staging Activation Expectations",
            "False-Positive Review Expectations",
            "Rollback And Disable Procedure",
            "Entra ID remains source evidence only",
            "does not authorize direct Entra ID actioning",
            "does not make Entra ID the authority for AegisOps case state, approval state, action state, execution state, or reconciliation outcomes",
        ):
            self.assertIn(term, text)

    def test_candidate_fixture_preserves_required_parser_and_privilege_evidence(self) -> None:
        fixture = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(fixture["decoder"]["name"], "entra_id")
        self.assertEqual(fixture["rule"]["id"], "entra-id-role-assignment")
        self.assertEqual(fixture["rule"]["description"], "Entra ID privileged role assignment")
        self.assertEqual(fixture["data"]["source_family"], "entra_id")
        self.assertEqual(fixture["data"]["audit_action"], "Add member to role")
        self.assertEqual(fixture["data"]["operation"], "Add member to role")
        self.assertEqual(fixture["data"]["record_type"], "Entra ID audit")
        self.assertEqual(fixture["data"]["privilege"]["change_type"], "role_assignment")
        self.assertEqual(fixture["data"]["privilege"]["scope"], "directory_role")
        self.assertEqual(fixture["data"]["privilege"]["permission"], "Global Administrator")
        self.assertEqual(fixture["data"]["privilege"]["role"], "Privileged Role Administrator")
        self.assertEqual(fixture["data"]["tenant"]["id"], "tenant-001")
        self.assertEqual(fixture["data"]["actor"]["id"], "spn-operations")
        self.assertEqual(fixture["data"]["target"]["id"], "role-global-admin")
        self.assertEqual(fixture["manager"]["name"], "wazuh-manager-entra-1")
        self.assertEqual(fixture["data"]["correlation_id"], "entra-corr-0001")
        self.assertEqual(fixture["data"]["request_id"], "ENTRA-REQ-0001")

    def test_candidate_verifier_is_available_for_source_family_review(self) -> None:
        self.assertTrue(VERIFIER_PATH.exists(), f"missing verifier: {VERIFIER_PATH}")


if __name__ == "__main__":
    unittest.main()
