from __future__ import annotations

from dataclasses import fields
from datetime import datetime
from typing import Mapping, Type, TypeVar

from ..models import ControlPlaneRecord


_BACKUP_DATETIME_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("first_seen_at", "last_seen_at"),
    "evidence": ("acquired_at",),
    "observation": ("observed_at",),
    "lifecycle_transition": ("transitioned_at",),
    "approval_decision": ("decided_at", "approved_expires_at"),
    "action_request": ("requested_at", "expires_at"),
    "action_execution": ("delegated_at", "expires_at"),
    "hunt": ("opened_at",),
    "hunt_run": ("started_at", "completed_at"),
    "ai_trace": ("generated_at",),
    "reconciliation": ("first_seen_at", "last_seen_at", "compared_at"),
}
_BACKUP_TUPLE_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("alert_ids", "case_ids"),
    "case": ("evidence_ids",),
    "observation": ("supporting_evidence_ids",),
    "approval_decision": ("approver_identities",),
    "ai_trace": ("material_input_refs",),
    "reconciliation": ("linked_execution_run_ids",),
}
_BACKUP_MAPPING_FIELDS_BY_FAMILY: dict[str, tuple[str, ...]] = {
    "analytic_signal": ("reviewed_context",),
    "alert": ("reviewed_context",),
    "case": ("reviewed_context",),
    "recommendation": ("reviewed_context", "assistant_advisory_draft"),
    "lifecycle_transition": ("attribution",),
    "approval_decision": ("target_snapshot",),
    "action_request": (
        "target_scope",
        "requested_payload",
        "policy_basis",
        "policy_evaluation",
    ),
    "action_execution": ("target_scope", "approved_payload", "provenance"),
    "hunt_run": ("scope_snapshot", "output_linkage"),
    "ai_trace": ("subject_linkage", "assistant_advisory_draft"),
    "reconciliation": ("subject_linkage",),
}


RecordT = TypeVar("RecordT", bound=ControlPlaneRecord)


class BackupPayloadCodec:
    def parse_optional_backup_created_at(self, value: object) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        return parsed

    def record_from_backup_payload(
        self,
        record_type: Type[RecordT],
        payload: Mapping[str, object],
    ) -> RecordT:
        if not isinstance(payload, Mapping):
            raise ValueError(
                f"{record_type.record_family} backup entries must be JSON objects"
            )
        family = record_type.record_family
        datetime_fields = set(_BACKUP_DATETIME_FIELDS_BY_FAMILY.get(family, ()))
        tuple_fields = set(_BACKUP_TUPLE_FIELDS_BY_FAMILY.get(family, ()))
        mapping_fields = set(_BACKUP_MAPPING_FIELDS_BY_FAMILY.get(family, ()))
        kwargs: dict[str, object] = {}
        for field_info in fields(record_type):
            if field_info.name not in payload:
                raise ValueError(
                    f"{family} backup entry is missing required field {field_info.name!r}"
                )
            value = payload[field_info.name]
            if field_info.name in datetime_fields:
                value = self._parse_backup_datetime(value, field_info.name)
            elif field_info.name in tuple_fields:
                if value is None:
                    value = ()
                elif isinstance(value, list):
                    value = tuple(value)
                elif not isinstance(value, tuple):
                    raise ValueError(
                        f"{family}.{field_info.name} must be a JSON array in restore payload"
                    )
                if any(not isinstance(item, str) or not item.strip() for item in value):
                    raise ValueError(
                        f"{family}.{field_info.name} must contain only non-empty strings"
                    )
            elif field_info.name in mapping_fields:
                value = self._parse_backup_mapping(value, family, field_info.name)
            kwargs[field_info.name] = value
        return record_type(**kwargs)

    def unexpected_restore_record_family_keys(
        self,
        payload: Mapping[str, object],
        *,
        expected_families: frozenset[str],
    ) -> tuple[str, ...]:
        non_string_keys = tuple(key for key in payload if not isinstance(key, str))
        if non_string_keys:
            raise ValueError(
                "restore payload contains non-string record family keys: "
                f"{non_string_keys!r}"
            )
        return tuple(sorted(set(payload) - expected_families))

    def is_valid_restore_record_count(self, value: object) -> bool:
        return isinstance(value, int) and not isinstance(value, bool)

    def _parse_backup_datetime(
        self,
        value: object,
        field_name: str,
    ) -> datetime | None:
        if value is None:
            return None
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{field_name} must be a non-empty ISO 8601 datetime")
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a valid ISO 8601 datetime") from exc
        if parsed.tzinfo is None:
            raise ValueError(f"{field_name} must include a timezone offset")
        return parsed

    def _parse_backup_mapping(
        self,
        value: object,
        family: str,
        field_name: str,
    ) -> Mapping[str, object]:
        if not isinstance(value, Mapping):
            raise ValueError(
                f"{family}.{field_name} must be a JSON object in restore payload"
            )
        return {str(key): item for key, item in value.items()}
