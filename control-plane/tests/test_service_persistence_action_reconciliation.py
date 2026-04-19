from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _service_persistence_support import ServicePersistenceTestBase
from test_service_persistence_action_reconciliation_create_tracking_ticket import (
    CreateTrackingTicketActionReconciliationPersistenceTests,
)
from test_service_persistence_action_reconciliation_delegation import (
    ActionDelegationPolicyPersistenceTests,
)
from test_service_persistence_action_reconciliation_reconciliation import (
    ActionExecutionReconciliationPersistenceTests,
)
from test_service_persistence_action_reconciliation_review_surfaces import (
    ActionReviewSurfacePersistenceTests,
)
from test_service_persistence_action_reconciliation_reviewed_requests import (
    ReviewedActionRequestPersistenceTests,
)


class ActionReconciliationPersistenceTests(ServicePersistenceTestBase):
    """Compatibility facade for legacy CI selectors and verifier scripts."""

    def test_service_records_execution_correlation_mismatch_states_separately(
        self,
    ) -> None:
        CreateTrackingTicketActionReconciliationPersistenceTests.test_service_records_execution_correlation_mismatch_states_separately(
            self
        )

    def test_service_evaluates_action_policy_into_approval_and_isolated_executor(
        self,
    ) -> None:
        ActionDelegationPolicyPersistenceTests.test_service_evaluates_action_policy_into_approval_and_isolated_executor(
            self
        )

    def test_service_evaluates_action_policy_into_shuffle_without_human_approval(
        self,
    ) -> None:
        ActionDelegationPolicyPersistenceTests.test_service_evaluates_action_policy_into_shuffle_without_human_approval(
            self
        )

    def test_service_delegates_approved_low_risk_action_through_shuffle_adapter(
        self,
    ) -> None:
        ActionDelegationPolicyPersistenceTests.test_service_delegates_approved_low_risk_action_through_shuffle_adapter(
            self
        )

    def test_service_rechecks_shuffle_approval_inside_transaction(self) -> None:
        ActionDelegationPolicyPersistenceTests.test_service_rechecks_shuffle_approval_inside_transaction(
            self
        )

    def test_service_rejects_shuffle_delegation_for_non_shuffle_execution_policy(
        self,
    ) -> None:
        ActionDelegationPolicyPersistenceTests.test_service_rejects_shuffle_delegation_for_non_shuffle_execution_policy(
            self
        )

    def test_service_delegates_approved_high_risk_action_through_isolated_executor(
        self,
    ) -> None:
        ActionDelegationPolicyPersistenceTests.test_service_delegates_approved_high_risk_action_through_isolated_executor(
            self
        )

    def test_service_rejects_shuffle_delegation_when_payload_binding_drifts(
        self,
    ) -> None:
        ActionDelegationPolicyPersistenceTests.test_service_rejects_shuffle_delegation_when_payload_binding_drifts(
            self
        )

    def test_service_rejects_shuffle_delegation_when_expiry_window_drifts_after_approval(
        self,
    ) -> None:
        ActionDelegationPolicyPersistenceTests.test_service_rejects_shuffle_delegation_when_expiry_window_drifts_after_approval(
            self
        )

    def test_service_reconcile_action_execution_supports_generic_execution_surfaces(
        self,
    ) -> None:
        ActionExecutionReconciliationPersistenceTests.test_service_reconcile_action_execution_supports_generic_execution_surfaces(
            self
        )

    def test_service_reconciles_shuffle_run_back_into_authoritative_action_execution(
        self,
    ) -> None:
        ActionExecutionReconciliationPersistenceTests.test_service_reconciles_shuffle_run_back_into_authoritative_action_execution(
            self
        )

    def test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution(
        self,
    ) -> None:
        ActionExecutionReconciliationPersistenceTests.test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution(
            self
        )


def load_tests(
    loader: unittest.TestLoader,
    standard_tests: unittest.TestSuite,
    pattern: str | None,
) -> unittest.TestSuite:
    del standard_tests, pattern
    suite = unittest.TestSuite()
    for case in (
        CreateTrackingTicketActionReconciliationPersistenceTests,
        ActionDelegationPolicyPersistenceTests,
        ActionExecutionReconciliationPersistenceTests,
        ActionReviewSurfacePersistenceTests,
        ReviewedActionRequestPersistenceTests,
    ):
        suite.addTests(loader.loadTestsFromTestCase(case))
    return suite


__all__ = [
    'ActionReconciliationPersistenceTests',
    'ActionDelegationPolicyPersistenceTests',
    'ActionExecutionReconciliationPersistenceTests',
    'ActionReviewSurfacePersistenceTests',
    'CreateTrackingTicketActionReconciliationPersistenceTests',
    'ReviewedActionRequestPersistenceTests',
]
