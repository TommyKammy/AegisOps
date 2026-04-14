from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class ServiceBoundaryRefactorRegressionValidationTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected regression module at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase19_regression_validation_keeps_live_slice_gating_and_service_surface_coverage(
        self,
    ) -> None:
        workflow_text = self._read(
            "control-plane/tests/test_phase19_operator_workflow_validation.py"
        )
        cli_text = self._read("control-plane/tests/test_cli_inspection.py")
        advisory_text = self._read(
            "control-plane/tests/test_service_persistence_assistant_advisory.py"
        )

        for term in (
            "def test_reviewed_runtime_path_covers_approved_operator_workflow(",
            "def test_reviewed_runtime_path_exposes_live_entra_id_case_through_existing_operator_surface(",
            "def test_reviewed_runtime_path_fails_closed_for_out_of_scope_case_reads(",
            "def test_long_running_runtime_surface_exposes_analyst_queue_alert_detail_and_case_detail_http_views(",
            "def test_long_running_runtime_surface_exposes_cited_advisory_review_routes(",
            "def test_long_running_runtime_surface_rejects_case_scoped_out_of_scope_advisory_reads(",
            "def test_long_running_runtime_surface_rejects_case_family_out_of_scope_advisory_reads(",
            "def test_long_running_runtime_surface_rejects_case_scoped_advisory_reads_without_linked_case(",
        ):
            self.assertIn(term, workflow_text + cli_text)

        for term in (
            "def test_service_delegates_assistant_context_and_advisory_rendering_to_assembler(",
            "def test_service_routes_reviewed_slice_checks_through_policy_module(",
            "def test_service_rejects_case_scoped_advisory_reads_without_linked_case(",
        ):
            self.assertIn(term, advisory_text)

    def test_phase20_regression_validation_keeps_action_path_binding_and_identity_coverage(
        self,
    ) -> None:
        action_text = self._read(
            "control-plane/tests/test_service_persistence_action_reconciliation.py"
        )
        boundary_text = self._read(
            "control-plane/tests/test_execution_coordinator_boundary.py"
        )
        cli_text = self._read("control-plane/tests/test_cli_inspection.py")

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
            "def test_service_keeps_requester_identity_inside_reviewed_action_request_deduplication(",
            "def test_service_rechecks_reviewed_action_request_context_inside_transaction(",
        ):
            self.assertIn(term, action_text)

        for term in (
            "def test_service_initializes_dedicated_execution_coordinator(",
            "def test_service_delegates_reviewed_action_request_creation_to_execution_coordinator(",
            "def test_service_delegates_shuffle_and_isolated_executor_flows_to_execution_coordinator(",
            "def test_service_delegates_reconciliation_flow_to_execution_coordinator(",
            "def test_cli_creates_reviewed_action_request_from_recommendation_context(",
        ):
            self.assertIn(term, boundary_text + cli_text)

    def test_phase21_regression_validation_keeps_readiness_restore_and_fail_closed_runtime_coverage(
        self,
    ) -> None:
        restore_text = self._read(
            "control-plane/tests/test_service_persistence_restore_readiness.py"
        )
        auth_text = self._read(
            "control-plane/tests/test_phase21_runtime_auth_validation.py"
        )
        end_to_end_text = self._read(
            "control-plane/tests/test_phase21_end_to_end_validation.py"
        )
        cli_text = self._read("control-plane/tests/test_cli_inspection.py")

        for term in (
            "def test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore(",
            "def test_service_phase21_restore_fails_closed_on_duplicate_alert_identifiers(",
            "def test_service_phase21_restore_fails_closed_on_duplicate_execution_run_ids(",
            "def test_service_phase21_restore_fails_closed_when_approval_record_is_missing(",
            "def test_service_phase21_restore_rejects_action_execution_surface_binding_mismatch(",
            "def test_service_phase21_restore_rejects_action_execution_expiry_binding_mismatch(",
            "def test_service_phase21_restore_rejects_action_execution_delegation_after_approval_expiry(",
            "def test_service_phase21_restore_rejects_reconciliation_run_binding_mismatch(",
        ):
            self.assertIn(term, restore_text)

        for term in (
            "def test_operational_runtime_surfaces_are_extracted_into_dedicated_collaborators(",
            "def test_protected_surface_runtime_fails_closed_without_trusted_proxy_bindings(",
            "def test_protected_surface_request_rejects_missing_authenticated_identity_header(",
            "def test_break_glass_contract_is_disabled_until_token_is_bound(",
            "def test_phase21_end_to_end_auth_boundaries_fail_closed_and_emit_observability(",
            "def test_phase21_end_to_end_restore_and_readiness_preserve_phase20_live_path(",
            "def test_long_running_runtime_surface_exposes_operator_readiness_diagnostics_http_view(",
            "def test_backup_and_restore_drill_commands_render_recovery_payloads(",
        ):
            self.assertIn(term, auth_text + end_to_end_text + cli_text)


if __name__ == "__main__":
    unittest.main()
