from __future__ import annotations

from .models import (
    ControlPlaneRecord,
    DetectorLifecycleRecord,
    FalsePositiveReviewRecord,
    SourceHealthRecord,
    SuppressionProposalRecord,
)


_DETECTOR_LIFECYCLE_STATES: frozenset[str] = frozenset(
    {
        "candidate",
        "staging",
        "active",
        "disabled",
        "rollback",
        "review-overdue",
    }
)
_DETECTOR_SOURCE_CATALOG_ENTRIES_BY_FAMILY: dict[str, frozenset[str]] = {
    "wazuh_detection": frozenset(
        {"docs/phase-61-minimum-source-catalog-contract.md"}
    ),
    "github_audit": frozenset(
        {
            "docs/source-families/github-audit/onboarding-package.md",
            "docs/source-families/github-audit/detector-activation-candidates/repository-admin-membership-change.md",
        }
    ),
    "microsoft_365_audit": frozenset(
        {"docs/source-families/microsoft-365-audit/onboarding-package.md"}
    ),
    "entra_id": frozenset(
        {
            "docs/source-families/entra-id/onboarding-package.md",
            "docs/source-families/entra-id/detector-activation-candidates/privileged-role-assignment.md",
        }
    ),
    "windows_security_endpoint": frozenset(
        {"docs/source-families/windows-security-and-endpoint/onboarding-package.md"}
    ),
}
_DETECTOR_STATE_REQUIRED_FIELDS: dict[str, tuple[str, ...]] = {
    "disabled": ("disabled_reason",),
    "rollback": ("rollback_reason",),
    "review-overdue": ("review_overdue_reason",),
}
_DETECTOR_REASON_FIELDS = frozenset(
    {"disabled_reason", "rollback_reason", "review_overdue_reason"}
)

_FALSE_POSITIVE_REVIEW_DISPOSITIONS = frozenset(
    {
        "benign_activity",
        "expected_activity",
        "duplicate_signal",
        "needs_detector_tuning",
        "recurring_benign_activity",
    }
)
_FALSE_POSITIVE_REVIEW_DISPUTE_STATES = frozenset(
    {"undisputed", "disputed", "resolved"}
)
_FALSE_POSITIVE_REVIEW_RECURRENCE_POSTURES = frozenset(
    {
        "single_reviewed_instance",
        "recurring_reviewed_pattern",
        "recurrence_under_review",
    }
)
_FALSE_POSITIVE_REVIEW_SOURCE_SIGNAL_HANDLING = frozenset(
    {"preserve_source_signal", "preserve_and_escalate_for_tuning"}
)
_SUPPRESSION_PROPOSAL_SCOPES = frozenset(
    {
        "detector_case_context",
        "detector_alert_context",
        "detector_evidence_context",
        "reviewed_recurring_pattern",
    }
)
_SUPPRESSION_PROPOSAL_SOURCE_SIGNAL_HANDLING = frozenset(
    {"preserve_source_signal", "preserve_and_escalate_for_review"}
)
_SOURCE_HEALTH_STATES = frozenset(
    {
        "available",
        "degraded",
        "unavailable",
        "stale_source",
        "missing_agent",
        "parser_failure",
        "volume_anomaly",
        "credential_degraded",
        "detector_drift",
        "mismatched",
    }
)
_SOURCE_HEALTH_DETECTOR_DRIFT_STATES = frozenset(
    {"none", "review_required", "mismatched"}
)
_SOURCE_HEALTH_CREDENTIAL_POSTURES = frozenset(
    {"reviewed", "degraded", "unavailable"}
)


def is_phase61_record_family(record: ControlPlaneRecord) -> bool:
    return isinstance(
        record,
        (
            DetectorLifecycleRecord,
            FalsePositiveReviewRecord,
            SuppressionProposalRecord,
            SourceHealthRecord,
        ),
    )


def validate_phase61_record(record: ControlPlaneRecord) -> bool:
    if isinstance(record, DetectorLifecycleRecord):
        _validate_detector_lifecycle_record(record)
        return True
    if isinstance(record, FalsePositiveReviewRecord):
        _validate_false_positive_review_record(record)
        return True
    if isinstance(record, SuppressionProposalRecord):
        _validate_suppression_proposal_record(record)
        return True
    if isinstance(record, SourceHealthRecord):
        _validate_source_health_record(record)
        return True
    return False


def _has_linkage_value(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return value.strip() != ""
    if isinstance(value, (tuple, list, set, frozenset)):
        return any(_has_linkage_value(item) for item in value)
    return True


def _require_any_linkage(
    record: ControlPlaneRecord,
    field_names: tuple[str, ...],
) -> None:
    if any(_has_linkage_value(getattr(record, field_name)) for field_name in field_names):
        return
    required_fields = ", ".join(field_names)
    raise ValueError(
        f"{record.record_family} record {record.record_id!r} requires at least one linkage field: "
        f"{required_fields}"
    )


def _require_non_empty_tuple(
    record: ControlPlaneRecord,
    field_name: str,
) -> None:
    values = _require_tuple_or_list(record, field_name)
    if len(values) >= 1:
        return
    raise ValueError(
        f"{record.record_family} record {record.record_id!r} requires non-empty {field_name}"
    )


def _require_tuple_or_list(
    record: ControlPlaneRecord,
    field_name: str,
) -> tuple[object, ...] | list[object]:
    values = getattr(record, field_name)
    if isinstance(values, (tuple, list)):
        return values
    raise ValueError(
        f"{record.record_family} record {record.record_id!r} requires {field_name} "
        "to be a tuple/list"
    )


def _require_non_blank_fields(
    record: ControlPlaneRecord,
    field_names: tuple[str, ...],
) -> None:
    for field_name in field_names:
        if _has_linkage_value(getattr(record, field_name)):
            continue
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} requires non-blank {field_name}"
        )


def _validate_source_catalog_binding(
    record: (
        DetectorLifecycleRecord
        | FalsePositiveReviewRecord
        | SuppressionProposalRecord
        | SourceHealthRecord
    ),
) -> tuple[str, str]:
    source_family = record.source_family.strip()
    if source_family not in _DETECTOR_SOURCE_CATALOG_ENTRIES_BY_FAMILY:
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} has unsupported "
            f"source_family {record.source_family!r}; expected one of "
            f"{sorted(_DETECTOR_SOURCE_CATALOG_ENTRIES_BY_FAMILY)!r}"
        )
    source_catalog_entry = record.source_catalog_entry.strip()
    if (
        source_catalog_entry
        not in _DETECTOR_SOURCE_CATALOG_ENTRIES_BY_FAMILY[source_family]
    ):
        raise ValueError(
            f"{record.record_family} record {record.record_id!r} has unsupported "
            f"source_catalog_entry {record.source_catalog_entry!r} for "
            f"source_family {source_family!r}; expected one of "
            f"{sorted(_DETECTOR_SOURCE_CATALOG_ENTRIES_BY_FAMILY[source_family])!r}"
        )
    return source_family, source_catalog_entry


def _validate_non_blank_sequence_entries(
    record: ControlPlaneRecord,
    values: tuple[object, ...] | list[object],
    field_name: str,
) -> None:
    for value in values:
        if not isinstance(value, str) or not _has_linkage_value(value):
            raise ValueError(
                f"{record.record_family} record {record.record_id!r} requires "
                f"non-blank {field_name} entries"
            )


def _validate_detector_lifecycle_record(record: DetectorLifecycleRecord) -> None:
    _require_non_blank_fields(
        record,
        (
            "owner",
            "source_family",
            "source_catalog_entry",
            "detector_identifier",
            "expected_signal_posture",
            "review_cadence",
            "rollback_owner",
            "disable_owner",
        ),
    )
    _require_non_empty_tuple(record, "lifecycle_audit_references")
    _validate_non_blank_sequence_entries(
        record,
        record.lifecycle_audit_references,
        "lifecycle_audit_references",
    )
    _validate_source_catalog_binding(record)

    expected_reason_fields = frozenset(
        _DETECTOR_STATE_REQUIRED_FIELDS.get(record.lifecycle_state, ())
    )
    for field_name in _DETECTOR_REASON_FIELDS:
        reason_value = getattr(record, field_name)
        if field_name in expected_reason_fields:
            if not _has_linkage_value(reason_value):
                raise ValueError(
                    f"detector_lifecycle record {record.record_id!r} in state "
                    f"{record.lifecycle_state!r} requires non-blank {field_name}"
                )
            continue
        if _has_linkage_value(reason_value):
            raise ValueError(
                f"detector_lifecycle record {record.record_id!r} in state "
                f"{record.lifecycle_state!r} must not set {field_name}; expected reason fields "
                f"{sorted(expected_reason_fields)!r}"
            )


def _validate_false_positive_review_record(
    record: FalsePositiveReviewRecord,
) -> None:
    _require_non_blank_fields(
        record,
        (
            "detector_lifecycle_id",
            "source_family",
            "source_catalog_entry",
            "owner",
            "disposition",
            "disposition_rationale",
            "dispute_state",
            "recurrence_posture",
            "source_signal_handling",
        ),
    )
    _require_non_empty_tuple(record, "review_evidence_references")
    _require_tuple_or_list(record, "evidence_ids")
    _require_any_linkage(record, ("alert_id", "case_id", "evidence_ids"))
    if record.alert_id is None and record.case_id is None:
        _require_non_empty_tuple(record, "evidence_ids")
    _validate_non_blank_sequence_entries(record, record.evidence_ids, "evidence_ids")
    _validate_non_blank_sequence_entries(
        record,
        record.review_evidence_references,
        "review_evidence_references",
    )
    _validate_source_catalog_binding(record)
    if record.disposition not in _FALSE_POSITIVE_REVIEW_DISPOSITIONS:
        raise ValueError(
            f"false_positive_review record {record.record_id!r} has invalid disposition "
            f"{record.disposition!r}; expected one of "
            f"{sorted(_FALSE_POSITIVE_REVIEW_DISPOSITIONS)!r}"
        )
    if record.dispute_state not in _FALSE_POSITIVE_REVIEW_DISPUTE_STATES:
        raise ValueError(
            f"false_positive_review record {record.record_id!r} has invalid dispute_state "
            f"{record.dispute_state!r}; expected one of "
            f"{sorted(_FALSE_POSITIVE_REVIEW_DISPUTE_STATES)!r}"
        )
    if record.recurrence_posture not in _FALSE_POSITIVE_REVIEW_RECURRENCE_POSTURES:
        raise ValueError(
            f"false_positive_review record {record.record_id!r} has invalid "
            f"recurrence_posture {record.recurrence_posture!r}; expected one of "
            f"{sorted(_FALSE_POSITIVE_REVIEW_RECURRENCE_POSTURES)!r}"
        )
    if (
        record.source_signal_handling
        not in _FALSE_POSITIVE_REVIEW_SOURCE_SIGNAL_HANDLING
    ):
        raise ValueError(
            f"false_positive_review record {record.record_id!r} must preserve source "
            "signals and may not delete, hide, or silently suppress source-native truth"
        )
    if record.dispute_state == "disputed" and record.lifecycle_state != "disputed":
        raise ValueError(
            f"false_positive_review record {record.record_id!r} disputed reviews must "
            "use lifecycle_state 'disputed'"
        )
    if (
        record.dispute_state != "disputed"
        and record.lifecycle_state == "disputed"
    ):
        raise ValueError(
            f"false_positive_review record {record.record_id!r} lifecycle_state "
            "'disputed' requires dispute_state 'disputed'"
        )
    if (
        record.disposition == "recurring_benign_activity"
        and record.recurrence_posture != "recurring_reviewed_pattern"
    ):
        raise ValueError(
            f"false_positive_review record {record.record_id!r} repeated false positives "
            "require recurrence_posture 'recurring_reviewed_pattern'"
        )


def _validate_suppression_proposal_record(
    record: SuppressionProposalRecord,
) -> None:
    _require_non_blank_fields(
        record,
        (
            "detector_lifecycle_id",
            "source_family",
            "source_catalog_entry",
            "owner",
            "rationale",
            "review_cadence",
            "expected_signal_impact",
            "scope",
            "source_signal_handling",
        ),
    )
    _require_non_empty_tuple(record, "citation_references")
    _require_tuple_or_list(record, "evidence_ids")
    _require_any_linkage(record, ("alert_id", "case_id", "evidence_ids"))
    if record.alert_id is None and record.case_id is None:
        _require_non_empty_tuple(record, "evidence_ids")
    _validate_non_blank_sequence_entries(record, record.evidence_ids, "evidence_ids")
    _validate_non_blank_sequence_entries(
        record,
        record.citation_references,
        "citation_references",
    )
    if record.expires_at is None:
        raise ValueError(
            f"suppression_proposal record {record.record_id!r} must set a finite expires_at"
        )
    _validate_source_catalog_binding(record)
    if record.scope not in _SUPPRESSION_PROPOSAL_SCOPES:
        raise ValueError(
            f"suppression_proposal record {record.record_id!r} has invalid scope "
            f"{record.scope!r}; expected one of {sorted(_SUPPRESSION_PROPOSAL_SCOPES)!r}"
        )
    if record.source_signal_handling not in _SUPPRESSION_PROPOSAL_SOURCE_SIGNAL_HANDLING:
        raise ValueError(
            f"suppression_proposal record {record.record_id!r} must preserve source "
            "signals and may not delete, hide, silently suppress, or apply source-native truth"
        )


def _validate_source_health_record(record: SourceHealthRecord) -> None:
    _require_non_blank_fields(
        record,
        (
            "source_family",
            "source_catalog_entry",
            "health_state",
            "reviewed_state",
            "detector_drift",
            "credential_posture",
            "operator_visible_reason",
        ),
    )
    _require_non_empty_tuple(record, "evidence_references")
    _validate_non_blank_sequence_entries(
        record,
        record.evidence_references,
        "evidence_references",
    )

    _validate_source_catalog_binding(record)
    if record.health_state not in _SOURCE_HEALTH_STATES:
        raise ValueError(
            f"source_health record {record.record_id!r} has invalid health_state "
            f"{record.health_state!r}; expected one of "
            f"{sorted(_SOURCE_HEALTH_STATES)!r}"
        )
    if record.reviewed_state != record.lifecycle_state:
        raise ValueError(
            f"source_health record {record.record_id!r} requires reviewed_state to match lifecycle_state"
        )
    if record.detector_drift not in _SOURCE_HEALTH_DETECTOR_DRIFT_STATES:
        raise ValueError(
            f"source_health record {record.record_id!r} has invalid detector_drift "
            f"{record.detector_drift!r}; expected one of "
            f"{sorted(_SOURCE_HEALTH_DETECTOR_DRIFT_STATES)!r}"
        )
    if record.credential_posture not in _SOURCE_HEALTH_CREDENTIAL_POSTURES:
        raise ValueError(
            f"source_health record {record.record_id!r} has invalid credential_posture "
            f"{record.credential_posture!r}; expected one of "
            f"{sorted(_SOURCE_HEALTH_CREDENTIAL_POSTURES)!r}"
        )
    if record.observed_at > record.reviewed_at:
        raise ValueError(
            f"source_health record {record.record_id!r} requires observed_at <= reviewed_at"
        )
    if record.source_native_authority or record.display_state_authority:
        raise ValueError(
            f"source_health record {record.record_id!r} must remain subordinate "
            "operational context and cannot become workflow truth"
        )
    if record.cache_sourced:
        raise ValueError(
            f"source_health record {record.record_id!r} must not be cache sourced; "
            "stale-cache source health is refused"
        )


__all__ = [
    "_DETECTOR_LIFECYCLE_STATES",
    "is_phase61_record_family",
    "validate_phase61_record",
]
