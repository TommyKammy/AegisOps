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
from aegisops_control_plane.action_lifecycle_write_coordinator import (
    ActionLifecycleWriteCoordinator,
)
from aegisops_control_plane.execution_coordinator import ExecutionCoordinator
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

    def test_service_initializes_dedicated_action_lifecycle_write_coordinator(
        self,
    ) -> None:
        service = self._build_service()

        self.assertTrue(
            hasattr(service, "_action_lifecycle_write_coordinator"),
            "expected AegisOpsControlPlaneService to compose a dedicated action lifecycle write coordinator",
        )

    def test_service_routes_action_lifecycle_write_entrypoints_through_coordinator(
        self,
    ) -> None:
        service = self._build_service()
        coordinator = mock.Mock()
        action_request_result = object()
        tracking_ticket_result = object()
        approval_result = object()
        shuffle_result = object()
        isolated_result = object()
        reconciliation_result = object()
        coordinator.create_reviewed_action_request_from_advisory.return_value = (
            action_request_result
        )
        coordinator.create_reviewed_tracking_ticket_request_from_advisory.return_value = (
            tracking_ticket_result
        )
        coordinator.record_action_approval_decision.return_value = approval_result
        coordinator.delegate_approved_action_to_shuffle.return_value = shuffle_result
        coordinator.delegate_approved_action_to_isolated_executor.return_value = (
            isolated_result
        )
        coordinator.reconcile_action_execution.return_value = reconciliation_result
        service._action_lifecycle_write_coordinator = coordinator
        expires_at = datetime(2026, 4, 15, 0, 0, tzinfo=timezone.utc)
        decided_at = datetime(2026, 4, 15, 0, 30, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 15, 1, 0, tzinfo=timezone.utc)
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

        self.assertIs(
            service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id="recommendation-001",
                requester_identity="analyst-001",
                recipient_identity="owner-001",
                message_intent="notify",
                escalation_reason="bounded reason",
                expires_at=expires_at,
                action_request_id="action-request-001",
            ),
            action_request_result,
        )
        self.assertIs(
            service.create_reviewed_tracking_ticket_request_from_advisory(
                record_family="recommendation",
                record_id="recommendation-002",
                requester_identity="analyst-001",
                coordination_reference_id="case-001",
                coordination_target_type="zammad",
                ticket_title="Review bounded case",
                ticket_description="Open a link-first coordination ticket.",
                expires_at=expires_at,
                ticket_severity="medium",
                action_request_id="action-request-002",
            ),
            tracking_ticket_result,
        )
        self.assertIs(
            service.record_action_approval_decision(
                action_request_id="action-request-001",
                approver_identity="approver-001",
                authenticated_approver_identity="approver-001",
                decision="grant",
                decision_rationale="Reviewed action remains bounded.",
                decided_at=decided_at,
                approval_decision_id="approval-001",
            ),
            approval_result,
        )
        self.assertIs(
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-001",
                approved_payload={"action": "notify"},
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
                evidence_ids=("evidence-001",),
            ),
            shuffle_result,
        )
        self.assertIs(
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-002",
                approved_payload={"action": "notify"},
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
                evidence_ids=("evidence-002",),
            ),
            isolated_result,
        )
        self.assertIs(
            service.reconcile_action_execution(
                action_request_id="action-request-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=observed_executions,
                compared_at=compared_at,
                stale_after=stale_after,
            ),
            reconciliation_result,
        )

        coordinator.create_reviewed_action_request_from_advisory.assert_called_once_with(
            record_family="recommendation",
            record_id="recommendation-001",
            requester_identity="analyst-001",
            recipient_identity="owner-001",
            message_intent="notify",
            escalation_reason="bounded reason",
            expires_at=expires_at,
            action_request_id="action-request-001",
        )
        coordinator.create_reviewed_tracking_ticket_request_from_advisory.assert_called_once_with(
            record_family="recommendation",
            record_id="recommendation-002",
            requester_identity="analyst-001",
            coordination_reference_id="case-001",
            coordination_target_type="zammad",
            ticket_title="Review bounded case",
            ticket_description="Open a link-first coordination ticket.",
            expires_at=expires_at,
            ticket_severity="medium",
            action_request_id="action-request-002",
        )
        coordinator.record_action_approval_decision.assert_called_once_with(
            action_request_id="action-request-001",
            approver_identity="approver-001",
            authenticated_approver_identity="approver-001",
            decision="grant",
            decision_rationale="Reviewed action remains bounded.",
            decided_at=decided_at,
            approval_decision_id="approval-001",
        )
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
        coordinator.reconcile_action_execution.assert_called_once_with(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
        )

    def test_action_lifecycle_write_coordinator_preserves_internal_boundaries(
        self,
    ) -> None:
        service = mock.Mock()
        coordinator = ActionLifecycleWriteCoordinator(service)
        service._execution_coordinator = mock.Mock()
        service._action_review_write_surface = mock.Mock()
        action_request_result = object()
        tracking_ticket_result = object()
        approval_result = object()
        shuffle_result = object()
        isolated_result = object()
        reconciliation_result = object()
        service._execution_coordinator.create_reviewed_action_request_from_advisory.return_value = (
            action_request_result
        )
        service._execution_coordinator.create_reviewed_tracking_ticket_request_from_advisory.return_value = (
            tracking_ticket_result
        )
        service._action_review_write_surface.record_action_approval_decision.return_value = (
            approval_result
        )
        service._execution_coordinator.delegate_approved_action_to_shuffle.return_value = (
            shuffle_result
        )
        service._execution_coordinator.delegate_approved_action_to_isolated_executor.return_value = (
            isolated_result
        )
        service._execution_coordinator.reconcile_action_execution.return_value = (
            reconciliation_result
        )
        expires_at = datetime(2026, 4, 15, 0, 0, tzinfo=timezone.utc)
        decided_at = datetime(2026, 4, 15, 0, 30, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 15, 1, 0, tzinfo=timezone.utc)
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

        self.assertIs(
            coordinator.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id="recommendation-001",
                requester_identity="analyst-001",
                recipient_identity="owner-001",
                message_intent="notify",
                escalation_reason="bounded reason",
                expires_at=expires_at,
                action_request_id="action-request-001",
            ),
            action_request_result,
        )
        self.assertIs(
            coordinator.create_reviewed_tracking_ticket_request_from_advisory(
                record_family="recommendation",
                record_id="recommendation-002",
                requester_identity="analyst-001",
                coordination_reference_id="case-001",
                coordination_target_type="zammad",
                ticket_title="Review bounded case",
                ticket_description="Open a link-first coordination ticket.",
                expires_at=expires_at,
                ticket_severity="medium",
                action_request_id="action-request-002",
            ),
            tracking_ticket_result,
        )
        self.assertIs(
            coordinator.record_action_approval_decision(
                action_request_id="action-request-001",
                approver_identity="approver-001",
                authenticated_approver_identity="approver-001",
                decision="grant",
                decision_rationale="Reviewed action remains bounded.",
                decided_at=decided_at,
                approval_decision_id="approval-001",
            ),
            approval_result,
        )
        self.assertIs(
            coordinator.delegate_approved_action_to_shuffle(
                action_request_id="action-request-001",
                approved_payload={"action": "notify"},
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
                evidence_ids=("evidence-001",),
            ),
            shuffle_result,
        )
        self.assertIs(
            coordinator.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-002",
                approved_payload={"action": "notify"},
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
                evidence_ids=("evidence-002",),
            ),
            isolated_result,
        )
        self.assertIs(
            coordinator.reconcile_action_execution(
                action_request_id="action-request-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=observed_executions,
                compared_at=compared_at,
                stale_after=stale_after,
            ),
            reconciliation_result,
        )

        service._execution_coordinator.create_reviewed_action_request_from_advisory.assert_called_once_with(
            record_family="recommendation",
            record_id="recommendation-001",
            requester_identity="analyst-001",
            recipient_identity="owner-001",
            message_intent="notify",
            escalation_reason="bounded reason",
            expires_at=expires_at,
            action_request_id="action-request-001",
        )
        service._execution_coordinator.create_reviewed_tracking_ticket_request_from_advisory.assert_called_once_with(
            record_family="recommendation",
            record_id="recommendation-002",
            requester_identity="analyst-001",
            coordination_reference_id="case-001",
            coordination_target_type="zammad",
            ticket_title="Review bounded case",
            ticket_description="Open a link-first coordination ticket.",
            expires_at=expires_at,
            ticket_severity="medium",
            action_request_id="action-request-002",
        )
        service._action_review_write_surface.record_action_approval_decision.assert_called_once_with(
            action_request_id="action-request-001",
            approver_identity="approver-001",
            authenticated_approver_identity="approver-001",
            decision="grant",
            decision_rationale="Reviewed action remains bounded.",
            decided_at=decided_at,
            approval_decision_id="approval-001",
        )
        service._execution_coordinator.delegate_approved_action_to_shuffle.assert_called_once_with(
            action_request_id="action-request-001",
            approved_payload={"action": "notify"},
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-001",),
        )
        service._execution_coordinator.delegate_approved_action_to_isolated_executor.assert_called_once_with(
            action_request_id="action-request-002",
            approved_payload={"action": "notify"},
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-002",),
        )
        service._execution_coordinator.reconcile_action_execution.assert_called_once_with(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
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

    def test_execution_coordinator_composes_dedicated_internal_collaborators(self) -> None:
        coordinator = ExecutionCoordinator(mock.sentinel.service)

        self.assertTrue(
            hasattr(coordinator, "_action_requests"),
            "expected ExecutionCoordinator to compose a dedicated action request collaborator",
        )
        self.assertTrue(
            hasattr(coordinator, "_delegation"),
            "expected ExecutionCoordinator to compose a dedicated delegation collaborator",
        )
        self.assertTrue(
            hasattr(coordinator, "_reconciliation"),
            "expected ExecutionCoordinator to compose a dedicated reconciliation collaborator",
        )

    def test_execution_coordinator_routes_public_entrypoints_through_internal_collaborators(
        self,
    ) -> None:
        coordinator = ExecutionCoordinator(mock.sentinel.service)
        action_request_result = object()
        shuffle_result = object()
        isolated_result = object()
        reconciliation_result = object()
        coordinator._action_requests = mock.Mock()
        coordinator._delegation = mock.Mock()
        coordinator._reconciliation = mock.Mock()
        coordinator._action_requests.create_reviewed_action_request_from_advisory.return_value = (
            action_request_result
        )
        coordinator._delegation.delegate_approved_action_to_shuffle.return_value = (
            shuffle_result
        )
        coordinator._delegation.delegate_approved_action_to_isolated_executor.return_value = (
            isolated_result
        )
        coordinator._reconciliation.reconcile_action_execution.return_value = (
            reconciliation_result
        )
        expires_at = datetime(2026, 4, 15, 0, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 15, 1, 0, tzinfo=timezone.utc)
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

        self.assertIs(
            coordinator.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id="recommendation-001",
                requester_identity="analyst-001",
                recipient_identity="owner-001",
                message_intent="notify",
                escalation_reason="bounded reason",
                expires_at=expires_at,
            ),
            action_request_result,
        )
        self.assertIs(
            coordinator.delegate_approved_action_to_shuffle(
                action_request_id="action-request-001",
                approved_payload={"action": "notify"},
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
                evidence_ids=("evidence-001",),
            ),
            shuffle_result,
        )
        self.assertIs(
            coordinator.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-002",
                approved_payload={"action": "notify"},
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
                evidence_ids=("evidence-002",),
            ),
            isolated_result,
        )
        self.assertIs(
            coordinator.reconcile_action_execution(
                action_request_id="action-request-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=observed_executions,
                compared_at=compared_at,
                stale_after=stale_after,
            ),
            reconciliation_result,
        )

        coordinator._action_requests.create_reviewed_action_request_from_advisory.assert_called_once_with(
            record_family="recommendation",
            record_id="recommendation-001",
            requester_identity="analyst-001",
            recipient_identity="owner-001",
            message_intent="notify",
            escalation_reason="bounded reason",
            expires_at=expires_at,
            action_request_id=None,
        )
        coordinator._delegation.delegate_approved_action_to_shuffle.assert_called_once_with(
            action_request_id="action-request-001",
            approved_payload={"action": "notify"},
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-001",),
        )
        coordinator._delegation.delegate_approved_action_to_isolated_executor.assert_called_once_with(
            action_request_id="action-request-002",
            approved_payload={"action": "notify"},
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-002",),
        )
        coordinator._reconciliation.reconcile_action_execution.assert_called_once_with(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=observed_executions,
            compared_at=compared_at,
            stale_after=stale_after,
        )


if __name__ == "__main__":
    unittest.main()
