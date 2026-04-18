from __future__ import annotations

from datetime import datetime, timezone
import pathlib
import secrets
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import CaseRecord, EvidenceRecord, ObservationRecord
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from tests.support.fixtures import load_wazuh_fixture


class Phase25OsqueryHostContextValidationTests(unittest.TestCase):
    def _build_host_bound_case(
        self,
        *,
        host_identifier: str | None,
    ) -> tuple[object, AegisOpsControlPlaneService, CaseRecord, datetime]:
        store, _ = make_store()
        shared_secret = secrets.token_urlsafe(24)
        reverse_proxy_secret = secrets.token_urlsafe(24)
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=shared_secret,
                wazuh_ingest_reverse_proxy_secret=reverse_proxy_secret,
            ),
            store=store,
        )
        reviewed_at = datetime(2026, 4, 18, 0, 0, tzinfo=timezone.utc)
        admitted = service.ingest_wazuh_alert(
            raw_alert=load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {shared_secret}",
            forwarded_proto="https",
            reverse_proxy_secret_header=reverse_proxy_secret,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        updated_reviewed_context = {
            **dict(promoted_case.reviewed_context),
            "asset": {
                **dict(promoted_case.reviewed_context.get("asset", {})),
            },
        }
        if host_identifier is not None:
            updated_reviewed_context["asset"]["host_identifier"] = host_identifier
        promoted_case = service.persist_record(
            CaseRecord(
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=promoted_case.evidence_ids,
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=updated_reviewed_context,
            )
        )
        return store, service, promoted_case, reviewed_at

    def test_attach_osquery_host_context_persists_augmenting_evidence_and_observation(
        self,
    ) -> None:
        _store, service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier="host-001"
        )

        evidence, observation = service.attach_osquery_host_context(
            case_id=promoted_case.case_id,
            host_identifier="host-001",
            query_name="running_processes",
            query_sql="SELECT pid, name, path FROM processes;",
            result_kind="process",
            rows=(
                {
                    "pid": "123",
                    "name": "sshd",
                    "path": "/usr/sbin/sshd",
                },
            ),
            collected_at=reviewed_at,
            reviewed_by="analyst-001",
            source_id="query-result-001",
            collection_path="pack/osquery-defense/processes/running_processes",
            query_context={"pack": "osquery-defense", "platform": "linux"},
            observation_scope_statement=(
                "Observed reviewed osquery host context on the explicitly scoped host."
            ),
        )

        self.assertEqual(evidence.case_id, promoted_case.case_id)
        self.assertEqual(evidence.alert_id, promoted_case.alert_id)
        self.assertEqual(evidence.source_system, "osquery")
        self.assertEqual(evidence.provenance["classification"], "augmenting-evidence")
        self.assertEqual(evidence.provenance["source_id"], "query-result-001")
        self.assertEqual(evidence.provenance["reviewed_by"], "analyst-001")
        self.assertEqual(
            evidence.provenance["collection_path"],
            "pack/osquery-defense/processes/running_processes",
        )
        self.assertEqual(evidence.content["host"]["host_identifier"], "host-001")
        self.assertEqual(evidence.content["query"]["name"], "running_processes")
        self.assertEqual(evidence.content["query"]["context"]["pack"], "osquery-defense")
        self.assertEqual(evidence.content["result"]["kind"], "process")
        self.assertEqual(evidence.content["result"]["row_count"], 1)
        self.assertEqual(
            evidence.content["result"]["columns"],
            ("name", "path", "pid"),
        )

        self.assertIsNotNone(observation)
        assert observation is not None
        self.assertEqual(observation.case_id, promoted_case.case_id)
        self.assertEqual(observation.supporting_evidence_ids, (evidence.evidence_id,))
        self.assertEqual(observation.provenance["classification"], "reviewed-derived")
        self.assertEqual(observation.content["host_context_evidence_id"], evidence.evidence_id)
        self.assertEqual(observation.content["result_kind"], "process")

        case_detail = service.inspect_case_detail(promoted_case.case_id)
        persisted_evidence = {
            record["evidence_id"]: record for record in case_detail.linked_evidence_records
        }
        self.assertEqual(
            persisted_evidence[evidence.evidence_id]["provenance"]["classification"],
            "augmenting-evidence",
        )
        persisted_observation = {
            record["observation_id"]: record
            for record in case_detail.linked_observation_records
        }
        self.assertEqual(
            persisted_observation[observation.observation_id]["content"][
                "host_context_evidence_id"
            ],
            evidence.evidence_id,
        )

    def test_attach_osquery_host_context_rejects_when_case_lacks_explicit_host_binding(
        self,
    ) -> None:
        store, service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier=None
        )
        baseline_evidence_ids = {
            record.evidence_id for record in store.list(EvidenceRecord)
        }
        baseline_observation_ids = {
            record.observation_id for record in store.list(ObservationRecord)
        }

        with self.assertRaisesRegex(
            ValueError,
            "reviewed case asset.host_identifier must explicitly bind osquery host context",
        ):
            service.attach_osquery_host_context(
                case_id=promoted_case.case_id,
                host_identifier="host-001",
                query_name="running_processes",
                query_sql="SELECT pid, name, path FROM processes;",
                result_kind="process",
                rows=({"pid": "123", "name": "sshd"},),
                collected_at=reviewed_at,
                reviewed_by="analyst-001",
                source_id="query-result-001",
                collection_path="pack/osquery-defense/processes/running_processes",
            )

        self.assertEqual(
            {record.evidence_id for record in store.list(EvidenceRecord)},
            baseline_evidence_ids,
        )
        self.assertEqual(
            {record.observation_id for record in store.list(ObservationRecord)},
            baseline_observation_ids,
        )

    def test_attach_osquery_host_context_rejects_incomplete_provenance_without_writes(
        self,
    ) -> None:
        store, service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier="host-001"
        )
        baseline_evidence_ids = {
            record.evidence_id for record in store.list(EvidenceRecord)
        }
        baseline_observation_ids = {
            record.observation_id for record in store.list(ObservationRecord)
        }

        with self.assertRaisesRegex(
            ValueError,
            "source_id must be a non-empty string",
        ):
            service.attach_osquery_host_context(
                case_id=promoted_case.case_id,
                host_identifier="host-001",
                query_name="running_processes",
                query_sql="SELECT pid, name, path FROM processes;",
                result_kind="process",
                rows=({"pid": "123", "name": "sshd"},),
                collected_at=reviewed_at,
                reviewed_by="analyst-001",
                source_id="",
                collection_path="pack/osquery-defense/processes/running_processes",
            )

        self.assertEqual(
            {record.evidence_id for record in store.list(EvidenceRecord)},
            baseline_evidence_ids,
        )
        self.assertEqual(
            {record.observation_id for record in store.list(ObservationRecord)},
            baseline_observation_ids,
        )


if __name__ == "__main__":
    unittest.main()
