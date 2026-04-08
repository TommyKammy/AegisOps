from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from urllib.parse import quote

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
    reviewed_correlation_fields: tuple[str, ...] = (
        "location",
        "data.srcip",
        "data.srcuser",
        "data.integration",
        "data.event_type",
        "data.audit_action",
        "data.actor.id",
        "data.actor.name",
        "data.actor.login",
        "data.target.id",
        "data.target.name",
        "data.target.login",
        "data.organization.name",
        "data.repository.full_name",
        "data.privilege.change_type",
        "data.privilege.scope",
    )

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
        reviewed_correlation_context = self._build_reviewed_correlation_context(
            native_alert
        )
        source_provenance = {
            "accountable_source_identity": accountable_source_identity,
            "agent": dict(agent or {}),
            "manager": dict(manager or {}),
            "decoder_name": _optional_string(
                (_optional_mapping(native_alert.get("decoder")) or {}).get("name")
            ),
            "location": _optional_string(native_alert.get("location")),
        }
        reviewed_source_profile = self._build_reviewed_source_profile(
            native_alert=native_alert,
            source_provenance=source_provenance,
            native_rule={
                "id": rule_id,
                "level": rule_level,
                "description": rule_description,
            },
        )
        correlation_key = self._build_correlation_key(
            rule_id,
            accountable_source_identity,
            reviewed_correlation_context,
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
            "source_provenance": source_provenance,
            "reviewed_correlation_context": dict(reviewed_correlation_context),
        }
        if reviewed_source_profile is not None:
            metadata["reviewed_source_profile"] = reviewed_source_profile

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
        reviewed_source_profile = _optional_mapping(
            record.metadata.get("reviewed_source_profile")
        )
        reviewed_correlation_context = _optional_mapping(
            record.metadata.get("reviewed_correlation_context")
        )
        accountable_source_identity = _require_non_empty_string(
            _require_mapping(
                record.metadata.get("source_provenance"),
                "source_provenance",
            ).get("accountable_source_identity"),
            "source_provenance.accountable_source_identity",
        )
        reviewed_context = reviewed_source_profile or reviewed_correlation_context or {}
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
            reviewed_context=dict(reviewed_context),
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

    def _build_reviewed_correlation_context(
        self,
        alert: Mapping[str, object],
    ) -> tuple[tuple[str, str], ...]:
        context: list[tuple[str, str]] = []
        for field_path in self.reviewed_correlation_fields:
            value = self._extract_reviewed_correlation_value(alert, field_path)
            if value is not None:
                context.append((field_path, value))
        return tuple(context)

    def _build_correlation_key(
        self,
        rule_id: str,
        accountable_source_identity: str,
        reviewed_correlation_context: tuple[tuple[str, str], ...],
    ) -> str:
        correlation_key = (
            f"wazuh:rule:{rule_id}:source:{accountable_source_identity}"
        )
        for field_path, value in reviewed_correlation_context:
            correlation_key += f":{field_path}={quote(value, safe='')}"
        return correlation_key

    def _build_reviewed_source_profile(
        self,
        *,
        native_alert: Mapping[str, object],
        source_provenance: Mapping[str, object],
        native_rule: Mapping[str, object],
    ) -> dict[str, object] | None:
        data = _optional_mapping(native_alert.get("data"))
        if data is None:
            return None

        actor = self._build_identity_entity(_optional_mapping(data.get("actor")))
        target = self._build_identity_entity(_optional_mapping(data.get("target")))
        organization = self._build_organization_entity(
            _optional_mapping(data.get("organization"))
        )
        repository = self._build_repository_entity(
            _optional_mapping(data.get("repository"))
        )
        privilege = self._build_privilege_entity(
            _optional_mapping(data.get("privilege"))
        )
        audit_action = _optional_string(data.get("audit_action"))
        source_family = _optional_string(data.get("source_family"))
        if source_family != "github_audit":
            return None

        has_github_context = any(
            value is not None
            for value in (
                actor,
                target,
                organization,
                repository,
                privilege,
                audit_action,
                source_family,
            )
        )
        if not has_github_context:
            return None

        profile: dict[str, object] = {
            "source": {
                "source_system": self.substrate_key,
                "source_family": source_family or "github_audit",
                "accountable_source_identity": _require_non_empty_string(
                    source_provenance.get("accountable_source_identity"),
                    "source_provenance.accountable_source_identity",
                ),
                "delivery_path": _optional_string(native_alert.get("location"))
                or _optional_string(source_provenance.get("location"))
                or "github_audit",
            },
            "provenance": {
                "rule_id": _require_non_empty_string(
                    native_rule.get("id"),
                    "native_rule.id",
                ),
                "rule_level": native_rule.get("level"),
                "rule_description": _require_non_empty_string(
                    native_rule.get("description"),
                    "native_rule.description",
                ),
                "decoder_name": _optional_string(source_provenance.get("decoder_name")),
                "location": _optional_string(source_provenance.get("location")),
                "audit_action": audit_action,
                "request_id": _optional_string(data.get("request_id")),
            },
        }
        if actor is not None or target is not None:
            identity_profile: dict[str, object] = {}
            if actor is not None:
                identity_profile["actor"] = actor
            if target is not None:
                identity_profile["target"] = target
            profile["identity"] = identity_profile
        if organization is not None or repository is not None:
            asset_profile: dict[str, object] = {}
            if organization is not None:
                asset_profile["organization"] = organization
            if repository is not None:
                asset_profile["repository"] = repository
            profile["asset"] = asset_profile
        if privilege is not None:
            profile["privilege"] = privilege
        return profile

    @staticmethod
    def _build_identity_entity(
        entity: Mapping[str, object] | None,
    ) -> dict[str, object] | None:
        if entity is None:
            return None
        profile: dict[str, object] = {}
        entity_type = _optional_string(entity.get("type"))
        if entity_type is not None:
            profile["identity_type"] = entity_type
        entity_id = _optional_string(entity.get("id"))
        if entity_id is not None:
            profile["identity_id"] = entity_id
        display_name = _optional_string(entity.get("name")) or _optional_string(
            entity.get("login")
        )
        if display_name is not None:
            profile["display_name"] = display_name
        if not profile:
            return None
        return profile

    @staticmethod
    def _build_organization_entity(
        entity: Mapping[str, object] | None,
    ) -> dict[str, object] | None:
        if entity is None:
            return None
        profile: dict[str, object] = {}
        organization_id = _optional_string(entity.get("id"))
        if organization_id is not None:
            profile["organization_id"] = organization_id
        organization_name = _optional_string(entity.get("name"))
        if organization_name is not None:
            profile["organization_name"] = organization_name
        if not profile:
            return None
        return profile

    @staticmethod
    def _build_repository_entity(
        entity: Mapping[str, object] | None,
    ) -> dict[str, object] | None:
        if entity is None:
            return None
        profile: dict[str, object] = {}
        repository_id = _optional_string(entity.get("id"))
        if repository_id is not None:
            profile["repository_id"] = repository_id
        repository_name = _optional_string(entity.get("name"))
        if repository_name is not None:
            profile["repository_name"] = repository_name
        repository_full_name = _optional_string(entity.get("full_name"))
        if repository_full_name is not None:
            profile["repository_full_name"] = repository_full_name
        if not profile:
            return None
        return profile

    @staticmethod
    def _build_privilege_entity(
        entity: Mapping[str, object] | None,
    ) -> dict[str, object] | None:
        if entity is None:
            return None
        profile: dict[str, object] = {}
        for field_name in ("change_type", "scope", "permission", "role"):
            value = _optional_string(entity.get(field_name))
            if value is not None:
                profile[field_name] = value
        if not profile:
            return None
        return profile

    @staticmethod
    def _extract_reviewed_correlation_value(
        alert: Mapping[str, object],
        field_path: str,
    ) -> str | None:
        current: object = alert
        for segment in field_path.split("."):
            if not isinstance(current, Mapping):
                return None
            current = current.get(segment)
        return _optional_string(current)
