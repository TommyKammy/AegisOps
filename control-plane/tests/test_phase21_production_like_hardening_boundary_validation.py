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
        roadmap_doc = REPO_ROOT / "docs" / "Phase 16-21 Epic Roadmap.md"
        end_to_end_test = (
            REPO_ROOT / "control-plane" / "tests" / "test_phase21_end_to_end_validation.py"
        )

        self.assertTrue(
            end_to_end_test.exists(),
            f"expected Phase 21 end-to-end validation tests at {end_to_end_test}",
        )

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
            "docs/wazuh-alert-ingest-contract.md",
            "docs/control-plane-state-model.md",
            "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md",
            "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md",
            "docs/architecture.md",
        ):
            self.assertIn(term, design_text)
            self.assertIn(term, validation_text)

        self.assertIn(
            "control-plane/tests/test_phase21_end_to_end_validation.py",
            validation_text,
        )

        validation_terms = [
            "Entra ID is the first reviewed second live source to onboard",
            "one-node-to-multi-node admission review",
            "reuses the existing payload-admission, dedupe, restatement, evidence-preservation, case-linkage, and thin-operator-surface contracts",
            "does not reopen broader action catalogs",
            "direct vendor-local actioning",
        ]

        if roadmap_doc.exists():
            validation_terms.extend(
                (
                    "Validation status: PASS",
                    "Confirmed comparison against `Phase 16-21 Epic Roadmap.md` completed using `docs/Phase 16-21 Epic Roadmap.md` as the reviewed roadmap baseline.",
                )
            )
        else:
            validation_terms.extend(
                (
                    "Validation status: FAIL",
                    "Validation cannot pass until the requested `Phase 16-21 Epic Roadmap.md` comparison is completed from a reviewed local artifact.",
                )
            )

        for term in validation_terms:
            self.assertIn(term, validation_text)

        for term in (
            "python3 -m unittest control-plane.tests.test_phase21_end_to_end_validation control-plane.tests.test_phase21_production_like_hardening_boundary_docs control-plane.tests.test_phase21_production_like_hardening_boundary_validation",
            "Phase 21 end-to-end validation test keeps auth fail-closed behavior, restore readability, readiness diagnostics, second-source onboarding, and the completed Phase 20 live path under one focused runtime proof.",
        ):
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
