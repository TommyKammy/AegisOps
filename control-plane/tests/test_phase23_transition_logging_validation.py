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


class Phase23TransitionLoggingValidationTests(ServicePersistenceTestBase):
    def test_transition_logging_rolls_back_current_state_when_append_only_save_fails(
        self,
    ) -> None:
        store, _ = make_store()
        failing_store = RecordTypeSaveFailingStore(
            inner=store,
            record_type=LifecycleTransitionRecord,
            message="synthetic lifecycle transition save failure",
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=failing_store,
        )
        alert = AlertRecord(
            alert_id="alert-transition-atomicity-001",
            finding_id="finding-transition-atomicity-001",
            analytic_signal_id=None,
            case_id=None,
            lifecycle_state="new",
        )

        with self.assertRaisesRegex(
            RuntimeError,
            "synthetic lifecycle transition save failure",
        ):
            service.persist_record(alert)

        self.assertIsNone(service.get_record(AlertRecord, alert.alert_id))
        self.assertEqual(service.list_lifecycle_transitions("alert", alert.alert_id), ())

    def test_case_and_alert_lifecycle_transitions_are_logged_append_only(self) -> None:
        store, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()

        closed_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="closed_resolved",
            rationale="Containment completed and the reviewed follow-up is finished.",
            recorded_at=reviewed_at + timedelta(minutes=30),
        )

        persisted_case = service.get_record(CaseRecord, promoted_case.case_id)
        persisted_alert = service.get_record(AlertRecord, promoted_case.alert_id)
        case_detail = service.inspect_case_detail(promoted_case.case_id)
        alert_detail = service.inspect_alert_detail(promoted_case.alert_id)
        transition_records = sorted(
            store.list(LifecycleTransitionRecord),
            key=lambda record: (record.transitioned_at, record.transition_id),
        )

        self.assertEqual(closed_case.lifecycle_state, "closed")
        self.assertEqual(persisted_case.lifecycle_state, "closed")
        self.assertEqual(persisted_alert.lifecycle_state, "closed")

        self.assertCountEqual(
            [
                (
                    record.subject_record_family,
                    record.subject_record_id,
                    record.lifecycle_state,
                )
                for record in transition_records
                if record.subject_record_family in {"case", "alert"}
                and record.subject_record_id in {promoted_case.case_id, promoted_case.alert_id}
            ],
            [
                ("alert", promoted_case.alert_id, "new"),
                ("case", promoted_case.case_id, "open"),
                ("alert", promoted_case.alert_id, "escalated_to_case"),
                ("case", promoted_case.case_id, "closed"),
                ("alert", promoted_case.alert_id, "closed"),
            ],
        )
        self.assertEqual(
            [entry["lifecycle_state"] for entry in case_detail.lifecycle_transitions],
            ["open", "closed"],
        )
        self.assertEqual(
            [entry["lifecycle_state"] for entry in alert_detail.lifecycle_transitions],
            ["new", "escalated_to_case", "closed"],
        )

    def test_action_request_pending_approval_transition_is_logged(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-transition-001",
            approval_decision_id="approval-transition-001",
            case_id="case-transition-001",
            alert_id="alert-transition-001",
            finding_id="finding-transition-001",
            idempotency_key="idempotency-transition-001",
            target_scope={"asset_id": "asset-transition-001"},
            requester_identity="analyst-001",
            requested_payload={"action_type": "notify_identity_owner"},
            policy_basis={"severity": "high"},
            policy_evaluation={"approval_requirement": "human_required"},
            payload_hash="payload-hash-transition-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="pending_approval",
        )

        service.persist_record(action_request)

        self.assertEqual(
            service.get_record(ActionRequestRecord, action_request.action_request_id),
            action_request,
        )
        self.assertEqual(
            [
                transition.lifecycle_state
                for transition in store.list(LifecycleTransitionRecord)
                if transition.subject_record_family == "action_request"
                and transition.subject_record_id == action_request.action_request_id
            ],
            ["pending_approval"],
        )
        self.assertEqual(
            [
                transition.lifecycle_state
                for transition in service.list_lifecycle_transitions(
                    "action_request",
                    action_request.action_request_id,
                )
            ],
            ["pending_approval"],
        )

    def test_transition_logging_uses_reviewed_event_timestamps(self) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Keep approval timing aligned with the reviewed workflow.",
        )
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="owner-001",
            message_intent="Notify the accountable owner.",
            escalation_reason="Reviewed response requires prompt owner contact.",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            action_request_id="action-request-transition-timestamp-001",
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        approval_decision = service.record_action_approval_decision(
            action_request_id=action_request.action_request_id,
            approver_identity="approver-001",
            decision="grant",
            decision_rationale="Reviewed and approved for operator follow-through.",
            decided_at=decided_at,
            approval_decision_id="approval-decision-transition-timestamp-001",
        )
        recorded_at = decided_at + timedelta(minutes=10)
        service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="closed_resolved",
            rationale="Containment completed and reviewed follow-up is finished.",
            recorded_at=recorded_at,
        )

        self.assertEqual(
            service.list_lifecycle_transitions("approval_decision", approval_decision.approval_decision_id)[
                -1
            ].transitioned_at,
            decided_at,
        )
        self.assertEqual(
            service.list_lifecycle_transitions("action_request", action_request.action_request_id)[
                -1
            ].transitioned_at,
            decided_at,
        )
        self.assertEqual(
            service.list_lifecycle_transitions("case", promoted_case.case_id)[
                -1
            ].transitioned_at,
            recorded_at,
        )
        self.assertEqual(
            service.list_lifecycle_transitions("alert", promoted_case.alert_id)[
                -1
            ].transitioned_at,
            recorded_at,
        )

    def test_transition_listing_orders_by_transitioned_at(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        alert = AlertRecord(
            alert_id="alert-transition-ordering-001",
            finding_id="finding-transition-ordering-001",
            analytic_signal_id=None,
            case_id=None,
            lifecycle_state="closed",
        )
        first_transitioned_at = datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc)
        second_transitioned_at = first_transitioned_at + timedelta(minutes=5)
        third_transitioned_at = first_transitioned_at + timedelta(minutes=10)

        store.save(alert)
        store.save(
            LifecycleTransitionRecord(
                transition_id="transition-ordering-300",
                subject_record_family="alert",
                subject_record_id=alert.alert_id,
                previous_lifecycle_state=None,
                lifecycle_state="new",
                transitioned_at=first_transitioned_at,
                attribution={"source": "test-fixture", "actor_identities": ()},
            )
        )
        store.save(
            LifecycleTransitionRecord(
                transition_id="transition-ordering-100",
                subject_record_family="alert",
                subject_record_id=alert.alert_id,
                previous_lifecycle_state="new",
                lifecycle_state="triaged",
                transitioned_at=second_transitioned_at,
                attribution={"source": "test-fixture", "actor_identities": ()},
            )
        )
        store.save(
            LifecycleTransitionRecord(
                transition_id="transition-ordering-200",
                subject_record_family="alert",
                subject_record_id=alert.alert_id,
                previous_lifecycle_state="triaged",
                lifecycle_state="closed",
                transitioned_at=third_transitioned_at,
                attribution={"source": "test-fixture", "actor_identities": ()},
            )
        )

        self.assertEqual(
            [
                transition.transition_id
                for transition in service.list_lifecycle_transitions(
                    "alert",
                    alert.alert_id,
                )
            ],
            [
                "transition-ordering-300",
                "transition-ordering-100",
                "transition-ordering-200",
            ],
        )
