from __future__ import annotations

import pathlib
import unittest


def _doc_path(relative_path: str) -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2] / relative_path


class Phase61SourceCatalogContractTests(unittest.TestCase):
    catalog_doc = _doc_path("docs/phase-61-minimum-source-catalog-contract.md")
    validation_doc = _doc_path("docs/phase-61-1-source-catalog-contract-validation.md")
    github_pkg = _doc_path("docs/source-families/github-audit/onboarding-package.md")
    entra_pkg = _doc_path("docs/source-families/entra-id/onboarding-package.md")
    m365_pkg = _doc_path("docs/source-families/microsoft-365-audit/onboarding-package.md")
    windows_pkg = _doc_path("docs/source-families/windows-security-and-endpoint/onboarding-package.md")

    def test_phase61_catalog_document_exists(self) -> None:
        for path in (
            self.catalog_doc,
            self.validation_doc,
            self.github_pkg,
            self.entra_pkg,
            self.m365_pkg,
            self.windows_pkg,
        ):
            self.assertTrue(path.exists(), f"expected {path} to exist")

    def test_phase61_catalog_lists_minimum_families_and_key_fields(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")

        required_family_headers = (
            "`wazuh_detection` (Wazuh manager and agent origin telemetry)",
            "`github_audit`",
            "`microsoft_365_audit`",
            "`entra_id`",
            "`windows_security_endpoint`",
        )

        required_terms = (
            "Reviewed owner",
            "Authority posture",
            "Evidence linkage",
            "Source-health requirements",
            "Explicit limitations",
        )

        for family_header in required_family_headers:
            self.assertIn(family_header, catalog_text)

        for term in required_terms:
            self.assertIn(term, catalog_text)

    def test_phase61_catalog_boundedness_rules_are_explicit(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")

        bounded_terms = (
            "This catalog must stay bounded to the five families above.",
            "The catalog must reject claims that broaden into marketplace",
            "Source-native alerts, statuses, and parser fields remain subordinate",
            "No broad endpoint market",
            "No raw Wazuh replacement",
        )
        for term in bounded_terms:
            self.assertIn(term, catalog_text)

    def test_phase61_catalog_rejects_out_of_scope_expansion(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")

        forbidden_terms = (
            "Phase 62",
            "Phase 66",
            "Beta",
            "RC",
            "GA",
            "commercial replacement readiness",
            "multi-site",
            "raw SIEM replacement",
            "broad SIEM source marketplace",
            "broad source-marketplace",
            "marketplace",
        )
        for term in forbidden_terms:
            self.assertIn(
                term,
                catalog_text,
                msg=(
                    f"bounded catalog must explicitly reject out-of-scope claim: {term}"
                ),
            )

    def test_phase61_validation_file_states_pass(self) -> None:
        validation_text = self.validation_doc.read_text(encoding="utf-8")

        required_headings = (
            "# Phase 61.1 Source Catalog Contract Validation",
            "- Validation status: PASS",
            "## Required artifacts",
            "## Outcome",
            "## Cross-link Review",
            "## Deviations",
            "- No deviations.",
            "Verification commands:",
            "Run `bash scripts/verify-phase-61-1-source-catalog-contract.sh`.",
        )
        for heading in required_headings:
            self.assertIn(heading, validation_text)

    def test_phase61_out_of_scope_boundaries_are_explicit(self) -> None:
        catalog_text = self.catalog_doc.read_text(encoding="utf-8")

        out_of_scope_terms = (
            "Phase 62 automation breadth",
            "Phase 66 RC proof",
            "Beta/RC/GA",
            "Source profile runtime onboarding",
            "live source enrollment",
            "live credentials",
        )
        for term in out_of_scope_terms:
            self.assertIn(term, catalog_text)

        validation_text = self.validation_doc.read_text(encoding="utf-8")
        for term in (
            "No Phase 62 automation breadth",
            "no multi-site source management",
            "no Phase 66 RC proof",
            "no Beta/RC/GA claims",
            "no commercial replacement readiness claim",
        ):
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
