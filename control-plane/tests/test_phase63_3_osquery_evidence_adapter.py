from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.evidence.osquery_evidence_adapter import (  # noqa: E402
    OsqueryEvidenceAdapter,
    OsqueryEvidenceAdapterInput,
)
from aegisops.control_plane.evidence.reviewed_evidence_requests import (  # noqa: E402
    ReviewedEvidenceRequestRecord,
)


class Phase633OsqueryEvidenceAdapterTests(unittest.TestCase):
    def _reviewed_request(
        self,
        *,
        now: datetime | None = None,
        host_identifier: str = "host-001",
    ) -> ReviewedEvidenceRequestRecord:
        requested_at = now or datetime.now(timezone.utc)
        return ReviewedEvidenceRequestRecord(
            evidence_request_id="evidence-request-001",
            case_id="case-001",
            requester_identity="analyst-001",
            requester_role="security_analyst",
            target={
                "target_class": "explicitly_bound_host",
                "host_identifier": host_identifier,
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
            requested_at=requested_at,
            expires_at=requested_at + timedelta(hours=2),
            lifecycle_state="reviewed",
            authority_posture=(
                "aegisops_owned_workflow_context_subordinate_evidence_output"
            ),
        )

    def _valid_input(
        self,
        *,
        now: datetime | None = None,
        host_identifier: str = "host-001",
        collected_at: datetime | None = None,
        custody: dict[str, object] | None = None,
        rows: object | None = None,
        adapter_state: str = "available",
        requested_operation: str = "collect_host_context",
    ) -> OsqueryEvidenceAdapterInput:
        timestamp = now or datetime.now(timezone.utc)
        return OsqueryEvidenceAdapterInput(
            request=self._reviewed_request(now=timestamp),
            host_identifier=host_identifier,
            query_id="osquery-pack-host-state",
            query_name="host_state",
            result_kind="host_state",
            rows=rows if rows is not None else ({"hostname": "host-001"},),
            collected_at=collected_at or timestamp,
            custody=custody
            if custody is not None
            else {
                "reviewed_query_id": "reviewed-query-001",
                "collector_identity": "osquery-automation-001",
                "collection_timestamp": timestamp.isoformat(),
                "host_binding": "host-001",
                "aegisops_evidence_record_id": "evidence-osquery-001",
            },
            adapter_state=adapter_state,
            requested_operation=requested_operation,
        )

    def test_normal_osquery_result_builds_subordinate_evidence_pack(self) -> None:
        now = datetime.now(timezone.utc)

        pack = OsqueryEvidenceAdapter().build_evidence_pack(
            self._valid_input(now=now),
            now=now,
        )

        self.assertEqual(pack.status, "available")
        self.assertEqual(pack.evidence_request_id, "evidence-request-001")
        self.assertEqual(pack.case_id, "case-001")
        self.assertEqual(pack.source_id, "osquery_host_state")
        self.assertEqual(pack.host_identifier, "host-001")
        self.assertEqual(pack.freshness, "fresh")
        self.assertEqual(pack.authority_posture, "subordinate_evidence_context_only")
        self.assertEqual(pack.custody["reviewed_query_id"], "reviewed-query-001")
        self.assertEqual(pack.provenance["request_binding"], "evidence-request-001")
        self.assertEqual(pack.content["result"]["row_count"], 1)
        self.assertEqual(pack.remediation_authority, "none")

    def test_stale_osquery_output_is_degraded_not_truth(self) -> None:
        now = datetime.now(timezone.utc)
        pack = OsqueryEvidenceAdapter().build_evidence_pack(
            self._valid_input(
                now=now,
                collected_at=now - timedelta(hours=25),
            ),
            now=now,
        )

        self.assertEqual(pack.status, "degraded")
        self.assertEqual(pack.freshness, "stale")
        self.assertIn("stale_collection", pack.degraded_reasons)
        self.assertEqual(pack.authority_posture, "subordinate_evidence_context_only")

    def test_unavailable_adapter_returns_unavailable_pack(self) -> None:
        now = datetime.now(timezone.utc)
        pack = OsqueryEvidenceAdapter().build_evidence_pack(
            self._valid_input(now=now, adapter_state="unavailable"),
            now=now,
        )

        self.assertEqual(pack.status, "unavailable")
        self.assertIn("adapter_unavailable", pack.unavailable_reasons)
        self.assertEqual(pack.content["result"]["rows"], ())

    def test_malformed_output_is_rejected(self) -> None:
        now = datetime.now(timezone.utc)

        with self.assertRaisesRegex(ValueError, "rows must be a sequence of mappings"):
            OsqueryEvidenceAdapter().build_evidence_pack(
                self._valid_input(now=now, rows="not-json-rows"),
                now=now,
            )

    def test_unauthorized_request_fails_closed(self) -> None:
        now = datetime.now(timezone.utc)
        request = self._reviewed_request(now=now).with_updates(
            authorization={
                "authorized": False,
                "reviewed_scope": "bounded_read_only_host_state",
                "decision_id": "approval-decision-001",
            }
        )
        adapter_input = self._valid_input(now=now)

        with self.assertRaisesRegex(ValueError, "reviewed evidence request invalid"):
            OsqueryEvidenceAdapter().build_evidence_pack(
                adapter_input.with_updates(request=request),
                now=now,
            )

    def test_target_mismatch_fails_closed(self) -> None:
        now = datetime.now(timezone.utc)

        with self.assertRaisesRegex(
            ValueError,
            "host_identifier must match reviewed request target",
        ):
            OsqueryEvidenceAdapter().build_evidence_pack(
                self._valid_input(now=now, host_identifier="host-002"),
                now=now,
            )

    def test_missing_custody_fails_closed(self) -> None:
        now = datetime.now(timezone.utc)

        with self.assertRaisesRegex(ValueError, "missing_osquery_custody"):
            OsqueryEvidenceAdapter().build_evidence_pack(
                self._valid_input(now=now, custody={}),
                now=now,
            )

    def test_no_remediation_or_direct_command_authority(self) -> None:
        now = datetime.now(timezone.utc)

        with self.assertRaisesRegex(ValueError, "osquery adapter is read-only"):
            OsqueryEvidenceAdapter().build_evidence_pack(
                self._valid_input(
                    now=now,
                    requested_operation="remediate_process",
                ),
                now=now,
            )


if __name__ == "__main__":
    unittest.main()
