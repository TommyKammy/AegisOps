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


class ActionReviewWriteBoundaryTests(unittest.TestCase):
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

    def test_service_initializes_dedicated_action_review_write_surface(self) -> None:
        service = self._build_service()

        self.assertTrue(
            hasattr(service, "_action_review_write_surface"),
            "expected AegisOpsControlPlaneService to compose a dedicated action-review write surface",
        )

    def test_service_delegates_action_review_write_entrypoints_to_write_surface(
        self,
    ) -> None:
        service = self._build_service()
        approval_decision = object()
        fallback_result = object()
        escalation_result = object()
        write_surface = mock.Mock()
        write_surface.record_action_approval_decision.return_value = approval_decision
        write_surface.record_action_review_manual_fallback.return_value = fallback_result
        write_surface.record_action_review_escalation_note.return_value = (
            escalation_result
        )
        service._action_review_write_surface = write_surface
        decided_at = datetime(2026, 4, 24, 9, 0, tzinfo=timezone.utc)
        fallback_at = datetime(2026, 4, 24, 10, 0, tzinfo=timezone.utc)
        escalated_at = datetime(2026, 4, 24, 11, 0, tzinfo=timezone.utc)

        self.assertIs(
            service.record_action_approval_decision(
                action_request_id="action-request-001",
                approver_identity="approver-001",
                authenticated_approver_identity="approver-001",
                decision="grant",
                decision_rationale="Reviewed notify request is bounded to the approved operator slice.",
                decided_at=decided_at,
                approval_decision_id="approval-001",
            ),
            approval_decision,
        )
        self.assertIs(
            service.record_action_review_manual_fallback(
                action_request_id="action-request-001",
                fallback_at=fallback_at,
                fallback_actor_identity="analyst-001",
                authority_boundary="business-hours operator",
                reason="Downstream execution surface timed out before authoritative confirmation.",
                action_taken="Recorded a manual follow-up and preserved the reviewed boundary.",
                verification_evidence_ids=("evidence-001",),
                residual_uncertainty="Awaiting durable downstream reconciliation.",
            ),
            fallback_result,
        )
        self.assertIs(
            service.record_action_review_escalation_note(
                action_request_id="action-request-001",
                escalated_at=escalated_at,
                escalated_by_identity="analyst-001",
                escalated_to="team-lead-001",
                note="Escalated for explicit after-hours accountability.",
            ),
            escalation_result,
        )

        write_surface.record_action_approval_decision.assert_called_once_with(
            action_request_id="action-request-001",
            approver_identity="approver-001",
            authenticated_approver_identity="approver-001",
            decision="grant",
            decision_rationale="Reviewed notify request is bounded to the approved operator slice.",
            decided_at=decided_at,
            approval_decision_id="approval-001",
        )
        write_surface.record_action_review_manual_fallback.assert_called_once_with(
            action_request_id="action-request-001",
            fallback_at=fallback_at,
            fallback_actor_identity="analyst-001",
            authority_boundary="business-hours operator",
            reason="Downstream execution surface timed out before authoritative confirmation.",
            action_taken="Recorded a manual follow-up and preserved the reviewed boundary.",
            verification_evidence_ids=("evidence-001",),
            residual_uncertainty="Awaiting durable downstream reconciliation.",
        )
        write_surface.record_action_review_escalation_note.assert_called_once_with(
            action_request_id="action-request-001",
            escalated_at=escalated_at,
            escalated_by_identity="analyst-001",
            escalated_to="team-lead-001",
            note="Escalated for explicit after-hours accountability.",
        )


if __name__ == "__main__":
    unittest.main()
