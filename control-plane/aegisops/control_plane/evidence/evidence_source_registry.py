from __future__ import annotations

import re
from typing import Iterable, Mapping

from .evidence_source_registry_data import (
    PHASE63_EVIDENCE_SOURCE_REGISTRY,
    EvidenceSourceEntry,
    EvidenceSourceValidationErrors,
    _ALLOWED_SOURCE_IDS,
    _ALLOWED_SOURCE_TYPES,
    _ALLOWED_STATUSES,
    _ALLOWED_TARGET_CLASSES,
    _ENTRY_FIELD_NAMES,
    _REQUIRED_SOURCE_PROFILES,
    _SUBORDINATE_AUTHORITY_POSTURE,
)
from .evidence_source_validation_catalog import (
    _MALFORMED_REGISTRY_ENTRY_ERROR,
    _SCALAR_FIELD_TYPE_ERROR_CODES,
    _SCALAR_FIELD_WHITESPACE_ERROR_CODES,
    _STATE_LIST_BLANK_ENTRY_ERROR_CODES,
    _STATE_LIST_FIELD_ERROR_CODES,
    _STATE_LIST_WHITESPACE_ENTRY_ERROR_CODES,
    _authority_widening_field_errors,
    _broad_or_default_source_errors,
    _contains_all_required_custody_terms,
    _contains_negated_required_custody_term,
    _has_authority_widening_claim,
    _has_broad_or_default_source_claim,
    _normalize_boundary_text,
)

_FRESHNESS_WINDOW_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


def _coerce_entry(
    entry: EvidenceSourceEntry | Mapping[str, object] | object,
) -> EvidenceSourceEntry:
    if isinstance(entry, EvidenceSourceEntry):
        return entry
    if not isinstance(entry, Mapping):
        entry = {}

    def text_field(key: str, default: str = "") -> str:
        value = entry.get(key, default)
        return str(value) if value is not None else ""

    def tuple_field(key: str) -> tuple[str, ...]:
        value = entry.get(key, ())
        if isinstance(value, str):
            return (value.strip(),) if value.strip() else ()
        if not isinstance(value, Iterable) or isinstance(value, Mapping):
            return ()
        coerced_items = tuple(str(item).strip() for item in value)
        return coerced_items

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
    entry: EvidenceSourceEntry | Mapping[str, object] | object,
) -> list[str]:
    if isinstance(entry, EvidenceSourceEntry):
        return []
    if not isinstance(entry, Mapping):
        return [_MALFORMED_REGISTRY_ENTRY_ERROR]
    unknown_fields = frozenset(str(key) for key in entry) - _ENTRY_FIELD_NAMES
    return ["unknown_registry_entry_field"] if unknown_fields else []


def _state_list_shape_errors(
    entry: EvidenceSourceEntry | Mapping[str, object] | object,
) -> list[str]:
    if isinstance(entry, EvidenceSourceEntry):
        return []
    if not isinstance(entry, Mapping):
        return []
    errors: list[str] = []
    for field_name, error_code in _STATE_LIST_FIELD_ERROR_CODES.items():
        value = entry.get(field_name)
        if isinstance(value, Mapping):
            errors.append(error_code)
            continue
        if (
            value is not None
            and not isinstance(value, str)
            and isinstance(value, Iterable)
        ):
            has_blank_item = False
            has_whitespace_drift = False
            for item in value:
                item_text = str(item) if item is not None else ""
                stripped_item = item_text.strip()
                if not stripped_item:
                    has_blank_item = True
                elif isinstance(item, str) and item_text != stripped_item:
                    has_whitespace_drift = True
            if has_blank_item:
                errors.append(_STATE_LIST_BLANK_ENTRY_ERROR_CODES[field_name])
            if has_whitespace_drift:
                errors.append(_STATE_LIST_WHITESPACE_ENTRY_ERROR_CODES[field_name])
    return errors


def _scalar_field_whitespace_errors(
    entry: EvidenceSourceEntry | Mapping[str, object] | object,
) -> list[str]:
    if isinstance(entry, EvidenceSourceEntry):
        return []
    if not isinstance(entry, Mapping):
        return []
    errors: list[str] = []
    field_error_codes = _SCALAR_FIELD_WHITESPACE_ERROR_CODES.items()
    for field_name, error_code in field_error_codes:
        value = entry.get(field_name)
        if isinstance(value, str) and value != value.strip():
            errors.append(error_code)
    return errors


def _scalar_field_shape_errors(
    entry: EvidenceSourceEntry | Mapping[str, object] | object,
) -> list[str]:
    if isinstance(entry, EvidenceSourceEntry):
        return []
    if not isinstance(entry, Mapping):
        return []
    errors: list[str] = []
    for field_name, error_code in _SCALAR_FIELD_TYPE_ERROR_CODES.items():
        value = entry.get(field_name)
        if value is not None and not isinstance(value, str):
            errors.append(error_code)
    return errors


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
    status_error: str,
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
        ("status", status_error),
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
            status_error="registry_key_status_mismatch",
            degraded_states_error="registry_key_degraded_states_mismatch",
            disabled_states_error="registry_key_disabled_states_mismatch",
            custody_requirements_error="registry_key_custody_requirements_mismatch",
        )
    )
    return errors


def validate_phase63_evidence_source_entry(
    entry: EvidenceSourceEntry | Mapping[str, object],
) -> EvidenceSourceValidationErrors:
    raw_errors = _unknown_mapping_field_errors(entry)
    raw_errors.extend(_state_list_shape_errors(entry))
    raw_errors.extend(_scalar_field_shape_errors(entry))
    raw_errors.extend(_scalar_field_whitespace_errors(entry))
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
            status_error="source_identity_status_mismatch",
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
