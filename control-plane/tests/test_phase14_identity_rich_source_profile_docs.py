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


if __name__ == "__main__":
    unittest.main()
