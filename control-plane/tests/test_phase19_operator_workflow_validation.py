from __future__ import annotations

from copy import deepcopy
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

import main
from aegisops_control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import AITraceRecord, CaseRecord, RecommendationRecord
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


FIXTURES_ROOT = pathlib.Path(__file__).resolve().parent / "fixtures" / "wazuh"
REVIEWED_SHARED_SECRET = "reviewed-shared-secret"  # noqa: S105
REVIEWED_PROXY_SECRET = "reviewed-proxy-secret"  # noqa: S105


def _load_wazuh_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


class Phase19OperatorWorkflowValidationTests(unittest.TestCase):
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

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
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
                handoff = post_json(
                    "/operator/record-case-handoff",
                    {
                        "case_id": case_id,
                        "handoff_at": "2026-04-07T17:45:00+00:00",
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
                        "recorded_at": "2026-04-07T17:45:00+00:00",
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

                closed_case = post_json(
                    "/operator/record-case-disposition",
                    {
                        "case_id": case_id,
                        "disposition": "closed_resolved",
                        "rationale": "Repository owner membership review completed and documented for this alert.",
                        "recorded_at": "2026-04-08T09:15:00+00:00",
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

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer):
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
                ):
                    with self.subTest(path=path):
                        payload = get_error_payload(path)
                        self.assertEqual(payload["error"], "invalid_request")
                        self.assertIn(
                            "outside the approved Phase 19 Wazuh-backed GitHub audit live slice",
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
                            "outside the approved Phase 19 Wazuh-backed GitHub audit live slice",
                            payload["message"],
                        )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)


if __name__ == "__main__":
    unittest.main()
