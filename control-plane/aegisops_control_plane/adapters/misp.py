from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Mapping, Sequence
from urllib.parse import quote


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


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


def _normalize_mapping_sequence(
    value: object,
    field_name: str,
) -> tuple[dict[str, object], ...]:
    if value is None:
        return ()
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of mappings")
    normalized: list[dict[str, object]] = []
    for index, item in enumerate(value):
        normalized.append(_normalize_mapping(item, f"{field_name}[{index}]"))
    return tuple(normalized)


def _normalize_indicator_value(object_type: str, value: object, field_name: str) -> str:
    normalized_value = _require_non_empty_string(value, field_name)
    if object_type in {"domain", "ip", "sha1", "sha256", "md5"}:
        return normalized_value.lower()
    return normalized_value


@dataclass(frozen=True)
class MispContextAttachment:
    source_record_id: str
    collector_identity: str
    acquired_at: datetime
    provenance: Mapping[str, object]
    content: Mapping[str, object]
    observation_provenance: Mapping[str, object]
    observation_content: Mapping[str, object]
    source_system: str = "misp"
    derivation_relationship: str = "misp_context_attachment"


@dataclass(frozen=True)
class MispContextAdapter:
    enabled: bool = False
    source_system: str = "misp"
    collector_identity: str = "misp-reviewed-context-adapter"
    allowed_object_types: tuple[str, ...] = (
        "domain",
        "url",
        "ip",
        "sha1",
        "sha256",
        "md5",
    )

    def build_attachment(
        self,
        *,
        case_id: str,
        alert_id: str | None,
        admitting_evidence_id: object,
        queried_object_type: object,
        queried_object_value: object,
        looked_up_at: object,
        reviewed_by: object,
        event_id: object,
        event_info: object,
        event_published_at: object | None,
        iocs: object | None = None,
        taxonomies: object | None = None,
        warninglists: object | None = None,
        galaxies: object | None = None,
        sightings: object | None = None,
        citation_url: object,
        staleness_marker: object | None = None,
        conflict_marker: object | None = None,
    ) -> MispContextAttachment:
        if not self.enabled:
            raise ValueError("MISP subordinate enrichment is disabled")

        case_id = _require_non_empty_string(case_id, "case_id")
        admitting_evidence_id = _require_non_empty_string(
            admitting_evidence_id,
            "admitting_evidence_id",
        )
        queried_object_type = _require_non_empty_string(
            queried_object_type,
            "queried_object_type",
        ).lower()
        if queried_object_type not in self.allowed_object_types:
            raise ValueError(
                f"queried_object_type must be one of {self.allowed_object_types!r}"
            )
        queried_object_value = _normalize_indicator_value(
            queried_object_type,
            queried_object_value,
            "queried_object_value",
        )
        looked_up_at = _require_aware_datetime(looked_up_at, "looked_up_at")
        reviewed_by = _require_non_empty_string(reviewed_by, "reviewed_by")
        event_id = _require_non_empty_string(event_id, "event_id")
        event_info = _require_non_empty_string(event_info, "event_info")
        citation_url = _require_non_empty_string(citation_url, "citation_url")
        staleness_marker = _normalize_mapping(staleness_marker, "staleness_marker")
        staleness_state = _require_non_empty_string(
            staleness_marker.get("state"),
            "staleness_marker.state",
        )
        _require_non_empty_string(
            staleness_marker.get("evaluated_at"),
            "staleness_marker.evaluated_at",
        )
        event_published_iso: str | None = None
        if event_published_at is not None:
            event_published_iso = _require_aware_datetime(
                event_published_at,
                "event_published_at",
            ).isoformat()

        normalized_iocs = _normalize_mapping_sequence(iocs, "iocs")
        normalized_taxonomies = _normalize_mapping_sequence(taxonomies, "taxonomies")
        normalized_warninglists = _normalize_mapping_sequence(
            warninglists,
            "warninglists",
        )
        normalized_galaxies = _normalize_mapping_sequence(galaxies, "galaxies")
        normalized_sightings = _normalize_mapping_sequence(sightings, "sightings")
        if not any(
            (
                normalized_iocs,
                normalized_taxonomies,
                normalized_warninglists,
                normalized_galaxies,
                normalized_sightings,
            )
        ):
            raise ValueError(
                "MISP attachment requires at least one IOC, taxonomy, warninglist, galaxy, or sighting entry"
            )

        normalized_conflict_marker: dict[str, object] | None = None
        if conflict_marker is not None:
            normalized_conflict_marker = _normalize_mapping(
                conflict_marker,
                "conflict_marker",
            )

        source_record_id = "misp://event/{}/object/{}/value/{}".format(
            quote(event_id, safe=""),
            quote(queried_object_type, safe=""),
            quote(queried_object_value, safe=""),
        )
        provenance = {
            "classification": "augmenting-evidence",
            "source_id": event_id,
            "timestamp": looked_up_at.isoformat(),
            "reviewed_by": reviewed_by,
            "adapter": "misp_context",
            "source_system": self.source_system,
            "queried_object_type": queried_object_type,
            "queried_object_value": queried_object_value,
            "admitting_evidence_id": admitting_evidence_id,
            "citation_url": citation_url,
            "staleness_state": staleness_state,
            "ambiguity_badge": (
                "unresolved" if normalized_conflict_marker is not None else "related-entity"
            ),
        }
        content = {
            "lookup_receipt": {
                "adapter": "misp_context",
                "service": self.source_system,
                "queried_object": {
                    "type": queried_object_type,
                    "value": queried_object_value,
                },
                "looked_up_at": looked_up_at.isoformat(),
                "admitting_case_id": case_id,
                "admitting_evidence_id": admitting_evidence_id,
            },
            "source_observation": {
                "event_id": event_id,
                "event_info": event_info,
                "event_published_at": event_published_iso,
                "iocs": normalized_iocs,
                "taxonomies": normalized_taxonomies,
                "warninglists": normalized_warninglists,
                "galaxies": normalized_galaxies,
                "sightings": normalized_sightings,
            },
            "citation_attachment": {
                "service": self.source_system,
                "url": citation_url,
                "queried_object": {
                    "type": queried_object_type,
                    "value": queried_object_value,
                },
                "lookup_timestamp": looked_up_at.isoformat(),
                "event_id": event_id,
            },
            "staleness_marker": staleness_marker,
            "scope": {
                "case_id": case_id,
                "alert_id": alert_id,
                "admitting_evidence_id": admitting_evidence_id,
            },
        }
        if normalized_conflict_marker is not None:
            content["conflict_marker"] = normalized_conflict_marker
            provenance["conflict_present"] = True

        observation_provenance = {
            "classification": "reviewed-derived",
            "source_id": event_id,
            "timestamp": looked_up_at.isoformat(),
            "reviewed_by": reviewed_by,
            "adapter": "misp_context",
            "source_system": self.source_system,
            "derived_from_source_id": event_id,
            "admitting_evidence_id": admitting_evidence_id,
            "queried_object_type": queried_object_type,
            "queried_object_value": queried_object_value,
            "ambiguity_badge": provenance["ambiguity_badge"],
        }
        observation_content = {
            "adapter": "misp_context",
            "event_id": event_id,
            "queried_object_type": queried_object_type,
            "queried_object_value": queried_object_value,
            "staleness_state": staleness_state,
            "conflict_present": normalized_conflict_marker is not None,
        }
        return MispContextAttachment(
            source_record_id=source_record_id,
            collector_identity=self.collector_identity,
            acquired_at=looked_up_at,
            provenance=provenance,
            content=content,
            observation_provenance=observation_provenance,
            observation_content=observation_content,
        )
