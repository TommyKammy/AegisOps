from __future__ import annotations

from copy import deepcopy
import json
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import ReconciliationRecord
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


FIXTURES_ROOT = pathlib.Path(__file__).resolve().parent / "fixtures" / "wazuh"


def _load_wazuh_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


class Phase18LiveWazuhQueueValidationTests(unittest.TestCase):
    def test_live_github_audit_ingest_restates_and_deduplicates_into_case_linked_queue_record(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="0.0.0.0",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",
                wazuh_ingest_trusted_proxy_cidrs=("10.10.0.5/32",),
            ),
            store=store,
        )

        created_alert = _load_wazuh_fixture("github-audit-alert.json")
        restated_alert = deepcopy(created_alert)
        restated_alert["id"] = "1731596200.1234568"
        restated_alert["timestamp"] = "2026-04-05T12:35:00+00:00"
        deduplicated_alert = deepcopy(restated_alert)

        created = service.ingest_wazuh_alert(
            raw_alert=created_alert,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            peer_addr="10.10.0.5",
        )
        promoted_case = service.promote_alert_to_case(created.alert.alert_id)
        restated = service.ingest_wazuh_alert(
            raw_alert=restated_alert,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            peer_addr="10.10.0.5",
        )
        deduplicated = service.ingest_wazuh_alert(
            raw_alert=deduplicated_alert,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            peer_addr="10.10.0.5",
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(deduplicated.disposition, "deduplicated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(deduplicated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.case_id, promoted_case.case_id)
        self.assertEqual(deduplicated.alert.case_id, promoted_case.case_id)

        restated_reconciliation = service.get_record(
            ReconciliationRecord,
            restated.reconciliation.reconciliation_id,
        )
        deduplicated_reconciliation = service.get_record(
            ReconciliationRecord,
            deduplicated.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["admission_provenance"],
            {
                "admission_kind": "live",
                "admission_channel": "live_wazuh_webhook",
            },
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["admission_provenance"],
            {
                "admission_kind": "live",
                "admission_channel": "live_wazuh_webhook",
            },
        )

        queue_view = service.inspect_analyst_queue()

        self.assertTrue(queue_view.read_only)
        self.assertEqual(queue_view.queue_name, "analyst_review")
        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], created.alert.alert_id)
        self.assertEqual(queue_view.records[0]["case_id"], promoted_case.case_id)
        self.assertEqual(queue_view.records[0]["case_lifecycle_state"], "open")
        self.assertEqual(queue_view.records[0]["queue_selection"], "business_hours_triage")
        self.assertEqual(queue_view.records[0]["review_state"], "case_required")
        self.assertEqual(queue_view.records[0]["source_system"], "wazuh")
        self.assertEqual(
            queue_view.records[0]["substrate_detection_record_ids"],
            (
                "wazuh:1731595300.1234567",
                "wazuh:1731596200.1234568",
            ),
        )
        self.assertEqual(
            queue_view.records[0]["accountable_source_identities"],
            ("manager:wazuh-manager-github-1",),
        )
        self.assertEqual(
            queue_view.records[0]["reviewed_context"]["source"]["source_family"],
            "github_audit",
        )
        self.assertEqual(
            queue_view.records[0]["correlation_key"],
            created.reconciliation.correlation_key,
        )
        self.assertEqual(
            queue_view.records[0]["last_seen_at"].isoformat(),
            "2026-04-05T12:35:00+00:00",
        )


if __name__ == "__main__":
    unittest.main()
