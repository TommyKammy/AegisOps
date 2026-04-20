from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import pathlib
import secrets
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.adapters.osquery import OsqueryHostContextAdapter
from aegisops_control_plane.config import RuntimeConfig
from aegisops_control_plane.models import (
    ActionRequestRecord,
    CaseRecord,
    EvidenceRecord,
    ObservationRecord,
)
from aegisops_control_plane.service import AegisOpsControlPlaneService
from postgres_test_support import make_store
from tests.support.fixtures import load_wazuh_fixture


@dataclass
class _EvidenceSaveMutationStore:
    inner: object
    mutate_once: object
    _mutated: bool = False
    last_isolation_level: str | None = None
    transaction_isolation_levels: tuple[str | None, ...] = ()

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

    def create_action_request_if_absent(
        self,
        record: ActionRequestRecord,
    ) -> tuple[ActionRequestRecord, bool]:
        return self.inner.create_action_request_if_absent(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        return self.inner.list(record_type)

    def latest_reconciliation_for_correlation_key(
        self,
        correlation_key: str,
        *,
        require_alert_id: bool = False,
    ) -> object | None:
        return self.inner.latest_reconciliation_for_correlation_key(
            correlation_key,
            require_alert_id=require_alert_id,
        )

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> object | None:
        return self.inner.latest_lifecycle_transition(record_family, record_id)

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[object, ...]:
        return self.inner.list_lifecycle_transitions(record_family, record_id)

    def inspect_readiness_aggregates(self) -> object:
        return self.inner.inspect_readiness_aggregates()

    def inspect_readiness_review_path_records(
        self,
        *,
        action_request_ids: tuple[str, ...],
        approval_decision_ids: tuple[str, ...],
        delegation_ids: tuple[str, ...] = (),
    ) -> object:
        return self.inner.inspect_readiness_review_path_records(
            action_request_ids=action_request_ids,
            approval_decision_ids=approval_decision_ids,
            delegation_ids=delegation_ids,
        )

    @contextmanager
    def transaction(self, *, isolation_level: str | None = None):
        self.last_isolation_level = isolation_level
        self.transaction_isolation_levels = (
            *self.transaction_isolation_levels,
            isolation_level,
        )
        with self.inner.transaction(isolation_level=isolation_level):
            yield


class Phase25OsqueryHostContextValidationTests(unittest.TestCase):
    _NON_PROCESS_OSQUERY_RESULT_CASES = (
        {
            "result_kind": "host_state",
            "query_name": "host_uptime",
            "query_sql": "SELECT hostname, uptime FROM uptime;",
            "rows": (
                {
                    "hostname": "host-001",
                    "uptime": "86400",
                },
            ),
            "collection_path": "pack/osquery-defense/host/host_uptime",
            "query_context": {"pack": "osquery-defense", "platform": "linux"},
            "expected_columns": ("hostname", "uptime"),
        },
        {
            "result_kind": "local_user",
            "query_name": "interactive_users",
            "query_sql": "SELECT uid, username, shell FROM users;",
            "rows": (
                {
                    "uid": "1000",
                    "username": "analyst",
                    "shell": "/bin/zsh",
                },
            ),
            "collection_path": "pack/osquery-defense/users/interactive_users",
            "query_context": {"pack": "osquery-defense", "platform": "linux"},
            "expected_columns": ("shell", "uid", "username"),
        },
        {
            "result_kind": "scheduled_query",
            "query_name": "pack_schedule",
            "query_sql": "SELECT name, interval, snapshot FROM osquery_schedule;",
            "rows": (
                {
                    "name": "pack_schedule",
                    "interval": "3600",
                    "snapshot": "false",
                },
            ),
            "collection_path": "pack/osquery-defense/schedule/pack_schedule",
            "query_context": {"pack": "osquery-defense", "platform": "linux"},
            "expected_columns": ("interval", "name", "snapshot"),
        },
    )

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

    def test_attach_osquery_host_context_preserves_guarantees_for_all_allowed_non_process_result_kinds(
        self,
    ) -> None:
        expected_allowed_kinds = {"host_state", "process", "local_user", "scheduled_query"}
        self.assertEqual(
            set(OsqueryHostContextAdapter().allowed_result_kinds),
            expected_allowed_kinds,
        )
        self.assertEqual(
            {scenario["result_kind"] for scenario in self._NON_PROCESS_OSQUERY_RESULT_CASES},
            expected_allowed_kinds - {"process"},
        )
        for scenario in self._NON_PROCESS_OSQUERY_RESULT_CASES:
            with self.subTest(result_kind=scenario["result_kind"]):
                _store, service, promoted_case, reviewed_at = self._build_host_bound_case(
                    host_identifier="host-001"
                )

                evidence, observation = service.attach_osquery_host_context(
                    case_id=promoted_case.case_id,
                    host_identifier="host-001",
                    query_name=scenario["query_name"],
                    query_sql=scenario["query_sql"],
                    result_kind=scenario["result_kind"],
                    rows=scenario["rows"],
                    collected_at=reviewed_at,
                    reviewed_by="analyst-001",
                    source_id=f"{scenario['result_kind']}-query-result-001",
                    collection_path=scenario["collection_path"],
                    query_context=scenario["query_context"],
                    observation_scope_statement=(
                        "Observed reviewed osquery host context on the explicitly scoped host."
                    ),
                )

                self.assertEqual(evidence.case_id, promoted_case.case_id)
                self.assertEqual(evidence.source_system, "osquery")
                self.assertEqual(
                    evidence.provenance["classification"],
                    "augmenting-evidence",
                )
                self.assertEqual(
                    evidence.provenance["collection_path"],
                    scenario["collection_path"],
                )
                self.assertEqual(
                    evidence.provenance["source_id"],
                    f"{scenario['result_kind']}-query-result-001",
                )
                self.assertEqual(
                    evidence.content["host"]["host_identifier"],
                    "host-001",
                )
                self.assertEqual(
                    evidence.content["query"]["name"],
                    scenario["query_name"],
                )
                self.assertEqual(
                    evidence.content["query"]["context"]["pack"],
                    "osquery-defense",
                )
                self.assertEqual(
                    evidence.content["result"]["kind"],
                    scenario["result_kind"],
                )
                self.assertEqual(evidence.content["result"]["row_count"], 1)
                self.assertEqual(
                    evidence.content["result"]["columns"],
                    scenario["expected_columns"],
                )

                self.assertIsNotNone(observation)
                assert observation is not None
                self.assertEqual(
                    observation.supporting_evidence_ids,
                    (evidence.evidence_id,),
                )
                self.assertEqual(
                    observation.provenance["classification"],
                    "reviewed-derived",
                )
                self.assertEqual(
                    observation.content["host_context_evidence_id"],
                    evidence.evidence_id,
                )
                self.assertEqual(
                    observation.content["result_kind"],
                    scenario["result_kind"],
                )

                case_detail = service.inspect_case_detail(promoted_case.case_id)
                persisted_evidence = {
                    record["evidence_id"]: record
                    for record in case_detail.linked_evidence_records
                }
                self.assertEqual(
                    persisted_evidence[evidence.evidence_id]["provenance"][
                        "classification"
                    ],
                    "augmenting-evidence",
                )
                self.assertEqual(
                    persisted_evidence[evidence.evidence_id]["content"]["result"]["kind"],
                    scenario["result_kind"],
                )
                self.assertEqual(
                    persisted_evidence[evidence.evidence_id]["content"]["query"][
                        "collection_path"
                    ],
                    scenario["collection_path"],
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
                self.assertEqual(
                    persisted_observation[observation.observation_id]["content"][
                        "result_kind"
                    ],
                    scenario["result_kind"],
                )

    def test_inspect_case_detail_exposes_cross_source_timeline_and_provenance_summary(
        self,
    ) -> None:
        _store, service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier="host-001"
        )
        second_source_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-entra-case-001",
                source_record_id="wazuh://entra/record/001",
                alert_id=None,
                case_id=promoted_case.case_id,
                source_system="wazuh",
                collector_identity="wazuh-reviewed-second-source-adapter",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_case_attachment",
                lifecycle_state="linked",
                provenance={
                    "classification": "unresolved-linkage",
                    "source_id": "entra-record-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "source_family": "entra_id",
                    "ambiguity_badge": "unresolved",
                    "blocking_reason": "stable_identifier_mismatch",
                },
                content={
                    "attachment_reason": (
                        "Reviewed second-source context remains candidate-only until "
                        "stable identifiers are reconciled."
                    )
                },
            )
        )
        promoted_case = service.persist_record(
            CaseRecord(
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=(
                    *promoted_case.evidence_ids,
                    second_source_evidence.evidence_id,
                ),
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        osquery_evidence, osquery_observation = service.attach_osquery_host_context(
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
            collected_at=reviewed_at.replace(minute=reviewed_at.minute + 1),
            reviewed_by="analyst-001",
            source_id="query-result-001",
            collection_path="pack/osquery-defense/processes/running_processes",
            query_context={"pack": "osquery-defense", "platform": "linux"},
            observation_scope_statement=(
                "Observed reviewed osquery host context on the explicitly scoped host."
            ),
        )
        assert osquery_observation is not None

        case_detail = service.inspect_case_detail(promoted_case.case_id)

        self.assertEqual(
            [entry["record_family"] for entry in case_detail.cross_source_timeline],
            ["alert", "evidence", "evidence", "evidence", "observation"],
        )
        self.assertEqual(
            case_detail.cross_source_timeline[0]["provenance_classification"],
            "authoritative-anchor",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[0]["source_family"],
            "github_audit",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[1]["record_id"],
            promoted_case.evidence_ids[0],
        )
        self.assertEqual(
            case_detail.cross_source_timeline[1]["source_family"],
            "wazuh",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[1]["blocking_reason"],
            "missing_provenance",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[2]["record_id"],
            second_source_evidence.evidence_id,
        )
        self.assertEqual(
            case_detail.cross_source_timeline[2]["source_family"],
            "entra_id",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[2]["ambiguity_badge"],
            "unresolved",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[2]["blocking_reason"],
            "stable_identifier_mismatch",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[3]["record_id"],
            osquery_evidence.evidence_id,
        )
        self.assertEqual(
            case_detail.cross_source_timeline[3]["source_family"],
            "osquery",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[3]["ambiguity_badge"],
            "related-entity",
        )
        self.assertEqual(
            case_detail.cross_source_timeline[4]["record_id"],
            osquery_observation.observation_id,
        )
        self.assertEqual(
            case_detail.cross_source_timeline[4]["provenance_classification"],
            "reviewed-derived",
        )

        self.assertEqual(
            case_detail.provenance_summary["authoritative_anchor"]["record_id"],
            promoted_case.alert_id,
        )
        self.assertEqual(
            case_detail.provenance_summary["source_families"],
            ("github_audit", "wazuh", "entra_id", "osquery"),
        )
        attached_records = {
            record["record_id"]: record
            for record in case_detail.provenance_summary["attached_records"]
        }
        self.assertEqual(
            attached_records[promoted_case.evidence_ids[0]]["blocking_reason"],
            "missing_provenance",
        )
        self.assertEqual(
            attached_records[second_source_evidence.evidence_id][
                "provenance_classification"
            ],
            "unresolved-linkage",
        )
        self.assertEqual(
            attached_records[second_source_evidence.evidence_id]["blocking_reason"],
            "stable_identifier_mismatch",
        )
        self.assertEqual(
            attached_records[osquery_evidence.evidence_id]["evidence_origin"],
            osquery_evidence.source_record_id,
        )
        self.assertEqual(
            attached_records[osquery_observation.observation_id]["reviewed_linkage"][
                "supporting_evidence_ids"
            ],
            (osquery_evidence.evidence_id,),
        )

    def test_inspect_case_detail_surfaces_missing_provenance_as_unresolved_linkage(
        self,
    ) -> None:
        _store, service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier="host-001"
        )
        second_source_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-entra-case-missing-provenance",
                source_record_id="wazuh://entra/record/missing-provenance",
                alert_id=None,
                case_id=promoted_case.case_id,
                source_system="wazuh",
                collector_identity="wazuh-reviewed-second-source-adapter",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_case_attachment",
                lifecycle_state="linked",
                content={"attachment_reason": "Persisted without reviewed provenance."},
            )
        )
        service.persist_record(
            CaseRecord(
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=(
                    *promoted_case.evidence_ids,
                    second_source_evidence.evidence_id,
                ),
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id)

        attached_records = {
            record["record_id"]: record
            for record in case_detail.provenance_summary["attached_records"]
        }
        self.assertIn(second_source_evidence.evidence_id, attached_records)
        self.assertEqual(
            attached_records[second_source_evidence.evidence_id][
                "provenance_classification"
            ],
            "unresolved-linkage",
        )
        self.assertEqual(
            attached_records[second_source_evidence.evidence_id]["blocking_reason"],
            "missing_provenance",
        )
        self.assertEqual(
            attached_records[second_source_evidence.evidence_id]["source_family"],
            "wazuh",
        )

    def test_inspect_case_detail_tolerates_malformed_persisted_provenance(
        self,
    ) -> None:
        store, service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier="host-001"
        )
        second_source_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-entra-case-malformed-provenance",
                source_record_id="wazuh://entra/record/malformed-provenance",
                alert_id=None,
                case_id=promoted_case.case_id,
                source_system="wazuh",
                collector_identity="wazuh-reviewed-second-source-adapter",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_case_attachment",
                lifecycle_state="linked",
                provenance={
                    "classification": "reviewed-derived",
                    "source_id": "entra-record-002",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "source_family": "entra_id",
                    "ambiguity_badge": "unresolved",
                },
                content={
                    "attachment_reason": "Persisted before provenance corruption test."
                },
            )
        )
        service.persist_record(
            CaseRecord(
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=(
                    *promoted_case.evidence_ids,
                    second_source_evidence.evidence_id,
                ),
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        backend = getattr(store.connection_factory, "__self__", None)
        assert backend is not None
        backend.tables["evidence_records"][second_source_evidence.evidence_id][
            "provenance"
        ] = {
            "classification": 123,
            "source_id": ["entra-record-002"],
            "timestamp": {"unexpected": "shape"},
            "reviewed_by": 456,
            "source_family": ["entra_id"],
            "blocking_reason": {"unexpected": "shape"},
            "ambiguity_badge": ["related-entity"],
        }

        case_detail = service.inspect_case_detail(promoted_case.case_id)

        attached_records = {
            record["record_id"]: record
            for record in case_detail.provenance_summary["attached_records"]
        }
        self.assertEqual(
            attached_records[second_source_evidence.evidence_id][
                "provenance_classification"
            ],
            "unresolved-linkage",
        )
        self.assertEqual(
            attached_records[second_source_evidence.evidence_id]["blocking_reason"],
            "missing_or_invalid_required_provenance_fields",
        )

    def test_case_assistant_context_fails_closed_on_unresolved_identity_ambiguity(
        self,
    ) -> None:
        _store, service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier="host-001"
        )
        stable_id_mismatch_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-entra-case-stable-id-mismatch",
                source_record_id="wazuh://entra/record/stable-id-mismatch",
                alert_id=None,
                case_id=promoted_case.case_id,
                source_system="wazuh",
                collector_identity="wazuh-reviewed-second-source-adapter",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_case_attachment",
                lifecycle_state="linked",
                provenance={
                    "classification": "unresolved-linkage",
                    "source_id": "entra-record-stable-id-mismatch",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "source_family": "entra_id",
                    "ambiguity_badge": "unresolved",
                    "blocking_reason": "stable_identifier_mismatch",
                },
                content={
                    "attachment_reason": (
                        "Reviewed Entra ID context remains unresolved until stable "
                        "identifiers are reconciled."
                    )
                },
            )
        )
        alias_overlap_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-entra-case-alias-overlap",
                source_record_id="wazuh://entra/record/alias-overlap",
                alert_id=None,
                case_id=promoted_case.case_id,
                source_system="wazuh",
                collector_identity="wazuh-reviewed-second-source-adapter",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_case_attachment",
                lifecycle_state="linked",
                provenance={
                    "classification": "unresolved-linkage",
                    "source_id": "entra-record-alias-overlap",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "source_family": "entra_id",
                    "ambiguity_badge": "unresolved",
                    "blocking_reason": "alias_like_overlap",
                },
                content={
                    "attachment_reason": (
                        "Alias-style overlap remains reviewed context only and must "
                        "not be collapsed into one identity."
                    )
                },
            )
        )
        service.persist_record(
            CaseRecord(
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=(
                    *promoted_case.evidence_ids,
                    stable_id_mismatch_evidence.evidence_id,
                    alias_overlap_evidence.evidence_id,
                ),
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id)
        attached_records = {
            record["record_id"]: record
            for record in case_detail.provenance_summary["attached_records"]
        }
        self.assertEqual(
            attached_records[stable_id_mismatch_evidence.evidence_id]["ambiguity_badge"],
            "unresolved",
        )
        self.assertEqual(
            attached_records[stable_id_mismatch_evidence.evidence_id]["blocking_reason"],
            "stable_identifier_mismatch",
        )
        self.assertEqual(
            attached_records[alias_overlap_evidence.evidence_id]["ambiguity_badge"],
            "unresolved",
        )
        self.assertEqual(
            attached_records[alias_overlap_evidence.evidence_id]["blocking_reason"],
            "alias_like_overlap",
        )

        snapshot = service.inspect_assistant_context("case", promoted_case.case_id)

        self.assertEqual(snapshot.advisory_output["status"], "unresolved")
        self.assertIn(
            "reviewed_casework_identity_ambiguity",
            snapshot.advisory_output["uncertainty_flags"],
        )
        summary_text = snapshot.advisory_output["cited_summary"]["text"]
        self.assertIn(
            f"Case summary {promoted_case.case_id} remains unresolved because reviewed "
            "multi-source casework still contains unresolved identity ambiguity:",
            summary_text,
        )
        self.assertIn(
            (
                f"{stable_id_mismatch_evidence.evidence_id} "
                "(stable_identifier_mismatch)"
            ),
            summary_text,
        )
        self.assertIn(
            f"{alias_overlap_evidence.evidence_id} (alias_like_overlap)",
            summary_text,
        )
        self.assertEqual(
            snapshot.advisory_output["cited_summary"]["citations"][0],
            promoted_case.case_id,
        )
        self.assertCountEqual(
            snapshot.advisory_output["cited_summary"]["citations"][1:],
            (
                stable_id_mismatch_evidence.evidence_id,
                alias_overlap_evidence.evidence_id,
            ),
        )
        self.assertTrue(
            any(
                stable_id_mismatch_evidence.evidence_id in question.get("text", "")
                and alias_overlap_evidence.evidence_id in question.get("text", "")
                for question in snapshot.advisory_output["unresolved_questions"]
            )
        )

    def test_inspect_case_detail_trims_persisted_provenance_strings(self) -> None:
        _store, service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier="host-001"
        )
        trimmed_source_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-entra-case-trimmed-provenance",
                source_record_id="wazuh://entra/record/trimmed-provenance",
                alert_id=None,
                case_id=promoted_case.case_id,
                source_system="entra_id",
                collector_identity="wazuh-reviewed-second-source-adapter",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_case_attachment",
                lifecycle_state="linked",
                provenance={
                    "classification": " reviewed-derived ",
                    "source_id": " entra-record-003 ",
                    "timestamp": f" {reviewed_at.isoformat()} ",
                    "reviewed_by": " analyst-001 ",
                    "source_family": " entra_id ",
                    "ambiguity_badge": " related-entity ",
                    "blocking_reason": " stable_identifier_mismatch ",
                },
                content={"attachment_reason": "Whitespace-padded provenance values."},
            )
        )
        canonical_source_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-entra-case-canonical-provenance",
                source_record_id="wazuh://entra/record/canonical-provenance",
                alert_id=None,
                case_id=promoted_case.case_id,
                source_system="entra_id",
                collector_identity="wazuh-reviewed-second-source-adapter",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_case_attachment",
                lifecycle_state="linked",
                provenance={
                    "classification": "reviewed-derived",
                    "source_id": "entra-record-004",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "source_family": "entra_id",
                    "ambiguity_badge": "related-entity",
                },
                content={"attachment_reason": "Canonical provenance values."},
            )
        )
        service.persist_record(
            CaseRecord(
                case_id=promoted_case.case_id,
                alert_id=promoted_case.alert_id,
                finding_id=promoted_case.finding_id,
                evidence_ids=(
                    *promoted_case.evidence_ids,
                    trimmed_source_evidence.evidence_id,
                    canonical_source_evidence.evidence_id,
                ),
                lifecycle_state=promoted_case.lifecycle_state,
                reviewed_context=promoted_case.reviewed_context,
            )
        )

        case_detail = service.inspect_case_detail(promoted_case.case_id)

        attached_records = {
            record["record_id"]: record
            for record in case_detail.provenance_summary["attached_records"]
        }
        self.assertEqual(
            attached_records[trimmed_source_evidence.evidence_id]["source_family"],
            "entra_id",
        )
        self.assertEqual(
            attached_records[trimmed_source_evidence.evidence_id][
                "provenance_classification"
            ],
            "reviewed-derived",
        )
        self.assertEqual(
            attached_records[trimmed_source_evidence.evidence_id]["ambiguity_badge"],
            "related-entity",
        )
        self.assertEqual(
            attached_records[trimmed_source_evidence.evidence_id]["blocking_reason"],
            "stable_identifier_mismatch",
        )
        self.assertEqual(
            case_detail.provenance_summary["source_families"],
            ("github_audit", "wazuh", "entra_id"),
        )

    def test_osquery_adapter_canonicalizes_source_record_id_segments(self) -> None:
        adapter = OsqueryHostContextAdapter()
        collected_at = datetime(2026, 4, 18, 0, 0, tzinfo=timezone.utc)

        first = adapter.build_attachment(
            case_id="case-001",
            alert_id="alert-001",
            authoritative_host_identifier="host/001",
            host_identifier="host/001",
            query_name="running_processes",
            query_sql="SELECT pid, name FROM processes;",
            result_kind="process",
            rows=({"pid": "123", "name": "sshd"},),
            collected_at=collected_at,
            reviewed_by="analyst-001",
            source_id="gamma",
            collection_path="alpha/source/beta",
        )
        second = adapter.build_attachment(
            case_id="case-001",
            alert_id="alert-001",
            authoritative_host_identifier="host/001",
            host_identifier="host/001",
            query_name="running_processes",
            query_sql="SELECT pid, name FROM processes;",
            result_kind="process",
            rows=({"pid": "123", "name": "sshd"},),
            collected_at=collected_at,
            reviewed_by="analyst-001",
            source_id="beta/source/gamma",
            collection_path="alpha",
        )

        self.assertNotEqual(first.source_record_id, second.source_record_id)
        self.assertIn("host%2F001", first.source_record_id)
        self.assertIn("alpha%2Fsource%2Fbeta", first.source_record_id)
        self.assertIn("beta%2Fsource%2Fgamma", second.source_record_id)

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

    def test_attach_osquery_host_context_rejects_blank_observation_scope_without_writes(
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
            "observation_id requires observation_scope_statement for osquery attachment",
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
                observation_scope_statement="   ",
                observation_id="observation-phase25-blank-scope-001",
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

    def test_attach_osquery_host_context_rejects_oversized_result_cells_without_writes(
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
            r"rows\[0\]\[payload\] exceeds max_cell_bytes=4096",
        ):
            service.attach_osquery_host_context(
                case_id=promoted_case.case_id,
                host_identifier="host-001",
                query_name="running_processes",
                query_sql="SELECT payload FROM process_events;",
                result_kind="process",
                rows=({"payload": "x" * 5000},),
                collected_at=reviewed_at,
                reviewed_by="analyst-001",
                source_id="query-result-oversized-001",
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

    def test_attach_osquery_host_context_merges_case_evidence_ids_from_latest_snapshot(
        self,
    ) -> None:
        store, _service, promoted_case, reviewed_at = self._build_host_bound_case(
            host_identifier="host-001"
        )
        concurrent_evidence = EvidenceRecord(
            evidence_id="evidence-phase25-concurrent-001",
            source_record_id="osquery://host/host-001/concurrent-source",
            alert_id=promoted_case.alert_id,
            case_id=promoted_case.case_id,
            source_system="osquery",
            collector_identity="concurrent-writer",
            acquired_at=reviewed_at,
            derivation_relationship="osquery_host_context",
            lifecycle_state="linked",
            provenance={"classification": "augmenting-evidence"},
            content={"adapter": "concurrent"},
        )

        def mutate_case(inner_store: object) -> None:
            inner_store.save(concurrent_evidence)
            current_case = inner_store.get(CaseRecord, promoted_case.case_id)
            assert current_case is not None
            inner_store.save(
                CaseRecord(
                    case_id=current_case.case_id,
                    alert_id=current_case.alert_id,
                    finding_id=current_case.finding_id,
                    evidence_ids=(
                        *current_case.evidence_ids,
                        concurrent_evidence.evidence_id,
                    ),
                    lifecycle_state=current_case.lifecycle_state,
                    reviewed_context=current_case.reviewed_context,
                )
            )

        wrapped_store = _EvidenceSaveMutationStore(
            inner=store,
            mutate_once=mutate_case,
        )
        service = AegisOpsControlPlaneService(
            RuntimeConfig(postgres_dsn="postgresql://control-plane.local/aegisops"),
            store=wrapped_store,
        )

        evidence, _observation = service.attach_osquery_host_context(
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
        )

        updated_case = wrapped_store.get(CaseRecord, promoted_case.case_id)
        assert updated_case is not None
        self.assertIn("SERIALIZABLE", wrapped_store.transaction_isolation_levels)
        self.assertIn(concurrent_evidence.evidence_id, updated_case.evidence_ids)
        self.assertIn(evidence.evidence_id, updated_case.evidence_ids)


if __name__ == "__main__":
    unittest.main()
