from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import pathlib
import secrets
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import CaseRecord, EvidenceRecord
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from tests.support.fixtures import load_wazuh_fixture


@dataclass
class _EvidenceSaveMutationStore:
    inner: object
    mutate_once: object
    _mutated: bool = False

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def save(self, record: object) -> object:
        saved = self.inner.save(record)
        if isinstance(record, EvidenceRecord) and not self._mutated:
            self._mutated = True
            self.mutate_once(self.inner)
        return saved

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        return self.inner.list(record_type)

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> object | None:
        return self.inner.latest_lifecycle_transition(record_family, record_id)

    @contextmanager
    def transaction(self, *, isolation_level: str | None = None):
        with self.inner.transaction(isolation_level=isolation_level):
            yield


class Phase28EndpointEvidencePackValidationTests(unittest.TestCase):
    def _build_host_bound_case(
        self,
        *,
        store: object | None = None,
        host_identifier: str = "host-001",
    ) -> tuple[object, AegisOpsControlPlaneService, CaseRecord, str, datetime]:
        if store is None:
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
        reviewed_at = datetime(2026, 4, 19, 0, 0, tzinfo=timezone.utc)
        admitted = service.ingest_wazuh_alert(
            raw_alert=load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {shared_secret}",
            forwarded_proto="https",
            reverse_proxy_secret_header=reverse_proxy_secret,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        promoted_case = service.persist_record(
            CaseRecord(
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=promoted_case.evidence_ids,
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context={
                    **dict(promoted_case.reviewed_context),
                    "asset": {
                        **dict(promoted_case.reviewed_context.get("asset", {})),
                        "host_identifier": host_identifier,
                    },
                },
            )
        )
        return (
            store,
            service,
            promoted_case,
            promoted_case.evidence_ids[0],
            reviewed_at,
        )

    def _approve_action_request(
        self,
        service: AegisOpsControlPlaneService,
        action_request_id: str,
        *,
        decided_at: datetime,
    ) -> None:
        service.record_action_approval_decision(
            action_request_id=action_request_id,
            approver_identity="reviewer-001",
            decision="grant",
            decision_rationale="Approved bounded read-only endpoint evidence collection.",
            decided_at=decided_at,
        )

    def test_create_endpoint_evidence_collection_request_routes_to_executor_with_bounded_scope(
        self,
    ) -> None:
        _store, service, promoted_case, anchor_evidence_id, _reviewed_at = (
            self._build_host_bound_case()
        )

        action_request = service.create_endpoint_evidence_collection_request(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence_id,
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need bounded read-only host triage to resolve the case evidence gap.",
            artifact_classes=("collection_manifest", "triage_bundle", "tool_output_receipt"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
        )

        self.assertEqual(action_request.case_id, promoted_case.case_id)
        self.assertEqual(action_request.alert_id, promoted_case.alert_id)
        self.assertEqual(
            action_request.requested_payload["action_type"],
            "collect_endpoint_evidence_pack",
        )
        self.assertEqual(
            action_request.requested_payload["admitting_evidence_id"],
            anchor_evidence_id,
        )
        self.assertEqual(
            action_request.requested_payload["artifact_classes"],
            (
                "collection_manifest",
                "tool_output_receipt",
                "triage_bundle",
            ),
        )
        self.assertEqual(
            action_request.target_scope["host_identifier"],
            "host-001",
        )
        self.assertEqual(
            action_request.policy_evaluation["execution_surface_type"],
            "executor",
        )
        self.assertEqual(
            action_request.policy_evaluation["execution_surface_id"],
            "isolated-executor",
        )
        self.assertEqual(
            action_request.policy_basis,
            {
                "severity": "medium",
                "target_scope": "single_asset",
                "action_reversibility": "reversible",
                "asset_criticality": "standard",
                "identity_criticality": "standard",
                "blast_radius": "single_target",
                "execution_constraint": "requires_isolated_executor",
            },
        )

    def test_ingest_endpoint_evidence_artifacts_persists_subordinate_evidence_with_citation_metadata(
        self,
    ) -> None:
        _store, service, promoted_case, anchor_evidence_id, reviewed_at = (
            self._build_host_bound_case()
        )
        action_request = service.create_endpoint_evidence_collection_request(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence_id,
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need endpoint evidence to resolve the reviewed host-state gap.",
            artifact_classes=("collection_manifest", "triage_bundle", "binary_analysis"),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
        )
        self._approve_action_request(
            service,
            action_request.action_request_id,
            decided_at=action_request.requested_at + timedelta(minutes=5),
        )

        ingested = service.ingest_endpoint_evidence_artifacts(
            action_request_id=action_request.action_request_id,
            artifacts=(
                {
                    "artifact_class": "collection_manifest",
                    "artifact_id": "manifest-001",
                    "source_artifact_id": "collector-manifest-001",
                    "collected_at": reviewed_at,
                    "collector_identity": "velociraptor",
                    "tool_name": "Velociraptor",
                    "tool_version": "0.7.2",
                    "source_boundary": "endpoint_evidence_pack",
                    "citation_kind": "raw_collected_output",
                    "description": "Reviewed manifest for the bounded endpoint collection.",
                    "content": {
                        "requested_paths": ("/opt/suspicious",),
                        "query_names": ("Artifact.Windows.System.Pslist",),
                    },
                },
                {
                    "artifact_class": "binary_analysis",
                    "artifact_id": "binary-analysis-001",
                    "source_artifact_id": "analysis-001",
                    "derived_from_artifact_id": "manifest-001",
                    "collected_at": reviewed_at + timedelta(minutes=5),
                    "collector_identity": "capa",
                    "tool_name": "capa",
                    "tool_version": "7.0.1",
                    "source_boundary": "endpoint_evidence_pack",
                    "citation_kind": "bounded_derivative",
                    "description": "Derived binary-analysis findings over the reviewed file sample.",
                    "content": {
                        "summary": "Matched capabilities from the bounded sample.",
                    },
                },
            ),
            admitted_by="analyst-001",
        )

        self.assertEqual(len(ingested), 2)
        manifest, analysis = ingested
        self.assertEqual(manifest.case_id, promoted_case.case_id)
        self.assertEqual(
            manifest.provenance["endpoint_request_id"],
            action_request.action_request_id,
        )
        self.assertEqual(manifest.provenance["admitting_evidence_id"], anchor_evidence_id)
        self.assertEqual(manifest.provenance["host_identifier"], "host-001")
        self.assertEqual(
            manifest.provenance["artifact_class"],
            "collection_manifest",
        )
        self.assertEqual(
            manifest.content["citation"]["kind"],
            "raw_collected_output",
        )
        self.assertEqual(
            analysis.provenance["derived_from_artifact_id"],
            "manifest-001",
        )
        self.assertEqual(
            analysis.content["citation"]["kind"],
            "bounded_derivative",
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id)
        persisted = {
            record["source_record_id"]: record for record in case_detail.linked_evidence_records
        }
        self.assertIn(
            f"endpoint-evidence://request/{action_request.action_request_id}/artifact/manifest-001",
            persisted,
        )
        self.assertIn(
            f"endpoint-evidence://request/{action_request.action_request_id}/artifact/binary-analysis-001",
            persisted,
        )

    def test_ingest_endpoint_evidence_artifacts_rejects_pending_approval_requests_without_writes(
        self,
    ) -> None:
        store, service, promoted_case, anchor_evidence_id, reviewed_at = (
            self._build_host_bound_case()
        )
        action_request = service.create_endpoint_evidence_collection_request(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence_id,
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need endpoint evidence to resolve the reviewed host-state gap.",
            artifact_classes=("collection_manifest",),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
        )
        before_ids = {record.evidence_id for record in store.list(EvidenceRecord)}

        with self.assertRaisesRegex(
            ValueError,
            "approved or executing endpoint evidence requests",
        ):
            service.ingest_endpoint_evidence_artifacts(
                action_request_id=action_request.action_request_id,
                artifacts=(
                    {
                        "artifact_class": "collection_manifest",
                        "artifact_id": "manifest-pending-001",
                        "source_artifact_id": "collector-manifest-pending-001",
                        "collected_at": reviewed_at,
                        "collector_identity": "velociraptor",
                        "tool_name": "Velociraptor",
                        "source_boundary": "endpoint_evidence_pack",
                        "citation_kind": "raw_collected_output",
                        "description": "Pending approval requests must stay blocked.",
                        "content": {"requested_paths": ("/opt/suspicious",)},
                    },
                ),
                admitted_by="analyst-001",
            )

        self.assertEqual(
            {record.evidence_id for record in store.list(EvidenceRecord)},
            before_ids,
        )

    def test_ingest_endpoint_evidence_artifacts_reuses_existing_records_on_retry(
        self,
    ) -> None:
        store, service, promoted_case, anchor_evidence_id, reviewed_at = (
            self._build_host_bound_case()
        )
        action_request = service.create_endpoint_evidence_collection_request(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence_id,
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need endpoint evidence to resolve the reviewed host-state gap.",
            artifact_classes=("collection_manifest",),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
        )
        self._approve_action_request(
            service,
            action_request.action_request_id,
            decided_at=action_request.requested_at + timedelta(minutes=5),
        )
        artifacts = (
            {
                "artifact_class": "collection_manifest",
                "artifact_id": "manifest-retry-001",
                "source_artifact_id": "collector-manifest-retry-001",
                "collected_at": reviewed_at,
                "collector_identity": "velociraptor",
                "tool_name": "Velociraptor",
                "source_boundary": "endpoint_evidence_pack",
                "citation_kind": "raw_collected_output",
                "description": "Retried endpoint evidence artifact.",
                "content": {"requested_paths": ("/opt/retry-sample",)},
            },
        )

        first_ingest = service.ingest_endpoint_evidence_artifacts(
            action_request_id=action_request.action_request_id,
            artifacts=artifacts,
            admitted_by="analyst-001",
        )
        second_ingest = service.ingest_endpoint_evidence_artifacts(
            action_request_id=action_request.action_request_id,
            artifacts=artifacts,
            admitted_by="analyst-001",
        )

        self.assertEqual(
            tuple(record.evidence_id for record in first_ingest),
            tuple(record.evidence_id for record in second_ingest),
        )
        case_detail = service.inspect_case_detail(promoted_case.case_id)
        persisted = [
            record
            for record in case_detail.linked_evidence_records
            if record["source_record_id"]
            == f"endpoint-evidence://request/{action_request.action_request_id}/artifact/manifest-retry-001"
        ]
        self.assertEqual(len(persisted), 1)
        self.assertEqual(
            {record.evidence_id for record in store.list(EvidenceRecord)},
            {
                promoted_case.evidence_ids[0],
                first_ingest[0].evidence_id,
            },
        )

    def test_ingest_endpoint_evidence_artifacts_rejects_unsupported_artifact_without_writes(
        self,
    ) -> None:
        inner_store, _service, _case, _anchor, _reviewed_at = self._build_host_bound_case()
        mutation_store = _EvidenceSaveMutationStore(
            inner=inner_store,
            mutate_once=lambda inner: inner.save(
                EvidenceRecord(
                    evidence_id="evidence-should-not-survive-001",
                    source_record_id="mutation-should-not-survive",
                    alert_id=None,
                    case_id="case-should-not-survive",
                    source_system="mutation-test",
                    collector_identity="mutation-test",
                    acquired_at=datetime(2026, 4, 19, 0, 10, tzinfo=timezone.utc),
                    derivation_relationship="mutation",
                    lifecycle_state="linked",
                    provenance={"classification": "mutation"},
                    content={"mutation": True},
                )
            ),
        )
        store, service, promoted_case, anchor_evidence_id, reviewed_at = (
            self._build_host_bound_case(store=mutation_store)
        )
        action_request = service.create_endpoint_evidence_collection_request(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence_id,
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need endpoint evidence to resolve the reviewed host-state gap.",
            artifact_classes=("collection_manifest",),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
        )
        self._approve_action_request(
            service,
            action_request.action_request_id,
            decided_at=action_request.requested_at + timedelta(minutes=5),
        )
        before_ids = {record.evidence_id for record in store.list(EvidenceRecord)}

        with self.assertRaisesRegex(
            ValueError,
            "artifact_class must be one of",
        ):
            service.ingest_endpoint_evidence_artifacts(
                action_request_id=action_request.action_request_id,
                artifacts=(
                    {
                        "artifact_class": "memory_dump",
                        "artifact_id": "artifact-unsupported-001",
                        "source_artifact_id": "collector-artifact-unsupported-001",
                        "collected_at": reviewed_at,
                        "collector_identity": "velociraptor",
                        "tool_name": "Velociraptor",
                        "source_boundary": "endpoint_evidence_pack",
                        "citation_kind": "raw_collected_output",
                        "description": "Unsupported artifact should fail closed.",
                        "content": {"bytes": "not-allowed"},
                    },
                ),
                admitted_by="analyst-001",
            )

        self.assertEqual(
            {record.evidence_id for record in store.list(EvidenceRecord)},
            before_ids,
        )


if __name__ == "__main__":
    unittest.main()
