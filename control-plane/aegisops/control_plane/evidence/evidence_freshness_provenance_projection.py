from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import re
from types import MappingProxyType
from typing import Mapping

from .bounded_enrichment_adapter import (
    BoundedEnrichmentEvidencePack,
    _BOUNDED_ENRICHMENT_SOURCE_ID,
    _scan_for_authority_claim,
    _scan_for_endpoint_command_language,
)
from .evidence_source_registry import PHASE63_EVIDENCE_SOURCE_REGISTRY


_ALLOWED_CONSUMERS = frozenset({"case_workbench", "ai_grounding"})
_NO_WORKFLOW_AUTHORITY = "none"
_SUBORDINATE_AUTHORITY_POSTURE = "subordinate_evidence_context_only"
_REQUIRED_CUSTODY_FIELDS = (
    "reviewed_file_hash",
    "enrichment_request_id",
    "collection_timestamp",
    "response_digest",
    "aegisops_evidence_record_id",
)
_REQUIRED_PROVENANCE_FIELDS = (
    "request_binding",
    "case_binding",
    "target_binding",
    "source_id",
    "enrichment_request_id",
    "collection_timestamp",
    "response_digest",
    "custody_reference",
    "authority_posture",
)
_REQUIRED_CONFIDENCE_FIELDS = (
    "posture",
    "freshness",
    "ambiguity_badge",
    "source_native_score_authority",
)
_ALLOWED_CUSTODY_FIELDS = frozenset(_REQUIRED_CUSTODY_FIELDS)
_ALLOWED_PROVENANCE_FIELDS = frozenset(_REQUIRED_PROVENANCE_FIELDS)
_ALLOWED_CONFIDENCE_FIELDS = frozenset(_REQUIRED_CONFIDENCE_FIELDS)
_ALLOWED_PACK_STATUSES = frozenset({"available", "degraded", "unavailable"})
_ALLOWED_SOURCE_STATUSES = frozenset({"enabled", "degraded", "disabled"})
_PROJECTION_DEGRADED_REASONS = frozenset({"source_stale"})
_PROJECTION_UNAVAILABLE_REASONS = frozenset(
    {
        "source_denied",
        "source_unavailable",
    }
)
_DURATION_PATTERN = re.compile(
    r"PT"
    r"(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+)S)?"
)


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    return MappingProxyType({str(key): item for key, item in value.items()})


def _mapping_has_non_empty_fields(
    value: Mapping[str, object],
    required_fields: tuple[str, ...],
) -> bool:
    return all(
        isinstance(value.get(field_name), str) and bool(str(value[field_name]).strip())
        for field_name in required_fields
    )


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(f"{field_name} must be timezone-aware") from exc
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be timezone-aware")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


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


def _mapping_string(value: Mapping[str, object], field_name: str) -> str:
    return _require_non_empty_string(value.get(field_name), field_name)


def _validate_projection_metadata_map(
    value: Mapping[str, object],
    allowed_fields: frozenset[str],
    authority_scanned_fields: frozenset[str],
) -> None:
    if frozenset(value) != allowed_fields:
        raise ValueError("unexpected_projection_metadata")
    if any(
        _scan_for_authority_claim(item) or _scan_for_endpoint_command_language(item)
        for field_name, item in value.items()
        if field_name in authority_scanned_fields
    ):
        raise ValueError("projection metadata cannot claim workflow authority")


@dataclass(frozen=True)
class EvidenceFreshnessProvenanceProjectionInput:
    evidence_pack: BoundedEnrichmentEvidencePack
    consumer: str
    expected_source_id: str
    expected_case_id: str
    requested_workflow_authority: str = _NO_WORKFLOW_AUTHORITY
    projected_at: datetime | None = None


@dataclass(frozen=True)
class EvidenceFreshnessProvenanceProjection:
    evidence_request_id: str
    case_id: str
    source_id: str
    consumer: str
    status: str
    freshness_state: str
    custody_state: str
    confidence_state: str
    provenance_state: str
    conflict_state: str
    source_state: str
    uncertainty_label: str
    degraded_reasons: tuple[str, ...] = ()
    unavailable_reasons: tuple[str, ...] = ()
    authority_posture: str = _SUBORDINATE_AUTHORITY_POSTURE
    authoritative_workflow_truth: bool = False
    workflow_authority: str = _NO_WORKFLOW_AUTHORITY
    custody: Mapping[str, object] = MappingProxyType({})
    provenance: Mapping[str, object] = MappingProxyType({})
    confidence: Mapping[str, object] = MappingProxyType({})

    def __post_init__(self) -> None:
        object.__setattr__(self, "custody", _freeze_mapping(self.custody))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "confidence", _freeze_mapping(self.confidence))

    def as_dict(self) -> dict[str, object]:
        return {
            "evidence_request_id": self.evidence_request_id,
            "case_id": self.case_id,
            "source_id": self.source_id,
            "consumer": self.consumer,
            "status": self.status,
            "freshness_state": self.freshness_state,
            "custody_state": self.custody_state,
            "confidence_state": self.confidence_state,
            "provenance_state": self.provenance_state,
            "conflict_state": self.conflict_state,
            "source_state": self.source_state,
            "uncertainty_label": self.uncertainty_label,
            "degraded_reasons": self.degraded_reasons,
            "unavailable_reasons": self.unavailable_reasons,
            "authority_posture": self.authority_posture,
            "authoritative_workflow_truth": self.authoritative_workflow_truth,
            "workflow_authority": self.workflow_authority,
            "custody": dict(self.custody),
            "provenance": dict(self.provenance),
            "confidence": dict(self.confidence),
        }


def _validate_projection_input(
    projection_input: EvidenceFreshnessProvenanceProjectionInput,
) -> BoundedEnrichmentEvidencePack:
    consumer = _require_non_empty_string(projection_input.consumer, "consumer")
    if consumer not in _ALLOWED_CONSUMERS:
        raise ValueError("projection consumer must be case_workbench or ai_grounding")
    requested_authority = _require_non_empty_string(
        projection_input.requested_workflow_authority,
        "requested_workflow_authority",
    )
    if requested_authority != _NO_WORKFLOW_AUTHORITY:
        raise ValueError("projection cannot drive workflow authority")

    pack = projection_input.evidence_pack
    expected_source_id = _require_non_empty_string(
        projection_input.expected_source_id,
        "expected_source_id",
    )
    expected_case_id = _require_non_empty_string(
        projection_input.expected_case_id,
        "expected_case_id",
    )
    if pack.source_id != expected_source_id:
        raise ValueError("source_mismatch")
    if expected_source_id != _BOUNDED_ENRICHMENT_SOURCE_ID:
        raise ValueError("unsupported_projection_source")
    if pack.case_id != expected_case_id:
        raise ValueError("case_mismatch")
    if (
        pack.authority_posture != _SUBORDINATE_AUTHORITY_POSTURE
        or pack.workflow_authority != _NO_WORKFLOW_AUTHORITY
    ):
        raise ValueError("projection cannot drive workflow authority")
    return pack


def _source_registry_entry(source_id: str):
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY.get(source_id)
    if registry_entry is None:
        raise ValueError("unsupported_source_id")
    if registry_entry.status not in _ALLOWED_SOURCE_STATUSES:
        raise ValueError("unexpected_source_status")
    return registry_entry


def _validate_projection_fields(pack: BoundedEnrichmentEvidencePack) -> None:
    if pack.status not in _ALLOWED_PACK_STATUSES:
        raise ValueError("unexpected_projection_status")
    registry_entry = _source_registry_entry(pack.source_id)
    allowed_degraded_reasons = (
        frozenset(registry_entry.degraded_states) | _PROJECTION_DEGRADED_REASONS
    )
    allowed_unavailable_reasons = (
        frozenset(registry_entry.disabled_states) | _PROJECTION_UNAVAILABLE_REASONS
    )
    if any(reason not in allowed_degraded_reasons for reason in pack.degraded_reasons):
        raise ValueError("unexpected_projection_reason")
    if any(reason not in allowed_unavailable_reasons for reason in pack.unavailable_reasons):
        raise ValueError("unexpected_projection_reason")
    if not _mapping_has_non_empty_fields(pack.custody, _REQUIRED_CUSTODY_FIELDS):
        raise ValueError("missing_projection_custody")
    if not _mapping_has_non_empty_fields(pack.provenance, _REQUIRED_PROVENANCE_FIELDS):
        raise ValueError("missing_projection_provenance")
    if not _mapping_has_non_empty_fields(pack.confidence, _REQUIRED_CONFIDENCE_FIELDS):
        if not pack.confidence or "ambiguity_badge" in pack.confidence:
            raise ValueError("missing_projection_confidence")
        raise ValueError("missing_projection_uncertainty")
    _validate_projection_metadata_map(
        pack.custody,
        _ALLOWED_CUSTODY_FIELDS,
        _ALLOWED_CUSTODY_FIELDS,
    )
    _validate_projection_metadata_map(
        pack.provenance,
        _ALLOWED_PROVENANCE_FIELDS,
        frozenset({"custody_reference"}),
    )
    _validate_projection_metadata_map(
        pack.confidence,
        _ALLOWED_CONFIDENCE_FIELDS,
        frozenset({"ambiguity_badge"}),
    )
    if pack.provenance["authority_posture"] != _SUBORDINATE_AUTHORITY_POSTURE:
        raise ValueError("projection cannot drive workflow authority")
    if pack.confidence["source_native_score_authority"] != _NO_WORKFLOW_AUTHORITY:
        raise ValueError("projection cannot drive workflow authority")
    if pack.confidence["posture"] != registry_entry.confidence_posture:
        raise ValueError("confidence_posture_mismatch")


def _validate_custody_bindings(
    pack: BoundedEnrichmentEvidencePack,
    looked_up_at: datetime,
) -> None:
    if _mapping_string(pack.custody, "reviewed_file_hash") != pack.file_hash:
        raise ValueError("custody_binding_mismatch")
    collection_timestamp = _require_aware_datetime(
        _mapping_string(pack.custody, "collection_timestamp"),
        "custody.collection_timestamp",
    )
    if collection_timestamp != looked_up_at:
        raise ValueError("custody_binding_mismatch")


def _validate_provenance_bindings(
    pack: BoundedEnrichmentEvidencePack,
    looked_up_at: datetime,
) -> None:
    expected_values = {
        "request_binding": pack.evidence_request_id,
        "case_binding": pack.case_id,
        "target_binding": pack.file_hash,
        "source_id": pack.source_id,
        "enrichment_request_id": _mapping_string(
            pack.custody,
            "enrichment_request_id",
        ),
        "response_digest": _mapping_string(pack.custody, "response_digest"),
    }
    for field_name, expected_value in expected_values.items():
        if _mapping_string(pack.provenance, field_name) != expected_value:
            raise ValueError("provenance_binding_mismatch")

    collection_timestamp = _require_aware_datetime(
        _mapping_string(pack.provenance, "collection_timestamp"),
        "provenance.collection_timestamp",
    )
    if collection_timestamp != looked_up_at:
        raise ValueError("provenance_binding_mismatch")


def _projection_freshness(
    pack: BoundedEnrichmentEvidencePack,
    projected_at: datetime,
) -> tuple[str, datetime]:
    looked_up_at = _require_aware_datetime(pack.looked_up_at, "looked_up_at")
    registry_entry = _source_registry_entry(pack.source_id)
    freshness_window = _parse_duration_seconds(registry_entry.freshness_window)
    age_seconds = (projected_at - looked_up_at).total_seconds()
    freshness = "stale" if age_seconds < 0 or age_seconds > freshness_window else "fresh"
    return freshness, looked_up_at


def _append_unique(reasons: list[str], reason: str) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _projected_degraded_reasons(
    pack: BoundedEnrichmentEvidencePack,
    freshness: str,
) -> tuple[str, ...]:
    reasons = list(pack.degraded_reasons)
    if freshness == "stale":
        _append_unique(reasons, "stale_reputation")
    registry_entry = _source_registry_entry(pack.source_id)
    if registry_entry.status == "degraded":
        _append_unique(reasons, "source_stale")
    return tuple(reasons)


def _projected_unavailable_reasons(
    pack: BoundedEnrichmentEvidencePack,
) -> tuple[str, ...]:
    reasons = list(pack.unavailable_reasons)
    registry_entry = _source_registry_entry(pack.source_id)
    if registry_entry.status == "disabled":
        _append_unique(reasons, "source_denied")
    return tuple(reasons)


def _projected_status(
    pack: BoundedEnrichmentEvidencePack,
    degraded_reasons: tuple[str, ...],
    unavailable_reasons: tuple[str, ...],
) -> str:
    if pack.status == "unavailable" or unavailable_reasons:
        return "unavailable"
    if degraded_reasons:
        return "degraded"
    return pack.status


def _projected_confidence(
    pack: BoundedEnrichmentEvidencePack,
    freshness: str,
) -> Mapping[str, object]:
    confidence = dict(pack.confidence)
    confidence["freshness"] = freshness
    return MappingProxyType(confidence)


def _uncertainty_label(
    pack: BoundedEnrichmentEvidencePack,
    freshness: str,
    degraded_reasons: tuple[str, ...],
    unavailable_reasons: tuple[str, ...],
    status: str,
) -> str:
    if (
        "source_unavailable" in unavailable_reasons
        or "source_denied" in unavailable_reasons
        or pack.status == "unavailable"
    ):
        return "source_unavailable"
    if status == "unavailable":
        return "source_unavailable"
    if "conflicting_enrichment" in degraded_reasons:
        return "unresolved_conflict"
    if (
        freshness == "stale"
        or "stale_reputation" in degraded_reasons
        or "source_stale" in degraded_reasons
    ):
        return "stale_review_required"
    return "related_entity_not_authoritative"


def _source_state(
    status: str,
    degraded_reasons: tuple[str, ...],
    unavailable_reasons: tuple[str, ...],
) -> str:
    if status == "unavailable" or unavailable_reasons:
        return "unavailable"
    if "source_stale" in degraded_reasons:
        return "degraded"
    return "available"


def project_evidence_freshness_provenance(
    projection_input: EvidenceFreshnessProvenanceProjectionInput,
) -> EvidenceFreshnessProvenanceProjection:
    pack = _validate_projection_input(projection_input)
    _validate_projection_fields(pack)
    projected_at = _require_aware_datetime(
        projection_input.projected_at or datetime.now(timezone.utc),
        "projected_at",
    )
    freshness, looked_up_at = _projection_freshness(pack, projected_at)
    _validate_custody_bindings(pack, looked_up_at)
    _validate_provenance_bindings(pack, looked_up_at)
    degraded_reasons = _projected_degraded_reasons(pack, freshness)
    unavailable_reasons = _projected_unavailable_reasons(pack)
    status = _projected_status(pack, degraded_reasons, unavailable_reasons)
    confidence = _projected_confidence(pack, freshness)

    conflict_state = (
        "conflicting"
        if "conflicting_enrichment" in degraded_reasons
        else "none"
    )
    source_state = _source_state(status, degraded_reasons, unavailable_reasons)

    return EvidenceFreshnessProvenanceProjection(
        evidence_request_id=pack.evidence_request_id,
        case_id=pack.case_id,
        source_id=pack.source_id,
        consumer=projection_input.consumer,
        status=status,
        freshness_state=freshness,
        custody_state="complete",
        confidence_state="present",
        provenance_state="bound",
        conflict_state=conflict_state,
        source_state=source_state,
        uncertainty_label=_uncertainty_label(
            pack,
            freshness,
            degraded_reasons,
            unavailable_reasons,
            status,
        ),
        degraded_reasons=degraded_reasons,
        unavailable_reasons=unavailable_reasons,
        custody=pack.custody,
        provenance=pack.provenance,
        confidence=confidence,
    )
