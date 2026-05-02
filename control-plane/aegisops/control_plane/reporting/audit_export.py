from __future__ import annotations

from contextlib import AbstractContextManager
from dataclasses import fields
from datetime import datetime
from typing import Mapping, Protocol, Type, TypeVar

from ..models import ControlPlaneRecord, EvidenceRecord
from ..publishable_paths import (
    REDACTED_LOCAL_PATH_TOKEN,
    is_workstation_local_path,
)


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


class AuditExportStore(Protocol):
    def list(self, record_type: Type[RecordT]) -> tuple[RecordT, ...]:
        ...

    def transaction(
        self,
        *,
        isolation_level: str | None = None,
    ) -> AbstractContextManager[None]:
        ...


_AUDIT_EXPORT_SECRET_TOKEN = "<redacted-secret>"
_AUDIT_EXPORT_SECRET_KEY_FRAGMENTS = (
    "authorization",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)


def _json_ready(value: object) -> object:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _record_to_dict(record: ControlPlaneRecord) -> dict[str, object]:
    return {field.name: getattr(record, field.name) for field in fields(record)}


def _audit_export_key_is_secret(key: object) -> bool:
    normalized_key = str(key).lower().replace("-", "_")
    return any(
        fragment in normalized_key for fragment in _AUDIT_EXPORT_SECRET_KEY_FRAGMENTS
    )


def _redact_audit_export_value(value: object, *, key: object | None = None) -> object:
    if key is not None and _audit_export_key_is_secret(key):
        return _AUDIT_EXPORT_SECRET_TOKEN
    if isinstance(value, Mapping):
        return {
            str(item_key): _redact_audit_export_value(item_value, key=item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, tuple):
        return [_redact_audit_export_value(item) for item in value]
    if isinstance(value, list):
        return [_redact_audit_export_value(item) for item in value]
    if isinstance(value, str) and is_workstation_local_path(value):
        return REDACTED_LOCAL_PATH_TOKEN
    return _json_ready(value)


def _audit_export_record_payload(record: ControlPlaneRecord) -> dict[str, object]:
    payload = {
        key: _redact_audit_export_value(value, key=key)
        for key, value in _record_to_dict(record).items()
    }
    payload["authority_role"] = "authoritative_control_plane_record"
    if isinstance(record, EvidenceRecord):
        payload.pop("provenance", None)
        payload.pop("content", None)
        payload["subordinate_evidence"] = {
            "authority_role": "subordinate_evidence",
            "promotion_allowed": False,
            "source_system": record.source_system,
            "source_record_id": record.source_record_id,
            "derivation_relationship": record.derivation_relationship,
            "provenance": _redact_audit_export_value(record.provenance),
            "content": _redact_audit_export_value(record.content),
        }
    return payload


def export_audit_retention_baseline(
    *,
    store: AuditExportStore,
    record_types: tuple[Type[ControlPlaneRecord], ...],
    export_id: str,
    exported_at: datetime,
) -> dict[str, object]:
    records_by_family: dict[str, list[dict[str, object]]] = {}
    with store.transaction(isolation_level="REPEATABLE READ"):
        for record_type in record_types:
            records_by_family[record_type.record_family] = [
                _audit_export_record_payload(record)
                for record in store.list(record_type)
            ]

    return {
        "schema_version": "phase49.audit-export.v1",
        "export_id": export_id,
        "exported_at": exported_at.isoformat(),
        "source_of_truth": "aegisops_authoritative_records",
        "records": records_by_family,
        "retention_baseline": {
            "document": "docs/retention-evidence-and-replay-readiness-baseline.md",
            "bounded": True,
            "unlimited_log_retention": False,
            "compliance_certification_claim": False,
        },
        "subordinate_evidence_policy": {
            "authority_role": "subordinate_evidence",
            "promotion_allowed": False,
            "label_required": True,
        },
    }
