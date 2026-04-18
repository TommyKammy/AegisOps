from __future__ import annotations

from dataclasses import replace
from datetime import timedelta, timezone
import io
import json
import pathlib
import sys
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import main
import test_cli_inspection as cli_inspection_tests


class Phase26EndToEndValidationTests(unittest.TestCase):
    def _helpers(self) -> cli_inspection_tests.ControlPlaneCliInspectionTests:
        return cli_inspection_tests.ControlPlaneCliInspectionTests()

    def _inspect_case_detail(
        self,
        *,
        service: cli_inspection_tests.AegisOpsControlPlaneService,
        case_id: str,
    ) -> dict[str, object]:
        stdout = io.StringIO()
        main.main(
            ["inspect-case-detail", "--case-id", case_id],
            stdout=stdout,
            service=service,
        )
        return json.loads(stdout.getvalue())

    def test_phase26_end_to_end_surfaces_link_first_ticket_reference_without_authority_drift(
        self,
    ) -> None:
        helpers = self._helpers()
        _, service, promoted_case, _evidence_id, _reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        service.persist_record(
            replace(
                service.get_record(
                    cli_inspection_tests.AlertRecord, promoted_case.alert_id
                ),
                coordination_reference_id="coord-ref-phase26-link-first-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                service.get_record(
                    cli_inspection_tests.CaseRecord, promoted_case.case_id
                ),
                coordination_reference_id="coord-ref-phase26-link-first-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )

        payload = self._inspect_case_detail(service=service, case_id=promoted_case.case_id)
        external_ticket_reference = payload["external_ticket_reference"]

        self.assertEqual(external_ticket_reference["authority"], "non_authoritative")
        self.assertEqual(external_ticket_reference["status"], "present")
        self.assertEqual(
            external_ticket_reference["coordination_reference_id"],
            "coord-ref-phase26-link-first-001",
        )
        self.assertEqual(
            external_ticket_reference["coordination_target_type"],
            "zammad",
        )
        self.assertEqual(
            external_ticket_reference["coordination_target_id"],
            "ZM-4242",
        )
        self.assertEqual(
            external_ticket_reference["ticket_reference_url"],
            "https://tickets.example.test/#ticket/4242",
        )
        self.assertIsNone(payload["current_action_review"])

    def test_phase26_end_to_end_surfaces_create_tracking_ticket_created_outcome(
        self,
    ) -> None:
        helpers = self._helpers()
        store, service, promoted_case, _evidence_id, reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = helpers._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="phase26-created-001",
            coordination_reference_id="coord-ref-phase26-created-001",
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

        payload = self._inspect_case_detail(service=service, case_id=promoted_case.case_id)
        outcome = payload["current_action_review"]["coordination_ticket_outcome"]

        self.assertEqual(outcome["status"], "created")
        self.assertEqual(
            outcome["coordination_reference_id"],
            "coord-ref-phase26-created-001",
        )
        self.assertEqual(outcome["coordination_target_type"], "zammad")
        self.assertEqual(
            outcome["external_receipt_id"],
            downstream_binding["external_receipt_id"],
        )
        self.assertEqual(
            outcome["ticket_reference_url"],
            downstream_binding["ticket_reference_url"],
        )

    def test_phase26_end_to_end_fail_closes_missing_receipt_before_user_facing_success(
        self,
    ) -> None:
        helpers = self._helpers()
        store, service, promoted_case, _evidence_id, reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        delegated_at = cli_inspection_tests.datetime.now(timezone.utc)
        seeded = helpers._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="phase26-missing-receipt-001",
            coordination_reference_id="coord-ref-phase26-missing-receipt-001",
        )
        original_dispatch = type(service._shuffle).dispatch_approved_action

        def dispatch_without_external_receipt_id(
            adapter: object,
            **kwargs: object,
        ) -> object:
            receipt = original_dispatch(adapter, **kwargs)
            return cli_inspection_tests.replace(receipt, external_receipt_id="")

        with mock.patch.object(
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
                    action_request_id=seeded["action_request"].action_request_id,
                    approved_payload=seeded["approved_payload"],
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        payload = self._inspect_case_detail(service=service, case_id=promoted_case.case_id)
        review = payload["current_action_review"]
        outcome = review["coordination_ticket_outcome"]

        self.assertEqual(review["action_execution_state"], "failed")
        self.assertEqual(outcome["status"], "timeout")
        self.assertEqual(outcome["timeout"]["path"], "provider")
        self.assertEqual(outcome["timeout"]["reason"], "execution_failed")
        self.assertEqual(
            store.list(cli_inspection_tests.ActionExecutionRecord)[0].provenance[
                "dispatch_failure"
            ]["error"],
            "adapter receipt missing required 'external_receipt_id' attribute",
        )

    def test_phase26_end_to_end_surfaces_duplicate_create_attempt_as_mismatch(
        self,
    ) -> None:
        helpers = self._helpers()
        _, service, promoted_case, _evidence_id, reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = helpers._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="phase26-duplicate-001",
            coordination_reference_id="coord-ref-phase26-duplicate-001",
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
                {
                    "execution_run_id": "shuffle-run-phase26-duplicate-secondary-001",
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
                    "external_receipt_id": "shuffle-receipt-phase26-duplicate-secondary-001",
                    "coordination_target_id": "zammad-ticket-phase26-duplicate-secondary-001",
                    "ticket_reference_url": (
                        "https://tickets.example.test/#ticket/"
                        "zammad-ticket-phase26-duplicate-secondary-001"
                    ),
                    "observed_at": compared_at + timedelta(seconds=1),
                    "status": "success",
                },
            ),
            compared_at=compared_at + timedelta(seconds=1),
            stale_after=reviewed_at + timedelta(hours=1),
        )

        payload = self._inspect_case_detail(service=service, case_id=promoted_case.case_id)
        outcome = payload["current_action_review"]["coordination_ticket_outcome"]

        self.assertEqual(outcome["status"], "mismatch")
        self.assertEqual(
            outcome["mismatch"]["mismatch_summary"],
            "duplicate downstream executions observed for one approved request",
        )

    def test_phase26_end_to_end_surfaces_create_tracking_ticket_identifier_mismatch(
        self,
    ) -> None:
        helpers = self._helpers()
        _, service, promoted_case, _evidence_id, reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        delegated_at = reviewed_at + timedelta(minutes=15)
        compared_at = reviewed_at + timedelta(minutes=20)
        seeded = helpers._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="phase26-mismatch-001",
            coordination_reference_id="coord-ref-phase26-mismatch-001",
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
                    "external_receipt_id": "shuffle-receipt-phase26-drifted-001",
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

        payload = self._inspect_case_detail(service=service, case_id=promoted_case.case_id)
        outcome = payload["current_action_review"]["coordination_ticket_outcome"]

        self.assertEqual(outcome["status"], "mismatch")
        self.assertEqual(
            outcome["mismatch"]["mismatch_summary"],
            "coordination receipt mismatch between authoritative action execution "
            "and observed downstream execution",
        )

    def test_phase26_end_to_end_surfaces_create_tracking_ticket_timeout(
        self,
    ) -> None:
        helpers = self._helpers()
        _, service, promoted_case, _evidence_id, reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        delegated_at = cli_inspection_tests.datetime.now(timezone.utc)
        seeded = helpers._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="phase26-timeout-001",
            coordination_reference_id="coord-ref-phase26-timeout-001",
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

        payload = self._inspect_case_detail(service=service, case_id=promoted_case.case_id)
        outcome = payload["current_action_review"]["coordination_ticket_outcome"]

        self.assertEqual(outcome["status"], "timeout")
        self.assertEqual(outcome["timeout"]["reason"], "dispatch_timeout")
        self.assertEqual(outcome["timeout"]["path"], "provider")

    def test_phase26_end_to_end_surfaces_create_tracking_ticket_manual_fallback(
        self,
    ) -> None:
        helpers = self._helpers()
        _, service, promoted_case, evidence_id, reviewed_at = (
            helpers._build_phase19_in_scope_case()
        )
        seeded = helpers._seed_create_tracking_ticket_request(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            suffix="phase26-manual-fallback-001",
            coordination_reference_id="coord-ref-phase26-manual-fallback-001",
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
            fallback_actor_identity="analyst-phase26-001",
            authority_boundary="approved_human_fallback",
            reason="The reviewed create-ticket automation path was unavailable after approval.",
            action_taken="Opened the reviewed tracking ticket manually using the approved procedure.",
            verification_evidence_ids=(evidence_id,),
            residual_uncertainty="Awaiting downstream operator acknowledgement in the next review window.",
        )
        service.persist_record(
            replace(
                service.get_record(
                    cli_inspection_tests.AlertRecord, promoted_case.alert_id
                ),
                coordination_reference_id="coord-ref-phase26-manual-fallback-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )
        service.persist_record(
            replace(
                service.get_record(
                    cli_inspection_tests.CaseRecord, promoted_case.case_id
                ),
                coordination_reference_id="coord-ref-phase26-manual-fallback-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-4242",
                ticket_reference_url="https://tickets.example.test/#ticket/4242",
            )
        )

        payload = self._inspect_case_detail(service=service, case_id=promoted_case.case_id)
        outcome = payload["current_action_review"]["coordination_ticket_outcome"]

        self.assertEqual(payload["external_ticket_reference"]["status"], "present")
        self.assertEqual(outcome["status"], "manual_fallback")
        self.assertEqual(
            outcome["manual_fallback"]["fallback_actor_identity"],
            "analyst-phase26-001",
        )
        self.assertEqual(
            outcome["manual_fallback"]["action_taken"],
            "Opened the reviewed tracking ticket manually using the approved procedure.",
        )


if __name__ == "__main__":
    unittest.main()
