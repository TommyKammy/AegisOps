from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import pathlib
import re
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

import aegisops_control_plane.adapters.postgres as postgres_adapter
import aegisops_control_plane.record_validation as record_validation
from aegisops_control_plane.adapters.postgres import (
    PostgresControlPlaneStore,
    _LIFECYCLE_STATES_BY_FAMILY,
)
from aegisops_control_plane.models import (
    AITraceRecord,
    ActionExecutionRecord,
    ActionRequestRecord,
    AnalyticSignalRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    ControlPlaneRecord,
    EvidenceRecord,
    HuntRecord,
    HuntRunRecord,
    LeadRecord,
    LifecycleTransitionRecord,
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)
from postgres_test_support import (
    FakePostgresBackend,
    FakePostgresConnection,
    FakePostgresCursor,
    make_store,
)


@dataclass(frozen=True)
class UnsupportedRecord(ControlPlaneRecord):
    record_family = "unsupported"
    identifier_field = "unsupported_id"

    unsupported_id: str
    lifecycle_state: str


class _TupleRowClosingBackend(FakePostgresBackend):
    def connect(self, dsn: str) -> "_TupleRowClosingConnection":
        return _TupleRowClosingConnection(self, dsn)


class _TupleRowClosingConnection(FakePostgresConnection):
    def cursor(self) -> "_TupleRowClosingCursor":
        return _TupleRowClosingCursor(self.backend, self.tables, self)


class _TupleRowClosingCursor(FakePostgresCursor):
    def fetchone(self) -> tuple[object, ...] | None:
        row = super().fetchone()
        return self._tuple_row(row)

    def fetchall(self) -> list[tuple[object, ...]]:
        tuple_rows: list[tuple[object, ...]] = []
        for row in super().fetchall():
            tuple_row = self._tuple_row(row)
            assert tuple_row is not None
            tuple_rows.append(tuple_row)
        return tuple_rows

    def close(self) -> None:
        self.description = None

    def _tuple_row(self, row: dict[str, object] | None) -> tuple[object, ...] | None:
        if row is None:
            return None
        assert self.description is not None
        return tuple(row[column[0]] for column in self.description)


class PostgresControlPlaneStoreTests(unittest.TestCase):
    def test_postgres_adapter_uses_shared_record_validation_boundary(self) -> None:
        self.assertIs(
            postgres_adapter._validate_record,
            record_validation._validate_record,
        )
        self.assertIs(
            postgres_adapter._validate_lifecycle_state,
            record_validation._validate_lifecycle_state,
        )
        self.assertIs(
            postgres_adapter._normalize_coordination_reference_record,
            record_validation._normalize_coordination_reference_record,
        )

    def test_store_reports_postgresql_authoritative_persistence_mode(self) -> None:
        store = PostgresControlPlaneStore("postgresql://control-plane.local/aegisops")

        self.assertEqual(store.persistence_mode, "postgresql")
        self.assertEqual(store.dsn, "postgresql://control-plane.local/aegisops")

    def test_phase14_reviewed_context_forward_migration_asset_exists(self) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0002_phase_14_reviewed_context_columns.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 14 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8")
        expected_tables = (
            "alert_records",
            "analytic_signal_records",
            "case_records",
            "recommendation_records",
        )

        self.assertIn("begin;", migration_sql.lower())
        self.assertIn("commit;", migration_sql.lower())
        for table_name in expected_tables:
            self.assertIn(
                f"alter table if exists aegisops_control.{table_name}",
                migration_sql.lower(),
            )
            self.assertIn(
                (
                    f"alter table if exists aegisops_control.{table_name}\n"
                    "  add column if not exists reviewed_context jsonb not null default '{}'::jsonb;"
                ),
                migration_sql.lower(),
            )

    def test_phase15_assistant_advisory_draft_forward_migration_asset_exists(self) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0003_phase_15_assistant_advisory_draft_columns.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 15 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)
        self.assertIn(
            "alter table if exists aegisops_control.recommendation_records",
            migration_sql,
        )
        self.assertIn(
            "alter table if exists aegisops_control.ai_trace_records",
            migration_sql,
        )
        self.assertIn(
            "add column if not exists assistant_advisory_draft jsonb not null default '{}'::jsonb;",
            migration_sql,
        )

    def test_phase20_action_request_binding_forward_migration_asset_exists(self) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0004_phase_20_action_request_binding_columns.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 20 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)
        self.assertIn(
            "alter table if exists aegisops_control.action_request_records",
            migration_sql,
        )
        self.assertIn(
            "add column if not exists requester_identity text;",
            migration_sql,
        )
        self.assertIn(
            "add column if not exists requested_payload jsonb not null default '{}'::jsonb;",
            migration_sql,
        )
        self.assertIn(
            (
                "update aegisops_control.action_request_records\n"
                "set requested_payload = '{}'::jsonb\n"
                "where requested_payload is null;"
            ),
            migration_sql,
        )
        self.assertIn(
            (
                "alter table if exists aegisops_control.action_request_records\n"
                "  alter column requested_payload drop default;"
            ),
            migration_sql,
        )
        self.assertIn("requester_identity text", schema_sql)
        self.assertIn(
            "requested_payload jsonb not null",
            schema_sql,
        )
        self.assertNotIn(
            "requested_payload jsonb not null default '{}'::jsonb",
            schema_sql,
        )

    def test_phase23_approval_decision_rationale_forward_migration_asset_exists(self) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0005_phase_23_approval_decision_rationale.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 23 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()
        bootstrap_sql = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0001_control_plane_schema_skeleton.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)
        self.assertIn(
            "alter table if exists aegisops_control.approval_decision_records",
            migration_sql,
        )
        self.assertIn(
            "add column if not exists decision_rationale text;",
            migration_sql,
        )
        self.assertIn("decision_rationale text", schema_sql)
        self.assertIn("decision_rationale text", bootstrap_sql)

    def test_phase26_external_ticket_reference_forward_migration_asset_exists(
        self,
    ) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0009_phase_26_external_ticket_reference_columns.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 26 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)
        for table_name in ("alert_records", "case_records"):
            self.assertIn(
                f"alter table if exists aegisops_control.{table_name}",
                migration_sql,
            )
        for required_column in (
            "coordination_reference_id text",
            "coordination_target_type text",
            "coordination_target_id text",
            "ticket_reference_url text",
        ):
            self.assertIn(required_column, schema_sql)
        https_host_pattern = (
            "or ticket_reference_url ~* '^https://[^/?#[:space:]]+([/?#][^[:space:]]*)?$'"
        )
        self.assertIn(https_host_pattern, migration_sql)
        self.assertIn(https_host_pattern, schema_sql)

    def test_phase28_action_request_idempotency_unique_index_migration_asset_exists(
        self,
    ) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0010_phase_28_action_request_idempotency_key_unique_index.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 28 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)
        self.assertIn("row_number() over", migration_sql)
        self.assertIn("partition by idempotency_key", migration_sql)
        self.assertIn("order by requested_at asc, action_request_id asc", migration_sql)
        self.assertIn("where idempotency_key is not null", migration_sql)
        self.assertIn(
            "delete from aegisops_control.action_request_records as action_request",
            migration_sql,
        )
        self.assertIn(
            "create unique index if not exists action_request_records_idempotency_key_key",
            migration_sql,
        )
        self.assertIn(
            "create unique index if not exists action_request_records_idempotency_key_key",
            schema_sql,
        )

    def test_phase28_reconciliation_correlation_lookup_index_migration_asset_exists(
        self,
    ) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0011_phase_28_reconciliation_correlation_lookup_index.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 28 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)
        self.assertIn(
            "create index if not exists reconciliation_records_correlation_alert_latest_idx",
            migration_sql,
        )
        self.assertIn("where alert_id is not null", migration_sql)
        self.assertIn(
            "create index if not exists reconciliation_records_correlation_alert_latest_idx",
            schema_sql,
        )
        self.assertIn("where alert_id is not null", schema_sql)

    def test_ai_trace_latest_lookup_index_migration_asset_exists(self) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0012_phase_32_ai_trace_latest_lookup_index.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing AI trace latest lookup migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()

        for sql in (migration_sql, schema_sql):
            self.assertIn("create index if not exists ai_trace_records_latest_idx", sql)
            self.assertIn("on aegisops_control.ai_trace_records", sql)
            self.assertIn("generated_at desc", sql)
            self.assertIn("ai_trace_id desc", sql)

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)

    def test_phase23_lifecycle_transition_forward_migration_asset_exists(self) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0006_phase_23_lifecycle_transition_records.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 23 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()
        bootstrap_sql = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0001_control_plane_schema_skeleton.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)
        self.assertIn(
            "create table if not exists aegisops_control.lifecycle_transition_records",
            migration_sql,
        )
        self.assertIn("'pending_approval'", migration_sql)
        self.assertIn("'pending_approval'", schema_sql)
        self.assertIn("'pending_approval'", bootstrap_sql)

    def test_phase23_lifecycle_transition_subject_index_migration_asset_exists(
        self,
    ) -> None:
        migration_path = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0007_phase_23_lifecycle_transition_subject_index.sql"
        )

        self.assertTrue(
            migration_path.exists(),
            f"Missing Phase 23 forward migration asset: {migration_path}",
        )

        migration_sql = migration_path.read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn("begin;", migration_sql)
        self.assertIn("commit;", migration_sql)
        self.assertIn(
            "create index if not exists lifecycle_transition_records_subject_latest_idx",
            migration_sql,
        )
        self.assertIn(
            "create index if not exists lifecycle_transition_records_subject_latest_idx",
            schema_sql,
        )

    def test_lifecycle_transition_schema_assets_exist(self) -> None:
        migration_sql = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0006_phase_23_lifecycle_transition_records.sql"
        ).read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()
        bootstrap_sql = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0001_control_plane_schema_skeleton.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn(
            "create table if not exists aegisops_control.lifecycle_transition_records",
            schema_sql,
        )
        self.assertIn("transition_id text primary key", schema_sql)
        self.assertIn("previous_lifecycle_state text", schema_sql)
        self.assertIn("attribution jsonb not null default '{}'::jsonb", schema_sql)
        self.assertIn(
            "create index if not exists lifecycle_transition_records_subject_latest_idx",
            schema_sql,
        )
        self.assertIn("subject_record_family in (", schema_sql)
        self.assertIn("previous_lifecycle_state is null or previous_lifecycle_state in (", schema_sql)
        self.assertIn("'pending_approval'", schema_sql)
        self.assertIn(
            "create table if not exists aegisops_control.lifecycle_transition_records",
            migration_sql,
        )
        self.assertIn("transition_id text primary key", migration_sql)
        self.assertIn("previous_lifecycle_state text", migration_sql)
        self.assertIn(
            "attribution jsonb not null default '{}'::jsonb",
            migration_sql,
        )
        self.assertIn("subject_record_family in (", migration_sql)
        self.assertIn(
            "previous_lifecycle_state is null or previous_lifecycle_state in (",
            migration_sql,
        )
        self.assertIn("'pending_approval'", migration_sql)
        self.assertNotIn(
            "create table if not exists aegisops_control.lifecycle_transition_records",
            bootstrap_sql,
        )

    def test_lifecycle_transition_schema_assets_bind_states_to_subject_families(
        self,
    ) -> None:
        migration_sql = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0006_phase_23_lifecycle_transition_records.sql"
        ).read_text(encoding="utf-8").lower()
        schema_sql = (
            CONTROL_PLANE_ROOT.parent / "postgres" / "control-plane" / "schema.sql"
        ).read_text(encoding="utf-8").lower()
        expected_states_by_family = {
            family: states
            for family, states in _LIFECYCLE_STATES_BY_FAMILY.items()
            if family != LifecycleTransitionRecord.record_family
        }

        for sql_text in (migration_sql, schema_sql):
            self.assertIn(
                "constraint lifecycle_transition_records_state_matches_subject_family check (",
                sql_text,
            )
            self.assertIn(
                "constraint lifecycle_transition_records_previous_state_matches_subject_family check (",
                sql_text,
            )
            for family, expected_states in expected_states_by_family.items():
                self.assertEqual(
                    self._extract_transition_state_set(
                        sql_text,
                        family,
                        "lifecycle_state",
                    ),
                    expected_states,
                )
                self.assertEqual(
                    self._extract_transition_state_set(
                        sql_text,
                        family,
                        "previous_lifecycle_state",
                    ),
                    expected_states,
                )

    def test_phase23_lifecycle_transition_migration_backfills_existing_authoritative_rows(
        self,
    ) -> None:
        migration_sql = (
            CONTROL_PLANE_ROOT.parent
            / "postgres"
            / "control-plane"
            / "migrations"
            / "0006_phase_23_lifecycle_transition_records.sql"
        ).read_text(encoding="utf-8").lower()

        self.assertIn(
            "insert into aegisops_control.lifecycle_transition_records",
            migration_sql,
        )
        self.assertIn("'phase23-migration-backfill'", migration_sql)
        self.assertIn(
            "coalesce(first_seen_at, last_seen_at, created_at, updated_at)",
            migration_sql,
        )
        self.assertIn(
            "coalesce(first_seen_at, last_seen_at, compared_at, created_at, updated_at)",
            migration_sql,
        )
        self.assertIn("reviewed_context -> 'triage' ->> 'recorded_at'", migration_sql)
        self.assertIn("reviewed_context -> 'triage' ->> 'disposition'", migration_sql)
        self.assertIn("lifecycle_state = 'pending_action'", migration_sql)
        self.assertIn("::timestamptz", migration_sql)
        self.assertIn("where existing.transition_id is null", migration_sql)
        self.assertIn("on conflict (transition_id) do nothing", migration_sql)
        for table_name in (
            "analytic_signal_records",
            "alert_records",
            "evidence_records",
            "observation_records",
            "lead_records",
            "case_records",
            "recommendation_records",
            "approval_decision_records",
            "action_request_records",
            "action_execution_records",
            "hunt_records",
            "hunt_run_records",
            "ai_trace_records",
            "reconciliation_records",
        ):
            self.assertIn(f"aegisops_control.{table_name}", migration_sql)

    def test_store_round_trips_reviewed_record_families_by_aegisops_ids(self) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        records = [
            AlertRecord(
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id="signal-001",
                case_id="case-001",
                lifecycle_state="investigating",
                reviewed_context={
                    "review": {"status": "approved"},
                    "analyst": {"identity_id": "analyst-001"},
                },
            ),
            AnalyticSignalRecord(
                analytic_signal_id="signal-001",
                substrate_detection_record_id="substrate-detection-001",
                finding_id="finding-001",
                alert_ids=("alert-001",),
                case_ids=("case-001",),
                correlation_key="claim:host-001:privilege-escalation",
                first_seen_at=timestamp,
                last_seen_at=timestamp,
                lifecycle_state="active",
                reviewed_context={
                    "review": {"status": "approved"},
                    "source": {"source_family": "wazuh"},
                },
            ),
            CaseRecord(
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                evidence_ids=("evidence-001",),
                lifecycle_state="investigating",
                reviewed_context={
                    "review": {"status": "approved"},
                    "case_owner": {"identity_id": "analyst-001"},
                },
            ),
            EvidenceRecord(
                evidence_id="evidence-001",
                source_record_id="artifact-001",
                alert_id="alert-001",
                case_id="case-001",
                source_system="opensearch",
                collector_identity="collector-001",
                acquired_at=timestamp,
                derivation_relationship="original",
                lifecycle_state="linked",
                provenance={
                    "classification": "augmenting-evidence",
                    "source_id": "artifact-001",
                },
                content={"result": {"kind": "process", "row_count": 1}},
            ),
            ObservationRecord(
                observation_id="observation-001",
                hunt_id="hunt-001",
                hunt_run_id="hunt-run-001",
                alert_id="alert-001",
                case_id="case-001",
                supporting_evidence_ids=("evidence-001",),
                author_identity="analyst-001",
                observed_at=timestamp,
                scope_statement="bounded triage observation",
                lifecycle_state="confirmed",
                provenance={"classification": "reviewed-derived"},
                content={"host_context_evidence_id": "evidence-001"},
            ),
            LeadRecord(
                lead_id="lead-001",
                observation_id="observation-001",
                finding_id="finding-001",
                hunt_run_id="hunt-run-001",
                alert_id="alert-001",
                case_id="case-001",
                triage_owner="analyst-001",
                triage_rationale="requires follow-up",
                lifecycle_state="triaged",
            ),
            RecommendationRecord(
                recommendation_id="recommendation-001",
                lead_id="lead-001",
                hunt_run_id="hunt-run-001",
                alert_id="alert-001",
                case_id="case-001",
                ai_trace_id="ai-trace-001",
                review_owner="reviewer-001",
                intended_outcome="escalate for action review",
                lifecycle_state="under_review",
                reviewed_context={
                    "review": {"status": "approved"},
                    "priority": "high",
                },
                assistant_advisory_draft={
                    "draft_id": "assistant-advisory-draft:recommendation:recommendation-001",
                    "source_record_family": "recommendation",
                    "source_record_id": "recommendation-001",
                    "review_lifecycle_state": "under_review",
                    "status": "ready",
                    "citations": ("recommendation-001", "evidence-001"),
                },
            ),
            ApprovalDecisionRecord(
                approval_decision_id="approval-001",
                action_request_id="action-request-001",
                approver_identities=("approver-001",),
                target_snapshot={"asset_id": "asset-001"},
                payload_hash="payload-hash-001",
                decided_at=timestamp,
                lifecycle_state="approved",
                approved_expires_at=timestamp,
            ),
            ActionRequestRecord(
                action_request_id="action-request-001",
                approval_decision_id="approval-001",
                case_id="case-001",
                alert_id="alert-001",
                finding_id="finding-001",
                idempotency_key="idempotency-001",
                target_scope={"asset_id": "asset-001"},
                requester_identity="analyst-001",
                requested_payload={"action_type": "notify_identity_owner"},
                policy_basis={
                    "severity": "high",
                    "target_scope": "single_asset",
                    "action_reversibility": "bounded_reversible",
                    "asset_criticality": "high",
                    "identity_criticality": "standard",
                    "blast_radius": "bounded_group",
                    "execution_constraint": "routine_allowed",
                },
                policy_evaluation={
                    "approval_requirement": "human_required",
                    "routing_target": "approval",
                    "execution_surface_type": "automation_substrate",
                    "execution_surface_id": "shuffle",
                },
                payload_hash="payload-hash-001",
                requested_at=timestamp,
                expires_at=None,
                lifecycle_state="approved",
            ),
            ActionExecutionRecord(
                action_execution_id="action-execution-001",
                action_request_id="action-request-001",
                approval_decision_id="approval-001",
                delegation_id="delegation-001",
                execution_surface_type="automation_substrate",
                execution_surface_id="shuffle",
                execution_run_id="shuffle-run-delegation-001",
                idempotency_key="idempotency-001",
                target_scope={"asset_id": "asset-001"},
                approved_payload={"action_type": "notify_identity_owner"},
                payload_hash="payload-hash-001",
                delegated_at=timestamp,
                expires_at=None,
                provenance={"delegation_issuer": "control-plane-service"},
                lifecycle_state="queued",
            ),
            HuntRecord(
                hunt_id="hunt-001",
                hypothesis_statement="suspicious persistence attempt",
                hypothesis_version="v1",
                owner_identity="hunter-001",
                scope_boundary="prod-endpoints",
                opened_at=timestamp,
                alert_id="alert-001",
                case_id="case-001",
                lifecycle_state="active",
            ),
            HuntRunRecord(
                hunt_run_id="hunt-run-001",
                hunt_id="hunt-001",
                scope_snapshot={"window": "24h"},
                execution_plan_reference="hunt-plan-001",
                output_linkage={"lead_ids": ["lead-001"]},
                started_at=timestamp,
                completed_at=None,
                lifecycle_state="running",
            ),
            AITraceRecord(
                ai_trace_id="ai-trace-001",
                subject_linkage={"recommendation_ids": ["recommendation-001"]},
                model_identity="gpt-5.4",
                prompt_version="prompt-v1",
                generated_at=timestamp,
                material_input_refs=("evidence-001",),
                reviewer_identity="reviewer-001",
                lifecycle_state="accepted_for_reference",
                assistant_advisory_draft={
                    "draft_id": "assistant-advisory-draft:ai_trace:ai-trace-001",
                    "source_record_family": "ai_trace",
                    "source_record_id": "ai-trace-001",
                    "review_lifecycle_state": "under_review",
                    "status": "ready",
                    "citations": ("ai-trace-001", "evidence-001", "recommendation-001"),
                },
            ),
            ReconciliationRecord(
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
            ),
        ]

        for record in records:
            store.save(record)

        expected_records = [
            (AlertRecord, "alert-001", records[0]),
            (AnalyticSignalRecord, "signal-001", records[1]),
            (CaseRecord, "case-001", records[2]),
            (EvidenceRecord, "evidence-001", records[3]),
            (ObservationRecord, "observation-001", records[4]),
            (LeadRecord, "lead-001", records[5]),
            (RecommendationRecord, "recommendation-001", records[6]),
            (ApprovalDecisionRecord, "approval-001", records[7]),
            (ActionRequestRecord, "action-request-001", records[8]),
            (ActionExecutionRecord, "action-execution-001", records[9]),
            (HuntRecord, "hunt-001", records[10]),
            (HuntRunRecord, "hunt-run-001", records[11]),
            (AITraceRecord, "ai-trace-001", records[12]),
            (ReconciliationRecord, "reconciliation-001", records[13]),
        ]

        for record_type, record_id, expected_record in expected_records:
            with self.subTest(record_type=record_type.__name__, record_id=record_id):
                self.assertEqual(store.get(record_type, record_id), expected_record)

        self.assertEqual(
            store.get(AlertRecord, "alert-001").reviewed_context,
            records[0].reviewed_context,
        )
        self.assertEqual(
            store.get(AnalyticSignalRecord, "signal-001").reviewed_context,
            records[1].reviewed_context,
        )
        self.assertEqual(
            store.get(CaseRecord, "case-001").reviewed_context,
            records[2].reviewed_context,
        )
        self.assertEqual(
            store.get(RecommendationRecord, "recommendation-001").reviewed_context,
            records[6].reviewed_context,
        )
        self.assertEqual(
            store.get(
                RecommendationRecord,
                "recommendation-001",
            ).assistant_advisory_draft,
            records[6].assistant_advisory_draft,
        )
        self.assertEqual(
            store.get(AITraceRecord, "ai-trace-001").assistant_advisory_draft,
            records[12].assistant_advisory_draft,
        )

        self.assertIsNone(store.get(AlertRecord, "finding-001"))
        self.assertIsNone(store.get(ActionRequestRecord, "approval-001"))
        self.assertIsNone(store.get(ReconciliationRecord, "n8n-exec-001"))

    def test_store_round_trips_assistant_advisory_draft_revision_history(self) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        recommendation = RecommendationRecord(
            recommendation_id="recommendation-history-001",
            lead_id="lead-001",
            hunt_run_id=None,
            alert_id="alert-001",
            case_id="case-001",
            ai_trace_id=None,
            review_owner="reviewer-001",
            intended_outcome="preserve prior draft snapshots",
            lifecycle_state="under_review",
            assistant_advisory_draft={
                "draft_id": "assistant-advisory-draft:recommendation:recommendation-history-001",
                "source_record_family": "recommendation",
                "source_record_id": "recommendation-history-001",
                "review_lifecycle_state": "under_review",
                "status": "ready",
                "citations": ("recommendation-history-001", "evidence-002"),
                "revision_history": (
                    {
                        "draft_id": "assistant-advisory-draft:recommendation:recommendation-history-001",
                        "source_record_family": "recommendation",
                        "source_record_id": "recommendation-history-001",
                        "review_lifecycle_state": "under_review",
                        "status": "insufficient_evidence",
                        "citations": ("recommendation-history-001",),
                    },
                ),
            },
        )
        ai_trace = AITraceRecord(
            ai_trace_id="ai-trace-history-001",
            subject_linkage={"recommendation_ids": ["recommendation-history-001"]},
            model_identity="gpt-5.4",
            prompt_version="prompt-v1",
            generated_at=timestamp,
            material_input_refs=("evidence-002",),
            reviewer_identity="reviewer-001",
            lifecycle_state="under_review",
            assistant_advisory_draft={
                "draft_id": "assistant-advisory-draft:ai_trace:ai-trace-history-001",
                "source_record_family": "ai_trace",
                "source_record_id": "ai-trace-history-001",
                "review_lifecycle_state": "under_review",
                "status": "ready",
                "citations": ("ai-trace-history-001", "recommendation-history-001"),
                "revision_history": (
                    {
                        "draft_id": "assistant-advisory-draft:ai_trace:ai-trace-history-001",
                        "source_record_family": "ai_trace",
                        "source_record_id": "ai-trace-history-001",
                        "review_lifecycle_state": "under_review",
                        "status": "ready",
                        "citations": ("ai-trace-history-001",),
                    },
                ),
            },
        )

        store.save(recommendation)
        store.save(ai_trace)

        self.assertEqual(
            store.get(
                RecommendationRecord,
                recommendation.recommendation_id,
            ).assistant_advisory_draft,
            recommendation.assistant_advisory_draft,
        )
        self.assertEqual(
            store.get(
                AITraceRecord,
                ai_trace.ai_trace_id,
            ).assistant_advisory_draft,
            ai_trace.assistant_advisory_draft,
        )

    def test_lifecycle_transition_records_are_insert_only(self) -> None:
        store, _ = make_store()
        transitioned_at = datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc)
        original = LifecycleTransitionRecord(
            transition_id="transition-001",
            subject_record_family="case",
            subject_record_id="case-001",
            previous_lifecycle_state=None,
            lifecycle_state="open",
            transitioned_at=transitioned_at,
            attribution={"actor_identity": "analyst-001"},
        )
        conflicting = LifecycleTransitionRecord(
            transition_id="transition-001",
            subject_record_family="case",
            subject_record_id="case-001",
            previous_lifecycle_state="open",
            lifecycle_state="closed",
            transitioned_at=transitioned_at,
            attribution={"actor_identity": "analyst-002"},
        )

        store.save(original)

        with self.assertRaisesRegex(
            ValueError,
            "duplicate key value violates unique constraint",
        ):
            store.save(conflicting)

        self.assertEqual(
            store.get(LifecycleTransitionRecord, "transition-001"),
            original,
        )

    def test_lifecycle_transition_records_require_supported_subject_family(self) -> None:
        store, _ = make_store()

        with self.assertRaisesRegex(
            ValueError,
            (
                r"lifecycle_transition record 'transition-unsupported-family' has unsupported "
                r"subject_record_family 'typo_family'"
            ),
        ):
            store.save(
                LifecycleTransitionRecord(
                    transition_id="transition-unsupported-family",
                    subject_record_family="typo_family",
                    subject_record_id="record-001",
                    previous_lifecycle_state=None,
                    lifecycle_state="open",
                    transitioned_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
                    attribution={},
                )
            )

    def test_lifecycle_transition_records_require_valid_subject_lifecycle_states(self) -> None:
        store, _ = make_store()

        with self.assertRaisesRegex(
            ValueError,
            (
                r"lifecycle_transition record 'transition-invalid-state' has invalid "
                r"lifecycle_state 'closed' for subject_record_family 'recommendation'"
            ),
        ):
            store.save(
                LifecycleTransitionRecord(
                    transition_id="transition-invalid-state",
                    subject_record_family="recommendation",
                    subject_record_id="recommendation-001",
                    previous_lifecycle_state="proposed",
                    lifecycle_state="closed",
                    transitioned_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
                    attribution={},
                )
            )

    def test_lifecycle_transition_records_allow_pending_approval_for_action_requests(
        self,
    ) -> None:
        store, _ = make_store()
        transition = LifecycleTransitionRecord(
            transition_id="transition-pending-approval",
            subject_record_family="action_request",
            subject_record_id="action-request-001",
            previous_lifecycle_state="draft",
            lifecycle_state="pending_approval",
            transitioned_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            attribution={"actor_identity": "reviewer-001"},
        )

        store.save(transition)

        self.assertEqual(
            store.get(LifecycleTransitionRecord, transition.transition_id),
            transition,
        )

    def test_store_reads_latest_lifecycle_transition_by_subject(self) -> None:
        store, _ = make_store()
        first_transition = LifecycleTransitionRecord(
            transition_id="transition-latest-001",
            subject_record_family="case",
            subject_record_id="case-latest-001",
            previous_lifecycle_state=None,
            lifecycle_state="open",
            transitioned_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            attribution={"source": "fixture", "actor_identities": ()},
        )
        latest_transition = LifecycleTransitionRecord(
            transition_id="transition-latest-002",
            subject_record_family="case",
            subject_record_id="case-latest-001",
            previous_lifecycle_state="open",
            lifecycle_state="closed",
            transitioned_at=datetime(2026, 4, 16, 8, 5, tzinfo=timezone.utc),
            attribution={"source": "fixture", "actor_identities": ()},
        )
        unrelated_transition = LifecycleTransitionRecord(
            transition_id="transition-latest-003",
            subject_record_family="case",
            subject_record_id="case-latest-002",
            previous_lifecycle_state=None,
            lifecycle_state="open",
            transitioned_at=datetime(2026, 4, 16, 8, 10, tzinfo=timezone.utc),
            attribution={"source": "fixture", "actor_identities": ()},
        )

        for transition in (
            first_transition,
            latest_transition,
            unrelated_transition,
        ):
            store.save(transition)

        self.assertEqual(
            store.latest_lifecycle_transition("case", "case-latest-001"),
            latest_transition,
        )
        self.assertIsNone(
            store.latest_lifecycle_transition("alert", "alert-missing-001")
        )

    def test_store_lists_latest_reconciliation_by_correlation_key(self) -> None:
        store, backend = make_store()
        older = ReconciliationRecord(
            reconciliation_id="reconciliation-correlation-older",
            subject_linkage={"finding_ids": ["finding-correlation-001"]},
            alert_id="alert-correlation-001",
            finding_id="finding-correlation-001",
            analytic_signal_id="signal-correlation-001",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:correlation-lookup",
            first_seen_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 16, 8, 1, tzinfo=timezone.utc),
            ingest_disposition="created",
            mismatch_summary="",
            compared_at=datetime(2026, 4, 16, 8, 2, tzinfo=timezone.utc),
            lifecycle_state="matched",
        )
        latest_without_alert = ReconciliationRecord(
            reconciliation_id="reconciliation-correlation-latest-without-alert",
            subject_linkage={"finding_ids": ["finding-correlation-002"]},
            alert_id=None,
            finding_id="finding-correlation-002",
            analytic_signal_id="signal-correlation-002",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:correlation-lookup",
            first_seen_at=datetime(2026, 4, 16, 8, 3, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 16, 8, 4, tzinfo=timezone.utc),
            ingest_disposition="matched",
            mismatch_summary="",
            compared_at=datetime(2026, 4, 16, 8, 9, tzinfo=timezone.utc),
            lifecycle_state="matched",
        )
        latest_with_alert = ReconciliationRecord(
            reconciliation_id="reconciliation-correlation-latest-with-alert",
            subject_linkage={"finding_ids": ["finding-correlation-003"]},
            alert_id="alert-correlation-003",
            finding_id="finding-correlation-003",
            analytic_signal_id="signal-correlation-003",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:correlation-lookup",
            first_seen_at=datetime(2026, 4, 16, 8, 6, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 16, 8, 7, tzinfo=timezone.utc),
            ingest_disposition="restated",
            mismatch_summary="",
            compared_at=datetime(2026, 4, 16, 8, 8, tzinfo=timezone.utc),
            lifecycle_state="matched",
        )
        unrelated = ReconciliationRecord(
            reconciliation_id="reconciliation-correlation-unrelated",
            subject_linkage={"finding_ids": ["finding-correlation-004"]},
            alert_id="alert-correlation-004",
            finding_id="finding-correlation-004",
            analytic_signal_id="signal-correlation-004",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:other",
            first_seen_at=datetime(2026, 4, 16, 8, 10, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 16, 8, 11, tzinfo=timezone.utc),
            ingest_disposition="matched",
            mismatch_summary="",
            compared_at=datetime(2026, 4, 16, 8, 12, tzinfo=timezone.utc),
            lifecycle_state="matched",
        )

        for record in (older, latest_without_alert, latest_with_alert, unrelated):
            store.save(record)

        statement_count_before = len(backend.statements)
        latest = store.latest_reconciliation_for_correlation_key(
            "claim:host-001:correlation-lookup"
        )
        latest_with_required_alert = store.latest_reconciliation_for_correlation_key(
            "claim:host-001:correlation-lookup",
            require_alert_id=True,
        )

        self.assertEqual(latest, latest_without_alert)
        self.assertEqual(latest_with_required_alert, latest_with_alert)
        self.assertEqual(
            backend.statements[statement_count_before][0],
            "select reconciliation_id, subject_linkage, alert_id, finding_id, analytic_signal_id, execution_run_id, linked_execution_run_ids, correlation_key, first_seen_at, last_seen_at, ingest_disposition, mismatch_summary, compared_at, lifecycle_state from aegisops_control.reconciliation_records where correlation_key = %s order by compared_at desc, reconciliation_id desc limit 1",
        )
        self.assertEqual(
            backend.statements[statement_count_before + 1][0],
            "select reconciliation_id, subject_linkage, alert_id, finding_id, analytic_signal_id, execution_run_id, linked_execution_run_ids, correlation_key, first_seen_at, last_seen_at, ingest_disposition, mismatch_summary, compared_at, lifecycle_state from aegisops_control.reconciliation_records where correlation_key = %s and alert_id is not null order by compared_at desc, reconciliation_id desc limit 1",
        )

    def test_reconciliation_lookup_maps_tuple_rows_before_cursor_close(self) -> None:
        store, _ = make_store(_TupleRowClosingBackend())
        older = ReconciliationRecord(
            reconciliation_id="reconciliation-tuple-001",
            subject_linkage={"finding_ids": ["finding-tuple-001"]},
            alert_id="alert-tuple-001",
            finding_id="finding-tuple-001",
            analytic_signal_id="signal-tuple-001",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:tuple-lookup",
            first_seen_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 16, 8, 1, tzinfo=timezone.utc),
            ingest_disposition="created",
            mismatch_summary="",
            compared_at=datetime(2026, 4, 16, 8, 2, tzinfo=timezone.utc),
            lifecycle_state="matched",
        )
        latest = ReconciliationRecord(
            reconciliation_id="reconciliation-tuple-002",
            subject_linkage={"finding_ids": ["finding-tuple-001", "finding-tuple-002"]},
            alert_id="alert-tuple-001",
            finding_id="finding-tuple-002",
            analytic_signal_id="signal-tuple-002",
            execution_run_id=None,
            linked_execution_run_ids=(),
            correlation_key="claim:host-001:tuple-lookup",
            first_seen_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 16, 8, 3, tzinfo=timezone.utc),
            ingest_disposition="restated",
            mismatch_summary="",
            compared_at=datetime(2026, 4, 16, 8, 4, tzinfo=timezone.utc),
            lifecycle_state="matched",
        )

        for record in (older, latest):
            store.save(record)

        self.assertEqual(
            store.latest_reconciliation_for_correlation_key(
                "claim:host-001:tuple-lookup"
            ),
            latest,
        )

    def test_store_lists_lifecycle_transitions_by_subject(self) -> None:
        store, _ = make_store()
        first_transition = LifecycleTransitionRecord(
            transition_id="transition-history-001",
            subject_record_family="case",
            subject_record_id="case-history-001",
            previous_lifecycle_state=None,
            lifecycle_state="open",
            transitioned_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            attribution={"source": "fixture", "actor_identities": ()},
        )
        latest_transition = LifecycleTransitionRecord(
            transition_id="transition-history-002",
            subject_record_family="case",
            subject_record_id="case-history-001",
            previous_lifecycle_state="open",
            lifecycle_state="closed",
            transitioned_at=datetime(2026, 4, 16, 8, 5, tzinfo=timezone.utc),
            attribution={"source": "fixture", "actor_identities": ()},
        )
        unrelated_transition = LifecycleTransitionRecord(
            transition_id="transition-history-003",
            subject_record_family="case",
            subject_record_id="case-history-002",
            previous_lifecycle_state=None,
            lifecycle_state="open",
            transitioned_at=datetime(2026, 4, 16, 8, 10, tzinfo=timezone.utc),
            attribution={"source": "fixture", "actor_identities": ()},
        )

        for transition in (
            latest_transition,
            unrelated_transition,
            first_transition,
        ):
            store.save(transition)

        self.assertEqual(
            store.list_lifecycle_transitions("case", "case-history-001"),
            (first_transition, latest_transition),
        )
        self.assertEqual(
            store.list_lifecycle_transitions("alert", "alert-missing-001"),
            (),
        )

    def test_lifecycle_transition_queries_map_tuple_rows_before_cursor_close(
        self,
    ) -> None:
        store, _ = make_store(_TupleRowClosingBackend())
        first_transition = LifecycleTransitionRecord(
            transition_id="transition-tuple-001",
            subject_record_family="case",
            subject_record_id="case-tuple-001",
            previous_lifecycle_state=None,
            lifecycle_state="open",
            transitioned_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            attribution={"source": "fixture", "actor_identities": ()},
        )
        latest_transition = LifecycleTransitionRecord(
            transition_id="transition-tuple-002",
            subject_record_family="case",
            subject_record_id="case-tuple-001",
            previous_lifecycle_state="open",
            lifecycle_state="closed",
            transitioned_at=datetime(2026, 4, 16, 8, 5, tzinfo=timezone.utc),
            attribution={"source": "fixture", "actor_identities": ()},
        )

        for transition in (first_transition, latest_transition):
            store.save(transition)

        self.assertEqual(
            store.latest_lifecycle_transition("case", "case-tuple-001"),
            latest_transition,
        )
        self.assertEqual(
            store.list_lifecycle_transitions("case", "case-tuple-001"),
            (first_transition, latest_transition),
        )

    def test_store_copies_mapping_fields_before_persistence(self) -> None:
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        target_scope = {"asset_id": "asset-001"}
        record = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id="approval-001",
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope=target_scope,
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="approved",
        )

        target_scope["asset_id"] = "asset-002"

        self.assertEqual(record.target_scope["asset_id"], "asset-001")
        with self.assertRaises(TypeError):
            record.target_scope["asset_id"] = "asset-003"  # type: ignore[index]

    def test_store_rejects_duplicate_action_request_idempotency_keys(self) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        first = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id=None,
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            requester_identity="analyst-001",
            requested_payload={"action_type": "collect_endpoint_evidence_pack"},
            policy_basis={"severity": "medium"},
            policy_evaluation={"routing_target": "approval"},
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="pending_approval",
        )
        conflicting = ActionRequestRecord(
            action_request_id="action-request-002",
            approval_decision_id=None,
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            requester_identity="analyst-001",
            requested_payload={"action_type": "collect_endpoint_evidence_pack"},
            policy_basis={"severity": "medium"},
            policy_evaluation={"routing_target": "approval"},
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="pending_approval",
        )

        store.save(first)

        with self.assertRaisesRegex(
            ValueError,
            "duplicate key value violates unique constraint",
        ):
            store.save(conflicting)

        self.assertEqual(store.list(ActionRequestRecord), (first,))

    def test_create_action_request_if_absent_returns_existing_idempotent_record(
        self,
    ) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        first = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id=None,
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            requester_identity="analyst-001",
            requested_payload={"action_type": "collect_endpoint_evidence_pack"},
            policy_basis={"severity": "medium"},
            policy_evaluation={"routing_target": "approval"},
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="pending_approval",
        )
        duplicate = ActionRequestRecord(
            action_request_id="action-request-002",
            approval_decision_id=None,
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            requester_identity="analyst-001",
            requested_payload={"action_type": "collect_endpoint_evidence_pack"},
            policy_basis={"severity": "medium"},
            policy_evaluation={"routing_target": "approval"},
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="pending_approval",
        )

        created, created_new = store.create_action_request_if_absent(first)
        replayed, replay_created = store.create_action_request_if_absent(duplicate)

        self.assertEqual(created, first)
        self.assertEqual(replayed, first)
        self.assertTrue(created_new)
        self.assertFalse(replay_created)
        self.assertEqual(store.list(ActionRequestRecord), (first,))

    def test_create_action_request_if_absent_rejects_conflicting_payload_hash(
        self,
    ) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        first = ActionRequestRecord(
            action_request_id="action-request-001",
            approval_decision_id=None,
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            requester_identity="analyst-001",
            requested_payload={"action_type": "collect_endpoint_evidence_pack"},
            policy_basis={"severity": "medium"},
            policy_evaluation={"routing_target": "approval"},
            payload_hash="payload-hash-001",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="pending_approval",
        )
        conflicting = ActionRequestRecord(
            action_request_id="action-request-002",
            approval_decision_id=None,
            case_id="case-001",
            alert_id="alert-001",
            finding_id="finding-001",
            idempotency_key="idempotency-001",
            target_scope={"asset_id": "asset-001"},
            requester_identity="analyst-001",
            requested_payload={"action_type": "collect_endpoint_evidence_pack"},
            policy_basis={"severity": "medium"},
            policy_evaluation={"routing_target": "approval"},
            payload_hash="payload-hash-002",
            requested_at=timestamp,
            expires_at=None,
            lifecycle_state="pending_approval",
        )

        store.create_action_request_if_absent(first)

        with self.assertRaisesRegex(
            ValueError,
            "idempotency_key already exists for a different action request payload",
        ):
            store.create_action_request_if_absent(conflicting)

        self.assertEqual(store.list(ActionRequestRecord), (first,))

    def test_store_freezes_nested_json_fields_after_round_trip(self) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        record = ReconciliationRecord(
            reconciliation_id="reconciliation-immutable-001",
            subject_linkage={
                "action_request_ids": ["action-request-001"],
                "targets": [{"asset_id": "asset-001"}],
            },
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

        store.save(record)
        persisted = store.get(ReconciliationRecord, "reconciliation-immutable-001")

        assert persisted is not None
        with self.assertRaises(TypeError):
            persisted.subject_linkage["action_request_ids"] += ("action-request-002",)
        with self.assertRaises(TypeError):
            persisted.subject_linkage["targets"][0]["asset_id"] = "asset-002"  # type: ignore[index]

    def test_store_lists_execution_reconciliation_records_separately(self) -> None:
        store, _ = make_store()
        requested_at = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)
        compared_at = datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc)
        records = (
            ReconciliationRecord(
                reconciliation_id="reconciliation-001",
                subject_linkage={
                    "action_request_ids": ["action-request-001"],
                    "execution_surface_types": ["automation_substrate"],
                    "execution_surface_ids": ["n8n"],
                },
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=(
                    "action-request-001:automation_substrate:n8n:idempotency-001"
                ),
                first_seen_at=requested_at,
                last_seen_at=requested_at,
                ingest_disposition="missing",
                mismatch_summary=(
                    "missing downstream execution for approved action request correlation"
                ),
                compared_at=compared_at,
                lifecycle_state="pending",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-002",
                subject_linkage={
                    "action_request_ids": ["action-request-001"],
                    "execution_surface_types": ["automation_substrate"],
                    "execution_surface_ids": ["n8n"],
                },
                alert_id="alert-001",
                finding_id="finding-001",
                analytic_signal_id=None,
                execution_run_id="exec-002",
                linked_execution_run_ids=("exec-001", "exec-002"),
                correlation_key=(
                    "action-request-001:automation_substrate:n8n:idempotency-001"
                ),
                first_seen_at=requested_at,
                last_seen_at=compared_at,
                ingest_disposition="duplicate",
                mismatch_summary=(
                    "duplicate downstream executions observed for one approved request"
                ),
                compared_at=compared_at,
                lifecycle_state="mismatched",
            ),
        )

        for record in records:
            store.save(record)

        stored_records = store.list(ReconciliationRecord)

        self.assertEqual(stored_records, records)
        self.assertEqual(
            tuple(record.ingest_disposition for record in stored_records),
            ("missing", "duplicate"),
        )
        self.assertIsNone(store.get(ReconciliationRecord, "exec-002"))
        self.assertEqual(
            store.get(ReconciliationRecord, "reconciliation-002"),
            records[1],
        )

    def test_store_readiness_review_path_records_use_timezone_safe_multi_field_sort_key(
        self,
    ) -> None:
        store, _ = make_store()
        compared_at = datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc)
        action_request_id = "action-request-readiness-review-path-001"
        records = (
            ReconciliationRecord(
                reconciliation_id="reconciliation-last-seen-wins",
                subject_linkage={"action_request_ids": [action_request_id]},
                alert_id=None,
                finding_id="finding-readiness-001",
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=f"{action_request_id}:automation_substrate:n8n:001",
                first_seen_at=datetime(2026, 4, 16, 7, 40, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 16, 7, 56, tzinfo=timezone.utc),
                ingest_disposition="missing",
                mismatch_summary="missing downstream execution",
                compared_at=compared_at,
                lifecycle_state="pending",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-first-seen-wins",
                subject_linkage={"action_request_ids": [action_request_id]},
                alert_id=None,
                finding_id="finding-readiness-001",
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=f"{action_request_id}:automation_substrate:n8n:002",
                first_seen_at=datetime(2026, 4, 16, 7, 50, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 16, 7, 55, tzinfo=timezone.utc),
                ingest_disposition="missing",
                mismatch_summary="missing downstream execution",
                compared_at=compared_at,
                lifecycle_state="pending",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-first-seen-loses",
                subject_linkage={"action_request_ids": [action_request_id]},
                alert_id=None,
                finding_id="finding-readiness-001",
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=f"{action_request_id}:automation_substrate:n8n:003",
                first_seen_at=datetime(2026, 4, 16, 7, 45, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 16, 7, 55, tzinfo=timezone.utc),
                ingest_disposition="missing",
                mismatch_summary="missing downstream execution",
                compared_at=compared_at,
                lifecycle_state="pending",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-naive-compared-at",
                subject_linkage={"action_request_ids": [action_request_id]},
                alert_id=None,
                finding_id="finding-readiness-001",
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=f"{action_request_id}:automation_substrate:n8n:004",
                first_seen_at=datetime(2026, 4, 16, 7, 35),
                last_seen_at=datetime(2026, 4, 16, 7, 58),
                ingest_disposition="missing",
                mismatch_summary="missing downstream execution",
                compared_at=datetime(2026, 4, 16, 7, 59),
                lifecycle_state="pending",
            ),
        )

        for record in records:
            store.save(record)

        readiness_records = store.inspect_readiness_review_path_records(
            action_request_ids=(action_request_id,),
            approval_decision_ids=(),
        )

        self.assertEqual(
            tuple(
                record.reconciliation_id
                for record in readiness_records.reconciliations
            ),
            (
                "reconciliation-last-seen-wins",
                "reconciliation-first-seen-wins",
                "reconciliation-first-seen-loses",
                "reconciliation-naive-compared-at",
            ),
        )

    def test_readiness_review_path_records_use_repeatable_read_snapshot(self) -> None:
        store, backend = make_store()
        action_request_id = "action-request-readiness-snapshot-001"
        approval_decision_id = "approval-readiness-snapshot-001"
        delegation_id = "delegation-readiness-snapshot-001"
        action_execution = ActionExecutionRecord(
            action_execution_id="action-execution-readiness-snapshot-001",
            action_request_id=action_request_id,
            approval_decision_id=approval_decision_id,
            delegation_id=delegation_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            execution_run_id="execution-run-readiness-snapshot-001",
            idempotency_key="idempotency-readiness-snapshot-001",
            target_scope={"asset_id": "asset-readiness-snapshot-001"},
            approved_payload={"action_type": "notify_identity_owner"},
            payload_hash="payload-hash-readiness-snapshot-001",
            delegated_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            expires_at=None,
            provenance={"source": "fixture"},
            lifecycle_state="succeeded",
        )
        reconciliation = ReconciliationRecord(
            reconciliation_id="reconciliation-readiness-snapshot-001",
            subject_linkage={"action_request_ids": [action_request_id]},
            alert_id=None,
            finding_id="finding-readiness-snapshot-001",
            analytic_signal_id=None,
            execution_run_id=action_execution.execution_run_id,
            linked_execution_run_ids=(action_execution.execution_run_id,),
            correlation_key=f"{action_request_id}:automation_substrate:n8n:001",
            first_seen_at=datetime(2026, 4, 16, 8, 1, tzinfo=timezone.utc),
            last_seen_at=datetime(2026, 4, 16, 8, 2, tzinfo=timezone.utc),
            ingest_disposition="matched",
            mismatch_summary="",
            compared_at=datetime(2026, 4, 16, 8, 3, tzinfo=timezone.utc),
            lifecycle_state="matched",
        )

        store.save(action_execution)
        store.save(reconciliation)

        statement_count_before = len(backend.statements)
        readiness_records = store.inspect_readiness_review_path_records(
            action_request_ids=(action_request_id,),
            approval_decision_ids=(approval_decision_id,),
            delegation_ids=(delegation_id,),
        )

        self.assertEqual(readiness_records.action_executions, (action_execution,))
        self.assertEqual(readiness_records.reconciliations, (reconciliation,))
        self.assertEqual(
            backend.statements[statement_count_before][0],
            "SET TRANSACTION ISOLATION LEVEL REPEATABLE READ",
        )

    def test_readiness_review_path_queries_map_tuple_rows_before_cursor_close(
        self,
    ) -> None:
        store, _ = make_store(_TupleRowClosingBackend())
        action_request_id = "action-request-readiness-tuple-001"
        approval_decision_id = "approval-readiness-tuple-001"
        delegation_id = "delegation-readiness-tuple-001"
        action_execution = ActionExecutionRecord(
            action_execution_id="action-execution-readiness-tuple-001",
            action_request_id=action_request_id,
            approval_decision_id=approval_decision_id,
            delegation_id=delegation_id,
            execution_surface_type="automation_substrate",
            execution_surface_id="n8n",
            execution_run_id="execution-run-readiness-tuple-001",
            idempotency_key="idempotency-readiness-tuple-001",
            target_scope={"asset_id": "asset-readiness-tuple-001"},
            approved_payload={"action_type": "notify_identity_owner"},
            payload_hash="payload-hash-readiness-tuple-001",
            delegated_at=datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc),
            expires_at=None,
            provenance={"source": "fixture"},
            lifecycle_state="succeeded",
        )
        reconciliations = (
            ReconciliationRecord(
                reconciliation_id="reconciliation-readiness-tuple-001",
                subject_linkage={"action_request_ids": [action_request_id]},
                alert_id=None,
                finding_id="finding-readiness-tuple-001",
                analytic_signal_id=None,
                execution_run_id=action_execution.execution_run_id,
                linked_execution_run_ids=(action_execution.execution_run_id,),
                correlation_key=f"{action_request_id}:automation_substrate:n8n:001",
                first_seen_at=datetime(2026, 4, 16, 8, 1, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 16, 8, 2, tzinfo=timezone.utc),
                ingest_disposition="matched",
                mismatch_summary="",
                compared_at=datetime(2026, 4, 16, 8, 7, tzinfo=timezone.utc),
                lifecycle_state="matched",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-readiness-tuple-002",
                subject_linkage={"approval_decision_ids": [approval_decision_id]},
                alert_id=None,
                finding_id="finding-readiness-tuple-001",
                analytic_signal_id=None,
                execution_run_id=action_execution.execution_run_id,
                linked_execution_run_ids=(action_execution.execution_run_id,),
                correlation_key=f"{action_request_id}:automation_substrate:n8n:002",
                first_seen_at=datetime(2026, 4, 16, 8, 1, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 16, 8, 3, tzinfo=timezone.utc),
                ingest_disposition="matched",
                mismatch_summary="",
                compared_at=datetime(2026, 4, 16, 8, 6, tzinfo=timezone.utc),
                lifecycle_state="matched",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-readiness-tuple-003",
                subject_linkage={
                    "action_execution_ids": [action_execution.action_execution_id]
                },
                alert_id=None,
                finding_id="finding-readiness-tuple-001",
                analytic_signal_id=None,
                execution_run_id=action_execution.execution_run_id,
                linked_execution_run_ids=(action_execution.execution_run_id,),
                correlation_key=f"{action_request_id}:automation_substrate:n8n:003",
                first_seen_at=datetime(2026, 4, 16, 8, 1, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 16, 8, 4, tzinfo=timezone.utc),
                ingest_disposition="matched",
                mismatch_summary="",
                compared_at=datetime(2026, 4, 16, 8, 5, tzinfo=timezone.utc),
                lifecycle_state="matched",
            ),
            ReconciliationRecord(
                reconciliation_id="reconciliation-readiness-tuple-004",
                subject_linkage={"delegation_ids": [delegation_id]},
                alert_id=None,
                finding_id="finding-readiness-tuple-001",
                analytic_signal_id=None,
                execution_run_id=action_execution.execution_run_id,
                linked_execution_run_ids=(action_execution.execution_run_id,),
                correlation_key=f"{action_request_id}:automation_substrate:n8n:004",
                first_seen_at=datetime(2026, 4, 16, 8, 1, tzinfo=timezone.utc),
                last_seen_at=datetime(2026, 4, 16, 8, 5, tzinfo=timezone.utc),
                ingest_disposition="matched",
                mismatch_summary="",
                compared_at=datetime(2026, 4, 16, 8, 4, tzinfo=timezone.utc),
                lifecycle_state="matched",
            ),
        )

        store.save(action_execution)
        for reconciliation in reconciliations:
            store.save(reconciliation)

        readiness_records = store.inspect_readiness_review_path_records(
            action_request_ids=(action_request_id,),
            approval_decision_ids=(approval_decision_id,),
            delegation_ids=(delegation_id,),
        )

        self.assertEqual(readiness_records.action_executions, (action_execution,))
        self.assertEqual(
            tuple(
                reconciliation.reconciliation_id
                for reconciliation in readiness_records.reconciliations
            ),
            (
                "reconciliation-readiness-tuple-001",
                "reconciliation-readiness-tuple-002",
                "reconciliation-readiness-tuple-003",
                "reconciliation-readiness-tuple-004",
            ),
        )

    def test_readiness_aggregates_treat_canceled_action_requests_as_terminal(
        self,
    ) -> None:
        store, _ = make_store()
        requested_at = datetime(2026, 4, 16, 8, 0, tzinfo=timezone.utc)
        action_request = ActionRequestRecord(
            action_request_id="action-request-readiness-canceled-001",
            approval_decision_id="approval-readiness-canceled-001",
            case_id="case-readiness-canceled-001",
            alert_id="alert-readiness-canceled-001",
            finding_id="finding-readiness-canceled-001",
            idempotency_key="idempotency-readiness-canceled-001",
            target_scope={"record_family": "recommendation"},
            payload_hash="payload-hash-readiness-canceled-001",
            requested_at=requested_at,
            expires_at=requested_at + timedelta(hours=4),
            lifecycle_state="canceled",
            requester_identity="analyst-001",
            requested_payload={"action_type": "notify_identity_owner"},
        )

        store.save(action_request)

        aggregates = store.inspect_readiness_aggregates()

        self.assertEqual(aggregates.action_request_total, 1)
        self.assertEqual(aggregates.active_action_request_ids, ())
        self.assertEqual(
            aggregates.terminal_review_outcome_action_request_ids,
            (action_request.action_request_id,),
        )

    def test_store_rejects_schema_invalid_records_before_persistence(self) -> None:
        store, _ = make_store()
        timestamp = datetime(2026, 4, 5, 12, 0, tzinfo=timezone.utc)

        invalid_cases = (
            (
                "invalid alert lifecycle",
                AlertRecord(
                    alert_id="alert-invalid",
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    case_id=None,
                    lifecycle_state="invalid",
                ),
                AlertRecord,
                "alert-invalid",
            ),
            (
                "empty case evidence linkage",
                CaseRecord(
                    case_id="case-invalid",
                    alert_id="alert-001",
                    finding_id=None,
                    evidence_ids=(),
                    lifecycle_state="open",
                ),
                CaseRecord,
                "case-invalid",
            ),
            (
                "reconciliation timestamps out of order",
                ReconciliationRecord(
                    reconciliation_id="reconciliation-invalid",
                    subject_linkage={"action_request_ids": ["action-request-001"]},
                    alert_id=None,
                    finding_id="finding-001",
                    analytic_signal_id=None,
                    execution_run_id=None,
                    linked_execution_run_ids=(),
                    correlation_key="action-request-001:automation_substrate:n8n:idempotency-001",
                    first_seen_at=datetime(2026, 4, 5, 12, 5, tzinfo=timezone.utc),
                    last_seen_at=timestamp,
                    ingest_disposition="matched",
                    mismatch_summary="invalid ordering",
                    compared_at=timestamp,
                    lifecycle_state="matched",
                ),
                ReconciliationRecord,
                "reconciliation-invalid",
            ),
            (
                "blank analytic signal linkage",
                AnalyticSignalRecord(
                    analytic_signal_id="signal-invalid",
                    substrate_detection_record_id="   ",
                    finding_id="",
                    alert_ids=(),
                    case_ids=(),
                    correlation_key="claim:host-001:privilege-escalation",
                    first_seen_at=timestamp,
                    last_seen_at=timestamp,
                    lifecycle_state="active",
                ),
                AnalyticSignalRecord,
                "signal-invalid",
            ),
            (
                "invalid reconciliation ingest disposition",
                ReconciliationRecord(
                    reconciliation_id="reconciliation-invalid-disposition",
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
                ),
                ReconciliationRecord,
                "reconciliation-invalid-disposition",
            ),
            (
                "blank action execution linkage",
                ActionExecutionRecord(
                    action_execution_id="action-execution-invalid-linkage",
                    action_request_id="action-request-001",
                    approval_decision_id="approval-001",
                    delegation_id="delegation-001",
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    execution_run_id="   ",
                    idempotency_key="idempotency-001",
                    target_scope={"asset_id": "asset-001"},
                    approved_payload={"action_type": "notify_identity_owner"},
                    payload_hash="payload-hash-001",
                    delegated_at=timestamp,
                    expires_at=None,
                    provenance={"delegation_issuer": "control-plane-service"},
                    lifecycle_state="queued",
                ),
                ActionExecutionRecord,
                "action-execution-invalid-linkage",
            ),
            (
                "action execution expires before delegation",
                ActionExecutionRecord(
                    action_execution_id="action-execution-invalid-expiry",
                    action_request_id="action-request-001",
                    approval_decision_id="approval-001",
                    delegation_id="delegation-001",
                    execution_surface_type="automation_substrate",
                    execution_surface_id="shuffle",
                    execution_run_id="shuffle-run-delegation-001",
                    idempotency_key="idempotency-001",
                    target_scope={"asset_id": "asset-001"},
                    approved_payload={"action_type": "notify_identity_owner"},
                    payload_hash="payload-hash-001",
                    delegated_at=timestamp,
                    expires_at=datetime(2026, 4, 5, 11, 59, tzinfo=timezone.utc),
                    provenance={"delegation_issuer": "control-plane-service"},
                    lifecycle_state="queued",
                ),
                ActionExecutionRecord,
                "action-execution-invalid-expiry",
            ),
        )

        for label, record, record_type, record_id in invalid_cases:
            with self.subTest(label=label):
                with self.assertRaises(ValueError):
                    store.save(record)
                self.assertIsNone(store.get(record_type, record_id))
                self.assertEqual(store.list(record_type), ())

    def test_store_rejects_unsupported_record_family_with_type_error(self) -> None:
        store, _ = make_store()

        with self.assertRaisesRegex(
            TypeError,
            "Unsupported control-plane record type: UnsupportedRecord",
        ):
            store.save(
                UnsupportedRecord(
                    unsupported_id="unsupported-001",
                    lifecycle_state="new",
                )
            )

    def test_store_persists_records_across_store_instances_sharing_postgres_backend(
        self,
    ) -> None:
        backend = FakePostgresBackend()
        first_store, _ = make_store(backend)
        second_store, _ = make_store(backend)
        record = AlertRecord(
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            case_id=None,
            lifecycle_state="new",
        )

        first_store.save(record)

        self.assertEqual(second_store.get(AlertRecord, "alert-001"), record)

    def test_store_transaction_rolls_back_changes_when_error_is_raised(self) -> None:
        store, _ = make_store()
        record = AlertRecord(
            alert_id="alert-001",
            finding_id="finding-001",
            analytic_signal_id="signal-001",
            case_id=None,
            lifecycle_state="new",
        )

        with self.assertRaisesRegex(RuntimeError, "rollback transaction"):
            with store.transaction():
                store.save(record)
                self.assertEqual(store.get(AlertRecord, "alert-001"), record)
                raise RuntimeError("rollback transaction")

        self.assertIsNone(store.get(AlertRecord, "alert-001"))
        self.assertEqual(store.list(AlertRecord), ())

    def test_store_normalizes_external_ticket_reference_fields_before_persistence(
        self,
    ) -> None:
        store, _ = make_store()

        persisted = store.save(
            AlertRecord(
                alert_id="alert-ticket-link-001",
                finding_id="finding-ticket-link-001",
                analytic_signal_id="signal-ticket-link-001",
                case_id=None,
                lifecycle_state="new",
                coordination_reference_id=" coord-ref-001 ",
                coordination_target_type=" zammad ",
                coordination_target_id=" ZM-4242 ",
                ticket_reference_url=" https://tickets.example.test/#ticket/4242 ",
            )
        )
        reloaded = store.get(AlertRecord, persisted.alert_id)

        self.assertEqual(persisted.coordination_reference_id, "coord-ref-001")
        self.assertEqual(persisted.coordination_target_type, "zammad")
        self.assertEqual(persisted.coordination_target_id, "ZM-4242")
        self.assertEqual(
            persisted.ticket_reference_url,
            "https://tickets.example.test/#ticket/4242",
        )
        self.assertEqual(reloaded, persisted)

    def test_store_allows_uppercase_https_ticket_reference_scheme(self) -> None:
        store, _ = make_store()

        persisted = store.save(
            AlertRecord(
                alert_id="alert-ticket-link-uppercase-001",
                finding_id="finding-ticket-link-uppercase-001",
                analytic_signal_id="signal-ticket-link-uppercase-001",
                case_id=None,
                lifecycle_state="new",
                coordination_reference_id="coord-ref-uppercase-001",
                coordination_target_type="zammad",
                coordination_target_id="ZM-5150",
                ticket_reference_url="HTTPS://tickets.example.test/#ticket/5150",
            )
        )

        self.assertEqual(
            persisted.ticket_reference_url,
            "HTTPS://tickets.example.test/#ticket/5150",
        )

    def test_store_rejects_ticket_reference_url_with_embedded_spaces(self) -> None:
        store, _ = make_store()

        with self.assertRaisesRegex(
            ValueError,
            "ticket_reference_url to be an https URL with a network location",
        ):
            store.save(
                AlertRecord(
                    alert_id="alert-ticket-link-space-001",
                    finding_id="finding-ticket-link-space-001",
                    analytic_signal_id="signal-ticket-link-space-001",
                    case_id=None,
                    lifecycle_state="new",
                    coordination_reference_id="coord-ref-space-001",
                    coordination_target_type="zammad",
                    coordination_target_id="ZM-5151",
                    ticket_reference_url="https://tickets.example.test/ticket 5151",
                )
            )

    def test_store_rejects_nested_isolation_level_requests(self) -> None:
        store, _ = make_store()

        with store.transaction():
            with self.assertRaisesRegex(
                ValueError,
                "Cannot set isolation_level inside an active transaction",
            ):
                with store.transaction(isolation_level="SERIALIZABLE"):
                    pass

    @staticmethod
    def _extract_transition_state_set(
        sql_text: str,
        family: str,
        state_field: str,
    ) -> frozenset[str]:
        match = re.search(
            rf"\(subject_record_family = '{re.escape(family)}' and {state_field} in \((.*?)\)\)",
            sql_text,
            re.DOTALL,
        )
        if match is None:
            raise AssertionError(
                f"missing {state_field} compatibility clause for transition family {family!r}"
            )
        return frozenset(re.findall(r"'([^']+)'", match.group(1)))


if __name__ == "__main__":
    unittest.main()
