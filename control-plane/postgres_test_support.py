from __future__ import annotations

import copy
import json
import re

from aegisops_control_plane.adapters.postgres import PostgresControlPlaneStore


_INSERT_RE = re.compile(
    r"insert into aegisops_control\.(?P<table>\w+) "
    r"\((?P<columns>[^)]+)\) values \((?P<placeholders>[^)]+)\) "
    r"on conflict \((?P<identifier>\w+)\) do update set (?P<assignments>.+)",
    re.IGNORECASE,
)
_INSERT_ONLY_RE = re.compile(
    r"insert into aegisops_control\.(?P<table>\w+) "
    r"\((?P<columns>[^)]+)\) values \((?P<placeholders>[^)]+)\)",
    re.IGNORECASE,
)
_SELECT_ONE_RE = re.compile(
    r"select (?P<columns>.+) from aegisops_control\.(?P<table>\w+) "
    r"where (?P<identifier>\w+) = %s",
    re.IGNORECASE,
)
_SELECT_ALL_RE = re.compile(
    r"select (?P<columns>.+) from aegisops_control\.(?P<table>\w+) "
    r"order by (?P<identifier>\w+)",
    re.IGNORECASE,
)
_SELECT_GROUP_COUNT_RE = re.compile(
    r"select (?P<field>\w+) as group_value, count\(\*\) as record_count "
    r"from aegisops_control\.(?P<table>\w+) "
    r"group by (?P=field) order by (?P=field)",
    re.IGNORECASE,
)
_SELECT_IDS_BY_STATES_RE = re.compile(
    r"select (?P<identifier>\w+) from aegisops_control\.(?P<table>\w+) "
    r"where lifecycle_state in \((?P<placeholders>.+)\) "
    r"order by (?P=identifier)",
    re.IGNORECASE,
)
_SELECT_LATEST_RECONCILIATION_RE = re.compile(
    r"select (?P<columns>.+) from aegisops_control\.reconciliation_records "
    r"order by compared_at desc, reconciliation_id desc limit 1",
    re.IGNORECASE,
)
_COUNT_ACTION_REQUESTS_BY_TYPE_RE = re.compile(
    r"select count\(\*\) as record_count "
    r"from aegisops_control\.action_request_records "
    r"where requested_payload ->> 'action_type' = %s"
    r"(?: and lifecycle_state = %s)?",
    re.IGNORECASE,
)
_COUNT_MATCHED_EXECUTION_RUNS_BY_TYPE_RE = re.compile(
    r"select count\(distinct reconciliation\.execution_run_id\) as record_count "
    r"from aegisops_control\.reconciliation_records as reconciliation "
    r"join aegisops_control\.action_execution_records as execution "
    r"on execution\.execution_run_id = reconciliation\.execution_run_id "
    r"join aegisops_control\.action_request_records as action_request "
    r"on action_request\.action_request_id = execution\.action_request_id "
    r"where action_request\.requested_payload ->> 'action_type' = %s "
    r"and reconciliation\.lifecycle_state = 'matched' "
    r"and reconciliation\.execution_run_id is not null",
    re.IGNORECASE,
)


class FakePostgresBackend:
    def __init__(self) -> None:
        self.tables: dict[str, dict[str, dict[str, object]]] = {}
        self.statements: list[tuple[str, tuple[object, ...] | None]] = []

    def connect(self, dsn: str) -> "FakePostgresConnection":
        return FakePostgresConnection(self, dsn)


class FakePostgresConnection:
    def __init__(self, backend: FakePostgresBackend, dsn: str) -> None:
        self.backend = backend
        self.dsn = dsn
        self.tables = copy.deepcopy(backend.tables)
        self.dirty = False

    def cursor(self) -> "FakePostgresCursor":
        return FakePostgresCursor(self.backend, self.tables, self)

    def commit(self) -> None:
        if self.dirty:
            self.backend.tables = copy.deepcopy(self.tables)

    def rollback(self) -> None:
        self.tables = copy.deepcopy(self.backend.tables)
        return None

    def close(self) -> None:
        return None


class FakePostgresCursor:
    def __init__(
        self,
        backend: FakePostgresBackend,
        tables: dict[str, dict[str, dict[str, object]]],
        connection: FakePostgresConnection,
    ) -> None:
        self.backend = backend
        self.tables = tables
        self.connection = connection
        self.description: tuple[tuple[str], ...] | None = None
        self._rows: list[dict[str, object]] = []

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        normalized = " ".join(query.strip().split())
        self.backend.statements.append((normalized, params))

        if normalized.upper().startswith("SET TRANSACTION ISOLATION LEVEL "):
            self.description = None
            self._rows = []
            return

        insert_match = _INSERT_RE.fullmatch(normalized)
        if insert_match is not None:
            self._execute_insert(insert_match.group("table"), insert_match.group("columns"), params)
            return
        insert_only_match = _INSERT_ONLY_RE.fullmatch(normalized)
        if insert_only_match is not None:
            self._execute_insert_only(
                insert_only_match.group("table"),
                insert_only_match.group("columns"),
                params,
            )
            return

        select_one_match = _SELECT_ONE_RE.fullmatch(normalized)
        if select_one_match is not None:
            self._execute_select_one(
                select_one_match.group("table"),
                select_one_match.group("columns"),
                params,
            )
            return

        select_all_match = _SELECT_ALL_RE.fullmatch(normalized)
        if select_all_match is not None:
            self._execute_select_all(
                select_all_match.group("table"),
                select_all_match.group("columns"),
            )
            return

        select_group_count_match = _SELECT_GROUP_COUNT_RE.fullmatch(normalized)
        if select_group_count_match is not None:
            self._execute_select_group_count(
                select_group_count_match.group("table"),
                select_group_count_match.group("field"),
            )
            return

        select_ids_by_states_match = _SELECT_IDS_BY_STATES_RE.fullmatch(normalized)
        if select_ids_by_states_match is not None:
            self._execute_select_ids_by_states(
                select_ids_by_states_match.group("table"),
                select_ids_by_states_match.group("identifier"),
                params,
            )
            return

        select_latest_reconciliation_match = _SELECT_LATEST_RECONCILIATION_RE.fullmatch(
            normalized
        )
        if select_latest_reconciliation_match is not None:
            self._execute_select_latest_reconciliation(
                select_latest_reconciliation_match.group("columns")
            )
            return

        count_action_requests_match = _COUNT_ACTION_REQUESTS_BY_TYPE_RE.fullmatch(
            normalized
        )
        if count_action_requests_match is not None:
            self._execute_count_action_requests_by_type(params)
            return

        count_matched_execution_runs_match = (
            _COUNT_MATCHED_EXECUTION_RUNS_BY_TYPE_RE.fullmatch(normalized)
        )
        if count_matched_execution_runs_match is not None:
            self._execute_count_matched_execution_runs_by_type(params)
            return

        raise AssertionError(f"Unsupported fake PostgreSQL query: {normalized}")

    def _execute_insert(
        self,
        table: str,
        columns: str,
        params: tuple[object, ...] | None,
    ) -> None:
        column_names = [column.strip() for column in columns.split(",")]
        row = dict(zip(column_names, params or ()))
        identifier_field = column_names[0]
        identifier_value = row[identifier_field]
        table_rows = self.tables.setdefault(table, {})
        table_rows[str(identifier_value)] = row
        self.connection.dirty = True
        self.description = None
        self._rows = []

    def _execute_insert_only(
        self,
        table: str,
        columns: str,
        params: tuple[object, ...] | None,
    ) -> None:
        column_names = [column.strip() for column in columns.split(",")]
        row = dict(zip(column_names, params or ()))
        identifier_field = column_names[0]
        identifier_value = str(row[identifier_field])
        table_rows = self.tables.setdefault(table, {})
        if identifier_value in table_rows:
            raise ValueError(
                f"duplicate key value violates unique constraint {table}.{identifier_field}"
            )
        table_rows[identifier_value] = row
        self.connection.dirty = True
        self.description = None
        self._rows = []

    def _execute_select_one(
        self,
        table: str,
        columns: str,
        params: tuple[object, ...] | None,
    ) -> None:
        column_names = [column.strip() for column in columns.split(",")]
        identifier_value = str((params or ("",))[0])
        row = self.tables.get(table, {}).get(identifier_value)
        self.description = tuple((name,) for name in column_names)
        self._rows = [self._project_row(row, column_names)] if row is not None else []

    def _execute_select_all(
        self,
        table: str,
        columns: str,
    ) -> None:
        column_names = [column.strip() for column in columns.split(",")]
        rows = self.tables.get(table, {})
        self.description = tuple((name,) for name in column_names)
        self._rows = [
            self._project_row(rows[record_id], column_names)
            for record_id in sorted(rows)
        ]

    def _execute_select_group_count(self, table: str, field_name: str) -> None:
        grouped_counts: dict[object, int] = {}
        for row in self.tables.get(table, {}).values():
            grouped_counts[row[field_name]] = grouped_counts.get(row[field_name], 0) + 1
        self.description = (("group_value",), ("record_count",))
        self._rows = [
            {"group_value": group_value, "record_count": grouped_counts[group_value]}
            for group_value in sorted(grouped_counts, key=lambda value: str(value))
        ]

    def _execute_select_ids_by_states(
        self,
        table: str,
        identifier_field: str,
        params: tuple[object, ...] | None,
    ) -> None:
        lifecycle_states = {str(value) for value in (params or ())}
        rows = self.tables.get(table, {})
        self.description = ((identifier_field,),)
        self._rows = [
            {identifier_field: rows[record_id][identifier_field]}
            for record_id in sorted(rows)
            if str(rows[record_id]["lifecycle_state"]) in lifecycle_states
        ]

    def _execute_select_latest_reconciliation(self, columns: str) -> None:
        column_names = [column.strip() for column in columns.split(",")]
        rows = list(self.tables.get("reconciliation_records", {}).values())
        rows.sort(
            key=lambda row: (row["compared_at"], row["reconciliation_id"]),
            reverse=True,
        )
        self.description = tuple((name,) for name in column_names)
        if not rows:
            self._rows = []
            return
        self._rows = [self._project_row(rows[0], column_names)]

    def _execute_count_action_requests_by_type(
        self,
        params: tuple[object, ...] | None,
    ) -> None:
        action_type = str((params or ("",))[0])
        lifecycle_state = str(params[1]) if params and len(params) > 1 else None
        count = 0
        for row in self.tables.get("action_request_records", {}).values():
            payload = row.get("requested_payload") or {}
            if isinstance(payload, str):
                payload = json.loads(payload)
            if payload.get("action_type") != action_type:
                continue
            if lifecycle_state is not None and row.get("lifecycle_state") != lifecycle_state:
                continue
            count += 1
        self.description = (("record_count",),)
        self._rows = [{"record_count": count}]

    def _execute_count_matched_execution_runs_by_type(
        self,
        params: tuple[object, ...] | None,
    ) -> None:
        action_type = str((params or ("",))[0])
        request_ids = {
            row["action_request_id"]
            for row in self.tables.get("action_request_records", {}).values()
            if (
                json.loads(row["requested_payload"])
                if isinstance(row.get("requested_payload"), str)
                else (row.get("requested_payload") or {})
            ).get("action_type")
            == action_type
        }
        execution_run_ids = {
            row["execution_run_id"]
            for row in self.tables.get("action_execution_records", {}).values()
            if row.get("action_request_id") in request_ids
            and row.get("execution_run_id") is not None
        }
        matched_execution_run_ids = {
            row["execution_run_id"]
            for row in self.tables.get("reconciliation_records", {}).values()
            if row.get("lifecycle_state") == "matched"
            and row.get("execution_run_id") in execution_run_ids
        }
        self.description = (("record_count",),)
        self._rows = [{"record_count": len(matched_execution_run_ids)}]

    @staticmethod
    def _project_row(
        row: dict[str, object] | None,
        column_names: list[str],
    ) -> dict[str, object]:
        if row is None:
            return {}
        return {column_name: row[column_name] for column_name in column_names}

    def fetchone(self) -> dict[str, object] | None:
        if not self._rows:
            return None
        return self._rows[0]

    def fetchall(self) -> list[dict[str, object]]:
        return list(self._rows)

    def close(self) -> None:
        return None


def make_store(
    backend: FakePostgresBackend | None = None,
) -> tuple[PostgresControlPlaneStore, FakePostgresBackend]:
    backend = backend or FakePostgresBackend()
    return (
        PostgresControlPlaneStore(
            "postgresql://control-plane.local/aegisops",
            connection_factory=backend.connect,
        ),
        backend,
    )
