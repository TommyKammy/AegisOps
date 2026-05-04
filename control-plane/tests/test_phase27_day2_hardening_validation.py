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
            "control-plane/tests/test_service_restore_backup_codec.py",
            "control-plane/tests/test_service_restore_drill_transactions.py",
            "control-plane/tests/test_service_readiness_projection.py",
            "control-plane/tests/test_service_restore_validation.py",
            "Evidence Matrix",
            "Phase 27-specific contract coverage",
            "Foundational coverage reused by Phase 27",
            "control-plane/tests/test_runtime_secret_boundary.py",
            "test_phase27_restore_runtime_contract_fails_closed_without_post_restore_bindings",
            "test_phase27_restore_reconciliation_truth_integrity_keeps_mismatch_reviewable",
            "Restore reconciliation truth integrity",
            "restored subordinate receipts and external-ticket evidence cannot auto-close cases or auto-advance action execution state",
            "test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state",
            "test_phase27_degraded_source_health_visibility_does_not_advance_workflow_authority",
            "Source-health degraded reviewed-surface visibility",
            "degraded `github_audit` source-health remains visible on the reviewed readiness inspection surface",
            "leaves alert, case, approval, action request, execution, and reconciliation lifecycle records unchanged",
            "test_phase27_identity_contract_fails_closed_for_missing_or_unreviewed_provider_boundary",
            "test_phase27_idp_outage_blocks_operator_authority_and_workflow_progression",
            "IdP outage fail-closed workflow authority",
            "test_phase27_upgrade_rollback_uncertainty_freezes_authority_sensitive_progression",
            "Upgrade/rollback authority freeze",
            "freezes approval, execution, reconciliation, and case lifecycle progression during upgrade or rollback uncertainty",
            "readiness remains failing closed and operator-visible",
            "test_phase27_secret_contract_requires_fresh_read_and_blocks_backend_outage",
            "test_phase27_secret_backend_outage_rejects_plaintext_fallback_and_blocks_workflow_progression",
            "test_phase27_secret_rotation_interruption_rejects_mixed_or_partial_credential_state",
            "interrupted Wazuh secret rotation rejects mixed direct/OpenBao sources, blocks partial companion-secret reloads, keeps readiness failing closed, and leaves authoritative workflow records unchanged",
            "interrupted rotation, stale or mixed credential sources, backend outage, plaintext fallback, local file fallback, and protected workflow progression",
            "Upgrade and rollback completion remain reviewed operational contracts and capacity guardrails",
            "subordinate receipts, tickets, assistant output, browser state, or optional evidence can advance workflow truth",
            "bash scripts/verify-phase-27-day-2-hardening-validation.sh",
            "python3 -m unittest control-plane.tests.test_phase27_day2_hardening_validation control-plane.tests.test_phase27_day2_runtime_contract",
        ):
            self.assertIn(term, validation_text)


if __name__ == "__main__":
    unittest.main()
