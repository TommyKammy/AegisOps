from __future__ import annotations

from contextvars import ContextVar
from contextlib import contextmanager
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
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
from ..readiness_contracts import (
    ReadinessDiagnosticsAggregates,
    ReadinessReviewPathRecords,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)
_MISSING_SORT_TIMESTAMP = datetime.min.replace(tzinfo=timezone.utc)


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


def _normalize_sort_datetime(value: datetime | None) -> datetime:
    if value is None:
        return _MISSING_SORT_TIMESTAMP
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _readiness_reconciliation_sort_key(
    record: ReconciliationRecord,
) -> tuple[datetime, datetime, datetime, str]:
    return (
        _normalize_sort_datetime(record.compared_at),
        _normalize_sort_datetime(record.last_seen_at),
        _normalize_sort_datetime(record.first_seen_at),
        record.reconciliation_id,
    )


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
    EvidenceRecord: TableConfig(
        EvidenceRecord,
        "evidence_records",
        json_fields=frozenset({"provenance", "content"}),
    ),
    ObservationRecord: TableConfig(
        ObservationRecord,
        "observation_records",
        json_fields=frozenset({"provenance", "content"}),
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


from ..record_validation import (  # noqa: E402
    _LIFECYCLE_STATES_BY_FAMILY,
    _normalize_coordination_reference_record,
    _validate_lifecycle_state,
    _validate_record,
)


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

    def lock_lifecycle_transition_subject(
        self,
        record_family: str,
        record_id: str,
    ) -> None:
        active_connection = self._active_connection.get()
        if active_connection is None:
            raise RuntimeError(
                "lifecycle transition subject locks require an active transaction"
            )

        cursor = active_connection.cursor()
        try:
            cursor.execute(
                "select pg_advisory_xact_lock(hashtext(%s), hashtext(%s))",
                (record_family, record_id),
            )
        finally:
            cursor.close()

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
        if isinstance(record, (AlertRecord, CaseRecord)):
            record = _normalize_coordination_reference_record(record)
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

    def create_action_request_if_absent(
        self,
        record: ActionRequestRecord,
    ) -> tuple[ActionRequestRecord, bool]:
        _validate_record(record)
        table = self._table_config(ActionRequestRecord)
        field_names = table.record_fields
        placeholders = ", ".join(
            self._placeholder(table, field_name) for field_name in field_names
        )
        params = tuple(
            self._serialize_field(table, field_name, getattr(record, field_name))
            for field_name in field_names
        )
        query = (
            f"insert into aegisops_control.{table.table_name} "
            f"({', '.join(field_names)}) values ({placeholders}) "
            f"on conflict (idempotency_key) do nothing "
            f"returning {', '.join(field_names)}"
        )
        existing_query = (
            f"select {', '.join(field_names)} "
            f"from aegisops_control.{table.table_name} "
            "where idempotency_key = %s"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, params)
                row = cursor.fetchone()
                created = row is not None
                if row is None:
                    cursor.execute(existing_query, (record.idempotency_key,))
                    row = cursor.fetchone()
                if row is None:
                    raise RuntimeError(
                        "action request idempotency insert returned no authoritative row"
                    )
                row_mapping = _row_to_mapping(cursor, row)
            finally:
                cursor.close()
        authoritative = self._row_to_record(ActionRequestRecord, row_mapping)
        if authoritative.payload_hash != record.payload_hash:
            raise ValueError(
                "idempotency_key already exists for a different action request payload"
            )
        return authoritative, created

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

    def latest_reconciliation_for_correlation_key(
        self,
        correlation_key: str,
        *,
        require_alert_id: bool = False,
    ) -> ReconciliationRecord | None:
        table = self._table_config(ReconciliationRecord)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            "where correlation_key = %s"
        )
        params: tuple[object, ...] = (correlation_key,)
        if require_alert_id:
            query += " and alert_id is not null"
        query += " order by compared_at desc, reconciliation_id desc limit 1"

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, params)
                row = cursor.fetchone()
                mapping = None if row is None else _row_to_mapping(cursor, row)
            finally:
                cursor.close()

        if mapping is None:
            return None
        return self._row_to_record(ReconciliationRecord, mapping)

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        table = self._table_config(LifecycleTransitionRecord)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            "where subject_record_family = %s and subject_record_id = %s "
            "order by transitioned_at desc, transition_id desc limit 1"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, (record_family, record_id))
                row = cursor.fetchone()
                mapping = None if row is None else _row_to_mapping(cursor, row)
            finally:
                cursor.close()

        if mapping is None:
            return None
        return self._row_to_record(
            LifecycleTransitionRecord,
            mapping,
        )

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        table = self._table_config(LifecycleTransitionRecord)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            "where subject_record_family = %s and subject_record_id = %s "
            "order by transitioned_at asc, transition_id asc"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, (record_family, record_id))
                rows = cursor.fetchall()
                mappings = tuple(_row_to_mapping(cursor, row) for row in rows)
            finally:
                cursor.close()

        return tuple(
            self._row_to_record(
                LifecycleTransitionRecord,
                mapping,
            )
            for mapping in mappings
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
            terminal_review_outcome_action_request_ids=self._list_identifier_values_by_lifecycle_states(
                ActionRequestRecord,
                (
                    "completed",
                    "failed",
                    "rejected",
                    "expired",
                    "canceled",
                    "superseded",
                ),
            ),
            action_execution_total=sum(action_execution_lifecycle_counts.values()),
            action_execution_lifecycle_counts=action_execution_lifecycle_counts,
            active_action_execution_ids=self._list_identifier_values_by_lifecycle_states(
                ActionExecutionRecord,
                ("dispatching", "queued", "running"),
            ),
            terminal_action_execution_ids=self._list_identifier_values_by_lifecycle_states(
                ActionExecutionRecord,
                (
                    "succeeded",
                    "failed",
                    "canceled",
                    "superseded",
                ),
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

    def inspect_readiness_review_path_records(
        self,
        *,
        action_request_ids: tuple[str, ...],
        approval_decision_ids: tuple[str, ...],
        delegation_ids: tuple[str, ...] = (),
    ) -> ReadinessReviewPathRecords:
        if self._active_connection.get() is None:
            with self.transaction(isolation_level="REPEATABLE READ"):
                return self.inspect_readiness_review_path_records(
                    action_request_ids=action_request_ids,
                    approval_decision_ids=approval_decision_ids,
                    delegation_ids=delegation_ids,
                )

        action_executions_by_id: dict[str, ActionExecutionRecord] = {}
        for action_execution in self._list_action_executions_by_action_request_ids(
            action_request_ids
        ):
            action_executions_by_id[action_execution.action_execution_id] = action_execution
        for action_execution in self._list_action_executions_by_delegation_ids(
            delegation_ids
        ):
            action_executions_by_id[action_execution.action_execution_id] = action_execution
        action_executions = tuple(action_executions_by_id.values())
        reconciliations_by_id: dict[str, ReconciliationRecord] = {}
        action_execution_ids = tuple(
            action_execution.action_execution_id for action_execution in action_executions
        )
        reconciliation_delegation_ids = tuple(
            sorted(
                {
                    *delegation_ids,
                    *(
                        action_execution.delegation_id
                        for action_execution in action_executions
                    ),
                }
            )
        )
        for linkage_key, linkage_ids in (
            ("action_request_ids", action_request_ids),
            ("approval_decision_ids", approval_decision_ids),
            ("action_execution_ids", action_execution_ids),
            ("delegation_ids", reconciliation_delegation_ids),
        ):
            for reconciliation in self._list_reconciliations_by_subject_linkage_ids(
                linkage_key=linkage_key,
                linkage_ids=linkage_ids,
            ):
                reconciliations_by_id[reconciliation.reconciliation_id] = reconciliation
        reconciliations = tuple(
            sorted(
                reconciliations_by_id.values(),
                key=_readiness_reconciliation_sort_key,
                reverse=True,
            )
        )
        return ReadinessReviewPathRecords(
            action_executions=action_executions,
            reconciliations=reconciliations,
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

    def _list_action_executions_by_action_request_ids(
        self,
        action_request_ids: tuple[str, ...],
    ) -> tuple[ActionExecutionRecord, ...]:
        if not action_request_ids:
            return ()

        table = self._table_config(ActionExecutionRecord)
        placeholders = ", ".join("%s" for _ in action_request_ids)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            f"where action_request_id in ({placeholders}) "
            "order by action_request_id asc, delegated_at desc, action_execution_id desc"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, action_request_ids)
                rows = cursor.fetchall()
                mappings = tuple(_row_to_mapping(cursor, row) for row in rows)
            finally:
                cursor.close()

        return tuple(
            self._row_to_record(ActionExecutionRecord, mapping) for mapping in mappings
        )

    def _list_action_executions_by_delegation_ids(
        self,
        delegation_ids: tuple[str, ...],
    ) -> tuple[ActionExecutionRecord, ...]:
        if not delegation_ids:
            return ()

        table = self._table_config(ActionExecutionRecord)
        placeholders = ", ".join("%s" for _ in delegation_ids)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            f"where delegation_id in ({placeholders}) "
            "order by delegated_at desc, action_execution_id desc"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, delegation_ids)
                rows = cursor.fetchall()
                mappings = tuple(_row_to_mapping(cursor, row) for row in rows)
            finally:
                cursor.close()

        return tuple(
            self._row_to_record(ActionExecutionRecord, mapping) for mapping in mappings
        )

    def _list_reconciliations_by_subject_linkage_ids(
        self,
        *,
        linkage_key: str,
        linkage_ids: tuple[str, ...],
    ) -> tuple[ReconciliationRecord, ...]:
        if not linkage_ids:
            return ()

        table = self._table_config(ReconciliationRecord)
        placeholders = ", ".join("%s" for _ in linkage_ids)
        query = (
            f"select {', '.join(table.record_fields)} "
            f"from aegisops_control.{table.table_name} "
            f"where coalesce(subject_linkage -> '{linkage_key}', '[]'::jsonb) "
            f"?| array[{placeholders}] "
            "order by compared_at desc, reconciliation_id desc"
        )

        with self._borrow_connection() as connection:
            cursor = connection.cursor()
            try:
                cursor.execute(query, linkage_ids)
                rows = cursor.fetchall()
                mappings = tuple(_row_to_mapping(cursor, row) for row in rows)
            finally:
                cursor.close()

        return tuple(
            self._row_to_record(ReconciliationRecord, mapping) for mapping in mappings
        )

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
