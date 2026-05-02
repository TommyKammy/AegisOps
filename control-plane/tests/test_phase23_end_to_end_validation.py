from __future__ import annotations

import contextlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
import json
import pathlib
import sys
import threading
import unittest
from unittest import mock
from urllib import request


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import main
from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import ApprovalDecisionRecord
from aegisops.control_plane.service import (
    AegisOpsControlPlaneService,
    AuthenticatedRuntimePrincipal,
)
from postgres_test_support import make_store
from support.fixtures import load_wazuh_fixture


REVIEWED_SHARED_SECRET = "reviewed-shared-secret"  # noqa: S105
REVIEWED_PROXY_SECRET = "reviewed-proxy-secret"  # noqa: S105
REVIEWED_PROXY_SERVICE_ACCOUNT = "svc-aegisops-proxy-control-plane"
REVIEWED_APPROVER_PRINCIPAL = AuthenticatedRuntimePrincipal(
    identity="approver-001",
    role="approver",
    access_path="reviewed_reverse_proxy",
    proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
)


class Phase23EndToEndValidationTests(unittest.TestCase):
    @staticmethod
    @contextlib.contextmanager
    def _mock_authenticated_surface_access(
        service: AegisOpsControlPlaneService,
        *,
        principal: AuthenticatedRuntimePrincipal = REVIEWED_APPROVER_PRINCIPAL,
    ) -> object:
        def _authenticate_surface_access(**kwargs: object) -> AuthenticatedRuntimePrincipal:
            allowed_roles = kwargs.get("allowed_roles")
            if not isinstance(allowed_roles, tuple):
                raise AssertionError(
                    "expected authenticate_protected_surface_request to receive allowed_roles"
                )
            if principal.role not in allowed_roles:
                joined_roles = ", ".join(sorted(allowed_roles))
                raise PermissionError(
                    "protected control-plane surface role is not authorized for this endpoint; "
                    f"expected one of: {joined_roles}"
                )
            return principal

        with mock.patch.object(
            service,
            "authenticate_protected_surface_request",
            side_effect=_authenticate_surface_access,
        ) as authenticate_mock:
            yield authenticate_mock

    def _build_service(self) -> AegisOpsControlPlaneService:
        store, _ = make_store()
        return AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

    def _build_pending_action_request(
        self,
        service: AegisOpsControlPlaneService,
        *,
        requester_identity: str = "analyst-001",
        action_request_id: str = "action-request-phase23-e2e-001",
    ) -> object:
        admitted = service.ingest_wazuh_alert(
            raw_alert=load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Validate the live approval, transition logging, and degraded visibility chain."
            ),
        )
        return service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity=requester_identity,
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Phase 23 validation must keep approval and degraded visibility explicit.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id=action_request_id,
        )

    @contextlib.contextmanager
    def _run_runtime(
        self,
        service: AegisOpsControlPlaneService,
        *,
        principal: AuthenticatedRuntimePrincipal = REVIEWED_APPROVER_PRINCIPAL,
    ) -> object:
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(
            main,
            "ThreadingHTTPServer",
            RecordingServer,
        ), self._mock_authenticated_surface_access(
            service,
            principal=principal,
        ):
            thread = threading.Thread(
                target=main.run_control_plane_service,
                args=(service,),
                daemon=True,
            )
            thread.start()
            try:
                for _ in range(100):
                    if servers:
                        break
                    thread.join(0.01)
                self.assertTrue(servers, "expected test HTTP server to start")
                yield f"http://127.0.0.1:{servers[0].server_port}"
            finally:
                if servers:
                    servers[0].shutdown()
                    servers[0].server_close()
                thread.join(timeout=2)

    def test_phase23_end_to_end_live_grant_keeps_transition_history_and_degraded_visibility_explicit(
        self,
    ) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(service)
        decided_at = action_request.requested_at + timedelta(minutes=10)
        approval_decision_id = "approval-phase23-e2e-001"

        with self._run_runtime(service) as base_url:
            response = request.urlopen(  # noqa: S310
                request.Request(  # noqa: S310
                    f"{base_url}/operator/record-action-approval-decision",
                    data=json.dumps(
                        {
                            "action_request_id": action_request.action_request_id,
                            "approval_decision_id": approval_decision_id,
                            "decision": "grant",
                            "approver_identity": "approver-001",
                            "decision_rationale": (
                                "The reviewed change is approved, but Phase 23 must keep any "
                                "missing delegation visible."
                            ),
                            "decided_at": decided_at.isoformat(),
                        }
                    ).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                ),
                timeout=2,
            )
            payload = json.loads(response.read().decode("utf-8"))

        self.assertEqual(response.status, HTTPStatus.OK)
        self.assertEqual(payload["lifecycle_state"], "approved")
        self.assertEqual(payload["approval_decision_id"], approval_decision_id)

        stored_request = service.get_record(type(action_request), action_request.action_request_id)
        self.assertIsNotNone(stored_request)
        self.assertEqual(stored_request.lifecycle_state, "approved")
        stored_decision = service.get_record(ApprovalDecisionRecord, approval_decision_id)
        self.assertIsNotNone(stored_decision)
        self.assertEqual(stored_decision.lifecycle_state, "approved")

        self.assertEqual(
            [
                transition.lifecycle_state
                for transition in service.list_lifecycle_transitions(
                    "action_request",
                    action_request.action_request_id,
                )
            ],
            ["pending_approval", "approved"],
        )
        self.assertEqual(
            [
                transition.lifecycle_state
                for transition in service.list_lifecycle_transitions(
                    "approval_decision",
                    approval_decision_id,
                )
            ],
            ["approved"],
        )

        stale_approved_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        service.persist_record(
            replace(
                stored_decision,
                approved_expires_at=stale_approved_expires_at,
            )
        )
        service.persist_record(
            replace(
                stored_request,
                expires_at=stale_approved_expires_at,
            )
        )

        case_detail = service.inspect_case_detail(stored_request.case_id)
        current_review = case_detail.current_action_review

        self.assertIsNotNone(current_review)
        assert current_review is not None
        self.assertEqual(current_review["review_state"], "approved")
        self.assertEqual(current_review["path_health"]["overall_state"], "degraded")
        self.assertEqual(
            current_review["path_health"]["paths"]["ingest"]["reason"],
            "ingest_signal_missing_after_approval",
        )
        self.assertEqual(
            current_review["path_health"]["paths"]["delegation"]["reason"],
            "reviewed_delegation_missing_after_approval",
        )
        self.assertEqual(
            current_review["path_health"]["paths"]["provider"]["reason"],
            "provider_signal_missing_after_approval",
        )
        self.assertEqual(
            current_review["path_health"]["paths"]["persistence"]["reason"],
            "reconciliation_missing_after_approval",
        )
        self.assertEqual(
            [entry["stage"] for entry in current_review["timeline"]],
            [
                "action_request",
                "approval_decision",
                "delegation",
                "action_execution",
                "reconciliation",
            ],
        )
        self.assertEqual(current_review["timeline"][0]["state"], "approved")
        self.assertEqual(current_review["timeline"][1]["state"], "approved")
        self.assertEqual(current_review["timeline"][2]["state"], "awaiting_delegation")
        self.assertEqual(current_review["timeline"][3]["state"], "awaiting_execution")
        self.assertEqual(current_review["timeline"][4]["state"], "awaiting_reconciliation")


if __name__ == "__main__":
    unittest.main()
