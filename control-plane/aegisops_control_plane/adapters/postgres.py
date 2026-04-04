from __future__ import annotations

from dataclasses import dataclass, field
from typing import Type, TypeVar

from ..models import ControlPlaneRecord


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


@dataclass
class PostgresControlPlaneStore:
    """In-process authoritative store for reviewed control-plane record families."""

    dsn: str
    _records: dict[str, dict[str, ControlPlaneRecord]] = field(
        default_factory=dict,
        init=False,
        repr=False,
    )

    def save(self, record: RecordT) -> RecordT:
        family_records = self._records.setdefault(record.record_family, {})
        family_records[record.record_id] = record
        return record

    def get(self, record_type: Type[RecordT], record_id: str) -> RecordT | None:
        family_records = self._records.get(record_type.record_family, {})
        record = family_records.get(record_id)
        if record is None:
            return None
        if not isinstance(record, record_type):
            raise TypeError(
                f"Stored {record.record_family} record did not match requested type {record_type.__name__}"
            )
        return record
