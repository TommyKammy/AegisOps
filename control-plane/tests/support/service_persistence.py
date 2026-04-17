from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pathlib
import secrets
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import (
    AITraceRecord,
    CaseRecord,
    EvidenceRecord,
    RecommendationRecord,
    ReconciliationRecord,
)
from aegisops_control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES,
)
from postgres_test_support import make_store

from support.fixtures import load_wazuh_fixture


class ServicePersistenceTestBase(unittest.TestCase):
    def _assert_authoritative_store_empty(self, store: object) -> None:
        for record_type in AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES:
            self.assertEqual(store.list(record_type), ())

    def _build_phase19_in_scope_case(
        self,
        *,
        store: object | None = None,
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
        reviewed_at = datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc)
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

    def _build_phase19_in_scope_alert_without_case(
        self,
        *,
        store: object | None = None,
    ) -> tuple[object, AegisOpsControlPlaneService, object, str, datetime]:
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
        admitted = service.ingest_wazuh_alert(
            raw_alert=load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {shared_secret}",
            forwarded_proto="https",
            reverse_proxy_secret_header=reverse_proxy_secret,
            peer_addr="127.0.0.1",
        )
        alert = admitted.alert
        evidence_records = tuple(
            evidence
            for evidence in store.list(EvidenceRecord)
            if evidence.alert_id == alert.alert_id
        )
        if not evidence_records:
            raise AssertionError("expected reviewed alert fixture to persist linked evidence")
        reviewed_at = service.list_lifecycle_transitions("alert", alert.alert_id)[
            -1
        ].transitioned_at
        return store, service, alert, evidence_records[0].evidence_id, reviewed_at

    def _build_phase19_out_of_scope_case(
        self,
        *,
        fixture_name: str,
    ) -> tuple[AegisOpsControlPlaneService, CaseRecord, str, datetime]:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        reviewed_at = datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc)
        adapter = WazuhAlertAdapter()
        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(load_wazuh_fixture(fixture_name)),
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id=f"evidence-{fixture_name}",
                source_record_id=admitted.alert.finding_id,
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="wazuh",
                collector_identity="collector://wazuh/replay",
                acquired_at=reviewed_at,
                derivation_relationship="native_detection_record",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        reviewed_at = service.list_lifecycle_transitions("case", promoted_case.case_id)[
            -1
        ].transitioned_at
        return service, promoted_case, admitted.alert.alert_id, reviewed_at

    def _build_phase19_out_of_scope_alert_without_case(
        self,
        *,
        fixture_name: str,
    ) -> tuple[AegisOpsControlPlaneService, object, str, datetime]:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        reviewed_at = datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc)
        adapter = WazuhAlertAdapter()
        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(load_wazuh_fixture(fixture_name)),
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id=f"evidence-{fixture_name}",
                source_record_id=admitted.alert.finding_id,
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="wazuh",
                collector_identity="collector://wazuh/replay",
                acquired_at=reviewed_at,
                derivation_relationship="native_detection_record",
                lifecycle_state="collected",
            )
        )
        reviewed_at = service.list_lifecycle_transitions("alert", admitted.alert.alert_id)[
            -1
        ].transitioned_at
        return service, admitted.alert, f"evidence-{fixture_name}", reviewed_at

    def _build_phase19_synthetic_out_of_scope_case(
        self,
    ) -> tuple[AegisOpsControlPlaneService, CaseRecord, datetime]:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        reviewed_at = datetime(2026, 4, 7, 9, 30, tzinfo=timezone.utc)
        admitted = service.ingest_finding_alert(
            finding_id="finding-phase19-synthetic-case-001",
            analytic_signal_id="signal-phase19-synthetic-case-001",
            substrate_detection_record_id="synthetic-phase19-case-record-001",
            correlation_key="claim:asset-phase19-synthetic-case-001:synthetic",
            first_seen_at=reviewed_at,
            last_seen_at=reviewed_at,
            reviewed_context={
                "asset": {"asset_id": "asset-phase19-synthetic-case-001"},
                "identity": {"identity_id": "principal-phase19-synthetic-case-001"},
                "source": {
                    "source_family": "synthetic_review_fixture",
                    "admission_kind": "synthetic",
                },
            },
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase19-synthetic-case-001",
                source_record_id=admitted.alert.finding_id,
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="synthetic",
                collector_identity="collector://synthetic/fixture",
                acquired_at=reviewed_at,
                derivation_relationship="finding_alert",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        reviewed_at = service.list_lifecycle_transitions("case", promoted_case.case_id)[
            -1
        ].transitioned_at
        return service, promoted_case, reviewed_at

    def _build_case_scoped_advisory_records_without_case_lineage(
        self,
    ) -> tuple[AegisOpsControlPlaneService, RecommendationRecord, AITraceRecord]:
        _, service, promoted_case, evidence_id, first_seen_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=first_seen_at,
            scope_statement="Case-scoped advisory reads must fail closed without case lineage.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Preserve reviewed lead linkage for bounded advisory rendering.",
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-lead-only-advisory-001",
                lead_id=lead.lead_id,
                hunt_run_id=None,
                alert_id=None,
                case_id=None,
                ai_trace_id=None,
                review_owner="analyst-001",
                intended_outcome="Review the lead linkage before any broader response.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-lead-only-advisory-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(),
                reviewer_identity="analyst-001",
                lifecycle_state="under_review",
            )
        )
        return service, recommendation, ai_trace

    def _assert_service_analyst_queue_prefers_wazuh_source_for_multi_source_linkage(
        self,
        *,
        wazuh_source_system: str,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(reconciliation)

        subject_linkage = dict(reconciliation.subject_linkage)
        subject_linkage["source_systems"] = ("opensearch", wazuh_source_system)
        service.persist_record(
            replace(reconciliation, subject_linkage=subject_linkage)
        )

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["source_system"], "wazuh")

    def _persist_newer_non_wazuh_detection_reconciliation(
        self,
    ) -> tuple[
        AegisOpsControlPlaneService,
        object,
        ReconciliationRecord,
        ReconciliationRecord,
    ]:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(reconciliation)

        subject_linkage = dict(reconciliation.subject_linkage)
        subject_linkage["source_systems"] = ("opensearch",)
        subject_linkage["substrate_detection_record_ids"] = (
            "opensearch:1731594986.4931506",
        )
        newer_non_wazuh_reconciliation = replace(
            reconciliation,
            reconciliation_id=f"{reconciliation.reconciliation_id}-opensearch",
            correlation_key=f"{reconciliation.correlation_key}:opensearch",
            compared_at=reconciliation.compared_at + timedelta(minutes=5),
            last_seen_at=(
                reconciliation.last_seen_at + timedelta(minutes=5)
                if reconciliation.last_seen_at is not None
                else None
            ),
            subject_linkage=subject_linkage,
        )
        service.persist_record(newer_non_wazuh_reconciliation)

        return (
            service,
            admitted,
            reconciliation,
            newer_non_wazuh_reconciliation,
        )
