from __future__ import annotations

# ruff: noqa: E402

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _restore_readiness_test_support import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AegisOpsControlPlaneService,
    AITraceRecord,
    ApprovalDecisionRecord,
    MalformedReadinessFieldStore,
    ReconciliationRecord,
    RuntimeConfig,
    ServicePersistenceTestBase,
    WazuhAlertAdapter,
    _ListCountingStore,
    _approved_binding_hash,
    _load_wazuh_fixture,
    _phase20_notify_identity_owner_payload,
    datetime,
    make_store,
    mock,
    replace,
    timedelta,
    timezone,
)


class ReadinessProjectionTests(ServicePersistenceTestBase):
    def test_service_phase21_readiness_surfaces_unresolved_review_path_health(
        self,
    ) -> None:
        store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep silent failures visible on readiness without leaving AegisOps.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="The reviewed action path needs explicit degraded visibility after approval.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase21-readiness-path-health-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-path-health-001",
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

        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(readiness.status, "degraded")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "degraded")
        self.assertEqual(
            review_path_health["paths"]["delegation"]["reason"],
            "reviewed_delegation_missing_after_approval",
        )
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "provider_signal_missing_after_approval",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "reconciliation_missing_after_approval",
        )

    def test_service_phase21_readiness_tracks_approved_review_awaiting_delegation(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep reviewed requests visible on readiness before delegation starts.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="The approved reviewed request must stay visible until delegation begins.",
            expires_at=expires_at,
            action_request_id="action-request-phase21-readiness-approved-path-health-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-approved-path-health-001",
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
                lifecycle_state="approved",
            )
        )
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(store.list_calls, 0)
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "delayed")
        self.assertEqual(
            review_path_health["paths"]["delegation"]["reason"],
            "awaiting_reviewed_delegation",
        )
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "awaiting_delegation",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "awaiting_reconciliation",
        )

    def test_service_phase21_readiness_promotes_expired_approved_review_to_degraded(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Promote overdue reviewed approvals into explicit degraded visibility.",
        )
        base_now = datetime.now(timezone.utc)
        requested_at = base_now - timedelta(hours=2)
        expired_at = base_now - timedelta(hours=1)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep overdue approved reviews explicit on readiness.",
            escalation_reason="Approval-only visibility must age into a degraded silent-failure signal.",
            expires_at=base_now + timedelta(hours=4),
            action_request_id="action-request-phase21-readiness-stale-approved-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-stale-approved-001",
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
                lifecycle_state="approved",
            )
        )
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

        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(readiness.status, "degraded")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "degraded")
        self.assertEqual(
            review_path_health["paths"]["ingest"]["reason"],
            "ingest_signal_missing_after_approval",
        )
        self.assertEqual(
            review_path_health["paths"]["delegation"]["reason"],
            "reviewed_delegation_missing_after_approval",
        )
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "provider_signal_missing_after_approval",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "reconciliation_missing_after_approval",
        )

    def test_service_phase21_readiness_promotes_expired_executing_review_to_degraded(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Promote overdue reviewed execution visibility gaps into degraded states.",
        )
        base_now = datetime.now(timezone.utc)
        requested_at = base_now - timedelta(hours=2)
        delegated_at = base_now - timedelta(hours=1, minutes=50)
        approval_expired_at = base_now - timedelta(hours=1)
        request_expires_at = base_now + timedelta(hours=4)
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id=(
                    "action-request-phase21-readiness-stale-executing-001"
                ),
                approval_decision_id=None,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key=(
                    "idempotency-phase21-readiness-stale-executing-001"
                ),
                target_scope={
                    "record_family": "recommendation",
                    "record_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "recipient_identity": "repo-owner-001",
                },
                payload_hash="payload-hash-phase21-readiness-stale-executing-001",
                requested_at=requested_at,
                expires_at=request_expires_at,
                lifecycle_state="pending_approval",
                requester_identity="analyst-001",
                requested_payload={
                    "action_type": "notify_identity_owner",
                    "recipient_identity": "repo-owner-001",
                    "message_intent": (
                        "Keep overdue reviewed execution outcomes explicit on readiness."
                    ),
                    "escalation_reason": (
                        "Queued or running reviewed executions must age into degraded silent-failure visibility."
                    ),
                    "source_record_family": "recommendation",
                    "source_record_id": recommendation.recommendation_id,
                    "recommendation_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                },
            )
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-stale-executing-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=approval_expired_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval.approval_decision_id,
                requested_at=requested_at,
                expires_at=request_expires_at,
                lifecycle_state="executing",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-phase21-readiness-stale-executing-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase21-readiness-stale-executing-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-readiness-stale-executing-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=delegated_at,
                expires_at=request_expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="running",
            )
        )
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

        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(readiness.status, "degraded")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "degraded")
        self.assertEqual(
            review_path_health["paths"]["ingest"]["reason"],
            "ingest_signal_timeout",
        )
        self.assertEqual(review_path_health["paths"]["delegation"]["reason"], "delegated")
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "authoritative_outcome_timeout",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "reconciliation_timeout",
        )

    def test_service_phase21_readiness_marks_reconciliation_without_execution_lineage_degraded(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Classify reconciliation-only reviewed visibility as degraded when execution lineage is missing.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id=(
                    "action-request-phase21-readiness-reconciliation-no-execution-001"
                ),
                approval_decision_id=None,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key=(
                    "idempotency-phase21-readiness-reconciliation-no-execution-001"
                ),
                target_scope={
                    "record_family": "recommendation",
                    "record_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "recipient_identity": "repo-owner-001",
                },
                payload_hash=(
                    "payload-hash-phase21-readiness-reconciliation-no-execution-001"
                ),
                requested_at=reviewed_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                requester_identity="analyst-001",
                requested_payload={
                    "action_type": "notify_identity_owner",
                    "recipient_identity": "repo-owner-001",
                    "message_intent": (
                        "Keep reconciliation-only reviewed path anomalies visible on readiness."
                    ),
                    "escalation_reason": (
                        "A persisted reconciliation without matching execution lineage must surface as degraded instead of awaiting."
                    ),
                    "source_record_family": "recommendation",
                    "source_record_id": recommendation.recommendation_id,
                    "recommendation_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                },
            )
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-reconciliation-no-execution-001"
                ),
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
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id=(
                    "reconciliation-phase21-readiness-reconciliation-no-execution-001"
                ),
                subject_linkage={
                    "action_request_ids": [action_request.action_request_id],
                    "approval_decision_ids": [approval.approval_decision_id],
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=(
                    "reconciliation-no-execution:"
                    f"{action_request.action_request_id}"
                ),
                first_seen_at=reviewed_at + timedelta(minutes=10),
                last_seen_at=reviewed_at + timedelta(minutes=10),
                ingest_disposition="matched",
                mismatch_summary="reconciliation observed without persisted execution",
                compared_at=reviewed_at + timedelta(minutes=11),
                lifecycle_state="matched",
            )
        )
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(store.list_calls, 0)
        self.assertEqual(readiness.status, "degraded")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "degraded")
        self.assertEqual(
            review_path_health["paths"]["ingest"]["reason"],
            "observations_current",
        )
        self.assertEqual(
            review_path_health["paths"]["delegation"]["reason"],
            "reviewed_delegation_record_missing",
        )
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "provider_execution_record_missing",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "reconciliation_execution_lineage_missing",
        )

    def test_service_phase21_readiness_promotes_expired_executing_review_without_execution_to_degraded(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Promote overdue reviewed delegation gaps into degraded states even when execution persistence is missing.",
        )
        base_now = datetime.now(timezone.utc)
        requested_at = base_now - timedelta(hours=2)
        expired_at = base_now - timedelta(hours=1)
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id=(
                    "action-request-phase21-readiness-stale-executing-no-execution-001"
                ),
                approval_decision_id=None,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key=(
                    "idempotency-phase21-readiness-stale-executing-no-execution-001"
                ),
                target_scope={
                    "record_family": "recommendation",
                    "record_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "recipient_identity": "repo-owner-001",
                },
                payload_hash=(
                    "payload-hash-phase21-readiness-stale-executing-no-execution-001"
                ),
                requested_at=requested_at,
                expires_at=expired_at,
                lifecycle_state="pending_approval",
                requester_identity="analyst-001",
                requested_payload={
                    "action_type": "notify_identity_owner",
                    "recipient_identity": "repo-owner-001",
                    "message_intent": (
                        "Keep overdue executing reviews without persisted executions explicit on readiness."
                    ),
                    "escalation_reason": (
                        "Missing delegation persistence after approval must age into degraded silent-failure visibility."
                    ),
                    "source_record_family": "recommendation",
                    "source_record_id": recommendation.recommendation_id,
                    "recommendation_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                },
            )
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-stale-executing-no-execution-001"
                ),
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

        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(readiness.status, "degraded")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "degraded")
        self.assertEqual(
            review_path_health["paths"]["ingest"]["reason"],
            "ingest_signal_missing_after_approval",
        )
        self.assertEqual(
            review_path_health["paths"]["delegation"]["reason"],
            "reviewed_delegation_missing_after_approval",
        )
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "provider_signal_missing_after_approval",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "reconciliation_missing_after_approval",
        )

    def test_service_phase21_readiness_tracks_terminal_review_lineage_without_full_table_reads(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep reviewed requests visible on readiness while matched execution lineage stays operator-visible.",
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id=(
                    "action-request-phase21-readiness-terminal-lineage-001"
                ),
                approval_decision_id=None,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key=(
                    "idempotency-phase21-readiness-terminal-lineage-001"
                ),
                target_scope={
                    "record_family": "recommendation",
                    "record_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "recipient_identity": "repo-owner-001",
                },
                payload_hash="payload-hash-phase21-readiness-terminal-lineage-001",
                requested_at=reviewed_at,
                expires_at=reviewed_at + timedelta(hours=4),
                lifecycle_state="pending_approval",
                requester_identity="analyst-001",
                requested_payload={
                    "action_type": "notify_identity_owner",
                    "recipient_identity": "repo-owner-001",
                    "message_intent": (
                        "Notify the accountable repository owner about the reviewed permission change."
                    ),
                    "escalation_reason": (
                        "The approved reviewed request must stay visible while execution lineage remains matched."
                    ),
                    "source_record_family": "recommendation",
                    "source_record_id": recommendation.recommendation_id,
                    "recommendation_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                },
            )
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-terminal-lineage-001",
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
        action_execution = service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-phase21-readiness-terminal-lineage-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase21-readiness-terminal-lineage-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-readiness-terminal-lineage-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=10),
                expires_at=action_request.expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="succeeded",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-terminal-lineage-001",
                subject_linkage={
                    "case_ids": (promoted_case.case_id,),
                    "action_execution_ids": (action_execution.action_execution_id,),
                    "delegation_ids": (action_execution.delegation_id,),
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=action_execution.execution_run_id,
                linked_execution_run_ids=(action_execution.execution_run_id,),
                correlation_key="phase21-readiness-terminal-lineage-001",
                first_seen_at=action_execution.delegated_at + timedelta(minutes=1),
                last_seen_at=action_execution.delegated_at + timedelta(minutes=2),
                ingest_disposition="matched",
                mismatch_summary="matched execution lineage remains operator-visible",
                compared_at=action_execution.delegated_at + timedelta(minutes=3),
                lifecycle_state="matched",
            )
        )
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(store.list_calls, 0)
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "healthy")
        self.assertEqual(review_path_health["paths"]["delegation"]["reason"], "delegated")
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "execution_succeeded",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "reconciliation_matched",
        )

    def test_service_phase21_readiness_tracks_terminal_failed_review_after_request_completion_without_full_table_reads(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep terminal reviewed provider failures visible after the request itself reaches a terminal state.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep terminal provider failures visible after request completion.",
            escalation_reason="Readiness must not hide provider failures just because the request left the active set.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase21-readiness-terminal-failed-completed-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-terminal-failed-completed-001"
                ),
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
                lifecycle_state="failed",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-phase21-readiness-terminal-failed-completed-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id=(
                    "delegation-phase21-readiness-terminal-failed-completed-001"
                ),
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id=(
                    "execution-run-phase21-readiness-terminal-failed-completed-001"
                ),
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=10),
                expires_at=action_request.expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="failed",
            )
        )
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(store.list_calls, 0)
        self.assertEqual(readiness.status, "degraded")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "failed")
        self.assertEqual(review_path_health["paths"]["delegation"]["reason"], "delegated")
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "execution_failed",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "awaiting_reconciliation",
        )

    def test_service_phase21_readiness_fallback_keeps_canceled_terminal_reviews_visible(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep canceled reviewed requests visible even when readiness falls back to full-table aggregate scans.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep canceled reviewed requests operator-visible during readiness fallback.",
            escalation_reason="Fallback readiness must classify canceled requests as terminal instead of dropping them from review-path visibility.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase21-readiness-fallback-canceled-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-fallback-canceled-001"
                ),
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
                lifecycle_state="canceled",
            )
        )
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
        setattr(store, "inspect_readiness_aggregates", None)

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertGreater(store.list_calls, 0)
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "healthy")
        self.assertEqual(
            review_path_health["paths"]["ingest"]["reason"],
            "review_closed_before_ingest",
        )
        self.assertEqual(
            review_path_health["paths"]["delegation"]["reason"],
            "review_closed_without_delegation",
        )
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "review_closed_before_provider",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "review_closed_before_reconciliation",
        )

    def test_service_phase21_readiness_tracks_terminal_review_without_execution_lineage_without_full_table_reads(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep terminal reviewed requests visible when the request outcome is persisted before any execution lineage exists.",
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id=(
                    "action-request-phase21-readiness-terminal-no-execution-001"
                ),
                approval_decision_id=None,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key=(
                    "idempotency-phase21-readiness-terminal-no-execution-001"
                ),
                target_scope={
                    "record_family": "recommendation",
                    "record_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "recipient_identity": "repo-owner-001",
                },
                payload_hash=(
                    "payload-hash-phase21-readiness-terminal-no-execution-001"
                ),
                requested_at=reviewed_at,
                expires_at=reviewed_at + timedelta(hours=4),
                lifecycle_state="pending_approval",
                requester_identity="analyst-001",
                requested_payload={
                    "action_type": "notify_identity_owner",
                    "recipient_identity": "repo-owner-001",
                    "message_intent": (
                        "Keep terminal reviewed requests visible without execution lineage."
                    ),
                    "escalation_reason": (
                        "Readiness must not drop reviewed outcomes just because execution persistence never materialized."
                    ),
                    "source_record_family": "recommendation",
                    "source_record_id": recommendation.recommendation_id,
                    "recommendation_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                },
            )
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-terminal-no-execution-001"
                ),
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
                lifecycle_state="failed",
            )
        )
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(store.list_calls, 0)
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "delayed")
        self.assertEqual(
            review_path_health["paths"]["ingest"]["reason"],
            "awaiting_ingest_signal",
        )
        self.assertEqual(
            review_path_health["paths"]["delegation"]["reason"],
            "awaiting_reviewed_delegation",
        )
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "awaiting_delegation",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "awaiting_reconciliation",
        )

    def test_service_phase21_readiness_keeps_delegation_only_stale_reconciliation_visible(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep delegation-linked unresolved reconciliation gaps visible after terminal execution.",
        )
        base_now = datetime.now(timezone.utc)
        requested_at = base_now - timedelta(hours=2)
        delegated_at = base_now - timedelta(hours=1, minutes=50)
        expired_at = base_now - timedelta(hours=1)
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id=(
                    "action-request-phase21-readiness-delegation-lineage-timeout-001"
                ),
                approval_decision_id=None,
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key=(
                    "idempotency-phase21-readiness-delegation-lineage-timeout-001"
                ),
                target_scope={
                    "record_family": "recommendation",
                    "record_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                    "recipient_identity": "repo-owner-001",
                },
                payload_hash=(
                    "payload-hash-phase21-readiness-delegation-lineage-timeout-001"
                ),
                requested_at=requested_at,
                expires_at=expired_at,
                lifecycle_state="pending_approval",
                requester_identity="analyst-001",
                requested_payload={
                    "action_type": "notify_identity_owner",
                    "recipient_identity": "repo-owner-001",
                    "message_intent": (
                        "Keep delegation-only stale reconciliation visible."
                    ),
                    "escalation_reason": (
                        "Delegation-linked persistence gaps must remain visible after execution leaves the active sets."
                    ),
                    "source_record_family": "recommendation",
                    "source_record_id": recommendation.recommendation_id,
                    "recommendation_id": recommendation.recommendation_id,
                    "case_id": promoted_case.case_id,
                    "alert_id": promoted_case.alert_id,
                    "finding_id": promoted_case.finding_id,
                },
            )
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-delegation-lineage-timeout-001"
                ),
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
                lifecycle_state="completed",
            )
        )
        action_execution = service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-phase21-readiness-delegation-lineage-timeout-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id=(
                    "delegation-phase21-readiness-delegation-lineage-timeout-001"
                ),
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id=(
                    "execution-run-phase21-readiness-delegation-lineage-timeout-001"
                ),
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=delegated_at,
                expires_at=expired_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="succeeded",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id=(
                    "reconciliation-phase21-readiness-delegation-lineage-timeout-001"
                ),
                subject_linkage={
                    "case_ids": (promoted_case.case_id,),
                    "delegation_ids": (action_execution.delegation_id,),
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=action_execution.execution_run_id,
                linked_execution_run_ids=(action_execution.execution_run_id,),
                correlation_key=(
                    "phase21-readiness-delegation-lineage-timeout-001"
                ),
                first_seen_at=delegated_at + timedelta(minutes=1),
                last_seen_at=delegated_at + timedelta(minutes=2),
                ingest_disposition="matched",
                mismatch_summary=(
                    "delegation-only stale reconciliation should stay operator-visible"
                ),
                compared_at=delegated_at + timedelta(minutes=3),
                lifecycle_state="stale",
            )
        )
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertEqual(store.list_calls, 0)
        self.assertEqual(readiness.status, "stale")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "degraded")
        self.assertEqual(review_path_health["paths"]["ingest"]["reason"], "observations_current")
        self.assertEqual(review_path_health["paths"]["delegation"]["reason"], "delegated")
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "execution_succeeded",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "reconciliation_stale",
        )

    def test_service_phase21_readiness_fallback_surfaces_terminal_executing_review_path_health(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep terminal reviewed failures visible when readiness falls back to full scans.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep terminal provider failures visible on readiness.",
            escalation_reason="Fallback readiness must not hide terminal execution failures for active reviewed requests.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase21-readiness-fallback-terminal-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-fallback-terminal-001"
                ),
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
                lifecycle_state="executing",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-phase21-readiness-fallback-terminal-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase21-readiness-fallback-terminal-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-readiness-fallback-terminal-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=10),
                expires_at=action_request.expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="failed",
            )
        )
        setattr(store, "inspect_readiness_review_path_records", None)
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertGreater(store.list_calls, 0)
        self.assertEqual(readiness.status, "degraded")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "failed")
        self.assertEqual(review_path_health["paths"]["delegation"]["reason"], "delegated")
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "execution_failed",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "awaiting_reconciliation",
        )

    def test_service_phase21_readiness_fallback_matches_execution_lineage_reconciliation(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep fallback readiness aligned with matched reviewed lineage.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep execution-linked reconciliation visible on readiness.",
            escalation_reason="Fallback readiness must match reconciliation lineage through execution identifiers.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase21-readiness-fallback-lineage-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-fallback-lineage-001",
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
        action_execution = service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-phase21-readiness-fallback-lineage-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase21-readiness-fallback-lineage-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-readiness-fallback-lineage-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=10),
                expires_at=action_request.expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="succeeded",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id=(
                    "reconciliation-phase21-readiness-fallback-lineage-001"
                ),
                subject_linkage={
                    "case_ids": (promoted_case.case_id,),
                    "action_execution_ids": (action_execution.action_execution_id,),
                    "delegation_ids": (action_execution.delegation_id,),
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=action_execution.execution_run_id,
                linked_execution_run_ids=(action_execution.execution_run_id,),
                correlation_key="phase21-readiness-fallback-lineage-001",
                first_seen_at=action_execution.delegated_at + timedelta(minutes=1),
                last_seen_at=action_execution.delegated_at + timedelta(minutes=2),
                ingest_disposition="matched",
                mismatch_summary=(
                    "fallback readiness matched reconciliation through execution lineage"
                ),
                compared_at=action_execution.delegated_at + timedelta(minutes=3),
                lifecycle_state="matched",
            )
        )
        setattr(store, "inspect_readiness_review_path_records", None)
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

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]

        self.assertGreater(store.list_calls, 0)
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "healthy")
        self.assertEqual(review_path_health["paths"]["delegation"]["reason"], "delegated")
        self.assertEqual(
            review_path_health["paths"]["provider"]["reason"],
            "execution_succeeded",
        )
        self.assertEqual(
            review_path_health["paths"]["persistence"]["reason"],
            "reconciliation_matched",
        )

    def test_service_phase21_readiness_counts_distinct_execution_runs_and_redacts_payload(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        target_scope = {"asset_id": "asset-phase21-readiness-001"}
        latest_seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
        )
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id=promoted_case.case_id,
            alert_id=promoted_case.alert_id,
            finding_id=promoted_case.finding_id,
        )
        payload_hash = _approved_binding_hash(
            target_scope=target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        requested_at = latest_seed_reconciliation.compared_at + timedelta(minutes=10)
        delegated_at = requested_at + timedelta(minutes=5)
        expires_at = requested_at + timedelta(hours=1)
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-001",
                action_request_id="action-request-phase21-readiness-001",
                approver_identities=("approver-001",),
                target_snapshot=target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-phase21-readiness-001",
                approval_decision_id="approval-phase21-readiness-001",
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key="idempotency-phase21-readiness-001",
                target_scope=target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                requester_identity="analyst-001",
                requested_payload=approved_payload,
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_identity",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-readiness-001",
                action_request_id="action-request-phase21-readiness-001",
                approval_decision_id="approval-phase21-readiness-001",
                delegation_id="delegation-phase21-readiness-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-readiness-001",
                idempotency_key="idempotency-phase21-readiness-001",
                target_scope=target_scope,
                approved_payload=approved_payload,
                payload_hash=payload_hash,
                delegated_at=delegated_at,
                expires_at=expires_at,
                provenance={"adapter": "shuffle"},
                lifecycle_state="queued",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-001",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id="execution-run-phase21-readiness-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-001",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="phase20 execution matched",
                compared_at=delegated_at + timedelta(minutes=1),
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-002",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id="execution-run-phase21-readiness-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-002",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="duplicate reconciliation for same execution run",
                compared_at=delegated_at + timedelta(minutes=2),
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-none-001",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-none-001",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="null execution run should stay out of phase20 metric",
                compared_at=delegated_at + timedelta(minutes=3),
                lifecycle_state="matched",
            )
        )

        readiness = service.inspect_readiness_diagnostics()

        self.assertEqual(
            readiness.metrics["phase20_notify_identity_owner"]["reconciled_executions"],
            1,
        )
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            "reconciliation-phase21-readiness-distinct-none-001",
        )
        self.assertNotIn(
            "latest_native_payload",
            readiness.latest_reconciliation["subject_linkage"],
        )
        stored_latest = service.get_record(
            ReconciliationRecord,
            "reconciliation-phase21-readiness-distinct-none-001",
        )
        self.assertIsNotNone(stored_latest)
        self.assertIn("latest_native_payload", stored_latest.subject_linkage)

    def test_service_phase21_readiness_treats_dispatching_executions_as_active(
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
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        execution = service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-dispatching-001",
                action_request_id="action-request-phase21-dispatching-001",
                approval_decision_id="approval-phase21-dispatching-001",
                delegation_id="delegation-phase21-dispatching-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="pending-dispatch-delegation-phase21-dispatching-001",
                idempotency_key="idempotency-phase21-dispatching-001",
                target_scope={"asset_id": "asset-phase21-dispatching-001"},
                approved_payload={
                    "action_type": "notify_identity_owner",
                    "recipient_identity": "repo-owner-001",
                },
                payload_hash="payload-hash-phase21-dispatching-001",
                delegated_at=delegated_at,
                expires_at=delegated_at + timedelta(hours=1),
                provenance={"delegation_issuer": "control-plane-service"},
                lifecycle_state="dispatching",
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        aggregates = store.inspect_readiness_aggregates()

        self.assertFalse(readiness.shutdown["shutdown_ready"])
        self.assertEqual(
            readiness.shutdown["active_action_execution_ids"],
            [execution.action_execution_id],
        )
        self.assertEqual(
            aggregates.active_action_execution_ids,
            (execution.action_execution_id,),
        )
        self.assertEqual(readiness.metrics["action_executions"]["dispatching"], 1)
        self.assertEqual(readiness.metrics["action_executions"]["terminal"], 0)

    def test_service_phase21_readiness_surfaces_source_and_automation_health(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep source silence and substrate lag visible on readiness.",
        )
        requested_at = reviewed_at - timedelta(hours=2)
        delegated_at = reviewed_at - timedelta(hours=1, minutes=50)
        expired_at = reviewed_at - timedelta(hours=1)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Show degraded source and automation health in readiness.",
            escalation_reason="Operators must not infer healthy ingest or delegation from silence.",
            expires_at=reviewed_at + timedelta(hours=4),
            action_request_id="action-request-phase21-readiness-health-surfaces-001",
        )
        approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-health-surfaces-001",
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
                    "action-execution-phase21-readiness-health-surfaces-001"
                ),
                action_request_id=action_request.action_request_id,
                approval_decision_id=approval.approval_decision_id,
                delegation_id="delegation-phase21-readiness-health-surfaces-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-readiness-health-surfaces-001",
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

        with mock.patch.object(
            service._restore_readiness_service,
            "_collect_readiness_review_snapshots",
            wraps=service._readiness_operability_helper._collect_readiness_review_snapshots,
        ) as collect_readiness_review_snapshots:
            readiness = service.inspect_readiness_diagnostics()
        source_health = readiness.metrics["source_health"]
        automation_health = readiness.metrics["automation_substrate_health"]

        self.assertEqual(collect_readiness_review_snapshots.call_count, 1)
        self.assertEqual(source_health["overall_state"], "degraded")
        self.assertEqual(source_health["tracked_sources"], 1)
        self.assertEqual(
            source_health["sources"]["github_audit"]["reason"],
            "ingest_signal_timeout",
        )
        self.assertEqual(
            source_health["sources"]["github_audit"]["affected_reviews"],
            1,
        )
        self.assertEqual(
            source_health["sources"]["github_audit"]["by_state"],
            {
                "healthy": 0,
                "delayed": 0,
                "degraded": 1,
                "failed": 0,
            },
        )
        self.assertEqual(automation_health["overall_state"], "degraded")
        self.assertEqual(automation_health["tracked_surfaces"], 1)
        self.assertEqual(
            automation_health["surfaces"]["automation_substrate:shuffle"]["state"],
            "degraded",
        )
        self.assertEqual(
            automation_health["surfaces"]["automation_substrate:shuffle"]["paths"][
                "delegation"
            ]["reason"],
            "delegation_receipt_timeout",
        )
        self.assertEqual(
            automation_health["surfaces"]["automation_substrate:shuffle"]["paths"][
                "provider"
            ]["reason"],
            "provider_receipt_timeout",
        )
        self.assertEqual(
            automation_health["surfaces"]["automation_substrate:shuffle"]["paths"][
                "persistence"
            ]["reason"],
            "reconciliation_timeout",
        )

    def test_service_phase21_readiness_surfaces_optional_extension_operability_defaults(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        readiness = service.inspect_readiness_diagnostics()
        optional_extensions = readiness.metrics["optional_extensions"]

        self.assertEqual(optional_extensions["tracked_extensions"], 4)
        self.assertEqual(optional_extensions["overall_state"], "ready")
        self.assertEqual(
            optional_extensions["extensions"]["assistant"],
            {
                "enablement": "enabled",
                "availability": "available",
                "readiness": "ready",
                "authority_mode": "advisory_only",
                "mainline_dependency": "non_blocking",
                "reason": "bounded_reviewed_summary_provider_available",
            },
        )
        self.assertEqual(
            optional_extensions["extensions"]["endpoint_evidence"],
            {
                "enablement": "disabled_by_default",
                "availability": "unavailable",
                "readiness": "not_applicable",
                "authority_mode": "augmenting_evidence",
                "mainline_dependency": "non_blocking",
                "reason": "isolated_executor_runtime_not_configured",
            },
        )
        self.assertEqual(
            optional_extensions["extensions"]["network_evidence"],
            {
                "enablement": "disabled_by_default",
                "availability": "unavailable",
                "readiness": "not_applicable",
                "authority_mode": "augmenting_evidence",
                "mainline_dependency": "non_blocking",
                "reason": "reviewed_network_evidence_extension_not_activated",
            },
        )
        self.assertEqual(
            optional_extensions["extensions"]["ml_shadow"],
            {
                "enablement": "disabled_by_default",
                "availability": "unavailable",
                "readiness": "not_applicable",
                "authority_mode": "shadow_only",
                "mainline_dependency": "non_blocking",
                "reason": "reviewed_ml_shadow_extension_not_activated",
            },
        )

    def test_service_readiness_handles_malformed_review_payload_fields(self) -> None:
        inner_store, _ = make_store()
        store = MalformedReadinessFieldStore(inner_store)
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Review repository owner change evidence before any approval-bound "
                "response."
            ),
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent=(
                "Notify the accountable repository owner about the reviewed "
                "permission change."
            ),
            escalation_reason=(
                "Reviewed GitHub audit evidence requires bounded owner notification."
            ),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-malformed-readiness-fields-001",
        )
        action_request = service.persist_record(
            replace(action_request, lifecycle_state="approved")
        )
        store.malformed_action_request_fields[action_request.action_request_id] = {
            "requested_payload": "malformed requested payload",
            "policy_evaluation": ("malformed policy evaluation",),
        }

        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]
        automation_health = readiness.metrics["automation_substrate_health"]

        self.assertEqual(review_path_health["review_count"], 1)
        self.assertEqual(review_path_health["overall_state"], "delayed")
        self.assertEqual(automation_health["tracked_surfaces"], 0)

    def test_service_readiness_reason_helpers_fail_closed_on_mismatched_states(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        helper = service._readiness_operability_helper

        self.assertEqual(
            helper._readiness_dominant_reason(
                (
                    {
                        "state": "healthy",
                        "reason": "healthy_reason",
                        "affected_reviews": 1,
                    },
                ),
                overall_state="degraded",
            ),
            "degraded_reason_unknown",
        )
        self.assertEqual(
            helper._aggregate_readiness_path_health(
                path_name="approval",
                review_path_health=(
                    {
                        "paths": {
                            "approval": {
                                "state": "unexpected",
                                "reason": "unexpected_reason",
                            },
                        },
                    },
                ),
            ),
            {
                "state": "degraded",
                "reason": "degraded_reason_unknown",
                "affected_reviews": 1,
                "by_state": {
                    "healthy": 0,
                    "delayed": 0,
                    "degraded": 0,
                    "failed": 0,
                },
            },
        )

    def test_service_readiness_degrades_malformed_assistant_subject_linkage(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = MalformedReadinessFieldStore(inner_store)
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-malformed-subject-linkage-001",
                subject_linkage={
                    "provider_identity": "openai",
                    "provider_status": "ready",
                    "provider_operational_quality": {
                        "availability": "available",
                        "posture": "ready",
                        "retry_policy": "not_recorded",
                    },
                },
                model_identity="openai/gpt-5.4",
                prompt_version="phase24-case-summary-v1",
                generated_at=datetime(2026, 4, 29, 9, 0, tzinfo=timezone.utc),
                material_input_refs=("case-001",),
                reviewer_identity="system://bounded-live-assistant",
                lifecycle_state="under_review",
            )
        )
        store.malformed_latest_ai_trace_fields["subject_linkage"] = (
            "malformed subject linkage"
        )

        readiness = service.inspect_readiness_diagnostics()
        assistant = readiness.metrics["optional_extensions"]["extensions"]["assistant"]

        self.assertEqual(assistant["readiness"], "degraded")
        self.assertEqual(assistant["reason"], "assistant_provider_degraded")
        self.assertEqual(
            assistant["latest_ai_trace_id"],
            "ai-trace-malformed-subject-linkage-001",
        )

    def test_service_phase493_operator_health_labels_optional_degradation_subordinate(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase493-timeout-001",
                subject_linkage={
                    "provider_identity": "openai",
                    "provider_status": "timeout",
                    "provider_failure_summary": "attempt 1: timeout: provider timed out",
                    "provider_operational_quality": {
                        "availability": "unavailable",
                        "posture": "timeout",
                        "retry_policy": "retry_exhausted",
                    },
                },
                model_identity="openai/gpt-5.4",
                prompt_version="phase24-case-summary-v1",
                generated_at=datetime(2026, 4, 29, 9, 0, tzinfo=timezone.utc),
                material_input_refs=("case-001",),
                reviewer_identity="system://bounded-live-assistant",
                lifecycle_state="under_review",
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        operator_health = readiness.metrics["operator_health"]

        self.assertEqual(readiness.status, "ready")
        self.assertEqual(operator_health["overall_state"], "degraded")
        self.assertEqual(
            operator_health["authority_source"],
            "aegisops_control_plane_records",
        )
        self.assertEqual(
            operator_health["subordinate_signal_policy"],
            "visibility_only",
        )
        self.assertFalse(operator_health["subordinate_signals_authoritative"])
        self.assertEqual(
            operator_health["mainline"]["readiness_status"],
            "ready",
        )
        self.assertEqual(operator_health["mainline"]["open_case_count"], 0)
        self.assertEqual(
            operator_health["mainline"]["active_action_request_count"],
            0,
        )
        self.assertEqual(
            operator_health["mainline"]["active_action_execution_count"],
            0,
        )
        self.assertEqual(
            operator_health["mainline"]["unresolved_reconciliation_count"],
            0,
        )
        self.assertEqual(
            operator_health["subordinate_context"]["optional_extensions"]["state"],
            "degraded",
        )
        self.assertEqual(
            operator_health["subordinate_context"]["optional_extensions"][
                "authority_mode"
            ],
            "non_authoritative",
        )
        self.assertEqual(
            operator_health["subordinate_context"]["optional_extensions"][
                "degraded_extensions"
            ],
            ("assistant",),
        )
        self.assertEqual(operator_health["commercial_claims"], ())

    def test_service_phase21_readiness_source_health_ignores_predelegation_backlog(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        future_expires_at = reviewed_at + timedelta(hours=4)
        expired_at = reviewed_at - timedelta(hours=1)

        predelegation_recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Keep pre-delegation backlog out of reviewed source health rollups."
            ),
        )
        predelegation_action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=predelegation_recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent=(
                "Keep source health scoped to reviews where ingest is actually expected."
            ),
            escalation_reason=(
                "Operators must not read delegation backlog as source-family silence."
            ),
            expires_at=future_expires_at,
            action_request_id=(
                "action-request-phase21-readiness-source-health-predelegation-001"
            ),
        )
        predelegation_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-source-health-predelegation-001"
                ),
                action_request_id=predelegation_action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(predelegation_action_request.target_scope),
                payload_hash=predelegation_action_request.payload_hash,
                decided_at=reviewed_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=future_expires_at,
            )
        )
        service.persist_record(
            replace(
                predelegation_action_request,
                approval_decision_id=predelegation_approval.approval_decision_id,
                requested_at=reviewed_at,
                expires_at=future_expires_at,
                lifecycle_state="approved",
            )
        )

        delegated_recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Keep actual ingest silence visible once delegation exists."
            ),
        )
        delegated_requested_at = reviewed_at - timedelta(hours=2)
        delegated_at = reviewed_at - timedelta(hours=1, minutes=50)
        delegated_action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=delegated_recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Keep delegated ingest silence explicit on readiness.",
            escalation_reason=(
                "Operators still need the real source-health signal after delegation."
            ),
            expires_at=reviewed_at + timedelta(hours=6),
            action_request_id=(
                "action-request-phase21-readiness-source-health-delegated-001"
            ),
        )
        delegated_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id=(
                    "approval-phase21-readiness-source-health-delegated-001"
                ),
                action_request_id=delegated_action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(delegated_action_request.target_scope),
                payload_hash=delegated_action_request.payload_hash,
                decided_at=delegated_requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expired_at,
            )
        )
        service.persist_record(
            replace(
                delegated_action_request,
                approval_decision_id=delegated_approval.approval_decision_id,
                requested_at=delegated_requested_at,
                expires_at=expired_at,
                lifecycle_state="executing",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id=(
                    "action-execution-phase21-readiness-source-health-delegated-001"
                ),
                action_request_id=delegated_action_request.action_request_id,
                approval_decision_id=delegated_approval.approval_decision_id,
                delegation_id=(
                    "delegation-phase21-readiness-source-health-delegated-001"
                ),
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id=(
                    "execution-run-phase21-readiness-source-health-delegated-001"
                ),
                idempotency_key=delegated_action_request.idempotency_key,
                target_scope=dict(delegated_action_request.target_scope),
                approved_payload=dict(delegated_action_request.requested_payload),
                payload_hash=delegated_action_request.payload_hash,
                delegated_at=delegated_at,
                expires_at=expired_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="dispatching",
            )
        )

        readiness = service.inspect_readiness_diagnostics()
        review_path_health = readiness.metrics["review_path_health"]
        source_health = readiness.metrics["source_health"]
        github_audit = source_health["sources"]["github_audit"]

        self.assertEqual(review_path_health["review_count"], 2)
        self.assertEqual(source_health["tracked_sources"], 1)
        self.assertEqual(source_health["overall_state"], "degraded")
        self.assertEqual(github_audit["tracked_reviews"], 1)
        self.assertEqual(github_audit["affected_reviews"], 1)
        self.assertEqual(
            github_audit["reason"],
            "ingest_signal_timeout",
        )
        self.assertEqual(
            github_audit["by_state"],
            {
                "healthy": 0,
                "delayed": 0,
                "degraded": 1,
                "failed": 0,
            },
        )

    def test_service_phase21_readiness_counts_unique_affected_reviews_per_automation_surface(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        expires_at = reviewed_at + timedelta(hours=4)

        def persist_review(
            *,
            suffix: str,
            requested_offset_minutes: int,
            request_state: str,
            execution_state: str,
            reconciliation_state: str,
            mismatch_summary: str,
        ) -> None:
            recommendation = service.record_case_recommendation(
                case_id=promoted_case.case_id,
                review_owner="analyst-001",
                intended_outcome=(
                    "Keep automation substrate impact counts aligned with unique"
                    f" reviewed requests ({suffix})."
                ),
            )
            requested_at = reviewed_at + timedelta(minutes=requested_offset_minutes)
            delegated_at = requested_at + timedelta(minutes=10)
            action_request = service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent=(
                    "Keep unique affected review counts on automation substrate"
                    f" readiness explicit ({suffix})."
                ),
                escalation_reason=(
                    "Operators must see distinct reviewed requests impacted on the"
                    " same automation surface."
                ),
                expires_at=expires_at,
                action_request_id=(
                    f"action-request-phase21-readiness-automation-impact-{suffix}"
                ),
            )
            approval = service.persist_record(
                ApprovalDecisionRecord(
                    approval_decision_id=(
                        f"approval-phase21-readiness-automation-impact-{suffix}"
                    ),
                    action_request_id=action_request.action_request_id,
                    approver_identities=("approver-001",),
                    target_snapshot=dict(action_request.target_scope),
                    payload_hash=action_request.payload_hash,
                    decided_at=requested_at + timedelta(minutes=5),
                    lifecycle_state="approved",
                    approved_expires_at=expires_at,
                )
            )
            service.persist_record(
                replace(
                    action_request,
                    approval_decision_id=approval.approval_decision_id,
                    requested_at=requested_at,
                    expires_at=expires_at,
                    lifecycle_state=request_state,
                )
            )
            action_execution = service.persist_record(
                ActionExecutionRecord(
                    action_execution_id=(
                        f"action-execution-phase21-readiness-automation-impact-{suffix}"
                    ),
                    action_request_id=action_request.action_request_id,
                    approval_decision_id=approval.approval_decision_id,
                    delegation_id=(
                        f"delegation-phase21-readiness-automation-impact-{suffix}"
                    ),
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    execution_run_id=(
                        f"execution-run-phase21-readiness-automation-impact-{suffix}"
                    ),
                    idempotency_key=action_request.idempotency_key,
                    target_scope=dict(action_request.target_scope),
                    approved_payload=dict(action_request.requested_payload),
                    payload_hash=action_request.payload_hash,
                    delegated_at=delegated_at,
                    expires_at=expires_at,
                    provenance={"initiated_by": "operator-review"},
                    lifecycle_state=execution_state,
                )
            )
            service.persist_record(
                ReconciliationRecord(
                    reconciliation_id=(
                        f"reconciliation-phase21-readiness-automation-impact-{suffix}"
                    ),
                    subject_linkage={
                        "action_request_ids": (action_request.action_request_id,),
                        "latest_native_payload": {"secret": "keep-in-store"},
                    },
                    alert_id=promoted_case.alert_id,
                    finding_id=promoted_case.finding_id,
                    analytic_signal_id=None,
                    execution_run_id=action_execution.execution_run_id,
                    linked_execution_run_ids=(action_execution.execution_run_id,),
                    correlation_key=(
                        f"phase21-readiness-automation-impact-{suffix}"
                    ),
                    first_seen_at=delegated_at + timedelta(minutes=1),
                    last_seen_at=delegated_at + timedelta(minutes=2),
                    ingest_disposition="matched",
                    mismatch_summary=mismatch_summary,
                    compared_at=delegated_at + timedelta(minutes=3),
                    lifecycle_state=reconciliation_state,
                )
            )

        persist_review(
            suffix="provider-001",
            requested_offset_minutes=0,
            request_state="failed",
            execution_state="failed",
            reconciliation_state="matched",
            mismatch_summary="provider failure remained tied to reviewed execution lineage",
        )
        persist_review(
            suffix="persistence-001",
            requested_offset_minutes=20,
            request_state="completed",
            execution_state="succeeded",
            reconciliation_state="stale",
            mismatch_summary="persistence drift remained tied to reviewed execution lineage",
        )

        readiness = service.inspect_readiness_diagnostics()
        automation_health = readiness.metrics["automation_substrate_health"]
        shuffle_surface = automation_health["surfaces"]["automation_substrate:shuffle"]

        self.assertEqual(automation_health["overall_state"], "failed")
        self.assertEqual(automation_health["tracked_surfaces"], 1)
        self.assertEqual(shuffle_surface["tracked_reviews"], 2)
        self.assertEqual(shuffle_surface["affected_reviews"], 2)
        self.assertEqual(shuffle_surface["state"], "failed")
        self.assertEqual(shuffle_surface["reason"], "execution_failed")
        self.assertEqual(
            shuffle_surface["paths"]["delegation"]["affected_reviews"],
            0,
        )
        self.assertEqual(
            shuffle_surface["paths"]["provider"]["affected_reviews"],
            1,
        )
        self.assertEqual(
            shuffle_surface["paths"]["persistence"]["affected_reviews"],
            1,
        )

    def test_service_phase21_readiness_weights_automation_reason_by_impacted_reviews(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        future_expires_at = reviewed_at + timedelta(hours=4)

        def persist_review(
            *,
            suffix: str,
            requested_at: datetime,
            delegated_at: datetime,
            expires_at: datetime,
            request_state: str,
            execution_state: str,
            reconciliation_state: str | None,
            mismatch_summary: str,
        ) -> None:
            recommendation = service.record_case_recommendation(
                case_id=promoted_case.case_id,
                review_owner="analyst-001",
                intended_outcome=(
                    "Keep automation substrate dominant reasons aligned with the"
                    f" most impacted reviewed requests ({suffix})."
                ),
            )
            action_request = service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent=(
                    "Keep the dominant automation surface reason weighted by"
                    f" reviewed impact ({suffix})."
                ),
                escalation_reason=(
                    "Operators must see the readiness reason affecting the most"
                    " reviewed requests on the same automation surface."
                ),
                expires_at=future_expires_at,
                action_request_id=(
                    f"action-request-phase21-readiness-automation-weighted-{suffix}"
                ),
            )
            approval = service.persist_record(
                ApprovalDecisionRecord(
                    approval_decision_id=(
                        f"approval-phase21-readiness-automation-weighted-{suffix}"
                    ),
                    action_request_id=action_request.action_request_id,
                    approver_identities=("approver-001",),
                    target_snapshot=dict(action_request.target_scope),
                    payload_hash=action_request.payload_hash,
                    decided_at=requested_at + timedelta(minutes=5),
                    lifecycle_state="approved",
                    approved_expires_at=expires_at,
                )
            )
            service.persist_record(
                replace(
                    action_request,
                    approval_decision_id=approval.approval_decision_id,
                    requested_at=requested_at,
                    expires_at=expires_at,
                    lifecycle_state=request_state,
                )
            )
            action_execution = service.persist_record(
                ActionExecutionRecord(
                    action_execution_id=(
                        f"action-execution-phase21-readiness-automation-weighted-{suffix}"
                    ),
                    action_request_id=action_request.action_request_id,
                    approval_decision_id=approval.approval_decision_id,
                    delegation_id=(
                        f"delegation-phase21-readiness-automation-weighted-{suffix}"
                    ),
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    execution_run_id=(
                        f"execution-run-phase21-readiness-automation-weighted-{suffix}"
                    ),
                    idempotency_key=action_request.idempotency_key,
                    target_scope=dict(action_request.target_scope),
                    approved_payload=dict(action_request.requested_payload),
                    payload_hash=action_request.payload_hash,
                    delegated_at=delegated_at,
                    expires_at=expires_at,
                    provenance={"initiated_by": "operator-review"},
                    lifecycle_state=execution_state,
                )
            )
            if reconciliation_state is not None:
                service.persist_record(
                    ReconciliationRecord(
                        reconciliation_id=(
                            f"reconciliation-phase21-readiness-automation-weighted-{suffix}"
                        ),
                        subject_linkage={
                            "action_request_ids": (action_request.action_request_id,),
                            "latest_native_payload": {"secret": "keep-in-store"},
                        },
                        alert_id=promoted_case.alert_id,
                        finding_id=promoted_case.finding_id,
                        analytic_signal_id=None,
                        execution_run_id=action_execution.execution_run_id,
                        linked_execution_run_ids=(action_execution.execution_run_id,),
                        correlation_key=(
                            f"phase21-readiness-automation-weighted-{suffix}"
                        ),
                        first_seen_at=delegated_at + timedelta(minutes=1),
                        last_seen_at=delegated_at + timedelta(minutes=2),
                        ingest_disposition="matched",
                        mismatch_summary=mismatch_summary,
                        compared_at=delegated_at + timedelta(minutes=3),
                        lifecycle_state=reconciliation_state,
                    )
                )

        persist_review(
            suffix="dispatching-001",
            requested_at=reviewed_at - timedelta(hours=2),
            delegated_at=reviewed_at - timedelta(hours=1, minutes=50),
            expires_at=reviewed_at - timedelta(hours=1),
            request_state="executing",
            execution_state="dispatching",
            reconciliation_state=None,
            mismatch_summary="dispatch lag remained tied to reviewed execution lineage",
        )
        persist_review(
            suffix="persistence-001",
            requested_at=reviewed_at + timedelta(minutes=5),
            delegated_at=reviewed_at + timedelta(minutes=15),
            expires_at=reviewed_at + timedelta(hours=4),
            request_state="completed",
            execution_state="succeeded",
            reconciliation_state="stale",
            mismatch_summary="persistence drift remained tied to reviewed execution lineage",
        )
        persist_review(
            suffix="persistence-002",
            requested_at=reviewed_at + timedelta(minutes=10),
            delegated_at=reviewed_at + timedelta(minutes=20),
            expires_at=reviewed_at + timedelta(hours=4),
            request_state="completed",
            execution_state="succeeded",
            reconciliation_state="stale",
            mismatch_summary="persistence drift remained tied to reviewed execution lineage",
        )

        readiness = service.inspect_readiness_diagnostics()
        automation_health = readiness.metrics["automation_substrate_health"]
        shuffle_surface = automation_health["surfaces"]["automation_substrate:shuffle"]

        self.assertEqual(automation_health["overall_state"], "degraded")
        self.assertEqual(shuffle_surface["state"], "degraded")
        self.assertEqual(shuffle_surface["tracked_reviews"], 3)
        self.assertEqual(shuffle_surface["affected_reviews"], 3)
        self.assertEqual(shuffle_surface["reason"], "reconciliation_stale")
        self.assertEqual(
            shuffle_surface["paths"]["delegation"]["affected_reviews"],
            1,
        )
        self.assertEqual(
            shuffle_surface["paths"]["provider"]["affected_reviews"],
            1,
        )
        self.assertEqual(
            shuffle_surface["paths"]["persistence"]["affected_reviews"],
            3,
        )

    def test_service_phase21_readiness_freezes_review_path_health_as_of_across_snapshot_collection(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        expires_at = reviewed_at + timedelta(hours=4)

        def persist_review(*, suffix: str, requested_offset_minutes: int) -> None:
            recommendation = service.record_case_recommendation(
                case_id=promoted_case.case_id,
                review_owner="analyst-001",
                intended_outcome=(
                    "Keep one frozen review-path evaluation timestamp across"
                    f" readiness snapshots ({suffix})."
                ),
            )
            requested_at = reviewed_at + timedelta(minutes=requested_offset_minutes)
            delegated_at = requested_at + timedelta(minutes=10)
            action_request = service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent=(
                    "Keep readiness review-path health evaluated at one instant"
                    f" across reviewed requests ({suffix})."
                ),
                escalation_reason=(
                    "Operators must not see mixed review-path states caused only"
                    " by crossing an expiry boundary mid-snapshot."
                ),
                expires_at=expires_at,
                action_request_id=(
                    f"action-request-phase21-readiness-frozen-as-of-{suffix}"
                ),
            )
            approval = service.persist_record(
                ApprovalDecisionRecord(
                    approval_decision_id=(
                        f"approval-phase21-readiness-frozen-as-of-{suffix}"
                    ),
                    action_request_id=action_request.action_request_id,
                    approver_identities=("approver-001",),
                    target_snapshot=dict(action_request.target_scope),
                    payload_hash=action_request.payload_hash,
                    decided_at=requested_at + timedelta(minutes=5),
                    lifecycle_state="approved",
                    approved_expires_at=expires_at,
                )
            )
            service.persist_record(
                replace(
                    action_request,
                    approval_decision_id=approval.approval_decision_id,
                    requested_at=requested_at,
                    expires_at=expires_at,
                    lifecycle_state="executing",
                )
            )
            service.persist_record(
                ActionExecutionRecord(
                    action_execution_id=(
                        f"action-execution-phase21-readiness-frozen-as-of-{suffix}"
                    ),
                    action_request_id=action_request.action_request_id,
                    approval_decision_id=approval.approval_decision_id,
                    delegation_id=(
                        f"delegation-phase21-readiness-frozen-as-of-{suffix}"
                    ),
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    execution_run_id=(
                        f"execution-run-phase21-readiness-frozen-as-of-{suffix}"
                    ),
                    idempotency_key=action_request.idempotency_key,
                    target_scope=dict(action_request.target_scope),
                    approved_payload=dict(action_request.requested_payload),
                    payload_hash=action_request.payload_hash,
                    delegated_at=delegated_at,
                    expires_at=expires_at,
                    provenance={"initiated_by": "operator-review"},
                    lifecycle_state="dispatching",
                )
            )

        persist_review(suffix="001", requested_offset_minutes=0)
        persist_review(suffix="002", requested_offset_minutes=15)

        counter = {"value": 0}

        def advancing_now(_tz: timezone | None = None) -> datetime:
            current = reviewed_at + timedelta(seconds=counter["value"])
            counter["value"] += 1
            return current

        with mock.patch(
            "aegisops_control_plane.service.datetime", wraps=datetime
        ) as mocked_datetime:
            mocked_datetime.now.side_effect = advancing_now
            with mock.patch.object(
                service._action_review_inspection_boundary,
                "path_health",
                wraps=service._action_review_inspection_boundary.path_health,
            ) as action_review_path_health:
                readiness = service.inspect_readiness_diagnostics()

        recorded_as_of = [
            call.kwargs["as_of"] for call in action_review_path_health.call_args_list
        ]

        self.assertEqual(readiness.metrics["review_path_health"]["review_count"], 2)
        self.assertEqual(action_review_path_health.call_count, 2)
        self.assertEqual(len(recorded_as_of), 2)
        self.assertEqual(recorded_as_of[0], recorded_as_of[1])

    def test_service_phase21_readiness_prefers_higher_reconciliation_id_when_compared_at_ties(
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
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(reconciliation)

        preferred_reconciliation = replace(
            reconciliation,
            reconciliation_id=f"{reconciliation.reconciliation_id}-z",
            correlation_key=f"{reconciliation.correlation_key}:z",
        )
        service.persist_record(preferred_reconciliation)

        readiness = service.inspect_readiness_diagnostics()

        self.assertIsNotNone(readiness.latest_reconciliation)
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            preferred_reconciliation.reconciliation_id,
        )
