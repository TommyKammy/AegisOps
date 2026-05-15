from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
import pathlib
import sys


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

from aegisops.control_plane.models import (
    EvidenceRecord,
    SourceHealthRecord,
)
from support.service_persistence import ServicePersistenceTestBase


class Phase617RecordSearchFilterTests(ServicePersistenceTestBase):
    def test_record_search_returns_reviewed_navigation_results_only(self) -> None:
        store, service, case, evidence_id, _reviewed_at = self._build_phase19_in_scope_case()
        service.persist_record(
            SourceHealthRecord(
                source_health_id="source-health-github-audit-001",
                source_family="github_audit",
                source_catalog_entry="docs/source-families/github-audit/onboarding-package.md",
                health_state="available",
                reviewed_state="reviewed",
                reviewed_at=datetime(2026, 5, 15, 8, 0, tzinfo=timezone.utc),
                observed_at=datetime(2026, 5, 15, 7, 55, tzinfo=timezone.utc),
                detector_drift="none",
                credential_posture="reviewed",
                evidence_references=("evidence://source-health/github-audit",),
                operator_visible_reason="Reviewed GitHub audit source is available.",
                source_native_authority=False,
                display_state_authority=False,
                cache_sourced=False,
            )
        )

        snapshot = service.inspect_record_search(
            query="github",
            record_families=("alert", "case", "evidence", "source_health"),
            source_family="github_audit",
        )
        result_keys = {
            (result["record_family"], result["record_id"])
            for result in snapshot.to_dict()["records"]
        }

        self.assertIn(("case", case.case_id), result_keys)
        self.assertIn(("evidence", evidence_id), result_keys)
        self.assertIn(("source_health", "source-health-github-audit-001"), result_keys)
        for result in snapshot.to_dict()["records"]:
            self.assertEqual(result["authority"], "navigation_only")
            self.assertEqual(result["route_kind"], "reviewed_surface")
            self.assertFalse(result["raw_source_authority"])

        stale_source_health = replace(
            store.get(SourceHealthRecord, "source-health-github-audit-001"),
            source_health_id="source-health-cache-001",
            cache_sourced=True,
        )
        with self.assertRaisesRegex(ValueError, "stale-cache"):
            service.persist_record(stale_source_health)

    def test_record_search_rejects_malformed_or_raw_source_queries(self) -> None:
        _store, service, _case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )

        invalid_queries = (
            "",
            "  ",
            "raw:wazuh rule.id:5715",
            "source-native status current",
            "close case case-001",
        )
        for query in invalid_queries:
            with self.subTest(query=query):
                with self.assertRaisesRegex(ValueError, "unsupported record search query"):
                    service.inspect_record_search(query=query)

        with self.assertRaisesRegex(ValueError, "Unsupported search record family"):
            service.inspect_record_search(
                query="github",
                record_families=("native_detection",),
            )

        raw_evidence = EvidenceRecord(
            evidence_id="evidence-raw-unlinked-001",
            source_record_id="native-raw-001",
            alert_id="alert-unreviewed-raw-001",
            case_id=None,
            source_system="wazuh",
            collector_identity="collector://wazuh/raw",
            acquired_at=datetime(2026, 5, 15, 8, 0, tzinfo=timezone.utc),
            derivation_relationship="native_detection_record",
            lifecycle_state="collected",
            provenance={"classification": "raw"},
            content={"message": "github raw source hit"},
        )
        service.persist_record(raw_evidence)

        snapshot = service.inspect_record_search(query="raw")
        result_ids = {
            result["record_id"]
            for result in snapshot.to_dict()["records"]
        }
        self.assertNotIn(raw_evidence.evidence_id, result_ids)


if __name__ == "__main__":
    import unittest

    unittest.main()
