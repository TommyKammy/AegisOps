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
        transition_records = store.list(LifecycleTransitionRecord)

        self.assertEqual(closed_case.lifecycle_state, "closed")
        self.assertEqual(persisted_case.lifecycle_state, "closed")
        self.assertEqual(persisted_alert.lifecycle_state, "closed")

        self.assertEqual(
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
