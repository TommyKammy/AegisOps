from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase20LowRiskActionValidationTests(unittest.TestCase):
    @staticmethod
    def _service_test_doc() -> pathlib.Path:
        return REPO_ROOT / "control-plane" / "tests" / "test_service_persistence.py"

    def test_reviewed_runtime_path_covers_phase20_low_risk_action_boundary(self) -> None:
        service_test_doc = self._service_test_doc()
        self.assertTrue(
            service_test_doc.exists(),
            f"expected service persistence tests at {service_test_doc}",
        )
        text = service_test_doc.read_text(encoding="utf-8")

        for term in (
            "def test_service_executes_phase20_first_live_action_end_to_end_from_reviewed_recommendation(",
            "def test_service_phase20_first_live_action_fail_closes_on_downstream_execution_surface_mismatch(",
            "def test_service_delegates_approved_low_risk_action_through_shuffle_adapter(",
            "def test_service_rechecks_shuffle_approval_inside_transaction(",
            "def test_service_rejects_shuffle_delegation_when_payload_binding_drifts(",
            "def test_service_rejects_shuffle_delegation_when_expiry_window_drifts_after_approval(",
            "def test_service_rejects_shuffle_delegation_when_target_scope_drifts(",
            "def test_service_reconciles_shuffle_run_back_into_authoritative_action_execution(",
            "def test_service_reconciliation_mismatch_does_not_mutate_authoritative_execution(",
            "def test_service_reconciliation_fail_closes_when_downstream_run_identity_drifts(",
            "def test_service_phase20_reconciliation_rejects_downstream_evidence_missing_binding_identifiers(",
            '"action_type": "notify_identity_owner"',
            '"execution_surface_id": "shuffle"',
            "approved payload binding does not match",
            "approved expiry window does not match action request expiry",
            "create_reviewed_action_request_from_advisory(",
            "delegate_approved_action_to_shuffle(",
            "reconcile_action_execution(",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
