from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase21ProductionLikeHardeningBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-21-production-like-hardening-boundary-and-sequence.md"

    @staticmethod
    def _validation_doc() -> pathlib.Path:
        return (
            REPO_ROOT
            / "docs"
            / "phase-21-production-like-hardening-boundary-and-sequence-validation.md"
        )

    def test_phase21_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 21 design doc at {design_doc}")

    def test_phase21_design_doc_defines_boundary_sequence_and_non_expansion_rules(self) -> None:
        design_doc = self._design_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 21 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "AegisOps Phase 21 Production-Like Hardening Boundary and Sequence",
            "Reviewed Phase 21 Hardening Boundary",
            "Auth, Service Accounts, and Secret Scope",
            "Reverse-Proxy, Admin Bootstrap, and Break-Glass Access",
            "Restore and Observability Boundary",
            "Topology Growth Conditions",
            "Reviewed Second-Source Onboarding Target",
            "Fixed Implementation Sequence",
            "auth and secrets -> admin bootstrap and break-glass controls -> restore proof -> observability proof -> topology growth gate review -> Entra ID second-source onboarding",
            "The approved first reviewed second live source to onboard after the existing GitHub audit live slice is Entra ID.",
            "GitHub audit -> Entra ID -> Microsoft 365 audit",
            "grows from the current one-node operating shape toward two-node or broader deployment patterns",
            "The reviewed topology-growth gate is therefore a one-node-to-multi-node admission review rather than pre-approval for cluster rollout.",
            "The reviewed second-source onboarding boundary must reuse the existing control-plane contracts for payload admission, dedupe, restatement, evidence preservation, case linkage, and thin operator-surface visibility.",
            "Phase 21 does not approve a parallel intake, evidence, case, or operator model for the second source.",
            "Phase 21 preserves the completed Phase 20 first live low-risk action exactly as the current approved live path.",
            "broad multi-source breadth",
            "broad UI expansion",
            "medium-risk or high-risk live action growth",
            "notify_identity_owner",
        ):
            self.assertIn(term, text)

    def test_phase21_validation_doc_exists_and_records_alignment_caveat(self) -> None:
        validation_doc = self._validation_doc()
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 21 validation doc at {validation_doc}",
        )
        text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "Phase 21 Production-Like Hardening Boundary and Sequence Validation",
            "Validation status: FAIL",
            "production-like hardening around the completed Phase 20 live path",
            "auth and secrets -> admin bootstrap and break-glass controls -> restore proof -> observability proof -> topology growth gate review -> Entra ID second-source onboarding",
            "GitHub audit -> Entra ID -> Microsoft 365 audit",
            "control-plane/tests/test_phase21_end_to_end_validation.py",
            "Phase 21 end-to-end validation test keeps auth fail-closed behavior, restore readability, readiness diagnostics, second-source onboarding, and the completed Phase 20 live path under one focused runtime proof.",
            "Phase 16-21 Epic Roadmap.md",
            "Validation cannot pass until the requested `Phase 16-21 Epic Roadmap.md` comparison is completed from a reviewed local artifact.",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
