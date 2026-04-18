from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _normalize_mapping(value: object, field_name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return {str(key): item for key, item in value.items()}


def _normalize_rows(rows: object) -> tuple[dict[str, object], ...]:
    if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
        raise ValueError("rows must be a sequence of mappings")
    normalized_rows: list[dict[str, object]] = []
    for index, row in enumerate(rows):
        normalized_rows.append(_normalize_mapping(row, f"rows[{index}]"))
    if not normalized_rows:
        raise ValueError("rows must contain at least one result row")
    return tuple(normalized_rows)


@dataclass(frozen=True)
class OsqueryHostContextAttachment:
    source_record_id: str
    collector_identity: str
    acquired_at: datetime
    provenance: Mapping[str, object]
    content: Mapping[str, object]
    observation_provenance: Mapping[str, object]
    observation_content: Mapping[str, object]
    source_system: str = "osquery"
    derivation_relationship: str = "osquery_host_context"


@dataclass(frozen=True)
class OsqueryHostContextAdapter:
    source_system: str = "osquery"
    collector_identity: str = "osquery-reviewed-host-context-adapter"
    allowed_result_kinds: tuple[str, ...] = (
        "host_state",
        "process",
        "local_user",
        "scheduled_query",
    )

    def build_attachment(
        self,
        *,
        case_id: str,
        alert_id: str | None,
        authoritative_host_identifier: str,
        host_identifier: object,
        query_name: object,
        query_sql: object,
        result_kind: object,
        rows: object,
        collected_at: object,
        reviewed_by: object,
        source_id: object,
        collection_path: object,
        query_context: object | None = None,
    ) -> OsqueryHostContextAttachment:
        case_id = _require_non_empty_string(case_id, "case_id")
        authoritative_host_identifier = _require_non_empty_string(
            authoritative_host_identifier,
            "authoritative_host_identifier",
        )
        host_identifier = _require_non_empty_string(host_identifier, "host_identifier")
        if host_identifier != authoritative_host_identifier:
            raise ValueError(
                "host_identifier must match the authoritative reviewed case host binding"
            )
        query_name = _require_non_empty_string(query_name, "query_name")
        query_sql = _require_non_empty_string(query_sql, "query_sql")
        result_kind = _require_non_empty_string(result_kind, "result_kind")
        if result_kind not in self.allowed_result_kinds:
            raise ValueError(
                f"result_kind must be one of {self.allowed_result_kinds!r}"
            )
        collected_at = _require_aware_datetime(collected_at, "collected_at")
        reviewed_by = _require_non_empty_string(reviewed_by, "reviewed_by")
        source_id = _require_non_empty_string(source_id, "source_id")
        collection_path = _require_non_empty_string(collection_path, "collection_path")
        normalized_rows = _normalize_rows(rows)
        normalized_query_context = (
            _normalize_mapping(query_context, "query_context")
            if query_context is not None
            else {}
        )
        columns = tuple(sorted({key for row in normalized_rows for key in row.keys()}))
        source_record_id = (
            f"osquery://host/{host_identifier}/collection/{collection_path}/source/{source_id}"
        )
        provenance = {
            "classification": "augmenting-evidence",
            "source_id": source_id,
            "timestamp": collected_at.isoformat(),
            "reviewed_by": reviewed_by,
            "adapter": "osquery_host_context",
            "source_system": self.source_system,
            "collection_path": collection_path,
            "host_identifier": host_identifier,
            "ambiguity_badge": "related-entity",
        }
        content = {
            "adapter": "osquery_host_context",
            "scope": {
                "case_id": case_id,
                "alert_id": alert_id,
            },
            "host": {
                "host_identifier": host_identifier,
            },
            "query": {
                "name": query_name,
                "sql": query_sql,
                "collection_path": collection_path,
                "context": normalized_query_context,
            },
            "result": {
                "kind": result_kind,
                "row_count": len(normalized_rows),
                "columns": columns,
                "rows": normalized_rows,
            },
        }
        observation_provenance = {
            "classification": "reviewed-derived",
            "source_id": source_id,
            "timestamp": collected_at.isoformat(),
            "reviewed_by": reviewed_by,
            "adapter": "osquery_host_context",
            "derived_from_source_id": source_id,
            "host_identifier": host_identifier,
            "ambiguity_badge": "related-entity",
        }
        observation_content = {
            "adapter": "osquery_host_context",
            "host_identifier": host_identifier,
            "query_name": query_name,
            "result_kind": result_kind,
            "row_count": len(normalized_rows),
        }
        return OsqueryHostContextAttachment(
            source_record_id=source_record_id,
            collector_identity=self.collector_identity,
            acquired_at=collected_at,
            provenance=provenance,
            content=content,
            observation_provenance=observation_provenance,
            observation_content=observation_content,
        )
