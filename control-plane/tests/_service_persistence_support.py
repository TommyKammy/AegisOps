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
from types import SimpleNamespace
import sys
from typing import Callable, Iterator
import unittest
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops_control_plane.assistant_context import (
    _reviewed_context_identifier_citations,
)
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
from aegisops_control_plane.execution_coordinator import _approved_payload_binding_hash
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
class _RecordTypeSaveFailingStore:
    inner: object
    record_type: type[object]
    message: str = "synthetic save failure"

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def save(self, record: object) -> object:
        if isinstance(record, self.record_type):
            raise RuntimeError(self.message)
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
