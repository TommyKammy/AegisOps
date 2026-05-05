from __future__ import annotations

# ruff: noqa: E402,F401

import ast
from collections.abc import Mapping
import copy
from datetime import datetime, timedelta, timezone
import importlib
import pathlib
import sys

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
if str(TESTS_ROOT) not in sys.path:
    sys.path.insert(0, str(TESTS_ROOT))

import _service_persistence_support as support
from _service_persistence_support import (
    AegisOpsControlPlaneService,
    ActionRequestRecord,
    AITraceRecord,
    RuntimeConfig,
    ServicePersistenceTestBase,
)
from aegisops.control_plane.models import ControlPlaneRecord

for name, value in vars(support).items():
    if not (name.startswith("__") and name.endswith("__")):
        globals()[name] = value

_PHASE21_LEGACY_MISSING_AUTHORITATIVE_FAMILIES = (
    "observation",
    "lead",
    "recommendation",
    "lifecycle_transition",
    "hunt",
    "hunt_run",
    "ai_trace",
)


class IsolationLevelFallbackProbeStore:
    def __init__(self, inner: object, nested_isolation_error: str) -> None:
        self.inner = inner
        self.nested_isolation_error = nested_isolation_error
        self.transaction_isolation_levels: tuple[str | None, ...] = ()

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def transaction(self, *, isolation_level: str | None = None):
        self.transaction_isolation_levels = (
            *self.transaction_isolation_levels,
            isolation_level,
        )
        if isolation_level == "REPEATABLE READ":
            raise ValueError(self.nested_isolation_error)
        return self.inner.transaction(isolation_level=isolation_level)

    def __getattr__(self, name: str) -> object:
        return getattr(self.inner, name)


class MalformedReadinessFieldStore:
    def __init__(self, inner: object) -> None:
        self.inner = inner
        self.malformed_action_request_fields: dict[str, dict[str, object]] = {}
        self.malformed_latest_ai_trace_fields: dict[str, object] = {}

    @property
    def dsn(self) -> str:
        return self.inner.dsn

    @property
    def persistence_mode(self) -> str:
        return self.inner.persistence_mode

    def transaction(self, *, isolation_level: str | None = None):
        return self.inner.transaction(isolation_level=isolation_level)

    def get(self, record_type: object, record_id: str) -> object | None:
        record = self.inner.get(record_type, record_id)
        if (
            record_type is ActionRequestRecord
            and record is not None
            and record_id in self.malformed_action_request_fields
        ):
            record = copy.copy(record)
            for field_name, value in self.malformed_action_request_fields[
                record_id
            ].items():
                object.__setattr__(record, field_name, value)
        return record

    def list(self, record_type: object) -> tuple[object, ...]:
        records = self.inner.list(record_type)
        if record_type is not ActionRequestRecord:
            return records
        return tuple(self.get(record_type, record.record_id) for record in records)

    def latest_ai_trace_record(self) -> object | None:
        record = self.inner.latest_ai_trace_record()
        if record is None or not self.malformed_latest_ai_trace_fields:
            return record
        record = copy.copy(record)
        for field_name, value in self.malformed_latest_ai_trace_fields.items():
            object.__setattr__(record, field_name, value)
        return record

    def __getattr__(self, name: str) -> object:
        return getattr(self.inner, name)


__all__ = tuple(
    name
    for name in globals()
    if not (name.startswith("__") and name.endswith("__"))
    and name not in {"pathlib", "sys", "support"}
)
