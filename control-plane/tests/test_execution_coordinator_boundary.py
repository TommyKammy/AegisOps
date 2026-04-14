from __future__ import annotations

from datetime import datetime, timezone
import pathlib
import sys
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


class ExecutionCoordinatorBoundaryTests(unittest.TestCase):
    def _build_service(self) -> AegisOpsControlPlaneService:
        store, _ = make_store()
        return AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
            ),
            store=store,
        )

    def test_service_initializes_dedicated_execution_coordinator(self) -> None:
        service = self._build_service()

        self.assertTrue(
            hasattr(service, "_execution_coordinator"),
            "expected AegisOpsControlPlaneService to compose a dedicated execution coordinator",
        )

    def test_service_delegates_reviewed_action_request_creation_to_execution_coordinator(
        self,
    ) -> None:
        service = self._build_service()
        expected = object()
        coordinator = mock.Mock()
        coordinator.create_reviewed_action_request_from_advisory.return_value = expected
        service._execution_coordinator = coordinator

        result = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id="recommendation-001",
            requester_identity="analyst-001",
            recipient_identity="owner-001",
            message_intent="notify",
            escalation_reason="bounded reason",
            expires_at=datetime(2026, 4, 15, 0, 0, tzinfo=timezone.utc),
        )

        self.assertIs(result, expected)
        coordinator.create_reviewed_action_request_from_advisory.assert_called_once_with(
            record_family="recommendation",
            record_id="recommendation-001",
            requester_identity="analyst-001",
            recipient_identity="owner-001",
            message_intent="notify",
            escalation_reason="bounded reason",
            expires_at=datetime(2026, 4, 15, 0, 0, tzinfo=timezone.utc),
            action_request_id=None,
        )

    def test_service_delegates_shuffle_and_isolated_executor_flows_to_execution_coordinator(
        self,
    ) -> None:
        service = self._build_service()
        shuffle_result = object()
        isolated_result = object()
        coordinator = mock.Mock()
        coordinator.delegate_approved_action_to_shuffle.return_value = shuffle_result
        coordinator.delegate_approved_action_to_isolated_executor.return_value = (
            isolated_result
        )
        service._execution_coordinator = coordinator
        delegated_at = datetime(2026, 4, 15, 1, 0, tzinfo=timezone.utc)

        shuffle = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-001",
            approved_payload={"action": "notify"},
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-001",),
        )
        isolated = service.delegate_approved_action_to_isolated_executor(
            action_request_id="action-request-002",
            approved_payload={"action": "notify"},
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-002",),
        )

        self.assertIs(shuffle, shuffle_result)
        self.assertIs(isolated, isolated_result)
        coordinator.delegate_approved_action_to_shuffle.assert_called_once_with(
            action_request_id="action-request-001",
            approved_payload={"action": "notify"},
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-001",),
        )
        coordinator.delegate_approved_action_to_isolated_executor.assert_called_once_with(
            action_request_id="action-request-002",
            approved_payload={"action": "notify"},
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-002",),
        )

    def test_service_delegates_reconciliation_flow_to_execution_coordinator(self) -> None:
        service = self._build_service()
        expected = object()
        coordinator = mock.Mock()
        coordinator.reconcile_action_execution.return_value = expected
        service._execution_coordinator = coordinator
        compared_at = datetime(2026, 4, 15, 2, 0, tzinfo=timezone.utc)
        stale_after = datetime(2026, 4, 15, 3, 0, tzinfo=timezone.utc)
        observed_executions = (
            {
                "execution_run_id": "shuffle-run-001",
                "execution_surface_id": "shuffle",
                "idempotency_key": "idem-001",
                "approval_decision_id": "approval-001",
                "delegation_id": "delegation-001",
                "payload_hash": "payload-001",
                "observed_at": compared_at,
            },
        )

        result = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
        )

        self.assertIs(result, expected)
        coordinator.reconcile_action_execution.assert_called_once_with(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
        )


if __name__ == "__main__":
    unittest.main()
