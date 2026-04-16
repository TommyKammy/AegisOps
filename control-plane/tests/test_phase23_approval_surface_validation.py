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
from urllib import error, request


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import main
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import ApprovalDecisionRecord
from aegisops_control_plane.service import (
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
REVIEWED_ANALYST_PRINCIPAL = AuthenticatedRuntimePrincipal(
    identity="analyst-002",
    role="analyst",
    access_path="reviewed_reverse_proxy",
    proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
)
REVIEWED_SECONDARY_APPROVER_PRINCIPAL = AuthenticatedRuntimePrincipal(
    identity="approver-002",
    role="approver",
    access_path="reviewed_reverse_proxy",
    proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
)


class Phase23ApprovalSurfaceValidationTests(unittest.TestCase):
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
                raise AssertionError("expected authenticate_protected_surface_request to receive allowed_roles")
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
        action_request_id: str = "action-request-phase23-live-grant-001",
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
            intended_outcome="Require a reviewed approval decision inside the runtime boundary.",
        )
        return service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity=requester_identity,
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
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
        ) as authenticate_mock:
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
                yield f"http://127.0.0.1:{servers[0].server_port}", authenticate_mock
            finally:
                if servers:
                    servers[0].shutdown()
                    servers[0].server_close()
                thread.join(timeout=2)

    def test_reviewed_runtime_path_records_live_grant_decision(self) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(service)
        decided_at = action_request.requested_at + timedelta(minutes=10)
        with self._run_runtime(service) as (base_url, _authenticate_mock):
            response = request.urlopen(  # noqa: S310
                request.Request(  # noqa: S310
                    f"{base_url}/operator/record-action-approval-decision",
                    data=json.dumps(
                        {
                            "action_request_id": action_request.action_request_id,
                            "approval_decision_id": "approval-phase23-live-grant-001",
                            "decision": "grant",
                            "approver_identity": "approver-001",
                            "decision_rationale": "Approver validated the reviewed owner notification scope.",
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
            self.assertEqual(
                payload["approval_decision_id"],
                "approval-phase23-live-grant-001",
            )
            self.assertEqual(payload["action_request_id"], action_request.action_request_id)
            self.assertEqual(payload["lifecycle_state"], "approved")
            self.assertEqual(payload["approver_identities"], ["approver-001"])
            self.assertEqual(
                payload["decision_rationale"],
                "Approver validated the reviewed owner notification scope.",
            )
            self.assertEqual(
                payload["approved_expires_at"],
                action_request.expires_at.isoformat(),
            )
            stored_request = service.get_record(
                type(action_request),
                action_request.action_request_id,
            )
            self.assertIsNotNone(stored_request)
            self.assertEqual(stored_request.approval_decision_id, payload["approval_decision_id"])
            self.assertEqual(stored_request.lifecycle_state, "approved")
            stored_decision = service.get_record(
                ApprovalDecisionRecord,
                payload["approval_decision_id"],
            )
            self.assertIsNotNone(stored_decision)
            self.assertEqual(
                stored_decision.approval_decision_id,
                payload["approval_decision_id"],
            )
            self.assertEqual(stored_decision.action_request_id, action_request.action_request_id)
            self.assertEqual(stored_decision.approver_identities, ("approver-001",))
            self.assertEqual(stored_decision.lifecycle_state, "approved")
            self.assertEqual(
                stored_decision.decision_rationale,
                "Approver validated the reviewed owner notification scope.",
            )
            self.assertEqual(stored_decision.decided_at, decided_at)
            self.assertEqual(stored_decision.approved_expires_at, action_request.expires_at)

            case_detail = json.loads(
                request.urlopen(  # noqa: S310
                    f"{base_url}/inspect-case-detail?case_id={stored_request.case_id}",
                    timeout=2,
                ).read().decode("utf-8")
            )
            self.assertEqual(
                case_detail["current_action_review"]["decision_rationale"],
                "Approver validated the reviewed owner notification scope.",
            )
            self.assertEqual(
                case_detail["current_action_review"]["timeline"][1]["details"][
                    "decision_rationale"
                ],
                "Approver validated the reviewed owner notification scope.",
            )

    def test_reviewed_runtime_path_records_live_reject_decision(self) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(
            service,
            action_request_id="action-request-phase23-live-reject-001",
        )
        approval_decision_id = "approval-phase23-live-reject-001"
        decision_rationale = (
            "Approver rejected the notification because the reviewed evidence is incomplete."
        )
        decided_at = action_request.requested_at + timedelta(minutes=10)

        with self._run_runtime(service) as (base_url, _authenticate_mock):
            response = request.urlopen(  # noqa: S310
                request.Request(  # noqa: S310
                    f"{base_url}/operator/record-action-approval-decision",
                    data=json.dumps(
                        {
                            "action_request_id": action_request.action_request_id,
                            "approval_decision_id": approval_decision_id,
                            "decision": "reject",
                            "approver_identity": "approver-001",
                            "decision_rationale": decision_rationale,
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
            self.assertEqual(payload["lifecycle_state"], "rejected")
            self.assertIsNone(payload["approved_expires_at"])
            stored_request = service.get_record(
                type(action_request),
                action_request.action_request_id,
            )
            self.assertIsNotNone(stored_request)
            self.assertEqual(stored_request.approval_decision_id, approval_decision_id)
            self.assertEqual(stored_request.lifecycle_state, "rejected")
            stored_decision = service.get_record(
                ApprovalDecisionRecord,
                approval_decision_id,
            )
            self.assertIsNotNone(stored_decision)
            self.assertEqual(stored_decision.action_request_id, action_request.action_request_id)
            self.assertEqual(stored_decision.approver_identities, ("approver-001",))
            self.assertEqual(stored_decision.lifecycle_state, "rejected")
            self.assertEqual(stored_decision.decision_rationale, decision_rationale)
            self.assertEqual(stored_decision.decided_at, decided_at)
            self.assertIsNone(stored_decision.approved_expires_at)

    def test_reviewed_runtime_path_records_decisions_with_serializable_transaction(
        self,
    ) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(
            service,
            action_request_id="action-request-phase23-serializable-001",
        )

        with mock.patch.object(
            service._store,
            "transaction",
            wraps=service._store.transaction,
        ) as transaction_mock:
            with self._run_runtime(service) as (base_url, _authenticate_mock):
                response = request.urlopen(  # noqa: S310
                    request.Request(  # noqa: S310
                        f"{base_url}/operator/record-action-approval-decision",
                        data=json.dumps(
                            {
                                "action_request_id": action_request.action_request_id,
                                "approval_decision_id": "approval-phase23-serializable-001",
                                "decision": "grant",
                                "approver_identity": "approver-001",
                                "decision_rationale": "Decision writes must hold the strongest transaction boundary in this path.",
                                "decided_at": (
                                    action_request.requested_at + timedelta(minutes=10)
                                ).isoformat(),
                            }
                        ).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=2,
                )

            self.assertEqual(response.status, HTTPStatus.OK)
            self.assertTrue(
                any(
                    call.kwargs.get("isolation_level") == "SERIALIZABLE"
                    for call in transaction_mock.call_args_list
                )
            )

    def test_reviewed_runtime_path_rejects_self_approval(self) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(
            service,
            requester_identity="approver-001",
            action_request_id="action-request-phase23-self-approval-001",
        )

        with self._run_runtime(service) as (base_url, _authenticate_mock):
            with self.assertRaises(error.HTTPError) as exc_info:
                request.urlopen(  # noqa: S310
                    request.Request(  # noqa: S310
                        f"{base_url}/operator/record-action-approval-decision",
                        data=json.dumps(
                            {
                                "action_request_id": action_request.action_request_id,
                                "approval_decision_id": "approval-phase23-self-approval-001",
                                "decision": "grant",
                                "approver_identity": "approver-001",
                                "decision_rationale": "Self approval must fail closed.",
                                "decided_at": (
                                    action_request.requested_at + timedelta(minutes=5)
                                ).isoformat(),
                            }
                        ).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=2,
                )
            self.assertEqual(exc_info.exception.code, HTTPStatus.FORBIDDEN)
            stored_request = service.get_record(
                type(action_request),
                action_request.action_request_id,
            )
            self.assertIsNotNone(stored_request)
            self.assertIsNone(stored_request.approval_decision_id)
            self.assertEqual(stored_request.lifecycle_state, "pending_approval")
            self.assertIsNone(
                service.get_record(
                    ApprovalDecisionRecord,
                    "approval-phase23-self-approval-001",
                )
            )

    def test_reviewed_runtime_path_rejects_analyst_decision_authority(self) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(
            service,
            action_request_id="action-request-phase23-analyst-authority-001",
        )

        with self._run_runtime(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
        ) as (base_url, authenticate_mock):
            with self.assertRaises(error.HTTPError) as exc_info:
                request.urlopen(  # noqa: S310
                    request.Request(  # noqa: S310
                        f"{base_url}/operator/record-action-approval-decision",
                        data=json.dumps(
                            {
                                "action_request_id": action_request.action_request_id,
                                "approval_decision_id": "approval-phase23-analyst-authority-001",
                                "decision": "grant",
                                "approver_identity": "analyst-002",
                                "decision_rationale": "Analysts must not record approval decisions.",
                                "decided_at": (
                                    action_request.requested_at + timedelta(minutes=10)
                                ).isoformat(),
                            }
                        ).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=2,
                )

            self.assertEqual(exc_info.exception.code, HTTPStatus.FORBIDDEN)
            error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
            self.assertEqual(error_payload["error"], "forbidden")
            self.assertIn("approver role authority", error_payload["message"])
            self.assertEqual(
                authenticate_mock.call_args_list[0].kwargs["allowed_roles"],
                ("analyst", "approver", "platform_admin"),
            )
            stored_request = service.get_record(
                type(action_request),
                action_request.action_request_id,
            )
            self.assertIsNotNone(stored_request)
            self.assertIsNone(stored_request.approval_decision_id)
            self.assertEqual(stored_request.lifecycle_state, "pending_approval")
            self.assertIsNone(
                service.get_record(
                    ApprovalDecisionRecord,
                    "approval-phase23-analyst-authority-001",
                )
            )

    def test_reviewed_runtime_path_rejects_approver_outside_request_policy(self) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(
            service,
            action_request_id="action-request-phase23-approver-policy-001",
        )
        action_request = service.persist_record(
            replace(
                action_request,
                policy_evaluation={
                    **dict(action_request.policy_evaluation),
                    "authorized_approver_identities": ("approver-001",),
                },
            )
        )

        with self._run_runtime(
            service,
            principal=REVIEWED_SECONDARY_APPROVER_PRINCIPAL,
        ) as (base_url, _authenticate_mock):
            with self.assertRaises(error.HTTPError) as exc_info:
                request.urlopen(  # noqa: S310
                    request.Request(  # noqa: S310
                        f"{base_url}/operator/record-action-approval-decision",
                        data=json.dumps(
                            {
                                "action_request_id": action_request.action_request_id,
                                "approval_decision_id": "approval-phase23-approver-policy-001",
                                "decision": "grant",
                                "approver_identity": "approver-002",
                                "decision_rationale": "Approver must be denied outside the request policy.",
                                "decided_at": (
                                    action_request.requested_at + timedelta(minutes=10)
                                ).isoformat(),
                            }
                        ).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=2,
                )

            self.assertEqual(exc_info.exception.code, HTTPStatus.FORBIDDEN)
            error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
            self.assertEqual(error_payload["error"], "forbidden")
            self.assertIn("not authorized", error_payload["message"])
            stored_request = service.get_record(
                type(action_request),
                action_request.action_request_id,
            )
            self.assertIsNotNone(stored_request)
            self.assertIsNone(stored_request.approval_decision_id)
            self.assertEqual(stored_request.lifecycle_state, "pending_approval")
            self.assertIsNone(
                service.get_record(
                    ApprovalDecisionRecord,
                    "approval-phase23-approver-policy-001",
                )
            )

    def test_reviewed_runtime_path_rejects_mismatched_approver_identity_assertion(
        self,
    ) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(
            service,
            action_request_id="action-request-phase23-auth-identity-mismatch-001",
        )
        direct_approver_principal = AuthenticatedRuntimePrincipal(
            identity="approver-001",
            role="approver",
            access_path="loopback_direct",
        )

        with self._run_runtime(
            service,
            principal=direct_approver_principal,
        ) as (base_url, _authenticate_mock):
            with self.assertRaises(error.HTTPError) as exc_info:
                request.urlopen(  # noqa: S310
                    request.Request(  # noqa: S310
                        f"{base_url}/operator/record-action-approval-decision",
                        data=json.dumps(
                            {
                                "action_request_id": action_request.action_request_id,
                                "approval_decision_id": "approval-phase23-auth-identity-mismatch-001",
                                "decision": "grant",
                                "approver_identity": "approver-002",
                                "decision_rationale": "Authenticated approvers must not impersonate other approvers.",
                                "decided_at": (
                                    action_request.requested_at + timedelta(minutes=10)
                                ).isoformat(),
                            }
                        ).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=2,
                )

            self.assertEqual(exc_info.exception.code, HTTPStatus.FORBIDDEN)
            error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
            self.assertEqual(error_payload["error"], "forbidden")
            self.assertIn("authenticated identity", error_payload["message"])
            stored_request = service.get_record(
                type(action_request),
                action_request.action_request_id,
            )
            self.assertIsNotNone(stored_request)
            self.assertIsNone(stored_request.approval_decision_id)
            self.assertEqual(stored_request.lifecycle_state, "pending_approval")
            self.assertIsNone(
                service.get_record(
                    ApprovalDecisionRecord,
                    "approval-phase23-auth-identity-mismatch-001",
                )
            )

    def test_reviewed_runtime_path_rejects_expired_request_decisions(self) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(
            service,
            action_request_id="action-request-phase23-expired-decision-001",
        )
        expires_at = action_request.requested_at + timedelta(minutes=1)
        action_request = service.persist_record(
            replace(
                action_request,
                expires_at=expires_at,
            )
        )

        with self._run_runtime(service) as (base_url, _authenticate_mock):
            with self.assertRaises(error.HTTPError) as exc_info:
                request.urlopen(  # noqa: S310
                    request.Request(  # noqa: S310
                        f"{base_url}/operator/record-action-approval-decision",
                        data=json.dumps(
                            {
                                "action_request_id": action_request.action_request_id,
                                "approval_decision_id": "approval-phase23-expired-decision-001",
                                "decision": "grant",
                                "approver_identity": "approver-001",
                                "decision_rationale": "Expired requests must fail closed at decision time.",
                                "decided_at": (
                                    action_request.requested_at + timedelta(minutes=5)
                                ).isoformat(),
                            }
                        ).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=2,
                )

            self.assertEqual(exc_info.exception.code, HTTPStatus.FORBIDDEN)
            error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
            self.assertEqual(error_payload["error"], "forbidden")
            self.assertIn("expired", error_payload["message"])
            stored_request = service.get_record(
                type(action_request),
                action_request.action_request_id,
            )
            self.assertIsNotNone(stored_request)
            self.assertIsNone(stored_request.approval_decision_id)
            self.assertEqual(stored_request.lifecycle_state, "expired")
            self.assertIsNone(
                service.get_record(
                    ApprovalDecisionRecord,
                    "approval-phase23-expired-decision-001",
                )
            )

    def test_reviewed_runtime_path_rejects_re_evaluated_policy_authorized_decisions(
        self,
    ) -> None:
        service = self._build_service()
        action_request = self._build_pending_action_request(
            service,
            action_request_id="action-request-phase23-policy-authorized-001",
        )
        action_request = service.persist_record(
            replace(
                action_request,
                policy_evaluation={
                    key: value
                    for key, value in dict(action_request.policy_evaluation).items()
                    if key != "approval_requirement_override"
                },
            )
        )

        with self._run_runtime(service) as (base_url, _authenticate_mock):
            with self.assertRaises(error.HTTPError) as exc_info:
                request.urlopen(  # noqa: S310
                    request.Request(  # noqa: S310
                        f"{base_url}/operator/record-action-approval-decision",
                        data=json.dumps(
                            {
                                "action_request_id": action_request.action_request_id,
                                "approval_decision_id": "approval-phase23-policy-authorized-001",
                                "decision": "grant",
                                "approver_identity": "approver-001",
                                "decision_rationale": "Policy-authorized requests must reject redundant approval decisions.",
                                "decided_at": (
                                    action_request.requested_at + timedelta(minutes=10)
                                ).isoformat(),
                            }
                        ).encode("utf-8"),
                        headers={"Content-Type": "application/json"},
                        method="POST",
                    ),
                    timeout=2,
                )

            self.assertEqual(exc_info.exception.code, HTTPStatus.FORBIDDEN)
            error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
            self.assertEqual(error_payload["error"], "forbidden")
            self.assertIn("policy_authorized", error_payload["message"])
            stored_request = service.get_record(
                type(action_request),
                action_request.action_request_id,
            )
            self.assertIsNotNone(stored_request)
            self.assertIsNone(stored_request.approval_decision_id)
            self.assertEqual(stored_request.lifecycle_state, "pending_approval")
            self.assertIsNone(
                service.get_record(
                    ApprovalDecisionRecord,
                    "approval-phase23-policy-authorized-001",
                )
            )
