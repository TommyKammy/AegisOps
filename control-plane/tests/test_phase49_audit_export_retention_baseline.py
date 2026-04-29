from __future__ import annotations

from datetime import datetime, timezone
import json
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import EvidenceRecord
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


LOCAL_EXPORT_PATH = (
    "/Users/alice/aegisops/export.json"  # publishable-path-hygiene: allowlist
)


class Phase49AuditExportRetentionBaselineTests(unittest.TestCase):
    def test_audit_export_derives_authoritative_snapshot_and_redacts_subordinate_evidence(
        self,
    ) -> None:
        store, backend = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        acquired_at = datetime(2026, 4, 29, 1, 30, tzinfo=timezone.utc)

        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-audit-export-1",
                source_record_id="native-wazuh-1",
                alert_id="alert-audit-export-1",
                case_id=None,
                source_system="wazuh",
                collector_identity="collector://wazuh/replay",
                acquired_at=acquired_at,
                derivation_relationship="native_detection_record",
                lifecycle_state="collected",
                provenance={
                    "subordinate_source": "wazuh",
                    "workspace_path": LOCAL_EXPORT_PATH,
                },
                content={
                    "finding": "audit log cleared",
                    "api_token": "live-token-must-not-export",
                },
            ),
            transitioned_at=acquired_at,
        )

        export = service.export_audit_retention_baseline(
            export_id="audit-export-phase49-2",
            exported_at=acquired_at,
        )

        self.assertEqual(export["schema_version"], "phase49.audit-export.v1")
        self.assertEqual(export["source_of_truth"], "aegisops_authoritative_records")
        self.assertEqual(
            export["retention_baseline"],
            {
                "document": "docs/retention-evidence-and-replay-readiness-baseline.md",
                "bounded": True,
                "unlimited_log_retention": False,
                "compliance_certification_claim": False,
            },
        )
        self.assertEqual(
            export["subordinate_evidence_policy"],
            {
                "authority_role": "subordinate_evidence",
                "promotion_allowed": False,
                "label_required": True,
            },
        )

        evidence_records = export["records"]["evidence"]
        self.assertEqual(len(evidence_records), 1)
        evidence = evidence_records[0]
        self.assertEqual(
            evidence["authority_role"],
            "authoritative_control_plane_record",
        )
        self.assertEqual(
            evidence["subordinate_evidence"]["authority_role"],
            "subordinate_evidence",
        )
        self.assertEqual(
            evidence["subordinate_evidence"]["content"]["api_token"],
            "<redacted-secret>",
        )
        self.assertEqual(
            evidence["subordinate_evidence"]["provenance"]["workspace_path"],
            "<redacted-local-path>",
        )
        self.assertNotIn("content", evidence)
        self.assertNotIn("provenance", evidence)

        serialized = json.dumps(export, sort_keys=True)
        self.assertNotIn("live-token-must-not-export", serialized)
        self.assertNotIn(LOCAL_EXPORT_PATH, serialized)

        self.assertTrue(
            any(
                statement.startswith("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
                for statement, _params in backend.statements
            ),
            "audit export must read authoritative records from one repeatable-read snapshot",
        )


if __name__ == "__main__":
    unittest.main()
