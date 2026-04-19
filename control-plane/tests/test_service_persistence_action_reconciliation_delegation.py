from __future__ import annotations
# ruff: noqa: E402

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _service_persistence_support as support
from _service_persistence_support import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AegisOpsControlPlaneService,
    ApprovalDecisionRecord,
    RuntimeConfig,
    ServicePersistenceTestBase,
    SimpleNamespace,
    _CommitFailingStore,
    _TransactionMutationStore,
    _approved_binding_hash,
    _phase20_notify_identity_owner_payload,
    datetime,
    logging,
    make_store,
    mock,
    replace,
    timezone,
)

class ActionDelegationPolicyPersistenceTests(ServicePersistenceTestBase):
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

        def persist_record_with_finalization_failure(
            record: object,
            **kwargs: object,
        ) -> object:
            if (
                isinstance(record, support.ActionExecutionRecord)
                and record.lifecycle_state == "queued"
            ):
                raise RuntimeError("synthetic finalization failure")
            return original_persist_record(record, **kwargs)

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


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str,
) -> unittest.TestSuite:
    del loader, pattern
    return tests
