from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pathlib
import secrets
import sys


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import EvidenceRecord
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from tests.test_service_persistence import ServicePersistenceTestBase
from tests.support.fixtures import load_wazuh_fixture


class Phase28MispEnrichmentValidationTests(ServicePersistenceTestBase):
    def _build_in_scope_case(
        self,
        *,
        misp_enrichment_enabled: bool,
    ) -> tuple[object, AegisOpsControlPlaneService, object, str, datetime]:
        store, _ = make_store()
        shared_secret = secrets.token_urlsafe(24)
        reverse_proxy_secret = secrets.token_urlsafe(24)
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=shared_secret,
                wazuh_ingest_reverse_proxy_secret=reverse_proxy_secret,
                misp_enrichment_enabled=misp_enrichment_enabled,
            ),
            store=store,
        )
        admitted = service.ingest_wazuh_alert(
            raw_alert=load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {shared_secret}",
            forwarded_proto="https",
            reverse_proxy_secret_header=reverse_proxy_secret,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        reviewed_at = service.list_lifecycle_transitions("case", promoted_case.case_id)[
            -1
        ].transitioned_at
        return store, service, promoted_case, promoted_case.evidence_ids[0], reviewed_at

    def _attach_anchor_evidence(
        self,
        *,
        service: AegisOpsControlPlaneService,
        promoted_case: object,
        reviewed_at: datetime,
        indicator_type: str = "domain",
        indicator_value: str = "malicious.example",
    ) -> EvidenceRecord:
        anchor_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-misp-anchor-001",
                source_record_id="reviewed-fixture-anchor-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="reviewed_fixture",
                collector_identity="fixture://reviewed/anchor",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "reviewed-derived",
                    "source_id": "reviewed-anchor-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "indicator_type": indicator_type,
                    "indicator_value": indicator_value,
                },
                content={
                    "indicator": {
                        "type": indicator_type,
                        "value": indicator_value,
                    }
                },
            )
        )
        service.persist_record(
            replace(
                promoted_case,
                evidence_ids=(*promoted_case.evidence_ids, anchor_evidence.evidence_id),
            )
        )
        return anchor_evidence

    def test_attach_misp_context_persists_subordinate_attachment_with_provenance(
        self,
    ) -> None:
        store, service, promoted_case, _, reviewed_at = self._build_in_scope_case(
            misp_enrichment_enabled=True
        )
        anchor_evidence = self._attach_anchor_evidence(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
        )

        evidence, observation = service.attach_misp_context(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence.evidence_id,
            queried_object_type="domain",
            queried_object_value="malicious.example",
            looked_up_at=reviewed_at,
            reviewed_by="analyst-001",
            event_id="misp-event-001",
            event_info="Known phishing infrastructure",
            event_published_at=reviewed_at - timedelta(hours=1),
            iocs=(
                {
                    "type": "domain",
                    "value": "malicious.example",
                    "category": "Network activity",
                    "to_ids": True,
                },
            ),
            taxonomies=(
                {
                    "namespace": "tlp",
                    "predicate": "color",
                    "value": "amber",
                },
            ),
            warninglists=(
                {
                    "name": "Known phishing domains",
                    "match": "malicious.example",
                },
            ),
            galaxies=(
                {
                    "name": "Threat Actor",
                    "cluster": "Example Actor",
                },
            ),
            sightings=(
                {
                    "source": "partner-feed",
                    "count": 2,
                    "timestamp": reviewed_at.isoformat(),
                },
            ),
            citation_url="https://misp.example/events/view/1",
            staleness_marker={
                "state": "fresh",
                "evaluated_at": reviewed_at.isoformat(),
            },
            observation_scope_statement=(
                "Attached bounded MISP context to the reviewed domain indicator."
            ),
        )

        self.assertEqual(evidence.case_id, promoted_case.case_id)
        self.assertEqual(evidence.source_system, "misp")
        self.assertEqual(
            evidence.provenance["classification"],
            "augmenting-evidence",
        )
        self.assertEqual(evidence.provenance["adapter"], "misp_context")
        self.assertEqual(evidence.provenance["queried_object_type"], "domain")
        self.assertEqual(
            evidence.provenance["queried_object_value"],
            "malicious.example",
        )
        self.assertEqual(
            evidence.content["citation_attachment"]["url"],
            "https://misp.example/events/view/1",
        )
        self.assertEqual(evidence.content["source_observation"]["event_id"], "misp-event-001")
        self.assertEqual(
            evidence.content["source_observation"]["iocs"][0]["value"],
            "malicious.example",
        )
        self.assertEqual(
            evidence.content["staleness_marker"]["state"],
            "fresh",
        )
        self.assertIsNotNone(observation)
        assert observation is not None
        self.assertEqual(observation.case_id, promoted_case.case_id)
        self.assertEqual(observation.supporting_evidence_ids, (evidence.evidence_id,))

        current_case = service.inspect_case_detail(promoted_case.case_id)
        linked_evidence_ids = {
            record["evidence_id"] for record in current_case.linked_evidence_records
        }
        self.assertIn(evidence.evidence_id, linked_evidence_ids)
        self.assertIn(anchor_evidence.evidence_id, linked_evidence_ids)

    def test_attach_misp_context_preserves_stale_and_conflicting_markers(
        self,
    ) -> None:
        _store, service, promoted_case, _, reviewed_at = self._build_in_scope_case(
            misp_enrichment_enabled=True
        )
        anchor_evidence = self._attach_anchor_evidence(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            indicator_value="stale.example",
        )

        evidence, observation = service.attach_misp_context(
            case_id=promoted_case.case_id,
            admitting_evidence_id=anchor_evidence.evidence_id,
            queried_object_type="domain",
            queried_object_value="stale.example",
            looked_up_at=reviewed_at,
            reviewed_by="analyst-001",
            event_id="misp-event-002",
            event_info="Conflicting stale context",
            event_published_at=reviewed_at - timedelta(days=10),
            iocs=(
                {
                    "type": "domain",
                    "value": "stale.example",
                    "category": "Network activity",
                },
            ),
            taxonomies=(
                {
                    "namespace": "admiralty-scale",
                    "predicate": "source-reliability",
                    "value": "c",
                },
            ),
            citation_url="https://misp.example/events/view/2",
            staleness_marker={
                "state": "stale",
                "evaluated_at": reviewed_at.isoformat(),
                "reason": "event older than review threshold",
            },
            conflict_marker={
                "state": "conflict",
                "reason": "MISP taxonomy confidence disagrees with reviewed case context",
            },
        )

        self.assertIsNone(observation)
        self.assertEqual(evidence.content["staleness_marker"]["state"], "stale")
        self.assertEqual(evidence.content["conflict_marker"]["state"], "conflict")
        self.assertTrue(evidence.provenance["conflict_present"])
        self.assertEqual(evidence.provenance["ambiguity_badge"], "unresolved")

    def test_attach_misp_context_rejects_disabled_mode_without_writes(self) -> None:
        store, service, promoted_case, _, reviewed_at = self._build_in_scope_case(
            misp_enrichment_enabled=False
        )
        anchor_evidence = self._attach_anchor_evidence(
            service=service,
            promoted_case=promoted_case,
            reviewed_at=reviewed_at,
            indicator_value="disabled.example",
        )
        evidence_before = store.list(EvidenceRecord)

        with self.assertRaisesRegex(
            ValueError,
            "MISP subordinate enrichment is disabled",
        ):
            service.attach_misp_context(
                case_id=promoted_case.case_id,
                admitting_evidence_id=anchor_evidence.evidence_id,
                queried_object_type="domain",
                queried_object_value="disabled.example",
                looked_up_at=reviewed_at,
                reviewed_by="analyst-001",
                event_id="misp-event-disabled-001",
                event_info="Disabled mode should fail closed",
                iocs=(
                    {
                        "type": "domain",
                        "value": "disabled.example",
                    },
                ),
                citation_url="https://misp.example/events/view/3",
                staleness_marker={
                    "state": "fresh",
                    "evaluated_at": reviewed_at.isoformat(),
                },
            )

        self.assertEqual(store.list(EvidenceRecord), evidence_before)
