from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, fields
import importlib
import json
from typing import Any, Callable, Mapping, Protocol, Type, TypeVar

from ..models import (
    AITraceRecord,
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
    ObservationRecord,
    ReconciliationRecord,
    RecommendationRecord,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


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
    AlertRecord: TableConfig(AlertRecord, "alert_records"),
    AnalyticSignalRecord: TableConfig(
        AnalyticSignalRecord,
        "analytic_signal_records",
        array_fields=frozenset({"alert_ids", "case_ids"}),
    ),
    CaseRecord: TableConfig(CaseRecord, "case_records", array_fields=frozenset({"evidence_ids"})),
    EvidenceRecord: TableConfig(EvidenceRecord, "evidence_records"),
    ObservationRecord: TableConfig(
        ObservationRecord,
        "observation_records",
        array_fields=frozenset({"supporting_evidence_ids"}),
    ),
    LeadRecord: TableConfig(LeadRecord, "lead_records"),
    RecommendationRecord: TableConfig(RecommendationRecord, "recommendation_records"),
    ApprovalDecisionRecord: TableConfig(
        ApprovalDecisionRecord,
        "approval_decision_records",
        json_fields=frozenset({"target_snapshot"}),
        array_fields=frozenset({"approver_identities"}),
    ),
    ActionRequestRecord: TableConfig(
        ActionRequestRecord,
        "action_request_records",
        json_fields=frozenset({"target_scope"}),
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
        json_fields=frozenset({"subject_linkage"}),
        array_fields=frozenset({"material_input_refs"}),
    ),
    ReconciliationRecord: TableConfig(
        ReconciliationRecord,
        "reconciliation_records",
        json_fields=frozenset({"subject_linkage"}),
        array_fields=frozenset({"linked_execution_ids"}),
    ),
}


def _validate_lifecycle_state(record: ControlPlaneRecord) -> None:
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
    if isinstance(record, ApprovalDecisionRecord):
        _require_non_empty_tuple(record, "approver_identities")
        return
    if isinstance(record, ActionRequestRecord):
        _require_any_linkage(record, ("case_id", "alert_id", "finding_id"))
        return
    if isinstance(record, ReconciliationRecord):
        _require_any_linkage(
            record,
            ("finding_id", "analytic_signal_id", "workflow_execution_id"),
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
        assignments = ", ".join(
            f"{field_name} = excluded.{field_name}"
            for field_name in field_names
            if field_name != table.identifier_field
        )
        params = tuple(
            self._serialize_field(table, field_name, getattr(record, field_name))
            for field_name in field_names
        )
        query = (
            f"insert into aegisops_control.{table.table_name} "
            f"({', '.join(field_names)}) values ({placeholders}) "
            f"on conflict ({table.identifier_field}) do update set {assignments}"
        )

        with self._connection() as connection:
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

        with self._connection() as connection:
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

        with self._connection() as connection:
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
