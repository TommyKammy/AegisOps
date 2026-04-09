from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase15IdentityGroundedAnalystAssistantBoundaryDocsTests(unittest.TestCase):
    def test_phase15_boundary_design_doc_exists(self) -> None:
        design_doc = REPO_ROOT / "docs" / "phase-15-identity-grounded-analyst-assistant-boundary.md"

        self.assertTrue(design_doc.exists(), f"expected Phase 15 design doc at {design_doc}")

    def test_phase15_operating_guidance_doc_exists(self) -> None:
        guidance_doc = (
            REPO_ROOT
            / "docs"
            / "phase-15-identity-grounded-analyst-assistant-operating-guidance.md"
        )

        self.assertTrue(
            guidance_doc.exists(),
            f"expected Phase 15 operating guidance doc at {guidance_doc}",
        )

    def test_phase15_operating_guidance_doc_defines_operator_grounding_and_uncertainty_rules(
        self,
    ) -> None:
        text = (
            REPO_ROOT
            / "docs"
            / "phase-15-identity-grounded-analyst-assistant-operating-guidance.md"
        ).read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 15 Identity-Grounded Analyst-Assistant Operating Guidance",
            "reviewed control-plane records",
            "linked evidence",
            "Safe Query Gateway policy",
            "preserve uncertainty",
            "alias-style",
            "secondary OpenSearch enrichment",
            "advisory-only",
        ):
            self.assertIn(term, text)

    def test_phase15_validation_doc_exists(self) -> None:
        validation_doc = (
            REPO_ROOT
            / "docs"
            / "phase-15-identity-grounded-analyst-assistant-boundary-validation.md"
        )

        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 15 validation doc at {validation_doc}",
        )

    def test_phase15_boundary_design_doc_defines_the_reviewed_grounding_inputs(self) -> None:
        text = (
            REPO_ROOT
            / "docs"
            / "phase-15-identity-grounded-analyst-assistant-boundary.md"
        ).read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 15 Identity-Grounded Analyst-Assistant Boundary",
            "This document defines the approved advisory-only analyst-assistant boundary",
            "first-class grounding inputs",
            "Alert",
            "Case",
            "Evidence",
            "Recommendation",
            "Reconciliation",
            "linked evidence",
            "reviewed context",
            "operator-facing companion guidance",
        ):
            self.assertIn(term, text)

    def test_phase15_boundary_design_doc_defines_the_optional_opensearch_extension_boundary(self) -> None:
        text = (
            REPO_ROOT
            / "docs"
            / "phase-15-identity-grounded-analyst-assistant-boundary.md"
        ).read_text(encoding="utf-8")

        for term in (
            "OpenSearch may contribute optional analytics or evidence lookups",
            "secondary analyst-assistant extension",
            "safe fallback",
            "does not own alert, case, recommendation, approval, action, or reconciliation truth",
        ):
            self.assertIn(term, text)

    def test_phase15_boundary_design_doc_fails_closed_on_ambiguous_identity_metadata(self) -> None:
        text = (
            REPO_ROOT
            / "docs"
            / "phase-15-identity-grounded-analyst-assistant-boundary.md"
        ).read_text(encoding="utf-8")

        for term in (
            "alias-style",
            "stable identifier",
            "must fail closed",
            "must not assert equality",
            "identity ambiguity",
        ):
            self.assertIn(term, text)

    def test_phase15_boundary_design_doc_defines_safe_query_citation_and_prompt_injection_guardrails(
        self,
    ) -> None:
        text = (
            REPO_ROOT
            / "docs"
            / "phase-15-identity-grounded-analyst-assistant-boundary.md"
        ).read_text(encoding="utf-8")

        for term in (
            "Safe Query Gateway policy",
            "free-form search",
            "query expansion",
            "Prompt content, analyst notes, and optional-extension instructions are untrusted input.",
            "acquire approval or execution authority",
            "citation completeness",
            "stay advisory-only and unresolved",
            "stable identifiers",
            "Optional extension inputs, including OpenSearch analytics",
        ):
            self.assertIn(term, text)

    def test_phase15_validation_doc_cross_links_the_boundary_set(self) -> None:
        text = (
            REPO_ROOT
            / "docs"
            / "phase-15-identity-grounded-analyst-assistant-boundary-validation.md"
        ).read_text(encoding="utf-8")

        for term in (
            "Phase 15 Identity-Grounded Analyst-Assistant Boundary Validation",
            "phase-15-identity-grounded-analyst-assistant-operating-guidance.md",
            "docs/phase-15-identity-grounded-analyst-assistant-boundary.md",
            "docs/control-plane-state-model.md",
            "docs/control-plane-runtime-service-boundary.md",
            "docs/asset-identity-privilege-context-baseline.md",
            "docs/phase-14-identity-rich-source-family-design.md",
            "docs/phase-13-guarded-automation-ci-validation.md",
            "docs/safe-query-gateway-and-tool-policy.md",
            "docs/phase-7-ai-hunt-design-validation.md",
            "advisory-only",
            "prompt-injection resistance",
            "citation completeness",
            "identity ambiguity handling",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
