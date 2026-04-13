from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase21ProductionLikeHardeningBoundaryValidationTests(unittest.TestCase):
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

    def test_phase21_validation_artifacts_cross_reference_governing_contracts(self) -> None:
        design_doc = self._design_doc()
        validation_doc = self._validation_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 21 design doc at {design_doc}")
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 21 validation doc at {validation_doc}",
        )

        design_text = design_doc.read_text(encoding="utf-8")
        validation_text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md",
            "docs/auth-baseline.md",
            "docs/network-exposure-and-access-path-policy.md",
            "docs/runbook.md",
            "docs/automation-substrate-contract.md",
            "docs/response-action-safety-model.md",
            "docs/source-onboarding-contract.md",
            "docs/phase-14-identity-rich-source-family-design.md",
            "docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md",
            "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md",
            "docs/architecture.md",
        ):
            self.assertIn(term, design_text)
            self.assertIn(term, validation_text)

        for term in (
            "Entra ID is the first reviewed second live source to onboard",
            "topology growth remains conditional only",
            "does not reopen broader action catalogs",
            "direct vendor-local actioning",
        ):
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
