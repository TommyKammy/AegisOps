from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping


EvidenceSourceValidationErrors = tuple[str, ...]


@dataclass(frozen=True)
class EvidenceSourceEntry:
    source_id: str
    source_type: str
    owner: str
    allowed_target_class: str
    custody_requirements: str
    freshness_window: str
    confidence_posture: str
    status: str
    degraded_states: tuple[str, ...]
    disabled_states: tuple[str, ...]
    authority_posture: str = "subordinate_evidence_context_only"

    def as_dict(self) -> dict[str, object]:
        return {
            "source_id": self.source_id,
            "source_type": self.source_type,
            "owner": self.owner,
            "allowed_target_class": self.allowed_target_class,
            "custody_requirements": self.custody_requirements,
            "freshness_window": self.freshness_window,
            "confidence_posture": self.confidence_posture,
            "status": self.status,
            "degraded_states": self.degraded_states,
            "disabled_states": self.disabled_states,
            "authority_posture": self.authority_posture,
        }


_ALLOWED_SOURCE_TYPES = frozenset(
    {
        "osquery",
        "malwarebazaar_hash_reputation",
    }
)
_ALLOWED_SOURCE_IDS = frozenset(
    {
        "osquery_host_state",
        "malwarebazaar_hash_reputation",
    }
)
_ALLOWED_TARGET_CLASSES = frozenset(
    {
        "explicitly_bound_host",
        "reviewed_file_hash",
    }
)
_ALLOWED_STATUSES = frozenset({"enabled", "disabled", "degraded"})
_SUBORDINATE_AUTHORITY_POSTURE = "subordinate_evidence_context_only"

_AUTHORITY_WIDENING_TERMS = (
    "authoritative",
    "workflow truth",
    "case truth",
    "approval truth",
    "approves",
    "approve",
    "execution receipt truth",
    "execution truth",
    "reconciliation truth",
    "detector activation truth",
    "release gate truth",
    "source truth",
    "close cases",
    "case closure",
)


def _coerce_entry(
    entry: EvidenceSourceEntry | Mapping[str, object],
) -> EvidenceSourceEntry:
    if isinstance(entry, EvidenceSourceEntry):
        return entry

    def text_field(key: str) -> str:
        value = entry.get(key, "")
        return str(value).strip() if value is not None else ""

    def tuple_field(key: str) -> tuple[str, ...]:
        value = entry.get(key, ())
        if isinstance(value, str):
            return (value.strip(),) if value.strip() else ()
        if isinstance(value, Iterable):
            return tuple(str(item).strip() for item in value if str(item).strip())
        return ()

    return EvidenceSourceEntry(
        source_id=text_field("source_id"),
        source_type=text_field("source_type"),
        owner=text_field("owner"),
        allowed_target_class=text_field("allowed_target_class"),
        custody_requirements=text_field("custody_requirements"),
        freshness_window=text_field("freshness_window"),
        confidence_posture=text_field("confidence_posture"),
        status=text_field("status"),
        degraded_states=tuple_field("degraded_states"),
        disabled_states=tuple_field("disabled_states"),
        authority_posture=text_field("authority_posture"),
    )


def _has_authority_widening_claim(value: str) -> bool:
    normalized = value.lower().replace("_", " ").replace("-", " ")
    return any(term in normalized for term in _AUTHORITY_WIDENING_TERMS)


PHASE63_EVIDENCE_SOURCE_REGISTRY: dict[str, EvidenceSourceEntry] = {
    "osquery_host_state": EvidenceSourceEntry(
        source_id="osquery_host_state",
        source_type="osquery",
        owner="IT Operations, Information Systems Department",
        allowed_target_class="explicitly_bound_host",
        custody_requirements=(
            "reviewed query id, operator or automation attribution, collection "
            "timestamp, host binding, and AegisOps evidence record id"
        ),
        freshness_window="PT24H",
        confidence_posture="observed_host_state_subordinate_context",
        status="enabled",
        degraded_states=("missing_host_binding", "stale_collection"),
        disabled_states=("disabled_by_policy", "missing_custody"),
    ),
    "malwarebazaar_hash_reputation": EvidenceSourceEntry(
        source_id="malwarebazaar_hash_reputation",
        source_type="malwarebazaar_hash_reputation",
        owner="IT Operations, Information Systems Department",
        allowed_target_class="reviewed_file_hash",
        custody_requirements=(
            "reviewed file hash, enrichment request id, collection timestamp, "
            "response digest, and AegisOps evidence record id"
        ),
        freshness_window="PT6H",
        confidence_posture="external_hash_reputation_subordinate_context",
        status="enabled",
        degraded_states=("stale_reputation", "incomplete_response_digest"),
        disabled_states=("disabled_by_policy", "missing_hash_custody"),
    ),
}


def validate_phase63_evidence_source_entry(
    entry: EvidenceSourceEntry | Mapping[str, object],
) -> EvidenceSourceValidationErrors:
    candidate = _coerce_entry(entry)
    errors: list[str] = []

    if not candidate.source_id:
        errors.append("missing_source_id")
    elif candidate.source_id not in _ALLOWED_SOURCE_IDS:
        errors.append("unsupported_source_id")

    if not candidate.source_type:
        errors.append("missing_source_type")
    elif candidate.source_type not in _ALLOWED_SOURCE_TYPES:
        errors.append("unsupported_source_type")

    if not candidate.owner:
        errors.append("missing_owner")

    if not candidate.allowed_target_class:
        errors.append("missing_allowed_target_class")
    elif candidate.allowed_target_class not in _ALLOWED_TARGET_CLASSES:
        errors.append("unsupported_allowed_target_class")

    if not candidate.custody_requirements:
        errors.append("missing_custody_requirements")

    if not candidate.freshness_window:
        errors.append("missing_freshness_window")
    elif not candidate.freshness_window.startswith("PT"):
        errors.append("freshness_window_not_duration")

    if not candidate.confidence_posture:
        errors.append("missing_confidence_posture")

    if not candidate.status:
        errors.append("missing_status")
    elif candidate.status not in _ALLOWED_STATUSES:
        errors.append("unsupported_status")

    if not candidate.degraded_states:
        errors.append("missing_degraded_states")

    if not candidate.disabled_states:
        errors.append("missing_disabled_states")

    if candidate.authority_posture != _SUBORDINATE_AUTHORITY_POSTURE:
        errors.append("authority_posture_not_subordinate")

    if _has_authority_widening_claim(candidate.confidence_posture):
        errors.append("confidence_posture_promotes_workflow_authority")

    if _has_authority_widening_claim(candidate.custody_requirements):
        errors.append("custody_requirements_promote_workflow_authority")

    return tuple(dict.fromkeys(errors))


def validate_phase63_evidence_source_registry(
    entries: Iterable[EvidenceSourceEntry | Mapping[str, object]],
) -> EvidenceSourceValidationErrors:
    candidates = tuple(_coerce_entry(entry) for entry in entries)
    errors: list[str] = []

    source_ids = {entry.source_id for entry in candidates}
    source_types = {entry.source_type for entry in candidates}
    if source_ids != _ALLOWED_SOURCE_IDS:
        errors.append("registry_source_ids_not_bounded")
    if source_types != _ALLOWED_SOURCE_TYPES:
        errors.append("registry_source_types_not_bounded")
    if len(candidates) != len(_ALLOWED_SOURCE_IDS):
        errors.append("broad_or_default_source_list")

    for entry in candidates:
        errors.extend(validate_phase63_evidence_source_entry(entry))

    return tuple(dict.fromkeys(errors))


def validate_phase63_evidence_source_use(
    entry: EvidenceSourceEntry | Mapping[str, object],
    *,
    target_class: str,
) -> EvidenceSourceValidationErrors:
    candidate = _coerce_entry(entry)
    errors = list(validate_phase63_evidence_source_entry(candidate))

    if candidate.status == "disabled":
        errors.append("source_disabled")
    if candidate.status == "degraded":
        errors.append("source_degraded")
    if target_class != candidate.allowed_target_class:
        errors.append("target_class_not_allowed")

    return tuple(dict.fromkeys(errors))
