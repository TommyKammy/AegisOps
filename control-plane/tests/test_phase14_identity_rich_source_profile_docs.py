from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase14IdentityRichSourceProfileDocsTests(unittest.TestCase):
    def test_microsoft_365_and_entra_source_profile_docs_exist(self) -> None:
        microsoft_doc = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "microsoft-365-audit"
            / "onboarding-package.md"
        )
        entra_doc = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "entra-id"
            / "onboarding-package.md"
        )

        for doc_path in (microsoft_doc, entra_doc):
            self.assertTrue(doc_path.exists(), f"expected reviewed onboarding package at {doc_path}")

    def test_phase14_family_triage_runbooks_exist(self) -> None:
        runbook_paths = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "github-audit"
            / "analyst-triage-runbook.md",
            REPO_ROOT
            / "docs"
            / "source-families"
            / "microsoft-365-audit"
            / "analyst-triage-runbook.md",
            REPO_ROOT
            / "docs"
            / "source-families"
            / "entra-id"
            / "analyst-triage-runbook.md",
        )

        for doc_path in runbook_paths:
            self.assertTrue(doc_path.exists(), f"expected reviewed triage runbook at {doc_path}")

    def test_microsoft_365_onboarding_package_defines_the_reviewed_wazuh_profile(
        self,
    ) -> None:
        text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "microsoft-365-audit"
            / "onboarding-package.md"
        ).read_text(encoding="utf-8")

        for term in (
            "Microsoft 365 Audit Wazuh-Backed Source Profile Onboarding Package",
            "Readiness state: `schema-reviewed`",
            "Wazuh-backed source profile",
            "tenant context",
            "actor identity",
            "target identity",
            "authentication context",
            "privilege-change metadata",
            "Direct Microsoft 365 actioning",
            "Non-audit Microsoft 365 telemetry families",
        ):
            self.assertIn(term, text)

    def test_entra_onboarding_package_defines_the_reviewed_wazuh_profile(self) -> None:
        text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "entra-id"
            / "onboarding-package.md"
        ).read_text(encoding="utf-8")

        for term in (
            "Entra ID Wazuh-Backed Source Profile Onboarding Package",
            "Readiness state: `schema-reviewed`",
            "Wazuh-backed source profile",
            "tenant context",
            "actor identity",
            "target identity",
            "authentication context",
            "privilege-change metadata",
            "Direct Entra ID actioning",
            "Non-audit Entra ID telemetry families",
        ):
            self.assertIn(term, text)

    def test_phase14_family_triage_runbooks_define_the_reviewed_posture(self) -> None:
        github_text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "github-audit"
            / "analyst-triage-runbook.md"
        ).read_text(encoding="utf-8")
        microsoft_text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "microsoft-365-audit"
            / "analyst-triage-runbook.md"
        ).read_text(encoding="utf-8")
        entra_text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "entra-id"
            / "analyst-triage-runbook.md"
        ).read_text(encoding="utf-8")

        shared_terms = (
            "Business-hours SecOps daily operating model",
            "AegisOps Source Onboarding Contract",
            "Wazuh Rule Lifecycle and Validation Runbook",
            "control-plane-first analyst workflow",
            "false-positive expectations",
            "read-oriented evidence",
        )
        family_specific_terms = {
            github_text: (
                "GitHub audit",
                "repository or organization context",
                "accountable source identity",
                "Direct GitHub API actioning",
            ),
            microsoft_text: (
                "Microsoft 365 audit",
                "tenant context",
                "authentication context",
                "Direct Microsoft 365 actioning",
            ),
            entra_text: (
                "Entra ID",
                "directory boundary",
                "authentication context",
                "Direct Entra ID actioning",
            ),
        }

        for text, terms in family_specific_terms.items():
            for term in shared_terms + terms:
                self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
