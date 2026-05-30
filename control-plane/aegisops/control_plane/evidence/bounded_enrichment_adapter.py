from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import hashlib
import json
import re
from types import MappingProxyType
from typing import Mapping

from .evidence_source_registry import (
    PHASE63_EVIDENCE_SOURCE_REGISTRY,
    _has_authority_widening_claim,
)
from .reviewed_evidence_requests import (
    ReviewedEvidenceRequestRecord,
    validate_phase63_reviewed_evidence_request,
)


_DURATION_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)
_BOUNDED_ENRICHMENT_SOURCE_ID = "malwarebazaar_hash_reputation"
_READ_ONLY_OPERATIONS = frozenset({"lookup_hash_reputation"})
_ACTIVE_REVIEWED_REQUEST_STATES = frozenset({"reviewed", "approved", "active"})
_REQUIRED_ENRICHMENT_CUSTODY_FIELDS = (
    "reviewed_file_hash",
    "enrichment_request_id",
    "collection_timestamp",
    "response_digest",
    "aegisops_evidence_record_id",
)
_HASH_PATTERN = re.compile(r"^(?:[0-9a-f]{32}|[0-9a-f]{40}|[0-9a-f]{64})$")
_RESPONSE_HASH_FIELDS = ("sha256_hash", "sha1_hash", "md5_hash", "hash")
_ENDPOINT_COMMAND_TERMS = (
    "quarantine",
    "quarantined",
    "quarantines",
    "quarantining",
    "contain host",
    "contain the host",
    "contained host",
    "containing host",
    "host containment",
    "isolate host",
    "isolate the host",
    "isolated host",
    "isolating host",
    "host isolation",
    "kill process",
    "kill the process",
    "killed process",
    "killing process",
    "terminate process",
    "terminate the process",
    "terminated process",
    "delete file",
    "delete the file",
    "deleted file",
    "remove file",
    "remove the file",
    "removed file",
    "remediate endpoint",
    "endpoint remediation",
    "mutate protected target",
    "block ip",
    "block domain",
    "block url",
    "block hash",
    "execute endpoint command",
    "run endpoint command",
    "issue endpoint command",
    "direct command authority",
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
        raise TypeError("Expected mapping-compatible bounded enrichment adapter field")
    return frozen


def _json_ready(value: object) -> object:
    if isinstance(value, Mapping):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    return value


def _validate_json_serializable(value: object, error_message: str) -> None:
    try:
        json.dumps(_json_ready(value), allow_nan=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError(error_message) from exc


def _canonical_response_digest(response: Mapping[str, object]) -> str:
    try:
        response_bytes = json.dumps(
            _json_ready(response),
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ValueError("enrichment response digest requires canonical JSON") from exc
    return "sha256:" + hashlib.sha256(response_bytes).hexdigest()


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def _require_supported_hash(value: object, field_name: str) -> str:
    normalized = _require_non_empty_string(value, field_name).lower()
    if _HASH_PATTERN.fullmatch(normalized) is None:
        raise ValueError(f"{field_name} must be MD5, SHA1, or SHA256 hex")
    return normalized


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime):
        raise ValueError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _parse_custody_collection_timestamp(value: object) -> datetime:
    raw_timestamp = _require_non_empty_string(
        value,
        "bounded enrichment custody collection_timestamp",
    )
    normalized_timestamp = raw_timestamp.replace("Z", "+00:00")
    try:
        parsed_timestamp = datetime.fromisoformat(normalized_timestamp)
    except ValueError as exc:
        raise ValueError(
            "bounded enrichment custody collection_timestamp must match looked_up_at"
        ) from exc
    return _require_aware_datetime(
        parsed_timestamp,
        "bounded enrichment custody collection_timestamp",
    )


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


def _response_hashes(response: Mapping[str, object]) -> tuple[str, ...]:
    hashes: list[str] = []
    for field_name in _RESPONSE_HASH_FIELDS:
        value = response.get(field_name)
        if isinstance(value, str) and value.strip():
            hashes.append(_require_supported_hash(value, f"enrichment response {field_name}"))
    return tuple(hashes)


def _normalize_command_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _has_endpoint_command_language(value: str) -> bool:
    normalized_value = f" {_normalize_command_text(value)} "
    return any(
        f" {_normalize_command_text(term)} " in normalized_value
        for term in _ENDPOINT_COMMAND_TERMS
    )


def _scan_for_authority_claim(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            _scan_for_authority_claim(key) or _scan_for_authority_claim(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list)):
        return any(_scan_for_authority_claim(item) for item in value)
    if isinstance(value, str):
        return _has_authority_widening_claim(value)
    return False


def _scan_for_endpoint_command_language(value: object) -> bool:
    if isinstance(value, Mapping):
        return any(
            _scan_for_endpoint_command_language(key)
            or _scan_for_endpoint_command_language(item)
            for key, item in value.items()
        )
    if isinstance(value, (tuple, list)):
        return any(_scan_for_endpoint_command_language(item) for item in value)
    if isinstance(value, str):
        return _has_endpoint_command_language(value)
    return False


@dataclass(frozen=True)
class BoundedEnrichmentAdapterInput:
    request: ReviewedEvidenceRequestRecord
    file_hash: str
    looked_up_at: datetime
    response: Mapping[str, object]
    custody: Mapping[str, object]
    adapter_state: str = "available"
    requested_operation: str = "lookup_hash_reputation"

    def __post_init__(self) -> None:
        object.__setattr__(self, "response", _freeze_mapping(self.response))
        object.__setattr__(self, "custody", _freeze_mapping(self.custody))

    def with_updates(self, **updates: object) -> "BoundedEnrichmentAdapterInput":
        return replace(self, **updates)


@dataclass(frozen=True)
class BoundedEnrichmentEvidencePack:
    evidence_request_id: str
    case_id: str
    source_id: str
    file_hash: str
    status: str
    freshness: str
    looked_up_at: datetime
    custody: Mapping[str, object]
    provenance: Mapping[str, object]
    confidence: Mapping[str, object]
    content: Mapping[str, object]
    authority_posture: str = "subordinate_evidence_context_only"
    degraded_reasons: tuple[str, ...] = ()
    unavailable_reasons: tuple[str, ...] = ()
    workflow_authority: str = "none"

    def __post_init__(self) -> None:
        object.__setattr__(self, "custody", _freeze_mapping(self.custody))
        object.__setattr__(self, "provenance", _freeze_mapping(self.provenance))
        object.__setattr__(self, "confidence", _freeze_mapping(self.confidence))
        object.__setattr__(self, "content", _freeze_mapping(self.content))

    def as_dict(self) -> dict[str, object]:
        return {
            "evidence_request_id": self.evidence_request_id,
            "case_id": self.case_id,
            "source_id": self.source_id,
            "file_hash": self.file_hash,
            "status": self.status,
            "freshness": self.freshness,
            "looked_up_at": self.looked_up_at.isoformat(),
            "custody": _json_ready(self.custody),
            "provenance": _json_ready(self.provenance),
            "confidence": _json_ready(self.confidence),
            "content": _json_ready(self.content),
            "authority_posture": self.authority_posture,
            "degraded_reasons": self.degraded_reasons,
            "unavailable_reasons": self.unavailable_reasons,
            "workflow_authority": self.workflow_authority,
        }


@dataclass(frozen=True)
class BoundedEnrichmentAdapter:
    source_id: str = _BOUNDED_ENRICHMENT_SOURCE_ID

    def build_evidence_pack(
        self,
        adapter_input: BoundedEnrichmentAdapterInput,
        *,
        now: datetime | None = None,
    ) -> BoundedEnrichmentEvidencePack:
        comparison_now = now or datetime.now(timezone.utc)
        _require_aware_datetime(comparison_now, "now")

        if self.source_id != _BOUNDED_ENRICHMENT_SOURCE_ID:
            raise ValueError(
                "bounded enrichment adapter source_id must be malwarebazaar_hash_reputation"
            )
        if adapter_input.requested_operation not in _READ_ONLY_OPERATIONS:
            raise ValueError("bounded enrichment adapter is read-only")

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
        if request.source_id != _BOUNDED_ENRICHMENT_SOURCE_ID:
            raise ValueError(
                "reviewed request source_id must be malwarebazaar_hash_reputation"
            )

        file_hash = _require_supported_hash(adapter_input.file_hash, "file_hash")
        request_file_hash = _require_supported_hash(
            request.target.get("file_hash"),
            "reviewed request target file_hash",
        )
        if file_hash != request_file_hash:
            raise ValueError("file_hash must match reviewed request target")

        looked_up_at = _require_aware_datetime(adapter_input.looked_up_at, "looked_up_at")
        if looked_up_at < request.requested_at:
            raise ValueError(
                "looked_up_at must not predate reviewed evidence request"
            )
        if looked_up_at > comparison_now:
            raise ValueError("looked_up_at must not be in the future")

        custody = adapter_input.custody
        if not custody or not _mapping_has_non_empty_fields(
            custody,
            _REQUIRED_ENRICHMENT_CUSTODY_FIELDS,
        ):
            raise ValueError("missing_enrichment_custody")
        custody_file_hash = _require_supported_hash(
            custody.get("reviewed_file_hash"),
            "bounded enrichment custody reviewed_file_hash",
        )
        if custody_file_hash != file_hash:
            raise ValueError(
                "file_hash must match bounded enrichment custody reviewed_file_hash"
            )
        custody_collection_timestamp = _parse_custody_collection_timestamp(
            custody.get("collection_timestamp")
        )
        if custody_collection_timestamp != looked_up_at:
            raise ValueError(
                "bounded enrichment custody collection_timestamp must match looked_up_at"
            )

        if adapter_input.adapter_state == "unavailable":
            response: Mapping[str, object] = MappingProxyType({})
        elif adapter_input.adapter_state != "available":
            raise ValueError("adapter_state must be available or unavailable")
        else:
            response = adapter_input.response
            if not response:
                raise ValueError("enrichment response must be present when source is available")
            query_status = response.get("query_status")
            if not isinstance(query_status, str) or query_status.strip().lower() != "ok":
                raise ValueError("MalwareBazaar response query_status must be ok")
            response_hashes = _response_hashes(response)
            if file_hash not in response_hashes:
                raise ValueError("response hash must match reviewed file hash")
            if _scan_for_authority_claim(response) or _scan_for_endpoint_command_language(
                response
            ):
                raise ValueError(
                    "enrichment response cannot claim workflow authority or endpoint command authority"
                )

        if str(custody["response_digest"]).strip() != _canonical_response_digest(response):
            raise ValueError(
                "response_digest must match canonical enrichment response"
            )

        freshness_window = _parse_duration_seconds(
            PHASE63_EVIDENCE_SOURCE_REGISTRY[
                _BOUNDED_ENRICHMENT_SOURCE_ID
            ].freshness_window
        )
        age_seconds = (comparison_now - looked_up_at).total_seconds()
        is_stale = age_seconds < 0 or age_seconds > freshness_window
        has_conflict = isinstance(response.get("conflict_marker"), Mapping)
        unavailable_reasons = (
            ("source_unavailable",)
            if adapter_input.adapter_state == "unavailable"
            else ()
        )
        degraded_reasons = tuple(
            reason
            for reason, present in (
                ("stale_reputation", is_stale),
                ("conflicting_enrichment", has_conflict),
            )
            if present
        )
        status = "available"
        if unavailable_reasons:
            status = "unavailable"
        elif degraded_reasons:
            status = "degraded"

        registry_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[
            _BOUNDED_ENRICHMENT_SOURCE_ID
        ]
        confidence = {
            "posture": registry_entry.confidence_posture,
            "freshness": "stale" if is_stale else "fresh",
            "ambiguity_badge": "unresolved" if has_conflict else "related-entity",
            "source_native_score_authority": "none",
        }
        provenance = {
            "request_binding": request.evidence_request_id,
            "case_binding": request.case_id,
            "target_binding": file_hash,
            "source_id": request.source_id,
            "enrichment_request_id": custody["enrichment_request_id"],
            "collection_timestamp": looked_up_at.isoformat(),
            "response_digest": custody["response_digest"],
            "custody_reference": request.custody["custody_reference"],
            "authority_posture": "subordinate_evidence_context_only",
        }
        content = {
            "adapter": "phase63_bounded_enrichment_adapter",
            "selected_source": "malwarebazaar_hash_reputation",
            "scope": {
                "case_id": request.case_id,
                "evidence_request_id": request.evidence_request_id,
                "requested_scope": request.requested_scope,
            },
            "lookup": {
                "file_hash": file_hash,
                "looked_up_at": looked_up_at.isoformat(),
            },
            "reputation": response,
            "authority_boundary": {
                "workflow_truth": "aegisops_records_only",
                "workflow_authority": "none",
            },
        }
        pack = BoundedEnrichmentEvidencePack(
            evidence_request_id=request.evidence_request_id,
            case_id=request.case_id,
            source_id=request.source_id,
            file_hash=file_hash,
            status=status,
            freshness="stale" if is_stale else "fresh",
            looked_up_at=looked_up_at,
            custody=custody,
            provenance=provenance,
            confidence=confidence,
            content=content,
            degraded_reasons=degraded_reasons,
            unavailable_reasons=unavailable_reasons,
        )
        _validate_json_serializable(
            pack.as_dict(),
            "bounded enrichment evidence pack must contain JSON-serializable finite values",
        )
        return pack
