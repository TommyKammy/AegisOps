from __future__ import annotations

import contextlib
from dataclasses import replace
from datetime import datetime, timedelta, timezone
import http.client
import io
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
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops_control_plane.execution_coordinator import _approved_payload_binding_hash
from aegisops_control_plane.models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    AnalyticSignalRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    RecommendationRecord,
    ReconciliationRecord,
)
from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    AuthenticatedRuntimePrincipal,
)
from postgres_test_support import make_store
from support.auth import (
    REVIEWED_ANALYST_PRINCIPAL,
    REVIEWED_PLATFORM_ADMIN_PRINCIPAL,
    REVIEWED_PROXY_SERVICE_ACCOUNT,
)
from support.fixtures import load_wazuh_fixture
from support.payloads import phase26_create_tracking_ticket_payload


_load_wazuh_fixture = load_wazuh_fixture


class ControlPlaneCliInspectionTests(unittest.TestCase):
    @staticmethod
    @contextlib.contextmanager
    def _mock_authenticated_surface_access(
        service: AegisOpsControlPlaneService,
        *,
        principal: AuthenticatedRuntimePrincipal,
    ) -> object:
        with mock.patch.object(
            service,
            "authenticate_protected_surface_request",
            return_value=principal,
        ):
            yield

    def _build_phase19_in_scope_case(
        self,
        *,
        store: object | None = None,
        host: str | None = None,
        port: int | None = None,
    ) -> tuple[object, AegisOpsControlPlaneService, CaseRecord, str, datetime]:
        if store is None:
            store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1" if host is None else host,
                port=0 if port is None else port,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        reviewed_at = datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc)
        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",  # noqa: S106 - test fixture secret
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        reviewed_at = service.list_lifecycle_transitions("case", promoted_case.case_id)[
            -1
        ].transitioned_at
        return store, service, promoted_case, promoted_case.evidence_ids[0], reviewed_at

    def _build_phase19_out_of_scope_case(
        self,
        *,
        fixture_name: str,
        host: str | None = None,
        port: int | None = None,
    ) -> tuple[AegisOpsControlPlaneService, CaseRecord]:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1" if host is None else host,
                port=0 if port is None else port,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(_load_wazuh_fixture(fixture_name)),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        return service, promoted_case

    def _seed_create_tracking_ticket_request(
        self,
        *,
        service: AegisOpsControlPlaneService,
        promoted_case: CaseRecord,
        reviewed_at: datetime,
        suffix: str,
        coordination_reference_id: str,
    ) -> dict[str, object]:
        requested_at = reviewed_at + timedelta(minutes=10)
        expires_at = reviewed_at + timedelta(hours=4)
        approved_target_scope = {
            "case_id": promoted_case.case_id,
            "alert_id": promoted_case.alert_id,
            "finding_id": promoted_case.finding_id,
            "coordination_reference_id": coordination_reference_id,
            "coordination_target_type": "zammad",
        }
        approved_payload = phase26_create_tracking_ticket_payload(
            case_id=promoted_case.case_id,
            alert_id=promoted_case.alert_id,
            finding_id=promoted_case.finding_id,
            coordination_reference_id=coordination_reference_id,
        )
        payload_hash = _approved_payload_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=f"approval-cli-create-ticket-{suffix}",
                action_request_id=f"action-request-cli-create-ticket-{suffix}",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id=f"action-request-cli-create-ticket-{suffix}",
                approval_decision_id=approval.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key=f"idempotency-cli-create-ticket-{suffix}",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                requested_payload=approved_payload,
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        return {
            "action_request": action_request,
            "approval": approval,
            "approved_payload": approved_payload,
            "payload_hash": payload_hash,
        }

    def _build_out_of_scope_case_advisory_review_records(
        self,
        *,
        fixture_name: str,
        host: str | None = None,
        port: int | None = None,
    ) -> tuple[AegisOpsControlPlaneService, RecommendationRecord, AITraceRecord]:
        service, promoted_case = self._build_phase19_out_of_scope_case(
            fixture_name=fixture_name,
            host=host,
            port=port,
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-cli-replay-linked-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-phase19-cli-replay-linked-001",
                review_owner="reviewer-001",
                intended_outcome="Replay-linked advisory reads must fail closed.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase19-cli-replay-linked-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc),
                material_input_refs=(),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )
        return service, recommendation, ai_trace

    def _build_case_scoped_advisory_records_without_case_lineage(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
    ) -> tuple[AegisOpsControlPlaneService, RecommendationRecord, AITraceRecord]:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case(
            host=host,
            port=port,
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Case-scoped advisory reads must fail closed without case lineage.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Preserve reviewed lead linkage for bounded advisory rendering.",
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-cli-lead-only-advisory-001",
                lead_id=lead.lead_id,
                hunt_run_id=None,
                alert_id=None,
                case_id=None,
                ai_trace_id=None,
                review_owner="analyst-001",
                intended_outcome="Review the lead linkage before any broader response.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-cli-lead-only-advisory-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=reviewed_at,
                material_input_refs=(),
                reviewer_identity="analyst-001",
                lifecycle_state="under_review",
            )
        )
        return service, recommendation, ai_trace

    def _seed_action_review_states_for_case(
        self,
        service: AegisOpsControlPlaneService,
        promoted_case: CaseRecord,
        reviewed_at: datetime,
        evidence_id: str,
    ) -> dict[str, object]:
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        base_requested_at = datetime.now(timezone.utc)
        pending_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-pending-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=base_requested_at + timedelta(hours=4),
            action_request_id="action-request-cli-review-pending-001",
        )
        base_requested_at = pending_request.requested_at
        rejected_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-review-rejected-001",
                action_request_id="action-request-cli-review-rejected-001",
                approver_identities=("approver-rejected-001",),
                target_snapshot=dict(pending_request.target_scope),
                payload_hash=pending_request.payload_hash,
                decided_at=base_requested_at + timedelta(minutes=10),
                lifecycle_state="rejected",
            )
        )
        rejected_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-cli-review-rejected-001",
                approval_decision_id=rejected_decision.approval_decision_id,
                idempotency_key="idempotency-cli-review-rejected-001",
                requested_at=base_requested_at + timedelta(minutes=5),
                lifecycle_state="rejected",
                requester_identity="analyst-002",
            )
        )
        expired_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-review-expired-001",
                action_request_id="action-request-cli-review-expired-001",
                approver_identities=("approver-expired-001",),
                target_snapshot=dict(pending_request.target_scope),
                payload_hash=pending_request.payload_hash,
                decided_at=base_requested_at + timedelta(minutes=20),
                lifecycle_state="expired",
                approved_expires_at=base_requested_at + timedelta(minutes=30),
            )
        )
        expired_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-cli-review-expired-001",
                approval_decision_id=expired_decision.approval_decision_id,
                idempotency_key="idempotency-cli-review-expired-001",
                requested_at=base_requested_at + timedelta(minutes=15),
                expires_at=base_requested_at + timedelta(minutes=30),
                lifecycle_state="expired",
                requester_identity="analyst-003",
            )
        )
        superseded_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-cli-review-superseded-001",
                idempotency_key="idempotency-cli-review-superseded-001",
                requested_at=base_requested_at + timedelta(minutes=25),
                lifecycle_state="superseded",
                requester_identity="analyst-004",
            )
        )
        replacement_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-cli-review-replacement-001",
                idempotency_key="idempotency-cli-review-replacement-001",
                requested_at=base_requested_at + timedelta(minutes=35),
                requester_identity="analyst-005",
            )
        )
        return {
            "recommendation": recommendation,
            "pending_request": pending_request,
            "rejected_request": rejected_request,
            "expired_request": expired_request,
            "superseded_request": superseded_request,
            "replacement_request": replacement_request,
        }

    def _seed_action_review_timeline_mismatch_for_case(
        self,
        service: AegisOpsControlPlaneService,
        promoted_case: CaseRecord,
        reviewed_at: datetime,
        evidence_id: str,
    ) -> dict[str, object]:
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-009",
            observed_at=reviewed_at,
            scope_statement=(
                "Observed control-plane timeline fixture requires preserved review lineage."
            ),
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-009",
            triage_rationale="Timeline inspection requires approval-bound reviewed lineage.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-009",
            intended_outcome=(
                "Review repository owner change evidence before any approval-bound response."
            ),
            lead_id=lead.lead_id,
        )
        requested_at = datetime.now(timezone.utc)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-009",
            recipient_identity="repo-owner-timeline-001",
            message_intent="Notify the accountable owner using the reviewed action path.",
            escalation_reason="Timeline inspection needs a reviewed action chain fixture.",
            expires_at=requested_at + timedelta(hours=4),
            action_request_id="action-request-cli-timeline-001",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-timeline-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-timeline-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        action_execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=requested_at + timedelta(minutes=7),
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": "shuffle-run-cli-timeline-observed-002",
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": action_execution.approval_decision_id,
                    "delegation_id": action_execution.delegation_id,
                    "payload_hash": action_execution.payload_hash,
                    "observed_at": requested_at + timedelta(minutes=9),
                    "status": "failed",
                },
            ),
            compared_at=requested_at + timedelta(minutes=10),
            stale_after=requested_at + timedelta(minutes=30),
        )
        return {
            "recommendation": recommendation,
            "action_request": approved_request,
            "approval_decision": approval_decision,
            "action_execution": action_execution,
            "reconciliation": reconciliation,
        }

    def _seed_action_review_predelegation_reconciliation_for_case(
        self,
        service: AegisOpsControlPlaneService,
        promoted_case: CaseRecord,
        reviewed_at: datetime,
        evidence_id: str,
    ) -> dict[str, object]:
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-009",
            observed_at=reviewed_at,
            scope_statement=(
                "Observed control-plane timeline fixture requires preserved pre-delegation reconciliation lineage."
            ),
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-009",
            triage_rationale="Timeline inspection requires approval-bound reviewed lineage.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-009",
            intended_outcome=(
                "Review repository owner change evidence before any approval-bound response."
            ),
            lead_id=lead.lead_id,
        )
        requested_at = datetime.now(timezone.utc)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-009",
            recipient_identity="repo-owner-timeline-001",
            message_intent="Notify the accountable owner using the reviewed action path.",
            escalation_reason="Timeline inspection needs a reviewed action chain fixture.",
            expires_at=requested_at + timedelta(hours=4),
            action_request_id="action-request-cli-predelegation-001",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-predelegation-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-timeline-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(),
            compared_at=requested_at + timedelta(minutes=6),
            stale_after=requested_at + timedelta(minutes=30),
        )
        action_execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=requested_at + timedelta(minutes=7),
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        return {
            "recommendation": recommendation,
            "action_request": approved_request,
            "approval_decision": approval_decision,
            "action_execution": action_execution,
            "reconciliation": reconciliation,
        }

    def _seed_action_review_retried_execution_for_case(
        self,
        service: AegisOpsControlPlaneService,
        promoted_case: CaseRecord,
        reviewed_at: datetime,
        evidence_id: str,
    ) -> dict[str, object]:
        seeded = self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )
        first_execution = seeded["action_execution"]
        first_reconciliation = seeded["reconciliation"]
        latest_execution = service.persist_record(
            replace(
                first_execution,
                action_execution_id="action-execution-cli-timeline-002",
                delegation_id="delegation-cli-timeline-002",
                execution_run_id="shuffle-run-cli-timeline-current-003",
                delegated_at=first_execution.delegated_at + timedelta(minutes=4),
                provenance={
                    **dict(first_execution.provenance),
                    "downstream_binding": {
                        "approval_decision_id": first_execution.approval_decision_id,
                        "delegation_id": "delegation-cli-timeline-002",
                        "payload_hash": first_execution.payload_hash,
                    },
                },
                lifecycle_state="queued",
            )
        )
        current_reconciliation = service.persist_record(
            replace(
                first_reconciliation,
                reconciliation_id="reconciliation-cli-timeline-current-003",
                subject_linkage={
                    **dict(first_reconciliation.subject_linkage),
                    "action_execution_ids": (latest_execution.action_execution_id,),
                    "delegation_ids": (latest_execution.delegation_id,),
                },
                execution_run_id=latest_execution.execution_run_id,
                linked_execution_run_ids=(latest_execution.execution_run_id,),
                last_seen_at=latest_execution.delegated_at + timedelta(minutes=2),
                mismatch_summary="matched latest reviewed execution lineage",
                compared_at=latest_execution.delegated_at + timedelta(minutes=3),
                lifecycle_state="matched",
                ingest_disposition="matched",
            )
        )
        unrelated_later_reconciliation = service.persist_record(
            replace(
                first_reconciliation,
                reconciliation_id="reconciliation-cli-timeline-older-004",
                last_seen_at=latest_execution.delegated_at + timedelta(minutes=8),
                compared_at=latest_execution.delegated_at + timedelta(minutes=9),
                mismatch_summary=(
                    "older execution lineage must not outrank the selected retry"
                ),
            )
        )
        return {
            **seeded,
            "selected_action_execution": latest_execution,
            "selected_reconciliation": current_reconciliation,
            "unrelated_later_reconciliation": unrelated_later_reconciliation,
        }

    def _assert_review_timeline_snapshot(
        self,
        review: dict[str, object],
        seeded: dict[str, object],
    ) -> None:
        action_execution = seeded["action_execution"]
        reconciliation = seeded["reconciliation"]
        self.assertEqual(review["action_request_id"], seeded["action_request"].action_request_id)
        self.assertEqual(
            [stage["stage"] for stage in review["timeline"]],
            [
                "action_request",
                "approval_decision",
                "delegation",
                "action_execution",
                "reconciliation",
            ],
        )
        self.assertEqual(review["timeline"][0]["state"], "approved")
        self.assertEqual(
            review["timeline"][0]["actor_identities"],
            ["analyst-009"],
        )
        self.assertEqual(review["timeline"][1]["state"], "approved")
        self.assertEqual(
            review["timeline"][1]["actor_identities"],
            ["approver-timeline-001"],
        )
        self.assertEqual(review["timeline"][2]["state"], "delegated")
        self.assertEqual(review["timeline"][2]["record_family"], "action_execution")
        self.assertEqual(
            review["timeline"][2]["record_id"],
            action_execution.action_execution_id,
        )
        self.assertEqual(
            review["timeline"][2]["occurred_at"],
            action_execution.delegated_at.isoformat(),
        )
        self.assertEqual(
            review["timeline"][2]["actor_identities"],
            ["control-plane-service"],
        )
        self.assertEqual(
            review["timeline"][2]["details"]["delegation_id"],
            action_execution.delegation_id,
        )
        self.assertEqual(review["timeline"][3]["state"], "queued")
        self.assertEqual(
            review["timeline"][3]["occurred_at"],
            None,
        )
        self.assertEqual(
            review["timeline"][3]["actor_identities"],
            ["control-plane-service"],
        )
        self.assertNotEqual(
            review["timeline"][3]["occurred_at"],
            action_execution.delegated_at.isoformat(),
        )
        self.assertEqual(
            review["timeline"][4]["state"],
            "mismatched",
        )
        self.assertEqual(
            review["timeline"][4]["record_id"],
            reconciliation.reconciliation_id,
        )
        self.assertEqual(
            review["mismatch_inspection"]["reconciliation_id"],
            reconciliation.reconciliation_id,
        )
        self.assertEqual(
            review["mismatch_inspection"]["lifecycle_state"],
            "mismatched",
        )
        self.assertEqual(
            review["mismatch_inspection"]["ingest_disposition"],
            "mismatch",
        )
        self.assertIn(
            "execution run identity mismatch",
            review["mismatch_inspection"]["mismatch_summary"],
        )
        self.assertEqual(
            review["mismatch_inspection"]["execution_run_id"],
            "shuffle-run-cli-timeline-observed-002",
        )
        self.assertEqual(
            review["mismatch_inspection"]["linked_execution_run_ids"],
            ["shuffle-run-cli-timeline-observed-002"],
        )

    def test_runtime_command_uses_runtime_service_builder_when_not_injected(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stdout = io.StringIO()

        with mock.patch.object(
            main,
            "build_runtime_service",
            return_value=service,
        ) as build_runtime_service:
            main.main(["runtime"], stdout=stdout)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["persistence_mode"], "postgresql")
        build_runtime_service.assert_called_once_with()

    def test_runtime_command_honors_injected_service_snapshot(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=9411,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        stdout = io.StringIO()

        main.main(["runtime"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["bind_host"], "127.0.0.1")
        self.assertEqual(payload["bind_port"], 9411)
        self.assertEqual(payload["postgres_dsn"], "postgresql://control-plane.local/aegisops")
        self.assertEqual(payload["persistence_mode"], "postgresql")

    def test_serve_command_uses_long_running_runtime_surface(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            main,
            "build_runtime_service",
            return_value=service,
        ) as build_runtime_service, mock.patch.object(
            main,
            "run_control_plane_service",
            return_value=0,
        ) as run_control_plane_service:
            exit_code = main.main(["serve"])

        self.assertEqual(exit_code, 0)
        build_runtime_service.assert_called_once_with()
        run_control_plane_service.assert_called_once_with(service, stderr=mock.ANY)

    def test_startup_and_shutdown_status_commands_render_reviewed_contracts(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_reverse_proxy_secret="reviewed-surface-secret",  # noqa: S106 - test fixture secret
                protected_surface_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_proxy_service_account=REVIEWED_PROXY_SERVICE_ACCOUNT,
                protected_surface_reviewed_identity_provider="authentik",
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        service.persist_record(
            CaseRecord(
                case_id="case-shutdown-001",
                alert_id="alert-shutdown-001",
                finding_id="finding-shutdown-001",
                evidence_ids=("evidence-shutdown-001",),
                lifecycle_state="open",
            )
        )
        startup_stdout = io.StringIO()
        shutdown_stdout = io.StringIO()

        main.main(["startup-status"], stdout=startup_stdout, service=service)
        main.main(["shutdown-status"], stdout=shutdown_stdout, service=service)

        startup_payload = json.loads(startup_stdout.getvalue())
        shutdown_payload = json.loads(shutdown_stdout.getvalue())
        self.assertTrue(startup_payload["startup_ready"])
        self.assertEqual(
            startup_payload["validated_surfaces"],
            ["wazuh_ingest", "protected_surface"],
        )
        self.assertFalse(shutdown_payload["shutdown_ready"])
        self.assertEqual(shutdown_payload["open_case_ids"], ["case-shutdown-001"])

    def test_startup_status_allows_loopback_protected_surface_without_proxy_bindings(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        startup_stdout = io.StringIO()

        main.main(["startup-status"], stdout=startup_stdout, service=service)

        startup_payload = json.loads(startup_stdout.getvalue())
        self.assertTrue(startup_payload["startup_ready"])
        self.assertNotIn(
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET",
            startup_payload["required_bindings"],
        )
        self.assertEqual(
            startup_payload["validated_surfaces"],
            ["wazuh_ingest", "protected_surface"],
        )

    def test_backup_and_restore_drill_commands_render_recovery_payloads(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        base_now = datetime.now(timezone.utc)
        expires_at = base_now + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-restore-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=base_now + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=action_request.requested_at + timedelta(minutes=10),
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": action_request.requested_at + timedelta(minutes=15),
                    "status": "success",
                },
            ),
            compared_at=action_request.requested_at + timedelta(minutes=16),
            stale_after=action_request.requested_at + timedelta(hours=1),
        )
        backup_stdout = io.StringIO()
        drill_stdout = io.StringIO()

        main.main(["backup-authoritative-record-chain"], stdout=backup_stdout, service=service)
        main.main(["run-authoritative-restore-drill"], stdout=drill_stdout, service=service)

        backup_payload = json.loads(backup_stdout.getvalue())
        drill_payload = json.loads(drill_stdout.getvalue())
        self.assertEqual(
            backup_payload["backup_schema_version"],
            "phase23.authoritative-record-chain.v2",
        )
        self.assertEqual(backup_payload["record_counts"]["action_execution"], 1)
        self.assertTrue(drill_payload["drill_passed"])
        self.assertIn(
            approval_decision.approval_decision_id,
            drill_payload["verified_approval_decision_ids"],
        )
        self.assertIn(
            recommendation.recommendation_id,
            drill_payload["verified_recommendation_ids"],
        )

    def test_backup_authoritative_record_chain_reports_usage_error_on_invalid_backup(
        self,
    ) -> None:
        service = mock.Mock()
        service.export_authoritative_record_chain_backup.side_effect = ValueError(
            "backup invariants failed closed"
        )
        stderr = io.StringIO()

        with mock.patch.object(sys, "stderr", stderr):
            with self.assertRaises(SystemExit) as exc:
                main.main(["backup-authoritative-record-chain"], service=service)

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("backup invariants failed closed", stderr.getvalue())

    def test_restore_authoritative_record_chain_reports_usage_error_on_lookup_failure(
        self,
    ) -> None:
        service = mock.Mock()
        service.restore_authoritative_record_chain_backup.side_effect = LookupError(
            "restore drill failed closed"
        )
        stderr = io.StringIO()

        with mock.patch.object(main, "_read_json_file", return_value={}):
            with mock.patch.object(sys, "stderr", stderr):
                with self.assertRaises(SystemExit) as exc:
                    main.main(
                        [
                            "restore-authoritative-record-chain",
                            "--input",
                            "authoritative-backup.json",
                        ],
                        service=service,
                    )

        self.assertEqual(exc.exception.code, 2)
        self.assertIn("restore drill failed closed", stderr.getvalue())

    def test_long_running_runtime_surface_starts_http_server(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )

        with mock.patch.object(main, "ThreadingHTTPServer") as server_cls:
            server = server_cls.return_value

            exit_code = main.run_control_plane_service(service)

        self.assertEqual(exit_code, 0)
        server_cls.assert_called_once_with(("127.0.0.1", 8089), mock.ANY)
        server.serve_forever.assert_called_once_with()
        server.server_close.assert_called_once_with()

    def test_long_running_runtime_surface_exposes_runtime_and_inspection_http_views(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            AlertRecord(
                alert_id="alert-http-001",
                finding_id="finding-http-001",
                analytic_signal_id="signal-http-001",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-http-001",
                subject_linkage={
                    "alert_ids": ("alert-http-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id="alert-http-001",
                finding_id="finding-http-001",
                analytic_signal_id="signal-http-001",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="claim:host-001:http-runtime",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                ingest_disposition="created",
                mismatch_summary="created during HTTP inspection test",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
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
                runtime_payload = json.loads(
                    request.urlopen(f"{base_url}/runtime", timeout=2).read().decode("utf-8")
                )
                records_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-records?family=alert",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                status_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-reconciliation-status",
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertEqual(runtime_payload["persistence_mode"], "postgresql")
                self.assertEqual(records_payload["record_family"], "alert")
                self.assertEqual(records_payload["records"][0]["alert_id"], "alert-http-001")
                self.assertEqual(status_payload["by_ingest_disposition"], {"created": 1})
                self.assertNotIn(
                    "latest_native_payload",
                    status_payload["records"][0]["subject_linkage"],
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_exposes_operator_readiness_diagnostics_http_view(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        reviewed_at = datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc)
        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",  # noqa: S106 - test fixture secret
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        evidence_id = promoted_case.evidence_ids[0]
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        base_now = datetime.now(timezone.utc)
        expires_at = base_now + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-http-readiness-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=base_now + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=base_now + timedelta(minutes=10),
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": base_now + timedelta(minutes=15),
                    "status": "success",
                },
            ),
            compared_at=base_now + timedelta(minutes=16),
            stale_after=base_now + timedelta(hours=1),
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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
                diagnostics_payload = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        f"{base_url}/diagnostics/readiness",
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertTrue(diagnostics_payload["read_only"])
                self.assertEqual(diagnostics_payload["status"], "ready")
                self.assertTrue(diagnostics_payload["booted"])
                self.assertTrue(diagnostics_payload["startup"]["startup_ready"])
                self.assertFalse(diagnostics_payload["shutdown"]["shutdown_ready"])
                self.assertEqual(
                    diagnostics_payload["metrics"]["action_requests"]["approved"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["action_executions"]["terminal"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["reconciliations"]["matched"],
                    2,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["phase20_notify_identity_owner"]["approved_action_requests"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["phase20_notify_identity_owner"]["reconciled_executions"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["review_path_health"]["overall_state"],
                    "healthy",
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["review_path_health"]["review_count"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["source_health"]["tracked_sources"],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["source_health"]["sources"][
                        "github_audit"
                    ]["state"],
                    "healthy",
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["automation_substrate_health"][
                        "tracked_surfaces"
                    ],
                    1,
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["automation_substrate_health"][
                        "surfaces"
                    ]["automation_substrate:shuffle"]["state"],
                    "healthy",
                )
                self.assertEqual(
                    diagnostics_payload["metrics"]["review_path_health"]["paths"],
                    {
                        "ingest": {
                            "state": "healthy",
                            "reason": "observations_current",
                            "affected_reviews": 0,
                            "by_state": {
                                "healthy": 1,
                                "delayed": 0,
                                "degraded": 0,
                                "failed": 0,
                            },
                        },
                        "delegation": {
                            "state": "healthy",
                            "reason": "delegated",
                            "affected_reviews": 0,
                            "by_state": {
                                "healthy": 1,
                                "delayed": 0,
                                "degraded": 0,
                                "failed": 0,
                            },
                        },
                        "provider": {
                            "state": "healthy",
                            "reason": "execution_succeeded",
                            "affected_reviews": 0,
                            "by_state": {
                                "healthy": 1,
                                "delayed": 0,
                                "degraded": 0,
                                "failed": 0,
                            },
                        },
                        "persistence": {
                            "state": "healthy",
                            "reason": "reconciliation_matched",
                            "affected_reviews": 0,
                            "by_state": {
                                "healthy": 1,
                                "delayed": 0,
                                "degraded": 0,
                                "failed": 0,
                            },
                        },
                    },
                )
                self.assertEqual(
                    diagnostics_payload["latest_reconciliation"]["reconciliation_id"],
                    reconciliation.reconciliation_id,
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_service_emits_structured_observability_logs_for_live_path_and_fail_closed_rejection(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        base_now = datetime.now(timezone.utc)
        expires_at = base_now + timedelta(hours=4)

        with self.assertLogs("aegisops.control_plane", level="INFO") as log_output:
            service.ingest_wazuh_alert(
                raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
                authorization_header="Bearer reviewed-shared-secret",  # noqa: S106 - test fixture secret
                forwarded_proto="https",
                reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                peer_addr="127.0.0.1",
            )
            action_request = service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=expires_at,
            )
            approval_decision = service.persist_record(
                ApprovalDecisionRecord(
                    approval_decision_id="approval-observability-log-001",
                    action_request_id=action_request.action_request_id,
                    approver_identities=("approver-001",),
                    target_snapshot=dict(action_request.target_scope),
                    payload_hash=action_request.payload_hash,
                    decided_at=base_now + timedelta(minutes=5),
                    lifecycle_state="approved",
                    approved_expires_at=action_request.expires_at,
                )
            )
            approved_request = service.persist_record(
                replace(
                    action_request,
                    approval_decision_id=approval_decision.approval_decision_id,
                    lifecycle_state="approved",
                )
            )
            execution = service.delegate_approved_action_to_shuffle(
                action_request_id=approved_request.action_request_id,
                approved_payload=dict(approved_request.requested_payload),
                delegated_at=base_now + timedelta(minutes=10),
                delegation_issuer="control-plane-service",
                evidence_ids=(evidence_id,),
            )
            service.reconcile_action_execution(
                action_request_id=approved_request.action_request_id,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=(
                    {
                        "execution_run_id": execution.execution_run_id,
                        "execution_surface_id": "shuffle",
                        "idempotency_key": approved_request.idempotency_key,
                        "approval_decision_id": execution.approval_decision_id,
                        "delegation_id": execution.delegation_id,
                        "payload_hash": execution.payload_hash,
                        "observed_at": base_now + timedelta(minutes=15),
                        "status": "success",
                    },
                ),
                compared_at=base_now + timedelta(minutes=16),
                stale_after=base_now + timedelta(hours=1),
            )

        structured_events = [
            json.loads(entry.split(":", 2)[2]) for entry in log_output.output
        ]
        self.assertEqual(
            [event["event"] for event in structured_events],
            [
                "wazuh_ingest_admitted",
                "action_request_created",
                "action_execution_delegated",
                "action_execution_reconciled",
            ],
        )
        self.assertEqual(structured_events[0]["disposition"], "deduplicated")
        self.assertEqual(structured_events[0]["peer_addr_class"], "loopback")
        self.assertNotIn("peer_addr", structured_events[0])
        self.assertEqual(
            structured_events[1]["action_type"],
            "notify_identity_owner",
        )
        self.assertTrue(structured_events[1]["requester_identity_present"])
        self.assertNotIn("requester_identity", structured_events[1])
        self.assertEqual(structured_events[2]["execution_surface_id"], "shuffle")
        self.assertEqual(structured_events[3]["lifecycle_state"], "matched")

        with self.assertLogs("aegisops.control_plane", level="WARNING") as rejected_logs:
            with self.assertRaisesRegex(
                PermissionError,
                "reviewed reverse proxy boundary credential",
            ):
                service.ingest_wazuh_alert(
                    raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
                    authorization_header="Bearer reviewed-shared-secret",  # noqa: S106 - test fixture secret
                    forwarded_proto="https",
                    reverse_proxy_secret_header="invalid-secret",  # noqa: S106 - intentional negative test fixture
                    peer_addr="127.0.0.1",
                )

        rejection_event = json.loads(rejected_logs.output[0].split(":", 2)[2])
        self.assertEqual(rejection_event["event"], "wazuh_ingest_rejected")
        self.assertEqual(rejection_event["reason"], "reverse_proxy_secret_mismatch")
        self.assertEqual(rejection_event["peer_addr_class"], "loopback")
        self.assertNotIn("peer_addr", rejection_event)

    def test_long_running_runtime_surface_exposes_analyst_queue_alert_detail_and_case_detail_http_views(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        alert = _load_wazuh_fixture("github-audit-alert.json")
        admitted = service.ingest_wazuh_alert(
            raw_alert=alert,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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
                queue_payload = json.loads(
                    request.urlopen(
                        f"{base_url}/inspect-analyst-queue",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                detail_payload = json.loads(
                    request.urlopen(
                        (
                            f"{base_url}/inspect-alert-detail"
                            f"?alert_id={admitted.alert.alert_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )
                case_payload = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        (
                            f"{base_url}/inspect-case-detail"
                            f"?case_id={promoted_case.case_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertTrue(queue_payload["read_only"])
                self.assertEqual(queue_payload["queue_name"], "analyst_review")
                self.assertEqual(queue_payload["total_records"], 1)
                self.assertEqual(
                    queue_payload["records"][0]["alert_id"],
                    admitted.alert.alert_id,
                )

                self.assertTrue(detail_payload["read_only"])
                self.assertEqual(detail_payload["alert_id"], admitted.alert.alert_id)
                self.assertEqual(detail_payload["alert"]["alert_id"], admitted.alert.alert_id)
                self.assertEqual(detail_payload["case_record"]["case_id"], promoted_case.case_id)
                self.assertEqual(
                    detail_payload["latest_reconciliation"]["reconciliation_id"],
                    admitted.reconciliation.reconciliation_id,
                )
                self.assertEqual(
                    detail_payload["provenance"],
                    {
                        "admission_kind": "live",
                        "admission_channel": "live_wazuh_webhook",
                    },
                )
                self.assertEqual(
                    detail_payload["lineage"]["substrate_detection_record_ids"],
                    ["wazuh:1731595300.1234567"],
                )
                self.assertEqual(
                    detail_payload["lineage"]["accountable_source_identities"],
                    ["manager:wazuh-manager-github-1"],
                )
                self.assertEqual(
                    detail_payload["reviewed_context"]["source"]["source_family"],
                    "github_audit",
                )
                self.assertTrue(case_payload["read_only"])
                self.assertEqual(case_payload["case_id"], promoted_case.case_id)
                self.assertEqual(
                    case_payload["case_record"]["case_id"],
                    promoted_case.case_id,
                )
                self.assertEqual(
                    case_payload["linked_evidence_ids"],
                    [detail_payload["linked_evidence_records"][0]["evidence_id"]],
                )
                self.assertEqual(
                    case_payload["advisory_output"]["output_kind"],
                    "case_summary",
                )
                self.assertEqual(
                    case_payload["advisory_output"]["status"],
                    "ready",
                )
                self.assertEqual(
                    case_payload["reviewed_context"]["source"]["source_family"],
                    "github_audit",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_blank_alert_detail_query(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                with self.assertRaises(error.HTTPError) as exc_info:
                    request.urlopen(
                        (
                            "http://127.0.0.1:"
                            f"{servers[0].server_port}/inspect-alert-detail?alert_id=%20%20"
                        ),
                        timeout=2,
                    )

                self.assertEqual(exc_info.exception.code, 400)
                error_payload = json.loads(exc_info.exception.read().decode("utf-8"))
                self.assertEqual(error_payload["error"], "invalid_request")
                self.assertEqual(
                    error_payload["message"],
                    "alert_id query parameter is required",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_direct_backend_wazuh_ingest_bypass(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                alert = _load_wazuh_fixture("github-audit-alert.json")
                request_body = json.dumps(alert).encode("utf-8")
                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=request_body,
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_missing_wazuh_shared_secret(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_missing_wazuh_reverse_proxy_secret(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_non_loopback_wazuh_ingest_without_trusted_proxies(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                port=8089,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS must be set",
        ):
            main.run_control_plane_service(service)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_without_bearer_auth(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_with_wrong_bearer_secret(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer wrong-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_wazuh_ingest_without_https_forwarding(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("github-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "403"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_non_github_wazuh_family(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                ingest_request = request.Request(
                    f"http://127.0.0.1:{servers[0].server_port}/intake/wazuh",
                    data=json.dumps(_load_wazuh_fixture("microsoft-365-audit-alert.json")).encode("utf-8"),
                    method="POST",
                    headers={
                        "Authorization": "Bearer reviewed-shared-secret",
                        "Content-Type": "application/json",
                        "X-AegisOps-Proxy-Secret": "reviewed-proxy-secret",
                        "X-Forwarded-Proto": "https",
                    },
                )

                with self.assertRaisesRegex(error.HTTPError, "400"):
                    request.urlopen(ingest_request, timeout=2)

                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_service_rejects_non_loopback_wazuh_ingest_from_untrusted_proxy_peer(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",  # noqa: S104 - intentional non-loopback test coverage
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        with self.assertRaisesRegex(
            PermissionError,
            "reviewed reverse proxy peer boundary",
        ):
            service.ingest_wazuh_alert(
                raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
                authorization_header="Bearer reviewed-shared-secret",
                forwarded_proto="https",
                reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                peer_addr="10.10.0.6",
            )

    def test_service_admits_non_loopback_wazuh_ingest_from_trusted_proxy_peer(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",  # noqa: S104 - intentional non-loopback test coverage
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        ingest_result = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="10.10.0.5",
        )

        self.assertEqual(ingest_result.disposition, "created")
        self.assertEqual(len(store.list(AlertRecord)), 1)
        self.assertEqual(len(store.list(AnalyticSignalRecord)), 1)

    def test_service_admits_trusted_proxy_peer_with_surrounding_whitespace(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",  # noqa: S104 - intentional non-loopback test coverage
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        ingest_result = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr=" 10.10.0.5 ",
        )

        self.assertEqual(ingest_result.disposition, "created")
        self.assertEqual(len(store.list(AlertRecord)), 1)
        self.assertEqual(len(store.list(AnalyticSignalRecord)), 1)

    def test_long_running_runtime_surface_rejects_oversized_wazuh_ingest_body(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                connection = http.client.HTTPConnection(
                    "127.0.0.1",
                    servers[0].server_port,
                    timeout=2,
                )
                connection.putrequest("POST", "/intake/wazuh")
                connection.putheader("Authorization", "Bearer reviewed-shared-secret")
                connection.putheader("Content-Type", "application/json")
                connection.putheader("X-AegisOps-Proxy-Secret", "reviewed-proxy-secret")
                connection.putheader("X-Forwarded-Proto", "https")
                connection.putheader(
                    "Content-Length",
                    str(main.MAX_WAZUH_INGEST_BODY_BYTES + 1),
                )
                connection.endheaders()

                response = connection.getresponse()
                self.assertEqual(response.status, 413)
                response_body = json.loads(response.read().decode("utf-8"))
                connection.close()
                self.assertEqual(response_body["error"], "request_too_large")
                self.assertEqual(store.list(AlertRecord), ())
                self.assertEqual(store.list(AnalyticSignalRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_cli_renders_read_only_record_and_reconciliation_views(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            AlertRecord(
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            AnalyticSignalRecord(
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                finding_id="finding-001",
                alert_ids=("alert-001",),
                case_ids=(),
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                lifecycle_state="active",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-001",
                subject_linkage={
                    "alert_ids": ("alert-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=compared_at,
                last_seen_at=compared_at,
                ingest_disposition="created",
                mismatch_summary="created upstream analytic signal into alert lifecycle",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )

        records_stdout = io.StringIO()
        analytic_signals_stdout = io.StringIO()
        status_stdout = io.StringIO()

        main.main(
            ["inspect-records", "--family", "alert"],
            stdout=records_stdout,
            service=service,
        )
        main.main(
            ["inspect-records", "--family", "analytic_signal"],
            stdout=analytic_signals_stdout,
            service=service,
        )
        main.main(
            ["inspect-reconciliation-status"],
            stdout=status_stdout,
            service=service,
        )

        records_payload = json.loads(records_stdout.getvalue())
        analytic_signals_payload = json.loads(analytic_signals_stdout.getvalue())
        status_payload = json.loads(status_stdout.getvalue())

        self.assertTrue(records_payload["read_only"])
        self.assertEqual(records_payload["record_family"], "alert")
        self.assertEqual(records_payload["records"][0]["alert_id"], "alert-001")

        self.assertTrue(analytic_signals_payload["read_only"])
        self.assertEqual(analytic_signals_payload["record_family"], "analytic_signal")
        self.assertEqual(
            analytic_signals_payload["records"][0]["analytic_signal_id"],
            "signal-001",
        )
        self.assertEqual(
            analytic_signals_payload["records"][0]["substrate_detection_record_id"],
            "substrate-detection-001",
        )

        self.assertTrue(status_payload["read_only"])
        self.assertEqual(status_payload["total_records"], 1)
        self.assertEqual(status_payload["by_ingest_disposition"], {"created": 1})
        self.assertEqual(
            status_payload["latest_compared_at"],
            "2026-04-05T12:00:00+00:00",
        )
        self.assertNotIn(
            "latest_native_payload",
            status_payload["records"][0]["subject_linkage"],
        )

    def test_cli_renders_wazuh_business_hours_analyst_queue_view(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["queue_name"], "analyst_review")
        self.assertEqual(payload["total_records"], 1)
        self.assertEqual(payload["records"][0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(
            payload["records"][0]["queue_selection"],
            "business_hours_triage",
        )
        self.assertEqual(payload["records"][0]["review_state"], "case_required")
        self.assertEqual(payload["records"][0]["case_id"], promoted_case.case_id)
        self.assertEqual(payload["records"][0]["case_lifecycle_state"], "open")
        self.assertEqual(payload["records"][0]["source_system"], "wazuh")
        self.assertEqual(
            payload["records"][0]["accountable_source_identities"],
            ["agent:007"],
        )
        self.assertEqual(
            payload["records"][0]["reviewed_context"]["location"],
            "/var/log/auth.log",
        )
        self.assertEqual(
            payload["records"][0]["native_rule"]["description"],
            "SSH brute force attempt",
        )
        self.assertEqual(
            payload["records"][0]["substrate_detection_record_ids"],
            ["wazuh:1731594986.4931506"],
        )

    def test_cli_renders_reviewed_wazuh_alert_detail_view(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", admitted.alert.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["alert_id"], admitted.alert.alert_id)
        self.assertEqual(payload["alert"]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(payload["case_record"]["case_id"], promoted_case.case_id)
        self.assertEqual(
            payload["latest_reconciliation"]["reconciliation_id"],
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            payload["provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )
        self.assertEqual(
            payload["lineage"]["substrate_detection_record_ids"],
            ["wazuh:1731595300.1234567"],
        )
        self.assertEqual(
            payload["lineage"]["accountable_source_identities"],
            ["manager:wazuh-manager-github-1"],
        )
        self.assertEqual(
            payload["reviewed_context"]["source"]["source_family"],
            "github_audit",
        )

    def test_cli_renders_analyst_assistant_context_view_for_a_case(self) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-assistant-cli-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="follow reviewed evidence",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "inspect-assistant-context",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["record_family"], "case")
        self.assertEqual(payload["record_id"], promoted_case.case_id)
        self.assertEqual(payload["record"]["case_id"], promoted_case.case_id)
        self.assertEqual(payload["advisory_output"]["output_kind"], "case_summary")
        self.assertEqual(payload["advisory_output"]["status"], "ready")
        self.assertIn(evidence_id, payload["advisory_output"]["citations"])
        self.assertEqual(payload["reviewed_context"], promoted_case.reviewed_context)
        self.assertEqual(payload["linked_evidence_ids"], [evidence_id])
        self.assertEqual(
            payload["linked_evidence_records"][0]["evidence_id"],
            evidence_id,
        )
        self.assertIn(promoted_case.alert_id, payload["linked_alert_ids"])
        self.assertIn(
            recommendation.recommendation_id,
            payload["linked_recommendation_ids"],
        )
        self.assertTrue(payload["linked_reconciliation_ids"])

    def test_cli_renders_cited_advisory_output_view_for_a_case(self) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-advisory-cli-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before any approval",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "inspect-advisory-output",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["record_family"], "case")
        self.assertEqual(payload["record_id"], promoted_case.case_id)
        self.assertEqual(payload["output_kind"], "case_summary")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["reviewed_context"], promoted_case.reviewed_context)
        self.assertIn(evidence_id, payload["citations"])
        self.assertIn("advisory_only", payload["uncertainty_flags"])
        self.assertEqual(payload["linked_evidence_ids"], [evidence_id])
        self.assertIn(promoted_case.alert_id, payload["linked_alert_ids"])
        self.assertIn(recommendation.recommendation_id, payload["linked_recommendation_ids"])
        self.assertTrue(payload["linked_reconciliation_ids"])

    def test_cli_renders_case_detail_with_evidence_provenance_and_cited_advisory_output(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, compared_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=compared_at,
            scope_statement="Observed permission change remains within reviewed GitHub audit scope.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Preserve durable case context for next business-hours analyst.",
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-case-detail-cli-001",
                lead_id=lead.lead_id,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before any approval",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=compared_at,
            handoff_owner="analyst-001",
            handoff_note="Resume owner-membership review during the next business-hours cycle.",
            follow_up_evidence_ids=(evidence_id,),
        )
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Tracked case remains open for the next analyst review window.",
            recorded_at=compared_at,
        )

        stdout = io.StringIO()
        main.main(
            [
                "inspect-case-detail",
                "--case-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["case_id"], promoted_case.case_id)
        self.assertEqual(payload["case_record"]["case_id"], promoted_case.case_id)
        self.assertEqual(
            payload["reviewed_context"]["asset"],
            promoted_case.reviewed_context["asset"],
        )
        self.assertEqual(
            payload["reviewed_context"]["identity"],
            promoted_case.reviewed_context["identity"],
        )
        self.assertEqual(
            payload["advisory_output"]["output_kind"],
            "case_summary",
        )
        self.assertEqual(payload["advisory_output"]["status"], "ready")
        self.assertEqual(payload["linked_evidence_ids"], [evidence_id])
        self.assertEqual(
            payload["linked_evidence_records"][0]["collector_identity"],
            "wazuh-native-detection-adapter",
        )
        self.assertEqual(
            payload["linked_evidence_records"][0]["derivation_relationship"],
            "native_detection_record",
        )
        self.assertEqual(payload["linked_observation_ids"], [observation.observation_id])
        self.assertEqual(payload["linked_lead_ids"], [lead.lead_id])
        self.assertEqual(
            payload["case_record"]["reviewed_context"]["triage"]["disposition"],
            "business_hours_handoff",
        )
        self.assertEqual(
            payload["case_record"]["reviewed_context"]["handoff"]["handoff_owner"],
            "analyst-001",
        )
        self.assertIn(
            recommendation.recommendation_id,
            payload["linked_recommendation_ids"],
        )
        self.assertIn(
            (
                "reviewed_context.provenance.rule_id="
                f"{promoted_case.reviewed_context['provenance']['rule_id']}"
            ),
            payload["advisory_output"]["citations"],
        )
        self.assertIn(
            promoted_case.case_id,
            payload["linked_reconciliation_records"][0]["subject_linkage"]["case_ids"],
        )
        self.assertIn(
            payload["linked_reconciliation_records"][0]["reconciliation_id"],
            payload["linked_reconciliation_ids"],
        )
        self.assertEqual(
            payload["cross_source_timeline"][0]["record_family"],
            "alert",
        )
        self.assertEqual(
            payload["cross_source_timeline"][0]["provenance_classification"],
            "authoritative-anchor",
        )
        self.assertEqual(
            payload["cross_source_timeline"][1]["record_family"],
            "evidence",
        )
        self.assertEqual(
            payload["cross_source_timeline"][1]["blocking_reason"],
            "missing_provenance",
        )
        self.assertEqual(
            payload["cross_source_timeline"][2]["record_family"],
            "observation",
        )
        self.assertEqual(
            payload["cross_source_timeline"][2]["blocking_reason"],
            "missing_provenance",
        )
        self.assertEqual(
            payload["provenance_summary"]["authoritative_anchor"]["record_id"],
            promoted_case.alert_id,
        )
        self.assertEqual(
            payload["provenance_summary"]["source_families"],
            ["github_audit", "wazuh", "unknown"],
        )

    def test_cli_records_bounded_operator_casework_actions(self) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        handoff_at = reviewed_at + timedelta(hours=8)

        promote_stdout = io.StringIO()
        main.main(
            ["promote-alert-to-case", "--alert-id", promoted_case.alert_id],
            stdout=promote_stdout,
            service=service,
        )
        promoted_case_payload = json.loads(promote_stdout.getvalue())
        case_id = promoted_case_payload["case_id"]
        self.assertEqual(promoted_case_payload["lifecycle_state"], "open")

        observation_stdout = io.StringIO()
        main.main(
            [
                "record-case-observation",
                "--case-id",
                case_id,
                "--author-identity",
                "analyst-001",
                "--observed-at",
                reviewed_at.isoformat(),
                "--scope-statement",
                "Observed repository permission change requires tracked review.",
                "--supporting-evidence-id",
                evidence_id,
            ],
            stdout=observation_stdout,
            service=service,
        )
        observation_payload = json.loads(observation_stdout.getvalue())
        self.assertEqual(observation_payload["case_id"], case_id)
        self.assertEqual(observation_payload["supporting_evidence_ids"], [evidence_id])

        lead_stdout = io.StringIO()
        main.main(
            [
                "record-case-lead",
                "--case-id",
                case_id,
                "--triage-owner",
                "analyst-001",
                "--triage-rationale",
                "Privilege-impacting change needs durable business-hours follow-up.",
                "--observation-id",
                observation_payload["observation_id"],
            ],
            stdout=lead_stdout,
            service=service,
        )
        lead_payload = json.loads(lead_stdout.getvalue())
        self.assertEqual(lead_payload["case_id"], case_id)
        self.assertEqual(lead_payload["observation_id"], observation_payload["observation_id"])

        recommendation_stdout = io.StringIO()
        main.main(
            [
                "record-case-recommendation",
                "--case-id",
                case_id,
                "--review-owner",
                "analyst-001",
                "--intended-outcome",
                "Review repository owner change evidence before any approval-bound response.",
                "--lead-id",
                lead_payload["lead_id"],
            ],
            stdout=recommendation_stdout,
            service=service,
        )
        recommendation_payload = json.loads(recommendation_stdout.getvalue())
        self.assertEqual(recommendation_payload["case_id"], case_id)
        self.assertEqual(recommendation_payload["lead_id"], lead_payload["lead_id"])

        handoff_stdout = io.StringIO()
        main.main(
            [
                "record-case-handoff",
                "--case-id",
                case_id,
                "--handoff-at",
                handoff_at.isoformat(),
                "--handoff-owner",
                "analyst-001",
                "--handoff-note",
                "Recheck repository owner membership against approved change window at next business-hours review.",
                "--follow-up-evidence-id",
                evidence_id,
            ],
            stdout=handoff_stdout,
            service=service,
        )
        handoff_payload = json.loads(handoff_stdout.getvalue())
        self.assertEqual(handoff_payload["case_id"], case_id)
        self.assertEqual(
            handoff_payload["reviewed_context"]["handoff"]["follow_up_evidence_ids"],
            [evidence_id],
        )

        disposition_stdout = io.StringIO()
        main.main(
            [
                "record-case-disposition",
                "--case-id",
                case_id,
                "--disposition",
                "business_hours_handoff",
                "--rationale",
                "No same-day response required; preserve next-shift context and keep case open.",
                "--recorded-at",
                handoff_at.isoformat(),
            ],
            stdout=disposition_stdout,
            service=service,
        )
        disposition_payload = json.loads(disposition_stdout.getvalue())
        self.assertEqual(disposition_payload["case_id"], case_id)
        self.assertEqual(disposition_payload["lifecycle_state"], "pending_action")
        self.assertEqual(
            disposition_payload["reviewed_context"]["triage"]["disposition"],
            "business_hours_handoff",
        )

        detail_stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", case_id],
            stdout=detail_stdout,
            service=service,
        )
        detail_payload = json.loads(detail_stdout.getvalue())
        self.assertEqual(detail_payload["linked_observation_ids"], [observation_payload["observation_id"]])
        self.assertEqual(detail_payload["linked_lead_ids"], [lead_payload["lead_id"]])
        self.assertIn(
            recommendation_payload["recommendation_id"],
            detail_payload["linked_recommendation_ids"],
        )
        self.assertEqual(
            detail_payload["case_record"]["reviewed_context"]["handoff"]["handoff_owner"],
            "analyst-001",
        )
        self.assertEqual(
            detail_payload["case_record"]["reviewed_context"]["triage"]["disposition"],
            "business_hours_handoff",
        )

    def test_long_running_runtime_surface_records_bounded_operator_casework_actions(self) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(host="127.0.0.1", port=0)
        )
        handoff_at = reviewed_at + timedelta(hours=8)

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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
                    response = request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        request.Request(  # noqa: S310 - local in-process test HTTP server
                            f"{base_url}{path}",
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=2,
                    )
                    return json.loads(response.read().decode("utf-8"))

                promoted_case_payload = post_json(
                    "/operator/promote-alert-to-case",
                    {"alert_id": promoted_case.alert_id},
                )
                case_id = promoted_case_payload["case_id"]
                self.assertEqual(promoted_case_payload["lifecycle_state"], "open")

                observation_payload = post_json(
                    "/operator/record-case-observation",
                    {
                        "case_id": case_id,
                        "author_identity": "analyst-001",
                        "observed_at": reviewed_at.isoformat(),
                        "scope_statement": "Observed repository permission change requires tracked review.",
                        "supporting_evidence_ids": [evidence_id],
                    },
                )
                self.assertEqual(observation_payload["case_id"], case_id)

                lead_payload = post_json(
                    "/operator/record-case-lead",
                    {
                        "case_id": case_id,
                        "triage_owner": "analyst-001",
                        "triage_rationale": "Privilege-impacting change needs durable business-hours follow-up.",
                        "observation_id": observation_payload["observation_id"],
                    },
                )
                self.assertEqual(lead_payload["observation_id"], observation_payload["observation_id"])

                recommendation_payload = post_json(
                    "/operator/record-case-recommendation",
                    {
                        "case_id": case_id,
                        "review_owner": "analyst-001",
                        "intended_outcome": "Review repository owner change evidence before any approval-bound response.",
                        "lead_id": lead_payload["lead_id"],
                    },
                )
                self.assertEqual(recommendation_payload["lead_id"], lead_payload["lead_id"])

                handoff_payload = post_json(
                    "/operator/record-case-handoff",
                    {
                        "case_id": case_id,
                        "handoff_at": handoff_at.isoformat(),
                        "handoff_owner": "analyst-001",
                        "handoff_note": "Recheck repository owner membership against approved change window at next business-hours review.",
                        "follow_up_evidence_ids": [evidence_id],
                    },
                )
                self.assertEqual(
                    handoff_payload["reviewed_context"]["handoff"]["follow_up_evidence_ids"],
                    [evidence_id],
                )

                disposition_payload = post_json(
                    "/operator/record-case-disposition",
                    {
                        "case_id": case_id,
                        "disposition": "business_hours_handoff",
                        "rationale": "No same-day response required; preserve next-shift context and keep case open.",
                        "recorded_at": handoff_at.isoformat(),
                    },
                )
                self.assertEqual(disposition_payload["lifecycle_state"], "pending_action")

                detail_payload = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        f"{base_url}/inspect-case-detail?case_id={case_id}",
                        timeout=2,
                    ).read().decode("utf-8")
                )
                self.assertEqual(detail_payload["linked_observation_ids"], [observation_payload["observation_id"]])
                self.assertEqual(detail_payload["linked_lead_ids"], [lead_payload["lead_id"]])
                self.assertIn(
                    recommendation_payload["recommendation_id"],
                    detail_payload["linked_recommendation_ids"],
                )
                self.assertEqual(
                    detail_payload["case_record"]["reviewed_context"]["triage"]["disposition"],
                    "business_hours_handoff",
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_exposes_cited_advisory_review_routes(self) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case(
            host="127.0.0.1",
            port=0,
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-http-advisory-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                assistant_context = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        (
                            f"{base_url}/inspect-assistant-context"
                            f"?family=case&record_id={promoted_case.case_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )
                advisory_output = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        (
                            f"{base_url}/inspect-advisory-output"
                            f"?family=case&record_id={promoted_case.case_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )
                recommendation_draft = json.loads(
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        (
                            f"{base_url}/render-recommendation-draft"
                            f"?family=case&record_id={promoted_case.case_id}"
                        ),
                        timeout=2,
                    ).read().decode("utf-8")
                )

                self.assertTrue(assistant_context["read_only"])
                self.assertEqual(assistant_context["record_family"], "case")
                self.assertEqual(assistant_context["record_id"], promoted_case.case_id)
                self.assertEqual(
                    assistant_context["advisory_output"]["output_kind"],
                    "case_summary",
                )
                self.assertEqual(assistant_context["reviewed_context"], promoted_case.reviewed_context)
                self.assertEqual(assistant_context["linked_evidence_ids"], [evidence_id])

                self.assertTrue(advisory_output["read_only"])
                self.assertEqual(advisory_output["record_family"], "case")
                self.assertEqual(advisory_output["record_id"], promoted_case.case_id)
                self.assertEqual(advisory_output["output_kind"], "case_summary")
                self.assertEqual(advisory_output["status"], "ready")
                self.assertIn(evidence_id, advisory_output["citations"])

                self.assertTrue(recommendation_draft["read_only"])
                self.assertEqual(recommendation_draft["record_family"], "case")
                self.assertEqual(recommendation_draft["record_id"], promoted_case.case_id)
                self.assertEqual(
                    recommendation_draft["recommendation_draft"]["source_output_kind"],
                    "case_summary",
                )
                self.assertEqual(
                    recommendation_draft["recommendation_draft"]["status"],
                    "ready",
                )
                self.assertIn(
                    recommendation.recommendation_id,
                    recommendation_draft["linked_recommendation_ids"],
                )

                with self.assertRaises(error.HTTPError) as invalid_family_exc:
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        (
                            f"{base_url}/inspect-advisory-output"
                            "?family=not-a-family"
                            f"&record_id={promoted_case.case_id}"
                        ),
                        timeout=2,
                    )

                self.assertEqual(invalid_family_exc.exception.code, 400)
                invalid_family_payload = json.loads(
                    invalid_family_exc.exception.read().decode("utf-8")
                )
                self.assertEqual(invalid_family_payload["error"], "invalid_request")
                self.assertIn(
                    "Unsupported control-plane record family",
                    invalid_family_payload["message"],
                )

                with self.assertRaises(error.HTTPError) as missing_record_exc:
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        (
                            f"{base_url}/render-recommendation-draft"
                            "?family=case"
                            "&record_id=case-missing-phase19-http-advisory-001"
                        ),
                        timeout=2,
                    )

                self.assertEqual(missing_record_exc.exception.code, 404)
                missing_record_payload = json.loads(
                    missing_record_exc.exception.read().decode("utf-8")
                )
                self.assertEqual(missing_record_payload["error"], "not_found")
                self.assertIn(
                    "Missing case",
                    missing_record_payload["message"],
                )
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_case_scoped_out_of_scope_advisory_reads(
        self,
    ) -> None:
        service, recommendation, ai_trace = self._build_out_of_scope_case_advisory_review_records(
            fixture_name="github-audit-alert.json",
            host="127.0.0.1",
            port=0,
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                for path, record_family, record_id in (
                    (
                        "/inspect-advisory-output",
                        "recommendation",
                        recommendation.recommendation_id,
                    ),
                    (
                        "/inspect-advisory-output",
                        "ai_trace",
                        ai_trace.ai_trace_id,
                    ),
                    (
                        "/render-recommendation-draft",
                        "recommendation",
                        recommendation.recommendation_id,
                    ),
                    (
                        "/render-recommendation-draft",
                        "ai_trace",
                        ai_trace.ai_trace_id,
                    ),
                ):
                    with self.subTest(
                        path=path,
                        record_family=record_family,
                    ):
                        with self.assertRaises(error.HTTPError) as exc_info:
                            request.urlopen(  # noqa: S310 - local in-process test HTTP server
                                (
                                    f"{base_url}{path}"
                                    f"?family={record_family}&record_id={record_id}"
                                ),
                                timeout=2,
                            )

                        self.assertEqual(exc_info.exception.code, 400)
                        payload = json.loads(
                            exc_info.exception.read().decode("utf-8")
                        )
                        self.assertEqual(payload["error"], "invalid_request")
                        self.assertIn(expected_message, payload["message"])
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_case_family_out_of_scope_advisory_reads(
        self,
    ) -> None:
        service, promoted_case = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json",
            host="127.0.0.1",
            port=0,
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                for path in (
                    "/inspect-assistant-context",
                    "/inspect-advisory-output",
                    "/render-recommendation-draft",
                ):
                    with self.subTest(path=path):
                        with self.assertRaises(error.HTTPError) as exc_info:
                            request.urlopen(  # noqa: S310 - local in-process test HTTP server
                                (
                                    f"{base_url}{path}"
                                    f"?family=case&record_id={promoted_case.case_id}"
                                ),
                                timeout=2,
                            )

                        self.assertEqual(exc_info.exception.code, 400)
                        payload = json.loads(
                            exc_info.exception.read().decode("utf-8")
                        )
                        self.assertEqual(payload["error"], "invalid_request")
                        self.assertIn(expected_message, payload["message"])
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_case_scoped_advisory_reads_without_linked_case(
        self,
    ) -> None:
        service, recommendation, ai_trace = (
            self._build_case_scoped_advisory_records_without_case_lineage(
                host="127.0.0.1",
                port=0,
            )
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                for path, record_family, record_id in (
                    (
                        "/inspect-advisory-output",
                        "recommendation",
                        recommendation.recommendation_id,
                    ),
                    (
                        "/inspect-advisory-output",
                        "ai_trace",
                        ai_trace.ai_trace_id,
                    ),
                    (
                        "/render-recommendation-draft",
                        "recommendation",
                        recommendation.recommendation_id,
                    ),
                    (
                        "/render-recommendation-draft",
                        "ai_trace",
                        ai_trace.ai_trace_id,
                    ),
                ):
                    with self.subTest(
                        path=path,
                        record_family=record_family,
                    ):
                        with self.assertRaises(error.HTTPError) as exc_info:
                            request.urlopen(  # noqa: S310 - local in-process test HTTP server
                                (
                                    f"{base_url}{path}"
                                    f"?family={record_family}&record_id={record_id}"
                                ),
                                timeout=2,
                            )

                        self.assertEqual(exc_info.exception.code, 400)
                        payload = json.loads(
                            exc_info.exception.read().decode("utf-8")
                        )
                        self.assertEqual(payload["error"], "invalid_request")
                        self.assertIn(expected_message, payload["message"])
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_rejects_oversized_operator_request_body(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with mock.patch.object(main, "ThreadingHTTPServer", RecordingServer), self._mock_authenticated_surface_access(
            service,
            principal=REVIEWED_ANALYST_PRINCIPAL,
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

                connection = http.client.HTTPConnection(
                    "127.0.0.1",
                    servers[0].server_port,
                    timeout=2,
                )
                connection.putrequest("POST", "/operator/promote-alert-to-case")
                connection.putheader("Content-Type", "application/json")
                connection.putheader(
                    "Content-Length",
                    str(main.MAX_WAZUH_INGEST_BODY_BYTES + 1),
                )
                connection.endheaders()

                response = connection.getresponse()
                self.assertEqual(response.status, 413)
                response_body = json.loads(response.read().decode("utf-8"))
                connection.close()
                self.assertEqual(response_body["error"], "request_too_large")
                self.assertEqual(store.list(AlertRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_long_running_runtime_surface_forbids_non_loopback_operator_requests(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                port=0,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",
            ),
            store=store,
        )
        admitted = service.ingest_finding_alert(
            finding_id="finding-phase19-http-auth-001",
            analytic_signal_id="signal-phase19-http-auth-001",
            substrate_detection_record_id="substrate-detection-phase19-http-auth-001",
            correlation_key="claim:asset-phase19-http-auth-001:github-audit",
            first_seen_at=datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc),
            reviewed_context={
                "asset": {"asset_id": "asset-phase19-http-auth-001"},
                "identity": {"identity_id": "principal-phase19-http-auth-001"},
            },
        )
        servers: list[main.ThreadingHTTPServer] = []

        class RecordingServer(main.ThreadingHTTPServer):
            def __init__(self, server_address: tuple[str, int], handler_class: type) -> None:
                super().__init__(server_address, handler_class)
                servers.append(self)

        with (
            mock.patch.object(main, "ThreadingHTTPServer", RecordingServer),
            mock.patch.object(
                main,
                "_require_loopback_operator_request",
                side_effect=PermissionError(
                    "operator write surface only accepts loopback callers until a reviewed operator auth boundary exists"
                ),
            ),
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

                with self.assertRaises(error.HTTPError) as exc_info:
                    request.urlopen(  # noqa: S310 - local in-process test HTTP server
                        request.Request(  # noqa: S310 - local in-process test HTTP server
                            f"http://127.0.0.1:{servers[0].server_port}/operator/promote-alert-to-case",
                            data=json.dumps({"alert_id": admitted.alert.alert_id}).encode("utf-8"),
                            headers={"Content-Type": "application/json"},
                            method="POST",
                        ),
                        timeout=2,
                    )

                self.assertEqual(exc_info.exception.code, 403)
                response_body = json.loads(exc_info.exception.read().decode("utf-8"))
                self.assertEqual(response_body["error"], "forbidden")
                self.assertEqual(store.list(CaseRecord), ())
            finally:
                if servers:
                    servers[0].shutdown()
                thread.join(timeout=2)

    def test_cli_renders_recommendation_draft_view_for_a_case(self) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-draft-cli-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "render-recommendation-draft",
                "--family",
                "case",
                "--record-id",
                promoted_case.case_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertTrue(payload["read_only"])
        self.assertEqual(payload["record_family"], "case")
        self.assertEqual(payload["record_id"], promoted_case.case_id)
        self.assertEqual(payload["reviewed_context"], promoted_case.reviewed_context)
        self.assertEqual(
            payload["recommendation_draft"]["source_output_kind"],
            "case_summary",
        )
        self.assertEqual(payload["recommendation_draft"]["status"], "ready")
        self.assertTrue(payload["recommendation_draft"]["candidate_recommendations"])
        self.assertIn(
            evidence_id,
            payload["recommendation_draft"]["citations"],
        )
        self.assertIn(
            "advisory_only",
            payload["recommendation_draft"]["uncertainty_flags"],
        )
        self.assertEqual(payload["linked_evidence_ids"], [evidence_id])
        self.assertIn(promoted_case.alert_id, payload["linked_alert_ids"])
        self.assertIn(recommendation.recommendation_id, payload["linked_recommendation_ids"])
        self.assertTrue(payload["linked_reconciliation_ids"])

    def test_cli_creates_reviewed_action_request_from_recommendation_context(self) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-cli-action-request-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "create-reviewed-action-request",
                "--family",
                "recommendation",
                "--record-id",
                recommendation.recommendation_id,
                "--requester-identity",
                "analyst-001",
                "--recipient-identity",
                "repo-owner-001",
                "--message-intent",
                "Notify the accountable repository owner about the reviewed permission change.",
                "--escalation-reason",
                "Reviewed GitHub audit evidence requires bounded owner notification.",
                "--expires-at",
                (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
                "--action-request-id",
                "action-request-cli-reviewed-001",
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["action_request_id"], "action-request-cli-reviewed-001")
        self.assertEqual(payload["case_id"], promoted_case.case_id)
        self.assertEqual(payload["alert_id"], promoted_case.alert_id)
        self.assertEqual(payload["requester_identity"], "analyst-001")
        self.assertEqual(payload["lifecycle_state"], "pending_approval")
        self.assertEqual(
            payload["policy_evaluation"],
            {
                "approval_requirement": "human_required",
                "approval_requirement_override": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )
        self.assertEqual(
            payload["requested_payload"]["action_type"],
            "notify_identity_owner",
        )
        self.assertEqual(
            payload["requested_payload"]["recommendation_id"],
            recommendation.recommendation_id,
        )

    def test_cli_inspect_case_detail_renders_action_review_states(self) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_states_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["current_action_review"]["review_state"], "pending")
        self.assertEqual(
            payload["current_action_review"]["action_request_id"],
            seeded["replacement_request"].action_request_id,
        )
        action_reviews_by_id = {
            record["action_request_id"]: record for record in payload["action_reviews"]
        }
        self.assertEqual(
            action_reviews_by_id[seeded["pending_request"].action_request_id]["review_state"],
            "pending",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["rejected_request"].action_request_id][
                "review_state"
            ],
            "rejected",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["rejected_request"].action_request_id][
                "approver_identities"
            ],
            ["approver-rejected-001"],
        )
        self.assertEqual(
            action_reviews_by_id[seeded["expired_request"].action_request_id]["review_state"],
            "expired",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["superseded_request"].action_request_id][
                "review_state"
            ],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[seeded["superseded_request"].action_request_id][
                "replacement_action_request_id"
            ],
            seeded["replacement_request"].action_request_id,
        )

    def test_cli_inspect_case_detail_classifies_terminal_non_delegated_review_path_health(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_states_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        action_reviews_by_id = {
            record["action_request_id"]: record for record in payload["action_reviews"]
        }
        expected_paths = {
            "ingest": {
                "state": "healthy",
                "reason": "review_closed_before_ingest",
            },
            "delegation": {
                "state": "healthy",
                "reason": "review_closed_without_delegation",
            },
            "provider": {
                "state": "healthy",
                "reason": "review_closed_before_provider",
            },
            "persistence": {
                "state": "healthy",
                "reason": "review_closed_before_reconciliation",
            },
        }

        for action_request in (
            seeded["rejected_request"],
            seeded["expired_request"],
            seeded["superseded_request"],
        ):
            review = action_reviews_by_id[action_request.action_request_id]
            self.assertEqual(review["path_health"]["overall_state"], "healthy")
            self.assertEqual(review["path_health"]["paths"], expected_paths)

    def test_cli_inspect_case_detail_renders_review_timeline_and_mismatch_details(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self._assert_review_timeline_snapshot(review, seeded)

    def test_cli_inspect_case_detail_renders_handoff_and_manual_fallback_visibility(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Waiting until the next business-hours cycle is unsafe for this repository owner change.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-visibility-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=request.expires_at,
            )
        )
        service.persist_record(
            replace(
                request,
                approval_decision_id=approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        promoted_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the approval and fallback review at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        promoted_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="The reviewed action remains unresolved and must stay visible for the next analyst.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )
        fallback_stdout = io.StringIO()
        main.main(
            [
                "record-action-review-manual-fallback",
                "--action-request-id",
                request.action_request_id,
                "--fallback-at",
                (reviewed_at + timedelta(minutes=45)).isoformat(),
                "--fallback-actor-identity",
                "analyst-003",
                "--authority-boundary",
                "approved_human_fallback",
                "--reason",
                "The reviewed automation path was unavailable after approval.",
                "--action-taken",
                "Notified the accountable repository owner using the approved manual procedure.",
                "--verification-evidence-id",
                evidence_id,
                "--residual-uncertainty",
                "Awaiting written owner acknowledgement in the next review window.",
            ],
            stdout=fallback_stdout,
            service=service,
        )
        escalation_stdout = io.StringIO()
        main.main(
            [
                "record-action-review-escalation-note",
                "--action-request-id",
                request.action_request_id,
                "--escalated-at",
                (reviewed_at + timedelta(minutes=15)).isoformat(),
                "--escalated-by-identity",
                "analyst-003",
                "--escalated-to",
                "on-call-manager-001",
                "--note",
                "On-call manager notified because the open approval could not be left unattended.",
            ],
            stdout=escalation_stdout,
            service=service,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["review_state"], "unresolved")
        self.assertEqual(
            review["runtime_visibility"]["after_hours_handoff"]["handoff_owner"],
            "analyst-002",
        )
        self.assertEqual(
            review["runtime_visibility"]["after_hours_handoff"]["disposition"],
            "business_hours_handoff",
        )
        self.assertEqual(
            review["runtime_visibility"]["after_hours_handoff"]["rationale"],
            "The reviewed action remains unresolved and must stay visible for the next analyst.",
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["action_request_id"],
            request.action_request_id,
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["fallback_at"],
            (reviewed_at + timedelta(minutes=45)).isoformat(),
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalation_reason"],
            "Waiting until the next business-hours cycle is unsafe for this repository owner change.",
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-001",
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalated_by_identity"],
            "analyst-003",
        )

    def test_cli_inspect_case_detail_scopes_runtime_visibility_to_the_matching_action_review(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep unresolved ownership explicit across multiple reviewed action requests.",
        )
        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the first reviewed permission change.",
            escalation_reason="First reviewed request remains approval-bound.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-visibility-scope-001",
        )
        first_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-visibility-scope-001",
                action_request_id=first_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(first_request.target_scope),
                payload_hash=first_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=first_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                first_request,
                approval_decision_id=first_approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-002",
            message_intent="Notify the accountable repository owner about the second reviewed permission change.",
            escalation_reason="Second reviewed request remains approval-bound.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-visibility-scope-002",
        )
        second_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-visibility-scope-002",
                action_request_id=second_request.action_request_id,
                approver_identities=("approver-002",),
                target_snapshot=dict(second_request.target_scope),
                payload_hash=second_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=10),
                lifecycle_state="approved",
                approved_expires_at=second_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                second_request,
                approval_decision_id=second_approval.approval_decision_id,
                lifecycle_state="unresolved",
            )
        )
        promoted_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the approval review at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        promoted_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Keep the unresolved action review explicit for the next analyst.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )
        main.main(
            [
                "record-action-review-manual-fallback",
                "--action-request-id",
                first_request.action_request_id,
                "--fallback-at",
                (reviewed_at + timedelta(minutes=30)).isoformat(),
                "--fallback-actor-identity",
                "analyst-002",
                "--authority-boundary",
                "approved_human_fallback",
                "--reason",
                "The first reviewed automation path was unavailable after approval.",
                "--action-taken",
                "Used the approved manual procedure for the first request only.",
                "--verification-evidence-id",
                evidence_id,
            ],
            stdout=io.StringIO(),
            service=service,
        )
        main.main(
            [
                "record-action-review-escalation-note",
                "--action-request-id",
                first_request.action_request_id,
                "--escalated-at",
                (reviewed_at + timedelta(minutes=12)).isoformat(),
                "--escalated-by-identity",
                "analyst-002",
                "--escalated-to",
                "on-call-manager-000",
                "--note",
                "On-call manager notified because the first open approval could not be left unattended.",
            ],
            stdout=io.StringIO(),
            service=service,
        )
        main.main(
            [
                "record-action-review-manual-fallback",
                "--action-request-id",
                second_request.action_request_id,
                "--fallback-at",
                (reviewed_at + timedelta(minutes=45)).isoformat(),
                "--fallback-actor-identity",
                "analyst-003",
                "--authority-boundary",
                "approved_human_fallback",
                "--reason",
                "The reviewed automation path was unavailable after approval.",
                "--action-taken",
                "Used the approved manual procedure for the second request only.",
                "--verification-evidence-id",
                evidence_id,
                "--residual-uncertainty",
                "Awaiting written owner acknowledgement in the next review window.",
            ],
            stdout=io.StringIO(),
            service=service,
        )
        main.main(
            [
                "record-action-review-escalation-note",
                "--action-request-id",
                second_request.action_request_id,
                "--escalated-at",
                (reviewed_at + timedelta(minutes=15)).isoformat(),
                "--escalated-by-identity",
                "analyst-003",
                "--escalated-to",
                "on-call-manager-001",
                "--note",
                "On-call manager notified because the second open approval could not be left unattended.",
            ],
            stdout=io.StringIO(),
            service=service,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        reviews_by_id = {
            review["action_request_id"]: review for review in payload["action_reviews"]
        }
        first_review = reviews_by_id[first_request.action_request_id]
        second_review = reviews_by_id[second_request.action_request_id]

        self.assertEqual(
            first_review["runtime_visibility"]["after_hours_handoff"]["rationale"],
            "Keep the unresolved action review explicit for the next analyst.",
        )
        self.assertEqual(
            first_review["runtime_visibility"]["manual_fallback"]["action_request_id"],
            first_request.action_request_id,
        )
        self.assertEqual(
            first_review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            first_approval.approval_decision_id,
        )
        self.assertEqual(
            first_review["runtime_visibility"]["manual_fallback"]["fallback_actor_identity"],
            "analyst-002",
        )
        self.assertEqual(
            first_review["runtime_visibility"]["escalation_notes"]["escalation_reason"],
            "First reviewed request remains approval-bound.",
        )
        self.assertEqual(
            first_review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-000",
        )
        self.assertEqual(
            first_review["runtime_visibility"]["escalation_notes"]["escalated_by_identity"],
            "analyst-002",
        )
        self.assertEqual(
            second_review["runtime_visibility"]["manual_fallback"]["action_request_id"],
            second_request.action_request_id,
        )
        self.assertEqual(
            second_review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            second_approval.approval_decision_id,
        )
        self.assertEqual(
            second_review["runtime_visibility"]["escalation_notes"]["escalation_reason"],
            "Second reviewed request remains approval-bound.",
        )
        self.assertEqual(
            second_review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-001",
        )
        self.assertEqual(
            second_review["runtime_visibility"]["escalation_notes"]["escalated_by_identity"],
            "analyst-003",
        )

    def test_cli_inspect_case_detail_hides_after_hours_handoff_for_completed_review_history(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep only live unresolved review chains marked as after-hours handoff.",
        )
        completed_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the completed reviewed change.",
            escalation_reason="Completed reviewed request should not inherit the active handoff note.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-handoff-history-001",
        )
        unresolved_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-002",
            message_intent="Notify the accountable repository owner about the unresolved reviewed change.",
            escalation_reason="Unresolved reviewed request should retain the active handoff note.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-handoff-history-002",
        )
        service.persist_record(
            replace(
                completed_request,
                lifecycle_state="completed",
                requested_at=completed_request.requested_at - timedelta(minutes=10),
            )
        )
        service.persist_record(replace(unresolved_request, lifecycle_state="unresolved"))
        service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-002",
            handoff_note="Resume the unresolved approval review at next business-hours open.",
            follow_up_evidence_ids=(evidence_id,),
        )
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Keep only the unresolved reviewed action visible for the next analyst handoff.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        reviews_by_id = {
            review["action_request_id"]: review for review in payload["action_reviews"]
        }
        completed_visibility = (
            reviews_by_id[completed_request.action_request_id]["runtime_visibility"] or {}
        )
        self.assertNotIn("after_hours_handoff", completed_visibility)
        self.assertEqual(
            reviews_by_id[unresolved_request.action_request_id]["runtime_visibility"][
                "after_hours_handoff"
            ]["handoff_owner"],
            "analyst-002",
        )

    def test_cli_runtime_visibility_ignores_non_handoff_triage_dispositions(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep routine pending approval triage from being mislabeled as a handoff.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Routine approval follow-up remains open.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-non-handoff-triage-001",
        )
        service.persist_record(replace(action_request, lifecycle_state="unresolved"))
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="pending_approval",
            rationale="Approval is still pending, but no after-hours handoff has been recorded.",
            recorded_at=reviewed_at + timedelta(minutes=20),
        )

        case_stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=case_stdout,
            service=service,
        )
        case_payload = json.loads(case_stdout.getvalue())

        queue_stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=queue_stdout, service=service)
        queue_payload = json.loads(queue_stdout.getvalue())

        self.assertIsNone(case_payload["current_action_review"]["runtime_visibility"])
        self.assertEqual(queue_payload["total_records"], 1)
        self.assertIsNone(queue_payload["records"][0]["current_action_review"]["runtime_visibility"])

    def test_cli_inspect_case_detail_keeps_preapproval_unresolved_review_path_health_delayed(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, _reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep pre-approval follow-up visible without overstating it as a post-approval silent failure.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Approval follow-up remains open.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-preapproval-unresolved-path-health-001",
        )
        service.persist_record(replace(action_request, lifecycle_state="unresolved"))

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]

        self.assertEqual(review["review_state"], "unresolved")
        self.assertEqual(review["path_health"]["overall_state"], "delayed")
        self.assertEqual(
            review["path_health"]["paths"],
            {
                "ingest": {
                    "state": "delayed",
                    "reason": "awaiting_ingest_signal",
                },
                "delegation": {
                    "state": "delayed",
                    "reason": "awaiting_approval",
                },
                "provider": {
                    "state": "delayed",
                    "reason": "awaiting_delegation",
                },
                "persistence": {
                    "state": "delayed",
                    "reason": "awaiting_reconciliation",
                },
            },
        )

    def test_cli_inspect_case_detail_classifies_stale_delegation_receipt_timeout(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Show overdue delegation receipt gaps as degraded path-health signals.",
        )
        base_now = datetime.now(timezone.utc)
        requested_at = base_now - timedelta(hours=2)
        delegated_at = base_now - timedelta(hours=1, minutes=50)
        expired_at = base_now - timedelta(hours=1)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep overdue delegation receipt gaps explicit in operator inspection.",
            escalation_reason="Delegation receipt timeouts must be visible without external dashboards.",
            expires_at=base_now + timedelta(hours=4),
            action_request_id="action-request-cli-stale-dispatching-path-health-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-stale-dispatching-path-health-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expired_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                requested_at=requested_at,
                expires_at=expired_at,
                lifecycle_state="executing",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-cli-stale-dispatching-path-health-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-cli-stale-dispatching-path-health-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-cli-stale-dispatching-path-health-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=delegated_at,
                expires_at=expired_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="dispatching",
            )
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]

        self.assertEqual(review["review_state"], "executing")
        self.assertEqual(review["path_health"]["overall_state"], "degraded")
        self.assertEqual(
            review["path_health"]["paths"],
            {
                "ingest": {
                    "state": "degraded",
                    "reason": "ingest_signal_timeout",
                },
                "delegation": {
                    "state": "degraded",
                    "reason": "delegation_receipt_timeout",
                },
                "provider": {
                    "state": "degraded",
                    "reason": "provider_receipt_timeout",
                },
                "persistence": {
                    "state": "degraded",
                    "reason": "reconciliation_timeout",
                },
            },
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_outcome(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        requested_at = reviewed_at + timedelta(minutes=10)
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        approved_target_scope = {
            "case_id": promoted_case.case_id,
            "alert_id": promoted_case.alert_id,
            "finding_id": promoted_case.finding_id,
            "coordination_reference_id": "coord-ref-cli-create-ticket-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = phase26_create_tracking_ticket_payload(
            case_id=promoted_case.case_id,
            alert_id=promoted_case.alert_id,
            finding_id=promoted_case.finding_id,
            coordination_reference_id="coord-ref-cli-create-ticket-001",
        )
        payload_hash = _approved_payload_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-create-ticket-outcome-001",
                action_request_id="action-request-cli-create-ticket-outcome-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=reviewed_at + timedelta(hours=4),
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-cli-create-ticket-outcome-001",
                approval_decision_id=approval.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key="idempotency-cli-create-ticket-outcome-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=reviewed_at + timedelta(hours=4),
                lifecycle_state="approved",
                requested_payload=approved_payload,
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-cli-create-ticket-outcome-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id="action-request-cli-create-ticket-outcome-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-cli-create-ticket-outcome-001",
                    "approval_decision_id": approval.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": payload_hash,
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": downstream_binding["external_receipt_id"],
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=reviewed_at + timedelta(hours=1),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]

        self.assertEqual(
            review["coordination_ticket_outcome"]["status"],
            "created",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["coordination_reference_id"],
            "coord-ref-cli-create-ticket-001",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["coordination_target_type"],
            "zammad",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["external_receipt_id"],
            downstream_binding["external_receipt_id"],
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["ticket_reference_url"],
            downstream_binding["ticket_reference_url"],
        )

    def test_cli_inspect_case_detail_repairs_nested_create_tracking_ticket_approval_linkage(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="repaired-approval-001",
            coordination_reference_id="coord-ref-cli-create-ticket-repaired-approval-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id=seeded["action_request"].action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": seeded["action_request"].idempotency_key,
                    "approval_decision_id": seeded["approval"].approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": seeded["payload_hash"],
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": downstream_binding["external_receipt_id"],
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=reviewed_at + timedelta(hours=1),
        )
        service.persist_record(
            replace(seeded["action_request"], approval_decision_id=None)
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(
            review["approval_decision_id"],
            seeded["approval"].approval_decision_id,
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["approval_decision_id"],
            seeded["approval"].approval_decision_id,
        )
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "created")

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_mismatch(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="mismatch-001",
            coordination_reference_id="coord-ref-cli-create-ticket-mismatch-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id=seeded["action_request"].action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": seeded["action_request"].idempotency_key,
                    "approval_decision_id": seeded["approval"].approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": seeded["payload_hash"],
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": "shuffle-receipt-cli-drifted-001",
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=reviewed_at + timedelta(hours=1),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "mismatch")
        self.assertEqual(
            review["coordination_ticket_outcome"]["mismatch"]["mismatch_summary"],
            "coordination receipt mismatch between authoritative action execution "
            "and observed downstream execution",
        )

    def test_cli_inspect_case_detail_omits_create_tracking_ticket_outcome_for_terminal_non_delegated_reviews(
        self,
    ) -> None:
        for review_state in ("rejected", "expired", "superseded", "canceled"):
            with self.subTest(review_state=review_state):
                _, service, promoted_case, _evidence_id, reviewed_at = (
                    self._build_phase19_in_scope_case()
                )
                seeded = self._seed_create_tracking_ticket_request(
                    service=service,
                    promoted_case=promoted_case,
                    reviewed_at=reviewed_at,
                    suffix=f"closed-without-delegation-{review_state}",
                    coordination_reference_id=(
                        f"coord-ref-cli-create-ticket-closed-without-delegation-{review_state}"
                    ),
                )
                if review_state in {"rejected", "expired"}:
                    service.persist_record(
                        replace(seeded["approval"], lifecycle_state=review_state)
                    )
                service.persist_record(
                    replace(seeded["action_request"], lifecycle_state=review_state)
                )

                stdout = io.StringIO()
                main.main(
                    ["inspect-case-detail", "--case-id", promoted_case.case_id],
                    stdout=stdout,
                    service=service,
                )

                payload = json.loads(stdout.getvalue())
                review = payload["current_action_review"]
                self.assertEqual(review["review_state"], review_state)
                self.assertIsNone(review["coordination_ticket_outcome"])

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_timeout(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = datetime.now(timezone.utc)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="timeout-001",
            coordination_reference_id="coord-ref-cli-create-ticket-timeout-001",
        )

        with mock.patch.object(
            type(service._shuffle),
            "dispatch_approved_action",
            autospec=True,
            side_effect=TimeoutError("synthetic create-tracking-ticket timeout"),
        ):
            with self.assertRaisesRegex(
                TimeoutError,
                "synthetic create-tracking-ticket timeout",
            ):
                service.delegate_approved_action_to_shuffle(
                    action_request_id=seeded["action_request"].action_request_id,
                    approved_payload=seeded["approved_payload"],
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "timeout")
        self.assertEqual(
            review["coordination_ticket_outcome"]["timeout"]["reason"],
            "dispatch_timeout",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["timeout"]["path"],
            "provider",
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_provider_failure_as_timeout(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="failure-001",
            coordination_reference_id="coord-ref-cli-create-ticket-failure-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        service.persist_record(replace(execution, lifecycle_state="failed"))

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "timeout")
        self.assertEqual(
            review["coordination_ticket_outcome"]["timeout"]["reason"],
            "execution_failed",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["timeout"]["path"],
            "provider",
        )

    def test_cli_inspect_case_detail_prefers_provider_failure_over_derived_timeouts(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        overdue_requested_at = datetime.now(timezone.utc) - timedelta(hours=2)
        overdue_expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="failure-precedence-001",
            coordination_reference_id="coord-ref-cli-create-ticket-failure-precedence-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        service.persist_record(
            replace(
                seeded["approval"],
                decided_at=overdue_requested_at + timedelta(minutes=5),
                approved_expires_at=overdue_expires_at,
            )
        )
        action_request = service.get_record(
            ActionRequestRecord, seeded["action_request"].action_request_id
        )
        service.persist_record(
            replace(
                action_request,
                requested_at=overdue_requested_at,
                expires_at=overdue_expires_at,
            )
        )
        service.persist_record(
            replace(
                execution,
                delegated_at=overdue_requested_at + timedelta(minutes=10),
                expires_at=overdue_expires_at,
                lifecycle_state="failed",
            )
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(
            review["path_health"]["paths"]["ingest"]["reason"],
            "ingest_signal_timeout",
        )
        self.assertEqual(
            review["path_health"]["paths"]["persistence"]["reason"],
            "reconciliation_timeout",
        )
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "timeout")
        self.assertEqual(
            review["coordination_ticket_outcome"]["timeout"]["reason"],
            "execution_failed",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["timeout"]["path"],
            "provider",
        )

    def test_cli_inspect_case_detail_surfaces_create_tracking_ticket_manual_fallback(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="manual-fallback-001",
            coordination_reference_id="coord-ref-cli-create-ticket-manual-fallback-001",
        )
        service.persist_record(
            replace(
                seeded["action_request"],
                lifecycle_state="unresolved",
            )
        )
        service.record_action_review_manual_fallback(
            action_request_id=seeded["action_request"].action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed create-ticket automation path was unavailable after approval.",
            action_taken="Opened the reviewed tracking ticket manually using the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting downstream operator acknowledgement in the next review window.",
        )
        service.persist_record(
            replace(
                service.get_record(AlertRecord, promoted_case.alert_id),
                coordination_reference_id=(
                    "coord-ref-cli-create-ticket-manual-fallback-001"
                ),
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                service.get_record(CaseRecord, promoted_case.case_id),
                coordination_reference_id=(
                    "coord-ref-cli-create-ticket-manual-fallback-001"
                ),
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(payload["external_ticket_reference"]["status"], "present")
        self.assertEqual(
            review["coordination_ticket_outcome"]["status"],
            "manual_fallback",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["manual_fallback"]["action_taken"],
            "Opened the reviewed tracking ticket manually using the approved procedure.",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["manual_fallback"][
                "fallback_actor_identity"
            ],
            "analyst-003",
        )

    def test_cli_inspect_case_detail_keeps_created_status_when_manual_fallback_is_recorded_after_success(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = self._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="created-with-fallback-001",
            coordination_reference_id="coord-ref-cli-create-ticket-created-with-fallback-001",
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=seeded["action_request"].action_request_id,
            approved_payload=seeded["approved_payload"],
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        downstream_binding = execution.provenance["downstream_binding"]
        service.reconcile_action_execution(
            action_request_id=seeded["action_request"].action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": seeded["action_request"].idempotency_key,
                    "approval_decision_id": seeded["approval"].approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": seeded["payload_hash"],
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": downstream_binding["external_receipt_id"],
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=reviewed_at + timedelta(hours=1),
        )
        service.record_action_review_manual_fallback(
            action_request_id=seeded["action_request"].action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-004",
            authority_boundary="approved_human_fallback",
            reason="Business-hours operator added manual fallback notes after a completed create-ticket review.",
            action_taken="Captured manual ticket fallback instructions for the reviewed coordination flow.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting operator acknowledgement during the next review window.",
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["coordination_ticket_outcome"]["status"], "created")
        self.assertEqual(
            review["coordination_ticket_outcome"]["manual_fallback"]["action_taken"],
            "Captured manual ticket fallback instructions for the reviewed coordination flow.",
        )
        self.assertEqual(
            review["coordination_ticket_outcome"]["manual_fallback"][
                "fallback_actor_identity"
            ],
            "analyst-004",
        )

    def test_cli_inspect_case_detail_keeps_after_hours_handoff_visible_for_non_executed_review_states(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_states_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )
        service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at + timedelta(hours=8),
            handoff_owner="analyst-visibility-001",
            handoff_note="Keep non-executed review states explicit for the next analyst handoff.",
            follow_up_evidence_ids=(evidence_id,),
        )
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Expired, rejected, and superseded reviewed requests must remain visibly handed off.",
            recorded_at=reviewed_at + timedelta(hours=8),
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        reviews_by_id = {
            review["action_request_id"]: review for review in payload["action_reviews"]
        }

        for action_request in (
            seeded["expired_request"],
            seeded["rejected_request"],
            seeded["superseded_request"],
        ):
            visibility = (
                reviews_by_id[action_request.action_request_id]["runtime_visibility"] or {}
            )
            self.assertEqual(
                visibility["after_hours_handoff"]["handoff_owner"],
                "analyst-visibility-001",
            )
            self.assertEqual(
                visibility["after_hours_handoff"]["disposition"],
                "business_hours_handoff",
            )
            self.assertEqual(
                visibility["after_hours_handoff"]["rationale"],
                "Expired, rejected, and superseded reviewed requests must remain visibly handed off.",
            )

    def test_cli_inspect_alert_detail_renders_alert_scoped_runtime_visibility(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep alert-scoped follow-up explicit when case linkage is absent.",
        )
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="The alert-scoped reviewed request cannot wait for the next shift.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-alert-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-alert-visibility-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=request.expires_at,
            )
        )
        request = service.persist_record(
            replace(
                request,
                approval_decision_id=approval.approval_decision_id,
                case_id=None,
                lifecycle_state="unresolved",
            )
        )
        service.record_action_review_manual_fallback(
            action_request_id=request.action_request_id,
            fallback_at=reviewed_at + timedelta(minutes=45),
            fallback_actor_identity="analyst-003",
            authority_boundary="approved_human_fallback",
            reason="The reviewed automation path was unavailable after approval.",
            action_taken="Used the approved manual procedure while the alert remained unlinked to casework.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting written owner acknowledgement in the next review window.",
        )
        service.record_action_review_escalation_note(
            action_request_id=request.action_request_id,
            escalated_at=reviewed_at + timedelta(minutes=15),
            escalated_by_identity="analyst-004",
            escalated_to="on-call-manager-001",
            note="On-call manager notified because the alert-scoped approval could not be left unattended.",
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", promoted_case.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["action_request_id"], request.action_request_id)
        self.assertEqual(review["review_state"], "unresolved")
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["approval_decision_id"],
            approval.approval_decision_id,
        )
        self.assertEqual(
            review["runtime_visibility"]["manual_fallback"]["fallback_actor_identity"],
            "analyst-003",
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalated_to"],
            "on-call-manager-001",
        )
        self.assertEqual(
            review["runtime_visibility"]["escalation_notes"]["escalated_by_identity"],
            "analyst-004",
        )

    def test_cli_inspect_alert_detail_classifies_unresolved_review_without_execution(
        self,
    ) -> None:
        _, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep post-approval silent failures visible on the reviewed action path.",
        )
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="The alert-scoped reviewed request cannot stay implicit after approval.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-cli-alert-unresolved-path-health-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-cli-alert-unresolved-path-health-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=request.expires_at,
            )
        )
        service.persist_record(
            replace(
                request,
                approval_decision_id=approval.approval_decision_id,
                case_id=None,
                lifecycle_state="unresolved",
            )
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", promoted_case.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["review_state"], "unresolved")
        self.assertEqual(review["path_health"]["overall_state"], "degraded")
        self.assertEqual(
            review["path_health"]["paths"],
            {
                "ingest": {
                    "state": "degraded",
                    "reason": "ingest_signal_missing_after_approval",
                },
                "delegation": {
                    "state": "degraded",
                    "reason": "reviewed_delegation_missing_after_approval",
                },
                "provider": {
                    "state": "degraded",
                    "reason": "provider_signal_missing_after_approval",
                },
                "persistence": {
                    "state": "degraded",
                    "reason": "reconciliation_missing_after_approval",
                },
            },
        )

    def test_cli_inspect_case_detail_keeps_reconciliation_bound_to_selected_execution(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_retried_execution_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(
            review["action_execution_id"],
            seeded["selected_action_execution"].action_execution_id,
        )
        self.assertEqual(
            review["delegation_id"],
            seeded["selected_action_execution"].delegation_id,
        )
        self.assertEqual(
            review["reconciliation_id"],
            seeded["selected_reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["mismatch_inspection"],
            None,
        )
        self.assertEqual(
            review["timeline"][3]["occurred_at"],
            None,
        )
        self.assertEqual(
            review["timeline"][4]["record_id"],
            seeded["selected_reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["timeline"][4]["details"]["execution_run_id"],
            seeded["selected_action_execution"].execution_run_id,
        )

    def test_cli_inspect_case_detail_preserves_predelegation_reconciliation_visibility(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_predelegation_reconciliation_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", promoted_case.case_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(
            review["action_execution_id"],
            seeded["action_execution"].action_execution_id,
        )
        self.assertEqual(
            review["reconciliation_id"],
            seeded["reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["timeline"][4]["record_id"],
            seeded["reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["timeline"][4]["state"],
            "pending",
        )
        self.assertEqual(
            review["mismatch_inspection"]["reconciliation_id"],
            seeded["reconciliation"].reconciliation_id,
        )
        self.assertEqual(
            review["mismatch_inspection"]["lifecycle_state"],
            "pending",
        )

    def test_cli_inspect_alert_detail_renders_review_timeline_and_mismatch_details(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", promoted_case.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self._assert_review_timeline_snapshot(payload["current_action_review"], seeded)

    def test_cli_inspect_alert_detail_classifies_path_health_for_mismatched_review(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(
            ["inspect-alert-detail", "--alert-id", promoted_case.alert_id],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        review = payload["current_action_review"]
        self.assertEqual(review["path_health"]["overall_state"], "degraded")
        self.assertTrue(review["path_health"]["summary"])
        self.assertEqual(
            review["path_health"]["paths"],
            {
                "ingest": {
                    "state": "degraded",
                    "reason": "mismatch_detected",
                },
                "delegation": {
                    "state": "healthy",
                    "reason": "delegated",
                },
                "provider": {
                    "state": "delayed",
                    "reason": "awaiting_authoritative_outcome",
                },
                "persistence": {
                    "state": "degraded",
                    "reason": "reconciliation_mismatched",
                },
            },
        )

    def test_cli_inspect_analyst_queue_renders_review_timeline_and_mismatch_details(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = self._build_phase19_in_scope_case()
        seeded = self._seed_action_review_timeline_mismatch_for_case(
            service,
            promoted_case,
            reviewed_at,
            evidence_id,
        )

        stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["total_records"], 1)
        self._assert_review_timeline_snapshot(
            payload["records"][0]["current_action_review"],
            seeded,
        )

    def test_cli_rejects_case_scoped_out_of_scope_advisory_reads_as_usage_errors(
        self,
    ) -> None:
        service, recommendation, ai_trace = self._build_out_of_scope_case_advisory_review_records(
            fixture_name="github-audit-alert.json"
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )

        for command, record_family, record_id in (
            (
                "inspect-advisory-output",
                "recommendation",
                recommendation.recommendation_id,
            ),
            (
                "inspect-advisory-output",
                "ai_trace",
                ai_trace.ai_trace_id,
            ),
            (
                "render-recommendation-draft",
                "recommendation",
                recommendation.recommendation_id,
            ),
            (
                "render-recommendation-draft",
                "ai_trace",
                ai_trace.ai_trace_id,
            ),
        ):
            stderr = io.StringIO()
            with self.subTest(
                command=command,
                record_family=record_family,
            ), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc_info:
                    main.main(
                        [
                            command,
                            "--family",
                            record_family,
                            "--record-id",
                            record_id,
                        ],
                        service=service,
                    )

            self.assertEqual(exc_info.exception.code, 2)
            self.assertIn(expected_message, stderr.getvalue())

    def test_cli_rejects_case_family_out_of_scope_advisory_reads_as_usage_errors(
        self,
    ) -> None:
        service, promoted_case = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )

        for command in (
            "inspect-assistant-context",
            "inspect-advisory-output",
            "render-recommendation-draft",
        ):
            stderr = io.StringIO()
            with self.subTest(command=command), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc_info:
                    main.main(
                        [
                            command,
                            "--family",
                            "case",
                            "--record-id",
                            promoted_case.case_id,
                        ],
                        service=service,
                    )

            self.assertEqual(exc_info.exception.code, 2)
            self.assertIn(expected_message, stderr.getvalue())

    def test_cli_rejects_case_scoped_advisory_reads_without_linked_case_as_usage_errors(
        self,
    ) -> None:
        service, recommendation, ai_trace = (
            self._build_case_scoped_advisory_records_without_case_lineage()
        )
        expected_message = (
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice"
        )

        for command, record_family, record_id in (
            (
                "inspect-advisory-output",
                "recommendation",
                recommendation.recommendation_id,
            ),
            (
                "inspect-advisory-output",
                "ai_trace",
                ai_trace.ai_trace_id,
            ),
            (
                "render-recommendation-draft",
                "recommendation",
                recommendation.recommendation_id,
            ),
            (
                "render-recommendation-draft",
                "ai_trace",
                ai_trace.ai_trace_id,
            ),
        ):
            stderr = io.StringIO()
            with self.subTest(
                command=command,
                record_family=record_family,
            ), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as exc_info:
                    main.main(
                        [
                            command,
                            "--family",
                            record_family,
                            "--record-id",
                            record_id,
                        ],
                        service=service,
                    )

            self.assertEqual(exc_info.exception.code, 2)
            self.assertIn(expected_message, stderr.getvalue())

    def test_cli_renders_recommendation_draft_with_source_review_outcome(self) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-draft-cli-outcome-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="accepted",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        stdout = io.StringIO()
        main.main(
            [
                "render-recommendation-draft",
                "--family",
                "recommendation",
                "--record-id",
                recommendation.recommendation_id,
            ],
            stdout=stdout,
            service=service,
        )

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["record_family"], "recommendation")
        self.assertEqual(payload["record_id"], recommendation.recommendation_id)
        self.assertEqual(
            payload["recommendation_draft"]["source_output_kind"],
            "recommendation_draft",
        )
        self.assertEqual(
            payload["recommendation_draft"]["review_lifecycle_state"],
            "accepted",
        )
        self.assertIn(
            "has been accepted and is anchored",
            payload["recommendation_draft"]["cited_summary"]["text"],
        )
        self.assertNotIn(
            "remains under review",
            payload["recommendation_draft"]["cited_summary"]["text"],
        )
        self.assertIn(
            evidence_id,
            payload["recommendation_draft"]["citations"],
        )

    def test_cli_renders_identity_rich_analyst_queue_view_with_reviewed_context(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("microsoft-365-audit-alert.json")
            ),
        )
        service.promote_alert_to_case(admitted.alert.alert_id)

        stdout = io.StringIO()
        main.main(["inspect-analyst-queue"], stdout=stdout, service=service)

        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["total_records"], 1)
        self.assertEqual(
            payload["records"][0]["reviewed_context"]["source"]["source_family"],
            "microsoft_365_audit",
        )
        self.assertEqual(
            payload["records"][0]["reviewed_context"]["identity"]["actor"]["identity_id"],
            "alex@contoso.com",
        )

    def test_cli_rejects_unknown_record_family_as_usage_error(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc_info:
                main.main(
                    ["inspect-records", "--family", "unknown-family"],
                    service=service,
                )

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("Unsupported control-plane record family", stderr.getvalue())

    def test_cli_rejects_blank_alert_detail_identifier_as_usage_error(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as exc_info:
                main.main(
                    ["inspect-alert-detail", "--alert-id", "   "],
                    service=service,
                )

        self.assertEqual(exc_info.exception.code, 2)
        self.assertIn("alert_id must be a non-empty string", stderr.getvalue())

    def test_cli_renders_inspection_views_against_empty_postgresql_store(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        records_stdout = io.StringIO()
        status_stdout = io.StringIO()

        main.main(
            ["inspect-records", "--family", "alert"],
            stdout=records_stdout,
            service=service,
        )
        main.main(
            ["inspect-reconciliation-status"],
            stdout=status_stdout,
            service=service,
        )

        records_payload = json.loads(records_stdout.getvalue())
        status_payload = json.loads(status_stdout.getvalue())

        self.assertTrue(records_payload["read_only"])
        self.assertEqual(records_payload["record_family"], "alert")
        self.assertEqual(records_payload["total_records"], 0)
        self.assertEqual(records_payload["records"], [])

        self.assertTrue(status_payload["read_only"])
        self.assertEqual(status_payload["total_records"], 0)
        self.assertIsNone(status_payload["latest_compared_at"])
        self.assertEqual(status_payload["by_lifecycle_state"], {})
        self.assertEqual(status_payload["by_ingest_disposition"], {})
        self.assertEqual(status_payload["records"], [])


if __name__ == "__main__":
    unittest.main()
