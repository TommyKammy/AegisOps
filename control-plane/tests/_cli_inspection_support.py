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



class ControlPlaneCliInspectionTestBase(unittest.TestCase):
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

    def _build_phase19_in_scope_alert_without_case(
        self,
        *,
        store: object | None = None,
        host: str | None = None,
        port: int | None = None,
    ) -> tuple[object, AegisOpsControlPlaneService, AlertRecord, str, datetime]:
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
        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",  # noqa: S106 - test fixture secret
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        alert = admitted.alert
        evidence_records = tuple(
            evidence
            for evidence in store.list(EvidenceRecord)
            if evidence.alert_id == alert.alert_id
        )
        if not evidence_records:
            raise AssertionError("expected reviewed alert fixture to persist linked evidence")
        reviewed_at = service.list_lifecycle_transitions("alert", alert.alert_id)[-1].transitioned_at
        return store, service, alert, evidence_records[0].evidence_id, reviewed_at

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
