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


from aegisops.control_plane.models import ReconciliationRecord
from aegisops.control_plane.models import ActionRequestRecord
from aegisops.control_plane.models import LifecycleTransitionRecord


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
    ) -> ReconciliationRecord | None:
        return self.inner.latest_reconciliation_for_correlation_key(
            correlation_key,
            require_alert_id=require_alert_id,
        )

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        return self.inner.latest_lifecycle_transition(record_family, record_id)

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
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

    def create_action_request_if_absent(
        self,
        record: ActionRequestRecord,
    ) -> tuple[ActionRequestRecord, bool]:
        return self.inner.create_action_request_if_absent(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        records = self.inner.list(record_type)
        if self._consume_mutation_token():
            self.mutate_once()
        return records

    def latest_reconciliation_for_correlation_key(
        self,
        correlation_key: str,
        *,
        require_alert_id: bool = False,
    ) -> ReconciliationRecord | None:
        reconciliation = self.inner.latest_reconciliation_for_correlation_key(
            correlation_key,
            require_alert_id=require_alert_id,
        )
        if self._consume_mutation_token():
            self.mutate_once()
        return reconciliation

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        transition = self.inner.latest_lifecycle_transition(record_family, record_id)
        if self._consume_mutation_token():
            self.mutate_once()
        return transition

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        transitions = self.inner.list_lifecycle_transitions(record_family, record_id)
        if self._consume_mutation_token():
            self.mutate_once()
        return transitions

    def inspect_readiness_aggregates(self) -> object:
        aggregates = self.inner.inspect_readiness_aggregates()
        if self._consume_mutation_token():
            self.mutate_once()
        return aggregates

    def inspect_readiness_review_path_records(
        self,
        *,
        action_request_ids: tuple[str, ...],
        approval_decision_ids: tuple[str, ...],
        delegation_ids: tuple[str, ...] = (),
    ) -> object:
        records = self.inner.inspect_readiness_review_path_records(
            action_request_ids=action_request_ids,
            approval_decision_ids=approval_decision_ids,
            delegation_ids=delegation_ids,
        )
        if self._consume_mutation_token():
            self.mutate_once()
        return records

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
    ) -> ReconciliationRecord | None:
        return self.inner.latest_reconciliation_for_correlation_key(
            correlation_key,
            require_alert_id=require_alert_id,
        )

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        return self.inner.latest_lifecycle_transition(record_family, record_id)

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
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

    def create_action_request_if_absent(
        self,
        record: ActionRequestRecord,
    ) -> tuple[ActionRequestRecord, bool]:
        if self.record_type is ActionRequestRecord:
            raise RuntimeError(self.message)
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
    ) -> ReconciliationRecord | None:
        return self.inner.latest_reconciliation_for_correlation_key(
            correlation_key,
            require_alert_id=require_alert_id,
        )

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        return self.inner.latest_lifecycle_transition(record_family, record_id)

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
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
    latest_reconciliation_for_correlation_key_calls: int = 0
    lifecycle_transition_record_list_calls: int = 0
    latest_lifecycle_transition_calls: int = 0
    lifecycle_transition_history_calls: int = 0

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def save(self, record: object) -> object:
        return self.inner.save(record)

    def create_action_request_if_absent(
        self,
        record: ActionRequestRecord,
    ) -> tuple[ActionRequestRecord, bool]:
        return self.inner.create_action_request_if_absent(record)

    def get(self, record_type: object, record_id: str) -> object | None:
        return self.inner.get(record_type, record_id)

    def list(self, record_type: object) -> tuple[object, ...]:
        self.list_calls += 1
        if record_type is ReconciliationRecord:
            self.reconciliation_list_calls += 1
        if record_type is LifecycleTransitionRecord:
            self.lifecycle_transition_record_list_calls += 1
        return self.inner.list(record_type)

    def latest_reconciliation_for_correlation_key(
        self,
        correlation_key: str,
        *,
        require_alert_id: bool = False,
    ) -> ReconciliationRecord | None:
        self.latest_reconciliation_for_correlation_key_calls += 1
        return self.inner.latest_reconciliation_for_correlation_key(
            correlation_key,
            require_alert_id=require_alert_id,
        )

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        self.latest_lifecycle_transition_calls += 1
        return self.inner.latest_lifecycle_transition(record_family, record_id)

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        self.lifecycle_transition_history_calls += 1
        return self.inner.list_lifecycle_transitions(record_family, record_id)

    def latest_ai_trace_record(self) -> object | None:
        return self.inner.latest_ai_trace_record()

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
    ) -> ReconciliationRecord | None:
        return self.inner.latest_reconciliation_for_correlation_key(
            correlation_key,
            require_alert_id=require_alert_id,
        )

    def latest_lifecycle_transition(
        self,
        record_family: str,
        record_id: str,
    ) -> LifecycleTransitionRecord | None:
        return self.inner.latest_lifecycle_transition(record_family, record_id)

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[LifecycleTransitionRecord, ...]:
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
