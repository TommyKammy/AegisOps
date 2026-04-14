from __future__ import annotations

import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _service_persistence_support as support
from _service_persistence_support import ServicePersistenceTestBase

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value


class ActionReconciliationPersistenceTests(ServicePersistenceTestBase):
    def test_service_records_execution_correlation_mismatch_states_separately(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        stale_cutoff = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        missing = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(),
            compared_at=requested_at,
            stale_after=stale_cutoff,
        )
        duplicate = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                    "status": "running",
                },
                {
                    "execution_run_id": "exec-002",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
                    "status": "running",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )
        mismatched = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-003",
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-999",
                    "observed_at": datetime(2026, 4, 5, 12, 10, tzinfo=timezone.utc),
                    "status": "failed",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 10, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )
        stale = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-004",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
                    "status": "success",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 45, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )

        self.assertEqual(missing.lifecycle_state, "pending")
        self.assertEqual(missing.ingest_disposition, "missing")
        self.assertEqual(missing.execution_run_id, None)
        self.assertIn("missing downstream execution", missing.mismatch_summary)
        self.assertEqual(
            missing.subject_linkage["action_request_ids"], ("action-request-001",)
        )
        self.assertEqual(
            missing.subject_linkage["execution_surface_types"],
            ("automation_substrate",),
        )
        self.assertEqual(
            missing.subject_linkage["execution_surface_ids"], ("n8n",)
        )

        self.assertEqual(duplicate.lifecycle_state, "mismatched")
        self.assertEqual(duplicate.ingest_disposition, "duplicate")
        self.assertEqual(duplicate.execution_run_id, "exec-002")
        self.assertEqual(
            duplicate.linked_execution_run_ids,
            ("exec-001", "exec-002"),
        )
        self.assertIn("duplicate downstream executions", duplicate.mismatch_summary)

        self.assertEqual(mismatched.lifecycle_state, "mismatched")
        self.assertEqual(mismatched.ingest_disposition, "mismatch")
        self.assertEqual(mismatched.execution_run_id, "exec-003")
        self.assertIn(
            "execution surface/idempotency mismatch",
            mismatched.mismatch_summary,
        )

        self.assertEqual(stale.lifecycle_state, "stale")
        self.assertEqual(stale.ingest_disposition, "stale")
        self.assertEqual(stale.execution_run_id, "exec-004")
        self.assertIn("stale downstream execution observation", stale.mismatch_summary)

        stored_reconciliations = store.list(ReconciliationRecord)
        self.assertEqual(len(stored_reconciliations), 4)
        self.assertEqual(
            sorted(record.ingest_disposition for record in stored_reconciliations),
            ["duplicate", "mismatch", "missing", "stale"],
        )
        self.assertEqual(
            service.get_record(ActionRequestRecord, "action-request-001"),
            action_request,
        )

    def test_service_reconcile_action_execution_rejects_non_approved_requests(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-pending",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="pending_approval",
        )
        service.persist_record(action_request)

        with self.assertRaisesRegex(ValueError, "is not approved"):
            service.reconcile_action_execution(
                action_request_id="action-request-pending",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                observed_executions=(),
                compared_at=requested_at,
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

    def test_service_reconcile_action_execution_requires_aware_datetimes(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        with self.assertRaisesRegex(ValueError, "compared_at must be timezone-aware"):
            service.reconcile_action_execution(
                action_request_id="action-request-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                observed_executions=(),
                compared_at=datetime(2026, 4, 5, 12, 0),
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

        with self.assertRaisesRegex(ValueError, "observed_at must be timezone-aware"):
            service.reconcile_action_execution(
                action_request_id="action-request-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                observed_executions=(
                    {
                        "execution_run_id": "exec-001",
                        "execution_surface_id": "n8n",
                        "idempotency_key": "idempotency-001",
                        "observed_at": datetime(2026, 4, 5, 12, 5),
                    },
                ),
                compared_at=requested_at,
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

    def test_service_reconcile_action_execution_ignores_repeated_polls_of_same_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.execution_run_id, "exec-001")
        self.assertEqual(
            reconciliation.linked_execution_run_ids,
            ("exec-001", "exec-001"),
        )

    def test_service_reconcile_action_execution_supports_generic_execution_surfaces(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
            observed_executions=(
                {
                    "execution_run_id": "executor-run-001",
                    "execution_surface_id": "isolated-executor",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.execution_run_id, "executor-run-001")
        self.assertEqual(
            reconciliation.linked_execution_run_ids,
            ("executor-run-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["execution_surface_types"],
            ("executor",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["execution_surface_ids"],
            ("isolated-executor",),
        )

    def test_service_reconciles_shuffle_run_back_into_authoritative_action_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 12, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-reconcile-001",
                action_request_id="action-request-routine-reconcile-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-reconcile-001",
                approval_decision_id="approval-routine-reconcile-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-reconcile-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-routine-reconcile-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-001",),
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-routine-reconcile-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-routine-reconcile-001",
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "succeeded")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["evidence_ids"],
            ("evidence-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["delegation_ids"],
            (execution.delegation_id,),
        )
        self.assertEqual(
            reconciliation.correlation_key,
            (
                "action-request-routine-reconcile-001:approval-routine-reconcile-001:"
                f"{execution.delegation_id}:automation_substrate:shuffle:"
                "idempotency-routine-reconcile-001"
            ),
        )

    def test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 14, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-003"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-003",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-reconcile-001",
                action_request_id="action-request-executor-reconcile-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-reconcile-001",
                approval_decision_id="approval-executor-reconcile-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-reconcile-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        execution = service.delegate_approved_action_to_isolated_executor(
            action_request_id="action-request-executor-reconcile-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-002",),
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-executor-reconcile-001",
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "isolated-executor",
                    "idempotency_key": "idempotency-executor-reconcile-001",
                    "observed_at": compared_at,
                    "status": "failed",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "failed")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["evidence_ids"],
            ("evidence-002",),
        )

    def test_service_reconciliation_mismatch_does_not_mutate_authoritative_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 12, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-reconcile-mismatch-001",
                action_request_id="action-request-routine-reconcile-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-reconcile-mismatch-001",
                approval_decision_id="approval-routine-reconcile-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-reconcile-mismatch-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-routine-reconcile-mismatch-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-003",),
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-routine-reconcile-mismatch-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "n8n",
                    "idempotency_key": execution.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": compared_at,
                    "status": "failed",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)

    def test_service_reconciliation_fail_closes_when_downstream_run_identity_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 12, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-reconcile-run-drift-001",
                action_request_id="action-request-routine-reconcile-run-drift-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-reconcile-run-drift-001",
                approval_decision_id="approval-routine-reconcile-run-drift-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-reconcile-run-drift-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-routine-reconcile-run-drift-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-004",),
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-routine-reconcile-run-drift-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": "shuffle-run-unexpected-001",
                    "execution_surface_id": "shuffle",
                    "idempotency_key": execution.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertIn("run identity mismatch", reconciliation.mismatch_summary)
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)

    def test_service_evaluates_action_policy_into_approval_and_isolated_executor(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-policy-high-risk",
                approval_decision_id=None,
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-policy-high-risk",
                target_scope={"asset_id": "prod-domain-controller-001"},
                payload_hash="payload-hash-policy-high-risk",
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="draft",
                policy_basis={
                    "severity": "critical",
                    "target_scope": "single_asset",
                    "action_reversibility": "irreversible",
                    "asset_criticality": "critical",
                    "identity_criticality": "high",
                    "blast_radius": "organization",
                    "execution_constraint": "requires_isolated_executor",
                },
            )
        )

        evaluated = service.evaluate_action_policy(
            "action-request-policy-high-risk"
        )

        self.assertEqual(
            evaluated.policy_evaluation,
            {
                "approval_requirement": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "executor",
                "execution_surface_id": "isolated-executor",
            },
        )
        self.assertEqual(
            service.get_record(
                ActionRequestRecord, "action-request-policy-high-risk"
            ),
            evaluated,
        )

    def test_service_evaluates_action_policy_into_shuffle_without_human_approval(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-policy-routine",
                approval_decision_id=None,
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-policy-routine",
                target_scope={"asset_id": "workstation-001"},
                payload_hash="payload-hash-policy-routine",
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="draft",
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_asset",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
            )
        )

        evaluated = service.evaluate_action_policy("action-request-policy-routine")

        self.assertEqual(
            evaluated.policy_evaluation,
            {
                "approval_requirement": "policy_authorized",
                "routing_target": "shuffle",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )

    def test_service_evaluate_action_policy_preserves_reviewed_human_gate_override(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-policy-reviewed-routine",
                approval_decision_id=None,
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-policy-reviewed-routine",
                target_scope={"recipient_identity": "repo-owner-001"},
                payload_hash="payload-hash-policy-reviewed-routine",
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="pending_approval",
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
                    "approval_requirement_override": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        evaluated = service.evaluate_action_policy(
            "action-request-policy-reviewed-routine"
        )

        self.assertEqual(
            evaluated.policy_evaluation,
            {
                "approval_requirement": "human_required",
                "approval_requirement_override": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )

    def test_service_delegates_approved_low_risk_action_through_shuffle_adapter(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-001",
                action_request_id="action-request-routine-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-001",
                approval_decision_id="approval-routine-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_asset",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-routine-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-001",),
        )

        self.assertEqual(
            execution.action_request_id,
            "action-request-routine-001",
        )
        self.assertEqual(
            execution.approval_decision_id,
            "approval-routine-001",
        )
        self.assertEqual(execution.execution_surface_type, "automation_substrate")
        self.assertEqual(execution.execution_surface_id, "shuffle")
        self.assertEqual(
            execution.idempotency_key,
            "idempotency-routine-001",
        )
        self.assertEqual(execution.payload_hash, payload_hash)
        self.assertEqual(
            execution.approved_payload,
            _phase20_notify_identity_owner_payload(
                recipient_identity="repo-owner-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
            ),
        )
        self.assertEqual(
            execution.provenance,
            {
                "delegation_issuer": "control-plane-service",
                "evidence_ids": ("evidence-001",),
                "adapter": "shuffle",
                "downstream_binding": {
                    "approval_decision_id": "approval-routine-001",
                    "delegation_id": execution.delegation_id,
                    "payload_hash": payload_hash,
                },
            },
        )
        self.assertEqual(execution.lifecycle_state, "queued")
        self.assertTrue(execution.delegation_id.startswith("delegation-"))
        self.assertTrue(execution.execution_run_id.startswith("shuffle-run-"))
        self.assertEqual(
            service.get_record(ActionExecutionRecord, execution.action_execution_id),
            execution,
        )

    def test_service_does_not_emit_action_execution_delegated_log_before_commit(
        self,
    ) -> None:
        base_store, _ = make_store()
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        seed_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=base_store,
        )
        seed_service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-commit-failure-001",
                action_request_id="action-request-routine-commit-failure-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        seed_service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-commit-failure-001",
                approval_decision_id="approval-routine-commit-failure-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-commit-failure-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_asset",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
                requested_payload=approved_payload,
            )
        )
        failing_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=_CommitFailingStore(base_store),
        )

        with mock.patch.object(failing_service, "_emit_structured_event") as emit_event:
            with self.assertRaisesRegex(RuntimeError, "synthetic commit failure"):
                failing_service.delegate_approved_action_to_shuffle(
                    action_request_id="action-request-routine-commit-failure-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        emit_event.assert_not_called()
        self.assertEqual(base_store.list(ActionExecutionRecord), ())

    def test_service_dispatches_shuffle_approved_action_outside_store_transaction(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-no-open-tx-001",
                action_request_id="action-request-routine-no-open-tx-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-no-open-tx-001",
                approval_decision_id="approval-routine-no-open-tx-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-no-open-tx-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                requested_payload=approved_payload,
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_asset",
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

        original_dispatch = type(service._shuffle).dispatch_approved_action

        def dispatch_without_transaction(adapter: object, **kwargs: object) -> object:
            self.assertIsNone(store._active_connection.get())
            return original_dispatch(adapter, **kwargs)

        with mock.patch.object(
            type(service._shuffle),
            "dispatch_approved_action",
            autospec=True,
            side_effect=dispatch_without_transaction,
        ):
            execution = service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-no-open-tx-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(execution.lifecycle_state, "queued")
        self.assertTrue(execution.execution_run_id.startswith("shuffle-run-"))

    def test_service_rechecks_shuffle_approval_inside_transaction(self) -> None:
        inner_store, _ = make_store()
        seed_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=inner_store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval_decision = ApprovalDecisionRecord(
            approval_decision_id="approval-routine-tx-recheck-001",
            action_request_id="action-request-routine-tx-recheck-001",
            approver_identities=("approver-001",),
            target_snapshot=approved_target_scope,
            payload_hash=payload_hash,
            decided_at=requested_at,
            lifecycle_state="approved",
        )
        seed_service.persist_record(approval_decision)
        seed_service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-tx-recheck-001",
                approval_decision_id="approval-routine-tx-recheck-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-tx-recheck-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        store = _TransactionMutationStore(
            inner=inner_store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(approval_decision, lifecycle_state="rejected")
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Approval decision 'approval-routine-tx-recheck-001' is not approved",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-tx-recheck-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(inner_store.list(ActionExecutionRecord), ())

    def test_service_fail_closes_when_shuffle_receipt_binding_drifts_after_dispatch(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-receipt-drift-001",
                action_request_id="action-request-routine-receipt-drift-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-receipt-drift-001",
                approval_decision_id="approval-routine-receipt-drift-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-receipt-drift-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
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
        original_dispatch = type(service._shuffle).dispatch_approved_action

        def dispatch_with_binding_drift(adapter: object, **kwargs: object) -> object:
            receipt = original_dispatch(adapter, **kwargs)
            return replace(receipt, payload_hash="payload-hash-drifted")

        with mock.patch.object(
            type(service._shuffle),
            "dispatch_approved_action",
            autospec=True,
            side_effect=dispatch_with_binding_drift,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "shuffle receipt does not match approved delegation binding",
            ):
                service.delegate_approved_action_to_shuffle(
                    action_request_id="action-request-routine-receipt-drift-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertEqual(executions[0].execution_surface_type, "automation_substrate")
        self.assertEqual(executions[0].execution_surface_id, "shuffle")
        self.assertTrue(
            executions[0].execution_run_id.startswith("pending-dispatch-delegation-")
        )
        self.assertNotIn("downstream_binding", executions[0].provenance)
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error_type"],
            "ValueError",
        )

    def test_service_fail_closes_when_shuffle_finalization_fails_after_dispatch(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-finalization-failure-001",
                action_request_id="action-request-routine-finalization-failure-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-finalization-failure-001",
                approval_decision_id="approval-routine-finalization-failure-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-finalization-failure-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                requested_payload=approved_payload,
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_asset",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        original_persist_record = service.persist_record

        def persist_record_with_finalization_failure(record: object) -> object:
            if (
                isinstance(record, ActionExecutionRecord)
                and record.lifecycle_state == "queued"
            ):
                raise RuntimeError("synthetic finalization failure")
            return original_persist_record(record)

        with mock.patch.object(
            service,
            "persist_record",
            side_effect=persist_record_with_finalization_failure,
        ):
            with self.assertRaisesRegex(RuntimeError, "synthetic finalization failure"):
                service.delegate_approved_action_to_shuffle(
                    action_request_id="action-request-routine-finalization-failure-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertEqual(executions[0].execution_surface_type, "automation_substrate")
        self.assertEqual(executions[0].execution_surface_id, "shuffle")
        self.assertTrue(
            executions[0].execution_run_id.startswith("pending-dispatch-delegation-")
        )
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error_type"],
            "RuntimeError",
        )
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error"],
            "synthetic finalization failure",
        )

    def test_service_fail_closes_when_shuffle_receipt_omits_adapter(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-missing-adapter-001",
                action_request_id="action-request-routine-missing-adapter-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-missing-adapter-001",
                approval_decision_id="approval-routine-missing-adapter-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-missing-adapter-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
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
        original_dispatch = type(service._shuffle).dispatch_approved_action

        def dispatch_without_adapter(adapter: object, **kwargs: object) -> object:
            receipt = original_dispatch(adapter, **kwargs)
            return SimpleNamespace(
                execution_surface_type=receipt.execution_surface_type,
                execution_surface_id=receipt.execution_surface_id,
                execution_run_id=receipt.execution_run_id,
                approval_decision_id=receipt.approval_decision_id,
                delegation_id=receipt.delegation_id,
                payload_hash=receipt.payload_hash,
                base_url=receipt.base_url,
            )

        with mock.patch.object(
            type(service._shuffle),
            "dispatch_approved_action",
            autospec=True,
            side_effect=dispatch_without_adapter,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "adapter receipt missing required 'adapter' attribute",
            ):
                service.delegate_approved_action_to_shuffle(
                    action_request_id="action-request-routine-missing-adapter-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertNotIn("adapter", executions[0].provenance)
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error_type"],
            "ValueError",
        )
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error"],
            "adapter receipt missing required 'adapter' attribute",
        )

    def test_service_fail_closes_when_shuffle_receipt_omits_execution_run_id(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-missing-run-id-001",
                action_request_id="action-request-routine-missing-run-id-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-missing-run-id-001",
                approval_decision_id="approval-routine-missing-run-id-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-missing-run-id-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
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
        original_dispatch = type(service._shuffle).dispatch_approved_action

        def dispatch_without_execution_run_id(adapter: object, **kwargs: object) -> object:
            receipt = original_dispatch(adapter, **kwargs)
            return replace(receipt, execution_run_id="")

        with mock.patch.object(
            type(service._shuffle),
            "dispatch_approved_action",
            autospec=True,
            side_effect=dispatch_without_execution_run_id,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "adapter receipt missing required 'execution_run_id' attribute",
            ):
                service.delegate_approved_action_to_shuffle(
                    action_request_id="action-request-routine-missing-run-id-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertTrue(
            executions[0].execution_run_id.startswith("pending-dispatch-delegation-")
        )
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error_type"],
            "ValueError",
        )
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error"],
            "adapter receipt missing required 'execution_run_id' attribute",
        )

    def test_service_fail_closes_when_isolated_executor_receipt_surface_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-001"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-receipt-drift-001",
                action_request_id="action-request-executor-receipt-drift-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-receipt-drift-001",
                approval_decision_id="approval-executor-receipt-drift-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-receipt-drift-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                requested_payload=approved_payload,
                policy_basis={
                    "severity": "critical",
                    "target_scope": "single_asset",
                    "action_reversibility": "irreversible",
                    "asset_criticality": "critical",
                    "identity_criticality": "high",
                    "blast_radius": "organization",
                    "execution_constraint": "requires_isolated_executor",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )
        original_dispatch = type(service._isolated_executor).dispatch_approved_action

        def dispatch_with_surface_drift(adapter: object, **kwargs: object) -> object:
            receipt = original_dispatch(adapter, **kwargs)
            return replace(
                receipt,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
            )

        with mock.patch.object(
            type(service._isolated_executor),
            "dispatch_approved_action",
            autospec=True,
            side_effect=dispatch_with_surface_drift,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "adapter receipt does not match approved execution surface",
            ):
                service.delegate_approved_action_to_isolated_executor(
                    action_request_id="action-request-executor-receipt-drift-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertEqual(executions[0].execution_surface_type, "executor")
        self.assertEqual(executions[0].execution_surface_id, "isolated-executor")
        self.assertTrue(
            executions[0].execution_run_id.startswith("pending-dispatch-delegation-")
        )
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error_type"],
            "ValueError",
        )

    def test_service_fail_closes_when_isolated_executor_receipt_omits_execution_run_id(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-001"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-missing-run-id-001",
                action_request_id="action-request-executor-missing-run-id-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-missing-run-id-001",
                approval_decision_id="approval-executor-missing-run-id-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-missing-run-id-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                requested_payload=approved_payload,
                policy_basis={
                    "severity": "critical",
                    "target_scope": "single_asset",
                    "action_reversibility": "irreversible",
                    "asset_criticality": "critical",
                    "identity_criticality": "high",
                    "blast_radius": "organization",
                    "execution_constraint": "requires_isolated_executor",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )
        original_dispatch = type(service._isolated_executor).dispatch_approved_action

        def dispatch_without_execution_run_id(adapter: object, **kwargs: object) -> object:
            receipt = original_dispatch(adapter, **kwargs)
            return replace(receipt, execution_run_id="")

        with mock.patch.object(
            type(service._isolated_executor),
            "dispatch_approved_action",
            autospec=True,
            side_effect=dispatch_without_execution_run_id,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "adapter receipt missing required 'execution_run_id' attribute",
            ):
                service.delegate_approved_action_to_isolated_executor(
                    action_request_id="action-request-executor-missing-run-id-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertTrue(
            executions[0].execution_run_id.startswith("pending-dispatch-delegation-")
        )
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error_type"],
            "ValueError",
        )
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error"],
            "adapter receipt missing required 'execution_run_id' attribute",
        )

    def test_service_rejects_shuffle_delegation_when_payload_binding_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = {
            "action_type": "notify_identity_owner",
            "asset_id": "workstation-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-mismatch-001",
                action_request_id="action-request-routine-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-mismatch-001",
                approval_decision_id="approval-routine-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-mismatch-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-mismatch-001",
                approved_payload={
                    "action_type": "notify_identity_owner",
                    "asset_id": "workstation-999",
                },
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_shuffle_delegation_when_expiry_window_drifts_after_approval(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        drifted_expires_at = datetime(2026, 4, 5, 14, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-expiry-001"}
        approved_payload = {
            "action_type": "notify_identity_owner",
            "asset_id": "workstation-expiry-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval_decision = ApprovalDecisionRecord(
            approval_decision_id="approval-routine-expiry-drift-001",
            action_request_id="action-request-routine-expiry-drift-001",
            approver_identities=("approver-001",),
            target_snapshot=approved_target_scope,
            payload_hash=payload_hash,
            decided_at=requested_at,
            lifecycle_state="approved",
            approved_expires_at=approved_expires_at,
        )
        action_request = ActionRequestRecord(
            action_request_id="action-request-routine-expiry-drift-001",
            approval_decision_id="approval-routine-expiry-drift-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-routine-expiry-drift-001",
            target_scope=approved_target_scope,
            payload_hash=payload_hash,
            requested_at=requested_at,
            expires_at=approved_expires_at,
            lifecycle_state="approved",
            policy_evaluation={
                "approval_requirement": "human_required",
                "routing_target": "shuffle",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )
        service.persist_record(approval_decision)
        service.persist_record(action_request)
        service.persist_record(replace(action_request, expires_at=drifted_expires_at))

        with self.assertRaisesRegex(
            ValueError,
            "approved expiry window does not match action request expiry",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-expiry-drift-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_isolated_executor_delegation_when_expiry_window_drifts_after_approval(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        drifted_expires_at = datetime(2026, 4, 5, 14, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-expiry-001"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-expiry-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        approval_decision = ApprovalDecisionRecord(
            approval_decision_id="approval-executor-expiry-drift-001",
            action_request_id="action-request-executor-expiry-drift-001",
            approver_identities=("approver-001",),
            target_snapshot=approved_target_scope,
            payload_hash=payload_hash,
            decided_at=requested_at,
            lifecycle_state="approved",
            approved_expires_at=approved_expires_at,
        )
        action_request = ActionRequestRecord(
            action_request_id="action-request-executor-expiry-drift-001",
            approval_decision_id="approval-executor-expiry-drift-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-executor-expiry-drift-001",
            target_scope=approved_target_scope,
            payload_hash=payload_hash,
            requested_at=requested_at,
            expires_at=approved_expires_at,
            lifecycle_state="approved",
            policy_evaluation={
                "approval_requirement": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "executor",
                "execution_surface_id": "isolated-executor",
            },
        )
        service.persist_record(approval_decision)
        service.persist_record(action_request)
        service.persist_record(replace(action_request, expires_at=drifted_expires_at))

        with self.assertRaisesRegex(
            ValueError,
            "approved expiry window does not match action request expiry",
        ):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-expiry-drift-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_shuffle_delegation_when_target_scope_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approval_target_scope = {"asset_id": "workstation-001"}
        requested_target_scope = {"asset_id": "workstation-777"}
        approved_payload = {
            "action_type": "notify_identity_owner",
            "asset_id": "workstation-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=requested_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-target-mismatch-001",
                action_request_id="action-request-routine-target-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-target-mismatch-001",
                approval_decision_id="approval-routine-target-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-target-mismatch-001",
                target_scope=requested_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-target-mismatch-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_shuffle_delegation_for_non_shuffle_execution_policy(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-001",
                action_request_id="action-request-executor-001",
                approver_identities=("approver-001",),
                target_snapshot={"asset_id": "critical-host-001"},
                payload_hash="payload-hash-executor-001",
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-001",
                approval_decision_id="approval-executor-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-001",
                target_scope={"asset_id": "critical-host-001"},
                payload_hash="payload-hash-executor-001",
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "not delegated through the automation substrate path",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-executor-001",
                approved_payload={"action_type": "disable_identity"},
                delegated_at=datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                delegation_issuer="control-plane-service",
            )

    def test_service_rejects_shuffle_delegation_for_non_phase20_live_action(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-unsupported-001"}
        approved_payload = {
            "action_type": "open_ticket",
            "asset_id": "workstation-unsupported-001",
            "ticket_queue": "soc-owner-followup",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-unsupported-action-001",
                action_request_id="action-request-routine-unsupported-action-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-unsupported-action-001",
                approval_decision_id="approval-routine-unsupported-action-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-unsupported-action-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "approved action is outside the reviewed Phase 20 Shuffle delegation scope",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-unsupported-action-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_delegates_approved_high_risk_action_through_isolated_executor(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-002"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-002",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-002",
                action_request_id="action-request-executor-002",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-002",
                approval_decision_id="approval-executor-002",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-002",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_basis={
                    "severity": "critical",
                    "target_scope": "single_asset",
                    "action_reversibility": "irreversible",
                    "asset_criticality": "critical",
                    "identity_criticality": "high",
                    "blast_radius": "organization",
                    "execution_constraint": "requires_isolated_executor",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        execution = service.delegate_approved_action_to_isolated_executor(
            action_request_id="action-request-executor-002",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-002",),
        )

        self.assertEqual(execution.action_request_id, "action-request-executor-002")
        self.assertEqual(execution.approval_decision_id, "approval-executor-002")
        self.assertEqual(execution.execution_surface_type, "executor")
        self.assertEqual(execution.execution_surface_id, "isolated-executor")
        self.assertEqual(execution.idempotency_key, "idempotency-executor-002")
        self.assertEqual(execution.payload_hash, payload_hash)
        self.assertEqual(
            execution.approved_payload,
            {
                "action_type": "disable_identity",
                "asset_id": "critical-host-002",
            },
        )
        self.assertEqual(
            execution.provenance,
            {
                "delegation_issuer": "control-plane-service",
                "evidence_ids": ("evidence-002",),
                "adapter": "isolated-executor",
            },
        )
        self.assertEqual(execution.lifecycle_state, "queued")
        self.assertTrue(execution.delegation_id.startswith("delegation-"))
        self.assertTrue(execution.execution_run_id.startswith("executor-run-"))
        self.assertEqual(
            service.get_record(ActionExecutionRecord, execution.action_execution_id),
            execution,
        )

    def test_service_emits_action_execution_delegated_log_for_isolated_executor(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-003"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-003",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-log-001",
                action_request_id="action-request-executor-log-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-log-001",
                approval_decision_id="approval-executor-log-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-log-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_basis={
                    "severity": "critical",
                    "target_scope": "single_asset",
                    "action_reversibility": "irreversible",
                    "asset_criticality": "critical",
                    "identity_criticality": "high",
                    "blast_radius": "organization",
                    "execution_constraint": "requires_isolated_executor",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with mock.patch.object(service, "_emit_structured_event") as emit_event:
            execution = service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-log-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        emit_event.assert_called_once_with(
            logging.INFO,
            "action_execution_delegated",
            action_execution_id=execution.action_execution_id,
            action_request_id=execution.action_request_id,
            approval_decision_id=execution.approval_decision_id,
            execution_surface_type=execution.execution_surface_type,
            execution_surface_id=execution.execution_surface_id,
            execution_run_id=execution.execution_run_id,
            lifecycle_state=execution.lifecycle_state,
        )

    def test_service_rejects_isolated_executor_delegation_for_cross_linked_approval(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-002"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-002",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-cross-link-001",
                action_request_id="action-request-executor-cross-link-other",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-cross-link-001",
                approval_decision_id="approval-executor-cross-link-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-cross-link-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-cross-link-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_isolated_executor_delegation_when_payload_binding_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-002"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-002",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-mismatch-001",
                action_request_id="action-request-executor-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-mismatch-001",
                approval_decision_id="approval-executor-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-mismatch-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-mismatch-001",
                approved_payload={
                    "action_type": "disable_account",
                    "asset_id": "critical-host-002",
                },
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_isolated_executor_delegation_when_target_scope_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approval_target_scope = {"asset_id": "critical-host-002"}
        requested_target_scope = {"asset_id": "critical-host-999"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-002",
        }
        payload_hash = _approved_binding_hash(
            target_scope=requested_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-target-mismatch-001",
                action_request_id="action-request-executor-target-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-target-mismatch-001",
                approval_decision_id="approval-executor-target-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-target-mismatch-001",
                target_scope=requested_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-target-mismatch-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_creates_approval_bound_action_request_from_reviewed_recommendation(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
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
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertIsNone(action_request.approval_decision_id)
        self.assertEqual(action_request.case_id, promoted_case.case_id)
        self.assertEqual(action_request.alert_id, promoted_case.alert_id)
        self.assertEqual(action_request.finding_id, promoted_case.finding_id)
        self.assertEqual(action_request.requester_identity, "analyst-001")
        self.assertEqual(
            action_request.target_scope,
            {
                "record_family": "recommendation",
                "record_id": recommendation.recommendation_id,
                "case_id": promoted_case.case_id,
                "alert_id": promoted_case.alert_id,
                "finding_id": promoted_case.finding_id,
                "recipient_identity": "repo-owner-001",
            },
        )
        self.assertEqual(
            action_request.requested_payload,
            {
                "action_type": "notify_identity_owner",
                "recipient_identity": "repo-owner-001",
                "message_intent": "Notify the accountable repository owner about the reviewed permission change.",
                "escalation_reason": "Reviewed GitHub audit evidence requires bounded owner notification.",
                "source_record_family": "recommendation",
                "source_record_id": recommendation.recommendation_id,
                "recommendation_id": recommendation.recommendation_id,
                "case_id": promoted_case.case_id,
                "alert_id": promoted_case.alert_id,
                "finding_id": promoted_case.finding_id,
                "linked_evidence_ids": (evidence_id,),
            },
        )
        self.assertEqual(
            action_request.payload_hash,
            _approved_binding_hash(
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
            ),
        )
        self.assertEqual(action_request.expires_at, expires_at)
        self.assertEqual(action_request.lifecycle_state, "pending_approval")
        self.assertEqual(
            action_request.policy_evaluation,
            {
                "approval_requirement": "human_required",
                "approval_requirement_override": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )
        self.assertEqual(
            service.get_record(ActionRequestRecord, action_request.action_request_id),
            action_request,
        )
        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_does_not_emit_action_request_created_log_before_commit(
        self,
    ) -> None:
        base_store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Prepare a reviewed owner notification request.",
        )
        failing_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=_CommitFailingStore(base_store),
        )
        baseline_requests = base_store.list(ActionRequestRecord)

        with mock.patch.object(failing_service, "_emit_structured_event") as emit_event:
            with self.assertRaisesRegex(RuntimeError, "synthetic commit failure"):
                failing_service.create_reviewed_action_request_from_advisory(
                    record_family="recommendation",
                    record_id=recommendation.recommendation_id,
                    requester_identity="analyst-001",
                    recipient_identity="repo-owner-001",
                    message_intent="Notify the repository owner about the reviewed change.",
                    escalation_reason="Reviewed low-risk action remains approval-bound.",
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
                )

        emit_event.assert_not_called()
        self.assertEqual(base_store.list(ActionRequestRecord), baseline_requests)

    def test_service_executes_phase20_first_live_action_end_to_end_from_reviewed_recommendation(
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
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-e2e-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
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
            delegated_at=delegated_at,
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
                    "observed_at": observed_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertEqual(
            approved_request.requested_payload["action_type"],
            "notify_identity_owner",
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "succeeded")
        self.assertEqual(stored_execution.approval_decision_id, "approval-phase20-e2e-001")
        self.assertEqual(stored_execution.execution_surface_type, "automation_substrate")
        self.assertEqual(stored_execution.execution_surface_id, "shuffle")
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.execution_run_id, execution.execution_run_id)
        self.assertEqual(
            reconciliation.subject_linkage["action_request_ids"],
            (approved_request.action_request_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["approval_decision_ids"],
            ("approval-phase20-e2e-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["delegation_ids"],
            (execution.delegation_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["evidence_ids"],
            (evidence_id,),
        )

    def test_service_phase20_first_live_action_fail_closes_on_downstream_execution_surface_mismatch(
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
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-mismatch-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
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
            delegated_at=delegated_at,
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
                    "execution_surface_id": "n8n",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(stored_execution.execution_surface_id, "shuffle")
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(
            reconciliation.mismatch_summary,
            "execution surface/idempotency mismatch between approved request and observed execution",
        )
        self.assertEqual(
            reconciliation.subject_linkage["approval_decision_ids"],
            ("approval-phase20-mismatch-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )

    def test_service_reconciliation_rolls_back_execution_state_when_reconciliation_write_fails(
        self,
    ) -> None:
        base_store, seed_service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = seed_service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = seed_service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = seed_service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-reconciliation-atomic-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = seed_service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        execution = seed_service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        existing_reconciliation_ids = {
            record.reconciliation_id for record in base_store.list(ReconciliationRecord)
        }
        failing_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=_RecordTypeSaveFailingStore(
                inner=base_store,
                record_type=ReconciliationRecord,
                message="synthetic reconciliation save failure",
            ),
        )

        with mock.patch.object(failing_service, "_emit_structured_event") as emit_event:
            with self.assertRaisesRegex(
                RuntimeError,
                "synthetic reconciliation save failure",
            ):
                failing_service.reconcile_action_execution(
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
                            "observed_at": observed_at,
                            "status": "success",
                        },
                    ),
                    compared_at=compared_at,
                    stale_after=stale_after,
                )

        emit_event.assert_not_called()
        stored_execution = base_store.get(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(
            {
                record.reconciliation_id
                for record in base_store.list(ReconciliationRecord)
            },
            existing_reconciliation_ids,
        )

    def test_service_reconciliation_does_not_downgrade_authoritative_execution_lifecycle(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-reconciliation-monotonic-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
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
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        service.persist_record(replace(execution, lifecycle_state="running"))

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
                    "observed_at": observed_at,
                    "status": "queued",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "running")
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(
            service._execution_coordinator._action_execution_lifecycle_from_status(
                "running",
                "succeeded",
            ),
            "succeeded",
        )

    def test_service_phase20_reconciliation_rejects_downstream_evidence_missing_binding_identifiers(
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
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-missing-binding-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
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
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )

        with self.assertRaisesRegex(
            ValueError,
            "observed execution must include string approval_decision_id",
        ):
            service.reconcile_action_execution(
                action_request_id=approved_request.action_request_id,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=(
                    {
                        "execution_run_id": execution.execution_run_id,
                        "execution_surface_id": "shuffle",
                        "idempotency_key": approved_request.idempotency_key,
                        "observed_at": observed_at,
                        "status": "success",
                    },
                ),
                compared_at=compared_at,
                stale_after=stale_after,
            )

    def test_service_rejects_reviewed_action_request_creation_when_malformed_or_out_of_scope(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        future_expiry = datetime.now(timezone.utc) + timedelta(hours=4)

        with self.assertRaisesRegex(
            ValueError,
            "recipient_identity must be a non-empty string",
        ):
            service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=future_expiry,
            )

        replay_service, replay_case, _, _ = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )
        replay_recommendation = replay_service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase20-out-of-scope-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=replay_case.alert_id,
                case_id=replay_case.case_id,
                ai_trace_id=None,
                review_owner="analyst-001",
                intended_outcome="Synthetic advisory reads must fail closed.",
                lifecycle_state="under_review",
                reviewed_context=replay_case.reviewed_context,
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            replay_service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=replay_recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=future_expiry,
            )

    def test_service_reuses_reviewed_action_request_for_matching_idempotency_key(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertEqual(second_request, first_request)
        self.assertEqual(store.list(ActionRequestRecord), (first_request,))

    def test_service_reuses_reviewed_action_request_for_equivalent_expiry_instants(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at_utc = datetime.now(timezone.utc) + timedelta(hours=4)
        expires_at_plus_two = expires_at_utc.astimezone(
            timezone(timedelta(hours=2))
        )

        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at_utc,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at_plus_two,
        )

        self.assertEqual(second_request, first_request)
        self.assertEqual(store.list(ActionRequestRecord), (first_request,))

    def test_service_inspects_action_review_states_on_queue_alert_and_case_surfaces(
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
            action_request_id="action-request-surface-pending-001",
        )
        base_requested_at = pending_request.requested_at
        rejected_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-rejected-001",
                action_request_id="action-request-surface-rejected-001",
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
                action_request_id="action-request-surface-rejected-001",
                approval_decision_id=rejected_decision.approval_decision_id,
                idempotency_key="idempotency-surface-rejected-001",
                requested_at=base_requested_at + timedelta(minutes=5),
                lifecycle_state="rejected",
                requester_identity="analyst-002",
            )
        )
        expired_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-expired-001",
                action_request_id="action-request-surface-expired-001",
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
                action_request_id="action-request-surface-expired-001",
                approval_decision_id=expired_decision.approval_decision_id,
                idempotency_key="idempotency-surface-expired-001",
                requested_at=base_requested_at + timedelta(minutes=15),
                expires_at=base_requested_at + timedelta(minutes=30),
                lifecycle_state="expired",
                requester_identity="analyst-003",
            )
        )
        superseded_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-surface-superseded-001",
                idempotency_key="idempotency-surface-superseded-001",
                requested_at=base_requested_at + timedelta(minutes=25),
                lifecycle_state="superseded",
                requester_identity="analyst-004",
            )
        )
        replacement_request = service.persist_record(
            replace(
                pending_request,
                action_request_id="action-request-surface-replacement-001",
                idempotency_key="idempotency-surface-replacement-001",
                requested_at=base_requested_at + timedelta(minutes=35),
                requester_identity="analyst-005",
            )
        )

        queue_snapshot = service.inspect_analyst_queue().to_dict()
        alert_snapshot = service.inspect_alert_detail(promoted_case.alert_id).to_dict()
        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()

        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["action_request_id"],
            replacement_request.action_request_id,
        )
        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["review_state"],
            "pending",
        )
        self.assertEqual(alert_snapshot["current_action_review"]["review_state"], "pending")
        self.assertEqual(case_snapshot["current_action_review"]["review_state"], "pending")
        action_reviews_by_id = {
            record["action_request_id"]: record for record in case_snapshot["action_reviews"]
        }
        self.assertEqual(
            action_reviews_by_id[pending_request.action_request_id]["review_state"],
            "pending",
        )
        self.assertEqual(
            action_reviews_by_id[rejected_request.action_request_id]["review_state"],
            "rejected",
        )
        self.assertEqual(
            action_reviews_by_id[rejected_request.action_request_id]["approver_identities"],
            ["approver-rejected-001"],
        )
        self.assertEqual(
            action_reviews_by_id[expired_request.action_request_id]["review_state"],
            "expired",
        )
        self.assertEqual(
            action_reviews_by_id[superseded_request.action_request_id]["review_state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[superseded_request.action_request_id]["approval_state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[superseded_request.action_request_id]["timeline"][1]["state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[superseded_request.action_request_id][
                "replacement_action_request_id"
            ],
            replacement_request.action_request_id,
        )

    def test_service_action_review_surfaces_keep_execution_linked_reconciliation_when_approval_lookup_is_missing(
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
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-indexed-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=support.datetime.now(support.timezone.utc)
            + support.timedelta(hours=4),
            action_request_id="action-request-surface-indexed-lineage-001",
        )
        action_request = service.persist_record(
            support.replace(
                action_request,
                approval_decision_id="approval-surface-missing-indexed-001",
                lifecycle_state="approved",
            )
        )
        action_execution = service.persist_record(
            support.ActionExecutionRecord(
                action_execution_id="action-execution-surface-indexed-lineage-001",
                action_request_id=action_request.action_request_id,
                approval_decision_id="approval-surface-missing-indexed-001",
                delegation_id="delegation-surface-indexed-lineage-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-surface-indexed-lineage-001",
                idempotency_key=action_request.idempotency_key,
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                payload_hash=action_request.payload_hash,
                delegated_at=action_request.requested_at
                + support.timedelta(minutes=10),
                expires_at=action_request.expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="queued",
            )
        )
        reconciliation = service.persist_record(
            support.ReconciliationRecord(
                reconciliation_id="reconciliation-surface-indexed-lineage-001",
                subject_linkage={
                    "case_ids": (promoted_case.case_id,),
                    "action_execution_ids": (action_execution.action_execution_id,),
                    "delegation_ids": (action_execution.delegation_id,),
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id="execution-run-surface-indexed-lineage-observed-001",
                linked_execution_run_ids=(
                    "execution-run-surface-indexed-lineage-observed-001",
                ),
                correlation_key="surface-indexed-lineage-001",
                first_seen_at=action_execution.delegated_at
                + support.timedelta(minutes=1),
                last_seen_at=action_execution.delegated_at
                + support.timedelta(minutes=2),
                ingest_disposition="mismatch",
                mismatch_summary="execution lineage should remain visible without approval lookup",
                compared_at=action_execution.delegated_at
                + support.timedelta(minutes=3),
                lifecycle_state="mismatched",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_review = case_snapshot["current_action_review"]

        self.assertEqual(
            action_review["action_request_id"],
            action_request.action_request_id,
        )
        self.assertEqual(
            action_review["action_execution_id"],
            action_execution.action_execution_id,
        )
        self.assertEqual(
            action_review["reconciliation_id"],
            reconciliation.reconciliation_id,
        )
        self.assertEqual(
            action_review["timeline"][4]["record_id"],
            reconciliation.reconciliation_id,
        )
        self.assertEqual(
            action_review["mismatch_inspection"]["reconciliation_id"],
            reconciliation.reconciliation_id,
        )

    def test_service_analyst_queue_prefetches_action_review_records_once_per_inspection(
        self,
    ) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-002",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        store.list_calls = 0
        store.reconciliation_list_calls = 0
        queue_snapshot = service.inspect_analyst_queue().to_dict()

        self.assertEqual(queue_snapshot["total_records"], 1)
        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["action_request_id"],
            second_request.action_request_id,
        )
        self.assertLessEqual(store.list_calls, 6)
        self.assertEqual(store.reconciliation_list_calls, 2)
        self.assertNotEqual(first_request.action_request_id, second_request.action_request_id)

    def test_service_action_review_surfaces_prefer_live_approval_and_execution_records(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        approved_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-approved-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-stale-approved-001",
        )
        approved_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-stale-approved-001",
                action_request_id=approved_request.action_request_id,
                approver_identities=("approver-approved-001",),
                target_snapshot=dict(approved_request.target_scope),
                payload_hash=approved_request.payload_hash,
                decided_at=approved_request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            replace(
                approved_request,
                approval_decision_id=approved_decision.approval_decision_id,
                lifecycle_state="pending_approval",
            )
        )

        executing_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-002",
            recipient_identity="repo-owner-executing-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-stale-executing-001",
        )
        executing_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-stale-executing-001",
                action_request_id=executing_request.action_request_id,
                approver_identities=("approver-executing-001",),
                target_snapshot=dict(executing_request.target_scope),
                payload_hash=executing_request.payload_hash,
                decided_at=executing_request.requested_at + timedelta(minutes=10),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            replace(
                executing_request,
                approval_decision_id=executing_decision.approval_decision_id,
                lifecycle_state="pending_approval",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-surface-stale-executing-001",
                action_request_id=executing_request.action_request_id,
                approval_decision_id=executing_decision.approval_decision_id,
                delegation_id="delegation-surface-stale-executing-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                execution_run_id="execution-run-surface-stale-executing-001",
                idempotency_key=executing_request.idempotency_key,
                target_scope=dict(executing_request.target_scope),
                approved_payload=dict(executing_request.requested_payload),
                payload_hash=executing_request.payload_hash,
                delegated_at=executing_request.requested_at + timedelta(minutes=15),
                expires_at=expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="queued",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_reviews_by_id = {
            record["action_request_id"]: record for record in case_snapshot["action_reviews"]
        }

        self.assertEqual(
            action_reviews_by_id[approved_request.action_request_id]["review_state"],
            "approved",
        )
        self.assertEqual(
            action_reviews_by_id[approved_request.action_request_id]["next_expected_action"],
            "await_reviewed_delegation",
        )
        self.assertEqual(
            action_reviews_by_id[approved_request.action_request_id]["approval_state"],
            "approved",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id]["review_state"],
            "executing",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id][
                "next_expected_action"
            ],
            "await_execution_reconciliation",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id][
                "action_execution_id"
            ],
            "action-execution-surface-stale-executing-001",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id][
                "execution_surface_type"
            ],
            "automation_substrate",
        )
        self.assertEqual(
            action_reviews_by_id[executing_request.action_request_id][
                "execution_surface_id"
            ],
            "n8n",
        )

    def test_service_action_review_surfaces_keep_policy_authorized_requests_out_of_review_chains(
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
        reviewed_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-reviewed-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-surface-reviewed-superseded-001",
        )
        reviewed_request = service.persist_record(
            replace(
                reviewed_request,
                lifecycle_state="superseded",
            )
        )
        reviewed_replacement = service.persist_record(
            replace(
                reviewed_request,
                action_request_id="action-request-surface-reviewed-replacement-001",
                idempotency_key="idempotency-surface-reviewed-replacement-001",
                requested_at=reviewed_request.requested_at + timedelta(minutes=10),
                lifecycle_state="pending_approval",
                requester_identity="analyst-002",
            )
        )
        policy_authorized_request = service.persist_record(
            replace(
                reviewed_request,
                action_request_id="action-request-surface-policy-authorized-001",
                approval_decision_id=None,
                idempotency_key="idempotency-surface-policy-authorized-001",
                requested_at=reviewed_request.requested_at + timedelta(minutes=20),
                lifecycle_state="approved",
                requester_identity="policy-engine",
                policy_evaluation={
                    "approval_requirement": "policy_authorized",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        queue_snapshot = service.inspect_analyst_queue().to_dict()
        alert_snapshot = service.inspect_alert_detail(promoted_case.alert_id).to_dict()
        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_reviews_by_id = {
            record["action_request_id"]: record for record in case_snapshot["action_reviews"]
        }

        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["action_request_id"],
            reviewed_replacement.action_request_id,
        )
        self.assertEqual(
            alert_snapshot["current_action_review"]["action_request_id"],
            reviewed_replacement.action_request_id,
        )
        self.assertEqual(
            case_snapshot["current_action_review"]["action_request_id"],
            reviewed_replacement.action_request_id,
        )
        self.assertNotIn(
            policy_authorized_request.action_request_id,
            action_reviews_by_id,
        )
        self.assertEqual(
            action_reviews_by_id[reviewed_request.action_request_id][
                "replacement_action_request_id"
            ],
            reviewed_replacement.action_request_id,
        )

    def test_service_action_review_surfaces_preserve_terminal_execution_states(
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
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-completed-execution-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-completed-execution-001",
        )
        decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-completed-execution-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-completed-execution-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        request = service.persist_record(
            replace(
                request,
                approval_decision_id=decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-surface-completed-001",
                action_request_id=request.action_request_id,
                approval_decision_id=decision.approval_decision_id,
                delegation_id="delegation-surface-completed-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-surface-completed-001",
                idempotency_key=request.idempotency_key,
                target_scope=dict(request.target_scope),
                approved_payload=dict(request.requested_payload),
                payload_hash=request.payload_hash,
                delegated_at=request.requested_at + timedelta(minutes=10),
                expires_at=expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="succeeded",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_review = case_snapshot["current_action_review"]

        self.assertEqual(
            action_review["action_request_id"],
            request.action_request_id,
        )
        self.assertEqual(action_review["review_state"], "completed")
        self.assertEqual(
            action_review["action_execution_state"],
            "succeeded",
        )
        self.assertEqual(
            action_review["next_expected_action"],
            "review_execution_outcome",
        )

    def test_service_action_review_surfaces_preserve_canceled_execution_state(
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
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-canceled-execution-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-canceled-execution-001",
        )
        decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-canceled-execution-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-canceled-execution-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        request = service.persist_record(
            replace(
                request,
                approval_decision_id=decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-surface-canceled-001",
                action_request_id=request.action_request_id,
                approval_decision_id=decision.approval_decision_id,
                delegation_id="delegation-surface-canceled-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-surface-canceled-001",
                idempotency_key=request.idempotency_key,
                target_scope=dict(request.target_scope),
                approved_payload=dict(request.requested_payload),
                payload_hash=request.payload_hash,
                delegated_at=request.requested_at + timedelta(minutes=10),
                expires_at=expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="canceled",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_review = case_snapshot["current_action_review"]

        self.assertEqual(
            action_review["action_request_id"],
            request.action_request_id,
        )
        self.assertEqual(action_review["review_state"], "canceled")
        self.assertEqual(
            action_review["action_execution_state"],
            "canceled",
        )
        self.assertEqual(
            action_review["next_expected_action"],
            "investigate_execution_cancellation",
        )

    def test_service_action_review_surfaces_preserve_failed_execution_state(
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
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-failed-execution-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-failed-execution-001",
        )
        decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-failed-execution-001",
                action_request_id=request.action_request_id,
                approver_identities=("approver-failed-execution-001",),
                target_snapshot=dict(request.target_scope),
                payload_hash=request.payload_hash,
                decided_at=request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        request = service.persist_record(
            replace(
                request,
                approval_decision_id=decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-surface-failed-001",
                action_request_id=request.action_request_id,
                approval_decision_id=decision.approval_decision_id,
                delegation_id="delegation-surface-failed-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-surface-failed-001",
                idempotency_key=request.idempotency_key,
                target_scope=dict(request.target_scope),
                approved_payload=dict(request.requested_payload),
                payload_hash=request.payload_hash,
                delegated_at=request.requested_at + timedelta(minutes=10),
                expires_at=expires_at,
                provenance={"initiated_by": "operator-review"},
                lifecycle_state="failed",
            )
        )

        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_review = case_snapshot["current_action_review"]

        self.assertEqual(
            action_review["action_request_id"],
            request.action_request_id,
        )
        self.assertEqual(action_review["review_state"], "failed")
        self.assertEqual(
            action_review["action_execution_state"],
            "failed",
        )
        self.assertEqual(
            action_review["next_expected_action"],
            "investigate_execution_failure",
        )

    def test_service_action_review_surfaces_use_newest_review_as_current(
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
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        rejected_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-rejected-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-current-rejected-001",
        )
        rejected_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-current-rejected-001",
                action_request_id=rejected_request.action_request_id,
                approver_identities=("approver-rejected-001",),
                target_snapshot=dict(rejected_request.target_scope),
                payload_hash=rejected_request.payload_hash,
                decided_at=rejected_request.requested_at + timedelta(minutes=5),
                lifecycle_state="rejected",
            )
        )
        rejected_request = service.persist_record(
            replace(
                rejected_request,
                approval_decision_id=rejected_decision.approval_decision_id,
                lifecycle_state="rejected",
            )
        )

        completed_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-002",
            recipient_identity="repo-owner-completed-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
            action_request_id="action-request-surface-current-completed-001",
        )
        completed_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-surface-current-completed-001",
                action_request_id=completed_request.action_request_id,
                approver_identities=("approver-completed-001",),
                target_snapshot=dict(completed_request.target_scope),
                payload_hash=completed_request.payload_hash,
                decided_at=completed_request.requested_at + timedelta(minutes=5),
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        completed_request = service.persist_record(
            replace(
                completed_request,
                approval_decision_id=completed_decision.approval_decision_id,
                lifecycle_state="completed",
            )
        )

        queue_snapshot = service.inspect_analyst_queue().to_dict()
        alert_snapshot = service.inspect_alert_detail(promoted_case.alert_id).to_dict()
        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()

        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["action_request_id"],
            completed_request.action_request_id,
        )
        self.assertEqual(
            queue_snapshot["records"][0]["current_action_review"]["review_state"],
            "completed",
        )
        self.assertEqual(
            alert_snapshot["current_action_review"]["action_request_id"],
            completed_request.action_request_id,
        )
        self.assertEqual(
            case_snapshot["current_action_review"]["action_request_id"],
            completed_request.action_request_id,
        )
        self.assertEqual(
            case_snapshot["action_reviews"][0]["action_request_id"],
            completed_request.action_request_id,
        )
        self.assertEqual(
            case_snapshot["action_reviews"][1]["action_request_id"],
            rejected_request.action_request_id,
        )

    def test_service_action_review_surfaces_find_cross_scope_replacement_requests(
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
        alert_scoped_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-superseded-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-surface-alert-superseded-001",
        )
        alert_scoped_request = service.persist_record(
            replace(
                alert_scoped_request,
                case_id=None,
                lifecycle_state="superseded",
            )
        )
        replacement_request = service.persist_record(
            replace(
                alert_scoped_request,
                action_request_id="action-request-surface-case-replacement-001",
                case_id=promoted_case.case_id,
                idempotency_key="idempotency-surface-case-replacement-001",
                requested_at=alert_scoped_request.requested_at + timedelta(minutes=15),
                lifecycle_state="pending_approval",
                requester_identity="analyst-002",
            )
        )

        alert_snapshot = service.inspect_alert_detail(promoted_case.alert_id).to_dict()
        case_snapshot = service.inspect_case_detail(promoted_case.case_id).to_dict()
        action_reviews_by_id = {
            record["action_request_id"]: record for record in case_snapshot["action_reviews"]
        }

        self.assertEqual(
            case_snapshot["current_action_review"]["action_request_id"],
            replacement_request.action_request_id,
        )
        self.assertEqual(
            alert_snapshot["current_action_review"]["action_request_id"],
            replacement_request.action_request_id,
        )
        self.assertEqual(
            action_reviews_by_id[alert_scoped_request.action_request_id]["review_state"],
            "superseded",
        )
        self.assertEqual(
            action_reviews_by_id[alert_scoped_request.action_request_id][
                "replacement_action_request_id"
            ],
            replacement_request.action_request_id,
        )

    def test_approved_payload_binding_hash_normalizes_equivalent_datetime_offsets(
        self,
    ) -> None:
        scheduled_for_utc = datetime.now(timezone.utc) + timedelta(hours=4)
        scheduled_for_plus_two = scheduled_for_utc.astimezone(
            timezone(timedelta(hours=2))
        )

        binding_hash_utc = _approved_payload_binding_hash(
            target_scope={
                "asset_id": "critical-host-001",
                "scheduled_for": scheduled_for_utc,
            },
            approved_payload={
                "action_type": "disable_identity",
                "scheduled_for": scheduled_for_utc,
            },
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        binding_hash_plus_two = _approved_payload_binding_hash(
            target_scope={
                "asset_id": "critical-host-001",
                "scheduled_for": scheduled_for_plus_two,
            },
            approved_payload={
                "action_type": "disable_identity",
                "scheduled_for": scheduled_for_plus_two,
            },
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )

        self.assertEqual(binding_hash_plus_two, binding_hash_utc)

    def test_service_keeps_requester_identity_inside_reviewed_action_request_deduplication(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-002",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertNotEqual(second_request.action_request_id, first_request.action_request_id)
        self.assertEqual(first_request.requester_identity, "analyst-001")
        self.assertEqual(second_request.requester_identity, "analyst-002")
        self.assertNotEqual(second_request.idempotency_key, first_request.idempotency_key)
        persisted_by_requester = {
            record.requester_identity: record
            for record in store.list(ActionRequestRecord)
        }
        self.assertEqual(
            persisted_by_requester,
            {
                "analyst-001": first_request,
                "analyst-002": second_request,
            },
        )

    def test_service_rechecks_reviewed_action_request_context_inside_transaction(
        self,
    ) -> None:
        inner_store, _ = make_store()
        (
            _,
            base_service,
            promoted_case,
            evidence_id,
            reviewed_at,
        ) = self._build_phase19_in_scope_case(store=inner_store)
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = base_service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = base_service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        store = _TransactionMutationStore(
            inner=inner_store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(
                    transactional_store.get(
                        RecommendationRecord,
                        recommendation.recommendation_id,
                    ),
                    intended_outcome=(
                        "Execute an organization-wide response immediately without waiting "
                        "for approval."
                    ),
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "reviewed advisory context is not ready for approval-bound action requests",
        ):
            service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            )

        self.assertEqual(inner_store.list(ActionRequestRecord), ())
