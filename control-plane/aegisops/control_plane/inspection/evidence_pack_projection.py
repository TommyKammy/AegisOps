from __future__ import annotations

from datetime import datetime, timezone
from typing import Mapping

from ..evidence.bounded_enrichment_adapter import BoundedEnrichmentEvidencePack
from ..evidence.evidence_freshness_provenance_projection import (
    EvidenceFreshnessProvenanceProjectionInput,
    _parse_duration_seconds,
    project_evidence_freshness_provenance,
)
from ..evidence.evidence_source_registry import PHASE63_EVIDENCE_SOURCE_REGISTRY


_EVIDENCE_PACK_PROJECTION_CONTENT_KEY = "evidence_pack_projection"
_EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE = "subordinate_evidence_context_only"
_EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES = {
    "browser_state",
    "browser_cache",
    "ui_cache",
    "cache",
}
_EVIDENCE_PACK_FORBIDDEN_READINESS_CLAIMS = {
    "release_readiness_claim",
    "rc_readiness_claim",
    "gate_readiness_claim",
}
_EVIDENCE_PACK_SUPPORTED_SOURCE_ID = "malwarebazaar_hash_reputation"
_EVIDENCE_PACK_BOUNDED_ENRICHMENT_SOURCE_SYSTEM = "phase63_bounded_enrichment_adapter"
_EVIDENCE_PACK_BOUNDED_ENRICHMENT_DERIVATION = "bounded_enrichment_projection"
_EVIDENCE_PACK_BOUNDED_ENRICHMENT_ADAPTER = "phase63_bounded_enrichment_adapter"
_EVIDENCE_PACK_ALLOWED_PROJECTION_LABELS = {
    "consumer": frozenset({"case_workbench"}),
    "status": frozenset({"available", "degraded", "unavailable"}),
    "freshness_state": frozenset({"fresh", "stale"}),
    "custody_state": frozenset({"complete"}),
    "confidence_state": frozenset({"present"}),
    "provenance_state": frozenset({"bound"}),
    "conflict_state": frozenset({"conflicting", "none"}),
    "source_state": frozenset({"available", "degraded", "unavailable"}),
    "uncertainty_label": frozenset(
        {
            "related_entity_not_authoritative",
            "stale_review_required",
            "unresolved_conflict",
            "source_unavailable",
        }
    ),
}
_EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS = frozenset(
    {
        "stale_reputation",
        "conflicting_enrichment",
        "source_stale",
    }
)
_EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS = frozenset(
    {
        "source_denied",
        "source_unavailable",
    }
)
_EVIDENCE_PACK_PROJECTION_REQUIRED_STRINGS = (
    "evidence_request_id",
    "case_id",
    "source_id",
    "consumer",
    "status",
    "freshness_state",
    "custody_state",
    "confidence_state",
    "provenance_state",
    "conflict_state",
    "source_state",
    "uncertainty_label",
    "authority_posture",
    "workflow_authority",
)
_EVIDENCE_PACK_REQUIRED_CUSTODY_FIELDS = frozenset(
    {
        "reviewed_file_hash",
        "enrichment_request_id",
        "collection_timestamp",
        "response_digest",
        "aegisops_evidence_record_id",
    }
)
_EVIDENCE_PACK_REQUIRED_PROVENANCE_FIELDS = frozenset(
    {
        "request_binding",
        "case_binding",
        "target_binding",
        "source_id",
        "enrichment_request_id",
        "collection_timestamp",
        "response_digest",
        "custody_reference",
        "authority_posture",
    }
)
_EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS = frozenset(
    {
        "posture",
        "freshness",
        "ambiguity_badge",
        "source_native_score_authority",
    }
)
_EVIDENCE_PACK_PROJECTION_CONTRACT_FIELDS = frozenset(
    {
        *_EVIDENCE_PACK_PROJECTION_REQUIRED_STRINGS,
        "degraded_reasons",
        "unavailable_reasons",
        "authoritative_workflow_truth",
        "custody",
        "provenance",
        "confidence",
    }
)
_EVIDENCE_PACK_PROJECTION_RECOGNIZED_FIELDS = frozenset(
    {
        *_EVIDENCE_PACK_PROJECTION_CONTRACT_FIELDS,
        "cache_sourced",
        "stale_cache",
        "projection_source",
        "operator_visible",
        *_EVIDENCE_PACK_FORBIDDEN_READINESS_CLAIMS,
    }
)


def build_linked_evidence_pack_projections(
    *,
    case_id: str,
    linked_evidence_records: tuple[dict[str, object], ...],
) -> tuple[dict[str, object], ...]:
    projections: list[dict[str, object]] = []
    for evidence_record in linked_evidence_records:
        if (
            _optional_string_from_mapping(
                evidence_record,
                "lifecycle_state",
            )
            != "validated"
        ):
            continue
        content = evidence_record.get("content")
        if not isinstance(content, Mapping):
            continue
        evidence_record_id = _optional_string_from_mapping(
            evidence_record,
            "evidence_id",
        )
        record_provenance = evidence_record.get("provenance")
        record_custody_reference = (
            _optional_string_from_mapping(
                record_provenance,
                "custody_reference",
            )
            if isinstance(record_provenance, Mapping)
            else None
        )
        projection = _linked_evidence_pack_projection_from_record(
            evidence_record=evidence_record,
            content=content,
        )
        if projection is None:
            continue
        if not isinstance(projection, Mapping):
            raise ValueError("linked evidence-pack projection must be a mapping")
        projections.append(
            _validated_linked_evidence_pack_projection(
                projection=projection,
                case_id=case_id,
                evidence_record_id=evidence_record_id,
                record_custody_reference=record_custody_reference,
            )
        )
    return tuple(projections)


def _linked_evidence_pack_projection_from_record(
    *,
    evidence_record: Mapping[str, object],
    content: Mapping[str, object],
) -> Mapping[str, object] | None:
    projection = content.get(_EVIDENCE_PACK_PROJECTION_CONTENT_KEY)
    if projection is not None:
        if not _has_bounded_enrichment_producer_markers(
            evidence_record=evidence_record,
        ):
            raise ValueError("linked evidence-pack projection producer marker mismatch")
        if not isinstance(projection, Mapping):
            raise ValueError("linked evidence-pack projection must be a mapping")
        return projection
    if not _is_bounded_enrichment_evidence_record(
        evidence_record=evidence_record,
        content=content,
    ):
        return None
    return _project_bounded_enrichment_evidence_pack(
        content=content,
        evidence_record=evidence_record,
    )


def _project_bounded_enrichment_evidence_pack(
    *,
    content: Mapping[str, object],
    evidence_record: Mapping[str, object],
) -> Mapping[str, object]:
    evidence_record_id = _optional_string_from_mapping(
        evidence_record,
        "evidence_id",
    )
    if evidence_record_id is None:
        raise ValueError("linked evidence-pack projection custody binding mismatch")
    looked_up_at = _datetime_from_evidence_pack_content(
        content,
        "looked_up_at",
    )
    provenance = content.get("provenance")
    if not isinstance(provenance, Mapping):
        raise ValueError("linked evidence-pack projection requires provenance map")
    record_provenance = evidence_record.get("provenance")
    if not isinstance(record_provenance, Mapping):
        raise ValueError("linked evidence-pack projection requires provenance map")
    expected_custody_reference = _optional_string_from_mapping(
        record_provenance,
        "custody_reference",
    )
    if expected_custody_reference is None:
        raise ValueError("linked evidence-pack projection provenance binding mismatch")
    pack = BoundedEnrichmentEvidencePack(
        evidence_request_id=_required_string_from_mapping(
            content,
            "evidence_request_id",
        ),
        case_id=_required_string_from_mapping(content, "case_id"),
        source_id=_required_string_from_mapping(content, "source_id"),
        file_hash=_required_string_from_mapping(content, "file_hash"),
        status=_required_string_from_mapping(content, "status"),
        freshness=_required_string_from_mapping(content, "freshness"),
        looked_up_at=looked_up_at,
        custody=_required_mapping_from_mapping(content, "custody"),
        provenance=provenance,
        confidence=_required_mapping_from_mapping(content, "confidence"),
        content=_required_mapping_from_mapping(content, "content"),
        authority_posture=_required_string_from_mapping(
            content,
            "authority_posture",
        ),
        degraded_reasons=_string_tuple_from_object(content.get("degraded_reasons")),
        unavailable_reasons=_string_tuple_from_object(
            content.get("unavailable_reasons")
        ),
        workflow_authority=_required_string_from_mapping(
            content,
            "workflow_authority",
        ),
    )
    projection = project_evidence_freshness_provenance(
        EvidenceFreshnessProvenanceProjectionInput(
            evidence_pack=pack,
            consumer="case_workbench",
            expected_source_id=pack.source_id,
            expected_case_id=pack.case_id,
            expected_custody_reference=expected_custody_reference,
            projected_at=datetime.now(timezone.utc),
        )
    ).as_dict()
    return projection


def _is_bounded_enrichment_evidence_record(
    *,
    evidence_record: Mapping[str, object],
    content: Mapping[str, object],
) -> bool:
    content_payload = content.get("content")
    content_adapter = (
        _optional_string_from_mapping(content_payload, "adapter")
        if isinstance(content_payload, Mapping)
        else None
    )
    return (
        _has_bounded_enrichment_producer_markers(evidence_record=evidence_record)
        and content_adapter == _EVIDENCE_PACK_BOUNDED_ENRICHMENT_ADAPTER
        and all(
            field_name in content
            for field_name in (
                "evidence_request_id",
                "case_id",
                "source_id",
                "file_hash",
                "looked_up_at",
                "custody",
                "provenance",
                "confidence",
                "content",
            )
        )
    )


def _has_bounded_enrichment_producer_markers(
    *,
    evidence_record: Mapping[str, object],
) -> bool:
    return (
        _optional_string_from_mapping(evidence_record, "source_system")
        == _EVIDENCE_PACK_BOUNDED_ENRICHMENT_SOURCE_SYSTEM
        and _optional_string_from_mapping(
            evidence_record,
            "derivation_relationship",
        )
        == _EVIDENCE_PACK_BOUNDED_ENRICHMENT_DERIVATION
    )


def _optional_string_from_mapping(
    mapping: Mapping[str, object],
    key: str,
) -> str | None:
    value = mapping.get(key)
    return value.strip() if isinstance(value, str) and value.strip() else None


def _string_tuple_from_object(value: object) -> tuple[str, ...]:
    if isinstance(value, str) and value.strip():
        return (value.strip(),)
    if isinstance(value, (tuple, list)):
        return tuple(
            entry.strip() for entry in value if isinstance(entry, str) and entry.strip()
        )
    return ()


def _required_string_from_mapping(
    mapping: Mapping[str, object],
    key: str,
) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError("linked evidence-pack projection is missing required fields")
    return value.strip()


def _required_mapping_from_mapping(
    mapping: Mapping[str, object],
    key: str,
) -> Mapping[str, object]:
    value = mapping.get(key)
    if not isinstance(value, Mapping):
        raise ValueError(
            "linked evidence-pack projection requires custody, provenance, and confidence maps"
        )
    return value


def _datetime_from_evidence_pack_content(
    mapping: Mapping[str, object],
    key: str,
) -> datetime:
    value = mapping.get(key)
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                "linked evidence-pack projection requires timezone-aware timestamps"
            ) from exc
    else:
        raise ValueError(
            "linked evidence-pack projection requires timezone-aware timestamps"
        )
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(
            "linked evidence-pack projection requires timezone-aware timestamps"
        )
    return parsed


def _required_metadata_map_fields(
    metadata: Mapping[str, object],
    required_fields: frozenset[str],
) -> None:
    if frozenset(metadata) != required_fields:
        raise ValueError(
            "linked evidence-pack projection is missing required metadata fields"
        )
    if any(
        _optional_string_from_mapping(metadata, field_name) is None
        for field_name in required_fields
    ):
        raise ValueError(
            "linked evidence-pack projection is missing required metadata fields"
        )


def _projection_reason_tuple(
    projection: Mapping[str, object],
    key: str,
) -> tuple[str, ...]:
    value = projection.get(key)
    if value is None:
        raise ValueError(
            "linked evidence-pack projection has unsupported evidence-pack projection reason"
        )
    if not isinstance(value, (tuple, list)):
        raise ValueError(
            "linked evidence-pack projection has unsupported evidence-pack projection reason"
        )
    reasons: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(
                "linked evidence-pack projection has unsupported evidence-pack projection reason"
            )
        reasons.append(item.strip())
    return tuple(reasons)


def _linked_evidence_pack_expected_uncertainty_label(
    *,
    values: Mapping[str, str],
    degraded_reasons: tuple[str, ...],
    unavailable_reasons: tuple[str, ...],
) -> str:
    if values["status"] == "unavailable" or unavailable_reasons:
        return "source_unavailable"
    if "conflicting_enrichment" in degraded_reasons:
        return "unresolved_conflict"
    if (
        values["freshness_state"] == "stale"
        or "stale_reputation" in degraded_reasons
        or "source_stale" in degraded_reasons
    ):
        return "stale_review_required"
    return "related_entity_not_authoritative"


def _validate_linked_evidence_pack_reason_consistency(
    *,
    values: Mapping[str, str],
    degraded_reasons: tuple[str, ...],
    unavailable_reasons: tuple[str, ...],
    confidence: Mapping[str, object],
) -> None:
    if values["status"] == "available" and (degraded_reasons or unavailable_reasons):
        raise ValueError(
            "linked evidence-pack projection has inconsistent evidence-pack projection reason"
        )
    if values["status"] == "degraded" and (
        not degraded_reasons or unavailable_reasons
    ):
        raise ValueError(
            "linked evidence-pack projection has inconsistent evidence-pack projection reason"
        )
    if values["status"] == "unavailable" and not unavailable_reasons:
        raise ValueError(
            "linked evidence-pack projection has inconsistent evidence-pack projection reason"
        )
    if ("stale_reputation" in degraded_reasons) != (
        values["freshness_state"] == "stale"
    ):
        raise ValueError(
            "linked evidence-pack projection has inconsistent evidence-pack projection reason"
        )
    expected_conflict_state = (
        "conflicting" if "conflicting_enrichment" in degraded_reasons else "none"
    )
    if values["conflict_state"] != expected_conflict_state:
        raise ValueError(
            "linked evidence-pack projection has inconsistent evidence-pack projection reason"
        )
    expected_source_state = (
        "unavailable"
        if values["status"] == "unavailable" or unavailable_reasons
        else "degraded"
        if "source_stale" in degraded_reasons
        else "available"
    )
    if values["source_state"] != expected_source_state:
        raise ValueError(
            "linked evidence-pack projection has inconsistent evidence-pack projection reason"
        )
    if values[
        "uncertainty_label"
    ] != _linked_evidence_pack_expected_uncertainty_label(
        values=values,
        degraded_reasons=degraded_reasons,
        unavailable_reasons=unavailable_reasons,
    ):
        raise ValueError(
            "linked evidence-pack projection has inconsistent evidence-pack projection reason"
        )
    if _optional_string_from_mapping(
        confidence,
        "freshness",
    ) != values["freshness_state"] or _optional_string_from_mapping(
        confidence,
        "ambiguity_badge",
    ) != (
        "unresolved"
        if "conflicting_enrichment" in degraded_reasons
        else "related-entity"
    ):
        raise ValueError(
            "linked evidence-pack projection has inconsistent evidence-pack projection reason"
        )
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY.get(values["source_id"])
    if registry_entry is None:
        raise ValueError(
            "linked evidence-pack projection has unsupported evidence-pack projection source"
        )
    if "source_stale" in degraded_reasons and registry_entry.status != "degraded":
        raise ValueError("linked evidence-pack projection source state reason mismatch")
    if "source_denied" in unavailable_reasons and registry_entry.status != "disabled":
        raise ValueError("linked evidence-pack projection source state reason mismatch")


def _validate_linked_evidence_pack_provenance_bindings(
    *,
    provenance: Mapping[str, object],
    custody: Mapping[str, object],
    record_custody_reference: str | None,
) -> None:
    expected_values = {
        "target_binding": _optional_string_from_mapping(
            custody,
            "reviewed_file_hash",
        ),
        "enrichment_request_id": _optional_string_from_mapping(
            custody,
            "enrichment_request_id",
        ),
        "collection_timestamp": _optional_string_from_mapping(
            custody,
            "collection_timestamp",
        ),
        "response_digest": _optional_string_from_mapping(
            custody,
            "response_digest",
        ),
        "custody_reference": record_custody_reference,
    }
    if any(
        expected_value is None
        or _optional_string_from_mapping(provenance, field_name) != expected_value
        for field_name, expected_value in expected_values.items()
    ):
        raise ValueError("linked evidence-pack projection provenance binding mismatch")


def _is_supported_reviewed_hash(value: str | None) -> bool:
    if value is None or len(value) not in {32, 40, 64}:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in value)


def _is_sha256_digest(value: str | None) -> bool:
    if value is None or not value.startswith("sha256:"):
        return False
    digest = value.removeprefix("sha256:")
    if len(digest) != 64:
        return False
    return all(character in "0123456789abcdefABCDEF" for character in digest)


def _validate_linked_evidence_pack_metadata_formats(
    *,
    custody: Mapping[str, object],
    provenance: Mapping[str, object],
) -> None:
    if not _is_supported_reviewed_hash(
        _optional_string_from_mapping(custody, "reviewed_file_hash")
    ) or not _is_sha256_digest(
        _optional_string_from_mapping(custody, "response_digest")
    ):
        raise ValueError(
            "linked evidence-pack projection has invalid evidence-pack metadata"
        )
    _datetime_from_evidence_pack_content(custody, "collection_timestamp")
    _datetime_from_evidence_pack_content(provenance, "collection_timestamp")


def _validate_linked_evidence_pack_freshness_window(
    *,
    values: Mapping[str, str],
    custody: Mapping[str, object],
) -> None:
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY.get(values["source_id"])
    if registry_entry is None:
        raise ValueError(
            "linked evidence-pack projection has unsupported evidence-pack projection source"
        )
    collection_timestamp = _datetime_from_evidence_pack_content(
        custody,
        "collection_timestamp",
    )
    age_seconds = (
        datetime.now(timezone.utc) - collection_timestamp.astimezone(timezone.utc)
    ).total_seconds()
    if age_seconds < 0:
        raise ValueError("linked evidence-pack projection freshness window mismatch")
    freshness_window_seconds = _parse_duration_seconds(registry_entry.freshness_window)
    if (
        values["freshness_state"] == "fresh" and age_seconds > freshness_window_seconds
    ) or (
        values["freshness_state"] == "stale" and age_seconds <= freshness_window_seconds
    ):
        raise ValueError("linked evidence-pack projection freshness window mismatch")


def _validated_linked_evidence_pack_projection(
    *,
    projection: Mapping[str, object],
    case_id: str,
    evidence_record_id: str | None,
    record_custody_reference: str | None,
) -> dict[str, object]:
    values = {
        field_name: _optional_string_from_mapping(projection, field_name)
        for field_name in _EVIDENCE_PACK_PROJECTION_REQUIRED_STRINGS
    }
    if any(value is None for value in values.values()):
        raise ValueError("linked evidence-pack projection is missing required fields")
    for field_name, allowed_values in _EVIDENCE_PACK_ALLOWED_PROJECTION_LABELS.items():
        if values[field_name] not in allowed_values:
            raise ValueError(
                "linked evidence-pack projection has unsupported evidence-pack projection label"
            )
    if values["source_id"] != _EVIDENCE_PACK_SUPPORTED_SOURCE_ID:
        raise ValueError(
            "linked evidence-pack projection has unsupported evidence-pack projection source"
        )
    degraded_reasons = _projection_reason_tuple(
        projection,
        "degraded_reasons",
    )
    unavailable_reasons = _projection_reason_tuple(
        projection,
        "unavailable_reasons",
    )
    if any(
        reason not in _EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS
        for reason in degraded_reasons
    ) or any(
        reason not in _EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS
        for reason in unavailable_reasons
    ):
        raise ValueError(
            "linked evidence-pack projection has unsupported evidence-pack projection reason"
        )
    typed_values = {key: value for key, value in values.items() if value is not None}
    if typed_values["case_id"] != case_id:
        raise ValueError("linked evidence-pack projection case binding mismatch")
    if projection.get("authoritative_workflow_truth") is not False:
        raise ValueError("linked evidence-pack projection cannot carry workflow truth")
    if typed_values["workflow_authority"] != "none":
        raise ValueError("linked evidence-pack projection cannot carry workflow authority")
    if typed_values["authority_posture"] != _EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE:
        raise ValueError("linked evidence-pack projection must stay subordinate")
    if projection.get("operator_visible") is not None and projection.get(
        "operator_visible"
    ) is not True:
        raise ValueError("linked evidence-pack projection must stay operator visible")
    if any(
        claim_name in projection
        for claim_name in _EVIDENCE_PACK_FORBIDDEN_READINESS_CLAIMS
    ):
        raise ValueError("linked evidence-pack projection cannot claim release readiness")
    projection_source = _optional_string_from_mapping(
        projection,
        "projection_source",
    )
    cache_sourced = projection.get("cache_sourced")
    stale_cache = projection.get("stale_cache")
    if (
        (cache_sourced is not None and cache_sourced is not False)
        or (stale_cache is not None and stale_cache is not False)
        or projection_source in _EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES
    ):
        raise ValueError("linked evidence-pack projection cannot be cache sourced")

    custody = projection.get("custody")
    provenance = projection.get("provenance")
    confidence = projection.get("confidence")
    if (
        not isinstance(custody, Mapping)
        or not isinstance(provenance, Mapping)
        or not isinstance(confidence, Mapping)
    ):
        raise ValueError(
            "linked evidence-pack projection requires custody, provenance, and confidence maps"
        )
    _required_metadata_map_fields(
        custody,
        _EVIDENCE_PACK_REQUIRED_CUSTODY_FIELDS,
    )
    _required_metadata_map_fields(
        provenance,
        _EVIDENCE_PACK_REQUIRED_PROVENANCE_FIELDS,
    )
    _required_metadata_map_fields(
        confidence,
        _EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS,
    )
    if evidence_record_id is None or _optional_string_from_mapping(
        custody,
        "aegisops_evidence_record_id",
    ) != evidence_record_id:
        raise ValueError("linked evidence-pack projection custody binding mismatch")
    if _optional_string_from_mapping(
        provenance,
        "request_binding",
    ) != typed_values["evidence_request_id"] or _optional_string_from_mapping(
        provenance,
        "case_binding",
    ) != case_id or _optional_string_from_mapping(
        provenance,
        "source_id",
    ) != typed_values["source_id"]:
        raise ValueError("linked evidence-pack projection provenance binding mismatch")
    _validate_linked_evidence_pack_provenance_bindings(
        provenance=provenance,
        custody=custody,
        record_custody_reference=record_custody_reference,
    )
    _validate_linked_evidence_pack_metadata_formats(
        custody=custody,
        provenance=provenance,
    )
    _validate_linked_evidence_pack_freshness_window(
        values=typed_values,
        custody=custody,
    )
    if (
        _optional_string_from_mapping(provenance, "authority_posture")
        != _EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE
    ):
        raise ValueError("linked evidence-pack projection must stay subordinate")
    if _optional_string_from_mapping(
        confidence,
        "source_native_score_authority",
    ) != "none":
        raise ValueError("linked evidence-pack projection cannot carry workflow authority")
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY.get(typed_values["source_id"])
    if registry_entry is None:
        raise ValueError(
            "linked evidence-pack projection has unsupported evidence-pack projection source"
        )
    if (
        _optional_string_from_mapping(confidence, "posture")
        != registry_entry.confidence_posture
    ):
        raise ValueError("linked evidence-pack projection confidence posture mismatch")
    _validate_linked_evidence_pack_reason_consistency(
        values=typed_values,
        degraded_reasons=degraded_reasons,
        unavailable_reasons=unavailable_reasons,
        confidence=confidence,
    )

    missing_fields = _EVIDENCE_PACK_PROJECTION_CONTRACT_FIELDS - frozenset(projection)
    if missing_fields:
        raise ValueError("linked evidence-pack projection is missing required fields")
    unexpected_fields = (
        frozenset(projection) - _EVIDENCE_PACK_PROJECTION_RECOGNIZED_FIELDS
    )
    if unexpected_fields:
        raise ValueError(
            "linked evidence-pack projection has unexpected evidence-pack projection field"
        )
    return {
        field_name: projection[field_name]
        for field_name in _EVIDENCE_PACK_PROJECTION_CONTRACT_FIELDS
    }
