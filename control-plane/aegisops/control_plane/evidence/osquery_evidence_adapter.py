from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import json
import re
from types import MappingProxyType
from typing import Mapping, Sequence

from .evidence_source_registry import PHASE63_EVIDENCE_SOURCE_REGISTRY
from .reviewed_evidence_requests import (
    ReviewedEvidenceRequestRecord,
    validate_phase63_reviewed_evidence_request,
)


_DURATION_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)
_ALLOWED_RESULT_KINDS = frozenset({"host_state", "process", "state_context"})
_READ_ONLY_OPERATIONS = frozenset({"collect_host_context", "collect_state_context"})
_ACTIVE_REVIEWED_REQUEST_STATES = frozenset({"reviewed", "approved", "active"})
_REQUIRED_OSQUERY_CUSTODY_FIELDS = (
    "reviewed_query_id",
    "collector_identity",
    "collection_timestamp",
    "host_binding",
    "aegisops_evidence_record_id",
)


def _freeze_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json_value(item) for key, item in value.items()}
        )
    if isinstance(value, tuple):
        return tuple(_freeze_json_value(item) for item in value)
    if isinstance(value, list):
        return tuple(_freeze_json_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    frozen = _freeze_json_value(value)
    if not isinstance(frozen, Mapping):
        raise TypeError("Expected mapping-compatible osquery evidence adapter field")
    return frozen


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _json_size_bytes(value: object) -> int:
    try:
        encoded_value = json.dumps(
            _json_ready(value),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("rows must contain JSON-serializable finite values") from exc
    return len(encoded_value)


def _validate_json_serializable(value: object, error_message: str) -> None:
    try:
        json.dumps(_json_ready(value), allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(error_message) from exc


def _parse_custody_collection_timestamp(value: object) -> datetime:
    raw_timestamp = _require_non_empty_string(
        value,
        "osquery custody collection_timestamp",
    )
    normalized_timestamp = raw_timestamp.replace("Z", "+00:00")
    try:
        parsed_timestamp = datetime.fromisoformat(normalized_timestamp)
    except ValueError as exc:
        raise ValueError(
            "osquery custody collection_timestamp must match collected_at"
        ) from exc
    return _require_aware_datetime(
        parsed_timestamp,
        "osquery custody collection_timestamp",
    )


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _normalize_rows(rows: object) -> tuple[Mapping[str, object], ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence of mappings")
    normalized_rows: list[Mapping[str, object]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise ValueError(f"rows[{index}] must be a mapping")
        normalized_rows.append(_freeze_mapping(row))
    return tuple(normalized_rows)


def _parse_duration_seconds(value: str) -> int:
    match = _DURATION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError("freshness window must be an ISO-8601 time duration")
    duration_parts = {
        name: int(match.group(name) or 0) for name in ("hours", "minutes", "seconds")
    }
    return (
        duration_parts["hours"] * 3600
        + duration_parts["minutes"] * 60
        + duration_parts["seconds"]
    )


def _mapping_has_non_empty_fields(
    value: Mapping[str, object],
    required_fields: tuple[str, ...],
) -> bool:
    return all(
        isinstance(value.get(field_name), str) and bool(str(value[field_name]).strip())
        for field_name in required_fields
    )


@dataclass(frozen=True)
class OsqueryEvidenceAdapterInput:
    request: ReviewedEvidenceRequestRecord
    host_identifier: str
    query_id: str
    query_name: str
    result_kind: str
    rows: object
    collected_at: datetime
    custody: Mapping[str, object]
    adapter_state: str = "available"
    requested_operation: str = "collect_host_context"

    def __post_init__(self) -> None:
        object.__setattr__(self, "custody", _freeze_mapping(self.custody))

    def with_updates(self, **updates: object) -> "OsqueryEvidenceAdapterInput":
        return replace(self, **updates)


@dataclass(frozen=True)
class OsqueryEvidencePack:
    evidence_request_id: str
    case_id: str
    source_id: str
    host_identifier: str
    query_id: str
    status: str
    freshness: str
    collected_at: datetime
    custody: Mapping[str, object]
    provenance: Mapping[str, object]
    content: Mapping[str, object]
    authority_posture: str = "subordinate_evidence_context_only"
    degraded_reasons: tuple[str, ...] = ()
    unavailable_reasons: tuple[str, ...] = ()
    remediation_authority: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "custody", _freeze_mapping(self.custody))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "content", _freeze_mapping(self.content))

    def as_dict(self) -> dict[str, object]:
        return {
            "evidence_request_id": self.evidence_request_id,
            "case_id": self.case_id,
            "source_id": self.source_id,
            "host_identifier": self.host_identifier,
            "query_id": self.query_id,
            "status": self.status,
            "freshness": self.freshness,
            "collected_at": self.collected_at.isoformat(),
            "custody": _json_ready(self.custody),
            "provenance": _json_ready(self.provenance),
            "content": _json_ready(self.content),
            "authority_posture": self.authority_posture,
            "degraded_reasons": self.degraded_reasons,
            "unavailable_reasons": self.unavailable_reasons,
            "remediation_authority": self.remediation_authority,
        }


@dataclass(frozen=True)
class OsqueryEvidenceAdapter:
    source_id: str = "osquery_host_state"
    max_rows: int = 500
    max_columns: int = 128
    max_column_name_bytes: int = 256
    max_cell_bytes: int = 4096

    def _validate_result_bounds(
        self,
        rows: tuple[Mapping[str, object], ...],
    ) -> None:
        if len(rows) > self.max_rows:
            raise ValueError(f"rows must contain at most {self.max_rows} rows")

        columns = tuple(sorted({key for row in rows for key in row.keys()}))
        if len(columns) > self.max_columns:
            raise ValueError(
                f"rows must contain at most {self.max_columns} distinct columns"
            )

        for row_index, row in enumerate(rows):
            for column_name, value in row.items():
                if _json_size_bytes(column_name) > self.max_column_name_bytes:
                    raise ValueError(
                        f"rows[{row_index}] column name exceeds "
                        f"max_column_name_bytes={self.max_column_name_bytes}"
                    )
                if _json_size_bytes(value) > self.max_cell_bytes:
                    raise ValueError(
                        f"rows[{row_index}][{column_name}] exceeds "
                        f"max_cell_bytes={self.max_cell_bytes}"
                    )

    def build_evidence_pack(
        self,
        adapter_input: OsqueryEvidenceAdapterInput,
        *,
        now: datetime | None = None,
    ) -> OsqueryEvidencePack:
        comparison_now = now or datetime.now(timezone.utc)
        _require_aware_datetime(comparison_now, "now")

        if adapter_input.requested_operation not in _READ_ONLY_OPERATIONS:
            raise ValueError("osquery adapter is read-only")

        request = adapter_input.request
        request_errors = validate_phase63_reviewed_evidence_request(
            request,
            now=comparison_now,
        )
        if request_errors:
            raise ValueError(
                "reviewed evidence request invalid: " + ",".join(request_errors)
            )
        if request.lifecycle_state not in _ACTIVE_REVIEWED_REQUEST_STATES:
            raise ValueError(
                "reviewed evidence request lifecycle_state must be active"
            )
        if request.source_id != self.source_id:
            raise ValueError("reviewed request source_id must be osquery_host_state")

        host_identifier = _require_non_empty_string(
            adapter_input.host_identifier,
            "host_identifier",
        )
        if host_identifier != request.target.get("host_identifier"):
            raise ValueError("host_identifier must match reviewed request target")

        custody = adapter_input.custody
        if not custody or not _mapping_has_non_empty_fields(
            custody,
            _REQUIRED_OSQUERY_CUSTODY_FIELDS,
        ):
            raise ValueError("missing_osquery_custody")
        if custody.get("host_binding") != host_identifier:
            raise ValueError("osquery custody host_binding must match request target")

        query_id = _require_non_empty_string(adapter_input.query_id, "query_id")
        if custody.get("reviewed_query_id") != query_id:
            raise ValueError("query_id must match osquery custody reviewed_query_id")
        query_name = _require_non_empty_string(adapter_input.query_name, "query_name")
        result_kind = _require_non_empty_string(
            adapter_input.result_kind,
            "result_kind",
        )
        if result_kind not in _ALLOWED_RESULT_KINDS:
            raise ValueError(
                "result_kind must be host_state, process, or state_context"
            )
        collected_at = _require_aware_datetime(
            adapter_input.collected_at,
            "collected_at",
        )
        custody_collection_timestamp = _parse_custody_collection_timestamp(
            custody.get("collection_timestamp")
        )
        if custody_collection_timestamp != collected_at:
            raise ValueError(
                "osquery custody collection_timestamp must match collected_at"
            )

        if adapter_input.adapter_state == "unavailable":
            rows = ()
        elif adapter_input.adapter_state != "available":
            raise ValueError("adapter_state must be available or unavailable")
        else:
            rows = _normalize_rows(adapter_input.rows)
            self._validate_result_bounds(rows)

        freshness_window = _parse_duration_seconds(
            PHASE63_EVIDENCE_SOURCE_REGISTRY[self.source_id].freshness_window
        )
        age_seconds = (comparison_now - collected_at).total_seconds()
        is_stale = age_seconds < 0 or age_seconds > freshness_window
        unavailable_reasons = (
            ("adapter_unavailable",)
            if adapter_input.adapter_state == "unavailable"
            else ()
        )
        degraded_reasons = ("stale_collection",) if is_stale else ()
        status = "available"
        if unavailable_reasons:
            status = "unavailable"
        elif degraded_reasons:
            status = "degraded"

        provenance = {
            "request_binding": request.evidence_request_id,
            "case_binding": request.case_id,
            "target_binding": host_identifier,
            "source_id": request.source_id,
            "reviewed_query_id": custody["reviewed_query_id"],
            "collector_identity": custody["collector_identity"],
            "collection_timestamp": collected_at.isoformat(),
            "custody_reference": request.custody["custody_reference"],
            "authority_posture": "subordinate_evidence_context_only",
        }
        content = {
            "adapter": "phase63_osquery_evidence_adapter",
            "scope": {
                "case_id": request.case_id,
                "evidence_request_id": request.evidence_request_id,
                "requested_scope": request.requested_scope,
            },
            "host": {"host_identifier": host_identifier},
            "query": {
                "query_id": query_id,
                "name": query_name,
                "result_kind": result_kind,
            },
            "result": {
                "row_count": len(rows),
                "rows": rows,
            },
            "authority_boundary": {
                "workflow_truth": "aegisops_records_only",
                "remediation_authority": "none",
            },
        }
        pack = OsqueryEvidencePack(
            evidence_request_id=request.evidence_request_id,
            case_id=request.case_id,
            source_id=request.source_id,
            host_identifier=host_identifier,
            query_id=query_id,
            status=status,
            freshness="stale" if is_stale else "fresh",
            collected_at=collected_at,
            custody=custody,
            provenance=provenance,
            content=content,
            degraded_reasons=degraded_reasons,
            unavailable_reasons=unavailable_reasons,
        )
        _validate_json_serializable(
            pack.as_dict(),
            "osquery evidence pack must contain JSON-serializable finite values",
        )
        return pack
