from __future__ import annotations

from contextlib import AbstractContextManager
from datetime import datetime
from typing import Callable, Protocol, Type, TypeVar

from .models import (
    ControlPlaneRecord,
    LifecycleTransitionRecord,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


class _PersistenceStore(Protocol):
    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        ...

    def save(self, record: RecordT) -> RecordT:
        ...

    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> AbstractContextManager[None]:
        ...


class _LifecycleTransitionHelper(Protocol):
    def linked_alert_case_lifecycle_lock_subject(
        self,
        record: ControlPlaneRecord,
    ) -> tuple[str, str] | None:
        ...

    def lock_lifecycle_transition_subject(
        self,
        record_family: str,
        record_id: str,
    ) -> None:
        ...

    def build_lifecycle_transition_records(
        self,
        record: ControlPlaneRecord,
        *,
        existing_record: ControlPlaneRecord | None,
        transitioned_at: datetime | None = None,
    ) -> tuple[LifecycleTransitionRecord, ...]:
        ...


class PersistenceLifecycleService:
    def __init__(
        self,
        *,
        store: _PersistenceStore,
        lifecycle_transition_helper: _LifecycleTransitionHelper,
        require_aware_datetime: Callable[[datetime, str], datetime],
    ) -> None:
        self._store = store
        self._lifecycle_transition_helper = lifecycle_transition_helper
        self._require_aware_datetime = require_aware_datetime

    def persist_record(
        self,
        record: RecordT,
        *,
        transitioned_at: datetime | None = None,
    ) -> RecordT:
        if isinstance(record, LifecycleTransitionRecord):
            raise ValueError(
                "persist_record does not accept direct lifecycle transition records"
            )
        if transitioned_at is not None:
            transitioned_at = self._require_aware_datetime(
                transitioned_at,
                "transitioned_at",
            )
        with self._store.transaction():
            lineage_lock_subject = (
                self._lifecycle_transition_helper.linked_alert_case_lifecycle_lock_subject(
                    record
                )
            )
            if lineage_lock_subject is not None:
                self._lifecycle_transition_helper.lock_lifecycle_transition_subject(
                    *lineage_lock_subject
                )
            self._lifecycle_transition_helper.lock_lifecycle_transition_subject(
                record.record_family,
                record.record_id,
            )
            existing_record = self._store.get(type(record), record.record_id)
            persisted_record = self._store.save(record)
            transition_records = (
                self._lifecycle_transition_helper.build_lifecycle_transition_records(
                    persisted_record,
                    existing_record=existing_record,
                    transitioned_at=transitioned_at,
                )
            )
            for transition_record in transition_records:
                self._store.save(transition_record)
            return persisted_record


__all__ = [
    "PersistenceLifecycleService",
]
