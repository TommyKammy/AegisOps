from __future__ import annotations

import ast
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

    @staticmethod
    def _defined_test_names(*relative_paths: str) -> set[str]:
        defined_names: set[str] = set()
        for relative_path in relative_paths:
            source = ServiceBoundaryRefactorRegressionValidationTests._read(relative_path)
            tree = ast.parse(source, filename=relative_path)
            defined_names.update(
                node.name
                for node in ast.walk(tree)
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
            )
        return defined_names

    def test_phase19_regression_validation_keeps_live_slice_gating_and_service_surface_coverage(
        self,
    ) -> None:
        workflow_and_cli_tests = self._defined_test_names(
            "control-plane/tests/test_phase19_operator_workflow_validation.py",
            "control-plane/tests/test_cli_inspection.py",
        )
        advisory_tests = self._defined_test_names(
            "control-plane/tests/test_service_persistence_assistant_advisory.py"
        )

        for term in (
            "test_reviewed_runtime_path_covers_approved_operator_workflow",
            "test_reviewed_runtime_path_exposes_live_entra_id_case_through_existing_operator_surface",
            "test_reviewed_runtime_path_fails_closed_for_out_of_scope_case_reads",
            "test_long_running_runtime_surface_exposes_analyst_queue_alert_detail_and_case_detail_http_views",
            "test_long_running_runtime_surface_exposes_cited_advisory_review_routes",
            "test_long_running_runtime_surface_rejects_case_scoped_out_of_scope_advisory_reads",
            "test_long_running_runtime_surface_rejects_case_family_out_of_scope_advisory_reads",
            "test_long_running_runtime_surface_rejects_case_scoped_advisory_reads_without_linked_case",
        ):
            self.assertIn(term, workflow_and_cli_tests)

        for term in (
            "test_service_delegates_assistant_context_and_advisory_rendering_to_assembler",
            "test_service_routes_reviewed_slice_checks_through_policy_module",
            "test_service_rejects_case_scoped_advisory_reads_without_linked_case",
        ):
            self.assertIn(term, advisory_tests)

    def test_phase20_regression_validation_keeps_action_path_binding_and_identity_coverage(
        self,
    ) -> None:
        action_tests = self._defined_test_names(
            "control-plane/tests/test_service_persistence_action_reconciliation.py",
            "control-plane/tests/test_service_persistence_action_reconciliation_create_tracking_ticket.py",
            "control-plane/tests/test_service_persistence_action_reconciliation_delegation.py",
            "control-plane/tests/test_service_persistence_action_reconciliation_reconciliation.py",
            "control-plane/tests/test_service_persistence_action_reconciliation_review_surfaces.py",
            "control-plane/tests/test_service_persistence_action_reconciliation_reviewed_requests.py",
        )
        boundary_and_cli_tests = self._defined_test_names(
            "control-plane/tests/test_execution_coordinator_boundary.py",
            "control-plane/tests/test_cli_inspection.py",
        )

        for term in (
            "test_service_executes_phase20_first_live_action_end_to_end_from_reviewed_recommendation",
            "test_service_phase20_first_live_action_fail_closes_on_downstream_execution_surface_mismatch",
            "test_service_delegates_approved_low_risk_action_through_shuffle_adapter",
            "test_service_rechecks_shuffle_approval_inside_transaction",
            "test_service_rejects_shuffle_delegation_when_payload_binding_drifts",
            "test_service_rejects_shuffle_delegation_when_expiry_window_drifts_after_approval",
            "test_service_rejects_shuffle_delegation_when_target_scope_drifts",
            "test_service_reconciles_shuffle_run_back_into_authoritative_action_execution",
            "test_service_reconciliation_mismatch_does_not_mutate_authoritative_execution",
            "test_service_reconciliation_fail_closes_when_downstream_run_identity_drifts",
            "test_service_phase20_reconciliation_rejects_downstream_evidence_missing_binding_identifiers",
            "test_service_keeps_requester_identity_inside_reviewed_action_request_deduplication",
            "test_service_rechecks_reviewed_action_request_context_inside_transaction",
        ):
            self.assertIn(term, action_tests)

        for term in (
            "test_service_initializes_dedicated_execution_coordinator",
            "test_service_delegates_reviewed_action_request_creation_to_execution_coordinator",
            "test_service_delegates_shuffle_and_isolated_executor_flows_to_execution_coordinator",
            "test_service_delegates_reconciliation_flow_to_execution_coordinator",
            "test_cli_creates_reviewed_action_request_from_recommendation_context",
        ):
            self.assertIn(term, boundary_and_cli_tests)

    def test_phase21_regression_validation_keeps_readiness_restore_and_fail_closed_runtime_coverage(
        self,
    ) -> None:
        restore_tests = self._defined_test_names(
            "control-plane/tests/test_service_persistence_restore_readiness.py"
        )
        auth_end_to_end_and_cli_tests = self._defined_test_names(
            "control-plane/tests/test_phase21_runtime_auth_validation.py",
            "control-plane/tests/test_phase21_end_to_end_validation.py",
            "control-plane/tests/test_cli_inspection.py",
        )

        for term in (
            "test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore",
            "test_service_phase21_restore_fails_closed_on_duplicate_alert_identifiers",
            "test_service_phase21_restore_fails_closed_on_duplicate_execution_run_ids",
            "test_service_phase21_restore_fails_closed_when_approval_record_is_missing",
            "test_service_phase21_restore_rejects_action_execution_surface_binding_mismatch",
            "test_service_phase21_restore_rejects_action_execution_expiry_binding_mismatch",
            "test_service_phase21_restore_rejects_action_execution_delegation_after_approval_expiry",
            "test_service_phase21_restore_rejects_reconciliation_run_binding_mismatch",
        ):
            self.assertIn(term, restore_tests)

        for term in (
            "test_operational_runtime_surfaces_are_extracted_into_dedicated_collaborators",
            "test_protected_surface_runtime_fails_closed_without_trusted_proxy_bindings",
            "test_protected_surface_request_rejects_missing_authenticated_identity_header",
            "test_break_glass_contract_is_disabled_until_token_is_bound",
            "test_phase21_end_to_end_auth_boundaries_fail_closed_and_emit_observability",
            "test_phase21_end_to_end_restore_and_readiness_preserve_phase20_live_path",
            "test_long_running_runtime_surface_exposes_operator_readiness_diagnostics_http_view",
            "test_backup_and_restore_drill_commands_render_recovery_payloads",
        ):
            self.assertIn(term, auth_end_to_end_and_cli_tests)

    def test_phase22_regression_validation_keeps_operator_trust_runtime_coverage(
        self,
    ) -> None:
        phase22_end_to_end_tests = self._defined_test_names(
            "control-plane/tests/test_phase22_end_to_end_validation.py"
        )
        phase19_to_phase21_validation_tests = self._defined_test_names(
            "control-plane/tests/test_phase19_operator_workflow_validation.py",
            "control-plane/tests/test_phase20_low_risk_action_validation.py",
            "control-plane/tests/test_phase21_end_to_end_validation.py",
        )

        for term in (
            "test_phase22_end_to_end_keeps_review_states_and_visibility_explicit",
            "test_phase22_end_to_end_keeps_success_claims_non_authoritative_until_reconciliation_matches",
        ):
            self.assertIn(term, phase22_end_to_end_tests)

        for term in (
            "test_reviewed_runtime_path_covers_approved_operator_workflow",
            "test_reviewed_runtime_path_covers_phase20_low_risk_action_boundary",
            "test_phase21_end_to_end_restore_and_readiness_preserve_phase20_live_path",
        ):
            self.assertIn(term, phase19_to_phase21_validation_tests)

    def test_phase26_regression_validation_keeps_link_first_and_soft_write_ticket_coverage(
        self,
    ) -> None:
        phase26_end_to_end_tests = self._defined_test_names(
            "control-plane/tests/test_phase26_end_to_end_validation.py"
        )
        phase26_supporting_tests = self._defined_test_names(
            "control-plane/tests/test_service_persistence_ingest_case_lifecycle.py",
            "control-plane/tests/test_service_persistence_action_reconciliation_create_tracking_ticket.py",
            "control-plane/tests/test_service_persistence_action_reconciliation_reconciliation.py",
            "control-plane/tests/test_cli_inspection.py",
        )

        for term in (
            "test_phase26_end_to_end_surfaces_link_first_ticket_reference_without_authority_drift",
            "test_phase26_end_to_end_surfaces_create_tracking_ticket_created_outcome",
            "test_phase26_end_to_end_fail_closes_missing_receipt_before_user_facing_success",
            "test_phase26_end_to_end_surfaces_duplicate_create_attempt_as_mismatch",
            "test_phase26_end_to_end_surfaces_create_tracking_ticket_identifier_mismatch",
            "test_phase26_end_to_end_surfaces_create_tracking_ticket_timeout",
            "test_phase26_end_to_end_surfaces_create_tracking_ticket_manual_fallback",
        ):
            self.assertIn(term, phase26_end_to_end_tests)

        for term in (
            "test_service_detail_surfaces_link_only_external_ticket_reference_on_alert_and_case",
            "test_service_detail_keeps_mismatched_external_ticket_reference_explicit",
            "test_service_fail_closes_when_create_tracking_ticket_receipt_omits_external_receipt_id",
            "test_service_fail_closes_when_create_tracking_ticket_reconciliation_receipt_drifts",
            "test_service_delegates_approved_create_tracking_ticket_through_shuffle",
            "test_cli_inspect_case_detail_surfaces_create_tracking_ticket_outcome",
            "test_cli_inspect_case_detail_surfaces_create_tracking_ticket_mismatch",
            "test_cli_inspect_case_detail_surfaces_create_tracking_ticket_timeout",
            "test_cli_inspect_case_detail_surfaces_create_tracking_ticket_manual_fallback",
        ):
            self.assertIn(term, phase26_supporting_tests)


if __name__ == "__main__":
    unittest.main()
