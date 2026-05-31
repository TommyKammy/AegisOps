from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
import re

from ..evidence.bounded_enrichment_adapter import (
    _require_supported_hash,
    _scan_for_authority_claim,
    _scan_for_endpoint_command_language,
)
from ..evidence.evidence_source_registry import PHASE63_EVIDENCE_SOURCE_REGISTRY

_AGENT_NAME = "ai_grounding_adapter"
_TOOL_NAME = "evidence_grounding"
_AUTHORITY_CEILING = "advisory_only"
_CONTRACT_VERSION = "phase-63-7"
_PHASE63_5_GROUNDING_SOURCE_ID = "malwarebazaar_hash_reputation"
_SUPPORTED_GROUNDING_SOURCE_IDS = frozenset({_PHASE63_5_GROUNDING_SOURCE_ID})
_REGISTRY_CITATIONS = (
    "docs/automation/ai-agent-registry.json",
    "docs/automation/ai-tool-registry.json",
    "docs/automation/ai-disabled-degraded-mode-contract.json",
    "docs/phase-51-6-authority-boundary-negative-test-policy.md",
    "docs/phase-59-4-ai-disabled-degraded-mode-contract.md",
    "docs/phase-63-5-evidence-freshness-provenance-projection.md",
)
_SUPPORTED_RECORD_FAMILIES = (
    "case",
    "reviewed_evidence_request",
    "evidence",
    "source",
    "ai_trace",
)
_NEGATIVE_AUTHORITY = (
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "evidence_truth_creation",
    "conflict_resolution",
    "workflow_progress",
    "production_write",
    "endpoint_remediation",
    "protected_target_mutation",
    "policy_bypass",
    "release_truth",
    "readiness_truth",
    "workflow_truth",
)
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
_SUBORDINATE_AUTHORITY_POSTURE = "subordinate_evidence_context_only"
_NO_WORKFLOW_AUTHORITY = "none"
_ALLOWED_STATUS = frozenset({"available", "degraded", "unavailable"})
_ALLOWED_FRESHNESS = frozenset({"fresh", "stale"})
_ALLOWED_CONFLICT = frozenset({"none", "conflicting"})
_ALLOWED_SOURCE_STATE = frozenset({"available", "degraded", "unavailable"})
_ALLOWED_DEGRADED_REASONS = frozenset(
    {
        "stale_reputation",
        "conflicting_enrichment",
        "source_stale",
    }
)
_ALLOWED_UNAVAILABLE_REASONS = frozenset(
    {
        "source_denied",
        "source_unavailable",
    }
)
_ALLOWED_UNCERTAINTY = frozenset(
    {
        "related_entity_not_authoritative",
        "stale_review_required",
        "unresolved_conflict",
        "source_unavailable",
    }
)
_DURATION_PATTERN = re.compile(
    r"PT"
    r"(?:(?P<hours>\d+)H)?"
    r"(?:(?P<minutes>\d+)M)?"
    r"(?:(?P<seconds>\d+)S)?"
)
_SHA256_DIGEST_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


def _validated_grounding_payload(
    grounding_context_payload: object,
    *,
    trusted_grounded_at: datetime,
) -> dict[str, object]:
    if not isinstance(grounding_context_payload, Mapping):
        return _invalid(("malformed_grounding_context_payload",))
    if grounding_context_payload.get("contract_version") != _CONTRACT_VERSION:
        return _invalid(("unsupported_ai_grounding_contract_version",))
    anchor = grounding_context_payload.get("review_anchor")
    if not isinstance(anchor, Mapping):
        return _invalid(("missing_review_anchor",))
    if anchor.get("direct_binding_required") is not True:
        return _invalid(("review_anchor_without_direct_binding",))
    anchor_family = _string(anchor.get("record_family"))
    anchor_id = _string(anchor.get("record_id"))
    if anchor_family != "case" or anchor_id is None:
        return _invalid(("unsupported_review_anchor",))
    custody_reference_bindings = anchor.get("custody_reference_by_evidence_request_id")
    evidence_record_bindings = anchor.get("evidence_record_id_by_evidence_request_id")
    reviewed_hash_bindings = anchor.get("reviewed_file_hash_by_evidence_request_id")
    collection_timestamp_bindings = anchor.get(
        "collection_timestamp_by_evidence_request_id"
    )
    response_digest_bindings = anchor.get("response_digest_by_evidence_request_id")

    raw_projections = grounding_context_payload.get("evidence_projections")
    if not isinstance(raw_projections, Sequence) or isinstance(
        raw_projections,
        (str, bytes),
    ):
        return _invalid(("malformed_evidence_projections",), anchor_id=anchor_id)
    if not raw_projections:
        return _invalid(("missing_grounding_projection",), anchor_id=anchor_id)

    reasons: list[str] = []
    projections: list[Mapping[str, object]] = []
    for raw_projection in raw_projections:
        if not isinstance(raw_projection, Mapping):
            reasons.append("malformed_evidence_projection")
            continue
        projection_reasons = _projection_reasons(
            raw_projection,
            anchor_id,
            custody_reference_bindings,
            evidence_record_bindings,
            reviewed_hash_bindings,
            collection_timestamp_bindings,
            response_digest_bindings,
            trusted_grounded_at,
        )
        reasons.extend(projection_reasons)
        if not projection_reasons:
            projections.append(raw_projection)

    return {
        "reasons": _dedupe_strings(tuple(reasons)),
        "anchor_id": anchor_id,
        "projections": tuple(projections),
    }


def _projection_reasons(
    projection: Mapping[str, object],
    anchor_id: str,
    custody_reference_bindings: object,
    evidence_record_bindings: object,
    reviewed_hash_bindings: object,
    collection_timestamp_bindings: object,
    response_digest_bindings: object,
    grounded_at: datetime,
) -> tuple[str, ...]:
    reasons: list[str] = []
    case_id = _string(projection.get("case_id"))
    evidence_request_id = _string(projection.get("evidence_request_id"))
    source_id = _string(projection.get("source_id"))
    expected_custody_reference = _expected_custody_reference(
        custody_reference_bindings,
        evidence_request_id,
    )
    expected_evidence_record_id = _expected_evidence_record_id(
        evidence_record_bindings,
        evidence_request_id,
    )
    expected_reviewed_file_hash = _expected_reviewed_file_hash(
        reviewed_hash_bindings,
        evidence_request_id,
    )
    expected_collection_timestamp = _expected_collection_timestamp(
        collection_timestamp_bindings,
        evidence_request_id,
    )
    expected_response_digest = _expected_response_digest(
        response_digest_bindings,
        evidence_request_id,
    )
    if projection.get("consumer") != "ai_grounding":
        reasons.append("unsupported_grounding_consumer")
    if case_id != anchor_id:
        reasons.append("grounding_not_bound_to_review_anchor")
    if evidence_request_id is None:
        reasons.append("missing_grounding_evidence_request_id")
    if source_id is None:
        reasons.append("missing_grounding_source_id")
    else:
        reasons.extend(_grounding_source_reasons(source_id, projection))
    if projection.get("authoritative_workflow_truth") is not False:
        reasons.append("grounding_authority_promotion_attempt")
    if projection.get("workflow_authority") != _NO_WORKFLOW_AUTHORITY:
        reasons.append("grounding_authority_promotion_attempt")
    if projection.get("authority_posture") != _SUBORDINATE_AUTHORITY_POSTURE:
        reasons.append("grounding_authority_promotion_attempt")
    if projection.get("status") not in _ALLOWED_STATUS:
        reasons.append("unsupported_grounding_status")
    if projection.get("freshness_state") not in _ALLOWED_FRESHNESS:
        reasons.append("unsupported_grounding_freshness")
    if projection.get("custody_state") != "complete":
        reasons.append("missing_grounding_custody")
    if projection.get("provenance_state") != "bound":
        reasons.append("missing_grounding_provenance")
    if projection.get("confidence_state") != "present":
        reasons.append("missing_grounding_confidence")
    if projection.get("conflict_state") not in _ALLOWED_CONFLICT:
        reasons.append("unsupported_grounding_conflict")
    if projection.get("source_state") not in _ALLOWED_SOURCE_STATE:
        reasons.append("unsupported_grounding_source_state")
    if projection.get("uncertainty_label") not in _ALLOWED_UNCERTAINTY:
        reasons.append("missing_grounding_uncertainty")
    else:
        reasons.extend(_uncertainty_state_reasons(projection))
    reasons.extend(_state_consistency_reasons(projection))
    custody = projection.get("custody")
    provenance = projection.get("provenance")
    confidence = projection.get("confidence")
    if not _mapping_has_non_empty_fields(custody, _REQUIRED_CUSTODY_FIELDS):
        reasons.append("missing_grounding_custody")
    if not _mapping_has_non_empty_fields(provenance, _REQUIRED_PROVENANCE_FIELDS):
        reasons.append("missing_grounding_provenance")
    if isinstance(custody, Mapping) and isinstance(provenance, Mapping):
        reasons.extend(
            _provenance_binding_reasons(
                provenance=provenance,
                custody=custody,
                projection=projection,
                anchor_id=anchor_id,
                expected_custody_reference=expected_custody_reference,
                expected_collection_timestamp=expected_collection_timestamp,
            )
        )
    if isinstance(custody, Mapping):
        reasons.extend(_reviewed_hash_reasons(custody, expected_reviewed_file_hash))
        reasons.extend(_response_digest_reasons(custody, expected_response_digest))
        reasons.extend(
            _evidence_record_binding_reasons(
                custody=custody,
                expected_evidence_record_id=expected_evidence_record_id,
            )
        )
        reasons.extend(
            _metadata_contract_reasons(
                custody,
                _ALLOWED_CUSTODY_FIELDS,
                _ALLOWED_CUSTODY_FIELDS,
            )
        )
    if expected_custody_reference is None:
        reasons.append("missing_grounding_custody_reference_binding")
    if expected_evidence_record_id is None:
        reasons.append("missing_grounding_evidence_record_binding")
    if expected_reviewed_file_hash is None:
        reasons.append("missing_grounding_reviewed_hash_binding")
    if expected_collection_timestamp is None:
        reasons.append("missing_grounding_collection_timestamp_binding")
    if expected_response_digest is None:
        reasons.append("missing_grounding_response_digest_binding")
    if not _mapping_has_non_empty_fields(confidence, _REQUIRED_CONFIDENCE_FIELDS):
        reasons.append("missing_grounding_confidence")
    if isinstance(provenance, Mapping):
        reasons.extend(
            _metadata_contract_reasons(
                provenance,
                _ALLOWED_PROVENANCE_FIELDS,
                _ALLOWED_PROVENANCE_FIELDS,
            )
        )
        if provenance.get("authority_posture") != _SUBORDINATE_AUTHORITY_POSTURE:
            reasons.append("grounding_authority_promotion_attempt")
    if isinstance(confidence, Mapping):
        reasons.extend(
            _metadata_contract_reasons(
                confidence,
                _ALLOWED_CONFIDENCE_FIELDS,
                frozenset({"ambiguity_badge"}),
            )
        )
        reasons.extend(_confidence_binding_reasons(confidence, source_id))
        if confidence.get("source_native_score_authority") != _NO_WORKFLOW_AUTHORITY:
            reasons.append("grounding_authority_promotion_attempt")
    reasons.extend(
        _freshness_recomputation_reasons(
            projection,
            grounded_at,
            expected_collection_timestamp,
        )
    )
    reasons.extend(_citation_reasons(projection, anchor_id))
    return tuple(reasons)


def _grounding_source_reasons(
    source_id: str,
    projection: Mapping[str, object],
) -> tuple[str, ...]:
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY.get(source_id)
    if registry_entry is None or source_id not in _SUPPORTED_GROUNDING_SOURCE_IDS:
        return ("unsupported_grounding_source",)
    if registry_entry.status not in {"enabled", "degraded", "disabled"}:
        return ("unsupported_grounding_source",)
    reasons: list[str] = []
    degraded_reasons = _string_tuple(projection.get("degraded_reasons"))
    unavailable_reasons = _string_tuple(projection.get("unavailable_reasons"))
    status = projection.get("status")
    source_state = projection.get("source_state")
    if status == "unavailable" or source_state == "unavailable":
        reasons.append("unavailable_evidence_source")
    if registry_entry.status == "disabled":
        if (
            status != "unavailable"
            or source_state != "unavailable"
            or "source_denied" not in unavailable_reasons
        ):
            reasons.append("grounding_source_registry_status_mismatch")
    if registry_entry.status == "degraded":
        if (
            status == "available"
            or source_state == "available"
            or "source_stale" not in degraded_reasons
        ):
            reasons.append("grounding_source_registry_status_mismatch")
    if registry_entry.status == "enabled":
        if (
            status == "unavailable"
            or source_state == "unavailable"
            or "source_unavailable" in unavailable_reasons
        ):
            reasons.append("unavailable_evidence_source")
        if (
            "source_denied" in unavailable_reasons
            or "source_stale" in degraded_reasons
        ):
            reasons.append("grounding_source_registry_status_mismatch")
    reasons.extend(_unsupported_projection_reason_reasons(projection))
    return tuple(reasons)


def _confidence_binding_reasons(
    confidence: Mapping[str, object],
    source_id: str | None,
) -> tuple[str, ...]:
    if source_id is None:
        return ()
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY.get(source_id)
    if registry_entry is None:
        return ()
    if confidence.get("posture") != registry_entry.confidence_posture:
        return ("grounding_confidence_posture_mismatch",)
    return ()


def _metadata_contract_reasons(
    value: Mapping[str, object],
    allowed_fields: frozenset[str],
    authority_scanned_fields: frozenset[str],
) -> tuple[str, ...]:
    reasons: list[str] = []
    if frozenset(value) != allowed_fields:
        reasons.append("unexpected_grounding_metadata")
    for field_name, item in value.items():
        if field_name not in authority_scanned_fields:
            continue
        for scan_value in _metadata_authority_values(field_name, item):
            if _scan_for_authority_claim(
                scan_value
            ) or _scan_for_endpoint_command_language(scan_value):
                reasons.append("grounding_metadata_authority_claim")
                return tuple(reasons)
    return tuple(reasons)


def _metadata_authority_values(
    field_name: str,
    item: object,
) -> tuple[object, ...]:
    if field_name == "request_binding" and isinstance(item, str):
        stripped_item = item.strip()
        scan_values = [
            re.sub(r"^evidence[-_\s]+request[-_\s]*", "", stripped_item, flags=re.I)
        ]
        if re.search(r"\bevidence[-_\s]*request[-_\s]*truths?\b", stripped_item, re.I):
            scan_values.append(stripped_item)
        return tuple(scan_values)
    if field_name == "authority_posture":
        return ("",)
    return (item,)


def _freshness_recomputation_reasons(
    projection: Mapping[str, object],
    grounded_at: datetime,
    expected_collection_timestamp: datetime | None,
) -> tuple[str, ...]:
    source_id = _string(projection.get("source_id"))
    if source_id is None:
        return ()
    registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY.get(source_id)
    if registry_entry is None:
        return ()
    if expected_collection_timestamp is None:
        return ("grounding_freshness_recompute_unavailable",)
    try:
        freshness_window_seconds = _parse_duration_seconds(registry_entry.freshness_window)
    except ValueError:
        return ("grounding_freshness_recompute_unavailable",)

    age_seconds = (grounded_at - expected_collection_timestamp).total_seconds()
    if age_seconds < 0:
        return ("grounding_freshness_recompute_mismatch",)
    expected_freshness = (
        "stale" if age_seconds > freshness_window_seconds else "fresh"
    )
    reasons: list[str] = []
    if projection.get("freshness_state") != expected_freshness:
        reasons.append("grounding_freshness_state_mismatch")
    confidence = projection.get("confidence")
    if (
        isinstance(confidence, Mapping)
        and confidence.get("freshness") != expected_freshness
    ):
        reasons.append("grounding_freshness_state_mismatch")
    return tuple(reasons)


def _trusted_grounded_at() -> datetime:
    return datetime.now(timezone.utc)


def _parse_duration_seconds(value: str) -> int:
    match = _DURATION_PATTERN.fullmatch(value.strip())
    if match is None:
        raise ValueError("freshness window must be an ISO-8601 time duration")
    duration_parts = {
        name: int(match.group(name) or 0) for name in ("hours", "minutes", "seconds")
    }
    seconds = (
        duration_parts["hours"] * 3600
        + duration_parts["minutes"] * 60
        + duration_parts["seconds"]
    )
    if seconds <= 0:
        raise ValueError("freshness window must be positive")
    return seconds


def _aware_datetime(value: object, field_name: str) -> datetime:
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


def _unsupported_projection_reason_reasons(
    projection: Mapping[str, object],
) -> tuple[str, ...]:
    if _malformed_optional_string_sequence(
        projection.get("degraded_reasons")
    ) or _malformed_optional_string_sequence(projection.get("unavailable_reasons")):
        return ("unsupported_grounding_reason",)
    degraded_reasons = _string_tuple(projection.get("degraded_reasons"))
    unavailable_reasons = _string_tuple(projection.get("unavailable_reasons"))
    if any(reason not in _ALLOWED_DEGRADED_REASONS for reason in degraded_reasons):
        return ("unsupported_grounding_reason",)
    if any(
        reason not in _ALLOWED_UNAVAILABLE_REASONS
        for reason in unavailable_reasons
    ):
        return ("unsupported_grounding_reason",)
    return ()


def _evidence_record_binding_reasons(
    *,
    custody: Mapping[str, object],
    expected_evidence_record_id: str | None,
) -> tuple[str, ...]:
    if expected_evidence_record_id is None:
        return ()
    evidence_record_id = _string(custody.get("aegisops_evidence_record_id"))
    if evidence_record_id != expected_evidence_record_id:
        return ("grounding_evidence_record_binding_mismatch",)
    return ()


def _response_digest_reasons(
    custody: Mapping[str, object],
    expected_response_digest: str | None,
) -> tuple[str, ...]:
    response_digest = _string(custody.get("response_digest"))
    if (
        response_digest is None
        or _SHA256_DIGEST_PATTERN.fullmatch(response_digest) is None
        or expected_response_digest is None
        or response_digest != expected_response_digest
    ):
        return ("grounding_response_digest_mismatch",)
    return ()


def _provenance_binding_reasons(
    *,
    provenance: Mapping[str, object],
    custody: Mapping[str, object],
    projection: Mapping[str, object],
    anchor_id: str,
    expected_custody_reference: str | None,
    expected_collection_timestamp: datetime | None,
) -> tuple[str, ...]:
    target_binding = _normalized_supported_hash(custody.get("reviewed_file_hash"))
    provenance_target_binding = _normalized_supported_hash(
        provenance.get("target_binding")
    )
    if target_binding is None or provenance_target_binding != target_binding:
        return ("grounding_provenance_binding_mismatch",)
    try:
        collection_timestamp = _aware_datetime(
            custody.get("collection_timestamp"),
            "custody.collection_timestamp",
        )
        provenance_collection_timestamp = _aware_datetime(
            provenance.get("collection_timestamp"),
            "provenance.collection_timestamp",
        )
    except ValueError:
        return ("grounding_provenance_binding_mismatch",)
    if (
        expected_collection_timestamp is None
        or collection_timestamp != expected_collection_timestamp
        or provenance_collection_timestamp != expected_collection_timestamp
    ):
        return ("grounding_provenance_binding_mismatch",)

    expected_values = {
        "request_binding": _string(projection.get("evidence_request_id")),
        "case_binding": anchor_id,
        "source_id": _string(projection.get("source_id")),
        "enrichment_request_id": _string(custody.get("enrichment_request_id")),
        "response_digest": _string(custody.get("response_digest")),
        "custody_reference": expected_custody_reference,
        "authority_posture": _SUBORDINATE_AUTHORITY_POSTURE,
    }
    for field_name, expected_value in expected_values.items():
        if expected_value is None:
            return ("grounding_provenance_binding_mismatch",)
        if _string(provenance.get(field_name)) != expected_value:
            return ("grounding_provenance_binding_mismatch",)
    return ()


def _reviewed_hash_reasons(
    custody: Mapping[str, object],
    expected_reviewed_file_hash: str | None,
) -> tuple[str, ...]:
    reviewed_file_hash = _normalized_supported_hash(custody.get("reviewed_file_hash"))
    if reviewed_file_hash is None:
        return ("unsupported_grounding_reviewed_hash",)
    if (
        expected_reviewed_file_hash is not None
        and reviewed_file_hash != expected_reviewed_file_hash
    ):
        return ("grounding_reviewed_hash_binding_mismatch",)
    return ()


def _normalized_supported_hash(value: object) -> str | None:
    try:
        return _require_supported_hash(value, "reviewed_file_hash")
    except ValueError:
        return None


def _citation_reasons(
    projection: Mapping[str, object],
    anchor_id: str,
) -> tuple[str, ...]:
    required = _projection_citation_ids(projection, anchor_id)
    if not required:
        return ("missing_required_grounding_citation",)
    if "citation_ids" not in projection:
        return ()
    supplied_value = projection.get("citation_ids")
    if not isinstance(supplied_value, (list, tuple)):
        return ("malformed_grounding_citation_ids",)
    supplied = _string_tuple(supplied_value)
    if len(supplied) != len(supplied_value):
        return ("malformed_grounding_citation_ids",)
    reasons: list[str] = []
    required_set = frozenset(required)
    supplied_set = frozenset(supplied)
    if not required_set.issubset(supplied_set):
        reasons.append("missing_required_grounding_citation")
    if not supplied_set.issubset(required_set):
        reasons.append("out_of_scope_grounding_citation")
    return tuple(reasons)


def _projection_citation_ids(
    projection: Mapping[str, object],
    anchor_id: str | None,
) -> tuple[str, ...]:
    if anchor_id is None:
        return ()
    evidence_request_id = _string(projection.get("evidence_request_id"))
    source_id = _string(projection.get("source_id"))
    custody = projection.get("custody")
    evidence_record_id = (
        _string(custody.get("aegisops_evidence_record_id"))
        if isinstance(custody, Mapping)
        else None
    )
    if (
        evidence_request_id is None
        or evidence_record_id is None
        or source_id is None
    ):
        return ()
    return (
        "case:" + anchor_id,
        "reviewed_evidence_request:" + evidence_request_id,
        "evidence:" + evidence_record_id,
        "source:" + source_id,
    )


def _expected_custody_reference(
    custody_reference_bindings: object,
    evidence_request_id: str | None,
) -> str | None:
    if evidence_request_id is None or not isinstance(custody_reference_bindings, Mapping):
        return None
    return _string(custody_reference_bindings.get(evidence_request_id))


def _expected_evidence_record_id(
    evidence_record_bindings: object,
    evidence_request_id: str | None,
) -> str | None:
    if evidence_request_id is None or not isinstance(evidence_record_bindings, Mapping):
        return None
    return _string(evidence_record_bindings.get(evidence_request_id))


def _expected_reviewed_file_hash(
    reviewed_hash_bindings: object,
    evidence_request_id: str | None,
) -> str | None:
    if evidence_request_id is None or not isinstance(reviewed_hash_bindings, Mapping):
        return None
    return _normalized_supported_hash(reviewed_hash_bindings.get(evidence_request_id))


def _expected_collection_timestamp(
    collection_timestamp_bindings: object,
    evidence_request_id: str | None,
) -> datetime | None:
    if evidence_request_id is None or not isinstance(
        collection_timestamp_bindings,
        Mapping,
    ):
        return None
    try:
        return _aware_datetime(
            collection_timestamp_bindings.get(evidence_request_id),
            "review_anchor.collection_timestamp_by_evidence_request_id",
        )
    except ValueError:
        return None


def _expected_response_digest(
    response_digest_bindings: object,
    evidence_request_id: str | None,
) -> str | None:
    if evidence_request_id is None or not isinstance(response_digest_bindings, Mapping):
        return None
    response_digest = _string(response_digest_bindings.get(evidence_request_id))
    if (
        response_digest is None
        or _SHA256_DIGEST_PATTERN.fullmatch(response_digest) is None
    ):
        return None
    return response_digest


def _uncertainty_state_reasons(
    projection: Mapping[str, object],
) -> tuple[str, ...]:
    expected = _expected_uncertainty_label(projection)
    if expected is None:
        return ("grounding_uncertainty_state_mismatch",)
    if projection.get("uncertainty_label") != expected:
        return ("grounding_uncertainty_state_mismatch",)
    return ()


def _expected_uncertainty_label(
    projection: Mapping[str, object],
) -> str | None:
    status = projection.get("status")
    source_state = projection.get("source_state")
    freshness_state = projection.get("freshness_state")
    conflict_state = projection.get("conflict_state")
    if status not in _ALLOWED_STATUS:
        return None
    if source_state not in _ALLOWED_SOURCE_STATE:
        return None
    if freshness_state not in _ALLOWED_FRESHNESS:
        return None
    if conflict_state not in _ALLOWED_CONFLICT:
        return None
    if status == "unavailable" or source_state == "unavailable":
        return "source_unavailable"
    if conflict_state == "conflicting":
        return "unresolved_conflict"
    if (
        freshness_state == "stale"
        or source_state == "degraded"
        or status == "degraded"
    ):
        return "stale_review_required"
    return "related_entity_not_authoritative"


def _state_consistency_reasons(
    projection: Mapping[str, object],
) -> tuple[str, ...]:
    status = projection.get("status")
    source_state = projection.get("source_state")
    freshness_state = projection.get("freshness_state")
    conflict_state = projection.get("conflict_state")
    degraded_reasons = _string_tuple(projection.get("degraded_reasons"))
    unavailable_reasons = _string_tuple(projection.get("unavailable_reasons"))
    confidence = projection.get("confidence")

    mismatched = False
    if status == "available":
        mismatched = (
            freshness_state != "fresh"
            or conflict_state != "none"
            or source_state != "available"
            or bool(degraded_reasons)
            or bool(unavailable_reasons)
        )
    if status == "degraded":
        mismatched = mismatched or bool(unavailable_reasons) or not degraded_reasons
    if status == "unavailable":
        mismatched = mismatched or source_state != "unavailable" or not unavailable_reasons
    if source_state == "unavailable" and status != "unavailable":
        mismatched = True
    if source_state == "degraded" and "source_stale" not in degraded_reasons:
        mismatched = True
    if source_state == "available" and "source_stale" in degraded_reasons:
        mismatched = True
    if conflict_state == "conflicting":
        mismatched = mismatched or (
            status != "degraded"
            or "conflicting_enrichment" not in degraded_reasons
        )
    if conflict_state == "none" and "conflicting_enrichment" in degraded_reasons:
        mismatched = True
    if freshness_state == "stale":
        mismatched = mismatched or (
            status == "available" or "stale_reputation" not in degraded_reasons
        )
    if freshness_state == "fresh" and "stale_reputation" in degraded_reasons:
        mismatched = True
    if isinstance(confidence, Mapping):
        expected_badge = (
            "unresolved" if conflict_state == "conflicting" else "related-entity"
        )
        mismatched = mismatched or (
            confidence.get("freshness") != freshness_state
            or confidence.get("ambiguity_badge") != expected_badge
        )
    return ("grounding_state_mismatch",) if mismatched else ()



def _invalid(
    reasons: tuple[str, ...],
    *,
    anchor_id: str | None = None,
) -> dict[str, object]:
    return {
        "reasons": reasons,
        "anchor_id": anchor_id,
        "projections": (),
    }


def _mapping_has_non_empty_fields(
    value: object,
    required_fields: tuple[str, ...],
) -> bool:
    if not isinstance(value, Mapping):
        return False
    return all(
        isinstance(value.get(field_name), str) and bool(str(value[field_name]).strip())
        for field_name in required_fields
    )


def _string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    normalized: list[str] = []
    for item in value:
        normalized_item = _string(item)
        if normalized_item is not None and normalized_item not in normalized:
            normalized.append(normalized_item)
    return tuple(normalized)


def _malformed_optional_string_sequence(value: object) -> bool:
    if value is None:
        return False
    if not isinstance(value, (list, tuple)):
        return True
    return any(_string(item) is None for item in value)


def _dedupe_strings(values: tuple[str, ...]) -> tuple[str, ...]:
    deduped: list[str] = []
    for value in values:
        if isinstance(value, str) and value not in deduped:
            deduped.append(value)
    return tuple(deduped)
