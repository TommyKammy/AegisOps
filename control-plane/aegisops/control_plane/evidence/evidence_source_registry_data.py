from __future__ import annotations

from dataclasses import dataclass


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


_ENTRY_FIELD_NAMES = frozenset(EvidenceSourceEntry.__dataclass_fields__)
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

_OSQUERY_REQUIRED_CUSTODY_TERMS = (
    "reviewed query id",
    "operator or automation attribution",
    "collection timestamp",
    "host binding",
    "AegisOps evidence record id",
)
_MALWAREBAZAAR_REQUIRED_CUSTODY_TERMS = (
    "reviewed file hash",
    "enrichment request id",
    "collection timestamp",
    "response digest",
    "AegisOps evidence record id",
)
_REQUIRED_SOURCE_PROFILES = {
    "osquery_host_state": {
        "source_type": "osquery",
        "owner": "IT Operations, Information Systems Department",
        "allowed_target_class": "explicitly_bound_host",
        "freshness_window": "PT24H",
        "confidence_posture": "observed_host_state_subordinate_context",
        "status": "enabled",
        "degraded_states": ("missing_host_binding", "stale_collection"),
        "disabled_states": ("disabled_by_policy", "missing_custody"),
        "custody_terms": _OSQUERY_REQUIRED_CUSTODY_TERMS,
    },
    "malwarebazaar_hash_reputation": {
        "source_type": "malwarebazaar_hash_reputation",
        "owner": "IT Operations, Information Systems Department",
        "allowed_target_class": "reviewed_file_hash",
        "freshness_window": "PT6H",
        "confidence_posture": "external_hash_reputation_subordinate_context",
        "status": "enabled",
        "degraded_states": (
            "stale_reputation",
            "incomplete_response_digest",
            "conflicting_enrichment",
        ),
        "disabled_states": ("disabled_by_policy", "missing_hash_custody"),
        "custody_terms": _MALWAREBAZAAR_REQUIRED_CUSTODY_TERMS,
    },
}


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
        degraded_states=(
            "stale_reputation",
            "incomplete_response_digest",
            "conflicting_enrichment",
        ),
        disabled_states=("disabled_by_policy", "missing_hash_custody"),
    ),
}
