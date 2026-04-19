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
    ServicePersistenceTestBase,
)

class CreateTrackingTicketActionReconciliationPersistenceTests(ServicePersistenceTestBase):
    def test_service_delegates_approved_create_tracking_ticket_through_shuffle(
        self,
    ) -> None:
        store, _ = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 18, 1, 0, tzinfo=support.timezone.utc)
        delegated_at = support.datetime(2026, 4, 18, 1, 5, tzinfo=support.timezone.utc)
        approved_target_scope = {
            "case_id": "case-tracking-001",
            "alert_id": "alert-tracking-001",
            "finding_id": "finding-tracking-001",
            "coordination_reference_id": "coord-ref-create-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = support._phase26_create_tracking_ticket_payload(
            case_id="case-tracking-001",
            alert_id="alert-tracking-001",
            finding_id="finding-tracking-001",
            coordination_reference_id="coord-ref-create-001",
        )
        payload_hash = support._approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            support.ApprovalDecisionRecord(
                approval_decision_id="approval-create-ticket-001",
                action_request_id="action-request-create-ticket-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            support.ActionRequestRecord(
                action_request_id="action-request-create-ticket-001",
                approval_decision_id="approval-create-ticket-001",
                case_id="case-tracking-001",
                alert_id="alert-tracking-001",
                finding_id="finding-tracking-001",
                idempotency_key="idempotency-create-ticket-001",
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

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-create-ticket-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-create-ticket-001",),
        )

        self.assertEqual(execution.lifecycle_state, "queued")
        self.assertEqual(execution.execution_surface_type, "automation_substrate")
        self.assertEqual(execution.execution_surface_id, "shuffle")
        self.assertEqual(
            execution.approved_payload["action_type"],
            "create_tracking_ticket",
        )
        self.assertEqual(
            execution.provenance["downstream_binding"]["coordination_reference_id"],
            "coord-ref-create-001",
        )
        self.assertEqual(
            execution.provenance["downstream_binding"]["coordination_target_type"],
            "zammad",
        )
        self.assertTrue(
            execution.provenance["downstream_binding"][
                "external_receipt_id"
            ].startswith("shuffle-receipt-delegation-")
        )
        self.assertTrue(
            execution.provenance["downstream_binding"][
                "coordination_target_id"
            ].startswith("zammad-ticket-delegation-")
        )
        self.assertTrue(
            execution.provenance["downstream_binding"][
                "ticket_reference_url"
            ].startswith("https://tickets.example.test/#ticket/zammad-ticket-delegation-")
        )
    def test_service_fail_closes_when_create_tracking_ticket_receipt_omits_external_receipt_id(
        self,
    ) -> None:
        store, _ = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 18, 1, 0, tzinfo=support.timezone.utc)
        delegated_at = support.datetime(2026, 4, 18, 1, 5, tzinfo=support.timezone.utc)
        approved_target_scope = {
            "case_id": "case-tracking-omit-receipt-001",
            "alert_id": "alert-tracking-omit-receipt-001",
            "finding_id": "finding-tracking-omit-receipt-001",
            "coordination_reference_id": "coord-ref-omit-receipt-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = support._phase26_create_tracking_ticket_payload(
            case_id="case-tracking-omit-receipt-001",
            alert_id="alert-tracking-omit-receipt-001",
            finding_id="finding-tracking-omit-receipt-001",
            coordination_reference_id="coord-ref-omit-receipt-001",
        )
        payload_hash = support._approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            support.ApprovalDecisionRecord(
                approval_decision_id="approval-create-ticket-omit-receipt-001",
                action_request_id="action-request-create-ticket-omit-receipt-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            support.ActionRequestRecord(
                action_request_id="action-request-create-ticket-omit-receipt-001",
                approval_decision_id="approval-create-ticket-omit-receipt-001",
                case_id="case-tracking-omit-receipt-001",
                alert_id="alert-tracking-omit-receipt-001",
                finding_id="finding-tracking-omit-receipt-001",
                idempotency_key="idempotency-create-ticket-omit-receipt-001",
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

        def dispatch_without_external_receipt_id(adapter: object, **kwargs: object) -> object:
            receipt = original_dispatch(adapter, **kwargs)
            return support.replace(receipt, external_receipt_id="")

        with support.mock.patch.object(
            type(service._shuffle),
            "dispatch_approved_action",
            autospec=True,
            side_effect=dispatch_without_external_receipt_id,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "adapter receipt missing required 'external_receipt_id' attribute",
            ):
                service.delegate_approved_action_to_shuffle(
                    action_request_id="action-request-create-ticket-omit-receipt-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(support.ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error"],
            "adapter receipt missing required 'external_receipt_id' attribute",
        )
    def test_service_fail_closes_when_create_tracking_ticket_receipt_binding_drifts(
        self,
    ) -> None:
        store, _ = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 18, 2, 0, tzinfo=support.timezone.utc)
        delegated_at = support.datetime(2026, 4, 18, 2, 5, tzinfo=support.timezone.utc)
        approved_target_scope = {
            "case_id": "case-tracking-receipt-drift-001",
            "alert_id": "alert-tracking-receipt-drift-001",
            "finding_id": "finding-tracking-receipt-drift-001",
            "coordination_reference_id": "coord-ref-receipt-drift-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = support._phase26_create_tracking_ticket_payload(
            case_id="case-tracking-receipt-drift-001",
            alert_id="alert-tracking-receipt-drift-001",
            finding_id="finding-tracking-receipt-drift-001",
            coordination_reference_id="coord-ref-receipt-drift-001",
        )
        payload_hash = support._approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            support.ApprovalDecisionRecord(
                approval_decision_id="approval-create-ticket-receipt-drift-001",
                action_request_id="action-request-create-ticket-receipt-drift-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            support.ActionRequestRecord(
                action_request_id="action-request-create-ticket-receipt-drift-001",
                approval_decision_id="approval-create-ticket-receipt-drift-001",
                case_id="case-tracking-receipt-drift-001",
                alert_id="alert-tracking-receipt-drift-001",
                finding_id="finding-tracking-receipt-drift-001",
                idempotency_key="idempotency-create-ticket-receipt-drift-001",
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

        def dispatch_with_drifted_coordination_reference(
            adapter: object,
            **kwargs: object,
        ) -> object:
            receipt = original_dispatch(adapter, **kwargs)
            return support.replace(
                receipt,
                coordination_reference_id="coord-ref-drifted-999",
            )

        with support.mock.patch.object(
            type(service._shuffle),
            "dispatch_approved_action",
            autospec=True,
            side_effect=dispatch_with_drifted_coordination_reference,
        ):
            with self.assertRaisesRegex(
                ValueError,
                "shuffle receipt does not match approved delegation binding",
            ):
                service.delegate_approved_action_to_shuffle(
                    action_request_id="action-request-create-ticket-receipt-drift-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(support.ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error"],
            "shuffle receipt does not match approved delegation binding",
        )
    def test_service_fail_closes_when_create_tracking_ticket_dispatch_times_out(
        self,
    ) -> None:
        store, _ = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 18, 3, 0, tzinfo=support.timezone.utc)
        delegated_at = support.datetime(2026, 4, 18, 3, 5, tzinfo=support.timezone.utc)
        approved_target_scope = {
            "case_id": "case-tracking-timeout-001",
            "alert_id": "alert-tracking-timeout-001",
            "finding_id": "finding-tracking-timeout-001",
            "coordination_reference_id": "coord-ref-timeout-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = support._phase26_create_tracking_ticket_payload(
            case_id="case-tracking-timeout-001",
            alert_id="alert-tracking-timeout-001",
            finding_id="finding-tracking-timeout-001",
            coordination_reference_id="coord-ref-timeout-001",
        )
        payload_hash = support._approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            support.ApprovalDecisionRecord(
                approval_decision_id="approval-create-ticket-timeout-001",
                action_request_id="action-request-create-ticket-timeout-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            support.ActionRequestRecord(
                action_request_id="action-request-create-ticket-timeout-001",
                approval_decision_id="approval-create-ticket-timeout-001",
                case_id="case-tracking-timeout-001",
                alert_id="alert-tracking-timeout-001",
                finding_id="finding-tracking-timeout-001",
                idempotency_key="idempotency-create-ticket-timeout-001",
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

        with support.mock.patch.object(
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
                    action_request_id="action-request-create-ticket-timeout-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        executions = store.list(support.ActionExecutionRecord)
        self.assertEqual(len(executions), 1)
        self.assertEqual(executions[0].lifecycle_state, "failed")
        self.assertEqual(
            executions[0].provenance["dispatch_failure"]["error_type"],
            "TimeoutError",
        )
    def test_service_reconciles_create_tracking_ticket_receipt_into_authoritative_records(
        self,
    ) -> None:
        store, _ = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 18, 4, 0, tzinfo=support.timezone.utc)
        delegated_at = support.datetime(2026, 4, 18, 4, 5, tzinfo=support.timezone.utc)
        compared_at = support.datetime(2026, 4, 18, 4, 10, tzinfo=support.timezone.utc)
        approved_target_scope = {
            "case_id": "case-tracking-reconcile-001",
            "alert_id": "alert-tracking-reconcile-001",
            "finding_id": "finding-tracking-reconcile-001",
            "coordination_reference_id": "coord-ref-reconcile-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = support._phase26_create_tracking_ticket_payload(
            case_id="case-tracking-reconcile-001",
            alert_id="alert-tracking-reconcile-001",
            finding_id="finding-tracking-reconcile-001",
            coordination_reference_id="coord-ref-reconcile-001",
        )
        payload_hash = support._approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            support.ApprovalDecisionRecord(
                approval_decision_id="approval-create-ticket-reconcile-001",
                action_request_id="action-request-create-ticket-reconcile-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            support.ActionRequestRecord(
                action_request_id="action-request-create-ticket-reconcile-001",
                approval_decision_id="approval-create-ticket-reconcile-001",
                case_id="case-tracking-reconcile-001",
                alert_id="alert-tracking-reconcile-001",
                finding_id="finding-tracking-reconcile-001",
                idempotency_key="idempotency-create-ticket-reconcile-001",
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

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-create-ticket-reconcile-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-create-ticket-reconcile-001",),
        )
        downstream_binding = execution.provenance["downstream_binding"]

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-create-ticket-reconcile-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-create-ticket-reconcile-001",
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
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
            stale_after=support.datetime(
                2026,
                4,
                18,
                4,
                30,
                tzinfo=support.timezone.utc,
            ),
        )

        stored_execution = service.get_record(
            support.ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(stored_execution.lifecycle_state, "succeeded")
        self.assertEqual(
            reconciliation.subject_linkage["coordination_reference_ids"],
            ("coord-ref-reconcile-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["coordination_target_types"],
            ("zammad",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["external_receipt_ids"],
            (downstream_binding["external_receipt_id"],),
        )
        self.assertEqual(
            reconciliation.subject_linkage["coordination_target_ids"],
            (downstream_binding["coordination_target_id"],),
        )
        self.assertEqual(
            reconciliation.subject_linkage["ticket_reference_urls"],
            (downstream_binding["ticket_reference_url"],),
        )
    def test_service_fail_closes_when_create_tracking_ticket_reconciliation_receipt_drifts(
        self,
    ) -> None:
        store, _ = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 18, 4, 12, tzinfo=support.timezone.utc)
        delegated_at = support.datetime(2026, 4, 18, 4, 17, tzinfo=support.timezone.utc)
        compared_at = support.datetime(2026, 4, 18, 4, 22, tzinfo=support.timezone.utc)
        approved_target_scope = {
            "case_id": "case-tracking-reconcile-drift-001",
            "alert_id": "alert-tracking-reconcile-drift-001",
            "finding_id": "finding-tracking-reconcile-drift-001",
            "coordination_reference_id": "coord-ref-reconcile-drift-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = support._phase26_create_tracking_ticket_payload(
            case_id="case-tracking-reconcile-drift-001",
            alert_id="alert-tracking-reconcile-drift-001",
            finding_id="finding-tracking-reconcile-drift-001",
            coordination_reference_id="coord-ref-reconcile-drift-001",
        )
        payload_hash = support._approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            support.ApprovalDecisionRecord(
                approval_decision_id="approval-create-ticket-reconcile-drift-001",
                action_request_id="action-request-create-ticket-reconcile-drift-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            support.ActionRequestRecord(
                action_request_id="action-request-create-ticket-reconcile-drift-001",
                approval_decision_id="approval-create-ticket-reconcile-drift-001",
                case_id="case-tracking-reconcile-drift-001",
                alert_id="alert-tracking-reconcile-drift-001",
                finding_id="finding-tracking-reconcile-drift-001",
                idempotency_key="idempotency-create-ticket-reconcile-drift-001",
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

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-create-ticket-reconcile-drift-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-create-ticket-reconcile-drift-001",),
        )
        downstream_binding = execution.provenance["downstream_binding"]

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-create-ticket-reconcile-drift-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-create-ticket-reconcile-drift-001",
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": "shuffle-receipt-drifted-001",
                    "coordination_target_id": downstream_binding[
                        "coordination_target_id"
                    ],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=support.datetime(
                2026,
                4,
                18,
                4,
                45,
                tzinfo=support.timezone.utc,
            ),
        )

        stored_execution = service.get_record(
            support.ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(
            reconciliation.mismatch_summary,
            "coordination receipt mismatch between authoritative action execution "
            "and observed downstream execution",
        )
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(
            reconciliation.subject_linkage["external_receipt_ids"],
            (downstream_binding["external_receipt_id"],),
        )
    def test_service_fail_closes_when_create_tracking_ticket_receipt_has_no_authoritative_execution(
        self,
    ) -> None:
        store, backend = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 18, 4, 20, tzinfo=support.timezone.utc)
        delegated_at = support.datetime(2026, 4, 18, 4, 25, tzinfo=support.timezone.utc)
        compared_at = support.datetime(2026, 4, 18, 4, 30, tzinfo=support.timezone.utc)
        approved_target_scope = {
            "case_id": "case-tracking-missing-authoritative-001",
            "alert_id": "alert-tracking-missing-authoritative-001",
            "finding_id": "finding-tracking-missing-authoritative-001",
            "coordination_reference_id": "coord-ref-missing-authoritative-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = support._phase26_create_tracking_ticket_payload(
            case_id="case-tracking-missing-authoritative-001",
            alert_id="alert-tracking-missing-authoritative-001",
            finding_id="finding-tracking-missing-authoritative-001",
            coordination_reference_id="coord-ref-missing-authoritative-001",
        )
        payload_hash = support._approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            support.ApprovalDecisionRecord(
                approval_decision_id="approval-create-ticket-missing-authoritative-001",
                action_request_id="action-request-create-ticket-missing-authoritative-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            support.ActionRequestRecord(
                action_request_id="action-request-create-ticket-missing-authoritative-001",
                approval_decision_id="approval-create-ticket-missing-authoritative-001",
                case_id="case-tracking-missing-authoritative-001",
                alert_id="alert-tracking-missing-authoritative-001",
                finding_id="finding-tracking-missing-authoritative-001",
                idempotency_key="idempotency-create-ticket-missing-authoritative-001",
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

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-create-ticket-missing-authoritative-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
        )
        backend.tables["action_execution_records"].pop(execution.action_execution_id)

        downstream_binding = execution.provenance["downstream_binding"]
        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-create-ticket-missing-authoritative-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-create-ticket-missing-authoritative-001",
                    "observed_at": compared_at,
                    "approval_decision_id": "approval-create-ticket-missing-authoritative-001",
                    "delegation_id": execution.delegation_id,
                    "payload_hash": payload_hash,
                    "coordination_reference_id": downstream_binding[
                        "coordination_reference_id"
                    ],
                    "coordination_target_type": downstream_binding[
                        "coordination_target_type"
                    ],
                    "external_receipt_id": downstream_binding["external_receipt_id"],
                    "coordination_target_id": downstream_binding["coordination_target_id"],
                    "ticket_reference_url": downstream_binding["ticket_reference_url"],
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=support.datetime(
                2026,
                4,
                18,
                4,
                45,
                tzinfo=support.timezone.utc,
            ),
        )

        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(
            reconciliation.mismatch_summary,
            "coordination receipt mismatch between authoritative action execution "
            "and observed downstream execution",
        )
    def test_service_rejects_blank_create_tracking_ticket_receipt_identifiers(
        self,
    ) -> None:
        store, _ = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 18, 4, 40, tzinfo=support.timezone.utc)
        approved_target_scope = {
            "case_id": "case-tracking-blank-receipt-001",
            "alert_id": "alert-tracking-blank-receipt-001",
            "finding_id": "finding-tracking-blank-receipt-001",
            "coordination_reference_id": "coord-ref-blank-receipt-001",
            "coordination_target_type": "zammad",
        }
        approved_payload = support._phase26_create_tracking_ticket_payload(
            case_id="case-tracking-blank-receipt-001",
            alert_id="alert-tracking-blank-receipt-001",
            finding_id="finding-tracking-blank-receipt-001",
            coordination_reference_id="coord-ref-blank-receipt-001",
        )
        payload_hash = support._approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            support.ApprovalDecisionRecord(
                approval_decision_id="approval-create-ticket-blank-receipt-001",
                action_request_id="action-request-create-ticket-blank-receipt-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            support.ActionRequestRecord(
                action_request_id="action-request-create-ticket-blank-receipt-001",
                approval_decision_id="approval-create-ticket-blank-receipt-001",
                case_id="case-tracking-blank-receipt-001",
                alert_id="alert-tracking-blank-receipt-001",
                finding_id="finding-tracking-blank-receipt-001",
                idempotency_key="idempotency-create-ticket-blank-receipt-001",
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

        with self.assertRaisesRegex(
            ValueError,
            "observed execution must include string external_receipt_id",
        ):
            service.reconcile_action_execution(
                action_request_id="action-request-create-ticket-blank-receipt-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=(
                    {
                        "execution_run_id": "shuffle-run-blank-receipt-001",
                        "execution_surface_id": "shuffle",
                        "idempotency_key": "idempotency-create-ticket-blank-receipt-001",
                        "observed_at": support.datetime(
                            2026,
                            4,
                            18,
                            4,
                            45,
                            tzinfo=support.timezone.utc,
                        ),
                        "approval_decision_id": "approval-create-ticket-blank-receipt-001",
                        "delegation_id": "delegation-blank-receipt-001",
                        "payload_hash": payload_hash,
                        "coordination_reference_id": "coord-ref-blank-receipt-001",
                        "coordination_target_type": "zammad",
                        "external_receipt_id": "   ",
                        "coordination_target_id": "zammad-ticket-blank-receipt-001",
                        "ticket_reference_url": "https://tickets.example.test/#ticket/zammad-ticket-blank-receipt-001",
                        "status": "success",
                    },
                ),
                compared_at=support.datetime(
                    2026,
                    4,
                    18,
                    4,
                    45,
                    tzinfo=support.timezone.utc,
                ),
                stale_after=support.datetime(
                    2026,
                    4,
                    18,
                    5,
                    0,
                    tzinfo=support.timezone.utc,
                ),
            )
    def test_service_records_execution_correlation_mismatch_states_separately(self) -> None:
        store, _ = support.make_store()
        service = support.AegisOpsControlPlaneService(
            support.RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        requested_at = support.datetime(2026, 4, 5, 12, 0, tzinfo=support.timezone.utc)
        stale_cutoff = support.datetime(
            2026, 4, 5, 12, 30, tzinfo=support.timezone.utc
        )
        action_request = support.ActionRequestRecord(
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
                    "observed_at": support.datetime(
                        2026, 4, 5, 12, 5, tzinfo=support.timezone.utc
                    ),
                    "status": "running",
                },
                {
                    "execution_run_id": "exec-002",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": support.datetime(
                        2026, 4, 5, 12, 6, tzinfo=support.timezone.utc
                    ),
                    "status": "running",
                },
            ),
            compared_at=support.datetime(
                2026, 4, 5, 12, 6, tzinfo=support.timezone.utc
            ),
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
                    "observed_at": support.datetime(
                        2026, 4, 5, 12, 10, tzinfo=support.timezone.utc
                    ),
                    "status": "failed",
                },
            ),
            compared_at=support.datetime(
                2026, 4, 5, 12, 10, tzinfo=support.timezone.utc
            ),
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
                    "observed_at": support.datetime(
                        2026, 4, 5, 12, 20, tzinfo=support.timezone.utc
                    ),
                    "status": "success",
                },
            ),
            compared_at=support.datetime(
                2026, 4, 5, 12, 45, tzinfo=support.timezone.utc
            ),
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

        stored_reconciliations = store.list(support.ReconciliationRecord)
        self.assertEqual(len(stored_reconciliations), 4)
        self.assertEqual(
            sorted(record.ingest_disposition for record in stored_reconciliations),
            ["duplicate", "mismatch", "missing", "stale"],
        )
        self.assertEqual(
            service.get_record(support.ActionRequestRecord, "action-request-001"),
            action_request,
        )


def load_tests(
    loader: unittest.TestLoader,
    tests: unittest.TestSuite,
    pattern: str,
) -> unittest.TestSuite:
    del loader, pattern
    return tests
