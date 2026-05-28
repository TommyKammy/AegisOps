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

    def test_authority_boundary_rejects_documented_verbs(self) -> None:
        claims = (
            "evidence output can execute the action",
            "source-native state can reconcile case findings",
            "freshness projection can close cases",
            "hash-reputation output can activate detectors",
            "verifier output can gate release",
            "UI cache can claim readiness",
            "evidence pack claims readiness",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                request = self._valid_request().with_updates(authority_posture=claim)

                self.assertIn(
                    "authority_posture_promotes_workflow_truth",
                    validate_phase63_reviewed_evidence_request(request),
                )

    def test_authority_boundary_rejects_authorization_posture_claims(self) -> None:
        claims = (
            "evidence output executes the action",
            "evidence output reconciles case findings",
            "evidence output can gate release",
            "evidence pack claims readiness",
        )
        for claim in claims:
            with self.subTest(claim=claim):
                request = self._valid_request().with_updates(
                    authorization={
                        "authorized": True,
                        "reviewed_scope": "bounded_read_only_host_state",
                        "decision_id": "approval-decision-001",
                        "authority_posture": claim,
                    },
                )

                self.assertIn(
                    "authority_posture_promotes_workflow_truth",
                    validate_phase63_reviewed_evidence_request(request),
                )

    def test_reviewed_scope_rejects_authority_claims(self) -> None:
        request = self._valid_request().with_updates(
            requested_scope="execute the containment action",
            authorization={
                "authorized": True,
                "reviewed_scope": "execute the containment action",
                "decision_id": "approval-decision-001",
            },
        )

        errors = validate_phase63_reviewed_evidence_request(request)

        self.assertIn("requested_scope_promotes_workflow_truth", errors)
        self.assertIn("authorization_scope_promotes_workflow_truth", errors)

    def test_source_status_truth_claims_are_normalized(self) -> None:
        cases = (
            {"status": "workflow_truth"},
            {"state": "case_truth"},
            {"registry_state": "approval truth"},
            {"source_state": "releaseGateTruth"},
        )
        for source_status in cases:
            with self.subTest(source_status=source_status):
                request = self._valid_request().with_updates(
                    source_status=source_status
                )

                self.assertIn(
                    "source_status_promotes_workflow_truth",
                    validate_phase63_reviewed_evidence_request(request),
                )

    def test_source_freshness_beyond_registry_window_is_stale(self) -> None:
        cases = (
            self._valid_request().with_updates(
                source_status={"status": "enabled", "freshness": "PT25H"}
            ),
            self._valid_request().with_updates(
                source_id="malwarebazaar_hash_reputation",
                target={
                    "target_class": "reviewed_file_hash",
                    "file_hash": "sha256:abc",
                    "case_id": "case-001",
                },
                requested_scope="bounded_read_only_hash_reputation",
                authorization={
                    "authorized": True,
                    "reviewed_scope": "bounded_read_only_hash_reputation",
                    "decision_id": "approval-decision-001",
                },
                source_status={"status": "enabled", "freshness": "PT7H"},
            ),
        )
        for request in cases:
            with self.subTest(source_id=request.source_id):
                self.assertIn(
                    "source_stale",
                    validate_phase63_reviewed_evidence_request(request),
                )

    def test_source_registry_degraded_and_disabled_state_names_fail_closed(
        self,
    ) -> None:
        cases = {
            "degraded_status": (
                {"status": "missing_host_binding"},
                "source_stale",
            ),
            "degraded_source_state": (
                {"source_state": "stale_collection"},
                "source_stale",
            ),
            "disabled_state": (
                {"state": "disabled_by_policy"},
                "source_denied",
            ),
            "disabled_registry_state": (
                {"registry_state": "missing_custody"},
                "source_denied",
            ),
            "disabled_status": (
                {"status": "missing_custody"},
                "source_denied",
            ),
        }
        for label, (source_status, expected_error) in cases.items():
            with self.subTest(label=label):
                request = self._valid_request().with_updates(
                    source_status=source_status
                )

                self.assertIn(
                    expected_error,
                    validate_phase63_reviewed_evidence_request(request),
                )

        malwarebazaar_request = self._valid_request().with_updates(
            source_id="malwarebazaar_hash_reputation",
            target={
                "target_class": "reviewed_file_hash",
                "file_hash": "sha256:abc",
                "case_id": "case-001",
            },
            requested_scope="bounded_read_only_hash_reputation",
            authorization={
                "authorized": True,
                "reviewed_scope": "bounded_read_only_hash_reputation",
                "decision_id": "approval-decision-001",
            },
            source_status={"status": "stale_reputation"},
        )

        self.assertIn(
            "source_stale",
            validate_phase63_reviewed_evidence_request(malwarebazaar_request),
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

    def test_duplicate_request_check_only_applies_to_active_candidate(self) -> None:
        request = self._valid_request().with_updates(lifecycle_state="completed")

        self.assertNotIn(
            "duplicate_request_ambiguity",
            validate_phase63_reviewed_evidence_request(
                request,
                existing_requests=(request.with_updates(evidence_request_id="other"),),
            ),
        )

    def test_duplicate_request_check_ignores_terminal_existing_requests(self) -> None:
        request = self._valid_request()

        self.assertNotIn(
            "duplicate_request_ambiguity",
            validate_phase63_reviewed_evidence_request(
                request,
                existing_requests=(
                    request.with_updates(
                        evidence_request_id="other",
                        lifecycle_state="completed",
                    ),
                ),
            ),
        )

    def test_evidence_request_id_reuse_for_different_subject_is_rejected(self) -> None:
        request = self._valid_request()
        existing_requests = (
            request.with_updates(
                case_id="case-002",
                target={
                    "target_class": "explicitly_bound_host",
                    "host_identifier": "host-002",
                    "case_id": "case-002",
                },
            ),
            request.with_updates(
                requested_scope="bounded_read_only_hash_reputation",
                authorization={
                    "authorized": True,
                    "reviewed_scope": "bounded_read_only_hash_reputation",
                    "decision_id": "approval-decision-001",
                },
            ),
            request.with_updates(
                source_id="malwarebazaar_hash_reputation",
                target={
                    "target_class": "reviewed_file_hash",
                    "file_hash": "sha256:abc",
                    "case_id": "case-001",
                },
            ),
        )
        for existing_request in existing_requests:
            with self.subTest(existing_request=existing_request):
                self.assertIn(
                    "evidence_request_id_subject_mismatch",
                    validate_phase63_reviewed_evidence_request(
                        request,
                        existing_requests=(existing_request,),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
