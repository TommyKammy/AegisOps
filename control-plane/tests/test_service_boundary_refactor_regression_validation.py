from __future__ import annotations

import ast
import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class ServiceBoundaryRefactorRegressionValidationTests(unittest.TestCase):
    @staticmethod
    def _path(relative_path: str) -> pathlib.Path:
        path = REPO_ROOT / relative_path
        if path.exists():
            return path
        canonical_relative_path = relative_path.replace(
            "control-plane/aegisops_control_plane/",
            "control-plane/aegisops/control_plane/",
            1,
        )
        return REPO_ROOT / canonical_relative_path

    @staticmethod
    def _read(relative_path: str) -> str:
        path = ServiceBoundaryRefactorRegressionValidationTests._path(relative_path)
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
            "test_service_delegates_assistant_context_to_assembler_and_advisory_to_coordinator",
            "test_assistant_advisory_coordinator_exposes_no_authority_bearing_methods",
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
            "test_service_initializes_dedicated_action_lifecycle_write_coordinator",
            "test_service_routes_action_lifecycle_write_entrypoints_through_coordinator",
            "test_action_lifecycle_write_coordinator_preserves_internal_boundaries",
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

    def test_phase50_11_3_runtime_auth_and_structured_event_helpers_leave_service_facade(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        runtime_boundary_source = self._read(
            "control-plane/aegisops_control_plane/runtime/runtime_boundary.py"
        )
        structured_events_source = self._read(
            "control-plane/aegisops_control_plane/structured_events.py"
        )
        service_tree = ast.parse(service_source)
        runtime_boundary_tree = ast.parse(runtime_boundary_source)
        structured_events_tree = ast.parse(structured_events_source)
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        service_method_names = {
            node.name
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }
        service_module_function_names = {
            node.name for node in service_tree.body if isinstance(node, ast.FunctionDef)
        }
        runtime_boundary_methods = {
            node.name
            for node in next(
                node
                for node in runtime_boundary_tree.body
                if isinstance(node, ast.ClassDef)
                and node.name == "RuntimeBoundaryService"
            ).body
            if isinstance(node, ast.FunctionDef)
        }
        structured_event_functions = {
            node.name
            for node in structured_events_tree.body
            if isinstance(node, ast.FunctionDef)
        }

        self.assertTrue(
            {
                "validate_wazuh_ingest_runtime",
                "validate_protected_surface_runtime",
                "authenticate_protected_surface_request",
                "require_admin_bootstrap_token",
                "require_break_glass_token",
                "is_trusted_wazuh_ingest_peer",
                "is_trusted_protected_surface_peer",
                "is_trusted_peer_for_proxy_cidrs",
            }.issubset(runtime_boundary_methods)
        )
        self.assertTrue(
            {
                "_classify_network_identifier",
                "_count_identity_values",
                "sanitize_structured_event_fields",
            }.issubset(structured_event_functions)
        )
        self.assertFalse(
            {
                "_classify_network_identifier",
                "_count_identity_values",
                "_sanitize_structured_event_fields",
            }
            & service_module_function_names
        )

        emit_structured_event = service_method_names & {"_emit_structured_event"}
        self.assertEqual(emit_structured_event, {"_emit_structured_event"})

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

    def test_phase26_regression_validation_keeps_operator_inspection_boundary_coverage(
        self,
    ) -> None:
        boundary_tests = self._defined_test_names(
            "control-plane/tests/test_operator_inspection_boundary.py",
            "control-plane/tests/test_cli_inspection.py",
            "control-plane/tests/test_phase25_osquery_host_context_validation.py",
        )

        for term in (
            "test_service_initializes_dedicated_operator_inspection_read_surface",
            "test_service_delegates_operator_inspection_entrypoints_to_read_surface",
            "test_long_running_runtime_surface_exposes_analyst_queue_alert_detail_and_case_detail_http_views",
            "test_inspect_case_detail_exposes_cross_source_timeline_and_provenance_summary",
        ):
            self.assertIn(term, boundary_tests)

    def test_phase31_regression_validation_keeps_action_review_write_boundary_coverage(
        self,
    ) -> None:
        boundary_tests = self._defined_test_names(
            "control-plane/tests/test_action_review_write_boundary.py",
            "control-plane/tests/test_phase22_end_to_end_validation.py",
            "control-plane/tests/test_phase26_end_to_end_validation.py",
        )

        for term in (
            "test_service_initializes_dedicated_action_review_write_surface",
            "test_service_delegates_action_review_write_entrypoints_to_write_surface",
            "test_phase22_end_to_end_keeps_review_states_and_visibility_explicit",
            "test_phase26_end_to_end_surfaces_create_tracking_ticket_manual_fallback",
        ):
            self.assertIn(term, boundary_tests)

    def test_phase50_11_action_review_inspection_helpers_live_behind_boundary(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        projection_source = self._read(
            "control-plane/aegisops_control_plane/actions/review/action_review_projection.py"
        )
        inspection_boundary_source = self._read(
            "control-plane/aegisops_control_plane/actions/review/action_review_inspection.py"
        )
        service_tree = ast.parse(service_source)
        projection_tree = ast.parse(projection_source)
        inspection_boundary_tree = ast.parse(inspection_boundary_source)
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        inspection_boundary_class = next(
            node
            for node in inspection_boundary_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "ActionReviewInspectionBoundary"
        )
        service_methods = {
            node.name: node
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }
        inspection_boundary_methods = {
            node.name
            for node in inspection_boundary_class.body
            if isinstance(node, ast.FunctionDef)
        }
        projection_functions = {
            node.name for node in projection_tree.body if isinstance(node, ast.FunctionDef)
        }
        projection_import_exports = {
            alias.asname or alias.name
            for node in projection_tree.body
            if isinstance(node, ast.ImportFrom)
            for alias in node.names
        }
        moved_private_helper_names = {
            "_action_request_is_review_bound",
            "_action_review_approval_decision",
            "_action_review_approval_state",
            "_action_review_context_matches_lineage",
            "_action_review_escalation_visibility",
            "_action_review_execution",
            "_action_review_ingest_path_health",
            "_action_review_manual_fallback_visibility",
            "_action_review_overall_path_state",
            "_action_review_path_health_summary",
            "_action_review_persistence_path_health",
            "_action_review_provider_path_health",
            "_action_review_stage_snapshot",
            "_action_review_state",
            "_action_review_visibility_context",
            "_action_review_visibility_entry",
            "_action_review_visibility_update",
            "_latest_action_review_reconciliation",
            "_next_expected_action_for_review_state",
            "_replacement_action_request",
        }
        self.assertTrue(
            moved_private_helper_names.issubset(
                projection_functions | projection_import_exports
            )
        )

        for helper_name in moved_private_helper_names:
            self.assertNotIn(
                helper_name,
                service_methods,
                f"{helper_name} should be bypassed by collaborators instead of retained on the service facade",
            )

        self.assertLessEqual(
            len(
                [
                    name
                    for name in service_methods
                    if name.startswith("_action_review")
                    or name.startswith("_build_action_review")
                ]
            ),
            2,
        )
        self.assertTrue(
            {
                "build_record_index",
                "chains_for_scope",
                "build_chain_snapshot",
                "latest_reconciliation",
                "path_health",
                "runtime_visibility",
                "visibility_context",
                "timeline",
                "mismatch_inspection",
                "coordination_ticket_outcome",
                "downstream_binding",
            }.issubset(inspection_boundary_methods)
        )

    def test_phase50_9_4_internal_action_review_write_delegates_bypass_service_facade(
        self,
    ) -> None:
        write_surface_source = self._read(
            "control-plane/aegisops_control_plane/actions/review/action_review_write_surface.py"
        )
        readiness_operability_source = self._read(
            "control-plane/aegisops_control_plane/readiness_operability.py"
        )
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        http_sources = "\n".join(
            self._read(relative_path)
            for relative_path in (
                "control-plane/aegisops_control_plane/http_surface.py",
                "control-plane/aegisops_control_plane/http_runtime_surface.py",
                "control-plane/aegisops_control_plane/http_protected_surface.py",
                "control-plane/aegisops_control_plane/cli.py",
            )
        )
        write_surface_tree = ast.parse(write_surface_source)
        readiness_operability_tree = ast.parse(readiness_operability_source)
        service_tree = ast.parse(service_source)
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        service_method_names = {
            node.name
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }
        removed_internal_delegate_names = {
            "_action_request_is_review_bound",
            "_action_review_approval_decision",
            "_action_review_approval_state",
            "_action_review_execution",
            "_action_review_state",
            "_action_review_visibility_update",
        }

        self.assertFalse(removed_internal_delegate_names & service_method_names)
        for helper_name in removed_internal_delegate_names:
            self.assertNotIn(helper_name, http_sources)

        direct_projection_call_names = {
            node.func.attr
            for tree in (write_surface_tree, readiness_operability_tree)
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "_action_review_projection"
        }
        self.assertTrue(
            {
                "_action_review_approval_decision",
                "_action_review_approval_state",
                "_action_review_execution",
                "_action_review_state",
                "_action_review_visibility_update",
            }.issubset(direct_projection_call_names)
        )
        service_facade_delegate_names = removed_internal_delegate_names - {
            "_action_request_is_review_bound",
        }
        for helper_name in service_facade_delegate_names:
            for tree in (write_surface_tree, readiness_operability_tree):
                service_facade_calls = [
                    node
                    for node in ast.walk(tree)
                    if isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == helper_name
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in {"self", "service"}
                ]
                self.assertFalse(
                    service_facade_calls,
                    f"{helper_name} must not be reached through the service facade",
                )

    def test_phase50_constructor_delegates_collaborator_composition(self) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        tree = ast.parse(service_source)
        service_class = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        constructor = next(
            node
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "__init__"
        )

        direct_constructor_calls = {
            node.func.id
            for node in ast.walk(constructor)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id
            in {
                "AITraceLifecycleService",
                "ActionLifecycleWriteCoordinator",
                "ActionOrchestrationBoundary",
                "ActionReviewWriteSurface",
                "AssistantAdvisoryCoordinator",
                "AssistantContextAssembler",
                "AssistantProviderAdapter",
                "CaseWorkflowService",
                "DetectionIntakeService",
                "EndpointEvidencePackAdapter",
                "EvidenceLinkageService",
                "ExecutionCoordinator",
                "ExternalEvidenceBoundary",
                "IsolatedExecutorAdapter",
                "LiveAssistantWorkflowCoordinator",
                "MispContextAdapter",
                "N8NReconciliationAdapter",
                "OperatorInspectionReadSurface",
                "OsqueryHostContextAdapter",
                "PostgresControlPlaneStore",
                "ReconciliationOrchestrationBoundary",
                "RestoreReadinessService",
                "ReviewedSlicePolicy",
                "RuntimeBoundaryService",
                "RuntimeRestoreReadinessDiagnosticsService",
                "ShuffleActionAdapter",
            }
        }
        composition_call_names = {
            node.func.id
            for node in ast.walk(constructor)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
        }

        self.assertFalse(
            direct_constructor_calls,
            "facade constructor should delegate collaborator wiring, found "
            f"{sorted(direct_constructor_calls)}",
        )
        self.assertIn(
            "build_control_plane_service_composition",
            composition_call_names,
        )

    def test_phase50_12_2_constructor_keeps_composition_assignment_out_of_facade(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        tree = ast.parse(service_source)
        service_class = next(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        constructor = next(
            node
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
            and node.name == "__init__"
        )
        self_assignments = [
            node
            for node in ast.walk(constructor)
            if isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "self"
            and isinstance(getattr(node, "ctx", None), ast.Store)
        ]
        direct_setattr_calls = [
            node
            for node in ast.walk(constructor)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "setattr"
            and (
                (
                    len(node.args) >= 1
                    and isinstance(node.args[0], ast.Name)
                    and node.args[0].id == "self"
                )
                or any(
                    keyword.arg in {"obj", "target"}
                    and isinstance(keyword.value, ast.Name)
                    and keyword.value.id == "self"
                    for keyword in node.keywords
                )
            )
        ]
        facade_self_wiring = self_assignments + direct_setattr_calls
        constructor_call_names = {
            node.func.id
            for node in ast.walk(constructor)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
        }

        self.assertLessEqual(
            len(facade_self_wiring),
            2,
            "facade constructor should not directly assign or setattr "
            "composition collaborators",
        )
        self.assertNotIn(
            "ControlPlaneServiceCompositionDependencies",
            constructor_call_names,
            "dependency container wiring should live outside the facade constructor",
        )
        self.assertIn(
            "install_control_plane_service_composition",
            constructor_call_names,
        )

    def test_phase50_12_3_action_approval_policy_helpers_leave_service_facade(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        write_surface_source = self._read(
            "control-plane/aegisops_control_plane/actions/review/action_review_write_surface.py"
        )
        service_tree = ast.parse(service_source)
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        service_method_names = {
            node.name
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }
        service_module_function_names = {
            node.name
            for node in service_tree.body
            if isinstance(node, ast.FunctionDef)
        }
        write_surface_functions = {
            node.name
            for node in ast.parse(write_surface_source).body
            if isinstance(node, ast.FunctionDef)
        }

        approval_policy_helpers = {
            "_require_reviewed_action_approver_policy",
            "_reviewed_action_class_for_request",
            "_authorized_approver_identities_for_request",
        }
        self.assertFalse(
            approval_policy_helpers & service_method_names,
            "reviewed action approval policy helpers should not remain service facade methods",
        )
        self.assertFalse(
            approval_policy_helpers & service_module_function_names,
            "reviewed action approval policy helpers should not remain service module functions",
        )
        self.assertTrue(
            approval_policy_helpers.issubset(write_surface_functions),
            "reviewed action approval policy helpers should live with the approval write surface",
        )

    def test_phase50_12_6_action_review_visibility_helpers_leave_service_facade(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        write_surface_source = self._read(
            "control-plane/aegisops_control_plane/actions/review/action_review_write_surface.py"
        )
        service_tree = ast.parse(service_source)
        write_surface_tree = ast.parse(write_surface_source)
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        write_surface_class = next(
            node
            for node in write_surface_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "ActionReviewWriteSurface"
        )
        service_method_names = {
            node.name
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }
        write_surface_method_names = {
            node.name
            for node in write_surface_class.body
            if isinstance(node, ast.FunctionDef)
        }

        visibility_helper_names = {
            "_require_review_bound_action_request",
            "_require_action_review_visibility_context_record",
            "_persist_action_review_visibility_context_record",
        }
        self.assertFalse(
            visibility_helper_names & service_method_names,
            "action review visibility persistence helpers should not remain "
            "service facade methods",
        )
        self.assertTrue(
            visibility_helper_names.issubset(write_surface_method_names),
            "action review visibility persistence helpers should live with the "
            "write surface that records the reviewed context",
        )

    def test_phase50_13_3_private_guard_helpers_move_to_owned_boundaries(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        operator_source = self._read(
            "control-plane/aegisops_control_plane/operator_inspection.py"
        )
        action_request_source = self._read(
            "control-plane/aegisops_control_plane/actions/execution_coordinator_action_requests.py"
        )
        service_tree = ast.parse(service_source)
        operator_tree = ast.parse(operator_source)
        action_request_tree = ast.parse(action_request_source)
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        operator_class = next(
            node
            for node in operator_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "OperatorInspectionReadSurface"
        )
        action_request_class = next(
            node
            for node in action_request_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "ReviewedActionRequestCoordinator"
        )
        service_method_names = {
            node.name
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }
        operator_method_names = {
            node.name
            for node in operator_class.body
            if isinstance(node, ast.FunctionDef)
        }
        action_request_method_names = {
            node.name
            for node in action_request_class.body
            if isinstance(node, ast.FunctionDef)
        }

        operator_guard_helpers = {
            "_alert_review_state",
            "_observations_for_case",
            "_leads_for_case",
        }
        action_request_guard_helpers = {
            "_require_single_linked_case_id",
            "_require_single_recommendation_binding",
        }
        moved_guard_helpers = operator_guard_helpers | action_request_guard_helpers

        self.assertFalse(
            moved_guard_helpers & service_method_names,
            "private guards with owned read/write boundaries should not remain "
            "service facade methods",
        )
        self.assertTrue(operator_guard_helpers.issubset(operator_method_names))
        self.assertTrue(
            action_request_guard_helpers.issubset(action_request_method_names)
        )

    def test_phase50_9_3_persistence_restore_and_status_helpers_leave_service_facade(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        backup_restore_source = self._read(
            "control-plane/aegisops_control_plane/runtime/restore_readiness_backup_restore.py"
        )
        projection_source = self._read(
            "control-plane/aegisops_control_plane/runtime/restore_readiness_projection.py"
        )
        persistence_source = self._read(
            "control-plane/aegisops_control_plane/persistence_lifecycle.py"
        )
        service_tree = ast.parse(service_source)
        backup_restore_functions = {
            node.name
            for node in ast.parse(backup_restore_source).body
            if isinstance(node, ast.FunctionDef)
        }
        projection_class = next(
            node
            for node in ast.parse(projection_source).body
            if isinstance(node, ast.ClassDef)
            and node.name == "_ReadinessHealthProjection"
        )
        projection_methods = {
            node.name for node in projection_class.body if isinstance(node, ast.FunctionDef)
        }
        persistence_class = next(
            node
            for node in ast.parse(persistence_source).body
            if isinstance(node, ast.ClassDef)
            and node.name == "PersistenceLifecycleService"
        )
        persistence_methods = {
            node.name
            for node in persistence_class.body
            if isinstance(node, ast.FunctionDef)
        }
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        service_methods = {
            node.name: node
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }
        service_module_functions = {
            node.name for node in service_tree.body if isinstance(node, ast.FunctionDef)
        }

        self.assertNotIn("_build_shutdown_status_snapshot", service_module_functions)
        self.assertIn("_build_shutdown_status_snapshot", projection_methods)
        self.assertFalse(
            {
                "_parse_backup_datetime",
                "_record_from_backup_payload",
            }
            & service_module_functions
        )
        self.assertTrue(
            {
                "_parse_backup_datetime",
                "_record_from_backup_payload",
            }.issubset(backup_restore_functions)
        )
        self.assertIn("persist_record", persistence_methods)

        persist_record = service_methods["persist_record"]
        self.assertEqual(
            len(persist_record.body),
            1,
            "service.persist_record should stay as a single return delegate",
        )
        self.assertIsInstance(persist_record.body[0], ast.Return)
        delegate_call = persist_record.body[0].value
        self.assertIsInstance(delegate_call, ast.Call)
        self.assertIsInstance(delegate_call.func, ast.Attribute)
        self.assertEqual(delegate_call.func.attr, "persist_record")
        self.assertIsInstance(delegate_call.func.value, ast.Attribute)
        self.assertEqual(
            delegate_call.func.value.attr,
            "_persistence_lifecycle_service",
        )
        self.assertIsInstance(delegate_call.func.value.value, ast.Name)
        self.assertEqual(delegate_call.func.value.value.id, "self")

    def test_phase50_detection_linkage_helpers_leave_service_facade(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        detection_source = self._read(
            "control-plane/aegisops_control_plane/ingestion/detection_lifecycle.py"
        )
        case_source = self._read(
            "control-plane/aegisops_control_plane/ingestion/case_workflow.py"
        )
        service_tree = ast.parse(service_source)
        detection_tree = ast.parse(detection_source)
        case_tree = ast.parse(case_source)
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        detection_class = next(
            node
            for node in detection_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "DetectionIntakeService"
        )
        case_linkage_class = next(
            node
            for node in case_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "CaseDetectionLinkageHelper"
        )

        case_linkage_helper_names = {
            "_link_case_to_analytic_signals",
            "_list_alert_evidence_records",
            "_link_case_to_alert_reconciliations",
        }
        detection_helper_names = {
            "ingest_analytic_signal_admission",
            "attach_native_detection_context",
            "resolve_analytic_signal_id",
        }
        removed_service_helper_names = {
            *case_linkage_helper_names,
            "_ingest_analytic_signal_admission",
            "_attach_native_detection_context",
            "_with_native_detection_admission_provenance",
            "_resolve_analytic_signal_id",
        }
        detection_method_names = {
            node.name
            for node in detection_class.body
            if isinstance(node, ast.FunctionDef)
        }
        case_linkage_method_names = {
            node.name
            for node in case_linkage_class.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertTrue(detection_helper_names.issubset(detection_method_names))
        self.assertTrue(case_linkage_helper_names.issubset(case_linkage_method_names))

        service_methods = {
            node.name: node
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }
        self.assertFalse(
            removed_service_helper_names & service_methods.keys(),
            "detection and case-linkage residual helpers should not remain service facade methods",
        )

    def test_phase50_10_5_lifecycle_transition_callers_bypass_facade_delegates(
        self,
    ) -> None:
        service_source = self._read("control-plane/aegisops_control_plane/service.py")
        composition_source = self._read(
            "control-plane/aegisops_control_plane/service_composition.py"
        )
        endpoint_source = self._read(
            "control-plane/aegisops_control_plane/evidence/external_evidence_endpoint.py"
        )
        service_tree = ast.parse(service_source)
        service_class = next(
            node
            for node in service_tree.body
            if isinstance(node, ast.ClassDef)
            and node.name == "AegisOpsControlPlaneService"
        )
        service_method_names = {
            node.name
            for node in service_class.body
            if isinstance(node, ast.FunctionDef)
        }

        self.assertNotIn("_build_lifecycle_transition_record", service_method_names)
        self.assertNotIn("_build_lifecycle_transition_records", service_method_names)
        self.assertIn(
            "lifecycle_transition_helper.build_lifecycle_transition_record",
            composition_source,
        )
        self.assertIn(
            "transition_helper.build_lifecycle_transition_records",
            endpoint_source,
        )
        self.assertNotIn(
            "service._build_lifecycle_transition_record",
            composition_source,
        )
        self.assertNotIn(
            "self._service._build_lifecycle_transition_records",
            endpoint_source,
        )

    def test_phase50_5_second_hotspot_boundary_methods_are_split(self) -> None:
        targets = {
            (
                "control-plane/aegisops_control_plane/assistant/assistant_context.py",
                "AssistantContextAssembler",
                "inspect_assistant_context",
            ): {
                "max_lines": 180,
                "required_helpers": {
                    "_require_context_record",
                    "_context_lineage",
                    "_linked_records_for_context",
                    "_context_reviewed_context",
                    "_build_context_snapshot",
                },
            },
            (
                "control-plane/aegisops_control_plane/ingestion/detection_lifecycle.py",
                "DetectionIntakeService",
                "ingest_analytic_signal_admission",
            ): {
                "max_lines": 170,
                "required_helpers": {
                    "_resolve_admission_inputs",
                    "_admit_new_alert",
                    "_merge_existing_alert_admission",
                    "_persist_analytic_signal_admission",
                    "_persist_admission_reconciliation",
                },
            },
            (
                "control-plane/aegisops_control_plane/operator_inspection.py",
                "OperatorInspectionReadSurface",
                "inspect_analyst_queue",
            ): {
                "max_lines": 90,
                "required_helpers": {
                    "_queue_record_for_alert",
                    "_sorted_queue_records",
                },
            },
        }

        for (relative_path, class_name, method_name), expectation in targets.items():
            source = self._read(relative_path)
            tree = ast.parse(source, filename=relative_path)
            target_class = next(
                node
                for node in tree.body
                if isinstance(node, ast.ClassDef) and node.name == class_name
            )
            methods = {
                node.name: node
                for node in target_class.body
                if isinstance(node, ast.FunctionDef)
            }
            self.assertTrue(
                expectation["required_helpers"].issubset(methods),
                f"{class_name} should split {method_name} through focused helpers",
            )
            target_method = methods[method_name]
            self.assertLessEqual(
                target_method.end_lineno - target_method.lineno + 1,
                expectation["max_lines"],
                f"{class_name}.{method_name} remains a second-hotspot candidate",
            )
            oversized_helpers = {
                helper_name: helper.end_lineno - helper.lineno + 1
                for helper_name, helper in methods.items()
                if helper.end_lineno - helper.lineno + 1 > 180
            }
            self.assertEqual(
                oversized_helpers,
                {},
                f"{class_name} should not replace one hotspot with a broad helper",
            )


if __name__ == "__main__":
    unittest.main()
