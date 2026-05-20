from __future__ import annotations

import re
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
_FRESHNESS_WINDOW_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)

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
        "degraded_states": ("stale_reputation", "incomplete_response_digest"),
        "disabled_states": ("disabled_by_policy", "missing_hash_custody"),
        "custody_terms": _MALWAREBAZAAR_REQUIRED_CUSTODY_TERMS,
    },
}


def _normalize_boundary_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _collapse_spelled_out_tokens(normalized_value: str) -> str:
    tokens = normalized_value.split()
    collapsed_tokens: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        if len(token) != 1 or not token.isalnum():
            collapsed_tokens.append(token)
            index += 1
            continue

        run_end = index
        while run_end < len(tokens) and len(tokens[run_end]) == 1 and tokens[run_end].isalnum():
            run_end += 1
        run_tokens = tokens[index:run_end]
        collapsed_tokens.append("".join(run_tokens) if len(run_tokens) > 1 else token)
        index = run_end
    return " ".join(collapsed_tokens)


def _normalized_boundary_text_variants(value: str) -> tuple[str, ...]:
    normalized = _normalize_boundary_text(value)
    collapsed = _collapse_spelled_out_tokens(normalized)
    if collapsed == normalized:
        return (normalized,)
    return (normalized, collapsed)


_PROHIBITED_RECORD_TRUTH_CLAIMS = (
    "alert_truth",
    "case_truth",
    "source_truth",
    "source of truth",
    "sources of truth",
    "evidence_truth",
    "evidence_request_truth",
    "audit_truth",
)
_PROHIBITED_ACTION_TRUTH_CLAIMS = (
    "approval_truth",
    "action_request_truth",
    "receipt_truth",
    "execution_receipt_truth",
    "execution_truth",
    "reconciliation_truth",
    "detector_activation_truth",
)
_READINESS_TRUTH_CLAIM = "readiness_truth"
_PROHIBITED_CLOSEOUT_TRUTH_CLAIMS = (
    "release_truth",
    "release_gate_truth",
    "gate_truth",
    "limitation_truth",
    "closeout_truth",
    "closeout_state_truth",
    _READINESS_TRUTH_CLAIM,
)
_PROHIBITED_ENVIRONMENT_TRUTH_CLAIMS = (
    "production_truth",
)
_PROHIBITED_WORKFLOW_TRUTH_CLAIMS = (
    *_PROHIBITED_RECORD_TRUTH_CLAIMS,
    *_PROHIBITED_ACTION_TRUTH_CLAIMS,
    *_PROHIBITED_CLOSEOUT_TRUTH_CLAIMS,
)
_DETECTOR_ACTIVATION_AUTHORITY_TERMS = (
    "activate detector",
    "activate detectors",
    "activate a detector",
    "activate the detector",
    "activates detector",
    "activates detectors",
    "activates a detector",
    "activates the detector",
    "activated detector",
    "activated detectors",
    "activated a detector",
    "activated the detector",
    "activating detector",
    "activating detectors",
    "activating a detector",
    "activating the detector",
    "detector activation",
    "detector activations",
    "detector activated",
    "detectors activated",
)
_ALERT_ADMISSION_AUTHORITY_TERMS = (
    "admitted alert",
    "admitted alerts",
    "admit alert",
    "admit alerts",
    "admits alert",
    "admits alerts",
    "admitting alert",
    "admitting alerts",
    "alert admission",
)
_REQUEST_AUTHORITY_TERMS = (
    "evidence request",
    "evidence requests",
    "action request",
    "action requests",
)
_APPROVAL_AUTHORITY_TERMS = (
    "approval",
    "approvals",
    "approved",
    "approves",
    "approve",
    "approving",
)
_EXECUTION_AUTHORITY_TERMS = (
    "executed",
    "execute",
    "executes",
    "executing",
)
_RECONCILIATION_AUTHORITY_TERMS = (
    "reconciled",
    "reconcile",
    "reconciles",
    "reconciling",
    "reconciliation owner",
    "reconciliation owners",
    "reconciliation ownership",
)
_CLOSURE_AUTHORITY_TERMS = (
    "closed",
    "close",
    "closes",
    "closing",
)
_RECORD_OWNER_AUTHORITY_TERMS = (
    "alert owner",
    "alert owners",
    "alert ownership",
    "case owner",
    "case owners",
    "case ownership",
    "evidence owner",
    "evidence owners",
    "evidence ownership",
    "approval owner",
    "approval owners",
    "approval ownership",
    "action request owner",
    "action request owners",
    "action request ownership",
    "execution receipt owner",
    "execution receipt owners",
    "execution receipt ownership",
    "audit owner",
    "audit owners",
    "audit ownership",
    "release owner",
    "release owners",
    "release ownership",
    "gate owner",
    "gate owners",
    "gate ownership",
    "closeout owner",
    "closeout owners",
    "closeout ownership",
)
_AUTHORITY_WIDENING_TERMS = (
    "authoritative",
    "workflow authority",
    "workflow truth",
    *_ALERT_ADMISSION_AUTHORITY_TERMS,
    *_REQUEST_AUTHORITY_TERMS,
    *_APPROVAL_AUTHORITY_TERMS,
    *_EXECUTION_AUTHORITY_TERMS,
    *_RECONCILIATION_AUTHORITY_TERMS,
    *_CLOSURE_AUTHORITY_TERMS,
    *_DETECTOR_ACTIVATION_AUTHORITY_TERMS,
    *_RECORD_OWNER_AUTHORITY_TERMS,
    "execution receipt",
    "execution receipts",
    "release gate",
    "release gates",
    "gate release",
    "gate releases",
    "limitation",
    "limitations",
    "closeout state",
    "claim readiness",
    "claims readiness",
    "claimed readiness",
    "claiming readiness",
    "readiness claim",
    "readiness claims",
    "readiness claimed",
    "close cases",
    "case closure",
    *_PROHIBITED_WORKFLOW_TRUTH_CLAIMS,
    *_PROHIBITED_ENVIRONMENT_TRUTH_CLAIMS,
)
_NORMALIZED_AUTHORITY_WIDENING_TERMS = tuple(
    _normalize_boundary_text(term) for term in _AUTHORITY_WIDENING_TERMS
)
_DEFERRED_EVIDENCE_SOURCE_TERMS = (
    "Velociraptor",
    "YARA",
    "capa",
    "MISP",
    "Suricata",
    "IntelOwl",
)
_BROAD_OR_DEFAULT_SOURCE_TERMS = (
    *_DEFERRED_EVIDENCE_SOURCE_TERMS,
    "default evidence source list",
    "default evidence source lists",
    "evidence source marketplace",
    "evidence source marketplaces",
    "public internet pivot",
    "public internet pivots",
)
_NORMALIZED_BROAD_OR_DEFAULT_SOURCE_TERMS = tuple(
    _normalize_boundary_text(term) for term in _BROAD_OR_DEFAULT_SOURCE_TERMS
)
_NORMALIZED_BROAD_SOURCE_ALIASES = tuple(
    alias
    for alias in (
        "m i s p",
        "y a r a",
        "c a p a",
        "intel owl",
    )
)
_AUTHORITY_FIELD_ERROR_CODES = {
    "source_id": "source_id_promotes_workflow_authority",
    "source_type": "source_type_promotes_workflow_authority",
    "owner": "owner_promotes_workflow_authority",
    "allowed_target_class": "allowed_target_class_promotes_workflow_authority",
    "custody_requirements": "custody_requirements_promote_workflow_authority",
    "freshness_window": "freshness_window_promotes_workflow_authority",
    "confidence_posture": "confidence_posture_promotes_workflow_authority",
    "status": "status_promotes_workflow_authority",
    "authority_posture": "authority_posture_promotes_workflow_authority",
    "degraded_states": "degraded_states_promotes_workflow_authority",
    "disabled_states": "disabled_states_promotes_workflow_authority",
}
_STATE_LIST_FIELD_ERROR_CODES = {
    "degraded_states": "degraded_states_not_sequence",
    "disabled_states": "disabled_states_not_sequence",
}
_SOURCE_IDENTITY_FIELD_WHITESPACE_ERROR_CODES = {
    "source_id": "source_id_whitespace_drift",
    "source_type": "source_type_whitespace_drift",
}
_NEGATED_REQUIRED_CUSTODY_PREFIXES = ("missing", "not", "no", "without")
_NEGATED_REQUIRED_CUSTODY_PREFIX_FILLERS = (
    "a",
    "an",
    "the",
    "any",
    "currently",
    "longer",
    "yet",
)
_NEGATED_REQUIRED_CUSTODY_SUFFIXES = (
    "absent",
    "missing",
    "not available",
    "not present",
    "not reviewed",
    "not verified",
    "omitted",
    "unavailable",
    "unverified",
)
_NEGATED_REQUIRED_CUSTODY_LINKING_VERBS = ("is", "are", "was", "were")
_NEGATED_REQUIRED_CUSTODY_CONTRACTIONS = ("isn t", "aren t", "wasn t", "weren t")
_NEGATED_REQUIRED_CUSTODY_CONTRACTED_STATES = (
    "available",
    "present",
    "reviewed",
    "verified",
)
_NEGATED_REQUIRED_CUSTODY_SUFFIX_MODIFIERS = ("currently", "longer")


def _coerce_entry(
    entry: EvidenceSourceEntry | Mapping[str, object],
) -> EvidenceSourceEntry:
    if isinstance(entry, EvidenceSourceEntry):
        return entry

    def text_field(key: str, default: str = "") -> str:
        value = entry.get(key, default)
        return str(value).strip() if value is not None else ""

    def tuple_field(key: str) -> tuple[str, ...]:
        value = entry.get(key, ())
        if isinstance(value, str):
            return (value.strip(),) if value.strip() else ()
        if not isinstance(value, Iterable) or isinstance(value, Mapping):
            return ()
        coerced_items = tuple(str(item).strip() for item in value)
        return tuple(item for item in coerced_items if item)

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
        authority_posture=text_field(
            "authority_posture", _SUBORDINATE_AUTHORITY_POSTURE
        ),
    )


def _unknown_mapping_field_errors(
    entry: EvidenceSourceEntry | Mapping[str, object],
) -> list[str]:
    if isinstance(entry, EvidenceSourceEntry):
        return []
    unknown_fields = frozenset(str(key) for key in entry) - _ENTRY_FIELD_NAMES
    return ["unknown_registry_entry_field"] if unknown_fields else []


def _state_list_shape_errors(
    entry: EvidenceSourceEntry | Mapping[str, object],
) -> list[str]:
    if isinstance(entry, EvidenceSourceEntry):
        return []
    errors: list[str] = []
    for field_name, error_code in _STATE_LIST_FIELD_ERROR_CODES.items():
        if isinstance(entry.get(field_name), Mapping):
            errors.append(error_code)
    return errors


def _source_identity_whitespace_errors(
    entry: EvidenceSourceEntry | Mapping[str, object],
) -> list[str]:
    if isinstance(entry, EvidenceSourceEntry):
        return []
    errors: list[str] = []
    field_error_codes = _SOURCE_IDENTITY_FIELD_WHITESPACE_ERROR_CODES.items()
    for field_name, error_code in field_error_codes:
        value = entry.get(field_name)
        if isinstance(value, str) and value != value.strip():
            errors.append(error_code)
    return errors


def _has_authority_widening_claim(value: str) -> bool:
    normalized_variants = tuple(
        f" {normalized} " for normalized in _normalized_boundary_text_variants(value)
    )
    return any(
        f" {term} " in normalized
        for normalized in normalized_variants
        for term in _NORMALIZED_AUTHORITY_WIDENING_TERMS
    )


def _has_broad_or_default_source_claim(value: str) -> bool:
    normalized_variants = tuple(
        f" {normalized} " for normalized in _normalized_boundary_text_variants(value)
    )
    return any(
        f" {term} " in normalized
        for normalized in normalized_variants
        for term in _NORMALIZED_BROAD_OR_DEFAULT_SOURCE_TERMS
    ) or any(
        f" {alias} " in normalized
        for normalized in normalized_variants
        for alias in _NORMALIZED_BROAD_SOURCE_ALIASES
    )


def _authority_widening_field_errors(entry: EvidenceSourceEntry) -> list[str]:
    scalar_fields = (
        "source_id",
        "source_type",
        "owner",
        "allowed_target_class",
        "custody_requirements",
        "freshness_window",
        "confidence_posture",
        "status",
        "authority_posture",
    )
    sequence_fields = ("degraded_states", "disabled_states")

    errors: list[str] = []
    for field_name in scalar_fields:
        if _has_authority_widening_claim(str(getattr(entry, field_name))):
            errors.append(_AUTHORITY_FIELD_ERROR_CODES[field_name])
    for field_name in sequence_fields:
        if any(
            _has_authority_widening_claim(value)
            for value in getattr(entry, field_name)
        ):
            errors.append(_AUTHORITY_FIELD_ERROR_CODES[field_name])
    return errors


def _entry_text_values(entry: EvidenceSourceEntry) -> tuple[str, ...]:
    return (
        entry.source_id,
        entry.source_type,
        entry.owner,
        entry.allowed_target_class,
        entry.custody_requirements,
        entry.freshness_window,
        entry.confidence_posture,
        entry.status,
        entry.authority_posture,
        *entry.degraded_states,
        *entry.disabled_states,
    )


def _broad_or_default_source_errors(entry: EvidenceSourceEntry) -> list[str]:
    if any(_has_broad_or_default_source_claim(value) for value in _entry_text_values(entry)):
        return ["unsupported_broad_source_reference"]
    return []


def _contains_required_custody_term(
    bounded_custody_text: str,
    required_custody_term: str,
) -> bool:
    return f" {required_custody_term} " in bounded_custody_text


def _contains_negated_required_custody_term(
    bounded_custody_text: str,
    required_custody_terms: tuple[str, ...],
) -> bool:
    custody_tokens = bounded_custody_text.split()
    prefix_tokens = frozenset(_NEGATED_REQUIRED_CUSTODY_PREFIXES)
    filler_tokens = frozenset(_NEGATED_REQUIRED_CUSTODY_PREFIX_FILLERS)

    suffix_sequences = tuple(
        tuple(_normalize_boundary_text(suffix).split())
        for suffix in _NEGATED_REQUIRED_CUSTODY_SUFFIXES
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{verb} {suffix}").split())
        for verb in _NEGATED_REQUIRED_CUSTODY_LINKING_VERBS
        for suffix in _NEGATED_REQUIRED_CUSTODY_SUFFIXES
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{contraction} {state}").split())
        for contraction in _NEGATED_REQUIRED_CUSTODY_CONTRACTIONS
        for state in _NEGATED_REQUIRED_CUSTODY_CONTRACTED_STATES
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{verb} no {modifier} available").split())
        for verb in _NEGATED_REQUIRED_CUSTODY_LINKING_VERBS
        for modifier in _NEGATED_REQUIRED_CUSTODY_SUFFIX_MODIFIERS
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{verb} {modifier} {suffix}").split())
        for verb in _NEGATED_REQUIRED_CUSTODY_LINKING_VERBS
        for modifier in _NEGATED_REQUIRED_CUSTODY_SUFFIX_MODIFIERS
        for suffix in _NEGATED_REQUIRED_CUSTODY_SUFFIXES
    )
    suffix_sequences += tuple(
        tuple(_normalize_boundary_text(f"{verb} no {modifier} {state}").split())
        for verb in _NEGATED_REQUIRED_CUSTODY_LINKING_VERBS
        for modifier in _NEGATED_REQUIRED_CUSTODY_SUFFIX_MODIFIERS
        for state in _NEGATED_REQUIRED_CUSTODY_CONTRACTED_STATES
    )

    for required_term in required_custody_terms:
        term_tokens = required_term.split()
        term_size = len(term_tokens)
        if not term_size:
            continue
        max_start = len(custody_tokens) - term_size
        for start in range(max_start + 1):
            end = start + term_size
            if tuple(custody_tokens[start:end]) != tuple(term_tokens):
                continue

            prefix_window = tuple(custody_tokens[max(0, start - 6) : start])
            for index, token in enumerate(prefix_window):
                if token in prefix_tokens and all(
                    trailing_token in filler_tokens
                    for trailing_token in prefix_window[index + 1 :]
                ):
                    return True

            trailing_tokens = tuple(custody_tokens[end : end + 6])
            if any(
                trailing_tokens[: len(sequence)] == sequence
                for sequence in suffix_sequences
            ):
                return True
    return False


def _contains_all_required_custody_terms(
    bounded_custody_text: str,
    required_custody_terms: tuple[str, ...],
) -> bool:
    return all(
        _contains_required_custody_term(bounded_custody_text, term)
        for term in required_custody_terms
    )


def _is_positive_time_duration(value: str) -> bool:
    match = _FRESHNESS_WINDOW_PATTERN.fullmatch(value)
    if not match:
        return False
    parts = [int(part) for part in match.groups(default="0")]
    return any(part > 0 for part in parts)


def _same_bounded_state_set(
    candidate_states: object,
    required_states: object,
) -> bool:
    if not isinstance(candidate_states, tuple) or not isinstance(required_states, tuple):
        return False
    return (
        len(candidate_states) == len(required_states)
        and frozenset(candidate_states) == frozenset(required_states)
    )


def _profile_field_matches(
    field_name: str,
    actual_value: object,
    required_value: object,
) -> bool:
    if field_name in {"degraded_states", "disabled_states"}:
        return _same_bounded_state_set(
            actual_value,
            required_value,
        )
    return actual_value == required_value


def _required_source_profile_errors(
    source_id: str,
    entry: EvidenceSourceEntry,
    *,
    source_type_error: str,
    owner_error: str,
    target_class_error: str,
    freshness_window_error: str,
    confidence_posture_error: str,
    degraded_states_error: str,
    disabled_states_error: str,
    custody_requirements_error: str,
) -> list[str]:
    required_profile = _REQUIRED_SOURCE_PROFILES.get(source_id)
    if required_profile is None:
        return []

    errors: list[str] = []
    profile_bound_fields = (
        ("source_type", source_type_error),
        ("owner", owner_error),
        ("allowed_target_class", target_class_error),
        ("freshness_window", freshness_window_error),
        ("confidence_posture", confidence_posture_error),
        ("degraded_states", degraded_states_error),
        ("disabled_states", disabled_states_error),
    )
    for field_name, error_code in profile_bound_fields:
        actual_value = getattr(entry, field_name)
        required_value = required_profile[field_name]
        if not _profile_field_matches(field_name, actual_value, required_value):
            errors.append(error_code)

    custody_text = _normalize_boundary_text(entry.custody_requirements)
    required_custody_terms = tuple(
        _normalize_boundary_text(term)
        for term in required_profile["custody_terms"]
    )
    bounded_custody_text = f" {custody_text} "
    has_disallowed_custody_negation = _contains_negated_required_custody_term(
        bounded_custody_text,
        required_custody_terms,
    )
    has_required_custody_terms = _contains_all_required_custody_terms(
        bounded_custody_text,
        required_custody_terms,
    )
    if has_disallowed_custody_negation or not has_required_custody_terms:
        errors.append(custody_requirements_error)
    return errors


def _registry_key_profile_errors(
    registry_key: str,
    entry: EvidenceSourceEntry,
) -> list[str]:
    errors: list[str] = []
    if registry_key != entry.source_id:
        errors.append("registry_key_entry_source_id_mismatch")
    errors.extend(
        _required_source_profile_errors(
            registry_key,
            entry,
            source_type_error="registry_key_source_type_mismatch",
            owner_error="registry_key_owner_mismatch",
            target_class_error="registry_key_target_class_mismatch",
            freshness_window_error="registry_key_freshness_window_mismatch",
            confidence_posture_error="registry_key_confidence_posture_mismatch",
            degraded_states_error="registry_key_degraded_states_mismatch",
            disabled_states_error="registry_key_disabled_states_mismatch",
            custody_requirements_error="registry_key_custody_requirements_mismatch",
        )
    )
    return errors


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
    raw_errors = _unknown_mapping_field_errors(entry)
    raw_errors.extend(_state_list_shape_errors(entry))
    raw_errors.extend(_source_identity_whitespace_errors(entry))
    candidate = _coerce_entry(entry)
    errors: list[str] = list(raw_errors)

    if not candidate.source_id:
        errors.append("missing_source_id")
    elif candidate.source_id not in _ALLOWED_SOURCE_IDS:
        errors.append("unsupported_source_id")

    if not candidate.source_type:
        errors.append("missing_source_type")
    elif candidate.source_type not in _ALLOWED_SOURCE_TYPES:
        errors.append("unsupported_source_type")

    errors.extend(
        _required_source_profile_errors(
            candidate.source_id,
            candidate,
            source_type_error="source_identity_type_mismatch",
            owner_error="source_identity_owner_mismatch",
            target_class_error="source_identity_target_class_mismatch",
            freshness_window_error="source_identity_freshness_window_mismatch",
            confidence_posture_error="source_identity_confidence_posture_mismatch",
            degraded_states_error="source_identity_degraded_states_mismatch",
            disabled_states_error="source_identity_disabled_states_mismatch",
            custody_requirements_error="source_identity_custody_requirements_mismatch",
        )
    )

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
    elif not _is_positive_time_duration(candidate.freshness_window):
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

    errors.extend(_authority_widening_field_errors(candidate))
    errors.extend(_broad_or_default_source_errors(candidate))

    return tuple(dict.fromkeys(errors))


def validate_phase63_evidence_source_registry(
    entries: (
        Iterable[EvidenceSourceEntry | Mapping[str, object]]
        | Mapping[str, EvidenceSourceEntry | Mapping[str, object]]
    ),
) -> EvidenceSourceValidationErrors:
    registry_keys: tuple[str, ...] = ()
    if isinstance(entries, Mapping):
        keyed_entries = tuple(
            (str(source_id), entry, _coerce_entry(entry))
            for source_id, entry in entries.items()
        )
        registry_keys = tuple(source_id for source_id, _, _ in keyed_entries)
        raw_candidates = tuple(entry for _, entry, _ in keyed_entries)
        candidates = tuple(entry for _, _, entry in keyed_entries)
    else:
        keyed_entries = ()
        raw_candidates = tuple(entries)
        candidates = tuple(_coerce_entry(entry) for entry in raw_candidates)
    errors: list[str] = []

    source_ids = {entry.source_id for entry in candidates}
    if registry_keys and set(registry_keys) != source_ids:
        errors.append("registry_key_source_id_mismatch")
    for registry_key, _, entry in keyed_entries:
        errors.extend(_registry_key_profile_errors(registry_key, entry))
    if source_ids != _ALLOWED_SOURCE_IDS:
        errors.append("registry_source_ids_not_bounded")
    if len(candidates) != len(_ALLOWED_SOURCE_IDS):
        errors.append("broad_or_default_source_list")

    for entry in raw_candidates:
        errors.extend(validate_phase63_evidence_source_entry(entry))

    return tuple(dict.fromkeys(errors))


def validate_phase63_evidence_source_use(
    entry: EvidenceSourceEntry | Mapping[str, object],
    *,
    target_class: str,
) -> EvidenceSourceValidationErrors:
    errors = list(validate_phase63_evidence_source_entry(entry))
    candidate = _coerce_entry(entry)

    if candidate.status == "disabled":
        errors.append("source_disabled")
    if candidate.status == "degraded":
        errors.append("source_degraded")
    if target_class != candidate.allowed_target_class:
        errors.append("target_class_not_allowed")

    return tuple(dict.fromkeys(errors))
