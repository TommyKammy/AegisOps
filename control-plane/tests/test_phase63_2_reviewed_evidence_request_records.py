from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.evidence.reviewed_evidence_requests import (  # noqa: E402
    ReviewedEvidenceRequestRecord,
    validate_phase63_reviewed_evidence_request,
)


class Phase632ReviewedEvidenceRequestRecordTests(unittest.TestCase):
    def _valid_request(self) -> ReviewedEvidenceRequestRecord:
        now = datetime.now(timezone.utc)
        return ReviewedEvidenceRequestRecord(
            evidence_request_id="evidence-request-001",
            case_id="case-001",
            requester_identity="analyst-001",
            requester_role="security_analyst",
            target={
                "target_class": "explicitly_bound_host",
                "host_identifier": "host-001",
                "case_id": "case-001",
            },
            source_id="osquery_host_state",
            requested_scope="bounded_read_only_host_state",
            custody={
                "reviewed_by": "reviewer-001",
                "custody_owner": "IT Operations, Information Systems Department",
                "custody_reference": "custody-ref-001",
                "provenance_chain": "AegisOps evidence record custody",
            },
            authorization={
                "authorized": True,
                "reviewed_scope": "bounded_read_only_host_state",
                "decision_id": "approval-decision-001",
            },
            linked_case_context={
                "case_id": "case-001",
                "admitting_evidence_id": "evidence-001",
                "reviewed_context_id": "reviewed-context-001",
            },
            requested_at=now,
            expires_at=now + timedelta(hours=2),
            lifecycle_state="reviewed",
            authority_posture="aegisops_owned_workflow_context_subordinate_evidence_output",
        )

    def test_valid_reviewed_evidence_request_is_accepted(self) -> None:
        self.assertEqual(
            validate_phase63_reviewed_evidence_request(self._valid_request()),
            (),
        )

    def test_required_acceptance_criteria_fail_closed(self) -> None:
        expired = self._valid_request()
        expired = expired.with_updates(
            expires_at=expired.requested_at - timedelta(minutes=1)
        )
        cases = {
            "missing_scope": (
                self._valid_request().with_updates(requested_scope=""),
                "missing_reviewed_scope",
            ),
            "expired_request": (expired, "request_expired"),
            "unauthorized_requester": (
                self._valid_request().with_updates(requester_role="viewer"),
                "unauthorized_requester_role",
            ),
            "invalid_target_source_pairing": (
                self._valid_request().with_updates(
                    target={
                        "target_class": "reviewed_file_hash",
                        "file_hash": "sha256:abc",
                        "case_id": "case-001",
                    },
                    source_id="osquery_host_state",
                ),
                "target_source_not_compatible",
            ),
            "missing_custody": (
                self._valid_request().with_updates(custody={}),
                "missing_custody",
            ),
            "missing_case_link": (
                self._valid_request().with_updates(linked_case_context={}),
                "missing_case_link",
            ),
            "stale_source": (
                self._valid_request().with_updates(
                    source_status={"status": "stale", "freshness": "PT25H"},
                ),
                "source_stale",
            ),
            "denied_source": (
                self._valid_request().with_updates(
                    source_status={"status": "denied"},
                ),
                "source_denied",
            ),
        }
        for label, (request, expected_error) in cases.items():
            with self.subTest(label=label):
                self.assertIn(
                    expected_error,
                    validate_phase63_reviewed_evidence_request(request),
                )

    def test_authority_boundary_rejects_evidence_output_as_truth(self) -> None:
        request = self._valid_request().with_updates(
            authority_posture="evidence output approves the case and creates source truth"
        )

        self.assertIn(
            "authority_posture_promotes_workflow_truth",
            validate_phase63_reviewed_evidence_request(request),
        )

    def test_duplicate_request_ambiguity_is_rejected(self) -> None:
        request = self._valid_request()

        self.assertIn(
            "duplicate_request_ambiguity",
            validate_phase63_reviewed_evidence_request(
                request,
                existing_requests=(request.with_updates(evidence_request_id="other"),),
            ),
        )


if __name__ == "__main__":
    unittest.main()
