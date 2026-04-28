from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase27Day2HardeningValidationTests(unittest.TestCase):
    @staticmethod
    def _validation_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-27-day-2-hardening-validation.md"

    def test_phase27_validation_doc_exists_and_separates_dedicated_and_foundational_evidence(
        self,
    ) -> None:
        validation_doc = self._validation_doc()
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 27 validation doc at {validation_doc}",
        )

        validation_text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "Validation status: PASS",
            "docs/runbook.md",
            "docs/auth-baseline.md",
            "docs/smb-footprint-and-deployment-profile-baseline.md",
            "control-plane/tests/test_phase27_day2_runtime_contract.py",
            "control-plane/tests/test_service_persistence_restore_readiness.py",
            "Evidence Matrix",
            "Phase 27-specific contract coverage",
            "Foundational coverage reused by Phase 27",
            "control-plane/tests/test_runtime_secret_boundary.py",
            "test_phase27_restore_runtime_contract_fails_closed_without_post_restore_bindings",
            "test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state",
            "test_phase27_identity_contract_fails_closed_for_missing_or_unreviewed_provider_boundary",
            "test_phase27_idp_outage_blocks_operator_authority_and_workflow_progression",
            "IdP outage fail-closed workflow authority",
            "test_phase27_secret_contract_requires_fresh_read_and_blocks_backend_outage",
            "Rollback remains a reviewed operational contract and capacity guardrail, not a dedicated runtime-enforced Phase 27 contract in the current path.",
            "None at the runtime-enforcement layer. Phase 27 currently relies on the reviewed runbook backup, restore, and rollback contract as the operator-facing rollback proof while dedicated runtime rollback enforcement remains out of scope.",
            "bash scripts/verify-phase-27-day-2-hardening-validation.sh",
            "python3 -m unittest control-plane.tests.test_phase27_day2_hardening_validation control-plane.tests.test_phase27_day2_runtime_contract",
        ):
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
