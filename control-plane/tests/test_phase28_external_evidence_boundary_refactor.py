from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pathlib
import secrets
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops.control_plane.config import RuntimeConfig
from aegisops.control_plane.evidence import external_evidence_boundary
from aegisops.control_plane.evidence import external_evidence_endpoint
from aegisops.control_plane.evidence import external_evidence_facade
from aegisops.control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store


class Phase28ExternalEvidenceBoundaryRefactorTests(unittest.TestCase):
    def _build_service(self) -> AegisOpsControlPlaneService:
        store, _ = make_store()
        shared_secret = secrets.token_urlsafe(24)
        reverse_proxy_secret = secrets.token_urlsafe(24)
        return AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret=shared_secret,
                wazuh_ingest_reverse_proxy_secret=reverse_proxy_secret,
                misp_enrichment_enabled=True,
            ),
            store=store,
        )

    def test_attach_misp_context_delegates_to_external_evidence_boundary(self) -> None:
        service = self._build_service()
        looked_up_at = datetime(2026, 4, 19, 0, 0, tzinfo=timezone.utc)
        sentinel = (object(), object())
        observed: dict[str, object] = {}

        def fake_attach_misp_context(**kwargs: object) -> tuple[object, object]:
            observed.update(kwargs)
            return sentinel

        service._external_evidence_boundary.attach_misp_context = fake_attach_misp_context

        result = service.attach_misp_context(
            case_id="case-001",
            admitting_evidence_id="evidence-001",
            queried_object_type="domain",
            queried_object_value="malicious.example",
            looked_up_at=looked_up_at,
            reviewed_by="analyst-001",
            event_id="misp-event-001",
            event_info="Known phishing infrastructure",
            citation_url="https://misp.local/events/view/1",
            staleness_marker={
                "state": "fresh",
                "evaluated_at": looked_up_at.isoformat(),
            },
            observation_scope_statement="Reviewed and scoped to the admitted indicator.",
        )

        self.assertIs(result, sentinel)
        self.assertEqual(
            observed,
            {
                "case_id": "case-001",
                "admitting_evidence_id": "evidence-001",
                "queried_object_type": "domain",
                "queried_object_value": "malicious.example",
                "looked_up_at": looked_up_at,
                "reviewed_by": "analyst-001",
                "event_id": "misp-event-001",
                "event_info": "Known phishing infrastructure",
                "event_published_at": None,
                "iocs": (),
                "taxonomies": (),
                "warninglists": (),
                "galaxies": (),
                "sightings": (),
                "citation_url": "https://misp.local/events/view/1",
                "staleness_marker": {
                    "state": "fresh",
                    "evaluated_at": looked_up_at.isoformat(),
                },
                "conflict_marker": None,
                "evidence_id": None,
                "observation_scope_statement": (
                    "Reviewed and scoped to the admitted indicator."
                ),
                "observation_id": None,
            },
        )

    def test_attach_osquery_host_context_delegates_to_external_evidence_boundary(
        self,
    ) -> None:
        service = self._build_service()
        collected_at = datetime(2026, 4, 18, 0, 0, tzinfo=timezone.utc)
        rows = (
            {
                "pid": "123",
                "name": "sshd",
                "path": "/usr/sbin/sshd",
            },
        )
        query_context = {"pack": "osquery-defense", "platform": "linux"}
        sentinel = (object(), object())
        observed: dict[str, object] = {}

        def fake_attach_osquery_host_context(**kwargs: object) -> tuple[object, object]:
            observed.update(kwargs)
            return sentinel

        service._external_evidence_boundary.attach_osquery_host_context = (
            fake_attach_osquery_host_context
        )

        result = service.attach_osquery_host_context(
            case_id="case-001",
            host_identifier="host-001",
            query_name="running_processes",
            query_sql="SELECT pid, name, path FROM processes;",
            result_kind="process",
            rows=rows,
            collected_at=collected_at,
            reviewed_by="analyst-001",
            source_id="query-result-001",
            collection_path="pack/osquery-defense/processes/running_processes",
            query_context=query_context,
            evidence_id="evidence-osquery-001",
            observation_scope_statement=(
                "Observed reviewed osquery host context on the explicitly scoped host."
            ),
            observation_id="observation-osquery-001",
        )

        self.assertIs(result, sentinel)
        self.assertEqual(
            observed,
            {
                "case_id": "case-001",
                "host_identifier": "host-001",
                "query_name": "running_processes",
                "query_sql": "SELECT pid, name, path FROM processes;",
                "result_kind": "process",
                "rows": rows,
                "collected_at": collected_at,
                "reviewed_by": "analyst-001",
                "source_id": "query-result-001",
                "collection_path": (
                    "pack/osquery-defense/processes/running_processes"
                ),
                "query_context": query_context,
                "evidence_id": "evidence-osquery-001",
                "observation_scope_statement": (
                    "Observed reviewed osquery host context on the explicitly scoped host."
                ),
                "observation_id": "observation-osquery-001",
            },
        )

    def test_create_endpoint_request_delegates_to_external_evidence_boundary(self) -> None:
        service = self._build_service()
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        sentinel = object()
        observed: dict[str, object] = {}

        def fake_create_endpoint_evidence_collection_request(
            **kwargs: object,
        ) -> object:
            observed.update(kwargs)
            return sentinel

        service._external_evidence_boundary.create_endpoint_evidence_collection_request = (
            fake_create_endpoint_evidence_collection_request
        )

        result = service.create_endpoint_evidence_collection_request(
            case_id="case-001",
            admitting_evidence_id="evidence-001",
            requester_identity="analyst-001",
            host_identifier="host-001",
            evidence_gap="Need endpoint evidence.",
            artifact_classes=("collection_manifest", "file_sample"),
            expires_at=expires_at,
            reviewed_gap_id="gap-001",
            reviewed_follow_up_decision_id="approval-decision-001",
            action_request_id="action-request-001",
        )

        self.assertIs(result, sentinel)
        self.assertEqual(
            observed,
            {
                "case_id": "case-001",
                "admitting_evidence_id": "evidence-001",
                "requester_identity": "analyst-001",
                "host_identifier": "host-001",
                "evidence_gap": "Need endpoint evidence.",
                "artifact_classes": ("collection_manifest", "file_sample"),
                "expires_at": expires_at,
                "reviewed_gap_id": "gap-001",
                "reviewed_follow_up_decision_id": "approval-decision-001",
                "action_request_id": "action-request-001",
            },
        )

    def test_ingest_endpoint_artifacts_delegates_to_external_evidence_boundary(self) -> None:
        service = self._build_service()
        artifacts = (
            {
                "artifact_class": "collection_manifest",
                "artifact_id": "artifact-001",
            },
        )
        sentinel = (object(),)
        observed: dict[str, object] = {}

        def fake_ingest_endpoint_evidence_artifacts(**kwargs: object) -> tuple[object]:
            observed.update(kwargs)
            return sentinel

        service._external_evidence_boundary.ingest_endpoint_evidence_artifacts = (
            fake_ingest_endpoint_evidence_artifacts
        )

        result = service.ingest_endpoint_evidence_artifacts(
            action_request_id="action-request-001",
            artifacts=artifacts,
            admitted_by="analyst-001",
        )

        self.assertIs(result, sentinel)
        self.assertEqual(
            observed,
            {
                "action_request_id": "action-request-001",
                "artifacts": artifacts,
                "admitted_by": "analyst-001",
            },
        )

    def test_external_evidence_residual_helpers_are_not_owned_by_service(self) -> None:
        residual_helper_names = (
            "_normalize_misp_indicator_type",
            "_normalize_misp_indicator_value",
            "_mapping_matches_misp_indicator",
            "_container_explicitly_cites_misp_indicator",
            "_require_explicit_misp_anchor_binding",
            "_require_case_host_identifier",
        )

        for helper_name in residual_helper_names:
            with self.subTest(helper_name=helper_name):
                self.assertFalse(
                    hasattr(AegisOpsControlPlaneService, helper_name),
                    f"{helper_name} should be owned by the external evidence boundary",
                )

    def test_external_evidence_public_routes_are_not_defined_in_service_module(
        self,
    ) -> None:
        service_source = (
            CONTROL_PLANE_ROOT / "aegisops_control_plane" / "service.py"
        ).read_text(encoding="utf-8")
        facade_source = (
            CONTROL_PLANE_ROOT
            / "aegisops_control_plane"
            / "evidence"
            / "external_evidence_facade.py"
        ).read_text(encoding="utf-8")
        public_route_names = (
            "attach_misp_context",
            "attach_osquery_host_context",
            "create_endpoint_evidence_collection_request",
            "ingest_endpoint_evidence_artifacts",
        )

        self.assertTrue(
            issubclass(
                AegisOpsControlPlaneService,
                external_evidence_facade.ExternalEvidenceFacade,
            )
        )
        for route_name in public_route_names:
            with self.subTest(route_name=route_name):
                self.assertNotIn(f"    def {route_name}(", service_source)
                self.assertIn(f"    def {route_name}(", facade_source)

    def test_misp_and_osquery_helpers_are_extracted_from_boundary_module(self) -> None:
        extracted_helper_names = (
            "_normalize_misp_indicator_type",
            "_normalize_misp_indicator_value",
            "_mapping_matches_misp_indicator",
            "_container_explicitly_cites_misp_indicator",
            "_require_explicit_misp_anchor_binding",
            "_require_case_host_identifier",
            "require_case_host_identifier",
        )

        for helper_name in extracted_helper_names:
            with self.subTest(helper_name=helper_name):
                self.assertFalse(
                    hasattr(external_evidence_boundary, helper_name),
                    f"{helper_name} should be owned by focused external evidence modules",
                )

    def test_endpoint_evidence_helpers_are_extracted_from_boundary_module(self) -> None:
        self.assertTrue(
            hasattr(external_evidence_endpoint, "EndpointExternalEvidenceHelper")
        )

        residual_helper_names = (
            "_resolve_reviewed_endpoint_gap_anchor",
            "_resolve_reviewed_endpoint_follow_up_decision_anchor",
            "_index_endpoint_request_artifacts",
            "_resolve_binary_analysis_attachment",
        )
        for helper_name in residual_helper_names:
            with self.subTest(helper_name=helper_name):
                self.assertFalse(
                    hasattr(
                        external_evidence_boundary.ExternalEvidenceBoundary,
                        helper_name,
                    ),
                    f"{helper_name} should be owned by the endpoint evidence helper",
                )


if __name__ == "__main__":
    unittest.main()
