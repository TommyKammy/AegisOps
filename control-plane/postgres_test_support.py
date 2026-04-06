from __future__ import annotations

import copy
import re

from aegisops_control_plane.adapters.postgres import PostgresControlPlaneStore


_INSERT_RE = re.compile(
    r"insert into aegisops_control\.(?P<table>\w+) "
    r"\((?P<columns>[^)]+)\) values \((?P<placeholders>[^)]+)\) "
    r"on conflict \((?P<identifier>\w+)\) do update set (?P<assignments>.+)",
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

    def cursor(self) -> "FakePostgresCursor":
        return FakePostgresCursor(self.backend, self.tables)

    def commit(self) -> None:
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
    ) -> None:
        self.backend = backend
        self.tables = tables
        self.description: tuple[tuple[str], ...] | None = None
        self._rows: list[dict[str, object]] = []

    def execute(self, query: str, params: tuple[object, ...] | None = None) -> None:
        normalized = " ".join(query.strip().split())
        self.backend.statements.append((normalized, params))

        insert_match = _INSERT_RE.fullmatch(normalized)
        if insert_match is not None:
            self._execute_insert(insert_match.group("table"), insert_match.group("columns"), params)
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
