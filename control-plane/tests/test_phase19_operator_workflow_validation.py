from __future__ import annotations

import contextlib
from copy import deepcopy
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import json
import pathlib
import sys
import threading
import unittest
from urllib import error, request
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import main
from aegisops.control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import (
    AITraceRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    RecommendationRecord,
)
from aegisops.control_plane.service import (
    AegisOpsControlPlaneService,
    AuthenticatedRuntimePrincipal,
)
from postgres_test_support import make_store
from support.fixtures import load_wazuh_fixture


REVIEWED_SHARED_SECRET = "reviewed-shared-secret"  # noqa: S105
REVIEWED_PROXY_SECRET = "reviewed-proxy-secret"  # noqa: S105
REVIEWED_PROXY_SERVICE_ACCOUNT = "svc-aegisops-proxy-control-plane"
REVIEWED_ANALYST_PRINCIPAL = AuthenticatedRuntimePrincipal(
    identity="analyst-001",
    role="analyst",
    access_path="reviewed_reverse_proxy",
    proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
)
REVIEWED_PLATFORM_ADMIN_PRINCIPAL = AuthenticatedRuntimePrincipal(
    identity="platform-admin-001",
    role="platform_admin",
    access_path="reviewed_reverse_proxy",
    proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
)


_load_wazuh_fixture = load_wazuh_fixture


class Phase19OperatorWorkflowValidationTests(unittest.TestCase):
    @staticmethod
    @contextlib.contextmanager
    def _mock_authenticated_surface_access(
        service: AegisOpsControlPlaneService,
        *,
        principal: AuthenticatedRuntimePrincipal = REVIEWED_ANALYST_PRINCIPAL,
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
        ):
            yield

    def test_reviewed_runtime_path_covers_approved_operator_workflow(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

        created_alert = _load_wazuh_fixture("github-audit-alert.json")
        restated_alert = deepcopy(created_alert)
        restated_alert["id"] = "1731596200.1234568"
        restated_alert["timestamp"] = "2026-04-05T12:35:00+00:00"
        deduplicated_alert = deepcopy(restated_alert)

        created = service.ingest_wazuh_alert(
            raw_alert=created_alert,
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        service.ingest_wazuh_alert(
            raw_alert=restated_alert,
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        service.ingest_wazuh_alert(
            raw_alert=deduplicated_alert,
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"

                def get_json(path: str) -> dict[str, object]:
                    response = request.urlopen(f"{base_url}{path}", timeout=2)  # noqa: S310
                    return json.loads(response.read().decode("utf-8"))

                def post_json(path: str, payload: dict[str, object]) -> dict[str, object]:
                    response = request.urlopen(  # noqa: S310
                        request.Request(  # noqa: S310
                            f"{base_url}{path}",
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=2,
                    )
                    return json.loads(response.read().decode("utf-8"))

                queue_payload = get_json("/inspect-analyst-queue")
                self.assertTrue(queue_payload["read_only"])
                self.assertEqual(queue_payload["queue_name"], "analyst_review")
                self.assertEqual(queue_payload["total_records"], 1)
                self.assertEqual(queue_payload["records"][0]["alert_id"], created.alert.alert_id)
                self.assertEqual(queue_payload["records"][0]["queue_selection"], "business_hours_triage")
                self.assertEqual(queue_payload["records"][0]["review_state"], "pending_review")
                self.assertIsNone(queue_payload["records"][0]["case_id"])
                self.assertEqual(queue_payload["records"][0]["source_system"], "wazuh")
                self.assertEqual(
                    queue_payload["records"][0]["substrate_detection_record_ids"],
                    ["wazuh:1731595300.1234567", "wazuh:1731596200.1234568"],
                )
                self.assertEqual(
                    queue_payload["records"][0]["accountable_source_identities"],
                    ["manager:wazuh-manager-github-1"],
                )
                self.assertEqual(
                    queue_payload["records"][0]["reviewed_context"]["source"]["source_family"],
                    "github_audit",
                )

                promoted_case = post_json(
                    "/operator/promote-alert-to-case",
                    {"alert_id": created.alert.alert_id},
                )
                case_id = str(promoted_case["case_id"])
                self.assertEqual(promoted_case["lifecycle_state"], "open")

                queue_after_promotion = get_json("/inspect-analyst-queue")
                self.assertEqual(queue_after_promotion["records"][0]["case_id"], case_id)
                self.assertEqual(
                    queue_after_promotion["records"][0]["case_lifecycle_state"],
                    "open",
                )
                self.assertEqual(
                    queue_after_promotion["records"][0]["review_state"],
                    "case_required",
                )

                alert_detail = get_json(f"/inspect-alert-detail?alert_id={created.alert.alert_id}")
                self.assertTrue(alert_detail["read_only"])
                self.assertEqual(alert_detail["alert"]["case_id"], case_id)
                self.assertEqual(alert_detail["case_record"]["case_id"], case_id)
                self.assertEqual(
                    alert_detail["provenance"],
                    {
                        "admission_kind": "live",
                        "admission_channel": "live_wazuh_webhook",
                    },
                )
                self.assertEqual(
                    alert_detail["lineage"]["substrate_detection_record_ids"],
                    ["wazuh:1731595300.1234567", "wazuh:1731596200.1234568"],
                )
                self.assertEqual(
                    alert_detail["lineage"]["accountable_source_identities"],
                    ["manager:wazuh-manager-github-1"],
                )
                self.assertEqual(
                    alert_detail["reviewed_context"]["source"]["source_family"],
                    "github_audit",
                )
                self.assertGreaterEqual(len(alert_detail["linked_evidence_records"]), 1)
                live_evidence_records = [
                    record
                    for record in alert_detail["linked_evidence_records"]
                    if record["collector_identity"] == "wazuh-native-detection-adapter"
                    and record["derivation_relationship"] == "native_detection_record"
                    and record["source_system"] == "wazuh"
                ]
                self.assertTrue(
                    live_evidence_records,
                    "expected at least one live Wazuh evidence record in alert detail",
                )
                evidence_id = str(live_evidence_records[0]["evidence_id"])

                observation = post_json(
                    "/operator/record-case-observation",
                    {
                        "case_id": case_id,
                        "author_identity": "analyst-001",
                        "observed_at": "2026-04-07T09:30:00+00:00",
                        "scope_statement": "Observed repository permission change requires tracked review.",
                        "supporting_evidence_ids": [evidence_id],
                    },
                )
                lead = post_json(
                    "/operator/record-case-lead",
                    {
                        "case_id": case_id,
                        "triage_owner": "analyst-001",
                        "triage_rationale": "Privilege-impacting change needs durable business-hours follow-up.",
                        "observation_id": observation["observation_id"],
                    },
                )
                recommendation = post_json(
                    "/operator/record-case-recommendation",
                    {
                        "case_id": case_id,
                        "review_owner": "analyst-001",
                        "intended_outcome": "Review repository owner change evidence before any approval-bound response.",
                        "lead_id": lead["lead_id"],
                    },
                )
                handoff_at = (
                    service.list_lifecycle_transitions("case", case_id)[-1]
                    .transitioned_at
                    + timedelta(minutes=5)
                ).isoformat()
                handoff = post_json(
                    "/operator/record-case-handoff",
                    {
                        "case_id": case_id,
                        "handoff_at": handoff_at,
                        "handoff_owner": "analyst-001",
                        "handoff_note": "Recheck repository owner membership against approved change window at next business-hours review.",
                        "follow_up_evidence_ids": [evidence_id],
                    },
                )
                disposition = post_json(
                    "/operator/record-case-disposition",
                    {
                        "case_id": case_id,
                        "disposition": "business_hours_handoff",
                        "rationale": "No same-day response required; preserve next-shift context and keep case open.",
                        "recorded_at": handoff_at,
                    },
                )

                self.assertEqual(observation["supporting_evidence_ids"], [evidence_id])
                self.assertEqual(lead["observation_id"], observation["observation_id"])
                self.assertEqual(recommendation["lead_id"], lead["lead_id"])
                self.assertEqual(
                    handoff["reviewed_context"]["handoff"]["follow_up_evidence_ids"],
                    [evidence_id],
                )
                self.assertEqual(disposition["lifecycle_state"], "pending_action")

                case_detail = get_json(f"/inspect-case-detail?case_id={case_id}")
                self.assertTrue(case_detail["read_only"])
                self.assertEqual(case_detail["case_record"]["case_id"], case_id)
                self.assertEqual(case_detail["case_record"]["lifecycle_state"], "pending_action")
                self.assertEqual(case_detail["linked_alert_ids"], [created.alert.alert_id])
                self.assertEqual(case_detail["linked_observation_ids"], [observation["observation_id"]])
                self.assertEqual(case_detail["linked_lead_ids"], [lead["lead_id"]])
                self.assertIn(evidence_id, case_detail["linked_evidence_ids"])
                self.assertIn(
                    recommendation["recommendation_id"],
                    case_detail["linked_recommendation_ids"],
                )
                self.assertEqual(
                    case_detail["reviewed_context"]["handoff"]["note"],
                    "Recheck repository owner membership against approved change window at next business-hours review.",
                )
                self.assertEqual(
                    case_detail["reviewed_context"]["triage"]["disposition"],
                    "business_hours_handoff",
                )
                self.assertEqual(
                    case_detail["advisory_output"]["output_kind"],
                    "case_summary",
                )
                self.assertEqual(case_detail["advisory_output"]["status"], "ready")
                self.assertIn(evidence_id, case_detail["advisory_output"]["citations"])
                self.assertIn(created.alert.alert_id, case_detail["advisory_output"]["citations"])
                self.assertIn(case_id, case_detail["advisory_output"]["citations"])

                assistant_context = get_json(
                    f"/inspect-assistant-context?family=case&record_id={case_id}"
                )
                self.assertTrue(assistant_context["read_only"])
                self.assertEqual(assistant_context["record_family"], "case")
                self.assertEqual(assistant_context["record_id"], case_id)
                self.assertEqual(
                    assistant_context["advisory_output"]["output_kind"],
                    "case_summary",
                )
                self.assertIn(evidence_id, assistant_context["linked_evidence_ids"])
                self.assertIn(
                    recommendation["recommendation_id"],
                    assistant_context["linked_recommendation_ids"],
                )

                advisory_output = get_json(
                    f"/inspect-advisory-output?family=case&record_id={case_id}"
                )
                self.assertTrue(advisory_output["read_only"])
                self.assertEqual(advisory_output["record_family"], "case")
                self.assertEqual(advisory_output["record_id"], case_id)
                self.assertEqual(advisory_output["output_kind"], "case_summary")
                self.assertEqual(advisory_output["status"], "ready")
                self.assertIn(evidence_id, advisory_output["citations"])
                self.assertIn(created.alert.alert_id, advisory_output["citations"])

                recommendation_draft = get_json(
                    f"/render-recommendation-draft?family=case&record_id={case_id}"
                )
                self.assertTrue(recommendation_draft["read_only"])
                self.assertEqual(recommendation_draft["record_family"], "case")
                self.assertEqual(recommendation_draft["record_id"], case_id)
                self.assertEqual(
                    recommendation_draft["recommendation_draft"]["source_output_kind"],
                    "case_summary",
                )
                self.assertEqual(
                    recommendation_draft["recommendation_draft"]["status"],
                    "ready",
                )
                self.assertIn(
                    recommendation["recommendation_id"],
                    recommendation_draft["linked_recommendation_ids"],
                )

                action_request = post_json(
                    "/operator/create-reviewed-action-request",
                    {
                        "family": "recommendation",
                        "record_id": recommendation["recommendation_id"],
                        "requester_identity": "analyst-001",
                        "recipient_identity": "repo-owner-001",
                        "message_intent": "Notify the accountable repository owner about the reviewed permission change.",
                        "escalation_reason": "Reviewed GitHub audit evidence requires bounded owner notification.",
                        "expires_at": (
                            datetime.now(timezone.utc) + timedelta(hours=4)
                        ).isoformat(),
                    },
                )
                self.assertEqual(action_request["case_id"], case_id)
                self.assertEqual(action_request["alert_id"], created.alert.alert_id)
                self.assertEqual(action_request["requester_identity"], "analyst-001")
                self.assertEqual(action_request["lifecycle_state"], "pending_approval")
                self.assertEqual(
                    action_request["policy_evaluation"],
                    {
                        "approval_requirement": "human_required",
                        "approval_requirement_override": "human_required",
                        "routing_target": "approval",
                        "execution_surface_type": "automation_substrate",
                        "execution_surface_id": "shuffle",
                    },
                )
                self.assertEqual(
                    action_request["requested_payload"]["action_type"],
                    "notify_identity_owner",
                )
                self.assertEqual(
                    action_request["requested_payload"]["recommendation_id"],
                    recommendation["recommendation_id"],
                )

                queue_with_pending_action = get_json("/inspect-analyst-queue")
                self.assertEqual(
                    queue_with_pending_action["records"][0]["current_action_review"][
                        "review_state"
                    ],
                    "pending",
                )
                self.assertEqual(
                    queue_with_pending_action["records"][0]["current_action_review"][
                        "action_request_id"
                    ],
                    action_request["action_request_id"],
                )
                self.assertEqual(
                    queue_with_pending_action["records"][0]["current_action_review"][
                        "requester_identity"
                    ],
                    "analyst-001",
                )
                self.assertEqual(
                    queue_with_pending_action["records"][0]["current_action_review"][
                        "approval_state"
                    ],
                    "pending",
                )
                self.assertEqual(
                    queue_with_pending_action["records"][0]["current_action_review"][
                        "next_expected_action"
                    ],
                    "await_approver_decision",
                )

                alert_detail_with_pending_action = get_json(
                    f"/inspect-alert-detail?alert_id={created.alert.alert_id}"
                )
                self.assertEqual(
                    alert_detail_with_pending_action["current_action_review"][
                        "review_state"
                    ],
                    "pending",
                )
                self.assertEqual(
                    alert_detail_with_pending_action["action_reviews"][0][
                        "action_request_state"
                    ],
                    "pending_approval",
                )
                self.assertEqual(
                    alert_detail_with_pending_action["action_reviews"][0][
                        "requester_identity"
                    ],
                    "analyst-001",
                )
                self.assertEqual(
                    alert_detail_with_pending_action["action_reviews"][0][
                        "requested_payload"
                    ]["action_type"],
                    "notify_identity_owner",
                )

                case_detail_with_pending_action = get_json(
                    f"/inspect-case-detail?case_id={case_id}"
                )
                self.assertEqual(
                    case_detail_with_pending_action["current_action_review"][
                        "review_state"
                    ],
                    "pending",
                )
                self.assertEqual(
                    case_detail_with_pending_action["action_reviews"][0][
                        "action_request_id"
                    ],
                    action_request["action_request_id"],
                )
                self.assertEqual(
                    case_detail_with_pending_action["action_reviews"][0]["expires_at"],
                    action_request["expires_at"],
                )
                self.assertEqual(
                    case_detail_with_pending_action["action_reviews"][0][
                        "recommendation_id"
                    ],
                    recommendation["recommendation_id"],
                )

                closure_at = (
                    service.list_lifecycle_transitions("case", case_id)[-1]
                    .transitioned_at
                    + timedelta(minutes=5)
                ).isoformat()
                closed_case = post_json(
                    "/operator/record-case-disposition",
                    {
                        "case_id": case_id,
                        "disposition": "closed_resolved",
                        "rationale": "Repository owner membership review completed and documented for this alert.",
                        "recorded_at": closure_at,
                    },
                )
                self.assertEqual(closed_case["lifecycle_state"], "closed")

                closed_case_detail = get_json(f"/inspect-case-detail?case_id={case_id}")
                self.assertTrue(closed_case_detail["read_only"])
                self.assertEqual(closed_case_detail["case_record"]["case_id"], case_id)
                self.assertEqual(closed_case_detail["case_record"]["lifecycle_state"], "closed")
                self.assertEqual(
                    closed_case_detail["case_record"]["reviewed_context"]["triage"]["disposition"],
                    "closed_resolved",
                )
                self.assertEqual(
                    closed_case_detail["case_record"]["reviewed_context"]["triage"]["closure_rationale"],
                    "Repository owner membership review completed and documented for this alert.",
                )
                self.assertEqual(
                    closed_case_detail["linked_alert_ids"],
                    [created.alert.alert_id],
                )
                self.assertEqual(
                    closed_case_detail["linked_observation_ids"],
                    [observation["observation_id"]],
                )
                self.assertEqual(closed_case_detail["linked_lead_ids"], [lead["lead_id"]])
                self.assertIn(evidence_id, closed_case_detail["linked_evidence_ids"])
                self.assertIn(
                    recommendation["recommendation_id"],
                    closed_case_detail["linked_recommendation_ids"],
                )
                self.assertEqual(
                    closed_case_detail["advisory_output"]["output_kind"],
                    "case_summary",
                )
                self.assertEqual(closed_case_detail["advisory_output"]["status"], "ready")
                self.assertIn(
                    evidence_id,
                    closed_case_detail["advisory_output"]["citations"],
                )
                self.assertIn(
                    created.alert.alert_id,
                    closed_case_detail["advisory_output"]["citations"],
                )
                self.assertIn(case_id, closed_case_detail["advisory_output"]["citations"])
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_reviewed_runtime_path_exposes_live_entra_id_case_through_existing_operator_surface(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("entra-id-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"

                def post_json(path: str, payload: dict[str, object]) -> dict[str, object]:
                    response = request.urlopen(  # noqa: S310
                        request.Request(  # noqa: S310
                            f"{base_url}{path}",
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=2,
                    )
                    return json.loads(response.read().decode("utf-8"))

                queue_payload = json.loads(
                    request.urlopen(  # noqa: S310
                        f"{base_url}/inspect-analyst-queue",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                case_payload = json.loads(
                    request.urlopen(  # noqa: S310
                        f"{base_url}/inspect-case-detail?case_id={promoted_case.case_id}",
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertEqual(queue_payload["total_records"], 1)
                self.assertEqual(
                    queue_payload["records"][0]["reviewed_context"]["source"]["source_family"],
                    "entra_id",
                )
                self.assertEqual(case_payload["case_id"], promoted_case.case_id)
                self.assertEqual(
                    case_payload["reviewed_context"]["source"]["source_family"],
                    "entra_id",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_reviewed_runtime_path_fail_closes_replayed_reviewed_family_queue_summary(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
            ),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("github-audit-alert.json")
            ),
        )
        service._assistant_provider_adapter = mock.Mock()

        with self.assertRaisesRegex(
            ValueError,
            rf"alert {admitted.alert.alert_id!r} is outside the approved .* live slice",
        ):
            service.run_live_assistant_workflow(
                workflow_task="queue_triage_summary",
                record_family="alert",
                record_id=admitted.alert.alert_id,
            )

        service._assistant_provider_adapter.generate.assert_not_called()

    def test_reviewed_runtime_path_surfaces_handoff_and_manual_fallback_visibility(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        reviewed_at = admitted.reconciliation.compared_at
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Waiting until the next business-hours cycle is unsafe for this repository owner change.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase19-runtime-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase19-runtime-visibility-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        promoted_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the unresolved approval review at next business-hours open.",
            follow_up_evidence_ids=promoted_case.evidence_ids,
        )
        promoted_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Keep the unresolved action visible for the next analyst handoff.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"

                def post_json(path: str, payload: dict[str, object]) -> dict[str, object]:
                    response = request.urlopen(  # noqa: S310
                        request.Request(  # noqa: S310
                            f"{base_url}{path}",
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=2,
                    )
                    return json.loads(response.read().decode("utf-8"))

                post_json(
                    "/operator/record-action-review-manual-fallback",
                    {
                        "action_request_id": action_request.action_request_id,
                        "fallback_at": (reviewed_at + timedelta(minutes=45)).isoformat(),
                        "fallback_actor_identity": "analyst-001",
                        "authority_boundary": "approved_human_fallback",
                        "reason": "The reviewed automation path was unavailable after approval.",
                        "action_taken": "Notified the accountable repository owner using the approved manual procedure.",
                        "verification_evidence_ids": list(promoted_case.evidence_ids),
                        "residual_uncertainty": "Awaiting written owner acknowledgement.",
                    },
                )
                post_json(
                    "/operator/record-action-review-escalation-note",
                    {
                        "action_request_id": action_request.action_request_id,
                        "escalated_at": (reviewed_at + timedelta(minutes=15)).isoformat(),
                        "escalated_by_identity": "analyst-001",
                        "escalated_to": "on-call-manager-001",
                        "note": "On-call manager notified because the unresolved action could not be left unattended.",
                    },
                )
                queue_payload = json.loads(
                    request.urlopen(  # noqa: S310
                        f"{base_url}/inspect-analyst-queue",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                case_payload = json.loads(
                    request.urlopen(  # noqa: S310
                        f"{base_url}/inspect-case-detail?case_id={promoted_case.case_id}",
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertEqual(
                    queue_payload["records"][0]["current_action_review"]["runtime_visibility"][
                        "after_hours_handoff"
                    ]["handoff_owner"],
                    "analyst-002",
                )
                self.assertEqual(
                    queue_payload["records"][0]["current_action_review"]["runtime_visibility"][
                        "after_hours_handoff"
                    ]["rationale"],
                    "Keep the unresolved action visible for the next analyst handoff.",
                )
                self.assertEqual(
                    case_payload["current_action_review"]["runtime_visibility"][
                        "manual_fallback"
                    ]["fallback_actor_identity"],
                    "analyst-001",
                )
                self.assertEqual(
                    case_payload["current_action_review"]["runtime_visibility"][
                        "manual_fallback"
                    ]["fallback_at"],
                    (reviewed_at + timedelta(minutes=45)).isoformat(),
                )
                self.assertEqual(
                    case_payload["current_action_review"]["runtime_visibility"][
                        "escalation_notes"
                    ]["escalation_reason"],
                    "Waiting until the next business-hours cycle is unsafe for this repository owner change.",
                )
                self.assertEqual(
                    case_payload["current_action_review"]["runtime_visibility"][
                        "escalation_notes"
                    ]["escalated_by_identity"],
                    "analyst-001",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_reviewed_runtime_path_returns_not_found_for_missing_runtime_visibility_records(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

        service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"

                for path, payload in (
                    (
                        "/operator/record-action-review-manual-fallback",
                        {
                            "action_request_id": "missing-action-request-id",
                            "fallback_at": datetime.now(timezone.utc).isoformat(),
                            "fallback_actor_identity": "analyst-001",
                            "authority_boundary": "approved_human_fallback",
                            "reason": "Missing requests should produce the operator not-found envelope.",
                            "action_taken": "No fallback should be recorded.",
                            "verification_evidence_ids": [],
                        },
                    ),
                    (
                        "/operator/record-action-review-escalation-note",
                        {
                            "action_request_id": "missing-action-request-id",
                            "escalated_at": datetime.now(timezone.utc).isoformat(),
                            "escalated_by_identity": "analyst-001",
                            "escalated_to": "on-call-manager-001",
                            "note": "Missing requests should produce the operator not-found envelope.",
                        },
                    ),
                ):
                    with self.subTest(path=path):
                        with self.assertRaises(error.HTTPError) as exc_info:
                            request.urlopen(  # noqa: S310
                                request.Request(  # noqa: S310
                                    f"{base_url}{path}",
                                    data=json.dumps(payload).encode("utf-8"),
                                    headers={"Content-Type": "application/json"},
                                    method="POST",
                                ),
                                timeout=2,
                            )
                        self.assertEqual(exc_info.exception.code, 404)
                        error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
                        self.assertEqual(error_payload["error"], "not_found")
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_reviewed_runtime_path_rejects_mismatched_escalation_actor_identity(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep the reviewed escalation path attributable.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Escalate the reviewed repository owner change.",
            escalation_reason="Waiting until the next business-hours cycle is unsafe.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase19-escalation-identity-001",
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"

                with self.assertRaises(error.HTTPError) as exc_info:
                    request.urlopen(  # noqa: S310
                        request.Request(  # noqa: S310
                            f"{base_url}/operator/record-action-review-escalation-note",
                            data=json.dumps(
                                {
                                    "action_request_id": action_request.action_request_id,
                                    "escalated_at": (
                                        admitted.reconciliation.compared_at
                                        + timedelta(minutes=15)
                                    ).isoformat(),
                                    "escalated_by_identity": "analyst-002",
                                    "escalated_to": "on-call-manager-001",
                                    "note": "Mismatched reviewed identity should fail closed.",
                                }
                            ).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=2,
                    )
                self.assertEqual(exc_info.exception.code, 403)
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_reviewed_runtime_path_rejects_mismatched_manual_fallback_actor_identity(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep the reviewed fallback path attributable.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Use a reviewed manual fallback for the repository owner change.",
            escalation_reason="Waiting until the next business-hours cycle is unsafe.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase19-manual-fallback-identity-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase19-manual-fallback-identity-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=admitted.reconciliation.compared_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"

                with self.assertRaises(error.HTTPError) as exc_info:
                    request.urlopen(  # noqa: S310
                        request.Request(  # noqa: S310
                            f"{base_url}/operator/record-action-review-manual-fallback",
                            data=json.dumps(
                                {
                                    "action_request_id": action_request.action_request_id,
                                    "fallback_at": (
                                        admitted.reconciliation.compared_at
                                        + timedelta(minutes=15)
                                    ).isoformat(),
                                    "fallback_actor_identity": "analyst-002",
                                    "authority_boundary": "approved_human_fallback",
                                    "reason": "Mismatched reviewed identity should fail closed.",
                                    "action_taken": "No manual fallback should be accepted.",
                                    "verification_evidence_ids": list(promoted_case.evidence_ids),
                                }
                            ).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=2,
                    )
                self.assertEqual(exc_info.exception.code, 403)
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_reviewed_runtime_path_fails_closed_for_out_of_scope_case_reads(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        in_scope_case = service.promote_alert_to_case(admitted.alert.alert_id)
        in_scope_recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-workflow-live-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=in_scope_case.alert_id,
                case_id=in_scope_case.case_id,
                ai_trace_id="ai-trace-phase19-workflow-live-001",
                review_owner="reviewer-001",
                intended_outcome="Review cited evidence before any escalation-bound follow-up.",
                lifecycle_state="under_review",
            )
        )
        in_scope_ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase19-workflow-live-001",
                subject_linkage={
                    "recommendation_ids": (in_scope_recommendation.recommendation_id,)
                },
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=admitted.reconciliation.compared_at,
                material_input_refs=in_scope_case.evidence_ids,
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
            )
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"

                def get_json(path: str) -> dict[str, object]:
                    response = request.urlopen(f"{base_url}{path}", timeout=2)  # noqa: S310
                    return json.loads(response.read().decode("utf-8"))

                def get_error_payload(path: str) -> dict[str, object]:
                    with self.assertRaises(error.HTTPError) as exc_info:
                        request.urlopen(f"{base_url}{path}", timeout=2)  # noqa: S310
                    self.assertEqual(exc_info.exception.code, 400)
                    return json.loads(exc_info.exception.read().decode("utf-8"))

                for path, record_family, record_id in (
                    (
                        "/inspect-advisory-output",
                        "recommendation",
                        in_scope_recommendation.recommendation_id,
                    ),
                    (
                        "/inspect-advisory-output",
                        "ai_trace",
                        in_scope_ai_trace.ai_trace_id,
                    ),
                    (
                        "/render-recommendation-draft",
                        "recommendation",
                        in_scope_recommendation.recommendation_id,
                    ),
                    (
                        "/render-recommendation-draft",
                        "ai_trace",
                        in_scope_ai_trace.ai_trace_id,
                    ),
                ):
                    with self.subTest(path=path, record_family=record_family):
                        payload = get_json(
                            f"{path}?family={record_family}&record_id={record_id}"
                        )
                        self.assertTrue(payload["read_only"])
                        self.assertEqual(payload["record_family"], record_family)
                        self.assertEqual(payload["record_id"], record_id)
                        self.assertIn(in_scope_case.case_id, payload["linked_case_ids"])

                adapter = WazuhAlertAdapter()
                replay_admitted = service.ingest_native_detection_record(
                    adapter,
                    adapter.build_native_detection_record(
                        _load_wazuh_fixture("github-audit-alert.json")
                    ),
                )
                replay_case = service.promote_alert_to_case(replay_admitted.alert.alert_id)

                spoofed_case = service.persist_record(
                    CaseRecord(
                        case_id="case-phase19-workflow-spoofed-001",
                        alert_id=in_scope_case.alert_id,
                        finding_id=in_scope_case.finding_id,
                        evidence_ids=in_scope_case.evidence_ids,
                        lifecycle_state=in_scope_case.lifecycle_state,
                        reviewed_context=dict(in_scope_case.reviewed_context),
                    )
                )

                synthetic_recommendation = service.persist_record(
                    RecommendationRecord(
                        recommendation_id="recommendation-phase19-workflow-synthetic-001",
                        lead_id=None,
                        hunt_run_id=None,
                        alert_id=in_scope_case.alert_id,
                        case_id=in_scope_case.case_id,
                        ai_trace_id="ai-trace-phase19-workflow-synthetic-001",
                        review_owner="reviewer-001",
                        intended_outcome="Synthetic advisory reads must fail closed.",
                        lifecycle_state="under_review",
                        reviewed_context={
                            "source": {
                                "source_family": "synthetic_review_fixture",
                                "admission_kind": "replay",
                            }
                        },
                    )
                )
                synthetic_ai_trace = service.persist_record(
                    AITraceRecord(
                        ai_trace_id="ai-trace-phase19-workflow-synthetic-001",
                        subject_linkage={
                            "recommendation_ids": (
                                synthetic_recommendation.recommendation_id,
                            )
                        },
                        model_identity="gpt-5.4",
                        prompt_version="prompt-v1",
                        generated_at=admitted.reconciliation.compared_at,
                        material_input_refs=("fixture://synthetic-phase19-review",),
                        reviewer_identity="reviewer-001",
                        lifecycle_state="under_review",
                    )
                )

                for path in (
                    f"/inspect-case-detail?case_id={replay_case.case_id}",
                    (
                        "/inspect-assistant-context"
                        f"?family=case&record_id={replay_case.case_id}"
                    ),
                    f"/inspect-advisory-output?family=case&record_id={replay_case.case_id}",
                    (
                        "/render-recommendation-draft"
                        f"?family=case&record_id={replay_case.case_id}"
                    ),
                    f"/inspect-case-detail?case_id={spoofed_case.case_id}",
                    (
                        "/inspect-assistant-context"
                        f"?family=case&record_id={spoofed_case.case_id}"
                    ),
                    f"/inspect-advisory-output?family=case&record_id={spoofed_case.case_id}",
                    (
                        "/render-recommendation-draft"
                        f"?family=case&record_id={spoofed_case.case_id}"
                    ),
                ):
                    with self.subTest(path=path):
                        payload = get_error_payload(path)
                        self.assertEqual(payload["error"], "invalid_request")
                        self.assertIn(
                            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                            payload["message"],
                        )

                for path, record_family, record_id in (
                    (
                        "/inspect-advisory-output",
                        "recommendation",
                        synthetic_recommendation.recommendation_id,
                    ),
                    (
                        "/inspect-advisory-output",
                        "ai_trace",
                        synthetic_ai_trace.ai_trace_id,
                    ),
                    (
                        "/render-recommendation-draft",
                        "recommendation",
                        synthetic_recommendation.recommendation_id,
                    ),
                    (
                        "/render-recommendation-draft",
                        "ai_trace",
                        synthetic_ai_trace.ai_trace_id,
                    ),
                ):
                    with self.subTest(path=path, record_family=record_family):
                        payload = get_error_payload(
                            f"{path}?family={record_family}&record_id={record_id}"
                        )
                        self.assertEqual(payload["error"], "invalid_request")
                        self.assertIn(
                            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                            payload["message"],
                        )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_create_reviewed_action_request_rejects_platform_admin_identity(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

        created = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {REVIEWED_SHARED_SECRET}",
            forwarded_proto="https",
            reverse_proxy_secret_header=REVIEWED_PROXY_SECRET,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(created.alert.alert_id)
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Require a reviewed approval decision inside the runtime boundary.",
        )

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
            principal=REVIEWED_PLATFORM_ADMIN_PRINCIPAL,
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"
                with self.assertRaises(error.HTTPError) as request_error:
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        request.Request(  # noqa: S310 - local in-process test HTTP server
                            f"{base_url}/operator/create-reviewed-action-request",
                            data=json.dumps(
                                {
                                    "family": "recommendation",
                                    "record_id": recommendation.recommendation_id,
                                    "requester_identity": "platform-admin-001",
                                    "recipient_identity": "repo-owner-001",
                                    "message_intent": "Notify the accountable repository owner about the reviewed permission change.",
                                    "escalation_reason": "Platform administrators must not replace the reviewed analyst request path.",
                                    "expires_at": (
                                        datetime.now(timezone.utc) + timedelta(hours=4)
                                    ).isoformat(),
                                }
                            ).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=2,
                    )
                self.assertEqual(request_error.exception.code, 403)
                payload = json.loads(request_error.exception.read().decode("utf-8"))
                self.assertIn("expected one of: analyst", payload["message"])
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_reviewed_action_request_http_surface_rejects_blank_defaulted_fields(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=REVIEWED_PROXY_SECRET,
            ),
            store=store,
        )

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
            service
        ), mock.patch.object(
            service,
            "create_reviewed_action_request_from_advisory",
            wraps=service.create_reviewed_action_request_from_advisory,
        ) as create_notify_request, mock.patch.object(
            service,
            "create_reviewed_tracking_ticket_request_from_advisory",
            wraps=service.create_reviewed_tracking_ticket_request_from_advisory,
        ) as create_ticket_request:
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
                base_url = f"http://127.0.0.1:{servers[0].server_port}"

                def post_invalid(payload: dict[str, object]) -> dict[str, object]:
                    with self.assertRaises(error.HTTPError) as request_error:
                        request.urlopen(  # noqa: S310 - local in-process test HTTP server
                            request.Request(  # noqa: S310 - local in-process test HTTP server
                                f"{base_url}/operator/create-reviewed-action-request",
                                data=json.dumps(payload).encode("utf-8"),
                                headers={"Content-Type": "application/json"},
                                method="POST",
                            ),
                            timeout=2,
                        )
                    self.assertEqual(request_error.exception.code, 400)
                    return json.loads(request_error.exception.read().decode("utf-8"))

                blank_action_type_error = post_invalid(
                    {
                        "action_type": " ",
                        "family": "recommendation",
                        "record_id": "recommendation-blank-action-type",
                        "requester_identity": "analyst-001",
                    }
                )
                self.assertIn(
                    "action_type must be a non-empty string",
                    blank_action_type_error["message"],
                )

                blank_ticket_severity_error = post_invalid(
                    {
                        "action_type": "create_tracking_ticket",
                        "coordination_reference_id": "coord-ref-reviewed-ticket-003",
                        "coordination_target_type": "zammad",
                        "expires_at": (
                            datetime.now(timezone.utc) + timedelta(hours=4)
                        ).isoformat(),
                        "family": "recommendation",
                        "record_id": "recommendation-blank-ticket-severity",
                        "requester_identity": "analyst-001",
                        "ticket_description": "Track one reviewed daily follow-up.",
                        "ticket_severity": " ",
                        "ticket_title": "Track reviewed follow-up",
                    }
                )
                self.assertIn(
                    "ticket_severity must be a non-empty string",
                    blank_ticket_severity_error["message"],
                )
                create_notify_request.assert_not_called()
                create_ticket_request.assert_not_called()
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
