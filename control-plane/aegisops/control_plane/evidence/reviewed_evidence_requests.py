from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
import re
from types import MappingProxyType
from typing import ClassVar, Iterable, Mapping

from .evidence_source_registry import (
    PHASE63_EVIDENCE_SOURCE_REGISTRY,
    _has_authority_widening_claim as _registry_has_authority_widening_claim,
    validate_phase63_evidence_source_use,
)


ReviewedEvidenceRequestValidationErrors = tuple[str, ...]


_DURATION_PATTERN = re.compile(
    r"^PT(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?$"
)


def _freeze_json_value(value: object) -> object:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze_json_value(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_json_value(item) for item in value)
    return value


def _freeze_mapping(value: Mapping[str, object]) -> Mapping[str, object]:
    frozen = _freeze_json_value(value)
    if not isinstance(frozen, Mapping):
        raise TypeError("Expected mapping-compatible reviewed evidence request field")
    return frozen


@dataclass(frozen=True)
class ReviewedEvidenceRequestRecord:
    record_family: ClassVar[str] = "reviewed_evidence_request"
    identifier_field: ClassVar[str] = "evidence_request_id"

    evidence_request_id: str
    case_id: str
    requester_identity: str
    requester_role: str
    target: Mapping[str, object]
    source_id: str
    requested_scope: str
    custody: Mapping[str, object]
    authorization: Mapping[str, object]
    linked_case_context: Mapping[str, object]
    requested_at: datetime
    expires_at: datetime
    lifecycle_state: str
    authority_posture: str
    source_status: Mapping[str, object] | None = None

    @property
    def record_id(self) -> str:
        return self.evidence_request_id

    def __post_init__(self) -> None:
        object.__setattr__(self, "target", _freeze_mapping(self.target))
        object.__setattr__(self, "custody", _freeze_mapping(self.custody))
        object.__setattr__(self, "authorization", _freeze_mapping(self.authorization))
        object.__setattr__(
            self,
            "linked_case_context",
            _freeze_mapping(self.linked_case_context),
        )
        object.__setattr__(
            self,
            "source_status",
            _freeze_mapping(self.source_status or {}),
        )

    def with_updates(self, **updates: object) -> "ReviewedEvidenceRequestRecord":
        return replace(self, **updates)


_AUTHORIZED_REQUESTER_ROLES = frozenset(
    {
        "security_analyst",
        "incident_responder",
        "evidence_reviewer",
    }
)
_ALLOWED_LIFECYCLE_STATES = frozenset(
    {
        "reviewed",
        "approved",
        "active",
        "completed",
        "expired",
        "denied",
        "cancelled",
    }
)
_ACTIVE_LIFECYCLE_STATES = frozenset({"reviewed", "approved", "active"})
_SUBORDINATE_AUTHORITY_POSTURE = (
    "aegisops_owned_workflow_context_subordinate_evidence_output"
)
_TARGET_CLASS_BY_SOURCE_ID = {
    "osquery_host_state": "explicitly_bound_host",
    "malwarebazaar_hash_reputation": "reviewed_file_hash",
}
_REQUIRED_TARGET_FIELDS_BY_CLASS = {
    "explicitly_bound_host": ("target_class", "host_identifier", "case_id"),
    "reviewed_file_hash": ("target_class", "file_hash", "case_id"),
}
_REQUIRED_CUSTODY_FIELDS = (
    "reviewed_by",
    "custody_owner",
    "custody_reference",
    "provenance_chain",
)
_REQUIRED_AUTHORIZATION_TEXT_FIELDS = ("reviewed_scope", "decision_id")
_REQUIRED_CASE_CONTEXT_FIELDS = (
    "case_id",
    "admitting_evidence_id",
    "reviewed_context_id",
)
_TERMINAL_SOURCE_STATUSES = frozenset({"denied", "disabled"})
_STALE_SOURCE_STATUSES = frozenset({"stale", "degraded"})
_SOURCE_AUTHORITY_STATUSES = frozenset({"authoritative", "source_truth"})
_APPROVED_INVENTORY_SCOPE_PHRASES = (
    "approved software inventory",
    "approved software state",
    "approved software",
)


def _normalize_text(value: object) -> str:
    split_camel_case = re.sub(r"(?<=[a-z0-9])(?=[A-Z])", " ", str(value))
    return re.sub(r"[^a-z0-9]+", " ", split_camel_case.lower()).strip()


def _authority_scan_text(value: object) -> str:
    normalized_value = _normalize_text(value)
    for phrase in _APPROVED_INVENTORY_SCOPE_PHRASES:
        normalized_phrase = _normalize_text(phrase)
        normalized_value = re.sub(
            rf"\b{re.escape(normalized_phrase)}\b",
            "software inventory",
            normalized_value,
        )
    return normalized_value


def _contains_authority_widening_claim(value: object) -> bool:
    return _registry_has_authority_widening_claim(_authority_scan_text(value))


def _non_empty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _mapping_has_non_empty_fields(
    value: Mapping[str, object],
    required_fields: tuple[str, ...],
) -> bool:
    return all(_non_empty_string(value.get(field_name)) for field_name in required_fields)


def _is_aware_datetime(value: object) -> bool:
    return (
        isinstance(value, datetime)
        and value.tzinfo is not None
        and value.utcoffset() is not None
    )


def _is_active_lifecycle_state(value: object) -> bool:
    return value in _ACTIVE_LIFECYCLE_STATES


def _reviewed_scope_promotes_workflow_truth(value: object) -> bool:
    return _non_empty_string(value) and _contains_authority_widening_claim(value)


def _reviewed_scope_errors(
    request: ReviewedEvidenceRequestRecord,
) -> ReviewedEvidenceRequestValidationErrors:
    if not _non_empty_string(request.requested_scope):
        return ("missing_reviewed_scope",)
    if _reviewed_scope_promotes_workflow_truth(request.requested_scope):
        return ("requested_scope_promotes_workflow_truth",)
    return ()


def _same_request_subject(
    left: ReviewedEvidenceRequestRecord,
    right: ReviewedEvidenceRequestRecord,
) -> bool:
    return (
        left.case_id == right.case_id
        and left.source_id == right.source_id
        and _target_binding(left.target) == _target_binding(right.target)
        and left.requested_scope == right.requested_scope
    )


def _target_binding(target: Mapping[str, object]) -> tuple[tuple[str, object], ...]:
    target_class = str(target.get("target_class", ""))
    binding_fields = _REQUIRED_TARGET_FIELDS_BY_CLASS.get(target_class)
    if binding_fields is None:
        return tuple(sorted(target.items()))
    return tuple((field_name, target.get(field_name)) for field_name in binding_fields)


def _same_request_binding(
    left: ReviewedEvidenceRequestRecord,
    right: ReviewedEvidenceRequestRecord,
) -> bool:
    return (
        _same_request_subject(left, right)
        and left.requester_identity == right.requester_identity
        and left.requester_role == right.requester_role
        and dict(left.custody) == dict(right.custody)
        and dict(left.authorization) == dict(right.authorization)
        and dict(left.linked_case_context) == dict(right.linked_case_context)
        and left.requested_at == right.requested_at
        and left.expires_at == right.expires_at
        and left.authority_posture == right.authority_posture
    )


def _same_active_request_subject(
    candidate: ReviewedEvidenceRequestRecord,
    existing_request: ReviewedEvidenceRequestRecord,
) -> bool:
    return (
        _is_active_lifecycle_state(candidate.lifecycle_state)
        and _is_active_lifecycle_state(existing_request.lifecycle_state)
        and candidate.evidence_request_id != existing_request.evidence_request_id
        and _same_request_subject(existing_request, candidate)
    )


def _parse_duration_seconds(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    match = _DURATION_PATTERN.fullmatch(value.strip())
    if match is None:
        return None
    if all(match.group(name) is None for name in ("hours", "minutes", "seconds")):
        return None
    duration_parts = {
        name: int(match.group(name) or 0) for name in ("hours", "minutes", "seconds")
    }
    total_seconds = (
        duration_parts["hours"] * 3600
        + duration_parts["minutes"] * 60
        + duration_parts["seconds"]
    )
    return total_seconds


def _source_status_values(source_status: Mapping[str, object]) -> tuple[str, ...]:
    status_values: list[str] = []
    for field_name in ("status", "state", "registry_state", "source_state"):
        field_value = source_status.get(field_name)
        if isinstance(field_value, str) and field_value.strip():
            status_values.append("_".join(_normalize_text(field_value).split()))
    return tuple(status_values)


def validate_phase63_reviewed_evidence_request(
    request: ReviewedEvidenceRequestRecord,
    *,
    existing_requests: Iterable[ReviewedEvidenceRequestRecord] = (),
    now: datetime | None = None,
) -> ReviewedEvidenceRequestValidationErrors:
    errors: list[str] = []

    if not _non_empty_string(request.evidence_request_id):
        errors.append("missing_evidence_request_id")
    if not _non_empty_string(request.case_id):
        errors.append("missing_case_id")
    if not _non_empty_string(request.requester_identity):
        errors.append("missing_requester_identity")
    if request.requester_role not in _AUTHORIZED_REQUESTER_ROLES:
        errors.append("unauthorized_requester_role")
    errors.extend(_reviewed_scope_errors(request))
    if request.lifecycle_state not in _ALLOWED_LIFECYCLE_STATES:
        errors.append("unsupported_lifecycle_state")

    if not _is_aware_datetime(request.requested_at):
        errors.append("requested_at_not_aware_datetime")
    if not _is_aware_datetime(request.expires_at):
        errors.append("expires_at_not_aware_datetime")
    if _is_aware_datetime(request.requested_at) and _is_aware_datetime(request.expires_at):
        if request.expires_at <= request.requested_at:
            errors.append("expiry_not_after_request")
        if now is not None and not _is_aware_datetime(now):
            errors.append("now_not_aware_datetime")
        comparison_now = now if now is not None else datetime.now(timezone.utc)
        if (
            _is_active_lifecycle_state(request.lifecycle_state)
            and _is_aware_datetime(comparison_now)
            and request.expires_at <= comparison_now
        ):
            errors.append("request_expired")

    if not request.target:
        errors.append("missing_target")
    target_class = str(request.target.get("target_class", ""))
    expected_target_class = _TARGET_CLASS_BY_SOURCE_ID.get(request.source_id)
    if expected_target_class is None:
        errors.append("unsupported_source_id")
    elif target_class != expected_target_class:
        errors.append("target_source_not_compatible")
    required_target_fields = _REQUIRED_TARGET_FIELDS_BY_CLASS.get(target_class)
    if required_target_fields is None:
        if target_class:
            errors.append("unsupported_target_class")
    elif not _mapping_has_non_empty_fields(request.target, required_target_fields):
        errors.append("missing_target_binding")
    if request.target.get("case_id") != request.case_id:
        errors.append("target_case_mismatch")

    source_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY.get(request.source_id)
    if source_entry is not None:
        source_use_errors = validate_phase63_evidence_source_use(
            source_entry,
            target_class=target_class,
        )
        if "target_class_not_allowed" in source_use_errors:
            errors.append("target_source_not_compatible")
        if "source_disabled" in source_use_errors:
            errors.append("source_denied")
        if "source_degraded" in source_use_errors:
            errors.append("source_stale")

        source_freshness = request.source_status.get("freshness")
        if source_freshness is not None:
            source_freshness_seconds = _parse_duration_seconds(source_freshness)
            registry_freshness_seconds = _parse_duration_seconds(
                source_entry.freshness_window
            )
            if (
                source_freshness_seconds is None
                or registry_freshness_seconds is None
                or source_freshness_seconds > registry_freshness_seconds
            ):
                errors.append("source_stale")

        source_status_values = _source_status_values(request.source_status)
        if any(value in source_entry.disabled_states for value in source_status_values):
            errors.append("source_denied")
        if any(value in source_entry.degraded_states for value in source_status_values):
            errors.append("source_stale")

    if not request.custody:
        errors.append("missing_custody")
    elif not _mapping_has_non_empty_fields(request.custody, _REQUIRED_CUSTODY_FIELDS):
        errors.append("incomplete_custody")
    if request.authorization.get("authorized") is not True:
        errors.append("authorization_denied")
    if not _mapping_has_non_empty_fields(
        request.authorization,
        _REQUIRED_AUTHORIZATION_TEXT_FIELDS,
    ):
        errors.append("incomplete_authorization")
    if (
        _non_empty_string(request.requested_scope)
        and request.authorization.get("reviewed_scope") != request.requested_scope
    ):
        errors.append("authorization_scope_mismatch")
    authorization_reviewed_scope = request.authorization.get("reviewed_scope", "")
    if _reviewed_scope_promotes_workflow_truth(authorization_reviewed_scope):
        errors.append("authorization_scope_promotes_workflow_truth")
    if not request.linked_case_context:
        errors.append("missing_case_link")
    elif not _mapping_has_non_empty_fields(
        request.linked_case_context,
        _REQUIRED_CASE_CONTEXT_FIELDS,
    ):
        errors.append("incomplete_case_link")
    if request.linked_case_context.get("case_id") != request.case_id:
        errors.append("linked_case_mismatch")

    source_status_values = _source_status_values(request.source_status)
    if any(value in _TERMINAL_SOURCE_STATUSES for value in source_status_values):
        errors.append("source_denied")
    if any(value in _STALE_SOURCE_STATUSES for value in source_status_values):
        errors.append("source_stale")
    if any(
        value in _SOURCE_AUTHORITY_STATUSES
        or _contains_authority_widening_claim(value)
        for value in source_status_values
    ):
        errors.append("source_status_promotes_workflow_truth")

    authority_values = (
        request.authority_posture,
        request.authorization.get("authority_posture", ""),
        request.source_status.get("authority_posture", ""),
    )
    if request.authority_posture != _SUBORDINATE_AUTHORITY_POSTURE:
        errors.append("authority_posture_not_subordinate")
    if any(_contains_authority_widening_claim(value) for value in authority_values):
        errors.append("authority_posture_promotes_workflow_truth")

    for existing_request in existing_requests:
        if (
            existing_request.evidence_request_id == request.evidence_request_id
            and not _same_request_binding(existing_request, request)
        ):
            if _same_request_subject(existing_request, request):
                errors.append("evidence_request_id_binding_mismatch")
            else:
                errors.append("evidence_request_id_subject_mismatch")
            break
        if _same_active_request_subject(request, existing_request):
            errors.append("duplicate_request_ambiguity")
            break

    return tuple(dict.fromkeys(errors))
