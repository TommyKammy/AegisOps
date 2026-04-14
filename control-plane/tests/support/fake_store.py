from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
import pathlib
import sys
import threading
from typing import Callable, Iterator
from unittest import mock


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.models import ReconciliationRecord


@dataclass
class TransactionMutationStore:
    inner: object
    mutate_once: Callable[[object], None]
    _mutated: bool = False
    _mutate_lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
    )

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

    def _consume_mutation_token(self) -> bool:
        with self._mutate_lock:
            if self._mutated:
                return False
            self._mutated = True
            return True

    @contextmanager
    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> Iterator[None]:
        with self.inner.transaction(isolation_level=isolation_level):
            if self._consume_mutation_token():
                self.mutate_once(self.inner)
            yield


@dataclass
class ConcurrentListMutationStore:
    inner: object
    mutate_once: Callable[[], None]
    _mutated: bool = False
    _mutate_lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
    )

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def _consume_mutation_token(self) -> bool:
        with self._mutate_lock:
            if self._mutated:
                return False
            self._mutated = True
            return True

    def save(self, record: object) -> object:
        return self.inner.save(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        records = self.inner.list(record_type)
        if self._consume_mutation_token():
            self.mutate_once()
        return records

    def inspect_readiness_aggregates(self) -> object:
        aggregates = self.inner.inspect_readiness_aggregates()
        if self._consume_mutation_token():
            self.mutate_once()
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
class CommitFailingStore:
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
                "CommitFailingStore requires an explicit connection factory"
            )

        def commit_failing_connection_factory(dsn: str) -> "CommitFailingConnection":
            return CommitFailingConnection(
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
class RecordTypeSaveFailingStore:
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
class CommitFailingConnection:
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
class ListCountingStore:
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
class OutOfBandMutationStore:
    inner: object
    mutate_once: Callable[[object], None]
    _mutated: bool = False
    _mutate_lock: threading.Lock = field(
        default_factory=threading.Lock,
        init=False,
        repr=False,
    )

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

    def _consume_mutation_token(self) -> bool:
        with self._mutate_lock:
            if self._mutated:
                return False
            self._mutated = True
            return True

    @contextmanager
    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> Iterator[None]:
        if self._consume_mutation_token():
            self.mutate_once(self.inner)
        with self.inner.transaction(isolation_level=isolation_level):
            yield
