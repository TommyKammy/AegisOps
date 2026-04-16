from __future__ import annotations

from contextvars import ContextVar
from contextlib import contextmanager
from dataclasses import dataclass, field, fields
import importlib
import json
from typing import Any, Callable, Iterator, Mapping, Protocol, Type, TypeVar

from ..models import (
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


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


@dataclass(frozen=True)
class ReadinessDiagnosticsAggregates:
    alert_total: int
    alert_lifecycle_counts: dict[str, int]
    case_total: int
    open_case_ids: tuple[str, ...]
    action_request_total: int
    action_request_lifecycle_counts: dict[str, int]
    active_action_request_ids: tuple[str, ...]
    action_execution_total: int
    action_execution_lifecycle_counts: dict[str, int]
    active_action_execution_ids: tuple[str, ...]
    reconciliation_total: int
    reconciliation_lifecycle_counts: dict[str, int]
    reconciliation_ingest_disposition_counts: dict[str, int]
    unresolved_reconciliation_ids: tuple[str, ...]
    latest_reconciliation: ReconciliationRecord | None
    phase20_requested_action_requests: int
    phase20_approved_action_requests: int
    phase20_reconciled_executions: int


class CursorProtocol(Protocol):
    description: object | None

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        ...

    def fetchone(self) -> object | None:
        ...

    def fetchall(self) -> list[object]:
        ...

    def close(self) -> None:
        ...


class ConnectionProtocol(Protocol):
    def cursor(self) -> CursorProtocol:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def close(self) -> None:
        ...


ConnectionFactory = Callable[[str], ConnectionProtocol]
_ALLOWED_TRANSACTION_ISOLATION_LEVELS = frozenset(
    {"READ COMMITTED", "REPEATABLE READ", "SERIALIZABLE"}
)


@dataclass(frozen=True)
class TableConfig:
    record_type: Type[ControlPlaneRecord]
    table_name: str
    json_fields: frozenset[str] = frozenset()
    array_fields: frozenset[str] = frozenset()

    @property
    def identifier_field(self) -> str:
        return self.record_type.identifier_field

    @property
    def record_fields(self) -> tuple[str, ...]:
        return tuple(field_info.name for field_info in fields(self.record_type))


_LIFECYCLE_STATES_BY_FAMILY: dict[str, frozenset[str]] = {
    "alert": frozenset(
        {
            "new",
            "triaged",
            "investigating",
            "escalated_to_case",
            "closed",
            "reopened",
            "superseded",
        }
    ),
    "analytic_signal": frozenset({"active", "superseded", "withdrawn"}),
    "case": frozenset(
        {
            "open",
            "investigating",
            "pending_action",
            "contained_pending_validation",
            "closed",
            "reopened",
            "superseded",
        }
    ),
    "evidence": frozenset(
        {"collected", "validated", "linked", "superseded", "withdrawn"}
    ),
    "observation": frozenset(
        {"captured", "confirmed", "challenged", "superseded", "withdrawn"}
    ),
    "lead": frozenset(
        {
            "open",
            "triaged",
            "promoted_to_alert",
            "promoted_to_case",
            "closed",
            "superseded",
        }
    ),
    "lifecycle_transition": frozenset(
        {
            "new",
            "triaged",
            "investigating",
            "escalated_to_case",
            "closed",
            "reopened",
            "superseded",
            "active",
            "withdrawn",
            "open",
            "pending_action",
            "contained_pending_validation",
            "collected",
            "validated",
            "linked",
            "captured",
            "confirmed",
            "challenged",
            "promoted_to_alert",
            "promoted_to_case",
            "proposed",
            "under_review",
            "accepted",
            "rejected",
            "materialized",
            "pending",
            "approved",
            "expired",
            "canceled",
            "draft",
            "executing",
            "completed",
            "failed",
            "unresolved",
            "dispatching",
            "queued",
            "running",
            "succeeded",
            "on_hold",
            "concluded",
            "planned",
            "generated",
            "accepted_for_reference",
            "rejected_for_reference",
            "matched",
            "mismatched",
            "stale",
            "resolved",
        }
    ),
    "recommendation": frozenset(
        {
            "proposed",
            "under_review",
            "accepted",
            "rejected",
            "materialized",
            "superseded",
            "withdrawn",
        }
    ),
    "approval_decision": frozenset(
        {"pending", "approved", "rejected", "expired", "canceled", "superseded"}
    ),
    "action_request": frozenset(
        {
            "draft",
            "pending_approval",
            "approved",
            "rejected",
            "expired",
            "canceled",
            "superseded",
            "executing",
            "completed",
            "failed",
            "unresolved",
        }
    ),
    "action_execution": frozenset(
        {
            "dispatching",
            "queued",
            "running",
            "succeeded",
            "failed",
            "canceled",
            "superseded",
        }
    ),
    "hunt": frozenset(
        {"draft", "active", "on_hold", "concluded", "closed", "superseded"}
    ),
    "hunt_run": frozenset(
        {"planned", "running", "completed", "canceled", "superseded", "unresolved"}
    ),
    "ai_trace": frozenset(
        {
            "generated",
            "under_review",
            "accepted_for_reference",
            "rejected_for_reference",
            "superseded",
            "withdrawn",
        }
    ),
    "reconciliation": frozenset(
        {"pending", "matched", "mismatched", "stale", "resolved", "superseded"}
    ),
}

_RECONCILIATION_INGEST_DISPOSITIONS = frozenset(
    {
        "created",
        "updated",
        "deduplicated",
        "restated",
        "matched",
        "missing",
        "duplicate",
        "mismatch",
        "stale",
    }
)

_TABLES_BY_RECORD_TYPE: dict[Type[ControlPlaneRecord], TableConfig] = {
    AlertRecord: TableConfig(
        AlertRecord,
        "alert_records",
        json_fields=frozenset({"reviewed_context"}),
    ),
    AnalyticSignalRecord: TableConfig(
        AnalyticSignalRecord,
        "analytic_signal_records",
        json_fields=frozenset({"reviewed_context"}),
        array_fields=frozenset({"alert_ids", "case_ids"}),
    ),
    CaseRecord: TableConfig(
        CaseRecord,
        "case_records",
        json_fields=frozenset({"reviewed_context"}),
        array_fields=frozenset({"evidence_ids"}),
    ),
    EvidenceRecord: TableConfig(EvidenceRecord, "evidence_records"),
    ObservationRecord: TableConfig(
        ObservationRecord,
        "observation_records",
        array_fields=frozenset({"supporting_evidence_ids"}),
    ),
    LeadRecord: TableConfig(LeadRecord, "lead_records"),
    LifecycleTransitionRecord: TableConfig(
        LifecycleTransitionRecord,
        "lifecycle_transition_records",
        json_fields=frozenset({"attribution"}),
    ),
    RecommendationRecord: TableConfig(
        RecommendationRecord,
        "recommendation_records",
        json_fields=frozenset({"reviewed_context", "assistant_advisory_draft"}),
    ),
    ApprovalDecisionRecord: TableConfig(
        ApprovalDecisionRecord,
        "approval_decision_records",
        json_fields=frozenset({"target_snapshot"}),
        array_fields=frozenset({"approver_identities"}),
    ),
    ActionRequestRecord: TableConfig(
        ActionRequestRecord,
        "action_request_records",
        json_fields=frozenset(
            {"target_scope", "requested_payload", "policy_basis", "policy_evaluation"}
        ),
    ),
    ActionExecutionRecord: TableConfig(
        ActionExecutionRecord,
        "action_execution_records",
        json_fields=frozenset({"target_scope", "approved_payload", "provenance"}),
    ),
    HuntRecord: TableConfig(HuntRecord, "hunt_records"),
    HuntRunRecord: TableConfig(
        HuntRunRecord,
        "hunt_run_records",
        json_fields=frozenset({"scope_snapshot", "output_linkage"}),
    ),
    AITraceRecord: TableConfig(
        AITraceRecord,
        "ai_trace_records",
        json_fields=frozenset({"subject_linkage", "assistant_advisory_draft"}),
        array_fields=frozenset({"material_input_refs"}),
    ),
    ReconciliationRecord: TableConfig(
        ReconciliationRecord,
        "reconciliation_records",
        json_fields=frozenset({"subject_linkage"}),
        array_fields=frozenset({"linked_execution_run_ids"}),
    ),
}


def _validate_lifecycle_state(record: ControlPlaneRecord) -> None:
    if isinstance(record, LifecycleTransitionRecord):
        if not isinstance(record.lifecycle_state, str) or not record.lifecycle_state.strip():
            raise ValueError(
                f"lifecycle_transition record {record.record_id!r} requires non-blank lifecycle_state"
            )
        return
    allowed_states = _LIFECYCLE_STATES_BY_FAMILY.get(record.record_family)
    if allowed_states is None:
        raise TypeError(
            f"Unsupported control-plane record type: {type(record).__name__}"
        )
    if record.lifecycle_state not in allowed_states:  # type: ignore[attr-defined]
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} has invalid lifecycle_state "
            f"{record.lifecycle_state!r}; expected one of {sorted(allowed_states)!r}"  # type: ignore[attr-defined]
        )


def _require_any_linkage(
    record: ControlPlaneRecord,
    field_names: tuple[str, ...],
) -> None:
    if any(_has_linkage_value(getattr(record, field_name)) for field_name in field_names):
        return
    required_fields = ", ".join(field_names)
    raise ValueError(
        f"{record.record_family} record {record.record_id!r} requires at least one linkage field: "
        f"{required_fields}"
    )


def _has_linkage_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    return True


def _require_non_empty_tuple(
    record: ControlPlaneRecord,
    field_name: str,
) -> None:
    values = getattr(record, field_name)
    if len(values) >= 1:
        return
    raise ValueError(
        f"{record.record_family} record {record.record_id!r} requires non-empty {field_name}"
    )


def _require_non_blank_fields(
    record: ControlPlaneRecord,
    field_names: tuple[str, ...],
) -> None:
    for field_name in field_names:
        if _has_linkage_value(getattr(record, field_name)):
            continue
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} requires non-blank {field_name}"
        )


def _validate_record(record: ControlPlaneRecord) -> None:
    _validate_lifecycle_state(record)

    if isinstance(record, AnalyticSignalRecord):
        _require_any_linkage(
            record,
            ("substrate_detection_record_id", "finding_id"),
        )
        if record.first_seen_at is not None and record.last_seen_at is not None:
            if record.first_seen_at > record.last_seen_at:
                raise ValueError(
                    f"analytic_signal record {record.record_id!r} requires first_seen_at <= last_seen_at"
                )
        return
    if isinstance(record, CaseRecord):
        _require_any_linkage(record, ("finding_id", "alert_id"))
        _require_non_empty_tuple(record, "evidence_ids")
        return
    if isinstance(record, EvidenceRecord):
        _require_any_linkage(record, ("alert_id", "case_id"))
        return
    if isinstance(record, ObservationRecord):
        _require_any_linkage(record, ("hunt_id", "hunt_run_id", "alert_id", "case_id"))
        _require_non_empty_tuple(record, "supporting_evidence_ids")
        return
    if isinstance(record, LeadRecord):
        _require_any_linkage(record, ("observation_id", "finding_id", "hunt_run_id"))
        return
    if isinstance(record, RecommendationRecord):
        _require_any_linkage(record, ("lead_id", "hunt_run_id", "alert_id", "case_id"))
        return
    if isinstance(record, LifecycleTransitionRecord):
        _require_non_blank_fields(
            record,
            ("transition_id", "subject_record_family", "subject_record_id"),
        )
        return
    if isinstance(record, ApprovalDecisionRecord):
        _require_non_empty_tuple(record, "approver_identities")
        return
    if isinstance(record, ActionRequestRecord):
        _require_any_linkage(record, ("case_id", "alert_id", "finding_id"))
        return
    if isinstance(record, ActionExecutionRecord):
        _require_non_blank_fields(
            record,
            (
                "action_execution_id",
                "action_request_id",
                "approval_decision_id",
                "delegation_id",
                "execution_surface_type",
                "execution_surface_id",
                "execution_run_id",
                "idempotency_key",
                "payload_hash",
            ),
        )
        if record.expires_at is not None and record.expires_at < record.delegated_at:
            raise ValueError(
                f"action_execution record {record.record_id!r} requires expires_at >= delegated_at"
            )
        return
    if isinstance(record, ReconciliationRecord):
        _require_any_linkage(
            record,
            ("finding_id", "analytic_signal_id", "execution_run_id"),
        )
        if record.ingest_disposition not in _RECONCILIATION_INGEST_DISPOSITIONS:
            raise ValueError(
                f"reconciliation record {record.record_id!r} has invalid ingest_disposition "
                f"{record.ingest_disposition!r}; expected one of "
                f"{sorted(_RECONCILIATION_INGEST_DISPOSITIONS)!r}"
            )
        if (
            record.first_seen_at is not None
            and record.last_seen_at is not None
            and record.first_seen_at > record.last_seen_at
        ):
            raise ValueError(
                f"reconciliation record {record.record_id!r} requires first_seen_at <= last_seen_at"
            )
        return
    if isinstance(
        record,
        (AlertRecord, HuntRecord, HuntRunRecord, AITraceRecord),
    ):
        return
    raise TypeError(f"Unsupported control-plane record type: {type(record).__name__}")


def _load_default_connection_factory() -> ConnectionFactory:
    for module_name in ("psycopg", "psycopg2"):
        try:
            module = importlib.import_module(module_name)
        except ImportError:
            continue
        connector = getattr(module, "connect", None)
        if callable(connector):
            return connector
    raise RuntimeError(
        "PostgreSQL client tooling is not installed; inject a connection_factory or "
        "install psycopg/psycopg2 for the reviewed control-plane store"
    )


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _json_dump(value: object) -> str:
    return json.dumps(_json_ready(value), separators=(",", ":"), sort_keys=True)


def _row_to_mapping(cursor: CursorProtocol, row: object) -> Mapping[str, object]:
    if isinstance(row, Mapping):
        return row

    description = getattr(cursor, "description", None)
    if not description:
        raise TypeError("Cursor description is required to map PostgreSQL rows")

    column_names: list[str] = []
    for column in description:
        if isinstance(column, str):
            column_names.append(column)
        else:
            column_names.append(column[0])

    if not isinstance(row, (list, tuple)):
        raise TypeError(f"Unsupported PostgreSQL row type: {type(row).__name__}")

    return dict(zip(column_names, row))


def _deserialize_json_value(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value


@dataclass
class PostgresControlPlaneStore:
    """Reviewed PostgreSQL-backed authority store for control-plane record families."""

    dsn: str
    connection_factory: ConnectionFactory | None = None
    persistence_mode: str = field(default="postgresql", init=False)
    _active_connection: ContextVar[ConnectionProtocol | None] = field(
        default_factory=lambda: ContextVar(
            "postgres_control_plane_store_active_connection",
            default=None,
        ),
        init=False,
        repr=False,
    )

    @contextmanager
    def _connection(self) -> Any:
        connection_factory = self.connection_factory or _load_default_connection_factory()
        connection = connection_factory(self.dsn)
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    @contextmanager
    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> Iterator[None]:
        active_connection = self._active_connection.get()
        if active_connection is not None:
            if isolation_level is not None:
                raise ValueError(
                    "Cannot set isolation_level inside an active transaction"
                )
            yield
            return

        with self._connection() as connection:
            if isolation_level is not None:
                normalized_isolation_level = isolation_level.strip().upper()
                if normalized_isolation_level not in _ALLOWED_TRANSACTION_ISOLATION_LEVELS:
                    raise ValueError(
                        "Unsupported transaction isolation level "
                        f"{isolation_level!r}"
                    )
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        f"SET TRANSACTION ISOLATION LEVEL {normalized_isolation_level}"
                    )
                finally:
                    cursor.close()
            token = self._active_connection.set(connection)
            try:
                yield
            finally:
                self._active_connection.reset(token)

    @contextmanager
    def _borrow_connection(self) -> Iterator[ConnectionProtocol]:
        active_connection = self._active_connection.get()
        if active_connection is not None:
            yield active_connection
            return

        with self._connection() as connection:
            yield connection

    @staticmethod
    def _table_config(record_type: Type[ControlPlaneRecord]) -> TableConfig:
        try:
            return _TABLES_BY_RECORD_TYPE[record_type]
        except KeyError as exc:
            raise TypeError(
                f"Unsupported control-plane record type: {record_type.__name__}"
            ) from exc

    @staticmethod
    def _serialize_field(table: TableConfig, field_name: str, value: object) -> object:
        if field_name in table.json_fields:
            return _json_dump(value)
        if field_name in table.array_fields:
            return list(value) if isinstance(value, tuple) else value
        return value

    @staticmethod
    def _deserialize_field(table: TableConfig, field_name: str, value: object) -> object:
        if field_name in table.json_fields:
            return _deserialize_json_value(value)
        if field_name in table.array_fields:
            if value is None:
                return ()
            if isinstance(value, tuple):
                return value
            if isinstance(value, list):
                return tuple(value)
        return value

    @staticmethod
    def _placeholder(table: TableConfig, field_name: str) -> str:
        if field_name in table.json_fields:
            return "%s::jsonb"
        if field_name in table.array_fields:
            return "%s::text[]"
        return "%s"

    def _row_to_record(
        self,
        record_type: Type[RecordT],
        row: Mapping[str, object],
    ) -> RecordT:
        table = self._table_config(record_type)
        kwargs = {
            field_name: self._deserialize_field(table, field_name, row[field_name])
            for field_name in table.record_fields
        }
        return record_type(**kwargs)

    def save(self, record: RecordT) -> RecordT:
        _validate_record(record)
        table = self._table_config(type(record))
        field_names = table.record_fields
        placeholders = ", ".join(
            self._placeholder(table, field_name) for field_name in field_names
        )
        params = tuple(
            self._serialize_field(table, field_name, getattr(record, field_name))
            for field_name in field_names
        )
        if isinstance(record, LifecycleTransitionRecord):
            query = (
                f"insert into aegisops_control.{table.table_name} "
                f"({', '.join(field_names)}) values ({placeholders})"
            )
        else:
            assignments = ", ".join(
                f"{field_name} = excluded.{field_name}"
                for field_name in field_names
                if field_name != table.identifier_field
            )
            query = (
                f"insert into aegisops_control.{table.table_name} "
                f"({', '.join(field_names)}) values ({placeholders}) "
                f"on conflict ({table.identifier_field}) do update set {assignments}"
            )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, params)
            finally:
                cursor.close()
        return record

    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        table = self._table_config(record_type)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            f"where {table.identifier_field} = %s"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, (record_id,))
                row = cursor.fetchone()
            finally:
                cursor.close()

        if row is None:
            return None
        return self._row_to_record(record_type, _row_to_mapping(cursor, row))

    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        table = self._table_config(record_type)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            f"order by {table.identifier_field}"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
            finally:
                cursor.close()

        return tuple(
            self._row_to_record(record_type, _row_to_mapping(cursor, row))
            for row in rows
        )

    def inspect_readiness_aggregates(self) -> ReadinessDiagnosticsAggregates:
        if self._active_connection.get() is None:
            with self.transaction(isolation_level="REPEATABLE READ"):
                return self.inspect_readiness_aggregates()

        alert_lifecycle_counts = self._count_grouped_by_field(
            AlertRecord,
            "lifecycle_state",
        )
        case_lifecycle_counts = self._count_grouped_by_field(
            CaseRecord,
            "lifecycle_state",
        )
        action_request_lifecycle_counts = self._count_grouped_by_field(
            ActionRequestRecord,
            "lifecycle_state",
        )
        action_execution_lifecycle_counts = self._count_grouped_by_field(
            ActionExecutionRecord,
            "lifecycle_state",
        )
        reconciliation_lifecycle_counts = self._count_grouped_by_field(
            ReconciliationRecord,
            "lifecycle_state",
        )
        reconciliation_ingest_disposition_counts = self._count_grouped_by_field(
            ReconciliationRecord,
            "ingest_disposition",
        )
        return ReadinessDiagnosticsAggregates(
            alert_total=sum(alert_lifecycle_counts.values()),
            alert_lifecycle_counts=alert_lifecycle_counts,
            case_total=sum(case_lifecycle_counts.values()),
            open_case_ids=self._list_identifier_values_by_lifecycle_states(
                CaseRecord,
                (
                    "open",
                    "investigating",
                    "pending_action",
                    "contained_pending_validation",
                    "reopened",
                ),
            ),
            action_request_total=sum(action_request_lifecycle_counts.values()),
            action_request_lifecycle_counts=action_request_lifecycle_counts,
            active_action_request_ids=self._list_identifier_values_by_lifecycle_states(
                ActionRequestRecord,
                ("pending_approval", "approved", "executing", "unresolved"),
            ),
            action_execution_total=sum(action_execution_lifecycle_counts.values()),
            action_execution_lifecycle_counts=action_execution_lifecycle_counts,
            active_action_execution_ids=self._list_identifier_values_by_lifecycle_states(
                ActionExecutionRecord,
                ("dispatching", "queued", "running"),
            ),
            reconciliation_total=sum(reconciliation_lifecycle_counts.values()),
            reconciliation_lifecycle_counts=reconciliation_lifecycle_counts,
            reconciliation_ingest_disposition_counts=reconciliation_ingest_disposition_counts,
            unresolved_reconciliation_ids=self._list_identifier_values_by_lifecycle_states(
                ReconciliationRecord,
                ("pending", "mismatched", "stale"),
            ),
            latest_reconciliation=self._latest_reconciliation(),
            phase20_requested_action_requests=self._count_action_requests_by_action_type(
                "notify_identity_owner"
            ),
            phase20_approved_action_requests=self._count_action_requests_by_action_type(
                "notify_identity_owner",
                lifecycle_state="approved",
            ),
            phase20_reconciled_executions=self._count_distinct_matched_execution_runs_for_action_type(
                "notify_identity_owner"
            ),
        )

    def _count_grouped_by_field(
        self,
        record_type: Type[ControlPlaneRecord],
        field_name: str,
    ) -> dict[str, int]:
        table = self._table_config(record_type)
        query = (
            f"select {field_name} as group_value, count(*) as record_count "
            f"from aegisops_control.{table.table_name} "
            f"group by {field_name} order by {field_name}"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                rows = cursor.fetchall()
            finally:
                cursor.close()

        counts: dict[str, int] = {}
        for row in rows:
            mapping = _row_to_mapping(cursor, row)
            group_value = mapping.get("group_value")
            if group_value is None:
                continue
            counts[str(group_value)] = int(mapping["record_count"])
        return counts

    def _list_identifier_values_by_lifecycle_states(
        self,
        record_type: Type[ControlPlaneRecord],
        lifecycle_states: tuple[str, ...],
    ) -> tuple[str, ...]:
        if not lifecycle_states:
            return ()

        table = self._table_config(record_type)
        placeholders = ", ".join("%s" for _ in lifecycle_states)
        query = (
            f"select {table.identifier_field} "
            f"from aegisops_control.{table.table_name} "
            f"where lifecycle_state in ({placeholders}) "
            f"order by {table.identifier_field}"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, lifecycle_states)
                rows = cursor.fetchall()
            finally:
                cursor.close()

        return tuple(str(_row_to_mapping(cursor, row)[table.identifier_field]) for row in rows)

    def _latest_reconciliation(self) -> ReconciliationRecord | None:
        table = self._table_config(ReconciliationRecord)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            "order by compared_at desc, reconciliation_id desc limit 1"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query)
                row = cursor.fetchone()
            finally:
                cursor.close()

        if row is None:
            return None
        return self._row_to_record(ReconciliationRecord, _row_to_mapping(cursor, row))

    def _count_action_requests_by_action_type(
        self,
        action_type: str,
        *,
        lifecycle_state: str | None = None,
    ) -> int:
        query = (
            "select count(*) as record_count "
            "from aegisops_control.action_request_records "
            "where requested_payload ->> 'action_type' = %s"
        )
        params: tuple[object, ...] = (action_type,)
        if lifecycle_state is not None:
            query += " and lifecycle_state = %s"
            params += (lifecycle_state,)

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, params)
                row = cursor.fetchone()
            finally:
                cursor.close()

        if row is None:
            return 0
        return int(_row_to_mapping(cursor, row)["record_count"])

    def _count_distinct_matched_execution_runs_for_action_type(
        self,
        action_type: str,
    ) -> int:
        query = (
            "select count(distinct reconciliation.execution_run_id) as record_count "
            "from aegisops_control.reconciliation_records as reconciliation "
            "join aegisops_control.action_execution_records as execution "
            "on execution.execution_run_id = reconciliation.execution_run_id "
            "join aegisops_control.action_request_records as action_request "
            "on action_request.action_request_id = execution.action_request_id "
            "where action_request.requested_payload ->> 'action_type' = %s "
            "and reconciliation.lifecycle_state = 'matched' "
            "and reconciliation.execution_run_id is not null"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, (action_type,))
                row = cursor.fetchone()
            finally:
                cursor.close()

        if row is None:
            return 0
        return int(_row_to_mapping(cursor, row)["record_count"])
