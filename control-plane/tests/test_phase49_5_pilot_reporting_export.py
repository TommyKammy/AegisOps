from __future__ import annotations

from datetime import datetime, timezone
import json
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.models import CaseRecord, EvidenceRecord
from aegisops.control_plane.reporting.pilot_reporting_export import (
    export_pilot_executive_summary,
)
from aegisops.control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


LOCAL_EXPORT_PATH = (
    "/Users/alice/aegisops/pilot-summary.json"  # publishable-path-hygiene: allowlist
)


class Phase495PilotReportingExportTests(unittest.TestCase):
    def test_executive_summary_derives_authoritative_records_and_labels_subordinate_evidence(
        self,
    ) -> None:
        store, backend = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        exported_at = datetime(2026, 4, 29, 3, 20, tzinfo=timezone.utc)
        evidence_acquired_at = datetime(2026, 4, 29, 3, 10, tzinfo=timezone.utc)

        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-pilot-summary-1",
                source_record_id="native-pilot-summary-1",
                alert_id="alert-pilot-summary-1",
                case_id="case-pilot-summary-1",
                source_system="zammad",
                collector_identity="collector://zammad/reviewed-export",
                acquired_at=evidence_acquired_at,
                derivation_relationship="coordination_context",
                lifecycle_state="collected",
                provenance={
                    "ticket_url": "https://tickets.example.invalid/123",
                    "workspace_path": LOCAL_EXPORT_PATH,
                },
                content={
                    "coordination_summary": "customer ticket confirms contact",
                    "api_token": "live-token-must-not-export",
                },
            ),
            transitioned_at=evidence_acquired_at,
        )
        service.persist_record(
            CaseRecord(
                case_id="case-pilot-summary-1",
                alert_id="alert-pilot-summary-1",
                finding_id="finding-pilot-summary-1",
                evidence_ids=("evidence-pilot-summary-1",),
                lifecycle_state="pending_action",
                reviewed_context={
                    "pilot_release_identifier": (
                        "aegisops-single-customer-pilot-2026-04-27-c4527e5"
                    ),
                    "operator_summary": "Reviewed case remains bounded.",
                },
            ),
            transitioned_at=exported_at,
        )

        export = export_pilot_executive_summary(
            store=store,
            export_id="pilot-exec-summary-phase49-5",
            release_identifier="aegisops-single-customer-pilot-2026-04-27-c4527e5",
            exported_at=exported_at,
        )

        self.assertEqual(export["schema_version"], "phase49.5.pilot-summary.v1")
        self.assertEqual(export["source_of_truth"], "aegisops_authoritative_records")
        self.assertEqual(
            export["claim_boundaries"],
            {
                "compliance_certification_claim": False,
                "sla_guarantee_claim": False,
                "autonomous_response_claim": False,
                "customer_portal_claim": False,
                "multi_tenant_reporting_claim": False,
            },
        )
        self.assertEqual(export["case_summary"]["total_cases"], 1)
        self.assertEqual(export["case_summary"]["by_lifecycle_state"], {"pending_action": 1})
        self.assertEqual(
            export["subordinate_evidence_policy"],
            {
                "authority_role": "subordinate_evidence",
                "promotion_allowed": False,
                "label_required": True,
            },
        )

        case = export["authoritative_records"]["cases"][0]
        self.assertEqual(case["case_id"], "case-pilot-summary-1")
        self.assertEqual(case["authority_role"], "authoritative_control_plane_record")
        subordinate = case["subordinate_evidence"][0]
        self.assertEqual(subordinate["authority_role"], "subordinate_evidence")
        self.assertFalse(subordinate["promotion_allowed"])
        self.assertEqual(subordinate["source_system"], "zammad")
        self.assertEqual(subordinate["content"]["api_token"], "<redacted-secret>")
        self.assertEqual(
            subordinate["provenance"]["workspace_path"],
            "<redacted-local-path>",
        )

        serialized = json.dumps(export, sort_keys=True)
        self.assertNotIn("live-token-must-not-export", serialized)
        self.assertNotIn(LOCAL_EXPORT_PATH, serialized)
        self.assertNotIn("SLA is promised", serialized)

        self.assertTrue(
            any(
                statement.startswith("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                for statement, _params in backend.statements
            ),
            "pilot executive summary export must read one authoritative snapshot",
        )

    def test_executive_summary_rejects_unsupported_customer_facing_claims(self) -> None:
        store, backend = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        exported_at = datetime(2026, 4, 29, 3, 45, tzinfo=timezone.utc)

        for claim, expected in (
            (
                "Compliance certification is complete.",
                "unsupported pilot executive summary claim",
            ),
            (
                "SLA is promised for 24x7 response.",
                "unsupported pilot executive summary claim",
            ),
            (
                "Autonomous response is approved for production.",
                "unsupported pilot executive summary claim",
            ),
            (
                "Token: abc123 must not appear in the executive export.",
                "secret-looking pilot executive summary value",
            ),
            (
                f"Review the local export at {LOCAL_EXPORT_PATH}.",
                "workstation-local pilot executive summary path",
            ),
        ):
            with self.subTest(claim=claim):
                with self.assertRaisesRegex(
                    ValueError,
                    expected,
                ):
                    export_pilot_executive_summary(
                        store=store,
                        export_id="pilot-exec-summary-phase49-5",
                        release_identifier=(
                            "aegisops-single-customer-pilot-2026-04-27-c4527e5"
                        ),
                        exported_at=exported_at,
                        executive_note=claim,
                    )

        self.assertFalse(
            any(
                statement.startswith("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                for statement, _params in backend.statements
            ),
            "invalid executive notes must be rejected before the export snapshot opens",
        )


if __name__ == "__main__":
    unittest.main()
