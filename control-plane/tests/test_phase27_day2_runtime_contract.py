from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pathlib
import sys
import tempfile
from typing import Callable
import unittest
from unittest import mock


TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from support.service_persistence import ServicePersistenceTestBase
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.http_protected_surface import authenticate_protected_write
from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    LifecycleTransitionRecord,
    ReconciliationRecord,
)
from postgres_test_support import make_store

import test_phase21_runtime_auth_validation as runtime_auth_tests
import test_runtime_secret_boundary as secret_boundary_tests


class _InterruptedOpenBaoRotationTransport:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def read_secret(
        self,
        *,
        address: str,
        token: str,
        mount: str,
        secret_path: str,
    ) -> str:
        del address
        del token
        del mount
        self.calls.append(secret_path)
        if secret_path == "kv/aegisops/control-plane/wazuh-ingest-shared-secret":
            return "reviewed-shared-secret-v2"
        raise RuntimeError("rotation interrupted before companion secret was current")


class Phase27Day2RuntimeContractTests(ServicePersistenceTestBase):
    def test_phase27_restore_runtime_contract_fails_closed_without_post_restore_bindings(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        readiness = restored_service.inspect_readiness_diagnostics()

        self.assertGreater(restore_summary.restored_record_counts["case"], 0)
        self.assertIn(promoted_case.case_id, restore_summary.restore_drill.verified_case_ids)
        self.assertFalse(restore_summary.restore_drill.drill_passed)
        self.assertEqual(readiness.status, "failing_closed")
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET",
            readiness.startup["missing_bindings"],
        )
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN",
            readiness.startup["missing_bindings"],
        )

    def test_phase27_restore_reconciliation_truth_integrity_keeps_mismatch_reviewable(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs a bounded tracking ticket.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Open one reviewed tracking ticket for daily operator follow-up.",
            lead_id=lead.lead_id,
        )
        action_request = service.create_reviewed_tracking_ticket_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            coordination_reference_id="coord-ref-phase27-restore-truth-001",
            coordination_target_type="zammad",
            ticket_title="Review restored reconciliation mismatch",
            ticket_description=(
                "Preserve the mismatched restore-drill receipt as subordinate evidence."
            ),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-phase27-restore-truth-001",
        )
        approval = service.record_action_approval_decision(
            action_request_id=action_request.action_request_id,
            approver_identity="approver-001",
            authenticated_approver_identity="approver-001",
            decision="grant",
            decision_rationale=(
                "Reviewed tracking ticket remains subordinate to AegisOps workflow truth."
            ),
            decided_at=reviewed_at + timedelta(minutes=5),
            approval_decision_id="approval-phase27-restore-truth-001",
        )
        approved_request = service.get_record(
            ActionRequestRecord,
            action_request.action_request_id,
        )
        assert approved_request is not None
        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=reviewed_at + timedelta(minutes=10),
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        downstream_binding = execution.provenance["downstream_binding"]
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": approval.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": "restored-downstream-receipt-drifted-001",
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": reviewed_at + timedelta(minutes=15),
                    "status": "success",
                },
            ),
            compared_at=reviewed_at + timedelta(minutes=20),
            stale_after=reviewed_at + timedelta(hours=1),
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                admin_bootstrap_token="reviewed-admin-bootstrap-token",
            ),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        readiness = restored_service.inspect_readiness_diagnostics()
        restored_case = restored_service.get_record(CaseRecord, promoted_case.case_id)
        restored_request = restored_service.get_record(
            ActionRequestRecord,
            approved_request.action_request_id,
        )
        restored_execution = restored_service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        restored_reconciliation = restored_service.get_record(
            ReconciliationRecord,
            reconciliation.reconciliation_id,
        )

        self.assertFalse(restore_summary.restore_drill.drill_passed)
        self.assertEqual(readiness.status, "failing_closed")
        self.assertEqual(readiness.metrics["reconciliations"]["mismatched"], 1)
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            reconciliation.reconciliation_id,
        )
        assert restored_case is not None
        assert restored_request is not None
        assert restored_execution is not None
        assert restored_reconciliation is not None
        self.assertEqual(restored_case.lifecycle_state, promoted_case.lifecycle_state)
        self.assertEqual(restored_request.lifecycle_state, "approved")
        self.assertEqual(restored_execution.lifecycle_state, "queued")
        self.assertEqual(restored_reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(restored_reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(
            restored_reconciliation.mismatch_summary,
            "coordination receipt mismatch between authoritative action execution "
            "and observed downstream execution",
        )
        self.assertEqual(
            restored_reconciliation.subject_linkage["external_receipt_ids"],
            (downstream_binding["external_receipt_id"],),
        )

    def test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep degraded health visible on the reviewed readiness path.",
        )
        requested_at = reviewed_at - timedelta(hours=2)
        delegated_at = reviewed_at - timedelta(hours=1, minutes=50)
        expired_at = reviewed_at - timedelta(hours=1)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Preserve degraded-mode visibility for source and automation health.",
            escalation_reason="Operators must not infer healthy runtime state from silence.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase27-day2-readiness-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase27-day2-readiness-001",
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
                action_execution_id="action-execution-phase27-day2-readiness-001",
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase27-day2-readiness-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase27-day2-readiness-001",
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

        readiness = service.inspect_readiness_diagnostics()
        source_health = readiness.metrics["source_health"]
        automation_health = readiness.metrics["automation_substrate_health"]

        self.assertEqual(readiness.status, "failing_closed")
        self.assertEqual(source_health["overall_state"], "degraded")
        self.assertEqual(
            source_health["sources"]["github_audit"]["reason"],
            "ingest_signal_timeout",
        )
        self.assertEqual(
            automation_health["overall_state"],
            "degraded",
        )
        self.assertEqual(
            automation_health["surfaces"]["automation_substrate:shuffle"]["state"],
            "degraded",
        )

    def test_phase27_degraded_source_health_visibility_does_not_advance_workflow_authority(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Keep degraded source-health visible without advancing workflow truth."
            ),
        )
        requested_at = reviewed_at - timedelta(hours=2)
        delegated_at = reviewed_at - timedelta(hours=1, minutes=50)
        expired_at = reviewed_at - timedelta(hours=1)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Show degraded source-health as reviewed context only.",
            escalation_reason=(
                "Operators need degraded source visibility without lifecycle promotion."
            ),
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase27-source-health-visibility-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase27-source-health-visibility-001",
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
                    "action-execution-phase27-source-health-visibility-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase27-source-health-visibility-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase27-source-health-visibility-001",
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

        initial_alerts = tuple(store.list(AlertRecord))
        initial_cases = tuple(store.list(CaseRecord))
        initial_action_requests = tuple(store.list(ActionRequestRecord))
        initial_approvals = tuple(store.list(ApprovalDecisionRecord))
        initial_executions = tuple(store.list(ActionExecutionRecord))
        initial_reconciliations = tuple(store.list(ReconciliationRecord))
        initial_transition_count = len(store.list(LifecycleTransitionRecord))

        readiness = service.inspect_readiness_diagnostics()
        source_health = readiness.metrics["source_health"]
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(readiness.status, "failing_closed")
        self.assertEqual(review_path_health["overall_state"], "degraded")
        self.assertEqual(source_health["overall_state"], "degraded")
        self.assertEqual(source_health["tracked_sources"], 1)
        self.assertEqual(
            source_health["summary"],
            "degraded source health: github_audit ingest signal timeout",
        )
        github_audit = source_health["sources"]["github_audit"]
        self.assertEqual(github_audit["state"], "degraded")
        self.assertEqual(github_audit["reason"], "ingest_signal_timeout")
        self.assertEqual(github_audit["tracked_reviews"], 1)
        self.assertEqual(github_audit["affected_reviews"], 1)
        self.assertEqual(
            github_audit["by_state"],
            {
                "healthy": 0,
                "delayed": 0,
                "degraded": 1,
                "failed": 0,
            },
        )

        self.assertEqual(tuple(store.list(AlertRecord)), initial_alerts)
        self.assertEqual(tuple(store.list(CaseRecord)), initial_cases)
        self.assertEqual(tuple(store.list(ActionRequestRecord)), initial_action_requests)
        self.assertEqual(tuple(store.list(ApprovalDecisionRecord)), initial_approvals)
        self.assertEqual(tuple(store.list(ActionExecutionRecord)), initial_executions)
        self.assertEqual(tuple(store.list(ReconciliationRecord)), initial_reconciliations)
        self.assertEqual(
            len(store.list(LifecycleTransitionRecord)),
            initial_transition_count,
        )

    def test_phase27_identity_contract_fails_closed_for_missing_or_unreviewed_provider_boundary(
        self,
    ) -> None:
        store, _ = make_store()
        startup_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host=runtime_auth_tests.TEST_NON_LOOPBACK_HOST,
                port=8080,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=runtime_auth_tests.REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=(
                    runtime_auth_tests.REVIEWED_WAZUH_PROXY_SECRET
                ),
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_reverse_proxy_secret=(
                    runtime_auth_tests.REVIEWED_SURFACE_PROXY_SECRET
                ),
                protected_surface_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_proxy_service_account=(
                    runtime_auth_tests.REVIEWED_PROXY_SERVICE_ACCOUNT
                ),
                admin_bootstrap_token=runtime_auth_tests.REVIEWED_ADMIN_BOOTSTRAP_TOKEN,
            ),
            store=store,
        )

        startup = startup_service.describe_startup_status()
        readiness = startup_service.inspect_readiness_diagnostics()

        self.assertFalse(startup.startup_ready)
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER",
            startup.missing_bindings,
        )
        self.assertEqual(readiness.status, "failing_closed")

        request_service = runtime_auth_tests._build_service(
            host=runtime_auth_tests.TEST_NON_LOOPBACK_HOST
        )
        with self.assertRaisesRegex(
            PermissionError,
            "protected control-plane surfaces require the reviewed identity provider boundary",
        ):
            request_service.authenticate_protected_surface_request(
                peer_addr="10.10.0.5",
                forwarded_proto="https",
                reverse_proxy_secret_header=(
                    runtime_auth_tests.REVIEWED_SURFACE_PROXY_SECRET
                ),
                proxy_service_account_header=(
                    runtime_auth_tests.REVIEWED_PROXY_SERVICE_ACCOUNT
                ),
                authenticated_identity_provider_header="entra-id",
                authenticated_subject_header="entra-user-001",
                authenticated_identity_header="analyst-001",
                authenticated_role_header="analyst",
                allowed_roles=("analyst",),
            )

    def test_phase27_idp_outage_blocks_operator_authority_and_workflow_progression(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host=runtime_auth_tests.TEST_NON_LOOPBACK_HOST,
                port=8080,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=runtime_auth_tests.REVIEWED_SHARED_SECRET,
                wazuh_ingest_reverse_proxy_secret=(
                    runtime_auth_tests.REVIEWED_WAZUH_PROXY_SECRET
                ),
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_reverse_proxy_secret=(
                    runtime_auth_tests.REVIEWED_SURFACE_PROXY_SECRET
                ),
                protected_surface_trusted_proxy_cidrs=("10.10.0.5/32",),
                protected_surface_proxy_service_account=(
                    runtime_auth_tests.REVIEWED_PROXY_SERVICE_ACCOUNT
                ),
                protected_surface_reviewed_identity_provider="authentik",
                admin_bootstrap_token=runtime_auth_tests.REVIEWED_ADMIN_BOOTSTRAP_TOKEN,
            ),
            store=store,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Do not let unavailable identity-provider context advance authority."
            ),
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep approval-bound action blocked during IdP outage.",
            escalation_reason="Missing IdP trust must not grant workflow authority.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase27-idp-outage-001",
        )

        initial_action_request = service.get_record(
            ActionRequestRecord,
            action_request.action_request_id,
        )
        initial_action_request_count = len(store.list(ActionRequestRecord))
        initial_case = service.get_record(CaseRecord, promoted_case.case_id)
        initial_transition_count = len(store.list(LifecycleTransitionRecord))
        initial_approval_count = len(store.list(ApprovalDecisionRecord))
        initial_execution_count = len(store.list(ActionExecutionRecord))
        initial_reconciliation_count = len(store.list(ReconciliationRecord))

        def assert_idp_outage_blocks(
            path: str,
            role: str,
            write: Callable[[], object],
        ) -> None:
            handler = mock.Mock()
            handler.client_address = ("10.10.0.5", 44321)
            headers = {
                "X-Forwarded-Proto": "https",
                "X-AegisOps-Proxy-Secret": (
                    runtime_auth_tests.REVIEWED_SURFACE_PROXY_SECRET
                ),
                "X-AegisOps-Proxy-Service-Account": (
                    runtime_auth_tests.REVIEWED_PROXY_SERVICE_ACCOUNT
                ),
                "X-AegisOps-Authenticated-Subject": "authentik-user-001",
                "X-AegisOps-Authenticated-Identity": (
                    "approver-001" if role == "approver" else "analyst-001"
                ),
                "X-AegisOps-Authenticated-Role": role,
            }
            handler.headers.get.side_effect = headers.get

            with self.assertRaisesRegex(
                PermissionError,
                "protected control-plane surfaces require an attributed reviewed identity provider header",
            ):
                authenticate_protected_write(
                    service=service,
                    handler=handler,
                    request_path=path,
                    require_loopback_operator_request_fn=lambda _handler: None,
                )
                write()

        assert_idp_outage_blocks(
            "/operator/create-reviewed-action-request",
            "analyst",
            lambda: service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-002",
                message_intent="This write must remain unreachable during IdP outage.",
                escalation_reason="Missing IdP trust cannot create authority.",
                expires_at=reviewed_at + timedelta(hours=4),
                action_request_id="action-request-phase27-idp-outage-unreachable-001",
            ),
        )
        assert_idp_outage_blocks(
            "/operator/record-action-approval-decision",
            "approver",
            lambda: service.record_action_approval_decision(
                action_request_id=action_request.action_request_id,
                approver_identity="approver-001",
                authenticated_approver_identity="approver-001",
                decision="grant",
                decision_rationale="This approval must remain unreachable.",
                decided_at=reviewed_at + timedelta(minutes=5),
                approval_decision_id="approval-phase27-idp-outage-unreachable-001",
            ),
        )
        assert_idp_outage_blocks(
            "/operator/record-case-disposition",
            "analyst",
            lambda: service.record_case_disposition(
                case_id=promoted_case.case_id,
                disposition="closed",
                rationale="This case lifecycle update must remain unreachable.",
                recorded_at=reviewed_at + timedelta(minutes=10),
            ),
        )

        self.assertEqual(
            service.get_record(ActionRequestRecord, action_request.action_request_id),
            initial_action_request,
        )
        self.assertEqual(len(store.list(ActionRequestRecord)), initial_action_request_count)
        self.assertEqual(service.get_record(CaseRecord, promoted_case.case_id), initial_case)
        self.assertEqual(len(store.list(LifecycleTransitionRecord)), initial_transition_count)
        self.assertEqual(len(store.list(ApprovalDecisionRecord)), initial_approval_count)
        self.assertEqual(len(store.list(ActionExecutionRecord)), initial_execution_count)
        self.assertEqual(
            len(store.list(ReconciliationRecord)),
            initial_reconciliation_count,
        )

    def test_phase27_upgrade_rollback_uncertainty_freezes_authority_sensitive_progression(
        self,
    ) -> None:
        store, seed_service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = seed_service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Keep rollback uncertainty from advancing workflow authority."
            ),
        )
        action_request = seed_service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Hold approval-bound action during rollback verification.",
            escalation_reason="Rollback-in-progress state must freeze authority.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase27-rollback-freeze-001",
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=runtime_auth_tests.REVIEWED_SHARED_SECRET,
                admin_bootstrap_token=(
                    runtime_auth_tests.REVIEWED_ADMIN_BOOTSTRAP_TOKEN
                ),
                control_plane_change_state="rollback_in_progress",
                control_plane_change_evidence_id="rollback-window-phase27-001",
            ),
            store=store,
        )

        initial_action_request = service.get_record(
            ActionRequestRecord,
            action_request.action_request_id,
        )
        initial_action_request_count = len(store.list(ActionRequestRecord))
        initial_case = service.get_record(CaseRecord, promoted_case.case_id)
        initial_transition_count = len(store.list(LifecycleTransitionRecord))
        initial_approval_count = len(store.list(ApprovalDecisionRecord))
        initial_execution_count = len(store.list(ActionExecutionRecord))
        initial_reconciliation_count = len(store.list(ReconciliationRecord))

        with self.assertRaisesRegex(
            PermissionError,
            "control-plane upgrade or rollback verification is not complete",
        ):
            service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-002",
                message_intent=(
                    "Do not create a fresh request during rollback verification."
                ),
                escalation_reason=(
                    "Rollback-in-progress state must freeze request creation."
                ),
                expires_at=reviewed_at + timedelta(hours=4),
                action_request_id="action-request-phase27-rollback-freeze-002",
            )

        with self.assertRaisesRegex(
            PermissionError,
            "control-plane upgrade or rollback verification is not complete",
        ):
            service.record_action_approval_decision(
                action_request_id=action_request.action_request_id,
                approver_identity="approver-001",
                authenticated_approver_identity="approver-001",
                decision="grant",
                decision_rationale="Rollback uncertainty must block approval.",
                decided_at=reviewed_at + timedelta(minutes=5),
                approval_decision_id="approval-phase27-rollback-freeze-001",
            )

        with self.assertRaisesRegex(
            PermissionError,
            "control-plane upgrade or rollback verification is not complete",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id=action_request.action_request_id,
                approved_payload=dict(action_request.requested_payload),
                delegated_at=reviewed_at + timedelta(minutes=10),
                delegation_issuer="control-plane-service",
            )

        with self.assertRaisesRegex(
            PermissionError,
            "control-plane upgrade or rollback verification is not complete",
        ):
            service.reconcile_action_execution(
                action_request_id=action_request.action_request_id,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=(),
                compared_at=reviewed_at + timedelta(minutes=15),
                stale_after=reviewed_at + timedelta(hours=1),
            )

        with self.assertRaisesRegex(
            PermissionError,
            "control-plane upgrade or rollback verification is not complete",
        ):
            service.record_case_disposition(
                case_id=promoted_case.case_id,
                disposition="closed",
                rationale="Rollback uncertainty must not close the case.",
                recorded_at=reviewed_at + timedelta(minutes=20),
            )

        readiness = service.inspect_readiness_diagnostics()
        freeze_status = readiness.metrics["control_plane_change_authority_freeze"]

        self.assertEqual(readiness.status, "failing_closed")
        self.assertEqual(freeze_status["state"], "frozen")
        self.assertEqual(freeze_status["change_state"], "rollback_in_progress")
        self.assertEqual(
            freeze_status["evidence_id"],
            "rollback-window-phase27-001",
        )
        self.assertEqual(
            service.get_record(ActionRequestRecord, action_request.action_request_id),
            initial_action_request,
        )
        self.assertEqual(len(store.list(ActionRequestRecord)), initial_action_request_count)
        self.assertEqual(service.get_record(CaseRecord, promoted_case.case_id), initial_case)
        self.assertEqual(len(store.list(LifecycleTransitionRecord)), initial_transition_count)
        self.assertEqual(len(store.list(ApprovalDecisionRecord)), initial_approval_count)
        self.assertEqual(len(store.list(ActionExecutionRecord)), initial_execution_count)
        self.assertEqual(
            len(store.list(ReconciliationRecord)),
            initial_reconciliation_count,
        )

    def test_phase27_secret_contract_requires_fresh_read_and_blocks_backend_outage(
        self,
    ) -> None:
        transport = secret_boundary_tests._MutableOpenBaoTransport(
            secrets={
                "kv/aegisops/control-plane/wazuh-ingest-shared-secret": (
                    "reviewed-shared-secret-v1"
                ),
            }
        )

        initial = RuntimeConfig.from_env(
            {
                "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH": (
                    "kv/aegisops/control-plane/wazuh-ingest-shared-secret"
                ),
            },
            secret_backend_transport=transport,
        )

        transport._secrets["kv/aegisops/control-plane/wazuh-ingest-shared-secret"] = (
            "reviewed-shared-secret-v2"
        )

        rotated = RuntimeConfig.from_env(
            {
                "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH": (
                    "kv/aegisops/control-plane/wazuh-ingest-shared-secret"
                ),
            },
            secret_backend_transport=transport,
        )

        failing_transport = secret_boundary_tests._MutableOpenBaoTransport(
            error=RuntimeError("backend unavailable")
        )

        with self.assertRaisesRegex(
            ValueError,
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH could not be read from OpenBao",
        ):
            RuntimeConfig.from_env(
                {
                    "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                    "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                    "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH": (
                        "kv/aegisops/control-plane/postgres-dsn"
                    ),
                },
                secret_backend_transport=failing_transport,
            )

        self.assertEqual(initial.wazuh_ingest_shared_secret, "reviewed-shared-secret-v1")
        self.assertEqual(rotated.wazuh_ingest_shared_secret, "reviewed-shared-secret-v2")

    def test_phase27_secret_backend_outage_rejects_plaintext_fallback_and_blocks_workflow_progression(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        initial_case = service.get_record(CaseRecord, promoted_case.case_id)
        initial_action_request_count = len(store.list(ActionRequestRecord))
        initial_transition_count = len(store.list(LifecycleTransitionRecord))
        initial_approval_count = len(store.list(ApprovalDecisionRecord))
        initial_execution_count = len(store.list(ActionExecutionRecord))
        initial_reconciliation_count = len(store.list(ReconciliationRecord))
        failing_transport = secret_boundary_tests._MutableOpenBaoTransport(
            error=RuntimeError("backend unavailable")
        )
        base_env = {
            "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
            "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
            "AEGISOPS_CONTROL_PLANE_HOST": runtime_auth_tests.TEST_NON_LOOPBACK_HOST,
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS": (
                "10.10.0.5/32"
            ),
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT": (
                runtime_auth_tests.REVIEWED_PROXY_SERVICE_ACCOUNT
            ),
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER": (
                "authentik"
            ),
        }
        openbao_env = {
            **base_env,
            "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH": (
                "kv/aegisops/control-plane/protected-surface-reverse-proxy-secret"
            ),
        }

        with self.assertRaisesRegex(
            ValueError,
            (
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH "
                "could not be read from OpenBao"
            ),
        ):
            RuntimeConfig.from_env(
                openbao_env,
                secret_backend_transport=failing_transport,
            )

        with self.assertRaisesRegex(
            ValueError,
            (
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET and "
                "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH "
                "are mutually exclusive"
            ),
        ):
            RuntimeConfig.from_env(
                {
                    **openbao_env,
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET": (
                        "unsafe-plaintext-fallback"
                    ),
                },
                secret_backend_transport=failing_transport,
            )

        with tempfile.NamedTemporaryFile("w+", encoding="utf-8") as handle:
            handle.write("unsafe-file-fallback\n")
            handle.flush()

            with self.assertRaisesRegex(
                ValueError,
                (
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE "
                    "and "
                    "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH "
                    "are mutually exclusive"
                ),
            ):
                RuntimeConfig.from_env(
                    {
                        **openbao_env,
                        "AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE": (
                            handle.name
                        ),
                    },
                    secret_backend_transport=failing_transport,
                )

        self.assertEqual(failing_transport.calls, 1)
        self.assertEqual(
            service.get_record(CaseRecord, promoted_case.case_id),
            initial_case,
        )
        self.assertEqual(len(store.list(ActionRequestRecord)), initial_action_request_count)
        self.assertEqual(len(store.list(LifecycleTransitionRecord)), initial_transition_count)
        self.assertEqual(len(store.list(ApprovalDecisionRecord)), initial_approval_count)
        self.assertEqual(len(store.list(ActionExecutionRecord)), initial_execution_count)
        self.assertEqual(
            len(store.list(ReconciliationRecord)),
            initial_reconciliation_count,
        )

    def test_phase27_secret_rotation_interruption_rejects_mixed_or_partial_credential_state(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host=runtime_auth_tests.TEST_NON_LOOPBACK_HOST,
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret-v1",
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret-v1",
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )
        initial_case = service.get_record(CaseRecord, promoted_case.case_id)
        initial_action_request_count = len(store.list(ActionRequestRecord))
        initial_transition_count = len(store.list(LifecycleTransitionRecord))
        initial_approval_count = len(store.list(ApprovalDecisionRecord))
        initial_execution_count = len(store.list(ActionExecutionRecord))
        initial_reconciliation_count = len(store.list(ReconciliationRecord))
        mixed_source_transport = secret_boundary_tests._MutableOpenBaoTransport(
            {
                "kv/aegisops/control-plane/wazuh-ingest-reverse-proxy-secret": (
                    "reviewed-proxy-secret-v2"
                ),
            }
        )

        with self.assertRaisesRegex(
            ValueError,
            "Wazuh ingest secret rotation bindings must not mix",
        ):
            RuntimeConfig.from_env(
                {
                    "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                    "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET": (
                        "reviewed-shared-secret-v1"
                    ),
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH": (
                        "kv/aegisops/control-plane/wazuh-ingest-reverse-proxy-secret"
                    ),
                },
                secret_backend_transport=mixed_source_transport,
            )

        interrupted_transport = _InterruptedOpenBaoRotationTransport()
        with self.assertRaisesRegex(
            ValueError,
            (
                "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH "
                "could not be read from OpenBao"
            ),
        ):
            RuntimeConfig.from_env(
                {
                    "AEGISOPS_OPENBAO_ADDRESS": "https://openbao.example.test",
                    "AEGISOPS_OPENBAO_TOKEN": "reviewed-openbao-token",
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH": (
                        "kv/aegisops/control-plane/wazuh-ingest-shared-secret"
                    ),
                    "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH": (
                        "kv/aegisops/control-plane/wazuh-ingest-reverse-proxy-secret"
                    ),
                },
                secret_backend_transport=interrupted_transport,
            )

        with self.assertRaisesRegex(
            PermissionError,
            "live Wazuh ingest bearer credential did not match the reviewed shared secret",
        ):
            service.ingest_wazuh_alert(
                raw_alert={},
                authorization_header="Bearer reviewed-shared-secret-v2",
                forwarded_proto="https",
                reverse_proxy_secret_header="reviewed-proxy-secret-v1",
                peer_addr="10.10.0.5",
            )

        self.assertEqual(mixed_source_transport.calls, 0)
        self.assertEqual(
            interrupted_transport.calls,
            [
                "kv/aegisops/control-plane/wazuh-ingest-shared-secret",
                "kv/aegisops/control-plane/wazuh-ingest-reverse-proxy-secret",
            ],
        )
        self.assertEqual(
            service.inspect_readiness_diagnostics().status,
            "failing_closed",
        )
        self.assertEqual(
            service.get_record(CaseRecord, promoted_case.case_id),
            initial_case,
        )
        self.assertEqual(len(store.list(ActionRequestRecord)), initial_action_request_count)
        self.assertEqual(len(store.list(LifecycleTransitionRecord)), initial_transition_count)
        self.assertEqual(len(store.list(ApprovalDecisionRecord)), initial_approval_count)
        self.assertEqual(len(store.list(ActionExecutionRecord)), initial_execution_count)
        self.assertEqual(
            len(store.list(ReconciliationRecord)),
            initial_reconciliation_count,
        )


if __name__ == "__main__":
    unittest.main()
