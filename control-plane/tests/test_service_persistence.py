from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
import hashlib
import inspect
import json
import logging
import pathlib
import secrets
import sys
from typing import Callable, Iterator
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AnalyticSignalAdmission,
    AnalyticSignalRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    LeadRecord,
    NativeDetectionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from aegisops_control_plane.adapters.wazuh import WazuhAlertAdapter
from aegisops_control_plane.service import (
    AegisOpsControlPlaneService,
    AUTHORITATIVE_RECORD_CHAIN_RECORD_TYPES,
    NativeDetectionRecordAdapter,
)
from postgres_test_support import make_store


FIXTURES_ROOT = pathlib.Path(__file__).resolve().parent / "fixtures" / "wazuh"


def _load_wazuh_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURES_ROOT / name).read_text(encoding="utf-8"))


def _approved_binding_hash(
    *,
    target_scope: dict[str, object],
    approved_payload: dict[str, object],
    execution_surface_type: str,
    execution_surface_id: str,
) -> str:
    binding = {
        "approved_payload": approved_payload,
        "execution_surface_id": execution_surface_id,
        "execution_surface_type": execution_surface_type,
        "target_scope": target_scope,
    }
    encoded = json.dumps(binding, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _phase20_notify_identity_owner_payload(
    *,
    recipient_identity: str,
    case_id: str,
    alert_id: str,
    finding_id: str,
    source_record_family: str = "recommendation",
    source_record_id: str = "recommendation-001",
    recommendation_id: str = "recommendation-001",
    linked_evidence_ids: tuple[str, ...] = ("evidence-001",),
    message_intent: str = (
        "Notify the accountable owner about the reviewed low-risk escalation."
    ),
    escalation_reason: str = (
        "Reviewed evidence requires a bounded single-recipient owner notification."
    ),
) -> dict[str, object]:
    return {
        "action_type": "notify_identity_owner",
        "recipient_identity": recipient_identity,
        "message_intent": message_intent,
        "escalation_reason": escalation_reason,
        "source_record_family": source_record_family,
        "source_record_id": source_record_id,
        "recommendation_id": recommendation_id,
        "case_id": case_id,
        "alert_id": alert_id,
        "finding_id": finding_id,
        "linked_evidence_ids": linked_evidence_ids,
    }


@dataclass
class _TransactionMutationStore:
    inner: object
    mutate_once: Callable[[object], None]
    _mutated: bool = False

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def save(self, record: object) -> object:
        return self.inner.save(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        return self.inner.list(record_type)

    def inspect_readiness_aggregates(self) -> object:
        return self.inner.inspect_readiness_aggregates()

    @contextmanager
    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> Iterator[None]:
        with self.inner.transaction(isolation_level=isolation_level):
            if not self._mutated:
                self.mutate_once(self.inner)
                self._mutated = True
            yield


@dataclass
class _ConcurrentListMutationStore:
    inner: object
    mutate_once: Callable[[], None]
    _mutated: bool = False

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def save(self, record: object) -> object:
        return self.inner.save(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        records = self.inner.list(record_type)
        if not self._mutated:
            self.mutate_once()
            self._mutated = True
        return records

    def inspect_readiness_aggregates(self) -> object:
        aggregates = self.inner.inspect_readiness_aggregates()
        if not self._mutated:
            self.mutate_once()
            self._mutated = True
        return aggregates

    @contextmanager
    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> Iterator[None]:
        with self.inner.transaction(isolation_level=isolation_level):
            yield


@dataclass
class _CommitFailingStore:
    inner: object
    message: str = "synthetic commit failure"

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def save(self, record: object) -> object:
        return self.inner.save(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        return self.inner.list(record_type)

    def inspect_readiness_aggregates(self) -> object:
        return self.inner.inspect_readiness_aggregates()

    @contextmanager
    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> Iterator[None]:
        connection_factory = self.inner.connection_factory
        if connection_factory is None:
            raise AssertionError(
                "_CommitFailingStore requires an explicit connection factory"
            )

        def commit_failing_connection_factory(dsn: str) -> "_CommitFailingConnection":
            return _CommitFailingConnection(
                inner=connection_factory(dsn),
                message=self.message,
            )

        with mock.patch.object(
            self.inner,
            "connection_factory",
            commit_failing_connection_factory,
        ):
            with self.inner.transaction(isolation_level=isolation_level):
                yield


@dataclass
class _CommitFailingConnection:
    inner: object
    message: str

    def cursor(self) -> object:
        return self.inner.cursor()

    def commit(self) -> None:
        raise RuntimeError(self.message)

    def rollback(self) -> object:
        return self.inner.rollback()

    def close(self) -> object:
        return self.inner.close()


@dataclass
class _ListCountingStore:
    inner: object
    list_calls: int = 0
    reconciliation_list_calls: int = 0

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def save(self, record: object) -> object:
        return self.inner.save(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        self.list_calls += 1
        if record_type is ReconciliationRecord:
            self.reconciliation_list_calls += 1
        return self.inner.list(record_type)

    def inspect_readiness_aggregates(self) -> object:
        return self.inner.inspect_readiness_aggregates()

    @contextmanager
    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> Iterator[None]:
        with self.inner.transaction(isolation_level=isolation_level):
            yield


@dataclass
class _OutOfBandMutationStore:
    inner: object
    mutate_once: Callable[[object], None]
    _mutated: bool = False

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def save(self, record: object) -> object:
        return self.inner.save(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        return self.inner.list(record_type)

    def inspect_readiness_aggregates(self) -> object:
        return self.inner.inspect_readiness_aggregates()

    @contextmanager
    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> Iterator[None]:
        if not self._mutated:
            self.mutate_once(self.inner)
            self._mutated = True
        with self.inner.transaction(isolation_level=isolation_level):
            yield


class ControlPlaneServiceHelperLayoutTests(unittest.TestCase):
    def test_service_defines_require_non_empty_string_once(self) -> None:
        source = inspect.getsource(AegisOpsControlPlaneService)
        self.assertEqual(source.count("def _require_non_empty_string("), 1)


class ControlPlaneServicePersistenceTests(unittest.TestCase):
    def test_service_delegates_assistant_context_and_advisory_rendering_to_assembler(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        service._assistant_context_assembler = mock.Mock()
        service._assistant_context_assembler.inspect_assistant_context.return_value = (
            mock.sentinel.assistant_context_snapshot
        )
        service._assistant_context_assembler.inspect_advisory_output.return_value = (
            mock.sentinel.advisory_output_snapshot
        )
        service._assistant_context_assembler.render_recommendation_draft.return_value = (
            mock.sentinel.recommendation_draft_snapshot
        )

        self.assertIs(
            service.inspect_assistant_context("case", "case-delegated-001"),
            mock.sentinel.assistant_context_snapshot,
        )
        self.assertIs(
            service.inspect_advisory_output("case", "case-delegated-001"),
            mock.sentinel.advisory_output_snapshot,
        )
        self.assertIs(
            service.render_recommendation_draft("case", "case-delegated-001"),
            mock.sentinel.recommendation_draft_snapshot,
        )
        service._assistant_context_assembler.inspect_assistant_context.assert_called_once_with(
            "case",
            "case-delegated-001",
        )
        service._assistant_context_assembler.inspect_advisory_output.assert_called_once_with(
            "case",
            "case-delegated-001",
        )
        service._assistant_context_assembler.render_recommendation_draft.assert_called_once_with(
            "case",
            "case-delegated-001",
        )

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
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {shared_secret}",
            forwarded_proto="https",
            reverse_proxy_secret_header=reverse_proxy_secret,
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        return store, service, promoted_case, promoted_case.evidence_ids[0], reviewed_at

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
            adapter.build_native_detection_record(_load_wazuh_fixture(fixture_name)),
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
        return service, promoted_case, admitted.alert.alert_id, reviewed_at

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

    def test_service_admits_wazuh_fixture_through_substrate_adapter_boundary(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("agent-origin-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        self.assertEqual(admitted.disposition, "created")
        self.assertIsNotNone(admitted.alert.analytic_signal_id)
        self.assertEqual(
            admitted.alert.finding_id,
            "finding:wazuh:rule:5710:source:agent:007:alert:1731594986.4931506",
        )
        self.assertTrue(
            admitted.alert.analytic_signal_id.startswith("analytic-signal-")
        )

        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].substrate_detection_record_id,
            "wazuh:1731594986.4931506",
        )
        self.assertEqual(
            signals[0].correlation_key,
            (
                "wazuh:rule:5710:source:agent:007"
                ":location=%2Fvar%2Flog%2Fauth.log"
                ":data.srcip=198.51.100.24"
                ":data.srcuser=invalid-user"
            ),
        )
        self.assertEqual(
            signals[0].first_seen_at,
            datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(
            signals[0].last_seen_at,
            datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(signals[0].alert_ids, (admitted.alert.alert_id,))

        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(reconciliation.ingest_disposition, "created")
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731594986.4931506",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            (admitted.alert.analytic_signal_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "/var/log/auth.log",
                "data.srcip": "198.51.100.24",
                "data.srcuser": "invalid-user",
            },
        )
        self.assertEqual(
            reconciliation.subject_linkage["admission_provenance"],
            {
                "admission_channel": "fixture_replay",
                "admission_kind": "replay",
            },
        )
        self.assertEqual(
            admitted.alert.reviewed_context,
            {
                "location": "/var/log/auth.log",
                "data.srcip": "198.51.100.24",
                "data.srcuser": "invalid-user",
                "provenance": {
                    "admission_kind": "replay",
                    "admission_channel": "fixture_replay",
                },
            },
        )

    def test_service_preserves_reviewed_context_across_identity_centric_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "asset_type": "repository",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-001",
                "identity_type": "service_account",
                "aliases": ("svc-001",),
                "owner": "identity-operations",
            },
            "privilege": {
                "privilege_scope": "repository_admin",
                "delegated_authority": "reviewed",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-identity-001",
            analytic_signal_id="signal-identity-001",
            substrate_detection_record_id="substrate-detection-identity-001",
            correlation_key="claim:asset-repo-001:privilege-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-identity-001",
                source_record_id="substrate-detection-identity-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-identity-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="approve reviewed identity-sensitive follow-up",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )

        self.assertEqual(admitted.alert.reviewed_context, reviewed_context)
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, admitted.alert.analytic_signal_id).reviewed_context,
            reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            reviewed_context,
        )
        self.assertEqual(
            service.get_record(CaseRecord, promoted_case.case_id).reviewed_context,
            reviewed_context,
        )
        self.assertEqual(
            service.get_record(RecommendationRecord, recommendation.recommendation_id).reviewed_context,
            reviewed_context,
        )

    def test_service_exposes_analyst_assistant_context_with_linked_evidence(self) -> None:
        _, service, promoted_case, evidence_id, first_seen_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-assistant-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="follow reviewed evidence",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        colliding_recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id=promoted_case.case_id,
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-002",
                intended_outcome="keep reviewed evidence visible",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        colliding_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id=promoted_case.case_id,
                subject_linkage={
                    "alert_ids": (promoted_case.alert_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-collision-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:case-collision",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
                ingest_disposition="matched",
                mismatch_summary="case-id collision across record families",
                compared_at=first_seen_at,
                lifecycle_state="matched",
            )
        )

        snapshot = service.inspect_assistant_context("case", promoted_case.case_id)

        self.assertTrue(snapshot.read_only)
        self.assertEqual(snapshot.record_family, "case")
        self.assertEqual(snapshot.record_id, promoted_case.case_id)
        self.assertEqual(snapshot.record["case_id"], promoted_case.case_id)
        self.assertEqual(snapshot.reviewed_context, promoted_case.reviewed_context)
        self.assertEqual(snapshot.linked_evidence_ids, (evidence_id,))
        self.assertEqual(
            snapshot.linked_evidence_records[0]["evidence_id"],
            evidence_id,
        )
        self.assertEqual(
            snapshot.linked_evidence_records[0]["alert_id"],
            promoted_case.alert_id,
        )
        self.assertIn(promoted_case.alert_id, snapshot.linked_alert_ids)
        self.assertIn(
            recommendation.recommendation_id,
            snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            colliding_recommendation.recommendation_id,
            snapshot.linked_recommendation_ids,
        )
        self.assertTrue(snapshot.linked_reconciliation_ids)
        self.assertIn(
            colliding_reconciliation.reconciliation_id,
            snapshot.linked_reconciliation_ids,
        )

    def test_service_exposes_citation_ready_context_for_recommendation_and_ai_trace(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-citation-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-citation-001",
                "owner": "identity-operations",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-citation-001",
            analytic_signal_id="signal-citation-001",
            substrate_detection_record_id="substrate-detection-citation-001",
            correlation_key="claim:asset-repo-citation-001:assistant-citation-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-citation-001",
                source_record_id="substrate-detection-citation-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-citation-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-citation-001",
                review_owner="reviewer-001",
                intended_outcome="draft advisory triage summary",
                lifecycle_state="under_review",
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-citation-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(evidence.evidence_id, recommendation.recommendation_id),
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
            )
        )

        recommendation_snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )
        ai_trace_snapshot = service.inspect_assistant_context("ai_trace", ai_trace.ai_trace_id)

        self.assertEqual(recommendation_snapshot.reviewed_context, reviewed_context)
        self.assertEqual(
            recommendation_snapshot.linked_evidence_ids,
            (evidence.evidence_id,),
        )
        self.assertEqual(
            recommendation_snapshot.linked_evidence_records[0]["evidence_id"],
            evidence.evidence_id,
        )
        self.assertIn(admitted.alert.alert_id, recommendation_snapshot.linked_alert_ids)
        self.assertIn(promoted_case.case_id, recommendation_snapshot.linked_case_ids)
        self.assertEqual(
            recommendation_snapshot.linked_alert_records[0]["alert_id"],
            admitted.alert.alert_id,
        )
        self.assertEqual(
            recommendation_snapshot.linked_case_records[0]["case_id"],
            promoted_case.case_id,
        )

        self.assertEqual(ai_trace_snapshot.reviewed_context, reviewed_context)
        self.assertIn(
            recommendation.recommendation_id,
            ai_trace_snapshot.linked_recommendation_ids,
        )
        self.assertIn(admitted.alert.alert_id, ai_trace_snapshot.linked_alert_ids)
        self.assertIn(promoted_case.case_id, ai_trace_snapshot.linked_case_ids)
        self.assertEqual(
            ai_trace_snapshot.linked_alert_records[0]["alert_id"],
            admitted.alert.alert_id,
        )
        self.assertEqual(
            ai_trace_snapshot.linked_case_records[0]["case_id"],
            promoted_case.case_id,
        )
        self.assertEqual(
            set(ai_trace_snapshot.linked_evidence_ids),
            {evidence.evidence_id},
        )
        self.assertEqual(
            {record["evidence_id"] for record in ai_trace_snapshot.linked_evidence_records},
            {evidence.evidence_id},
        )
        self.assertEqual(
            recommendation_snapshot.advisory_output["output_kind"],
            "recommendation_draft",
        )
        self.assertEqual(
            recommendation_snapshot.advisory_output["status"],
            "ready",
        )
        self.assertIn(
            recommendation.recommendation_id,
            recommendation_snapshot.advisory_output["citations"],
        )
        self.assertIn(
            evidence.evidence_id,
            recommendation_snapshot.advisory_output["citations"],
        )
        self.assertTrue(
            recommendation_snapshot.advisory_output["cited_summary"]["text"]
        )
        self.assertTrue(
            recommendation_snapshot.advisory_output["candidate_recommendations"]
        )
        self.assertIn(
            "advisory_only",
            recommendation_snapshot.advisory_output["uncertainty_flags"],
        )

    def test_service_projects_assistant_context_into_advisory_and_draft_views(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-projection-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        advisory_snapshot = service.inspect_advisory_output("case", promoted_case.case_id)
        recommendation_draft = service.render_recommendation_draft(
            "case",
            promoted_case.case_id,
        )

        self.assertTrue(advisory_snapshot.read_only)
        self.assertEqual(advisory_snapshot.record_family, "case")
        self.assertEqual(advisory_snapshot.record_id, promoted_case.case_id)
        self.assertEqual(advisory_snapshot.output_kind, "case_summary")
        self.assertEqual(advisory_snapshot.status, "ready")
        self.assertEqual(advisory_snapshot.reviewed_context, promoted_case.reviewed_context)
        self.assertIn(evidence_id, advisory_snapshot.citations)
        self.assertIn("advisory_only", advisory_snapshot.uncertainty_flags)
        self.assertIn(promoted_case.alert_id, advisory_snapshot.linked_alert_ids)
        self.assertEqual(advisory_snapshot.linked_evidence_ids, (evidence_id,))
        self.assertIn(
            recommendation.recommendation_id,
            advisory_snapshot.linked_recommendation_ids,
        )
        self.assertTrue(advisory_snapshot.linked_reconciliation_ids)

        self.assertTrue(recommendation_draft.read_only)
        self.assertEqual(
            recommendation_draft.recommendation_draft["source_output_kind"],
            "case_summary",
        )
        self.assertEqual(
            recommendation_draft.recommendation_draft["status"],
            "ready",
        )
        self.assertTrue(
            recommendation_draft.recommendation_draft["candidate_recommendations"]
        )
        self.assertIn(
            evidence_id,
            recommendation_draft.recommendation_draft["citations"],
        )
        self.assertIn(
            "advisory_only",
            recommendation_draft.recommendation_draft["uncertainty_flags"],
        )
        self.assertEqual(
            recommendation_draft.reviewed_context,
            promoted_case.reviewed_context,
        )
        self.assertEqual(
            recommendation_draft.linked_evidence_ids,
            (evidence_id,),
        )
        self.assertIn(
            recommendation.recommendation_id,
            recommendation_draft.linked_recommendation_ids,
        )

    def test_service_materializes_assistant_advisory_drafts_on_review_records(self) -> None:
        _, service, promoted_case, evidence_id, first_seen_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-advisory-review-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-advisory-review-001",
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-advisory-review-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        attached_recommendation = service.attach_assistant_advisory_draft(
            "recommendation",
            recommendation.recommendation_id,
        )
        attached_ai_trace = service.attach_assistant_advisory_draft(
            "ai_trace",
            ai_trace.ai_trace_id,
        )

        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["draft_id"],
            "assistant-advisory-draft:recommendation:recommendation-advisory-review-001",
        )
        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["source_record_family"],
            "recommendation",
        )
        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["source_record_id"],
            recommendation.recommendation_id,
        )
        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["review_lifecycle_state"],
            "under_review",
        )
        self.assertEqual(
            attached_recommendation.assistant_advisory_draft["status"],
            "ready",
        )
        self.assertIn(
            evidence_id,
            attached_recommendation.assistant_advisory_draft["citations"],
        )

        self.assertEqual(
            attached_ai_trace.assistant_advisory_draft["draft_id"],
            "assistant-advisory-draft:ai_trace:ai-trace-advisory-review-001",
        )
        self.assertEqual(
            attached_ai_trace.assistant_advisory_draft["source_record_family"],
            "ai_trace",
        )
        self.assertEqual(
            attached_ai_trace.assistant_advisory_draft["source_record_id"],
            ai_trace.ai_trace_id,
        )
        self.assertEqual(
            attached_ai_trace.assistant_advisory_draft["review_lifecycle_state"],
            "under_review",
        )
        self.assertIn(
            recommendation.recommendation_id,
            attached_ai_trace.assistant_advisory_draft["citations"],
        )

        accepted_recommendation = service.persist_record(
            replace(attached_recommendation, lifecycle_state="accepted")
        )
        rejected_ai_trace = service.persist_record(
            replace(attached_ai_trace, lifecycle_state="rejected_for_reference")
        )

        self.assertEqual(
            accepted_recommendation.assistant_advisory_draft["review_lifecycle_state"],
            "under_review",
        )
        self.assertEqual(
            rejected_ai_trace.assistant_advisory_draft["review_lifecycle_state"],
            "under_review",
        )
        self.assertEqual(
            service.get_record(
                RecommendationRecord,
                recommendation.recommendation_id,
            ).assistant_advisory_draft["draft_id"],
            "assistant-advisory-draft:recommendation:recommendation-advisory-review-001",
        )
        self.assertEqual(
            service.get_record(
                AITraceRecord,
                ai_trace.ai_trace_id,
            ).assistant_advisory_draft["draft_id"],
            "assistant-advisory-draft:ai_trace:ai-trace-advisory-review-001",
        )

    def test_service_preserves_prior_assistant_advisory_draft_revisions_on_repeat_attachment(
        self,
    ) -> None:
        _, service, promoted_case, _, first_seen_at = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-advisory-history-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the draft history",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        initial_attachment = service.attach_assistant_advisory_draft(
            "recommendation",
            recommendation.recommendation_id,
        )
        initial_snapshot = dict(initial_attachment.assistant_advisory_draft)

        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-advisory-history-001",
                source_record_id="artifact-advisory-history-001",
                alert_id=recommendation.alert_id,
                case_id=recommendation.case_id,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="original",
                lifecycle_state="collected",
            )
        )

        updated_attachment = service.attach_assistant_advisory_draft(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertIn(
            evidence.evidence_id,
            updated_attachment.assistant_advisory_draft["citations"],
        )
        self.assertEqual(
            updated_attachment.assistant_advisory_draft["revision_history"][0],
            initial_snapshot,
        )

    def test_service_renders_recommendation_draft_with_current_review_outcome(self) -> None:
        _, service, promoted_case, evidence_id, first_seen_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-advisory-render-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-advisory-render-001",
                review_owner="reviewer-001",
                intended_outcome="review the cited evidence before escalation",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-advisory-render-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        recommendation_under_review = service.render_recommendation_draft(
            "recommendation",
            recommendation.recommendation_id,
        )
        ai_trace_under_review = service.render_recommendation_draft(
            "ai_trace",
            ai_trace.ai_trace_id,
        )

        self.assertIn(
            "remains under review",
            recommendation_under_review.recommendation_draft["cited_summary"]["text"],
        )
        self.assertIn(
            "remains under review",
            ai_trace_under_review.recommendation_draft["cited_summary"]["text"],
        )

        accepted_recommendation = service.persist_record(
            replace(recommendation, lifecycle_state="accepted")
        )
        rejected_ai_trace = service.persist_record(
            replace(ai_trace, lifecycle_state="rejected_for_reference")
        )

        accepted_recommendation_draft = service.render_recommendation_draft(
            "recommendation",
            accepted_recommendation.recommendation_id,
        )
        rejected_ai_trace_draft = service.render_recommendation_draft(
            "ai_trace",
            rejected_ai_trace.ai_trace_id,
        )

        self.assertIn(
            "has been accepted and is anchored",
            accepted_recommendation_draft.recommendation_draft["cited_summary"]["text"],
        )
        self.assertEqual(
            accepted_recommendation_draft.recommendation_draft["review_lifecycle_state"],
            "accepted",
        )
        self.assertNotIn(
            "remains under review",
            accepted_recommendation_draft.recommendation_draft["cited_summary"]["text"],
        )
        self.assertIn(
            "has been rejected for reference",
            rejected_ai_trace_draft.recommendation_draft["cited_summary"]["text"],
        )
        self.assertEqual(
            rejected_ai_trace_draft.recommendation_draft["review_lifecycle_state"],
            "rejected_for_reference",
        )
        self.assertNotIn(
            "remains under review",
            rejected_ai_trace_draft.recommendation_draft["cited_summary"]["text"],
        )

    def test_service_rejects_case_scoped_advisory_reads_without_linked_case(
        self,
    ) -> None:
        service, recommendation, ai_trace = (
            self._build_case_scoped_advisory_records_without_case_lineage()
        )

        for record_family, record_id in (
            ("recommendation", recommendation.recommendation_id),
            ("ai_trace", ai_trace.ai_trace_id),
        ):
            with self.subTest(record_family=record_family):
                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.inspect_advisory_output(record_family, record_id)

                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.render_recommendation_draft(record_family, record_id)

    def test_service_includes_evidence_derived_recommendations_in_ai_trace_context(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {"asset_id": "asset-ai-trace-evidence-001"},
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-ai-trace-evidence-001",
            analytic_signal_id="signal-ai-trace-evidence-001",
            substrate_detection_record_id="substrate-detection-ai-trace-evidence-001",
            correlation_key="claim:ai-trace:evidence:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-ai-trace-evidence-001",
                source_record_id="substrate-detection-ai-trace-evidence-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="detached_review_input",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-ai-trace-evidence-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="use evidence-derived lineage",
                lifecycle_state="under_review",
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-evidence-001",
                subject_linkage={
                    "evidence_ids": (evidence.evidence_id,),
                },
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(evidence.evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
            )
        )

        snapshot = service.inspect_assistant_context("ai_trace", ai_trace.ai_trace_id)

        self.assertIn(recommendation.recommendation_id, snapshot.linked_recommendation_ids)
        self.assertEqual(snapshot.reviewed_context, reviewed_context)
        self.assertIn(admitted.alert.alert_id, snapshot.linked_alert_ids)
        self.assertIn(promoted_case.case_id, snapshot.linked_case_ids)
        self.assertEqual(
            snapshot.linked_alert_records[0]["alert_id"],
            admitted.alert.alert_id,
        )
        self.assertEqual(
            snapshot.linked_case_records[0]["case_id"],
            promoted_case.case_id,
        )
        self.assertEqual(
            {record["evidence_id"] for record in snapshot.linked_evidence_records},
            {evidence.evidence_id},
        )

    def test_service_fails_closed_when_reviewed_context_is_internally_inconsistent(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-conflict-001",
            analytic_signal_id="signal-conflict-001",
            substrate_detection_record_id="substrate-detection-conflict-001",
            correlation_key="claim:conflict:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={
                "asset": {"asset_id": "asset-reviewed-001"},
            },
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-conflict-001",
                source_record_id="substrate-detection-conflict-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-conflict-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the conflicting identifiers",
                lifecycle_state="under_review",
                reviewed_context={
                    "asset": {"asset_id": "asset-reviewed-999"},
                },
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(snapshot.linked_evidence_ids, (evidence.evidence_id,))
        self.assertEqual(snapshot.advisory_output["status"], "unresolved")
        self.assertIn(
            "conflicting_reviewed_context",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertIn(
            "asset.asset_id",
            snapshot.advisory_output["unresolved_questions"][0]["text"],
        )

    def test_service_fails_closed_when_identity_context_is_alias_only(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-alias-only-001",
            analytic_signal_id="signal-alias-only-001",
            substrate_detection_record_id="substrate-detection-alias-only-001",
            correlation_key="claim:alias-only:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={
                "identity": {
                    "aliases": ("svc-prod-shared",),
                },
            },
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-alias-only-001",
                source_record_id="substrate-detection-alias-only-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-alias-only-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="review the cited identity lineage",
                lifecycle_state="under_review",
                reviewed_context={
                    "identity": {
                        "aliases": ("svc-prod-shared",),
                    },
                },
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(snapshot.advisory_output["status"], "unresolved")
        self.assertIn(
            "ambiguous_identity_alias_only",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertTrue(
            any(
                "stable identity identifier" in question.get("text", "")
                for question in snapshot.advisory_output["unresolved_questions"]
            )
        )

    def test_service_fails_closed_when_recommendation_text_claims_authority_or_scope_expansion(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-overreach-001",
            analytic_signal_id="signal-overreach-001",
            substrate_detection_record_id="substrate-detection-overreach-001",
            correlation_key="claim:overreach:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={
                "asset": {"asset_id": "asset-overreach-001"},
                "identity": {"identity_id": "principal-overreach-001"},
            },
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-overreach-001",
                source_record_id="substrate-detection-overreach-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-overreach-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome=(
                    "Approval granted to execute tenant-wide containment and reconcile "
                    "the incident as closed."
                ),
                lifecycle_state="under_review",
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(snapshot.linked_evidence_ids, (evidence.evidence_id,))
        self.assertEqual(snapshot.advisory_output["status"], "unresolved")
        self.assertIn(
            "authority_overreach",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertIn(
            "scope_expansion_attempt",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertTrue(
            all(
                "Approval granted" not in candidate.get("text", "")
                for candidate in snapshot.advisory_output.get(
                    "candidate_recommendations",
                    (),
                )
            )
        )

    def test_service_does_not_treat_unresolved_as_resolution_authority(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-unresolved-001",
            analytic_signal_id="signal-unresolved-001",
            substrate_detection_record_id="substrate-detection-unresolved-001",
            correlation_key="claim:unresolved:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={
                "asset": {"asset_id": "asset-unresolved-001"},
                "identity": {"identity_id": "principal-unresolved-001"},
            },
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-unresolved-001",
                source_record_id="substrate-detection-unresolved-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-unresolved-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="keep unresolved evidence visible",
                lifecycle_state="under_review",
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            recommendation.recommendation_id,
        )

        self.assertEqual(snapshot.advisory_output["status"], "ready")
        self.assertNotIn(
            "authority_overreach",
            snapshot.advisory_output["uncertainty_flags"],
        )
        self.assertTrue(
            any(
                "keep unresolved evidence visible" in candidate.get("text", "")
                for candidate in snapshot.advisory_output["candidate_recommendations"]
            )
        )

    def test_service_keeps_anchored_recommendation_context_from_absorbing_sibling_anchors(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        first_admitted = service.ingest_finding_alert(
            finding_id="finding-anchored-001",
            analytic_signal_id="signal-anchored-001",
            substrate_detection_record_id="substrate-detection-anchored-001",
            correlation_key="claim:anchored:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={"asset": {"asset_id": "asset-anchored-001"}},
        )
        first_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-anchored-001",
                source_record_id="substrate-detection-anchored-001",
                alert_id=first_admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        first_case = service.promote_alert_to_case(first_admitted.alert.alert_id)
        anchored_recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-anchored-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=first_admitted.alert.alert_id,
                case_id=first_case.case_id,
                ai_trace_id="ai-trace-shared-001",
                review_owner="reviewer-001",
                intended_outcome="keep the anchored context narrow",
                lifecycle_state="under_review",
            )
        )

        second_admitted = service.ingest_finding_alert(
            finding_id="finding-anchored-002",
            analytic_signal_id="signal-anchored-002",
            substrate_detection_record_id="substrate-detection-anchored-002",
            correlation_key="claim:anchored:002",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={"asset": {"asset_id": "asset-anchored-002"}},
        )
        second_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-anchored-002",
                source_record_id="substrate-detection-anchored-002",
                alert_id=second_admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        second_case = service.promote_alert_to_case(second_admitted.alert.alert_id)
        sibling_recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-anchored-002",
                lead_id=None,
                hunt_run_id=None,
                alert_id=second_admitted.alert.alert_id,
                case_id=second_case.case_id,
                ai_trace_id="ai-trace-shared-001",
                review_owner="reviewer-002",
                intended_outcome="different anchored lineage",
                lifecycle_state="under_review",
            )
        )

        snapshot = service.inspect_assistant_context(
            "recommendation",
            anchored_recommendation.recommendation_id,
        )

        self.assertIn(first_admitted.alert.alert_id, snapshot.linked_alert_ids)
        self.assertIn(first_case.case_id, snapshot.linked_case_ids)
        self.assertEqual(
            snapshot.linked_evidence_ids,
            (first_evidence.evidence_id,),
        )
        self.assertIn(
            sibling_recommendation.recommendation_id,
            snapshot.linked_recommendation_ids,
        )
        self.assertNotIn(second_admitted.alert.alert_id, snapshot.linked_alert_ids)
        self.assertNotIn(second_case.case_id, snapshot.linked_case_ids)
        self.assertNotIn(second_evidence.evidence_id, snapshot.linked_evidence_ids)

    def test_service_uses_ai_trace_subject_linkage_and_material_inputs_for_citation_context(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-ai-trace-001",
            analytic_signal_id="signal-ai-trace-001",
            substrate_detection_record_id="substrate-detection-ai-trace-001",
            correlation_key="claim:ai-trace:001",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context={"asset": {"asset_id": "asset-ai-trace-001"}},
        )
        detached_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-ai-trace-001",
                source_record_id="substrate-detection-ai-trace-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="detached_review_input",
                lifecycle_state="collected",
            )
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-ai-trace-001",
                lead_id="lead-ai-trace-001",
                hunt_run_id=None,
                alert_id=None,
                case_id=None,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="use detached evidence in advisory context",
                lifecycle_state="under_review",
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-001",
                subject_linkage={
                    "recommendation_ids": (recommendation.recommendation_id,),
                    "evidence_ids": (detached_evidence.evidence_id,),
                },
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=first_seen_at,
                material_input_refs=(detached_evidence.evidence_id,),
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
            )
        )

        snapshot = service.inspect_assistant_context("ai_trace", ai_trace.ai_trace_id)

        self.assertIn(recommendation.recommendation_id, snapshot.linked_recommendation_ids)
        self.assertEqual(
            snapshot.linked_evidence_ids,
            (detached_evidence.evidence_id,),
        )
        self.assertEqual(
            snapshot.linked_evidence_records[0]["evidence_id"],
            detached_evidence.evidence_id,
        )

    def test_service_exposes_assistant_context_for_action_approvals_and_executions(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-approval-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-approval-001",
                "owner": "identity-operations",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-assistant-approval-001",
            analytic_signal_id="signal-assistant-approval-001",
            substrate_detection_record_id="substrate-detection-assistant-approval-001",
            correlation_key="claim:asset-repo-approval-001:assistant-approval-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-assistant-approval-001",
                source_record_id="substrate-detection-assistant-approval-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-assistant-approval-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="follow reviewed evidence",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )
        approval_target_scope = {"asset_id": "asset-repo-approval-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id=promoted_case.case_id,
            alert_id=admitted.alert.alert_id,
            finding_id=admitted.alert.finding_id,
            source_record_id=recommendation.recommendation_id,
            recommendation_id=recommendation.recommendation_id,
            linked_evidence_ids=(evidence.evidence_id,),
        )
        payload_hash = _approved_binding_hash(
            target_scope=approval_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-assistant-approval-001",
                action_request_id="action-request-assistant-approval-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=first_seen_at,
                lifecycle_state="approved",
            )
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-assistant-approval-001",
                approval_decision_id=approval_decision.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                idempotency_key="idempotency-assistant-approval-001",
                target_scope=approval_target_scope,
                payload_hash=payload_hash,
                requested_at=first_seen_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=action_request.action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-assistant-approval-missing-001",),
        )

        approval_snapshot = service.inspect_assistant_context(
            "approval_decision",
            approval_decision.approval_decision_id,
        )
        execution_snapshot = service.inspect_assistant_context(
            "action_execution",
            execution.action_execution_id,
        )
        action_request_snapshot = service.inspect_assistant_context(
            "action_request",
            action_request.action_request_id,
        )
        reconciliation_snapshot = service.inspect_assistant_context(
            "reconciliation",
            admitted.reconciliation.reconciliation_id,
        )

        self.assertTrue(approval_snapshot.read_only)
        self.assertEqual(approval_snapshot.linked_alert_ids, (admitted.alert.alert_id,))
        self.assertEqual(approval_snapshot.linked_case_ids, (promoted_case.case_id,))
        self.assertEqual(approval_snapshot.linked_evidence_ids, (evidence.evidence_id,))
        self.assertEqual(
            approval_snapshot.linked_evidence_records[0]["evidence_id"],
            evidence.evidence_id,
        )
        self.assertIn(
            recommendation.recommendation_id,
            approval_snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            approval_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(approval_snapshot.reviewed_context, reviewed_context)
        self.assertEqual(action_request_snapshot.reviewed_context, reviewed_context)

        self.assertTrue(execution_snapshot.read_only)
        self.assertEqual(execution_snapshot.reviewed_context, reviewed_context)
        self.assertEqual(execution_snapshot.linked_alert_ids, (admitted.alert.alert_id,))
        self.assertEqual(execution_snapshot.linked_case_ids, (promoted_case.case_id,))
        self.assertEqual(
            execution_snapshot.linked_evidence_ids,
            (
                "evidence-assistant-approval-missing-001",
                evidence.evidence_id,
            ),
        )
        self.assertEqual(len(execution_snapshot.linked_evidence_records), 1)
        self.assertEqual(
            execution_snapshot.linked_evidence_records[0]["evidence_id"],
            evidence.evidence_id,
        )
        self.assertIn(
            recommendation.recommendation_id,
            execution_snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(reconciliation_snapshot.reviewed_context, reviewed_context)

    def test_service_matches_reconciliations_via_direct_action_linkage(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-reconciliation-001",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-reconciliation-001",
                "owner": "identity-operations",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-assistant-reconciliation-001",
            analytic_signal_id="signal-assistant-reconciliation-001",
            substrate_detection_record_id="substrate-detection-assistant-reconciliation-001",
            correlation_key="claim:asset-repo-reconciliation-001:assistant-reconciliation-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-assistant-reconciliation-001",
                source_record_id="substrate-detection-assistant-reconciliation-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-assistant-reconciliation-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=admitted.alert.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id=None,
                review_owner="reviewer-001",
                intended_outcome="follow reviewed evidence",
                lifecycle_state="under_review",
                reviewed_context=reviewed_context,
            )
        )
        approval_target_scope = {"asset_id": "asset-repo-reconciliation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id=promoted_case.case_id,
            alert_id=admitted.alert.alert_id,
            finding_id=admitted.alert.finding_id,
            source_record_id=recommendation.recommendation_id,
            recommendation_id=recommendation.recommendation_id,
            linked_evidence_ids=("evidence-assistant-reconciliation-001",),
        )
        payload_hash = _approved_binding_hash(
            target_scope=approval_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-assistant-reconciliation-001",
                action_request_id="action-request-assistant-reconciliation-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=first_seen_at,
                lifecycle_state="approved",
            )
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-assistant-reconciliation-001",
                approval_decision_id=approval_decision.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                idempotency_key="idempotency-assistant-reconciliation-001",
                target_scope=approval_target_scope,
                payload_hash=payload_hash,
                requested_at=first_seen_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=action_request.action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-assistant-reconciliation-missing-001",),
        )

        action_request_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-action-request-001",
                subject_linkage={
                    "action_request_ids": (action_request.action_request_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-action-request-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:action-request",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="direct action request linkage",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        approval_decision_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-approval-decision-001",
                subject_linkage={
                    "approval_decision_ids": (approval_decision.approval_decision_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-approval-decision-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:approval-decision",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="direct approval decision linkage",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        action_execution_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-action-execution-001",
                subject_linkage={
                    "action_execution_ids": (execution.action_execution_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-action-execution-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:action-execution",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="direct action execution linkage",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        delegation_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-delegation-001",
                subject_linkage={
                    "delegation_ids": (execution.delegation_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-delegation-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:delegation",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="direct delegation linkage",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        subject_alert_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-subject-alert-001",
                subject_linkage={
                    "alert_ids": (admitted.alert.alert_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-subject-alert-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:subject-alert",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="subject-linkage alert association",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        subject_analytic_signal_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-subject-signal-001",
                subject_linkage={
                    "analytic_signal_ids": (admitted.alert.analytic_signal_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-subject-signal-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:subject-signal",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="subject-linkage analytic signal association",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )
        subject_finding_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-subject-finding-001",
                subject_linkage={
                    "finding_ids": (admitted.alert.finding_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-subject-finding-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:subject-finding",
                first_seen_at=first_seen_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="subject-linkage finding association",
                compared_at=delegated_at,
                lifecycle_state="matched",
            )
        )

        execution_snapshot = service.inspect_assistant_context(
            "action_execution",
            execution.action_execution_id,
        )
        alert_snapshot = service.inspect_assistant_context("alert", admitted.alert.alert_id)

        self.assertIn(
            action_request_reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            approval_decision_reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            action_execution_reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            delegation_reconciliation.reconciliation_id,
            execution_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            subject_alert_reconciliation.reconciliation_id,
            alert_snapshot.linked_reconciliation_ids,
        )
        self.assertIn(
            subject_analytic_signal_reconciliation.reconciliation_id,
            alert_snapshot.linked_reconciliation_ids,
        )

        subject_alert_snapshot = service.inspect_assistant_context(
            "reconciliation",
            subject_alert_reconciliation.reconciliation_id,
        )
        subject_signal_snapshot = service.inspect_assistant_context(
            "reconciliation",
            subject_analytic_signal_reconciliation.reconciliation_id,
        )

        self.assertEqual(
            subject_alert_snapshot.linked_alert_ids,
            (admitted.alert.alert_id,),
        )
        self.assertIn(
            recommendation.recommendation_id,
            subject_alert_snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            subject_alert_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(
            subject_alert_snapshot.linked_case_ids,
            (promoted_case.case_id,),
        )
        self.assertIn(
            subject_finding_reconciliation.reconciliation_id,
            subject_alert_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(subject_alert_snapshot.reviewed_context, reviewed_context)

        self.assertEqual(
            subject_signal_snapshot.linked_alert_ids,
            (admitted.alert.alert_id,),
        )
        self.assertEqual(
            subject_signal_snapshot.linked_case_ids,
            (promoted_case.case_id,),
        )
        self.assertIn(
            recommendation.recommendation_id,
            subject_signal_snapshot.linked_recommendation_ids,
        )
        self.assertIn(
            admitted.reconciliation.reconciliation_id,
            subject_signal_snapshot.linked_reconciliation_ids,
        )
        self.assertEqual(subject_signal_snapshot.reviewed_context, reviewed_context)

    def test_service_renders_reconciliation_assistant_context_for_isolated_executor_lineage(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 12, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-isolated-001",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-isolated-001",
                "owner": "identity-operations",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-assistant-isolated-001",
            analytic_signal_id="signal-assistant-isolated-001",
            substrate_detection_record_id="substrate-detection-assistant-isolated-001",
            correlation_key="claim:asset-repo-isolated-001:assistant-isolated-review",
            first_seen_at=requested_at,
            last_seen_at=requested_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-assistant-isolated-001",
                source_record_id="substrate-detection-assistant-isolated-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=requested_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        approval_target_scope = {"asset_id": "critical-host-003"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-003",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approval_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-isolated-lineage-001",
                action_request_id="action-request-isolated-lineage-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        action_request = service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-isolated-lineage-001",
                approval_decision_id=approval_decision.approval_decision_id,
                case_id=promoted_case.case_id,
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                idempotency_key="idempotency-isolated-lineage-001",
                target_scope=approval_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        execution = service.delegate_approved_action_to_isolated_executor(
            action_request_id=action_request.action_request_id,
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-assistant-isolated-missing-001",),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=action_request.action_request_id,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "isolated-executor",
                    "idempotency_key": execution.idempotency_key,
                    "observed_at": compared_at,
                    "status": "failed",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )
        delegation_reconciliation = service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-assistant-isolated-delegation-001",
                subject_linkage={
                    "delegation_ids": (execution.delegation_id,),
                },
                alert_id=None,
                finding_id=None,
                analytic_signal_id=None,
                execution_run_id="execution-run-isolated-delegation-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:isolated-delegation",
                first_seen_at=requested_at,
                last_seen_at=compared_at,
                ingest_disposition="matched",
                mismatch_summary="direct delegation linkage",
                compared_at=compared_at,
                lifecycle_state="matched",
            )
        )

        snapshot = service.inspect_assistant_context(
            "reconciliation",
            reconciliation.reconciliation_id,
        )

        self.assertEqual(
            reconciliation.subject_linkage["delegation_ids"],
            (execution.delegation_id,),
        )
        self.assertEqual(snapshot.linked_alert_ids, (admitted.alert.alert_id,))
        self.assertEqual(snapshot.linked_case_ids, (promoted_case.case_id,))
        self.assertEqual(snapshot.reviewed_context, reviewed_context)
        self.assertIn(
            delegation_reconciliation.reconciliation_id,
            snapshot.linked_reconciliation_ids,
        )

    def test_service_preserves_declared_missing_evidence_ids_in_assistant_context(
        self,
    ) -> None:
        _, service, case, evidence_id, _ = self._build_phase19_in_scope_case()
        case = service.persist_record(
            replace(
                case,
                evidence_ids=(
                    "evidence-assistant-missing-001",
                    evidence_id,
                ),
            )
        )

        snapshot = service.inspect_assistant_context("case", case.case_id)

        self.assertEqual(
            snapshot.linked_evidence_ids,
            (
                "evidence-assistant-missing-001",
                evidence_id,
            ),
        )
        self.assertEqual(len(snapshot.linked_evidence_records), 1)
        self.assertEqual(
            snapshot.linked_evidence_records[0]["evidence_id"],
            evidence_id,
        )

    def test_service_merges_reviewed_context_for_existing_alert_updates(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-001",
            },
        }
        reviewed_context_update = {
            "asset": {
                "criticality": "high",
            },
            "identity": {
                "owner": "identity-operations",
            },
        }
        materially_new_reviewed_context = {
            "privilege": {
                "privilege_scope": "repository_admin",
                "delegated_authority": "reviewed",
            }
        }
        merged_reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-001",
                "owner": "identity-operations",
            },
            "privilege": {
                "privilege_scope": "repository_admin",
                "delegated_authority": "reviewed",
            },
        }

        created = service.ingest_finding_alert(
            finding_id="finding-merge-001",
            analytic_signal_id="signal-merge-001",
            substrate_detection_record_id="substrate-detection-merge-001",
            correlation_key="claim:asset-repo-001:privilege-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-merge-001",
                source_record_id="substrate-detection-merge-001",
                alert_id=created.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(created.alert.alert_id)
        context_updated = service.ingest_finding_alert(
            finding_id="finding-merge-001",
            analytic_signal_id="signal-merge-001",
            substrate_detection_record_id="substrate-detection-merge-001",
            correlation_key="claim:asset-repo-001:privilege-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context_update,
        )
        materially_updated = service.ingest_finding_alert(
            finding_id="finding-merge-002",
            analytic_signal_id="signal-merge-001",
            substrate_detection_record_id="substrate-detection-merge-002",
            correlation_key="claim:asset-repo-001:privilege-review",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            materially_new_work=True,
            reviewed_context=materially_new_reviewed_context,
        )

        self.assertEqual(context_updated.disposition, "updated")
        self.assertEqual(materially_updated.disposition, "updated")
        self.assertEqual(context_updated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(materially_updated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(context_updated.alert.case_id, promoted_case.case_id)
        self.assertEqual(materially_updated.alert.case_id, promoted_case.case_id)
        self.assertEqual(context_updated.alert.reviewed_context, {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-001",
                "owner": "identity-operations",
            },
        })
        self.assertEqual(materially_updated.alert.reviewed_context, merged_reviewed_context)
        self.assertEqual(
            service.get_record(CaseRecord, promoted_case.case_id).reviewed_context,
            merged_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, created.alert.analytic_signal_id).reviewed_context,
            service.get_record(AlertRecord, created.alert.alert_id).reviewed_context,
        )

    def test_service_preserves_reviewed_context_when_native_detection_links_existing_case(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
            },
            "identity": {
                "identity_id": "principal-001",
            },
            "privilege": {
                "privilege_scope": "repository_admin",
            },
        }
        reviewed_context_update = {
            "asset": {
                "criticality": "high",
            },
            "identity": {
                "owner": "identity-operations",
            },
        }
        reviewed_context_followup = {
            "privilege": {
                "delegated_authority": "reviewed",
            },
        }
        merged_reviewed_context = {
            "asset": {
                "asset_id": "asset-repo-001",
                "ownership": "platform-security",
                "criticality": "high",
            },
            "identity": {
                "identity_id": "principal-001",
                "owner": "identity-operations",
            },
            "privilege": {
                "privilege_scope": "repository_admin",
                "delegated_authority": "reviewed",
            },
        }

        admitted = service.ingest_finding_alert(
            finding_id="finding-native-link-001",
            analytic_signal_id="signal-native-link-001",
            substrate_detection_record_id="substrate-detection-native-link-001",
            correlation_key="claim:asset-repo-001:native-link",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context,
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-native-link-001",
                source_record_id="substrate-detection-native-link-001",
                alert_id=admitted.alert.alert_id,
                case_id=None,
                source_system="reviewed-source",
                collector_identity="control-plane-test",
                acquired_at=first_seen_at,
                derivation_relationship="admitted_analytic_signal",
                lifecycle_state="collected",
            )
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        updated_result = service.ingest_finding_alert(
            finding_id="finding-native-link-001",
            analytic_signal_id="signal-native-link-001",
            substrate_detection_record_id="substrate-detection-native-link-001",
            correlation_key="claim:asset-repo-001:native-link",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context_update,
        )
        followup_result = service.ingest_finding_alert(
            finding_id="finding-native-link-001",
            analytic_signal_id="signal-native-link-001",
            substrate_detection_record_id="substrate-detection-native-link-001",
            correlation_key="claim:asset-repo-001:native-link",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            reviewed_context=reviewed_context_followup,
        )
        native_record = NativeDetectionRecord(
            substrate_key="wazuh",
            native_record_id="native-detection-001",
            record_kind="alert",
            correlation_key="claim:asset-repo-001:native-link",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
            metadata={},
        )

        linked = service._attach_native_detection_context(
            record=native_record,
            ingest_result=updated_result,
            substrate_detection_record_id="substrate-detection-native-link-001",
        )
        relinked = service._attach_native_detection_context(
            record=native_record,
            ingest_result=followup_result,
            substrate_detection_record_id="substrate-detection-native-link-001",
        )

        self.assertEqual(linked.alert.case_id, promoted_case.case_id)
        self.assertEqual(relinked.alert.case_id, promoted_case.case_id)
        self.assertEqual(
            service.get_record(CaseRecord, promoted_case.case_id).reviewed_context,
            merged_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            merged_reviewed_context,
        )

    def test_service_extends_promoted_wazuh_alert_with_existing_case_linkage(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        created = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(created.alert.alert_id)

        restated_payload = _load_wazuh_fixture("agent-origin-alert.json")
        restated_payload["id"] = "1731595888.5000001"
        restated_payload["timestamp"] = "2026-04-05T12:15:00+00:00"
        restated = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(restated_payload),
        )

        restated_signal = service.get_record(
            AnalyticSignalRecord,
            restated.reconciliation.analytic_signal_id,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            restated.reconciliation.reconciliation_id,
        )

        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.case_id, promoted_case.case_id)
        self.assertEqual(restated.alert.lifecycle_state, "escalated_to_case")
        self.assertIsNotNone(restated_signal)
        self.assertEqual(restated_signal.case_ids, (promoted_case.case_id,))
        self.assertIsNotNone(reconciliation)
        self.assertEqual(
            reconciliation.subject_linkage["case_ids"],
            (promoted_case.case_id,),
        )

        persisted_case = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(persisted_case)
        self.assertEqual(persisted_case.alert_id, created.alert.alert_id)
        self.assertEqual(persisted_case.finding_id, created.alert.finding_id)
        self.assertEqual(persisted_case.lifecycle_state, "open")
        evidence_records = sorted(
            (
                evidence
                for evidence in store.list(EvidenceRecord)
                if evidence.alert_id == created.alert.alert_id
            ),
            key=lambda evidence: evidence.evidence_id,
        )
        self.assertEqual(len(evidence_records), 2)
        self.assertEqual(
            sorted(evidence.evidence_id for evidence in evidence_records),
            sorted(persisted_case.evidence_ids),
        )
        self.assertEqual(
            tuple(evidence.case_id for evidence in evidence_records),
            (promoted_case.case_id, promoted_case.case_id),
        )

    def test_service_keeps_distinct_wazuh_incidents_separate_when_native_context_differs(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        first_payload = _load_wazuh_fixture("agent-origin-alert.json")
        second_payload = _load_wazuh_fixture("agent-origin-alert.json")
        second_payload["id"] = "1731595888.5000001"
        second_payload["timestamp"] = "2026-04-05T12:15:00+00:00"
        second_payload["location"] = "/var/log/secure"
        second_payload["data"] = {
            "srcip": "203.0.113.77",
            "srcuser": "invalid-user",
        }

        created = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(first_payload),
        )
        distinct = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(second_payload),
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(distinct.disposition, "created")
        self.assertNotEqual(distinct.alert.alert_id, created.alert.alert_id)

        alerts = store.list(AlertRecord)
        self.assertEqual(len(alerts), 2)

        first_reconciliation = service.get_record(
            ReconciliationRecord,
            created.reconciliation.reconciliation_id,
        )
        second_reconciliation = service.get_record(
            ReconciliationRecord,
            distinct.reconciliation.reconciliation_id,
        )

        self.assertIsNotNone(first_reconciliation)
        self.assertIsNotNone(second_reconciliation)
        self.assertEqual(
            first_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731594986.4931506",),
        )
        self.assertEqual(
            second_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731595888.5000001",),
        )

    def test_service_keeps_github_audit_repository_identity_separate_when_stable_ids_differ(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        first_payload = _load_wazuh_fixture("github-audit-alert.json")
        second_payload = _load_wazuh_fixture("github-audit-alert.json")
        second_payload["data"]["organization"]["id"] = "org-999"
        second_payload["data"]["repository"]["id"] = "repo-999"

        created = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(first_payload),
        )
        distinct = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(second_payload),
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(distinct.disposition, "created")
        self.assertNotEqual(distinct.alert.alert_id, created.alert.alert_id)
        self.assertNotEqual(
            created.reconciliation.correlation_key,
            distinct.reconciliation.correlation_key,
        )

        alerts = store.list(AlertRecord)
        self.assertEqual(len(alerts), 2)

        first_reconciliation = service.get_record(
            ReconciliationRecord,
            created.reconciliation.reconciliation_id,
        )
        second_reconciliation = service.get_record(
            ReconciliationRecord,
            distinct.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            first_reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
                "data.source_family": "github_audit",
                "data.audit_action": "member.added",
                "data.actor.id": "octocat",
                "data.actor.name": "octocat",
                "data.target.id": "security-reviews",
                "data.target.name": "security-reviews",
                "data.organization.id": "org-001",
                "data.organization.name": "TommyKammy",
                "data.repository.id": "repo-001",
                "data.repository.full_name": "TommyKammy/AegisOps",
                "data.privilege.change_type": "membership_change",
                "data.privilege.scope": "repository_admin",
                "data.privilege.permission": "admin",
                "data.privilege.role": "maintainer",
            },
        )
        self.assertEqual(
            second_reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
                "data.source_family": "github_audit",
                "data.audit_action": "member.added",
                "data.actor.id": "octocat",
                "data.actor.name": "octocat",
                "data.target.id": "security-reviews",
                "data.target.name": "security-reviews",
                "data.organization.id": "org-999",
                "data.organization.name": "TommyKammy",
                "data.repository.id": "repo-999",
                "data.repository.full_name": "TommyKammy/AegisOps",
                "data.privilege.change_type": "membership_change",
                "data.privilege.scope": "repository_admin",
                "data.privilege.permission": "admin",
                "data.privilege.role": "maintainer",
            },
        )

    def test_service_admits_github_audit_fixture_through_wazuh_source_profile(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("github-audit-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "github_audit",
                "accountable_source_identity": "manager:wazuh-manager-github-1",
                "delivery_path": "github/orgs/TommyKammy/repos/AegisOps/audit",
            },
            "identity": {
                "actor": {
                    "identity_type": "user",
                    "identity_id": "octocat",
                    "display_name": "octocat",
                },
                "target": {
                    "identity_type": "team",
                    "identity_id": "security-reviews",
                    "display_name": "security-reviews",
                },
            },
            "asset": {
                "organization": {
                    "organization_id": "org-001",
                    "organization_name": "TommyKammy",
                },
                "repository": {
                    "repository_id": "repo-001",
                    "repository_name": "AegisOps",
                    "repository_full_name": "TommyKammy/AegisOps",
                },
            },
            "privilege": {
                "change_type": "membership_change",
                "scope": "repository_admin",
                "permission": "admin",
                "role": "maintainer",
            },
            "provenance": {
                "audit_action": "member.added",
                "request_id": "GH-REQ-0001",
                "rule_id": "github-audit-privilege-change",
                "rule_level": 8,
                "rule_description": "GitHub audit repository privilege change",
                "decoder_name": "github_audit",
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
            },
        }
        expected_reviewed_context = {
            **expected_profile,
            "provenance": {
                **expected_profile["provenance"],
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        }

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.reviewed_context, expected_reviewed_context)
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, admitted.alert.analytic_signal_id).reviewed_context,
            expected_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            expected_reviewed_context,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["accountable_source_identities"],
            ("manager:wazuh-manager-github-1",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_source_profile"],
            expected_profile,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "github/orgs/TommyKammy/repos/AegisOps/audit",
                "data.source_family": "github_audit",
                "data.audit_action": "member.added",
                "data.actor.id": "octocat",
                "data.actor.name": "octocat",
                "data.target.id": "security-reviews",
                "data.target.name": "security-reviews",
                "data.organization.id": "org-001",
                "data.organization.name": "TommyKammy",
                "data.repository.id": "repo-001",
                "data.repository.full_name": "TommyKammy/AegisOps",
                "data.privilege.change_type": "membership_change",
                "data.privilege.scope": "repository_admin",
                "data.privilege.permission": "admin",
                "data.privilege.role": "maintainer",
            },
        )

    def test_service_distinguishes_live_wazuh_github_audit_ingest_from_replay_provenance(
        self,
    ) -> None:
        replay_store, _ = make_store()
        replay_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=replay_store,
        )
        live_store, _ = make_store()
        live_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=live_store,
        )
        adapter = WazuhAlertAdapter()
        payload = _load_wazuh_fixture("github-audit-alert.json")

        replay_result = replay_service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(payload),
        )
        live_result = live_service.ingest_wazuh_alert(
            raw_alert=payload,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )

        self.assertEqual(
            replay_result.alert.reviewed_context["provenance"]["admission_channel"],
            "fixture_replay",
        )
        self.assertEqual(
            replay_result.alert.reviewed_context["provenance"]["admission_kind"],
            "replay",
        )
        self.assertEqual(
            live_result.alert.reviewed_context["provenance"]["admission_channel"],
            "live_wazuh_webhook",
        )
        self.assertEqual(
            live_result.alert.reviewed_context["provenance"]["admission_kind"],
            "live",
        )
        self.assertEqual(
            replay_service.get_record(
                ReconciliationRecord,
                replay_result.reconciliation.reconciliation_id,
            ).subject_linkage["admission_provenance"],
            {
                "admission_channel": "fixture_replay",
                "admission_kind": "replay",
            },
        )
        self.assertEqual(
            live_service.get_record(
                ReconciliationRecord,
                live_result.reconciliation.reconciliation_id,
            ).subject_linkage["admission_provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )

    def test_service_restates_and_deduplicates_live_wazuh_github_audit_ingest_with_case_linkage(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )
        payload = _load_wazuh_fixture("github-audit-alert.json")

        created = service.ingest_wazuh_alert(
            raw_alert=payload,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(created.alert.alert_id)

        restated_payload = _load_wazuh_fixture("github-audit-alert.json")
        restated_payload["id"] = "1731595300.7654321"
        restated_payload["timestamp"] = "2026-04-05T12:25:00+00:00"
        restated = service.ingest_wazuh_alert(
            raw_alert=restated_payload,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        deduplicated = service.ingest_wazuh_alert(
            raw_alert=restated_payload,
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )

        created_signal = service.get_record(
            AnalyticSignalRecord,
            created.alert.analytic_signal_id,
        )
        restated_signal = service.get_record(
            AnalyticSignalRecord,
            restated.reconciliation.analytic_signal_id,
        )
        restated_reconciliation = service.get_record(
            ReconciliationRecord,
            restated.reconciliation.reconciliation_id,
        )
        deduplicated_reconciliation = service.get_record(
            ReconciliationRecord,
            deduplicated.reconciliation.reconciliation_id,
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(deduplicated.disposition, "deduplicated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(deduplicated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.case_id, promoted_case.case_id)
        self.assertEqual(deduplicated.alert.case_id, promoted_case.case_id)
        self.assertEqual(restated.alert.lifecycle_state, "escalated_to_case")
        self.assertEqual(deduplicated.alert.lifecycle_state, "escalated_to_case")
        self.assertEqual(
            restated.alert.reviewed_context["provenance"]["admission_channel"],
            "live_wazuh_webhook",
        )
        self.assertEqual(
            restated.alert.reviewed_context["provenance"]["admission_kind"],
            "live",
        )
        self.assertEqual(
            deduplicated.alert.reviewed_context["provenance"]["admission_channel"],
            "live_wazuh_webhook",
        )
        self.assertEqual(
            deduplicated.alert.reviewed_context["provenance"]["admission_kind"],
            "live",
        )

        self.assertIsNotNone(created_signal)
        self.assertEqual(created_signal.case_ids, (promoted_case.case_id,))
        self.assertEqual(
            created_signal.substrate_detection_record_id,
            "wazuh:1731595300.1234567",
        )
        self.assertEqual(
            created_signal.last_seen_at,
            datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
        )

        self.assertIsNotNone(restated_signal)
        self.assertEqual(restated_signal.case_ids, (promoted_case.case_id,))
        self.assertEqual(
            restated_signal.substrate_detection_record_id,
            "wazuh:1731595300.7654321",
        )
        self.assertEqual(
            restated_signal.last_seen_at,
            datetime(2026, 4, 5, 12, 25, tzinfo=timezone.utc),
        )

        self.assertIsNotNone(restated_reconciliation)
        self.assertEqual(restated_reconciliation.ingest_disposition, "restated")
        self.assertEqual(
            restated_reconciliation.subject_linkage["case_ids"],
            (promoted_case.case_id,),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("wazuh:1731595300.1234567", "wazuh:1731595300.7654321"),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["analytic_signal_ids"],
            (created.alert.analytic_signal_id, restated.reconciliation.analytic_signal_id),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["admission_provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )
        self.assertEqual(
            restated_reconciliation.last_seen_at,
            datetime(2026, 4, 5, 12, 25, tzinfo=timezone.utc),
        )

        self.assertIsNotNone(deduplicated_reconciliation)
        self.assertEqual(
            deduplicated_reconciliation.ingest_disposition,
            "deduplicated",
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["case_ids"],
            (promoted_case.case_id,),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage[
                "substrate_detection_record_ids"
            ],
            ("wazuh:1731595300.1234567", "wazuh:1731595300.7654321"),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["admission_provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )

        persisted_case = service.get_record(CaseRecord, promoted_case.case_id)
        self.assertIsNotNone(persisted_case)
        self.assertEqual(persisted_case.alert_id, created.alert.alert_id)
        self.assertEqual(persisted_case.finding_id, created.alert.finding_id)
        self.assertEqual(persisted_case.lifecycle_state, "open")
        self.assertEqual(
            persisted_case.reviewed_context["provenance"]["admission_channel"],
            "live_wazuh_webhook",
        )
        self.assertEqual(
            persisted_case.reviewed_context["provenance"]["admission_kind"],
            "live",
        )
        evidence_records = sorted(
            (
                evidence
                for evidence in store.list(EvidenceRecord)
                if evidence.alert_id == created.alert.alert_id
            ),
            key=lambda evidence: evidence.evidence_id,
        )
        self.assertEqual(len(evidence_records), 2)
        self.assertEqual(
            tuple(evidence.case_id for evidence in evidence_records),
            (promoted_case.case_id, promoted_case.case_id),
        )

    def test_service_exposes_live_wazuh_entra_id_ingest_through_phase19_operator_surface(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )

        admitted = service.ingest_wazuh_alert(
            raw_alert=_load_wazuh_fixture("entra-id-alert.json"),
            authorization_header="Bearer reviewed-shared-secret",
            forwarded_proto="https",
            reverse_proxy_secret_header="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
            peer_addr="127.0.0.1",
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        queue_view = service.inspect_analyst_queue()
        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(queue_view.records[0]["case_id"], promoted_case.case_id)
        self.assertEqual(
            queue_view.records[0]["reviewed_context"]["source"]["source_family"],
            "entra_id",
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id)
        self.assertEqual(case_detail.case_id, promoted_case.case_id)
        self.assertEqual(
            case_detail.reviewed_context["source"]["source_family"],
            "entra_id",
        )
        self.assertEqual(case_detail.linked_alert_ids, (admitted.alert.alert_id,))

    def test_service_admits_microsoft_365_audit_fixture_through_wazuh_source_profile(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("microsoft-365-audit-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "microsoft_365_audit",
                "accountable_source_identity": "manager:wazuh-manager-m365-1",
                "delivery_path": "microsoft365/contoso/exchange",
            },
            "identity": {
                "actor": {
                    "identity_type": "user",
                    "identity_id": "alex@contoso.com",
                    "display_name": "Alex Rivera",
                },
                "target": {
                    "identity_type": "mailbox",
                    "identity_id": "shared-mailbox-finance",
                    "display_name": "shared-mailbox-finance",
                },
            },
            "asset": {
                "tenant": {
                    "tenant_id": "tenant-001",
                    "tenant_name": "Contoso",
                },
                "app": {
                    "app_id": "app-365-exchange",
                    "app_name": "Exchange Online",
                    "app_type": "workload",
                },
            },
            "authentication": {
                "method": "oauth2",
                "client_app": "Outlook",
                "result": "success",
            },
            "privilege": {
                "change_type": "permission_grant",
                "scope": "mailbox",
                "permission": "full_access",
            },
            "provenance": {
                "audit_action": "Add-MailboxPermission",
                "request_id": "M365-REQ-0001",
                "workload": "exchange",
                "operation": "Add-MailboxPermission",
                "record_type": "Microsoft 365 audit",
                "rule_id": "microsoft-365-audit-privilege-change",
                "rule_level": 7,
                "rule_description": "Microsoft 365 audit mailbox permission change",
                "decoder_name": "microsoft_365_audit",
                "location": "microsoft365/contoso/exchange",
            },
        }
        expected_reviewed_context = {
            **expected_profile,
            "provenance": {
                **expected_profile["provenance"],
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        }

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.reviewed_context, expected_reviewed_context)
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, admitted.alert.analytic_signal_id).reviewed_context,
            expected_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            expected_reviewed_context,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_source_profile"],
            expected_profile,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "microsoft365/contoso/exchange",
                "data.source_family": "microsoft_365_audit",
                "data.audit_action": "Add-MailboxPermission",
                "data.workload": "exchange",
                "data.operation": "Add-MailboxPermission",
                "data.record_type": "Microsoft 365 audit",
                "data.actor.id": "alex@contoso.com",
                "data.actor.name": "Alex Rivera",
                "data.target.id": "shared-mailbox-finance",
                "data.target.name": "shared-mailbox-finance",
                "data.tenant.id": "tenant-001",
                "data.tenant.name": "Contoso",
                "data.app.id": "app-365-exchange",
                "data.app.name": "Exchange Online",
                "data.authentication.method": "oauth2",
                "data.authentication.client_app": "Outlook",
                "data.authentication.result": "success",
                "data.privilege.change_type": "permission_grant",
                "data.privilege.scope": "mailbox",
                "data.privilege.permission": "full_access",
            },
        )

    def test_service_admits_entra_id_fixture_through_wazuh_source_profile(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()
        native_record = adapter.build_native_detection_record(
            _load_wazuh_fixture("entra-id-alert.json")
        )

        admitted = service.ingest_native_detection_record(adapter, native_record)

        expected_profile = {
            "source": {
                "source_system": "wazuh",
                "source_family": "entra_id",
                "accountable_source_identity": "manager:wazuh-manager-entra-1",
                "delivery_path": "entra/contoso/directory",
            },
            "identity": {
                "actor": {
                    "identity_type": "service_principal",
                    "identity_id": "spn-operations",
                    "display_name": "Operations Automation",
                },
                "target": {
                    "identity_type": "role",
                    "identity_id": "role-global-admin",
                    "display_name": "Global Administrator",
                },
            },
            "asset": {
                "tenant": {
                    "tenant_id": "tenant-001",
                    "tenant_name": "Contoso",
                },
                "app": {
                    "app_id": "app-entra-admin",
                    "app_name": "Azure Portal",
                    "app_type": "service",
                },
            },
            "authentication": {
                "method": "mfa",
                "client_app": "Azure Portal",
                "result": "success",
            },
            "privilege": {
                "change_type": "role_assignment",
                "scope": "directory_role",
                "permission": "Global Administrator",
                "role": "Privileged Role Administrator",
            },
            "provenance": {
                "audit_action": "Add member to role",
                "request_id": "ENTRA-REQ-0001",
                "correlation_id": "entra-corr-0001",
                "operation": "Add member to role",
                "record_type": "Entra ID audit",
                "rule_id": "entra-id-role-assignment",
                "rule_level": 8,
                "rule_description": "Entra ID privileged role assignment",
                "decoder_name": "entra_id",
                "location": "entra/contoso/directory",
            },
        }
        expected_reviewed_context = {
            **expected_profile,
            "provenance": {
                **expected_profile["provenance"],
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        }

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.reviewed_context, expected_reviewed_context)
        self.assertEqual(
            service.get_record(AnalyticSignalRecord, admitted.alert.analytic_signal_id).reviewed_context,
            expected_reviewed_context,
        )
        self.assertEqual(
            service.get_record(AlertRecord, admitted.alert.alert_id).reviewed_context,
            expected_reviewed_context,
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_source_profile"],
            expected_profile,
        )
        self.assertEqual(
            reconciliation.subject_linkage["reviewed_correlation_context"],
            {
                "location": "entra/contoso/directory",
                "data.source_family": "entra_id",
                "data.audit_action": "Add member to role",
                "data.actor.id": "spn-operations",
                "data.actor.name": "Operations Automation",
                "data.target.id": "role-global-admin",
                "data.target.name": "Global Administrator",
                "data.tenant.id": "tenant-001",
                "data.tenant.name": "Contoso",
                "data.app.id": "app-entra-admin",
                "data.app.name": "Azure Portal",
                "data.authentication.method": "mfa",
                "data.authentication.client_app": "Azure Portal",
                "data.authentication.result": "success",
                "data.correlation_id": "entra-corr-0001",
                "data.operation": "Add member to role",
                "data.privilege.change_type": "role_assignment",
                "data.privilege.scope": "directory_role",
                "data.privilege.permission": "Global Administrator",
                "data.privilege.role": "Privileged Role Administrator",
                "data.record_type": "Entra ID audit",
            },
        )

    def test_service_admits_native_detection_records_via_substrate_adapter_boundary(self) -> None:
        @dataclass(frozen=True)
        class TestNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id=f"finding::{record.native_record_id}",
                    analytic_signal_id=f"signal::{record.native_record_id}",
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        admitted = service.ingest_native_detection_record(
            TestNativeRecordAdapter(),
            NativeDetectionRecord(
                substrate_key="test-substrate",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                metadata={"vendor": "test"},
            ),
        )

        self.assertEqual(admitted.disposition, "created")
        self.assertEqual(admitted.alert.finding_id, "finding::native-001")
        self.assertEqual(admitted.alert.analytic_signal_id, "signal::native-001")
        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(
            signals[0].substrate_detection_record_id,
            "test-substrate:native-001",
        )

    def test_service_trims_native_admission_provenance_before_persisting_reviewed_context(
        self,
    ) -> None:
        @dataclass(frozen=True)
        class TestNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id=f"finding::{record.native_record_id}",
                    analytic_signal_id=f"signal::{record.native_record_id}",
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        admitted = service.ingest_native_detection_record(
            TestNativeRecordAdapter(),
            NativeDetectionRecord(
                substrate_key="test-substrate",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                metadata={
                    "admission_provenance": {
                        "admission_kind": " replay ",
                        "admission_channel": " fixture_replay ",
                    }
                },
            ),
        )

        self.assertEqual(
            admitted.alert.reviewed_context["provenance"],
            {
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        )
        self.assertEqual(
            service.get_record(
                ReconciliationRecord,
                admitted.reconciliation.reconciliation_id,
            ).subject_linkage["admission_provenance"],
            {
                "admission_kind": "replay",
                "admission_channel": "fixture_replay",
            },
        )

    def test_service_rolls_back_native_ingest_when_evidence_timestamp_is_naive(
        self,
    ) -> None:
        @dataclass(frozen=True)
        class TimestampNormalizingNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id=f"finding::{record.native_record_id}",
                    analytic_signal_id=f"signal::{record.native_record_id}",
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                    last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "record.first_seen_at must be timezone-aware",
        ):
            service.ingest_native_detection_record(
                TimestampNormalizingNativeRecordAdapter(),
                NativeDetectionRecord(
                    substrate_key="test-substrate",
                    native_record_id="native-001",
                    record_kind="alert",
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=datetime(2026, 4, 5, 12, 0),
                    last_seen_at=datetime(2026, 4, 5, 12, 15),
                    metadata={"vendor": "test"},
                ),
            )

        self.assertEqual(store.list(AlertRecord), ())
        self.assertEqual(store.list(AnalyticSignalRecord), ())
        self.assertEqual(store.list(ReconciliationRecord), ())
        self.assertEqual(store.list(EvidenceRecord), ())

    def test_service_namespaces_fallback_substrate_detection_ids_by_substrate(self) -> None:
        @dataclass(frozen=True)
        class FallbackNativeRecordAdapter(NativeDetectionRecordAdapter):
            substrate_key: str

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id=None,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        first = service.ingest_native_detection_record(
            FallbackNativeRecordAdapter(substrate_key="substrate-a"),
            NativeDetectionRecord(
                substrate_key="substrate-a",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
                metadata={"vendor": "a"},
            ),
        )
        second = service.ingest_native_detection_record(
            FallbackNativeRecordAdapter(substrate_key="substrate-b"),
            NativeDetectionRecord(
                substrate_key="substrate-b",
                native_record_id="native-001",
                record_kind="alert",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                metadata={"vendor": "b"},
            ),
        )

        self.assertEqual(first.disposition, "created")
        self.assertEqual(second.disposition, "restated")
        self.assertIsNotNone(first.reconciliation.analytic_signal_id)
        self.assertIsNotNone(second.reconciliation.analytic_signal_id)
        self.assertNotEqual(
            first.reconciliation.analytic_signal_id,
            second.reconciliation.analytic_signal_id,
        )
        self.assertEqual(
            second.reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-a:native-001", "substrate-b:native-001"),
        )
        self.assertEqual(
            second.reconciliation.subject_linkage["analytic_signal_ids"],
            (
                first.reconciliation.analytic_signal_id,
                second.reconciliation.analytic_signal_id,
            ),
        )
        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 2)

    def test_service_rejects_blank_substrate_keys_at_native_detection_boundary(self) -> None:
        @dataclass(frozen=True)
        class BlankSubstrateAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "   "

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id=record.native_record_id,
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "adapter\\.substrate_key must be a non-empty string",
        ):
            service.ingest_native_detection_record(
                BlankSubstrateAdapter(),
                NativeDetectionRecord(
                    substrate_key="   ",
                    native_record_id="native-001",
                    record_kind="alert",
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                    last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                    metadata={"vendor": "test"},
                ),
            )

    def test_service_rejects_blank_detection_id_at_native_detection_boundary(self) -> None:
        @dataclass(frozen=True)
        class BlankDetectionIdAdapter(NativeDetectionRecordAdapter):
            substrate_key: str = "test-substrate"

            def build_analytic_signal_admission(
                self, record: NativeDetectionRecord
            ) -> AnalyticSignalAdmission:
                return AnalyticSignalAdmission(
                    finding_id="finding::shared",
                    analytic_signal_id=None,
                    substrate_detection_record_id="   ",
                    correlation_key=record.correlation_key,
                    first_seen_at=record.first_seen_at,
                    last_seen_at=record.last_seen_at,
                )

        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "substrate_detection_record_id/native_record_id must be a non-empty string",
        ):
            service.ingest_native_detection_record(
                BlankDetectionIdAdapter(),
                NativeDetectionRecord(
                    substrate_key="test-substrate",
                    native_record_id="native-001",
                    record_kind="alert",
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                    last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                    metadata={"vendor": "test"},
                ),
            )

    def test_runtime_snapshot_reports_postgresql_authoritative_persistence_mode(self) -> None:
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops")
        )

        snapshot = service.describe_runtime()

        self.assertEqual(snapshot.persistence_mode, "postgresql")
        self.assertEqual(snapshot.postgres_dsn, "postgresql://control-plane.local/aegisops")

    def test_service_round_trips_records_by_control_plane_identifier(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )
        reconciliation = ReconciliationRecord(
            reconciliation_id="reconciliation-001",
            subject_linkage={"action_request_ids": ["action-request-001"]},
            alert_id=None,
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id="n8n-exec-001",
            linked_execution_run_ids=("n8n-exec-001",),
            correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
            first_seen_at=timestamp,
            last_seen_at=timestamp,
            ingest_disposition="matched",
            mismatch_summary="matched execution",
            compared_at=timestamp,
            lifecycle_state="matched",
        )

        service.persist_record(action_request)
        service.persist_record(reconciliation)

        self.assertEqual(
            service.get_record(ActionRequestRecord, "action-request-001"),
            action_request,
        )
        self.assertEqual(
            service.get_record(ReconciliationRecord, "reconciliation-001"),
            reconciliation,
        )
        self.assertIsNone(service.get_record(ActionRequestRecord, "approval-001"))
        self.assertIsNone(service.get_record(ReconciliationRecord, "n8n-exec-001"))

    def test_service_accepts_injected_store_for_runtime_snapshot(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://ignored.local/aegisops"),
            store=store,
        )

        snapshot = service.describe_runtime()

        self.assertEqual(snapshot.postgres_dsn, "postgresql://control-plane.local/aegisops")
        self.assertEqual(snapshot.persistence_mode, "postgresql")

    def test_service_returns_nested_immutable_json_backed_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        record = ActionRequestRecord(
            action_request_id="action-request-immutable-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={
                "asset_ids": ["asset-001"],
                "filters": {"environment": "prod"},
            },
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )

        service.persist_record(record)
        persisted = service.get_record(
            ActionRequestRecord, "action-request-immutable-001"
        )

        assert persisted is not None
        with self.assertRaises(TypeError):
            persisted.target_scope["asset_ids"] += ("asset-002",)
        with self.assertRaises(TypeError):
            persisted.target_scope["filters"]["environment"] = "dev"  # type: ignore[index]

    def test_service_exposes_read_only_record_and_reconciliation_inspection(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        first_compared_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        latest_compared_at = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        alert = AlertRecord(
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            case_id=None,
            lifecycle_state="triaged",
        )
        matched = ReconciliationRecord(
            reconciliation_id="reconciliation-001",
            subject_linkage={"alert_ids": ("alert-001",), "finding_ids": ("finding-001",)},
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_compared_at,
            last_seen_at=first_compared_at,
            ingest_disposition="matched",
            mismatch_summary="matched upstream signal into alert lifecycle",
            compared_at=first_compared_at,
            lifecycle_state="matched",
        )
        stale = ReconciliationRecord(
            reconciliation_id="reconciliation-002",
            subject_linkage={
                "alert_ids": ("alert-001",),
                "finding_ids": ("finding-001",),
                "execution_surface_types": ("automation_substrate",),
                "execution_surface_ids": ("n8n",),
            },
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            execution_run_id="exec-001",
            linked_execution_run_ids=("exec-001",),
            correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
            first_seen_at=first_compared_at,
            last_seen_at=latest_compared_at,
            ingest_disposition="stale",
            mismatch_summary="stale downstream execution observation requires refresh",
            compared_at=latest_compared_at,
            lifecycle_state="stale",
        )

        service.persist_record(alert)
        service.persist_record(matched)
        service.persist_record(stale)

        records_view = service.inspect_records("alert")
        status_view = service.inspect_reconciliation_status()

        self.assertTrue(records_view.read_only)
        self.assertEqual(records_view.record_family, "alert")
        self.assertEqual(records_view.total_records, 1)
        self.assertEqual(records_view.records[0]["alert_id"], "alert-001")
        self.assertEqual(records_view.records[0]["lifecycle_state"], "triaged")

        self.assertTrue(status_view.read_only)
        self.assertEqual(status_view.total_records, 2)
        self.assertEqual(status_view.by_lifecycle_state, {"matched": 1, "stale": 1})
        self.assertEqual(status_view.by_ingest_disposition, {"matched": 1, "stale": 1})
        self.assertEqual(status_view.latest_compared_at, latest_compared_at)
        self.assertEqual(
            tuple(record["reconciliation_id"] for record in status_view.records),
            ("reconciliation-001", "reconciliation-002"),
        )

    def test_service_exposes_wazuh_origin_alerts_in_business_hours_analyst_queue(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        queue_view = service.inspect_analyst_queue()

        self.assertTrue(queue_view.read_only)
        self.assertEqual(queue_view.queue_name, "analyst_review")
        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(queue_view.records[0]["queue_selection"], "business_hours_triage")
        self.assertEqual(queue_view.records[0]["review_state"], "case_required")
        self.assertEqual(queue_view.records[0]["escalation_boundary"], "tracked_case")
        self.assertEqual(queue_view.records[0]["source_system"], "wazuh")
        self.assertEqual(
            queue_view.records[0]["substrate_detection_record_ids"],
            ("wazuh:1731594986.4931506",),
        )
        self.assertEqual(
            queue_view.records[0]["accountable_source_identities"],
            ("agent:007",),
        )
        self.assertEqual(queue_view.records[0]["case_id"], promoted_case.case_id)
        self.assertEqual(queue_view.records[0]["case_lifecycle_state"], "open")
        self.assertEqual(
            queue_view.records[0]["native_rule"],
            {
                "id": "5710",
                "level": 10,
                "description": "SSH brute force attempt",
            },
        )
        self.assertEqual(len(queue_view.records[0]["evidence_ids"]), 1)

    def test_service_exposes_reviewed_context_in_analyst_queue_for_identity_rich_alerts(
        self,
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
                _load_wazuh_fixture("microsoft-365-audit-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(queue_view.records[0]["case_id"], promoted_case.case_id)
        self.assertEqual(
            queue_view.records[0]["reviewed_context"],
            admitted.alert.reviewed_context,
        )
        self.assertEqual(
            queue_view.records[0]["reviewed_context"]["source"]["source_family"],
            "microsoft_365_audit",
        )

    def test_service_records_bounded_casework_actions_for_triage_disposition_and_handoff(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        handoff_at = datetime(2026, 4, 7, 17, 45, tzinfo=timezone.utc)

        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        handed_off_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=handoff_at,
            handoff_owner="analyst-001",
            handoff_note="Recheck repository owner membership against approved change window at next business-hours review.",
            follow_up_evidence_ids=(evidence_id,),
        )
        disposed_case = service.record_case_disposition(
            case_id=handed_off_case.case_id,
            disposition="business_hours_handoff",
            rationale="No same-day response required; preserve next-shift context and keep case open.",
            recorded_at=handoff_at,
        )

        detail = service.inspect_case_detail(promoted_case.case_id)

        self.assertEqual(observation.case_id, promoted_case.case_id)
        self.assertEqual(observation.lifecycle_state, "confirmed")
        self.assertEqual(lead.case_id, promoted_case.case_id)
        self.assertEqual(lead.lifecycle_state, "triaged")
        self.assertEqual(recommendation.case_id, promoted_case.case_id)
        self.assertEqual(recommendation.lifecycle_state, "under_review")
        self.assertEqual(disposed_case.lifecycle_state, "pending_action")
        self.assertEqual(
            detail.case_record["reviewed_context"]["triage"]["disposition"],
            "business_hours_handoff",
        )
        self.assertEqual(
            detail.case_record["reviewed_context"]["triage"]["closure_rationale"],
            "No same-day response required; preserve next-shift context and keep case open.",
        )
        self.assertEqual(
            detail.case_record["reviewed_context"]["handoff"]["note"],
            "Recheck repository owner membership against approved change window at next business-hours review.",
        )
        self.assertEqual(
            detail.case_record["reviewed_context"]["handoff"]["handoff_owner"],
            "analyst-001",
        )
        self.assertEqual(detail.linked_observation_ids, (observation.observation_id,))
        self.assertEqual(detail.linked_lead_ids, (lead.lead_id,))
        self.assertIn(recommendation.recommendation_id, detail.linked_recommendation_ids)
        self.assertEqual(
            detail.linked_observation_records[0]["supporting_evidence_ids"],
            (evidence_id,),
        )
        self.assertEqual(
            detail.linked_lead_records[0]["triage_rationale"],
            "Privilege-impacting change needs durable business-hours follow-up.",
        )

    def test_service_allows_in_scope_case_assistant_context_on_phase19_operator_surface(
        self,
    ) -> None:
        _, service, promoted_case, evidence_id, _ = self._build_phase19_in_scope_case()

        snapshot = service.inspect_assistant_context("case", promoted_case.case_id)

        self.assertTrue(snapshot.read_only)
        self.assertEqual(snapshot.record_family, "case")
        self.assertEqual(snapshot.record_id, promoted_case.case_id)
        self.assertEqual(snapshot.record["case_id"], promoted_case.case_id)
        self.assertEqual(snapshot.advisory_output["output_kind"], "case_summary")
        self.assertIn(evidence_id, snapshot.linked_evidence_ids)

    def test_service_rejects_replay_only_case_from_phase19_operator_surface(self) -> None:
        service, promoted_case, _, reviewed_at = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_assistant_context("case", promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_case_detail(promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_observation(
                case_id=promoted_case.case_id,
                author_identity="analyst-001",
                observed_at=reviewed_at,
                scope_statement="Replay-only casework must fail closed.",
            )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Replay-only casework must fail closed.",
            )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_recommendation(
                case_id=promoted_case.case_id,
                review_owner="analyst-001",
                intended_outcome="Replay-only casework must fail closed.",
            )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_handoff(
                case_id=promoted_case.case_id,
                handoff_at=reviewed_at,
                handoff_owner="analyst-001",
                handoff_note="Replay-only casework must fail closed.",
            )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_disposition(
                case_id=promoted_case.case_id,
                disposition="business_hours_handoff",
                rationale="Replay-only casework must fail closed.",
                recorded_at=reviewed_at,
            )

    def test_service_rejects_case_scoped_advisory_reads_linked_to_replay_only_case(
        self,
    ) -> None:
        service, promoted_case, _, reviewed_at = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-replay-linked-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-phase19-replay-linked-001",
                review_owner="reviewer-001",
                intended_outcome="Replay-linked advisory reads must fail closed.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase19-replay-linked-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=reviewed_at,
                material_input_refs=(),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        for record_family, record_id in (
            ("case", promoted_case.case_id),
            ("recommendation", recommendation.recommendation_id),
            ("ai_trace", ai_trace.ai_trace_id),
        ):
            with self.subTest(record_family=record_family):
                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.inspect_advisory_output(record_family, record_id)

                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.render_recommendation_draft(record_family, record_id)

    def test_service_rejects_synthetic_case_scoped_reads_spoofing_in_scope_case_lineage(
        self,
    ) -> None:
        _, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-synthetic-linked-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-phase19-synthetic-linked-001",
                review_owner="reviewer-001",
                intended_outcome="Synthetic case-scoped advisory reads must fail closed.",
                lifecycle_state="under_review",
                reviewed_context={
                    "source": {
                        "source_family": "synthetic_review_fixture",
                        "admission_kind": "replay",
                    }
                },
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase19-synthetic-linked-001",
                subject_linkage={"recommendation_ids": (recommendation.recommendation_id,)},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=reviewed_at,
                material_input_refs=("fixture://synthetic-phase19-review",),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        for record_family, record_id in (
            ("recommendation", recommendation.recommendation_id),
            ("ai_trace", ai_trace.ai_trace_id),
        ):
            with self.subTest(record_family=record_family):
                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.inspect_advisory_output(record_family, record_id)

                with self.assertRaisesRegex(
                    ValueError,
                    "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
                ):
                    service.render_recommendation_draft(record_family, record_id)

    def test_service_rejects_synthetic_case_scoped_advisory_reads_from_ingested_finding_case(
        self,
    ) -> None:
        service, promoted_case, _ = self._build_phase19_synthetic_out_of_scope_case()

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_assistant_context("case", promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_advisory_output("case", promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.render_recommendation_draft("case", promoted_case.case_id)

    def test_service_rejects_ai_trace_subject_linkage_declaring_out_of_scope_provenance(
        self,
    ) -> None:
        _, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()
        recommendation = service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase19-trace-provenance-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                ai_trace_id="ai-trace-phase19-trace-provenance-001",
                review_owner="reviewer-001",
                intended_outcome="AI trace lineage must validate its own provenance.",
                lifecycle_state="under_review",
                reviewed_context=promoted_case.reviewed_context,
            )
        )
        ai_trace = service.persist_record(
            AITraceRecord(
                ai_trace_id="ai-trace-phase19-trace-provenance-001",
                subject_linkage={
                    "recommendation_ids": (recommendation.recommendation_id,),
                    "reviewed_source_profile": {
                        "source_family": "synthetic_review_fixture",
                    },
                    "admission_provenance": {
                        "admission_kind": "replay",
                        "admission_channel": "fixture_replay",
                    },
                },
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=reviewed_at,
                material_input_refs=("fixture://synthetic-phase19-review",),
                reviewer_identity="reviewer-001",
                lifecycle_state="under_review",
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_advisory_output("ai_trace", ai_trace.ai_trace_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.render_recommendation_draft("ai_trace", ai_trace.ai_trace_id)

    def test_service_treats_non_mapping_provenance_context_as_out_of_scope(self) -> None:
        _, service, _, _, _ = self._build_phase19_in_scope_case()

        self.assertTrue(
            service._phase19_context_declares_out_of_scope_provenance(
                "synthetic_review_fixture"
            )
        )

    def test_service_treats_missing_source_family_as_out_of_scope(self) -> None:
        _, service, _, _, _ = self._build_phase19_in_scope_case()

        self.assertTrue(
            service._phase19_context_declares_out_of_scope_provenance(
                {
                    "provenance": {
                        "admission_kind": "live",
                        "admission_channel": "live_wazuh_webhook",
                    }
                }
            )
        )

    def test_service_rejects_non_github_audit_case_from_phase19_operator_surface(
        self,
    ) -> None:
        service, promoted_case, _, reviewed_at = self._build_phase19_out_of_scope_case(
            fixture_name="microsoft-365-audit-alert.json"
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_case_detail(promoted_case.case_id)

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.record_case_observation(
                case_id=promoted_case.case_id,
                author_identity="analyst-001",
                observed_at=reviewed_at,
                scope_statement="Broader source-family casework must fail closed.",
            )

    def test_service_rejects_case_without_reciprocal_alert_linkage_from_phase19_operator_surface(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        spoofed_case = service.persist_record(
            CaseRecord(
                case_id="case-phase19-spoofed-alert-linkage",
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=promoted_case.evidence_ids,
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=dict(promoted_case.reviewed_context),
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_case_detail(spoofed_case.case_id)

    def test_service_rejects_case_without_reciprocal_reconciliation_linkage_from_phase19_operator_surface(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = self._build_phase19_in_scope_case()
        alert = service.get_record(AlertRecord, promoted_case.alert_id)
        self.assertIsNotNone(alert)

        spoofed_case_id = "case-phase19-spoofed-reconciliation-linkage"
        service.persist_record(
            replace(
                alert,
                case_id=spoofed_case_id,
            )
        )
        spoofed_case = service.persist_record(
            CaseRecord(
                case_id=spoofed_case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=promoted_case.evidence_ids,
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=dict(promoted_case.reviewed_context),
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            service.inspect_case_detail(spoofed_case.case_id)

    def test_service_rejects_duplicate_casework_identifiers(self) -> None:
        _, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            observation_id="observation-phase19-duplicate-ids-001",
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Initial observation for duplicate-id guard coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        with self.assertRaisesRegex(
            ValueError,
            "observation_id 'observation-phase19-duplicate-ids-001' already exists",
        ):
            service.record_case_observation(
                case_id=promoted_case.case_id,
                observation_id=observation.observation_id,
                author_identity="analyst-002",
                observed_at=reviewed_at,
                scope_statement="Collision should be rejected before persist_record updates in place.",
                supporting_evidence_ids=(evidence_id,),
            )

        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            lead_id="lead-phase19-duplicate-ids-001",
            triage_owner="analyst-001",
            triage_rationale="Create a concrete lead before checking duplicate lead IDs.",
        )
        with self.assertRaisesRegex(
            ValueError,
            "lead_id 'lead-phase19-duplicate-ids-001' already exists",
        ):
            service.record_case_lead(
                case_id=promoted_case.case_id,
                observation_id=observation.observation_id,
                lead_id=lead.lead_id,
                triage_owner="analyst-002",
                triage_rationale="Collision should be rejected before persist_record updates in place.",
            )

        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            recommendation_id="recommendation-phase19-duplicate-ids-001",
            review_owner="analyst-001",
            intended_outcome="Establish a recommendation before checking duplicate recommendation IDs.",
        )
        with self.assertRaisesRegex(
            ValueError,
            "recommendation_id 'recommendation-phase19-duplicate-ids-001' already exists",
        ):
            service.record_case_recommendation(
                case_id=promoted_case.case_id,
                lead_id=lead.lead_id,
                recommendation_id=recommendation.recommendation_id,
                review_owner="analyst-002",
                intended_outcome="Collision should be rejected before persist_record updates in place.",
            )

    def test_service_rejects_unknown_case_disposition(self) -> None:
        _, service, promoted_case, _, reviewed_at = self._build_phase19_in_scope_case()

        with self.assertRaisesRegex(
            ValueError,
            "Unsupported case disposition 'typo_pending_review'",
        ):
            service.record_case_disposition(
                case_id=promoted_case.case_id,
                disposition="typo_pending_review",
                rationale="Typos should be rejected instead of changing lifecycle state.",
                recorded_at=reviewed_at,
            )

    def test_service_rejects_raced_observation_identifier_collision(self) -> None:
        store, _ = make_store()
        store, _base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                ObservationRecord(
                    observation_id="observation-phase19-race-001",
                    hunt_id=None,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    supporting_evidence_ids=(evidence_id,),
                    author_identity="analyst-racer",
                    observed_at=reviewed_at,
                    scope_statement="Concurrent writer inserted the requested observation ID.",
                    lifecycle_state="confirmed",
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "observation_id 'observation-phase19-race-001' already exists",
        ):
            service.record_case_observation(
                case_id=promoted_case.case_id,
                observation_id="observation-phase19-race-001",
                author_identity="analyst-001",
                observed_at=reviewed_at,
                scope_statement="Caller-supplied observation IDs must reject raced duplicates.",
                supporting_evidence_ids=(evidence_id,),
            )

    def test_service_rejects_raced_lead_identifier_collision(self) -> None:
        store, _ = make_store()
        store, base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Seed observation for raced lead collision coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                LeadRecord(
                    lead_id="lead-phase19-race-001",
                    observation_id=observation.observation_id,
                    finding_id=promoted_case.finding_id,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    triage_owner="analyst-racer",
                    triage_rationale="Concurrent writer inserted the requested lead ID.",
                    lifecycle_state="triaged",
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "lead_id 'lead-phase19-race-001' already exists",
        ):
            service.record_case_lead(
                case_id=promoted_case.case_id,
                observation_id=observation.observation_id,
                lead_id="lead-phase19-race-001",
                triage_owner="analyst-001",
                triage_rationale="Caller-supplied lead IDs must reject raced duplicates.",
            )

    def test_service_rejects_raced_recommendation_identifier_collision(self) -> None:
        store, _ = make_store()
        store, base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Seed observation for raced recommendation collision coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = base_service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Seed lead for raced recommendation collision coverage.",
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                RecommendationRecord(
                    recommendation_id="recommendation-phase19-race-001",
                    lead_id=lead.lead_id,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    ai_trace_id=None,
                    review_owner="analyst-racer",
                    intended_outcome="Concurrent writer inserted the requested recommendation ID.",
                    lifecycle_state="under_review",
                    reviewed_context=promoted_case.reviewed_context,
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "recommendation_id 'recommendation-phase19-race-001' already exists",
        ):
            service.record_case_recommendation(
                case_id=promoted_case.case_id,
                lead_id=lead.lead_id,
                recommendation_id="recommendation-phase19-race-001",
                review_owner="analyst-001",
                intended_outcome=(
                    "Caller-supplied recommendation IDs must reject raced duplicates."
                ),
            )

    def test_service_rejects_raced_generated_observation_identifier_collision(self) -> None:
        store, _ = make_store()
        store, _base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                ObservationRecord(
                    observation_id="observation-phase19-generated-race-001",
                    hunt_id=None,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    supporting_evidence_ids=(evidence_id,),
                    author_identity="analyst-racer",
                    observed_at=reviewed_at,
                    scope_statement="Concurrent writer inserted the minted observation ID.",
                    lifecycle_state="confirmed",
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            AegisOpsControlPlaneService,
            "_next_identifier",
            return_value="observation-phase19-generated-race-001",
        ):
            with self.assertRaisesRegex(
                ValueError,
                "observation_id 'observation-phase19-generated-race-001' already exists",
            ):
                service.record_case_observation(
                    case_id=promoted_case.case_id,
                    author_identity="analyst-001",
                    observed_at=reviewed_at,
                    scope_statement="Generated observation IDs must reject raced duplicates.",
                    supporting_evidence_ids=(evidence_id,),
                )

        observations = store.list(ObservationRecord)
        self.assertEqual(len(observations), 1)
        self.assertEqual(
            observations[0].observation_id,
            "observation-phase19-generated-race-001",
        )

    def test_service_rejects_raced_generated_lead_identifier_collision(self) -> None:
        store, _ = make_store()
        store, base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Seed observation for generated lead race coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                LeadRecord(
                    lead_id="lead-phase19-generated-race-001",
                    observation_id=observation.observation_id,
                    finding_id=promoted_case.finding_id,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    triage_owner="analyst-racer",
                    triage_rationale="Concurrent writer inserted the minted lead ID.",
                    lifecycle_state="triaged",
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            AegisOpsControlPlaneService,
            "_next_identifier",
            return_value="lead-phase19-generated-race-001",
        ):
            with self.assertRaisesRegex(
                ValueError,
                "lead_id 'lead-phase19-generated-race-001' already exists",
            ):
                service.record_case_lead(
                    case_id=promoted_case.case_id,
                    observation_id=observation.observation_id,
                    triage_owner="analyst-001",
                    triage_rationale="Generated lead IDs must reject raced duplicates.",
                )

        leads = store.list(LeadRecord)
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0].lead_id, "lead-phase19-generated-race-001")

    def test_service_rejects_raced_generated_recommendation_identifier_collision(
        self,
    ) -> None:
        store, _ = make_store()
        store, base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Seed observation for generated recommendation race coverage.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = base_service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Seed lead for generated recommendation race coverage.",
        )
        store = _OutOfBandMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                RecommendationRecord(
                    recommendation_id="recommendation-phase19-generated-race-001",
                    lead_id=lead.lead_id,
                    hunt_run_id=None,
                    alert_id=promoted_case.alert_id,
                    case_id=promoted_case.case_id,
                    ai_trace_id=None,
                    review_owner="analyst-racer",
                    intended_outcome=(
                        "Concurrent writer inserted the minted recommendation ID."
                    ),
                    lifecycle_state="under_review",
                    reviewed_context=promoted_case.reviewed_context,
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with mock.patch.object(
            AegisOpsControlPlaneService,
            "_next_identifier",
            return_value="recommendation-phase19-generated-race-001",
        ):
            with self.assertRaisesRegex(
                ValueError,
                "recommendation_id 'recommendation-phase19-generated-race-001' already exists",
            ):
                service.record_case_recommendation(
                    case_id=promoted_case.case_id,
                    lead_id=lead.lead_id,
                    review_owner="analyst-001",
                    intended_outcome=(
                        "Generated recommendation IDs must reject raced duplicates."
                    ),
                )

        recommendations = store.list(RecommendationRecord)
        self.assertEqual(len(recommendations), 1)
        self.assertEqual(
            recommendations[0].recommendation_id,
            "recommendation-phase19-generated-race-001",
        )

    def test_service_merges_concurrent_reviewed_context_into_case_handoff(self) -> None:
        store, _ = make_store()
        store, _base_service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        store = _TransactionMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(
                    transactional_store.get(CaseRecord, promoted_case.case_id),
                    reviewed_context={
                        **dict(
                            transactional_store.get(
                                CaseRecord,
                                promoted_case.case_id,
                            ).reviewed_context
                        ),
                        "triage": {
                            "disposition": "pending_approval",
                            "closure_rationale": "Concurrent triage update",
                            "recorded_at": reviewed_at.isoformat(),
                        },
                    },
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        updated_case = service.record_case_handoff(
            case_id=promoted_case.case_id,
            handoff_at=reviewed_at,
            handoff_owner="analyst-001",
            handoff_note="Carry forward the next-step evidence review.",
            follow_up_evidence_ids=(evidence_id,),
        )

        self.assertEqual(
            updated_case.reviewed_context["triage"]["disposition"],
            "pending_approval",
        )
        self.assertEqual(
            updated_case.reviewed_context["asset"]["repository"]["repository_full_name"],
            "TommyKammy/AegisOps",
        )
        self.assertEqual(
            updated_case.reviewed_context["identity"]["actor"]["identity_id"],
            "octocat",
        )
        self.assertEqual(
            updated_case.reviewed_context["handoff"]["follow_up_evidence_ids"],
            (evidence_id,),
        )

    def test_service_merges_concurrent_reviewed_context_into_case_disposition(self) -> None:
        store, _ = make_store()
        store, _base_service, promoted_case, _, reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        store = _TransactionMutationStore(
            inner=store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(
                    transactional_store.get(CaseRecord, promoted_case.case_id),
                    reviewed_context={
                        **dict(
                            transactional_store.get(
                                CaseRecord,
                                promoted_case.case_id,
                            ).reviewed_context
                        ),
                        "handoff": {
                            "handoff_at": reviewed_at.isoformat(),
                            "handoff_owner": "analyst-002",
                            "note": "Concurrent handoff note",
                            "follow_up_evidence_ids": (),
                        },
                    },
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        updated_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="pending_approval",
            rationale="Disposition update should preserve concurrent handoff context.",
            recorded_at=reviewed_at,
        )

        self.assertEqual(
            updated_case.reviewed_context["handoff"]["handoff_owner"],
            "analyst-002",
        )
        self.assertEqual(
            updated_case.reviewed_context["asset"]["repository"]["repository_full_name"],
            "TommyKammy/AegisOps",
        )
        self.assertEqual(
            updated_case.reviewed_context["identity"]["actor"]["identity_id"],
            "octocat",
        )
        self.assertEqual(
            updated_case.reviewed_context["triage"]["disposition"],
            "pending_approval",
        )

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
                _load_wazuh_fixture("agent-origin-alert.json")
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

    def test_service_analyst_queue_prefers_explicit_wazuh_source_for_multi_source_linkage(
        self,
    ) -> None:
        self._assert_service_analyst_queue_prefers_wazuh_source_for_multi_source_linkage(
            wazuh_source_system="wazuh"
        )

    def test_service_analyst_queue_accepts_mixed_case_wazuh_source_for_multi_source_linkage(
        self,
    ) -> None:
        self._assert_service_analyst_queue_prefers_wazuh_source_for_multi_source_linkage(
            wazuh_source_system="WaZuH"
        )

    def test_service_alert_detail_prefers_higher_reconciliation_id_when_compared_at_ties(
        self,
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
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(reconciliation)

        preferred_reconciliation = replace(
            reconciliation,
            reconciliation_id=f"{reconciliation.reconciliation_id}-z",
            correlation_key=f"{reconciliation.correlation_key}:z",
        )
        service.persist_record(preferred_reconciliation)

        queue_view = service.inspect_analyst_queue()
        detail = service.inspect_alert_detail(admitted.alert.alert_id)

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(
            queue_view.records[0]["correlation_key"],
            preferred_reconciliation.correlation_key,
        )
        self.assertEqual(
            detail.latest_reconciliation["reconciliation_id"],
            preferred_reconciliation.reconciliation_id,
        )
        self.assertEqual(
            detail.lineage["reconciliation_id"],
            preferred_reconciliation.reconciliation_id,
        )

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
                _load_wazuh_fixture("agent-origin-alert.json")
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

    def test_service_analyst_queue_keeps_latest_wazuh_detection_when_newer_non_wazuh_detection_exists(
        self,
    ) -> None:
        (
            service,
            admitted,
            reviewed_wazuh_reconciliation,
            newer_non_wazuh_reconciliation,
        ) = self._persist_newer_non_wazuh_detection_reconciliation()

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(
            queue_view.records[0]["correlation_key"],
            reviewed_wazuh_reconciliation.correlation_key,
        )
        self.assertNotEqual(
            queue_view.records[0]["correlation_key"],
            newer_non_wazuh_reconciliation.correlation_key,
        )

    def test_service_alert_detail_keeps_latest_wazuh_detection_when_newer_non_wazuh_detection_exists(
        self,
    ) -> None:
        (
            service,
            admitted,
            reviewed_wazuh_reconciliation,
            newer_non_wazuh_reconciliation,
        ) = self._persist_newer_non_wazuh_detection_reconciliation()

        detail = service.inspect_alert_detail(admitted.alert.alert_id)

        self.assertEqual(
            detail.latest_reconciliation["reconciliation_id"],
            reviewed_wazuh_reconciliation.reconciliation_id,
        )
        self.assertEqual(
            detail.lineage["reconciliation_id"],
            reviewed_wazuh_reconciliation.reconciliation_id,
        )
        self.assertNotEqual(
            detail.latest_reconciliation["reconciliation_id"],
            newer_non_wazuh_reconciliation.reconciliation_id,
        )

    def test_service_alert_detail_reports_wazuh_when_origin_is_inferred_from_detection_ids(
        self,
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
                _load_wazuh_fixture("agent-origin-alert.json")
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
            "WaZuH:1731594986.4931506",
        )
        service.persist_record(
            replace(reconciliation, subject_linkage=subject_linkage)
        )

        detail = service.inspect_alert_detail(admitted.alert.alert_id)

        self.assertEqual(detail.source_system, "wazuh")
        self.assertEqual(
            detail.lineage["substrate_detection_record_ids"],
            ("WaZuH:1731594986.4931506",),
        )

    def test_service_alert_detail_redacts_raw_native_payload_from_latest_reconciliation(
        self,
    ) -> None:
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
            raw_alert=_load_wazuh_fixture("github-audit-alert.json"),
            authorization_header=f"Bearer {shared_secret}",
            forwarded_proto="https",
            reverse_proxy_secret_header=reverse_proxy_secret,
            peer_addr="127.0.0.1",
        )
        stored_reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(stored_reconciliation)
        self.assertIn("latest_native_payload", stored_reconciliation.subject_linkage)

        detail = service.inspect_alert_detail(admitted.alert.alert_id)
        detail_subject_linkage = detail.latest_reconciliation["subject_linkage"]

        self.assertIsInstance(detail_subject_linkage, dict)
        self.assertNotIn("latest_native_payload", detail_subject_linkage)
        self.assertEqual(
            detail_subject_linkage["admission_provenance"],
            {
                "admission_channel": "live_wazuh_webhook",
                "admission_kind": "live",
            },
        )

    def test_service_alert_detail_excludes_case_only_sibling_evidence(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        promoted_case = service.promote_alert_to_case(admitted.alert.alert_id)
        sibling_evidence = EvidenceRecord(
            evidence_id="evidence-case-sibling-001",
            source_record_id="case-sibling-source-001",
            alert_id="alert-sibling-001",
            case_id=promoted_case.case_id,
            source_system="wazuh",
            collector_identity="collector://wazuh/live",
            acquired_at=datetime(2026, 4, 11, 14, 0, tzinfo=timezone.utc),
            derivation_relationship="correlated_case_context",
            lifecycle_state="linked",
        )
        service.persist_record(sibling_evidence)

        detail = service.inspect_alert_detail(admitted.alert.alert_id)

        linked_evidence_ids = {
            record["evidence_id"] for record in detail.linked_evidence_records
        }

        self.assertNotIn(sibling_evidence.evidence_id, linked_evidence_ids)
        self.assertNotIn(sibling_evidence.evidence_id, detail.lineage["evidence_ids"])
        self.assertEqual(
            linked_evidence_ids,
            {
                evidence.evidence_id
                for evidence in store.list(EvidenceRecord)
                if evidence.alert_id == admitted.alert.alert_id
            },
        )

    def test_service_analyst_queue_ignores_newer_action_execution_reconciliation(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        admitted = service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-queue-001",
                approval_decision_id="approval-queue-001",
                case_id=None,
                alert_id=admitted.alert.alert_id,
                finding_id=admitted.alert.finding_id,
                idempotency_key="idempotency-queue-001",
                target_scope={"asset_id": "asset-queue-001"},
                payload_hash="payload-hash-queue-001",
                requested_at=datetime(2026, 4, 5, 12, 10, tzinfo=timezone.utc),
                expires_at=None,
                lifecycle_state="approved",
            )
        )
        service.reconcile_action_execution(
            action_request_id="action-request-queue-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-queue-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-queue-001",
                    "observed_at": datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 1)
        self.assertEqual(queue_view.records[0]["alert_id"], admitted.alert.alert_id)
        self.assertEqual(
            queue_view.records[0]["correlation_key"],
            admitted.reconciliation.correlation_key,
        )
        self.assertEqual(queue_view.records[0]["source_system"], "wazuh")

    def test_service_analyst_queue_scans_reconciliations_once_for_multiple_alerts(self) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        adapter = WazuhAlertAdapter()

        service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        service.ingest_native_detection_record(
            adapter,
            adapter.build_native_detection_record(
                _load_wazuh_fixture("github-audit-alert.json")
            ),
        )

        store.reconciliation_list_calls = 0
        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 2)
        self.assertEqual(store.reconciliation_list_calls, 1)

    def test_service_analyst_queue_sorts_unknown_last_seen_after_real_timestamps(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        seen_at = datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc)

        service.persist_record(
            AlertRecord(
                alert_id="alert-known-last-seen",
                finding_id="finding-known-last-seen",
                analytic_signal_id="signal-known-last-seen",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-known-last-seen",
                subject_linkage={
                    "alert_ids": ("alert-known-last-seen",),
                    "analytic_signal_ids": ("signal-known-last-seen",),
                    "substrate_detection_record_ids": ("wazuh:known-last-seen",),
                    "source_systems": ("wazuh",),
                },
                alert_id="alert-known-last-seen",
                finding_id="finding-known-last-seen",
                analytic_signal_id="signal-known-last-seen",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="wazuh:known-last-seen",
                first_seen_at=seen_at,
                last_seen_at=seen_at,
                ingest_disposition="created",
                mismatch_summary="known last-seen timestamp",
                compared_at=seen_at,
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            AlertRecord(
                alert_id="alert-unknown-last-seen",
                finding_id="finding-unknown-last-seen",
                analytic_signal_id="signal-unknown-last-seen",
                case_id=None,
                lifecycle_state="new",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-unknown-last-seen",
                subject_linkage={
                    "alert_ids": ("alert-unknown-last-seen",),
                    "analytic_signal_ids": ("signal-unknown-last-seen",),
                    "substrate_detection_record_ids": ("wazuh:unknown-last-seen",),
                    "source_systems": ("wazuh",),
                },
                alert_id="alert-unknown-last-seen",
                finding_id="finding-unknown-last-seen",
                analytic_signal_id="signal-unknown-last-seen",
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="wazuh:unknown-last-seen",
                first_seen_at=seen_at,
                last_seen_at=None,
                ingest_disposition="created",
                mismatch_summary="unknown last-seen timestamp",
                compared_at=seen_at,
                lifecycle_state="matched",
            )
        )

        queue_view = service.inspect_analyst_queue()

        self.assertEqual(queue_view.total_records, 2)
        self.assertEqual(
            tuple(record["alert_id"] for record in queue_view.records),
            ("alert-known-last-seen", "alert-unknown-last-seen"),
        )

    def test_service_rejects_schema_invalid_records_before_they_are_inspectable(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            service.persist_record(
                AlertRecord(
                    alert_id="alert-invalid",
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    case_id=None,
                    lifecycle_state="invalid",
                )
            )

        with self.assertRaises(ValueError):
            service.persist_record(
                ReconciliationRecord(
                    reconciliation_id="reconciliation-invalid",
                    subject_linkage={"action_request_ids": ["action-request-001"]},
                    alert_id=None,
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    execution_run_id=None,
                    linked_execution_run_ids=(),
                    correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
                    first_seen_at=timestamp,
                    last_seen_at=timestamp,
                    ingest_disposition="invalid",
                    mismatch_summary="invalid disposition",
                    compared_at=timestamp,
                    lifecycle_state="matched",
                )
            )

        alert_snapshot = service.inspect_records("alert")
        reconciliation_snapshot = service.inspect_records("reconciliation")

        self.assertEqual(alert_snapshot.total_records, 0)
        self.assertEqual(alert_snapshot.records, ())
        self.assertIsNone(service.get_record(AlertRecord, "alert-invalid"))
        self.assertEqual(reconciliation_snapshot.total_records, 0)
        self.assertEqual(reconciliation_snapshot.records, ())
        self.assertIsNone(
            service.get_record(ReconciliationRecord, "reconciliation-invalid")
        )

    def test_service_upserts_alert_lifecycle_from_upstream_signals(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        first_seen = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        restated_seen = datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc)
        updated_seen = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        duplicate_seen = datetime(2026, 4, 5, 12, 45, tzinfo=timezone.utc)

        created = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=first_seen,
        )
        restated = service.ingest_finding_alert(
            finding_id="finding-002",
            analytic_signal_id="signal-002",
            substrate_detection_record_id="substrate-detection-002",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=restated_seen,
        )
        updated = service.ingest_finding_alert(
            finding_id="finding-003",
            analytic_signal_id="signal-003",
            substrate_detection_record_id="substrate-detection-003",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=updated_seen,
            last_seen_at=updated_seen,
            materially_new_work=True,
        )
        deduplicated = service.ingest_finding_alert(
            finding_id="finding-003",
            analytic_signal_id="signal-003",
            substrate_detection_record_id="substrate-detection-003",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=updated_seen,
            last_seen_at=duplicate_seen,
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(updated.disposition, "updated")
        self.assertEqual(deduplicated.disposition, "deduplicated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(updated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(deduplicated.alert.alert_id, created.alert.alert_id)
        self.assertEqual(restated.alert.finding_id, "finding-001")
        self.assertEqual(restated.alert.analytic_signal_id, "signal-001")
        self.assertEqual(updated.alert.finding_id, "finding-003")
        self.assertEqual(updated.alert.analytic_signal_id, "signal-003")
        self.assertEqual(deduplicated.alert.finding_id, "finding-003")
        self.assertEqual(deduplicated.alert.analytic_signal_id, "signal-003")

        stored_alert = service.get_record(AlertRecord, created.alert.alert_id)
        self.assertEqual(stored_alert, updated.alert)
        self.assertEqual(stored_alert.lifecycle_state, "new")

        created_reconciliation = service.get_record(
            ReconciliationRecord, created.reconciliation.reconciliation_id
        )
        restated_reconciliation = service.get_record(
            ReconciliationRecord, restated.reconciliation.reconciliation_id
        )
        updated_reconciliation = service.get_record(
            ReconciliationRecord, updated.reconciliation.reconciliation_id
        )
        deduplicated_reconciliation = service.get_record(
            ReconciliationRecord, deduplicated.reconciliation.reconciliation_id
        )
        self.assertEqual(created_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(created_reconciliation.ingest_disposition, "created")
        self.assertEqual(created_reconciliation.first_seen_at, first_seen)
        self.assertEqual(created_reconciliation.last_seen_at, first_seen)
        self.assertEqual(restated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(restated_reconciliation.ingest_disposition, "restated")
        self.assertEqual(restated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(restated_reconciliation.last_seen_at, restated_seen)
        self.assertEqual(
            restated_reconciliation.subject_linkage["finding_ids"],
            ("finding-001", "finding-002"),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002"),
        )
        self.assertEqual(
            restated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-detection-001", "substrate-detection-002"),
        )
        self.assertEqual(updated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(updated_reconciliation.ingest_disposition, "updated")
        self.assertEqual(updated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(updated_reconciliation.last_seen_at, updated_seen)
        self.assertEqual(
            updated_reconciliation.subject_linkage["finding_ids"],
            ("finding-001", "finding-002", "finding-003"),
        )
        self.assertEqual(
            updated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002", "signal-003"),
        )
        self.assertEqual(
            updated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            (
                "substrate-detection-001",
                "substrate-detection-002",
                "substrate-detection-003",
            ),
        )
        self.assertEqual(deduplicated_reconciliation.alert_id, created.alert.alert_id)
        self.assertEqual(
            deduplicated_reconciliation.ingest_disposition, "deduplicated"
        )
        self.assertEqual(deduplicated_reconciliation.first_seen_at, first_seen)
        self.assertEqual(deduplicated_reconciliation.last_seen_at, duplicate_seen)
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["finding_ids"],
            ("finding-001", "finding-002", "finding-003"),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002", "signal-003"),
        )
        self.assertEqual(
            deduplicated_reconciliation.subject_linkage["substrate_detection_record_ids"],
            (
                "substrate-detection-001",
                "substrate-detection-002",
                "substrate-detection-003",
            ),
        )

        signal_one = service.get_record(AnalyticSignalRecord, "signal-001")
        signal_two = service.get_record(AnalyticSignalRecord, "signal-002")
        signal_three = service.get_record(AnalyticSignalRecord, "signal-003")

        self.assertEqual(signal_one.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_one.case_ids, ())
        self.assertEqual(signal_one.finding_id, "finding-001")
        self.assertEqual(
            signal_one.substrate_detection_record_id,
            "substrate-detection-001",
        )
        self.assertEqual(signal_one.correlation_key, "claim:host-001:privilege-escalation")
        self.assertEqual(signal_one.first_seen_at, first_seen)
        self.assertEqual(signal_one.last_seen_at, first_seen)

        self.assertEqual(signal_two.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_two.finding_id, "finding-002")
        self.assertEqual(
            signal_two.substrate_detection_record_id,
            "substrate-detection-002",
        )
        self.assertEqual(signal_two.first_seen_at, first_seen)
        self.assertEqual(signal_two.last_seen_at, restated_seen)

        self.assertEqual(signal_three.alert_ids, (created.alert.alert_id,))
        self.assertEqual(signal_three.finding_id, "finding-003")
        self.assertEqual(
            signal_three.substrate_detection_record_id,
            "substrate-detection-003",
        )
        self.assertEqual(signal_three.first_seen_at, updated_seen)
        self.assertEqual(signal_three.last_seen_at, duplicate_seen)

    def test_service_restates_when_repeated_finding_adds_new_signal_identity(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        second_seen = datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc)

        created = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=first_seen,
        )
        restated = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="signal-002",
            substrate_detection_record_id="substrate-detection-002",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen,
            last_seen_at=second_seen,
        )

        self.assertEqual(created.disposition, "created")
        self.assertEqual(restated.disposition, "restated")
        self.assertEqual(restated.alert.alert_id, created.alert.alert_id)

        reconciliation = service.get_record(
            ReconciliationRecord, restated.reconciliation.reconciliation_id
        )
        self.assertEqual(reconciliation.ingest_disposition, "restated")
        self.assertEqual(
            reconciliation.subject_linkage["finding_ids"],
            ("finding-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            ("signal-001", "signal-002"),
        )
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            ("substrate-detection-001", "substrate-detection-002"),
        )

    def test_service_rejects_naive_intake_timestamps(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(ValueError, "first_seen_at must be timezone-aware"):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0),
                last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
            )

        with self.assertRaisesRegex(ValueError, "last_seen_at must be timezone-aware"):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 15),
            )

    def test_service_rejects_inverted_intake_timestamps(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "last_seen_at must be greater than or equal to first_seen_at",
        ):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
            )

    def test_service_rejects_blank_required_admission_identities(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        with self.assertRaisesRegex(ValueError, "finding_id must be a non-empty string"):
            service.ingest_finding_alert(
                finding_id="   ",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
            )

        with self.assertRaisesRegex(
            ValueError,
            "correlation_key must be a non-empty string",
        ):
            service.ingest_finding_alert(
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                correlation_key=" \t ",
                first_seen_at=first_seen_at,
                last_seen_at=first_seen_at,
            )

    def test_service_mints_analytic_signal_identity_when_admission_leaves_it_blank(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        first_seen_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        admitted = service.ingest_finding_alert(
            finding_id="finding-001",
            analytic_signal_id="   ",
            substrate_detection_record_id="",
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=first_seen_at,
            last_seen_at=first_seen_at,
        )

        self.assertEqual(admitted.disposition, "created")
        self.assertIsNotNone(admitted.alert.analytic_signal_id)
        self.assertTrue(admitted.alert.analytic_signal_id.startswith("analytic-signal-"))

        signals = store.list(AnalyticSignalRecord)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].analytic_signal_id, admitted.alert.analytic_signal_id)
        self.assertIsNone(signals[0].substrate_detection_record_id)
        self.assertEqual(signals[0].finding_id, "finding-001")

        reconciliation = service.get_record(
            ReconciliationRecord, admitted.reconciliation.reconciliation_id
        )
        self.assertEqual(
            reconciliation.analytic_signal_id,
            admitted.alert.analytic_signal_id,
        )
        self.assertEqual(
            reconciliation.subject_linkage["analytic_signal_ids"],
            (admitted.alert.analytic_signal_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["substrate_detection_record_ids"],
            (),
        )

    def test_service_inspects_analytic_signal_records_as_first_class_records(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        analytic_signal = AnalyticSignalRecord(
            analytic_signal_id="signal-001",
            substrate_detection_record_id="substrate-detection-001",
            finding_id="finding-001",
            alert_ids=("alert-001",),
            case_ids=("case-001",),
            correlation_key="claim:host-001:privilege-escalation",
            first_seen_at=datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 5, 12, 15, tzinfo=timezone.utc),
            lifecycle_state="active",
        )

        service.persist_record(analytic_signal)

        self.assertEqual(
            service.get_record(AnalyticSignalRecord, "signal-001"),
            analytic_signal,
        )

        inspection = service.inspect_records("analytic_signal")

        self.assertTrue(inspection.read_only)
        self.assertEqual(inspection.record_family, "analytic_signal")
        self.assertEqual(inspection.total_records, 1)
        self.assertEqual(
            inspection.records[0]["analytic_signal_id"],
            "signal-001",
        )
        self.assertEqual(
            inspection.records[0]["substrate_detection_record_id"],
            "substrate-detection-001",
        )

    def test_service_records_execution_correlation_mismatch_states_separately(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                opensearch_url="https://opensearch.internal",
                n8n_base_url="https://n8n.internal",
            ),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        stale_cutoff = datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        missing = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(),
            compared_at=requested_at,
            stale_after=stale_cutoff,
        )
        duplicate = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                    "status": "running",
                },
                {
                    "execution_run_id": "exec-002",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
                    "status": "running",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )
        mismatched = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-003",
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-999",
                    "observed_at": datetime(2026, 4, 5, 12, 10, tzinfo=timezone.utc),
                    "status": "failed",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 10, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )
        stale = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-004",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 20, tzinfo=timezone.utc),
                    "status": "success",
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 45, tzinfo=timezone.utc),
            stale_after=stale_cutoff,
        )

        self.assertEqual(missing.lifecycle_state, "pending")
        self.assertEqual(missing.ingest_disposition, "missing")
        self.assertEqual(missing.execution_run_id, None)
        self.assertIn("missing downstream execution", missing.mismatch_summary)
        self.assertEqual(
            missing.subject_linkage["action_request_ids"], ("action-request-001",)
        )
        self.assertEqual(
            missing.subject_linkage["execution_surface_types"],
            ("automation_substrate",),
        )
        self.assertEqual(
            missing.subject_linkage["execution_surface_ids"], ("n8n",)
        )

        self.assertEqual(duplicate.lifecycle_state, "mismatched")
        self.assertEqual(duplicate.ingest_disposition, "duplicate")
        self.assertEqual(duplicate.execution_run_id, "exec-002")
        self.assertEqual(
            duplicate.linked_execution_run_ids,
            ("exec-001", "exec-002"),
        )
        self.assertIn("duplicate downstream executions", duplicate.mismatch_summary)

        self.assertEqual(mismatched.lifecycle_state, "mismatched")
        self.assertEqual(mismatched.ingest_disposition, "mismatch")
        self.assertEqual(mismatched.execution_run_id, "exec-003")
        self.assertIn(
            "execution surface/idempotency mismatch",
            mismatched.mismatch_summary,
        )

        self.assertEqual(stale.lifecycle_state, "stale")
        self.assertEqual(stale.ingest_disposition, "stale")
        self.assertEqual(stale.execution_run_id, "exec-004")
        self.assertIn("stale downstream execution observation", stale.mismatch_summary)

        stored_reconciliations = store.list(ReconciliationRecord)
        self.assertEqual(len(stored_reconciliations), 4)
        self.assertEqual(
            sorted(record.ingest_disposition for record in stored_reconciliations),
            ["duplicate", "mismatch", "missing", "stale"],
        )
        self.assertEqual(
            service.get_record(ActionRequestRecord, "action-request-001"),
            action_request,
        )

    def test_service_reconcile_action_execution_rejects_non_approved_requests(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-pending",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="pending_approval",
        )
        service.persist_record(action_request)

        with self.assertRaisesRegex(ValueError, "is not approved"):
            service.reconcile_action_execution(
                action_request_id="action-request-pending",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                observed_executions=(),
                compared_at=requested_at,
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

    def test_service_reconcile_action_execution_requires_aware_datetimes(self) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        with self.assertRaisesRegex(ValueError, "compared_at must be timezone-aware"):
            service.reconcile_action_execution(
                action_request_id="action-request-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                observed_executions=(),
                compared_at=datetime(2026, 4, 5, 12, 0),
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

        with self.assertRaisesRegex(ValueError, "observed_at must be timezone-aware"):
            service.reconcile_action_execution(
                action_request_id="action-request-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="n8n",
                observed_executions=(
                    {
                        "execution_run_id": "exec-001",
                        "execution_surface_id": "n8n",
                        "idempotency_key": "idempotency-001",
                        "observed_at": datetime(2026, 4, 5, 12, 5),
                    },
                ),
                compared_at=requested_at,
                stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
            )

    def test_service_reconcile_action_execution_ignores_repeated_polls_of_same_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            observed_executions=(
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
                {
                    "execution_run_id": "exec-001",
                    "execution_surface_id": "n8n",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 6, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.execution_run_id, "exec-001")
        self.assertEqual(
            reconciliation.linked_execution_run_ids,
            ("exec-001", "exec-001"),
        )

    def test_service_reconcile_action_execution_supports_generic_execution_surfaces(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id=None,
            alert_id=None,
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            payload_hash="payload-hash-001",
            requested_at=requested_at,
            expires_at=None,
            lifecycle_state="approved",
        )
        service.persist_record(action_request)

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-001",
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
            observed_executions=(
                {
                    "execution_run_id": "executor-run-001",
                    "execution_surface_id": "isolated-executor",
                    "idempotency_key": "idempotency-001",
                    "observed_at": datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                },
            ),
            compared_at=datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.execution_run_id, "executor-run-001")
        self.assertEqual(
            reconciliation.linked_execution_run_ids,
            ("executor-run-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["execution_surface_types"],
            ("executor",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["execution_surface_ids"],
            ("isolated-executor",),
        )

    def test_service_reconciles_shuffle_run_back_into_authoritative_action_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 12, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-reconcile-001",
                action_request_id="action-request-routine-reconcile-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-reconcile-001",
                approval_decision_id="approval-routine-reconcile-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-reconcile-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-routine-reconcile-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-001",),
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-routine-reconcile-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": "idempotency-routine-reconcile-001",
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "succeeded")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["evidence_ids"],
            ("evidence-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["delegation_ids"],
            (execution.delegation_id,),
        )
        self.assertEqual(
            reconciliation.correlation_key,
            (
                "action-request-routine-reconcile-001:approval-routine-reconcile-001:"
                f"{execution.delegation_id}:automation_substrate:shuffle:"
                "idempotency-routine-reconcile-001"
            ),
        )

    def test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 14, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-003"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-003",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-reconcile-001",
                action_request_id="action-request-executor-reconcile-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-reconcile-001",
                approval_decision_id="approval-executor-reconcile-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-reconcile-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        execution = service.delegate_approved_action_to_isolated_executor(
            action_request_id="action-request-executor-reconcile-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-002",),
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-executor-reconcile-001",
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "isolated-executor",
                    "idempotency_key": "idempotency-executor-reconcile-001",
                    "observed_at": compared_at,
                    "status": "failed",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "failed")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["evidence_ids"],
            ("evidence-002",),
        )

    def test_service_reconciliation_mismatch_does_not_mutate_authoritative_execution(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 12, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-reconcile-mismatch-001",
                action_request_id="action-request-routine-reconcile-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-reconcile-mismatch-001",
                approval_decision_id="approval-routine-reconcile-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-reconcile-mismatch-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-routine-reconcile-mismatch-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-003",),
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-routine-reconcile-mismatch-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "n8n",
                    "idempotency_key": execution.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": compared_at,
                    "status": "failed",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)

    def test_service_reconciliation_fail_closes_when_downstream_run_identity_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 12, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-reconcile-run-drift-001",
                action_request_id="action-request-routine-reconcile-run-drift-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-reconcile-run-drift-001",
                approval_decision_id="approval-routine-reconcile-run-drift-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-reconcile-run-drift-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-routine-reconcile-run-drift-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-004",),
        )

        reconciliation = service.reconcile_action_execution(
            action_request_id="action-request-routine-reconcile-run-drift-001",
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": "shuffle-run-unexpected-001",
                    "execution_surface_id": "shuffle",
                    "idempotency_key": execution.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": compared_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=datetime(2026, 4, 5, 12, 30, tzinfo=timezone.utc),
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertIn("run identity mismatch", reconciliation.mismatch_summary)
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(stored_execution.execution_run_id, execution.execution_run_id)

    def test_service_evaluates_action_policy_into_approval_and_isolated_executor(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-policy-high-risk",
                approval_decision_id=None,
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-policy-high-risk",
                target_scope={"asset_id": "prod-domain-controller-001"},
                payload_hash="payload-hash-policy-high-risk",
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="draft",
                policy_basis={
                    "severity": "critical",
                    "target_scope": "single_asset",
                    "action_reversibility": "irreversible",
                    "asset_criticality": "critical",
                    "identity_criticality": "high",
                    "blast_radius": "organization",
                    "execution_constraint": "requires_isolated_executor",
                },
            )
        )

        evaluated = service.evaluate_action_policy(
            "action-request-policy-high-risk"
        )

        self.assertEqual(
            evaluated.policy_evaluation,
            {
                "approval_requirement": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "executor",
                "execution_surface_id": "isolated-executor",
            },
        )
        self.assertEqual(
            service.get_record(
                ActionRequestRecord, "action-request-policy-high-risk"
            ),
            evaluated,
        )

    def test_service_evaluates_action_policy_into_shuffle_without_human_approval(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-policy-routine",
                approval_decision_id=None,
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-policy-routine",
                target_scope={"asset_id": "workstation-001"},
                payload_hash="payload-hash-policy-routine",
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="draft",
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_asset",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
            )
        )

        evaluated = service.evaluate_action_policy("action-request-policy-routine")

        self.assertEqual(
            evaluated.policy_evaluation,
            {
                "approval_requirement": "policy_authorized",
                "routing_target": "shuffle",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )

    def test_service_delegates_approved_low_risk_action_through_shuffle_adapter(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-001",
                action_request_id="action-request-routine-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-001",
                approval_decision_id="approval-routine-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_asset",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id="action-request-routine-001",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-001",),
        )

        self.assertEqual(
            execution.action_request_id,
            "action-request-routine-001",
        )
        self.assertEqual(
            execution.approval_decision_id,
            "approval-routine-001",
        )
        self.assertEqual(execution.execution_surface_type, "automation_substrate")
        self.assertEqual(execution.execution_surface_id, "shuffle")
        self.assertEqual(
            execution.idempotency_key,
            "idempotency-routine-001",
        )
        self.assertEqual(execution.payload_hash, payload_hash)
        self.assertEqual(
            execution.approved_payload,
            _phase20_notify_identity_owner_payload(
                recipient_identity="repo-owner-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
            ),
        )
        self.assertEqual(
            execution.provenance,
            {
                "delegation_issuer": "control-plane-service",
                "evidence_ids": ("evidence-001",),
                "adapter": "shuffle",
                "downstream_binding": {
                    "approval_decision_id": "approval-routine-001",
                    "delegation_id": execution.delegation_id,
                    "payload_hash": payload_hash,
                },
            },
        )
        self.assertEqual(execution.lifecycle_state, "queued")
        self.assertTrue(execution.delegation_id.startswith("delegation-"))
        self.assertTrue(execution.execution_run_id.startswith("shuffle-run-"))
        self.assertEqual(
            service.get_record(ActionExecutionRecord, execution.action_execution_id),
            execution,
        )

    def test_service_does_not_emit_action_execution_delegated_log_before_commit(
        self,
    ) -> None:
        base_store, _ = make_store()
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        seed_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=base_store,
        )
        seed_service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-commit-failure-001",
                action_request_id="action-request-routine-commit-failure-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        seed_service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-commit-failure-001",
                approval_decision_id="approval-routine-commit-failure-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-commit-failure-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_asset",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
                requested_payload=approved_payload,
            )
        )
        failing_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=_CommitFailingStore(base_store),
        )

        with mock.patch.object(failing_service, "_emit_structured_event") as emit_event:
            with self.assertRaisesRegex(RuntimeError, "synthetic commit failure"):
                failing_service.delegate_approved_action_to_shuffle(
                    action_request_id="action-request-routine-commit-failure-001",
                    approved_payload=approved_payload,
                    delegated_at=delegated_at,
                    delegation_issuer="control-plane-service",
                )

        emit_event.assert_not_called()
        self.assertEqual(base_store.list(ActionExecutionRecord), ())

    def test_service_rechecks_shuffle_approval_inside_transaction(self) -> None:
        inner_store, _ = make_store()
        seed_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=inner_store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
        )
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval_decision = ApprovalDecisionRecord(
            approval_decision_id="approval-routine-tx-recheck-001",
            action_request_id="action-request-routine-tx-recheck-001",
            approver_identities=("approver-001",),
            target_snapshot=approved_target_scope,
            payload_hash=payload_hash,
            decided_at=requested_at,
            lifecycle_state="approved",
        )
        seed_service.persist_record(approval_decision)
        seed_service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-tx-recheck-001",
                approval_decision_id="approval-routine-tx-recheck-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-tx-recheck-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        store = _TransactionMutationStore(
            inner=inner_store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(approval_decision, lifecycle_state="rejected")
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "Approval decision 'approval-routine-tx-recheck-001' is not approved",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-tx-recheck-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(inner_store.list(ActionExecutionRecord), ())

    def test_service_rejects_shuffle_delegation_when_payload_binding_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-001"}
        approved_payload = {
            "action_type": "notify_identity_owner",
            "asset_id": "workstation-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-mismatch-001",
                action_request_id="action-request-routine-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-mismatch-001",
                approval_decision_id="approval-routine-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-mismatch-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-mismatch-001",
                approved_payload={
                    "action_type": "notify_identity_owner",
                    "asset_id": "workstation-999",
                },
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_shuffle_delegation_when_expiry_window_drifts_after_approval(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        drifted_expires_at = datetime(2026, 4, 5, 14, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-expiry-001"}
        approved_payload = {
            "action_type": "notify_identity_owner",
            "asset_id": "workstation-expiry-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        approval_decision = ApprovalDecisionRecord(
            approval_decision_id="approval-routine-expiry-drift-001",
            action_request_id="action-request-routine-expiry-drift-001",
            approver_identities=("approver-001",),
            target_snapshot=approved_target_scope,
            payload_hash=payload_hash,
            decided_at=requested_at,
            lifecycle_state="approved",
            approved_expires_at=approved_expires_at,
        )
        action_request = ActionRequestRecord(
            action_request_id="action-request-routine-expiry-drift-001",
            approval_decision_id="approval-routine-expiry-drift-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-routine-expiry-drift-001",
            target_scope=approved_target_scope,
            payload_hash=payload_hash,
            requested_at=requested_at,
            expires_at=approved_expires_at,
            lifecycle_state="approved",
            policy_evaluation={
                "approval_requirement": "human_required",
                "routing_target": "shuffle",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )
        service.persist_record(approval_decision)
        service.persist_record(action_request)
        service.persist_record(replace(action_request, expires_at=drifted_expires_at))

        with self.assertRaisesRegex(
            ValueError,
            "approved expiry window does not match action request expiry",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-expiry-drift-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_isolated_executor_delegation_when_expiry_window_drifts_after_approval(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        drifted_expires_at = datetime(2026, 4, 5, 14, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-expiry-001"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-expiry-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        approval_decision = ApprovalDecisionRecord(
            approval_decision_id="approval-executor-expiry-drift-001",
            action_request_id="action-request-executor-expiry-drift-001",
            approver_identities=("approver-001",),
            target_snapshot=approved_target_scope,
            payload_hash=payload_hash,
            decided_at=requested_at,
            lifecycle_state="approved",
            approved_expires_at=approved_expires_at,
        )
        action_request = ActionRequestRecord(
            action_request_id="action-request-executor-expiry-drift-001",
            approval_decision_id="approval-executor-expiry-drift-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-executor-expiry-drift-001",
            target_scope=approved_target_scope,
            payload_hash=payload_hash,
            requested_at=requested_at,
            expires_at=approved_expires_at,
            lifecycle_state="approved",
            policy_evaluation={
                "approval_requirement": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "executor",
                "execution_surface_id": "isolated-executor",
            },
        )
        service.persist_record(approval_decision)
        service.persist_record(action_request)
        service.persist_record(replace(action_request, expires_at=drifted_expires_at))

        with self.assertRaisesRegex(
            ValueError,
            "approved expiry window does not match action request expiry",
        ):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-expiry-drift-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_shuffle_delegation_when_target_scope_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approval_target_scope = {"asset_id": "workstation-001"}
        requested_target_scope = {"asset_id": "workstation-777"}
        approved_payload = {
            "action_type": "notify_identity_owner",
            "asset_id": "workstation-001",
        }
        payload_hash = _approved_binding_hash(
            target_scope=requested_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-target-mismatch-001",
                action_request_id="action-request-routine-target-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-target-mismatch-001",
                approval_decision_id="approval-routine-target-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-target-mismatch-001",
                target_scope=requested_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-target-mismatch-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_shuffle_delegation_for_non_shuffle_execution_policy(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-001",
                action_request_id="action-request-executor-001",
                approver_identities=("approver-001",),
                target_snapshot={"asset_id": "critical-host-001"},
                payload_hash="payload-hash-executor-001",
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-001",
                approval_decision_id="approval-executor-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-001",
                target_scope={"asset_id": "critical-host-001"},
                payload_hash="payload-hash-executor-001",
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "not delegated through the automation substrate path",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-executor-001",
                approved_payload={"action_type": "disable_identity"},
                delegated_at=datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                delegation_issuer="control-plane-service",
            )

    def test_service_rejects_shuffle_delegation_for_non_phase20_live_action(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "workstation-unsupported-001"}
        approved_payload = {
            "action_type": "open_ticket",
            "asset_id": "workstation-unsupported-001",
            "ticket_queue": "soc-owner-followup",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-routine-unsupported-action-001",
                action_request_id="action-request-routine-unsupported-action-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-routine-unsupported-action-001",
                approval_decision_id="approval-routine-unsupported-action-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-routine-unsupported-action-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "shuffle",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "approved action is outside the reviewed Phase 20 Shuffle delegation scope",
        ):
            service.delegate_approved_action_to_shuffle(
                action_request_id="action-request-routine-unsupported-action-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_delegates_approved_high_risk_action_through_isolated_executor(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-002"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-002",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-002",
                action_request_id="action-request-executor-002",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-002",
                approval_decision_id="approval-executor-002",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-002",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_basis={
                    "severity": "critical",
                    "target_scope": "single_asset",
                    "action_reversibility": "irreversible",
                    "asset_criticality": "critical",
                    "identity_criticality": "high",
                    "blast_radius": "organization",
                    "execution_constraint": "requires_isolated_executor",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        execution = service.delegate_approved_action_to_isolated_executor(
            action_request_id="action-request-executor-002",
            approved_payload=approved_payload,
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=("evidence-002",),
        )

        self.assertEqual(execution.action_request_id, "action-request-executor-002")
        self.assertEqual(execution.approval_decision_id, "approval-executor-002")
        self.assertEqual(execution.execution_surface_type, "executor")
        self.assertEqual(execution.execution_surface_id, "isolated-executor")
        self.assertEqual(execution.idempotency_key, "idempotency-executor-002")
        self.assertEqual(execution.payload_hash, payload_hash)
        self.assertEqual(
            execution.approved_payload,
            {
                "action_type": "disable_identity",
                "asset_id": "critical-host-002",
            },
        )
        self.assertEqual(
            execution.provenance,
            {
                "delegation_issuer": "control-plane-service",
                "evidence_ids": ("evidence-002",),
                "adapter": "isolated-executor",
            },
        )
        self.assertEqual(execution.lifecycle_state, "queued")
        self.assertTrue(execution.delegation_id.startswith("delegation-"))
        self.assertTrue(execution.execution_run_id.startswith("executor-run-"))
        self.assertEqual(
            service.get_record(ActionExecutionRecord, execution.action_execution_id),
            execution,
        )

    def test_service_emits_action_execution_delegated_log_for_isolated_executor(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        expires_at = datetime(2026, 4, 5, 13, 0, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-003"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-003",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-log-001",
                action_request_id="action-request-executor-log-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-log-001",
                approval_decision_id="approval-executor-log-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-log-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                policy_basis={
                    "severity": "critical",
                    "target_scope": "single_asset",
                    "action_reversibility": "irreversible",
                    "asset_criticality": "critical",
                    "identity_criticality": "high",
                    "blast_radius": "organization",
                    "execution_constraint": "requires_isolated_executor",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with mock.patch.object(service, "_emit_structured_event") as emit_event:
            execution = service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-log-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        emit_event.assert_called_once_with(
            logging.INFO,
            "action_execution_delegated",
            action_execution_id=execution.action_execution_id,
            action_request_id=execution.action_request_id,
            approval_decision_id=execution.approval_decision_id,
            execution_surface_type=execution.execution_surface_type,
            execution_surface_id=execution.execution_surface_id,
            execution_run_id=execution.execution_run_id,
            lifecycle_state=execution.lifecycle_state,
        )

    def test_service_rejects_isolated_executor_delegation_for_cross_linked_approval(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-002"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-002",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-cross-link-001",
                action_request_id="action-request-executor-cross-link-other",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-cross-link-001",
                approval_decision_id="approval-executor-cross-link-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-cross-link-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-cross-link-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_isolated_executor_delegation_when_payload_binding_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approved_target_scope = {"asset_id": "critical-host-002"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-002",
        }
        payload_hash = _approved_binding_hash(
            target_scope=approved_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-mismatch-001",
                action_request_id="action-request-executor-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approved_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-mismatch-001",
                approval_decision_id="approval-executor-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-mismatch-001",
                target_scope=approved_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-mismatch-001",
                approved_payload={
                    "action_type": "disable_account",
                    "asset_id": "critical-host-002",
                },
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_rejects_isolated_executor_delegation_when_target_scope_drifts(
        self,
    ) -> None:
        store, _ = make_store()
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        delegated_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        approval_target_scope = {"asset_id": "critical-host-002"}
        requested_target_scope = {"asset_id": "critical-host-999"}
        approved_payload = {
            "action_type": "disable_identity",
            "asset_id": "critical-host-002",
        }
        payload_hash = _approved_binding_hash(
            target_scope=requested_target_scope,
            approved_payload=approved_payload,
            execution_surface_type="executor",
            execution_surface_id="isolated-executor",
        )
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-executor-target-mismatch-001",
                action_request_id="action-request-executor-target-mismatch-001",
                approver_identities=("approver-001",),
                target_snapshot=approval_target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-executor-target-mismatch-001",
                approval_decision_id="approval-executor-target-mismatch-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-executor-target-mismatch-001",
                target_scope=requested_target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=None,
                lifecycle_state="approved",
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "executor",
                    "execution_surface_id": "isolated-executor",
                },
            )
        )

        with self.assertRaisesRegex(ValueError, "approved payload binding does not match"):
            service.delegate_approved_action_to_isolated_executor(
                action_request_id="action-request-executor-target-mismatch-001",
                approved_payload=approved_payload,
                delegated_at=delegated_at,
                delegation_issuer="control-plane-service",
            )

        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_creates_approval_bound_action_request_from_reviewed_recommendation(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertIsNone(action_request.approval_decision_id)
        self.assertEqual(action_request.case_id, promoted_case.case_id)
        self.assertEqual(action_request.alert_id, promoted_case.alert_id)
        self.assertEqual(action_request.finding_id, promoted_case.finding_id)
        self.assertEqual(action_request.requester_identity, "analyst-001")
        self.assertEqual(
            action_request.target_scope,
            {
                "record_family": "recommendation",
                "record_id": recommendation.recommendation_id,
                "case_id": promoted_case.case_id,
                "alert_id": promoted_case.alert_id,
                "finding_id": promoted_case.finding_id,
                "recipient_identity": "repo-owner-001",
            },
        )
        self.assertEqual(
            action_request.requested_payload,
            {
                "action_type": "notify_identity_owner",
                "recipient_identity": "repo-owner-001",
                "message_intent": "Notify the accountable repository owner about the reviewed permission change.",
                "escalation_reason": "Reviewed GitHub audit evidence requires bounded owner notification.",
                "source_record_family": "recommendation",
                "source_record_id": recommendation.recommendation_id,
                "recommendation_id": recommendation.recommendation_id,
                "case_id": promoted_case.case_id,
                "alert_id": promoted_case.alert_id,
                "finding_id": promoted_case.finding_id,
                "linked_evidence_ids": (evidence_id,),
            },
        )
        self.assertEqual(
            action_request.payload_hash,
            _approved_binding_hash(
                target_scope=dict(action_request.target_scope),
                approved_payload=dict(action_request.requested_payload),
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
            ),
        )
        self.assertEqual(action_request.expires_at, expires_at)
        self.assertEqual(action_request.lifecycle_state, "pending_approval")
        self.assertEqual(
            action_request.policy_evaluation,
            {
                "approval_requirement": "human_required",
                "routing_target": "approval",
                "execution_surface_type": "automation_substrate",
                "execution_surface_id": "shuffle",
            },
        )
        self.assertEqual(
            service.get_record(ActionRequestRecord, action_request.action_request_id),
            action_request,
        )
        self.assertEqual(store.list(ActionExecutionRecord), ())

    def test_service_does_not_emit_action_request_created_log_before_commit(
        self,
    ) -> None:
        base_store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Prepare a reviewed owner notification request.",
        )
        failing_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=_CommitFailingStore(base_store),
        )
        baseline_requests = base_store.list(ActionRequestRecord)

        with mock.patch.object(failing_service, "_emit_structured_event") as emit_event:
            with self.assertRaisesRegex(RuntimeError, "synthetic commit failure"):
                failing_service.create_reviewed_action_request_from_advisory(
                    record_family="recommendation",
                    record_id=recommendation.recommendation_id,
                    requester_identity="analyst-001",
                    recipient_identity="repo-owner-001",
                    message_intent="Notify the repository owner about the reviewed change.",
                    escalation_reason="Reviewed low-risk action remains approval-bound.",
                    expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
                )

        emit_event.assert_not_called()
        self.assertEqual(base_store.list(ActionRequestRecord), baseline_requests)

    def test_service_executes_phase20_first_live_action_end_to_end_from_reviewed_recommendation(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-e2e-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertEqual(
            approved_request.requested_payload["action_type"],
            "notify_identity_owner",
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "succeeded")
        self.assertEqual(stored_execution.approval_decision_id, "approval-phase20-e2e-001")
        self.assertEqual(stored_execution.execution_surface_type, "automation_substrate")
        self.assertEqual(stored_execution.execution_surface_id, "shuffle")
        self.assertEqual(reconciliation.ingest_disposition, "matched")
        self.assertEqual(reconciliation.lifecycle_state, "matched")
        self.assertEqual(reconciliation.execution_run_id, execution.execution_run_id)
        self.assertEqual(
            reconciliation.subject_linkage["action_request_ids"],
            (approved_request.action_request_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["approval_decision_ids"],
            ("approval-phase20-e2e-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["delegation_ids"],
            (execution.delegation_id,),
        )
        self.assertEqual(
            reconciliation.subject_linkage["evidence_ids"],
            (evidence_id,),
        )

    def test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-restore-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        backup = service.export_authoritative_record_chain_backup()

        restored_store, restored_backend = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=restored_store,
        )
        statement_count_before_restore = len(restored_backend.statements)
        with mock.patch.object(
            restored_service,
            "inspect_assistant_context",
            wraps=restored_service.inspect_assistant_context,
        ) as inspect_assistant_context:
            restore_summary = restored_service.restore_authoritative_record_chain_backup(
                backup
            )

        self.assertEqual(
            restored_backend.statements[statement_count_before_restore][0],
            "SET TRANSACTION ISOLATION LEVEL SERIALIZABLE",
        )

        self.assertEqual(
            backup["backup_schema_version"],
            "phase21.authoritative-record-chain.v1",
        )
        self.assertEqual(backup["record_counts"]["action_execution"], 1)
        self.assertEqual(restore_summary.restored_record_counts["reconciliation"], 2)
        self.assertTrue(restore_summary.restore_drill.drill_passed)
        self.assertEqual(
            restore_summary.restore_drill.verified_action_execution_ids,
            (execution.action_execution_id,),
        )
        self.assertEqual(
            restore_summary.restore_drill.verified_approval_decision_ids,
            (approval_decision.approval_decision_id,),
        )
        self.assertIn(
            promoted_case.case_id,
            restore_summary.restore_drill.verified_case_ids,
        )
        self.assertIn(
            reconciliation.reconciliation_id,
            restore_summary.restore_drill.verified_reconciliation_ids,
        )
        self.assertCountEqual(
            restore_summary.restore_drill.verified_reconciliation_ids,
            tuple(
                record.reconciliation_id
                for record in service._store.list(ReconciliationRecord)
            ),
        )
        self.assertIn(
            mock.call("reconciliation", reconciliation.reconciliation_id),
            inspect_assistant_context.call_args_list,
        )

        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        self.assertEqual(
            restored_case_detail.case_record["case_id"],
            promoted_case.case_id,
        )
        self.assertEqual(restored_case_detail.linked_evidence_ids, (evidence_id,))

        restored_approval_context = restored_service.inspect_assistant_context(
            "approval_decision",
            approval_decision.approval_decision_id,
        )
        self.assertEqual(
            restored_approval_context.linked_case_ids,
            (promoted_case.case_id,),
        )
        self.assertIn(
            reconciliation.reconciliation_id,
            restored_approval_context.linked_reconciliation_ids,
        )

    def test_service_phase21_restore_drill_can_run_standalone_after_restore(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        restore_drill = restored_service.run_authoritative_restore_drill()

        self.assertTrue(restore_drill.drill_passed)
        self.assertEqual(
            restore_drill.verified_case_ids,
            restore_summary.restore_drill.verified_case_ids,
        )
        self.assertEqual(
            restore_drill.verified_reconciliation_ids,
            restore_summary.restore_drill.verified_reconciliation_ids,
        )
        self.assertEqual(restore_drill.verified_case_ids, (promoted_case.case_id,))

        restored_case_detail = restored_service.inspect_case_detail(promoted_case.case_id)
        self.assertEqual(restored_case_detail.linked_evidence_ids, (evidence_id,))

    def test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        restore_summary = restored_service.restore_authoritative_record_chain_backup(
            backup
        )
        readiness = restored_service.inspect_readiness_diagnostics()

        self.assertFalse(restore_summary.restore_drill.drill_passed)
        self.assertEqual(readiness.status, "failing_closed")
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET",
            readiness.startup["missing_bindings"],
        )
        self.assertIn(
            "AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN",
            readiness.startup["missing_bindings"],
        )

    def test_service_phase21_restore_drill_uses_single_transaction_snapshot(
        self,
    ) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before restore drill")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-restore-drill-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(concurrent_reconciliation),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=snapshot_store,
        )

        statement_count_before_snapshot = len(backend.statements)
        restore_drill = snapshot_service.run_authoritative_restore_drill()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertTrue(restore_drill.drill_passed)
        self.assertEqual(
            restore_drill.verified_reconciliation_ids,
            (seed_reconciliation.reconciliation_id,),
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-restore-drill-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_service_phase21_backup_uses_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_alert = service.get_record(AlertRecord, promoted_case.alert_id)
        if seed_alert is None:
            self.fail("expected seeded alert record before snapshot export")

        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(
                replace(
                    seed_alert,
                    alert_id="alert-phase21-backup-concurrent-001",
                )
            ),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=snapshot_store,
        )

        statement_count_before_backup = len(backend.statements)
        backup = snapshot_service.export_authoritative_record_chain_backup()

        self.assertEqual(
            backend.statements[statement_count_before_backup][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(backup["record_counts"]["alert"], 1)
        self.assertEqual(len(backup["record_families"]["alert"]), 1)
        self.assertCountEqual(
            [record["alert_id"] for record in backup["record_families"]["alert"]],
            (promoted_case.alert_id,),
        )
        self.assertEqual(len(base_store.list(AlertRecord)), 2)
        self.assertEqual(
            concurrent_store.get(AlertRecord, "alert-phase21-backup-concurrent-001"),
            replace(
                seed_alert,
                alert_id="alert-phase21-backup-concurrent-001",
            ),
        )

    def test_service_phase21_readiness_uses_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before readiness snapshot")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-readiness-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        snapshot_store = _ConcurrentListMutationStore(
            inner=base_store,
            mutate_once=lambda: concurrent_store.save(concurrent_reconciliation),
        )
        snapshot_service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=snapshot_store,
        )

        statement_count_before_snapshot = len(backend.statements)
        readiness = snapshot_service.inspect_readiness_diagnostics()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(readiness.status, "ready")
        self.assertEqual(readiness.metrics["reconciliations"]["stale"], 0)
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            seed_reconciliation.reconciliation_id,
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-readiness-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_store_phase21_readiness_aggregates_use_single_transaction_snapshot(self) -> None:
        base_store, backend = make_store()
        concurrent_store, _ = make_store(backend)
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=base_store)
        )
        seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
            default=None,
        )
        if seed_reconciliation is None:
            self.fail("expected seeded reconciliation record before readiness aggregate snapshot")

        concurrent_reconciliation = replace(
            seed_reconciliation,
            reconciliation_id="reconciliation-phase21-aggregate-concurrent-001",
            compared_at=seed_reconciliation.compared_at + timedelta(minutes=30),
            lifecycle_state="stale",
        )
        original_count_grouped_by_field = base_store._count_grouped_by_field
        mutation_applied = False

        def count_grouped_by_field(
            record_type: object,
            field_name: str,
        ) -> dict[str, int]:
            nonlocal mutation_applied
            counts = original_count_grouped_by_field(record_type, field_name)
            if not mutation_applied:
                mutation_applied = True
                concurrent_store.save(concurrent_reconciliation)
            return counts

        statement_count_before_snapshot = len(backend.statements)
        with mock.patch.object(
            base_store,
            "_count_grouped_by_field",
            side_effect=count_grouped_by_field,
        ):
            aggregates = base_store.inspect_readiness_aggregates()

        self.assertEqual(
            backend.statements[statement_count_before_snapshot][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )
        self.assertEqual(aggregates.reconciliation_lifecycle_counts.get("stale", 0), 0)
        self.assertEqual(
            aggregates.latest_reconciliation.reconciliation_id
            if aggregates.latest_reconciliation is not None
            else None,
            seed_reconciliation.reconciliation_id,
        )
        self.assertEqual(len(base_store.list(ReconciliationRecord)), 2)
        self.assertEqual(
            concurrent_store.get(
                ReconciliationRecord,
                "reconciliation-phase21-aggregate-concurrent-001",
            ),
            concurrent_reconciliation,
        )

    def test_service_phase21_readiness_avoids_full_table_list_reads(self) -> None:
        inner_store, _ = make_store()
        store = _ListCountingStore(inner=inner_store)
        _store, _service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case(store=store)
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(
                host="127.0.0.1",
                postgres_dsn="postgresql://control-plane.local/aegisops",
                wazuh_ingest_shared_secret="reviewed-shared-secret",  # noqa: S106 - test fixture secret
                wazuh_ingest_reverse_proxy_secret="reviewed-proxy-secret",  # noqa: S106 - test fixture secret
                admin_bootstrap_token="reviewed-admin-bootstrap-token",  # noqa: S106 - test fixture secret
                break_glass_token="reviewed-break-glass-token",  # noqa: S106 - test fixture secret
            ),
            store=store,
        )

        store.list_calls = 0
        readiness = service.inspect_readiness_diagnostics()

        self.assertEqual(readiness.status, "ready")
        self.assertEqual(store.list_calls, 0)

    def test_service_phase21_readiness_counts_distinct_execution_runs_and_redacts_payload(
        self,
    ) -> None:
        _store, service, promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        target_scope = {"asset_id": "asset-phase21-readiness-001"}
        latest_seed_reconciliation = max(
            service._store.list(ReconciliationRecord),
            key=lambda record: record.compared_at,
        )
        approved_payload = _phase20_notify_identity_owner_payload(
            recipient_identity="repo-owner-001",
            case_id=promoted_case.case_id,
            alert_id=promoted_case.alert_id,
            finding_id=promoted_case.finding_id,
        )
        payload_hash = _approved_binding_hash(
            target_scope=target_scope,
            approved_payload=approved_payload,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
        )
        requested_at = latest_seed_reconciliation.compared_at + timedelta(minutes=10)
        delegated_at = requested_at + timedelta(minutes=5)
        expires_at = requested_at + timedelta(hours=1)
        service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-readiness-001",
                action_request_id="action-request-phase21-readiness-001",
                approver_identities=("approver-001",),
                target_snapshot=target_scope,
                payload_hash=payload_hash,
                decided_at=requested_at,
                lifecycle_state="approved",
                approved_expires_at=expires_at,
            )
        )
        service.persist_record(
            ActionRequestRecord(
                action_request_id="action-request-phase21-readiness-001",
                approval_decision_id="approval-phase21-readiness-001",
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                idempotency_key="idempotency-phase21-readiness-001",
                target_scope=target_scope,
                payload_hash=payload_hash,
                requested_at=requested_at,
                expires_at=expires_at,
                lifecycle_state="approved",
                requester_identity="analyst-001",
                requested_payload=approved_payload,
                policy_basis={
                    "severity": "low",
                    "target_scope": "single_identity",
                    "action_reversibility": "reversible",
                    "asset_criticality": "standard",
                    "identity_criticality": "standard",
                    "blast_radius": "single_target",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-readiness-001",
                action_request_id="action-request-phase21-readiness-001",
                approval_decision_id="approval-phase21-readiness-001",
                delegation_id="delegation-phase21-readiness-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-readiness-001",
                idempotency_key="idempotency-phase21-readiness-001",
                target_scope=target_scope,
                approved_payload=approved_payload,
                payload_hash=payload_hash,
                delegated_at=delegated_at,
                expires_at=expires_at,
                provenance={"adapter": "shuffle"},
                lifecycle_state="queued",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-001",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id="execution-run-phase21-readiness-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-001",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="phase20 execution matched",
                compared_at=delegated_at + timedelta(minutes=1),
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-002",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id="execution-run-phase21-readiness-001",
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-002",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="duplicate reconciliation for same execution run",
                compared_at=delegated_at + timedelta(minutes=2),
                lifecycle_state="matched",
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase21-readiness-distinct-none-001",
                subject_linkage={
                    "action_request_ids": ("action-request-phase21-readiness-001",),
                    "latest_native_payload": {"secret": "keep-in-store"},
                },
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key="reconciliation:phase21-readiness:distinct-none-001",
                first_seen_at=requested_at,
                last_seen_at=delegated_at,
                ingest_disposition="matched",
                mismatch_summary="null execution run should stay out of phase20 metric",
                compared_at=delegated_at + timedelta(minutes=3),
                lifecycle_state="matched",
            )
        )

        readiness = service.inspect_readiness_diagnostics()

        self.assertEqual(
            readiness.metrics["phase20_notify_identity_owner"]["reconciled_executions"],
            1,
        )
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            "reconciliation-phase21-readiness-distinct-none-001",
        )
        self.assertNotIn(
            "latest_native_payload",
            readiness.latest_reconciliation["subject_linkage"],
        )
        stored_latest = service.get_record(
            ReconciliationRecord,
            "reconciliation-phase21-readiness-distinct-none-001",
        )
        self.assertIsNotNone(stored_latest)
        self.assertIn("latest_native_payload", stored_latest.subject_linkage)

    def test_service_phase21_readiness_prefers_higher_reconciliation_id_when_compared_at_ties(
        self,
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
                _load_wazuh_fixture("agent-origin-alert.json")
            ),
        )
        reconciliation = service.get_record(
            ReconciliationRecord,
            admitted.reconciliation.reconciliation_id,
        )
        self.assertIsNotNone(reconciliation)

        preferred_reconciliation = replace(
            reconciliation,
            reconciliation_id=f"{reconciliation.reconciliation_id}-z",
            correlation_key=f"{reconciliation.correlation_key}:z",
        )
        service.persist_record(preferred_reconciliation)

        readiness = service.inspect_readiness_diagnostics()

        self.assertIsNotNone(readiness.latest_reconciliation)
        self.assertEqual(
            readiness.latest_reconciliation["reconciliation_id"],
            preferred_reconciliation.reconciliation_id,
        )

    def test_service_phase21_restore_rejects_non_string_tuple_elements(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["case"][0]["evidence_ids"] = [
            backup["record_families"]["case"][0]["evidence_ids"][0],
            {"invalid": "evidence-id"},
        ]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "case.evidence_ids must contain only non-empty strings",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_on_duplicate_alert_identifiers(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["alert"].append(
            dict(backup["record_families"]["alert"][0])
        )
        backup["record_counts"]["alert"] = len(backup["record_families"]["alert"])

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            r"duplicate alert identifiers .*restored_record_counts\['alert'\]=2",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_on_duplicate_execution_run_ids(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-duplicate-run-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-duplicate-run-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id=approval_decision.approval_decision_id,
                delegation_id="delegation-phase21-duplicate-run-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-duplicate-run-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        duplicate_execution = dict(backup["record_families"]["action_execution"][0])
        duplicate_execution["action_execution_id"] = (
            "action-execution-phase21-duplicate-run-002"
        )
        duplicate_execution["delegation_id"] = "delegation-phase21-duplicate-run-002"
        duplicate_execution["delegated_at"] = (
            reviewed_at + timedelta(minutes=2)
        ).isoformat()
        backup["record_families"]["action_execution"].append(duplicate_execution)
        backup["record_counts"]["action_execution"] = len(
            backup["record_families"]["action_execution"]
        )

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            (
                r"duplicate action_execution execution_run_id values "
                r".*restored_record_counts\['action_execution'\]=2"
            ),
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_fails_closed_when_approval_record_is_missing(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-missing-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        execution = service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-missing-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id="approval-phase21-missing-001",
                delegation_id="delegation-phase21-missing-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-missing-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        self.assertEqual(len(backup["record_families"]["approval_decision"]), 1)
        backup["record_families"]["approval_decision"] = [
            record
            for record in backup["record_families"]["approval_decision"]
            if record["approval_decision_id"] != approval_decision.approval_decision_id
        ]
        backup["record_counts"]["approval_decision"] = len(
            backup["record_families"]["approval_decision"]
        )

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "missing approval_decision record 'approval-phase21-missing-001' required by action request",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)

        self._assert_authoritative_store_empty(restored_store)
        self.assertIsNone(
            restored_service.get_record(ActionExecutionRecord, execution.action_execution_id)
        )

    def test_service_phase21_restore_fails_closed_when_target_contains_recommendation(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )
        restored_service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-existing-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id="alert-existing-001",
                case_id="case-existing-001",
                ai_trace_id=None,
                review_owner="analyst-001",
                intended_outcome="Pre-existing recommendation should block restore.",
                lifecycle_state="under_review",
                reviewed_context={"reviewed_at": reviewed_at.isoformat()},
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "authoritative restore target must be empty before restore; found existing records for recommendation",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)

    def test_service_phase21_restore_fails_closed_when_analytic_signal_links_missing_alert(
        self,
    ) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        self.assertEqual(len(backup["record_families"]["analytic_signal"]), 1)
        backup["record_families"]["analytic_signal"][0]["alert_ids"] = [
            "alert-phase21-missing-analytic-signal-link-001"
        ]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "missing alert record 'alert-phase21-missing-analytic-signal-link-001' required by analytic signal",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_non_mapping_payload_fields(self) -> None:
        _store, service, _promoted_case, _evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["alert"][0]["reviewed_context"] = ["not-a-mapping"]

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "alert.reviewed_context must be a JSON object in restore payload",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_approval_target_binding_mismatch(self) -> None:
        _store, service, promoted_case, _evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-binding-mismatch-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["approval_decision"][0]["target_snapshot"] = {
            "record_family": "recommendation",
            "record_id": recommendation.recommendation_id,
            "case_id": promoted_case.case_id,
            "alert_id": promoted_case.alert_id,
            "finding_id": promoted_case.finding_id,
            "recipient_identity": "repo-owner-999",
        }

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "approval decision 'approval-phase21-binding-mismatch-001' does not match action request target binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_action_execution_surface_binding_mismatch(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-execution-binding-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-execution-binding-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id=approval_decision.approval_decision_id,
                delegation_id="delegation-phase21-execution-binding-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-execution-binding-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["action_execution"][0]["execution_surface_id"] = (
            "isolated-executor"
        )

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "action execution 'action-execution-phase21-execution-binding-001' does not match action request execution surface binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_action_execution_expiry_binding_mismatch(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-expiry-binding-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-expiry-binding-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id=approval_decision.approval_decision_id,
                delegation_id="delegation-phase21-expiry-binding-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-expiry-binding-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["action_execution"][0]["expires_at"] = (
            approved_request.expires_at + timedelta(minutes=5)
        ).isoformat()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "action execution 'action-execution-phase21-expiry-binding-001' does not match action request expiry binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_action_execution_delegation_after_approval_expiry(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-expiry-window-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=reviewed_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        service.persist_record(
            ActionExecutionRecord(
                action_execution_id="action-execution-phase21-expiry-window-001",
                action_request_id=approved_request.action_request_id,
                approval_decision_id=approval_decision.approval_decision_id,
                delegation_id="delegation-phase21-expiry-window-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="execution-run-phase21-expiry-window-001",
                idempotency_key=approved_request.idempotency_key,
                target_scope=dict(approved_request.target_scope),
                approved_payload=dict(approved_request.requested_payload),
                payload_hash=approved_request.payload_hash,
                delegated_at=reviewed_at + timedelta(minutes=1),
                expires_at=approved_request.expires_at,
                provenance={"evidence_ids": (evidence_id,)},
                lifecycle_state="queued",
            )
        )
        backup = service.export_authoritative_record_chain_backup()
        backup["record_families"]["action_execution"][0]["delegated_at"] = (
            approved_request.expires_at + timedelta(minutes=1)
        ).isoformat()

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "action execution 'action-execution-phase21-expiry-window-001' exceeds approval expiry binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase21_restore_rejects_reconciliation_run_binding_mismatch(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, _reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        primary_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        primary_decided_at = primary_request.requested_at + timedelta(minutes=1)
        primary_delegated_at = primary_request.requested_at + timedelta(minutes=2)
        primary_observed_at = primary_request.requested_at + timedelta(minutes=3)
        primary_compared_at = primary_request.requested_at + timedelta(minutes=4)
        primary_stale_after = primary_request.requested_at + timedelta(hours=1)
        primary_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-reconciliation-primary-001",
                action_request_id=primary_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(primary_request.target_scope),
                payload_hash=primary_request.payload_hash,
                decided_at=primary_decided_at,
                lifecycle_state="approved",
                approved_expires_at=primary_request.expires_at,
            )
        )
        approved_primary_request = service.persist_record(
            replace(
                primary_request,
                approval_decision_id=primary_approval.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        primary_execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_primary_request.action_request_id,
            approved_payload=dict(approved_primary_request.requested_payload),
            delegated_at=primary_delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        primary_reconciliation = service.reconcile_action_execution(
            action_request_id=approved_primary_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": primary_execution.execution_run_id,
                    "execution_surface_id": "shuffle",
                    "idempotency_key": approved_primary_request.idempotency_key,
                    "approval_decision_id": primary_execution.approval_decision_id,
                    "delegation_id": primary_execution.delegation_id,
                    "payload_hash": primary_execution.payload_hash,
                    "observed_at": primary_observed_at,
                    "status": "success",
                },
            ),
            compared_at=primary_compared_at,
            stale_after=primary_stale_after,
        )

        secondary_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-002",
            message_intent="Notify the backup repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at + timedelta(hours=1),
        )
        secondary_decided_at = secondary_request.requested_at + timedelta(minutes=1)
        secondary_delegated_at = secondary_request.requested_at + timedelta(minutes=2)
        secondary_approval = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase21-reconciliation-secondary-001",
                action_request_id=secondary_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(secondary_request.target_scope),
                payload_hash=secondary_request.payload_hash,
                decided_at=secondary_decided_at,
                lifecycle_state="approved",
                approved_expires_at=secondary_request.expires_at,
            )
        )
        approved_secondary_request = service.persist_record(
            replace(
                secondary_request,
                approval_decision_id=secondary_approval.approval_decision_id,
                lifecycle_state="approved",
            )
        )
        secondary_execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_secondary_request.action_request_id,
            approved_payload=dict(approved_secondary_request.requested_payload),
            delegated_at=secondary_delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )

        backup = service.export_authoritative_record_chain_backup()
        for record in backup["record_families"]["reconciliation"]:
            if (
                record["reconciliation_id"]
                == primary_reconciliation.reconciliation_id
            ):
                record["execution_run_id"] = secondary_execution.execution_run_id
                record["linked_execution_run_ids"] = [
                    secondary_execution.execution_run_id
                ]
                break
        else:
            self.fail("expected primary reconciliation in authoritative backup")

        restored_store, _ = make_store()
        restored_service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=restored_store,
        )

        with self.assertRaisesRegex(
            ValueError,
            f"reconciliation '{primary_reconciliation.reconciliation_id}' does not match its action execution run binding",
        ):
            restored_service.restore_authoritative_record_chain_backup(backup)
        self._assert_authoritative_store_empty(restored_store)

    def test_service_phase20_first_live_action_fail_closes_on_downstream_execution_surface_mismatch(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-mismatch-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )
        reconciliation = service.reconcile_action_execution(
            action_request_id=approved_request.action_request_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="shuffle",
            observed_executions=(
                {
                    "execution_run_id": execution.execution_run_id,
                    "execution_surface_id": "n8n",
                    "idempotency_key": approved_request.idempotency_key,
                    "approval_decision_id": execution.approval_decision_id,
                    "delegation_id": execution.delegation_id,
                    "payload_hash": execution.payload_hash,
                    "observed_at": observed_at,
                    "status": "success",
                },
            ),
            compared_at=compared_at,
            stale_after=stale_after,
        )

        stored_execution = service.get_record(
            ActionExecutionRecord,
            execution.action_execution_id,
        )
        self.assertIsNotNone(stored_execution)
        self.assertEqual(stored_execution.lifecycle_state, "queued")
        self.assertEqual(stored_execution.execution_surface_id, "shuffle")
        self.assertEqual(reconciliation.ingest_disposition, "mismatch")
        self.assertEqual(reconciliation.lifecycle_state, "mismatched")
        self.assertEqual(
            reconciliation.mismatch_summary,
            "execution surface/idempotency mismatch between approved request and observed execution",
        )
        self.assertEqual(
            reconciliation.subject_linkage["approval_decision_ids"],
            ("approval-phase20-mismatch-001",),
        )
        self.assertEqual(
            reconciliation.subject_linkage["action_execution_ids"],
            (execution.action_execution_id,),
        )

    def test_service_phase20_reconciliation_rejects_downstream_evidence_missing_binding_identifiers(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)
        action_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        decided_at = action_request.requested_at + timedelta(minutes=5)
        delegated_at = action_request.requested_at + timedelta(minutes=10)
        observed_at = action_request.requested_at + timedelta(minutes=15)
        compared_at = action_request.requested_at + timedelta(minutes=16)
        stale_after = action_request.requested_at + timedelta(hours=1)
        approval_decision = service.persist_record(
            ApprovalDecisionRecord(
                approval_decision_id="approval-phase20-missing-binding-001",
                action_request_id=action_request.action_request_id,
                approver_identities=("approver-001",),
                target_snapshot=dict(action_request.target_scope),
                payload_hash=action_request.payload_hash,
                decided_at=decided_at,
                lifecycle_state="approved",
                approved_expires_at=action_request.expires_at,
            )
        )
        approved_request = service.persist_record(
            replace(
                action_request,
                approval_decision_id=approval_decision.approval_decision_id,
                lifecycle_state="approved",
            )
        )

        execution = service.delegate_approved_action_to_shuffle(
            action_request_id=approved_request.action_request_id,
            approved_payload=dict(approved_request.requested_payload),
            delegated_at=delegated_at,
            delegation_issuer="control-plane-service",
            evidence_ids=(evidence_id,),
        )

        with self.assertRaisesRegex(
            ValueError,
            "observed execution must include string approval_decision_id",
        ):
            service.reconcile_action_execution(
                action_request_id=approved_request.action_request_id,
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                observed_executions=(
                    {
                        "execution_run_id": execution.execution_run_id,
                        "execution_surface_id": "shuffle",
                        "idempotency_key": approved_request.idempotency_key,
                        "observed_at": observed_at,
                        "status": "success",
                    },
                ),
                compared_at=compared_at,
                stale_after=stale_after,
            )

    def test_service_rejects_reviewed_action_request_creation_when_malformed_or_out_of_scope(
        self,
    ) -> None:
        _, service, promoted_case, _, _ = (
            self._build_phase19_in_scope_case()
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
        )
        future_expiry = datetime.now(timezone.utc) + timedelta(hours=4)

        with self.assertRaisesRegex(
            ValueError,
            "recipient_identity must be a non-empty string",
        ):
            service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=future_expiry,
            )

        replay_service, replay_case, _, _ = self._build_phase19_out_of_scope_case(
            fixture_name="github-audit-alert.json"
        )
        replay_recommendation = replay_service.persist_record(
            RecommendationRecord(
                recommendation_id="recommendation-phase20-out-of-scope-001",
                lead_id=None,
                hunt_run_id=None,
                alert_id=replay_case.alert_id,
                case_id=replay_case.case_id,
                ai_trace_id=None,
                review_owner="analyst-001",
                intended_outcome="Synthetic advisory reads must fail closed.",
                lifecycle_state="under_review",
                reviewed_context=replay_case.reviewed_context,
            )
        )

        with self.assertRaisesRegex(
            ValueError,
            "outside the approved Phase 19 Wazuh-backed GitHub audit and Entra ID live slice",
        ):
            replay_service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=replay_recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=future_expiry,
            )

    def test_service_reuses_reviewed_action_request_for_matching_idempotency_key(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertEqual(second_request, first_request)
        self.assertEqual(store.list(ActionRequestRecord), (first_request,))

    def test_service_keeps_requester_identity_inside_reviewed_action_request_deduplication(
        self,
    ) -> None:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=service.record_case_lead(
                case_id=promoted_case.case_id,
                triage_owner="analyst-001",
                triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
                observation_id=observation.observation_id,
            ).lead_id,
        )
        expires_at = datetime.now(timezone.utc) + timedelta(hours=4)

        first_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-001",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )
        second_request = service.create_reviewed_action_request_from_advisory(
            record_family="recommendation",
            record_id=recommendation.recommendation_id,
            requester_identity="analyst-002",
            recipient_identity="repo-owner-001",
            message_intent="Notify the accountable repository owner about the reviewed permission change.",
            escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
            expires_at=expires_at,
        )

        self.assertNotEqual(second_request.action_request_id, first_request.action_request_id)
        self.assertEqual(first_request.requester_identity, "analyst-001")
        self.assertEqual(second_request.requester_identity, "analyst-002")
        self.assertNotEqual(second_request.idempotency_key, first_request.idempotency_key)
        persisted_by_requester = {
            record.requester_identity: record
            for record in store.list(ActionRequestRecord)
        }
        self.assertEqual(
            persisted_by_requester,
            {
                "analyst-001": first_request,
                "analyst-002": second_request,
            },
        )

    def test_service_rechecks_reviewed_action_request_context_inside_transaction(
        self,
    ) -> None:
        inner_store, _ = make_store()
        (
            _,
            base_service,
            promoted_case,
            evidence_id,
            reviewed_at,
        ) = self._build_phase19_in_scope_case(store=inner_store)
        observation = base_service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Observed repository permission change requires tracked review.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = base_service.record_case_lead(
            case_id=promoted_case.case_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting change needs durable business-hours follow-up.",
            observation_id=observation.observation_id,
        )
        recommendation = base_service.record_case_recommendation(
            case_id=promoted_case.case_id,
            review_owner="analyst-001",
            intended_outcome="Review repository owner change evidence before any approval-bound response.",
            lead_id=lead.lead_id,
        )
        store = _TransactionMutationStore(
            inner=inner_store,
            mutate_once=lambda transactional_store: transactional_store.save(
                replace(
                    transactional_store.get(
                        RecommendationRecord,
                        recommendation.recommendation_id,
                    ),
                    intended_outcome=(
                        "Execute an organization-wide response immediately without waiting "
                        "for approval."
                    ),
                )
            ),
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=store,
        )

        with self.assertRaisesRegex(
            ValueError,
            "reviewed advisory context is not ready for approval-bound action requests",
        ):
            service.create_reviewed_action_request_from_advisory(
                record_family="recommendation",
                record_id=recommendation.recommendation_id,
                requester_identity="analyst-001",
                recipient_identity="repo-owner-001",
                message_intent="Notify the accountable repository owner about the reviewed permission change.",
                escalation_reason="Reviewed GitHub audit evidence requires bounded owner notification.",
                expires_at=datetime.now(timezone.utc) + timedelta(hours=4),
            )

        self.assertEqual(inner_store.list(ActionRequestRecord), ())


if __name__ == "__main__":
    unittest.main()
