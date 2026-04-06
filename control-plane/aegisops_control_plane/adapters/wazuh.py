from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping

from ..models import AnalyticSignalAdmission, NativeDetectionRecord


def _require_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _optional_mapping(value: object) -> Mapping[str, object] | None:
    return value if isinstance(value, Mapping) else None


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _optional_string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item.strip())


@dataclass(frozen=True)
class WazuhAlertAdapter:
    substrate_key: str = "wazuh"

    def build_native_detection_record(
        self,
        alert: Mapping[str, object],
    ) -> NativeDetectionRecord:
        native_alert = _require_mapping(alert, "alert")
        native_record_id = _require_non_empty_string(native_alert.get("id"), "id")
        timestamp = self._parse_timestamp(
            _require_non_empty_string(native_alert.get("timestamp"), "timestamp")
        )
        rule = _require_mapping(native_alert.get("rule"), "rule")
        rule_id = _require_non_empty_string(rule.get("id"), "rule.id")
        rule_level = rule.get("level")
        if not isinstance(rule_level, int):
            raise ValueError("rule.level must be an integer")
        rule_description = _require_non_empty_string(
            rule.get("description"),
            "rule.description",
        )

        agent = _optional_mapping(native_alert.get("agent"))
        manager = _optional_mapping(native_alert.get("manager"))
        accountable_source_identity = self._resolve_accountable_source_identity(
            agent,
            manager,
        )
        correlation_key = (
            f"wazuh:rule:{rule_id}:source:{accountable_source_identity}"
        )

        metadata = {
            "raw_alert": dict(native_alert),
            "source_system": self.substrate_key,
            "native_rule": {
                "id": rule_id,
                "level": rule_level,
                "description": rule_description,
                "groups": _optional_string_tuple(rule.get("groups")),
                "mitre": dict(_optional_mapping(rule.get("mitre")) or {}),
            },
            "source_provenance": {
                "accountable_source_identity": accountable_source_identity,
                "agent": dict(agent or {}),
                "manager": dict(manager or {}),
                "decoder_name": _optional_string(
                    (_optional_mapping(native_alert.get("decoder")) or {}).get("name")
                ),
                "location": _optional_string(native_alert.get("location")),
            },
        }

        return NativeDetectionRecord(
            substrate_key=self.substrate_key,
            native_record_id=native_record_id,
            record_kind="alert",
            correlation_key=correlation_key,
            first_seen_at=timestamp,
            last_seen_at=timestamp,
            metadata=metadata,
        )

    def build_analytic_signal_admission(
        self,
        record: NativeDetectionRecord,
    ) -> AnalyticSignalAdmission:
        native_rule = _require_mapping(record.metadata.get("native_rule"), "native_rule")
        accountable_source_identity = _require_non_empty_string(
            _require_mapping(
                record.metadata.get("source_provenance"),
                "source_provenance",
            ).get("accountable_source_identity"),
            "source_provenance.accountable_source_identity",
        )
        finding_id = (
            "finding:"
            f"{self.substrate_key}:"
            f"rule:{_require_non_empty_string(native_rule.get('id'), 'native_rule.id')}:"
            f"source:{accountable_source_identity}:"
            f"alert:{record.native_record_id}"
        )
        return AnalyticSignalAdmission(
            finding_id=finding_id,
            analytic_signal_id=None,
            substrate_detection_record_id=record.native_record_id,
            correlation_key=record.correlation_key,
            first_seen_at=record.first_seen_at,
            last_seen_at=record.last_seen_at,
        )

    @staticmethod
    def _parse_timestamp(value: str) -> datetime:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return parsed

    @staticmethod
    def _resolve_accountable_source_identity(
        agent: Mapping[str, object] | None,
        manager: Mapping[str, object] | None,
    ) -> str:
        agent_id = _optional_string((agent or {}).get("id"))
        if agent_id is not None:
            return f"agent:{agent_id}"

        manager_name = _optional_string((manager or {}).get("name"))
        if manager_name is not None:
            return f"manager:{manager_name}"

        raise ValueError(
            "agent.id or manager.name must provide an accountable source identity"
        )
