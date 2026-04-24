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
        family_specific_terms = (
            (
                "github-audit",
                github_text,
                (
                    "GitHub audit",
                    "repository or organization context",
                    "accountable source identity",
                    "Direct GitHub API actioning",
                ),
            ),
            (
                "microsoft-365-audit",
                microsoft_text,
                (
                    "Microsoft 365 audit",
                    "tenant context",
                    "authentication context",
                    "Direct Microsoft 365 actioning",
                ),
            ),
            (
                "entra-id",
                entra_text,
                (
                    "Entra ID",
                    "directory boundary",
                    "authentication context",
                    "Direct Entra ID actioning",
                ),
            ),
        )

        for family_name, text, terms in family_specific_terms:
            with self.subTest(family=family_name):
                for term in shared_terms + terms:
                    self.assertIn(term, text)

    def test_phase14_onboarding_packages_define_reviewed_ownership_and_prerequisites(
        self,
    ) -> None:
        github_text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "github-audit"
            / "onboarding-package.md"
        ).read_text(encoding="utf-8")
        microsoft_text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "microsoft-365-audit"
            / "onboarding-package.md"
        ).read_text(encoding="utf-8")
        entra_text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "entra-id"
            / "onboarding-package.md"
        ).read_text(encoding="utf-8")

        shared_terms = (
            "Parser ownership remains with IT Operations, Information Systems Department.",
            "Representative raw payload references are stored in `control-plane/tests/fixtures/wazuh/`.",
            "The reviewed fixture is sufficient for future parser and mapping validation without claiming that live source onboarding is approved.",
        )
        family_specific_terms = (
            (
                "github-audit",
                github_text,
                (
                    "Readiness state: `detection-ready`",
                    "Reviewed parser evidence source",
                    "This package does not approve live GitHub API actioning, response automation, source-side credentials, or non-audit GitHub telemetry families.",
                    "GitHub repository privilege change",
                    "GitHub audit",
                ),
            ),
            (
                "microsoft-365-audit",
                microsoft_text,
                (
                    "Readiness state: `schema-reviewed`",
                    "Versioned parser changes remain future implementation work.",
                    "This package does not approve direct Microsoft 365 actioning, non-audit Microsoft 365 telemetry families, source-side credentials, or runtime automation.",
                    "Microsoft 365 mailbox permission change",
                    "Microsoft 365 audit",
                ),
            ),
            (
                "entra-id",
                entra_text,
                (
                    "Readiness state: `schema-reviewed`",
                    "Versioned parser changes remain future implementation work.",
                    "This package does not approve direct Entra ID actioning, non-audit Entra ID telemetry families, source-side credentials, or runtime automation.",
                    "Entra ID privileged role assignment",
                    "Entra ID",
                ),
            ),
        )

        for family_name, text, terms in family_specific_terms:
            with self.subTest(family=family_name):
                for term in shared_terms + terms:
                    self.assertIn(term, text)

    def test_github_audit_detection_ready_package_requires_reviewed_evidence(
        self,
    ) -> None:
        onboarding_text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "github-audit"
            / "onboarding-package.md"
        ).read_text(encoding="utf-8")
        runbook_text = (
            REPO_ROOT
            / "docs"
            / "source-families"
            / "github-audit"
            / "analyst-triage-runbook.md"
        ).read_text(encoding="utf-8")

        required_onboarding_terms = (
            "Readiness state: `detection-ready`",
            "Reviewed detection-ready scope",
            "Parser and Version Evidence",
            "Reviewed parser evidence source",
            "Field Coverage Verification",
            "Provenance Evidence",
            "Detector-Use Approval and Limits",
            "Future detection content may reference GitHub audit only for repository and organization privilege, access, and workflow-administration review signals that preserve accountable source identity, actor identity, target identity, repository or organization context, privilege-change or workflow-administration metadata, timestamp quality, and Wazuh provenance.",
            "Detector activation still requires separate rule review, rollout review, and Wazuh rule lifecycle validation.",
            "This package does not approve live GitHub API actioning, response automation, source-side credentials, GitHub-owned case authority, direct vendor workflow truth, non-audit GitHub telemetry families, or detector activation without separate detector review.",
        )
        required_runbook_terms = (
            "Detector-use handling",
            "GitHub audit may support detector review only within the approved detection-ready scope in the onboarding package.",
            "Analysts must treat GitHub audit as source evidence for AegisOps review, not as GitHub-owned workflow truth or direct action authority.",
            "Family-specific false-positive review",
            "Provenance handling",
            "If accountable source identity, actor identity, target identity, repository or organization context, timestamp quality, parser evidence, or Wazuh provenance is missing or malformed, the analyst keeps the item out of detector-ready handling until the prerequisite is repaired or a documented exception path applies.",
        )

        for term in required_onboarding_terms:
            self.assertIn(term, onboarding_text)
        for term in required_runbook_terms:
            self.assertIn(term, runbook_text)


if __name__ == "__main__":
    unittest.main()
