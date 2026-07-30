from __future__ import annotations
# ruff: noqa: E402

import pathlib
import sys
import unittest
from dataclasses import replace

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from _service_persistence_support import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AegisOpsControlPlaneService,
    ApprovalDecisionRecord,
    ReconciliationRecord,
    RuntimeConfig,
    ServicePersistenceTestBase,
    _approved_binding_hash,
    _phase20_notify_identity_owner_payload,
    datetime,
    make_store,
    timezone,
)

class ActionExecutionReconciliationPersistenceTests(ServicePersistenceTestBase):
    def _build_phase67_failed_shuffle_context(
        self,
    ) -> tuple[
        object,
        AegisOpsControlPlaneService,
        ActionExecutionRecord,
        dict[str, str],
    ]:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 7, 29, 1, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 7, 29, 1, 5, tzinfo=timezone.utc)
        target_scope = {
            "recipient_identity": "local-test-sink",
            "risk": 1,
        }
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="local-test-sink",
            case_id="case-phase67-failed-001",
            alert_id="alert-phase67-failed-001",
            finding_id="finding-phase67-failed-001",
        )
        approved_payload["shuffle_delegation_binding"] = {
            "workflow_id": "notify_identity_owner",
            "workflow_version_id": "notify_identity_owner-v1-reviewed-2026-05-03",
            "correlation_id": "phase67-failed-correlation-001",
            "expected_execution_receipt_id": "phase67-failed-receipt-001",
            "requested_scope": target_scope,
        }
        payload_hash = _approved_binding_hash(
            target_scope=target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="phase67-failed-approval-001",
                action_request_id="phase67-failed-action-001",
                approver_identities=("phase67-lab-operator",),
                target_snapshot=target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="phase67-failed-action-001",
                approval_decision_id="phase67-failed-approval-001",
                case_id="case-phase67-failed-001",
                alert_id="alert-phase67-failed-001",
                finding_id="finding-phase67-failed-001",
                idempotency_key="phase67-failed-idempotency-001",
                target_scope=target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                requested_payload=approved_payload,
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="phase67-failed-action-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="phase67-lab-operator",
        )
        return store, service, execution, target_scope

    def test_phase67_failed_shuffle_receipt_remains_unresolved_and_idempotent(
        self,
    ) -> None:
        store, service, execution, target_scope = (
            self._build_phase67_failed_shuffle_context()
        )
        downstream_binding = execution.provenance["downstream_binding"]
        observed_at = datetime(2026, 7, 29, 1, 12, tzinfo=timezone.utc)
        failed_receipt = (
            {
                "execution_run_id": execution.execution_run_id,
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
                "idempotency_key": execution.idempotency_key,
                "approval_decision_id": execution.approval_decision_id,
                "delegation_id": execution.delegation_id,
                "payload_hash": execution.payload_hash,
                "action_request_id": execution.action_request_id,
                "workflow_id": downstream_binding["workflow_id"],
                "workflow_version_id": downstream_binding["workflow_version_id"],
                "correlation_id": downstream_binding["correlation_id"],
                "expected_execution_receipt_id": downstream_binding[
                    "expected_execution_receipt_id"
                ],
                "external_receipt_id": downstream_binding[
                    "expected_execution_receipt_id"
                ],
                "requested_scope": target_scope,
                "idempotency_execution_count": 1,
                "observed_at": observed_at,
                "status": " ERROR ",
            },
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id=execution.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=failed_receipt,
            compared_at=observed_at,
            stale_after=datetime(2026, 7, 29, 1, 30, tzinfo=timezone.utc),
        )
        replay = service.reconcile_action_execution(
            action_request_id=execution.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=failed_receipt,
            compared_at=datetime(2026, 7, 29, 1, 13, tzinfo=timezone.utc),
            stale_after=datetime(2026, 7, 29, 1, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertIn("requires operator review", reconciliation.mismatch_summary)
        self.assertEqual(stored_execution.lifecycle_state, "failed")
        self.assertEqual(
            stored_execution.provenance["normalized_receipt"]["requested_scope"],
            target_scope,
        )
        self.assertEqual(
            stored_execution.provenance["normalized_receipt"][
                "idempotency_execution_count"
            ],
            1,
        )
        self.assertEqual(replay.reconciliation_id, reconciliation.reconciliation_id)
        self.assertEqual(len(store.list(ReconciliationRecord)), 1)

    def test_phase67_canceled_shuffle_receipt_remains_unresolved(self) -> None:
        store, service, execution, target_scope = (
            self._build_phase67_failed_shuffle_context()
        )
        downstream_binding = execution.provenance["downstream_binding"]
        observed_at = datetime(2026, 7, 29, 1, 12, tzinfo=timezone.utc)
        canceled_receipt = (
            {
                "execution_run_id": execution.execution_run_id,
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
                "idempotency_key": execution.idempotency_key,
                "approval_decision_id": execution.approval_decision_id,
                "delegation_id": execution.delegation_id,
                "payload_hash": execution.payload_hash,
                "action_request_id": execution.action_request_id,
                "workflow_id": downstream_binding["workflow_id"],
                "workflow_version_id": downstream_binding[
                    "workflow_version_id"
                ],
                "correlation_id": downstream_binding["correlation_id"],
                "expected_execution_receipt_id": downstream_binding[
                    "expected_execution_receipt_id"
                ],
                "external_receipt_id": downstream_binding[
                    "expected_execution_receipt_id"
                ],
                "requested_scope": target_scope,
                "idempotency_execution_count": 1,
                "observed_at": observed_at,
                "status": " CANCELLED ",
            },
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id=execution.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=canceled_receipt,
            compared_at=observed_at,
            stale_after=datetime(2026, 7, 29, 1, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertIn("requires operator review", reconciliation.mismatch_summary)
        self.assertEqual(stored_execution.lifecycle_state, "canceled")
        self.assertEqual(len(store.list(ReconciliationRecord)), 1)

    def test_phase67_unrecognized_shuffle_receipt_status_remains_unresolved(
        self,
    ) -> None:
        for status in (None, "", "TIMED_OUT"):
            with self.subTest(status=status):
                store, service, execution, target_scope = (
                    self._build_phase67_failed_shuffle_context()
                )
                downstream_binding = execution.provenance["downstream_binding"]
                observed_at = datetime(
                    2026,
                    7,
                    29,
                    1,
                    12,
                    tzinfo=timezone.utc,
                )
                receipt = {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                    "idempotency_key": execution.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "action_request_id": execution.action_request_id,
                    "workflow_id": downstream_binding["workflow_id"],
                    "workflow_version_id": downstream_binding[
                        "workflow_version_id"
                    ],
                    "correlation_id": downstream_binding["correlation_id"],
                    "expected_execution_receipt_id": downstream_binding[
                        "expected_execution_receipt_id"
                    ],
                    "external_receipt_id": downstream_binding[
                        "expected_execution_receipt_id"
                    ],
                    "requested_scope": target_scope,
                    "idempotency_execution_count": 1,
                    "observed_at": observed_at,
                }
                if status is not None:
                    receipt["status"] = status

                reconciliation = service.reconcile_action_execution(
                    action_request_id=execution.action_request_id,
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    observed_executions=(receipt,),
                    compared_at=observed_at,
                    stale_after=datetime(
                        2026,
                        7,
                        29,
                        1,
                        30,
                        tzinfo=timezone.utc,
                    ),
                )

                stored_execution = service.get_record(
                    ActionExecutionRecord,
                    execution.action_execution_id,
                )
                self.assertEqual(
                    reconciliation.ingest_disposition,
                    "mismatch",
                )
                self.assertEqual(
                    reconciliation.lifecycle_state,
                    "mismatched",
                )
                self.assertIn(
                    "unrecognized downstream execution status",
                    reconciliation.mismatch_summary,
                )
                self.assertEqual(stored_execution.lifecycle_state, "queued")
                self.assertEqual(len(store.list(ReconciliationRecord)), 1)

    def test_phase67_real_shuffle_receipt_requires_exact_scope_and_single_execution(
        self,
    ) -> None:
        store, service, execution, target_scope = (
            self._build_phase67_failed_shuffle_context()
        )
        execution = store.save(
            replace(
                execution,
                provenance={
                    **execution.provenance,
                    "adapter": "shuffle_real_http",
                },
            )
        )
        downstream_binding = execution.provenance["downstream_binding"]
        observed_at = datetime(2026, 7, 29, 1, 12, tzinfo=timezone.utc)
        receipt = {
            "execution_run_id": execution.execution_run_id,
            "execution_surface_type": "automation_substrate",
            "execution_surface_id": "shuffle",
            "idempotency_key": execution.idempotency_key,
            "approval_decision_id": execution.approval_decision_id,
            "delegation_id": execution.delegation_id,
            "payload_hash": execution.payload_hash,
            "action_request_id": execution.action_request_id,
            "workflow_id": downstream_binding["workflow_id"],
            "workflow_version_id": downstream_binding["workflow_version_id"],
            "correlation_id": downstream_binding["correlation_id"],
            "expected_execution_receipt_id": downstream_binding[
                "expected_execution_receipt_id"
            ],
            "external_receipt_id": downstream_binding[
                "expected_execution_receipt_id"
            ],
            "requested_scope": target_scope,
            "observed_at": observed_at,
            "status": "success",
        }

        missing_count = service.reconcile_action_execution(
            action_request_id=execution.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(receipt,),
            compared_at=observed_at,
            stale_after=datetime(2026, 7, 29, 1, 30, tzinfo=timezone.utc),
        )
        receipt["idempotency_execution_count"] = 1
        receipt["requested_scope"] = {"recipient_identity": "other-test-sink"}
        mismatched_scope = service.reconcile_action_execution(
            action_request_id=execution.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(receipt,),
            compared_at=datetime(2026, 7, 29, 1, 13, tzinfo=timezone.utc),
            stale_after=datetime(2026, 7, 29, 1, 30, tzinfo=timezone.utc),
        )
        receipt["requested_scope"] = {
            "recipient_identity": "local-test-sink",
            "risk": True,
        }
        type_drifted_scope = service.reconcile_action_execution(
            action_request_id=execution.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(receipt,),
            compared_at=datetime(2026, 7, 29, 1, 13, 30, tzinfo=timezone.utc),
            stale_after=datetime(2026, 7, 29, 1, 30, tzinfo=timezone.utc),
        )
        receipt["requested_scope"] = target_scope
        for malformed_count in (True, 1.0):
            with self.subTest(idempotency_execution_count=malformed_count):
                receipt["idempotency_execution_count"] = malformed_count
                with self.assertRaisesRegex(ValueError, "must be integer one"):
                    service.reconcile_action_execution(
                        action_request_id=execution.action_request_id,
                        execution_surface_type="automation_substrate",
                        execution_surface_id="shuffle",
                        observed_executions=(receipt,),
                        compared_at=datetime(
                            2026,
                            7,
                            29,
                            1,
                            14,
                            tzinfo=timezone.utc,
                        ),
                        stale_after=datetime(
                            2026,
                            7,
                            29,
                            1,
                            30,
                            tzinfo=timezone.utc,
                        ),
                    )

        receipt["idempotency_execution_count"] = 1
        receipt["requested_scope"] = target_scope
        external_receipt_mismatches = []
        for index, external_receipt_id in enumerate(
            (None, "different-external-receipt"),
            start=1,
        ):
            if external_receipt_id is None:
                receipt.pop("external_receipt_id", None)
            else:
                receipt["external_receipt_id"] = external_receipt_id
            external_receipt_mismatches.append(
                service.reconcile_action_execution(
                    action_request_id=execution.action_request_id,
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    observed_executions=(receipt,),
                    compared_at=datetime(
                        2026,
                        7,
                        29,
                        1,
                        15 + index,
                        tzinfo=timezone.utc,
                    ),
                    stale_after=datetime(
                        2026,
                        7,
                        29,
                        1,
                        30,
                        tzinfo=timezone.utc,
                    ),
                )
            )

        self.assertEqual(missing_count.ingest_disposition, "mismatch")
        self.assertEqual(mismatched_scope.ingest_disposition, "mismatch")
        self.assertEqual(type_drifted_scope.ingest_disposition, "mismatch")
        self.assertEqual(
            [
                reconciliation.ingest_disposition
                for reconciliation in external_receipt_mismatches
            ],
            ["mismatch", "mismatch"],
        )
        self.assertNotIn("normalized_receipt", execution.provenance)
        self.assertEqual(len(store.list(ReconciliationRecord)), 5)

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
                        "execution_surface_type": "automation_substrate",
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
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_type": "automation_substrate",
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
                    "execution_surface_type": "executor",
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

    def test_service_reconcile_action_execution_treats_surface_type_drift_as_mismatch(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-surface-type-drift-001",
            approval_decision_id="approval-surface-type-drift-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-surface-type-drift-001",
            idempotency_key="idempotency-surface-type-drift-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-surface-type-drift-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        execution_surface_id = "n8n"
        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-surface-type-drift-001",
            execution_surface_type="automation_substrate",
            execution_surface_id=execution_surface_id,
            observed_executions=(
                {
                    "execution_run_id": "exec-surface-type-drift-001",
                    "execution_surface_type": "executor",
                    "execution_surface_id": execution_surface_id,
                    "idempotency_key": "idempotency-surface-type-drift-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(
            reconciliation.mismatch_summary,
            "execution surface/idempotency mismatch between approved request and observed execution",
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
        approved_payload["shuffle_delegation_binding"] = {
            "workflow_id": "notify_identity_owner",
            "workflow_version_id": "notify_identity_owner-v1-reviewed-2026-05-03",
            "correlation_id": "shuffle-correlation-notify-reconcile-001",
            "expected_execution_receipt_id": "shuffle-receipt-notify-reconcile-001",
            "requested_scope": approved_target_scope,
        }
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
                requested_payload=approved_payload,
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
        downstream_binding = execution.provenance["downstream_binding"]

        observed_receipt = (
            {
                "execution_run_id": execution.execution_run_id,
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
                "idempotency_key": "idempotency-routine-reconcile-001",
                "approval_decision_id": execution.approval_decision_id,
                "delegation_id": execution.delegation_id,
                "payload_hash": execution.payload_hash,
                "action_request_id": execution.action_request_id,
                "workflow_id": downstream_binding["workflow_id"],
                "workflow_version_id": downstream_binding["workflow_version_id"],
                "correlation_id": downstream_binding["correlation_id"],
                "expected_execution_receipt_id": downstream_binding[
                    "expected_execution_receipt_id"
                ],
                "external_receipt_id": downstream_binding[
                    "expected_execution_receipt_id"
                ],
                "requested_scope": downstream_binding["requested_scope"],
                "observed_at": compared_at,
                "status": "success",
            },
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-routine-reconcile-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=observed_receipt,
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )
        replay = service.reconcile_action_execution(
            action_request_id="action-request-routine-reconcile-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=observed_receipt,
            compared_at=datetime(2026, 4, 5, 12, 13, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "succeeded")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)
        self.assertEqual(replay.reconciliation_id, reconciliation.reconciliation_id)
        self.assertEqual(
            len(store.list(ReconciliationRecord)),
            1,
        )
        self.assertEqual(
            stored_execution.provenance["normalized_receipt"]["requested_scope"],
            approved_target_scope,
        )
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
            reconciliation.subject_linkage["workflow_ids"],
            ("notify_identity_owner",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["workflow_version_ids"],
            ("notify_identity_owner-v1-reviewed-2026-05-03",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["correlation_ids"],
            ("shuffle-correlation-notify-reconcile-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["expected_execution_receipt_ids"],
            ("shuffle-receipt-notify-reconcile-001",),
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
                    "execution_surface_type": "executor",
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
        self.assertNotIn("normalized_receipt", stored_execution.provenance)
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
                    "execution_surface_type": "automation_substrate",
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
                    "execution_surface_type": "automation_substrate",
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


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str,
) -> unittest.TestSuite:
    del loader, pattern
    return tests
