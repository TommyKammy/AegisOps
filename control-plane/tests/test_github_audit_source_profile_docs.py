from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DOC_PATH = REPO_ROOT / "docs" / "source-families" / "github-audit" / "onboarding-package.md"


class GitHubAuditSourceProfileDocsTests(unittest.TestCase):
    def test_github_audit_onboarding_package_defines_the_reviewed_wazuh_profile(self) -> None:
        self.assertTrue(DOC_PATH.exists(), f"expected reviewed GitHub audit package at {DOC_PATH}")
        text = DOC_PATH.read_text(encoding="utf-8")

        for term in (
            "GitHub Audit Wazuh-Backed Source Profile Onboarding Package",
            "Readiness state: `detection-ready`",
            "Wazuh-backed source profile",
            "Reviewed detection-ready scope",
            "Parser and Version Evidence",
            "Reviewed parser evidence source",
            "Field Coverage Verification",
            "Provenance Evidence",
            "Detector-Use Approval and Limits",
            "accountable source identity",
            "actor identity",
            "target identity",
            "repository or organization context",
            "privilege-change metadata",
            "Detector activation still requires separate rule review, rollout review, and Wazuh rule lifecycle validation.",
            "Direct GitHub API actioning",
            "Non-audit GitHub telemetry families",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
