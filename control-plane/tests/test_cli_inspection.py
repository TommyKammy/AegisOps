from __future__ import annotations
# ruff: noqa: E402

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _cli_inspection_support import (
    AegisOpsControlPlaneService,
    ActionExecutionRecord,
    AlertRecord,
    CaseRecord,
    ControlPlaneCliInspectionTestBase,
    datetime,
    replace,
)
from test_cli_inspection_action_reviews import CliInspectionActionReviewTests
from test_cli_inspection_runtime_surface import CliInspectionRuntimeSurfaceTests
from test_cli_inspection_usage_errors import CliInspectionUsageErrorTests
from test_cli_inspection_workflow_family import CliInspectionWorkflowFamilyTests


class ControlPlaneCliInspectionTests(ControlPlaneCliInspectionTestBase):
    """Legacy facade for helper consumers and regression-name probes."""

    def test_long_running_runtime_surface_exposes_analyst_queue_alert_detail_and_case_detail_http_views(
        self,
    ) -> None:
        CliInspectionRuntimeSurfaceTests.test_long_running_runtime_surface_exposes_analyst_queue_alert_detail_and_case_detail_http_views(
            self
        )

    def test_long_running_runtime_surface_exposes_operator_readiness_diagnostics_http_view(
        self,
    ) -> None:
        CliInspectionRuntimeSurfaceTests.test_long_running_runtime_surface_exposes_operator_readiness_diagnostics_http_view(
            self
        )

    def test_backup_and_restore_drill_commands_render_recovery_payloads(self) -> None:
        CliInspectionRuntimeSurfaceTests.test_backup_and_restore_drill_commands_render_recovery_payloads(
            self
        )

    def test_long_running_runtime_surface_exposes_cited_advisory_review_routes(
        self,
    ) -> None:
        CliInspectionWorkflowFamilyTests.test_long_running_runtime_surface_exposes_cited_advisory_review_routes(
            self
        )

    def test_cli_renders_read_only_record_and_reconciliation_views(self) -> None:
        CliInspectionWorkflowFamilyTests.test_cli_renders_read_only_record_and_reconciliation_views(
            self
        )

    def test_cli_renders_wazuh_business_hours_analyst_queue_view(self) -> None:
        CliInspectionWorkflowFamilyTests.test_cli_renders_reviewed_wazuh_business_hours_analyst_queue_view(
            self
        )

    def test_long_running_runtime_surface_rejects_case_scoped_out_of_scope_advisory_reads(
        self,
    ) -> None:
        CliInspectionWorkflowFamilyTests.test_long_running_runtime_surface_rejects_case_scoped_out_of_scope_advisory_reads(
            self
        )

    def test_long_running_runtime_surface_rejects_case_family_out_of_scope_advisory_reads(
        self,
    ) -> None:
        CliInspectionWorkflowFamilyTests.test_long_running_runtime_surface_rejects_case_family_out_of_scope_advisory_reads(
            self
        )

    def test_long_running_runtime_surface_rejects_case_scoped_advisory_reads_without_linked_case(
        self,
    ) -> None:
        CliInspectionWorkflowFamilyTests.test_long_running_runtime_surface_rejects_case_scoped_advisory_reads_without_linked_case(
            self
        )

    def test_cli_creates_reviewed_action_request_from_recommendation_context(
        self,
    ) -> None:
        CliInspectionActionReviewTests.test_cli_creates_reviewed_action_request_from_recommendation_context(
            self
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_outcome(
        self,
    ) -> None:
        CliInspectionActionReviewTests.test_cli_inspect_case_detail_surfaces_create_tracking_ticket_outcome(
            self
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_mismatch(
        self,
    ) -> None:
        CliInspectionActionReviewTests.test_cli_inspect_case_detail_surfaces_create_tracking_ticket_mismatch(
            self
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_timeout(
        self,
    ) -> None:
        CliInspectionActionReviewTests.test_cli_inspect_case_detail_surfaces_create_tracking_ticket_timeout(
            self
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_manual_fallback(
        self,
    ) -> None:
        CliInspectionActionReviewTests.test_cli_inspect_case_detail_surfaces_create_tracking_ticket_manual_fallback(
            self
        )

    def test_cli_renders_identity_rich_analyst_queue_view_with_reviewed_context(
        self,
    ) -> None:
        CliInspectionUsageErrorTests.test_cli_renders_identity_rich_analyst_queue_view_with_reviewed_context(
            self
        )


class CliInspectionVerifierCompatibilityTests(unittest.TestCase):
    """Legacy verifier names that must stay unittest-discoverable in this module."""

    def _run_split_case(
        self,
        case_type: type[unittest.TestCase],
        test_name: str,
    ) -> None:
        result = unittest.TestResult()
        case_type(test_name).run(result)
        if result.wasSuccessful():
            return
        details = []
        for _, message in result.failures + result.errors:
            details.append(message)
        self.fail("\n\n".join(details) or f"{case_type.__name__}.{test_name} failed")

    def test_cli_renders_read_only_record_and_reconciliation_views(self) -> None:
        self._run_split_case(
            CliInspectionWorkflowFamilyTests,
            "test_cli_renders_read_only_record_and_reconciliation_views",
        )

    def test_cli_renders_wazuh_business_hours_analyst_queue_view(self) -> None:
        self._run_split_case(
            CliInspectionWorkflowFamilyTests,
            "test_cli_renders_reviewed_wazuh_business_hours_analyst_queue_view",
        )

    def test_cli_renders_identity_rich_analyst_queue_view_with_reviewed_context(
        self,
    ) -> None:
        self._run_split_case(
            CliInspectionUsageErrorTests,
            "test_cli_renders_identity_rich_analyst_queue_view_with_reviewed_context",
        )


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del standard_tests
    if pattern not in (None, "test_cli_inspection.py"):
        return unittest.TestSuite()
    suite = unittest.TestSuite()
    for case in (
        CliInspectionRuntimeSurfaceTests,
        CliInspectionWorkflowFamilyTests,
        CliInspectionActionReviewTests,
        CliInspectionUsageErrorTests,
    ):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


__all__ = [
    "AegisOpsControlPlaneService",
    "ActionExecutionRecord",
    "AlertRecord",
    "CliInspectionActionReviewTests",
    "CliInspectionRuntimeSurfaceTests",
    "CliInspectionUsageErrorTests",
    "CliInspectionVerifierCompatibilityTests",
    "CliInspectionWorkflowFamilyTests",
    "ControlPlaneCliInspectionTests",
    "CaseRecord",
    "datetime",
    "replace",
]


if __name__ == "__main__":
    unittest.main()
