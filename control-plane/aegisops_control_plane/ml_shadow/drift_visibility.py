from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Mapping

from .dataset import Phase29ShadowDatasetSnapshot


_REQUIRED_SOURCE_HEALTH_FEATURES = (
    "source_health_state",
    "source_health_ingest_disposition",
)
_DEGRADED_SOURCE_HEALTH_STATES = frozenset({"stale", "degraded", "unresolved"})
_DEGRADED_SOURCE_HEALTH_DISPOSITIONS = frozenset({"stale", "degraded", "partial"})


class Phase29EvidentlyDriftVisibilityError(ValueError):
    """Raised when reviewed drift visibility cannot stay within the Phase 29 boundary."""


@dataclass(frozen=True)
class Phase29SubjectDriftVisibility:
    subject_record_family: str
    subject_record_id: str
    source_health_state: str
    source_health_ingest_disposition: str
    status: str
    correlation_status: str
    feature_drift_count: int
    shadow_data_drift_ratio: float
    drifted_features: Mapping[str, Mapping[str, object]]
    feature_health: Mapping[str, Mapping[str, object]]


@dataclass(frozen=True)
class Phase29EvidentlyDriftVisibilityReport:
    reference_snapshot_id: str
    candidate_snapshot_id: str
    rendered_at: str
    registry_posture: str
    authority_posture: str
    drift_surface: str
    status: str
    subject_count: int
    subjects: tuple[Phase29SubjectDriftVisibility, ...]


def build_phase29_evidently_drift_visibility_report(
    *,
    reference_snapshot: Phase29ShadowDatasetSnapshot,
    candidate_snapshot: Phase29ShadowDatasetSnapshot,
    rendered_at: datetime,
    stale_feature_after: timedelta,
) -> Phase29EvidentlyDriftVisibilityReport:
    if not isinstance(reference_snapshot, Phase29ShadowDatasetSnapshot):
        raise TypeError("reference_snapshot must be a Phase29ShadowDatasetSnapshot")
    if not isinstance(candidate_snapshot, Phase29ShadowDatasetSnapshot):
        raise TypeError("candidate_snapshot must be a Phase29ShadowDatasetSnapshot")
    rendered_at = _require_aware_datetime(rendered_at, "rendered_at")
    if (
        not isinstance(stale_feature_after, timedelta)
        or stale_feature_after <= timedelta(0)
    ):
        raise Phase29EvidentlyDriftVisibilityError(
            "stale_feature_after must be a positive timedelta"
        )
    _validate_snapshot(reference_snapshot, "reference_snapshot")
    _validate_snapshot(candidate_snapshot, "candidate_snapshot")

    reference_examples = _examples_by_subject(reference_snapshot, "reference snapshot")
    candidate_examples = _examples_by_subject(candidate_snapshot, "candidate snapshot")

    subjects: list[Phase29SubjectDriftVisibility] = []
    for subject_key, candidate_example in sorted(candidate_examples.items()):
        if subject_key not in reference_examples:
            raise Phase29EvidentlyDriftVisibilityError(
                "candidate snapshot contains subject without reviewed baseline: "
                f"{subject_key[0]} {subject_key[1]}"
            )
        reference_example = reference_examples[subject_key]
        subjects.append(
            _build_subject_visibility(
                reference_example=reference_example,
                candidate_example=candidate_example,
                rendered_at=rendered_at,
                stale_feature_after=stale_feature_after,
            )
        )

    report_status = "shadow-ready"
    if any(subject.status == "degraded" for subject in subjects):
        report_status = "degraded"
    elif any(
        subject.correlation_status == "drift-detected"
        or subject.feature_drift_count > 0
        for subject in subjects
    ):
        report_status = "drift-detected"
    elif any(subject.status == "unresolved" for subject in subjects):
        report_status = "unresolved"

    return Phase29EvidentlyDriftVisibilityReport(
        reference_snapshot_id=reference_snapshot.snapshot_id,
        candidate_snapshot_id=candidate_snapshot.snapshot_id,
        rendered_at=rendered_at.isoformat(),
        registry_posture="shadow-only",
        authority_posture="non-authoritative",
        drift_surface="reviewed-equivalent",
        status=report_status,
        subject_count=len(subjects),
        subjects=tuple(subjects),
    )


def _build_subject_visibility(
    *,
    reference_example: Mapping[str, object],
    candidate_example: Mapping[str, object],
    rendered_at: datetime,
    stale_feature_after: timedelta,
) -> Phase29SubjectDriftVisibility:
    subject_record_family = _require_non_empty_string(
        candidate_example.get("subject_record_family"),
        "candidate_example.subject_record_family",
    )
    subject_record_id = _require_non_empty_string(
        candidate_example.get("subject_record_id"),
        "candidate_example.subject_record_id",
    )
    reference_features = _expect_mapping(reference_example.get("features"), "reference.features")
    candidate_features = _expect_mapping(candidate_example.get("features"), "candidate.features")
    for required_feature in _REQUIRED_SOURCE_HEALTH_FEATURES:
        if required_feature not in candidate_features:
            raise Phase29EvidentlyDriftVisibilityError(
                "candidate snapshot is missing required source-health feature: "
                f"{required_feature}"
            )
        if required_feature not in reference_features:
            raise Phase29EvidentlyDriftVisibilityError(
                "reference snapshot is missing required source-health feature: "
                f"{required_feature}"
            )
        _validate_feature_entry(
            candidate_features[required_feature],
            f"candidate.features.{required_feature}",
        )
        _validate_feature_entry(
            reference_features[required_feature],
            f"reference.features.{required_feature}",
        )

    source_health_state = _require_non_empty_string(
        candidate_features["source_health_state"]["value"],
        "candidate.features.source_health_state.value",
    )
    source_health_ingest_disposition = _require_non_empty_string(
        candidate_features["source_health_ingest_disposition"]["value"],
        "candidate.features.source_health_ingest_disposition.value",
    )

    feature_health: dict[str, Mapping[str, object]] = {}
    drifted_features: dict[str, Mapping[str, object]] = {}
    degraded_feature_seen = False

    missing_candidate_features = sorted(set(reference_features) - set(candidate_features))
    if missing_candidate_features:
        raise Phase29EvidentlyDriftVisibilityError(
            "candidate snapshot is missing reviewed baseline features: "
            + ", ".join(missing_candidate_features)
        )

    for feature_name, candidate_feature in sorted(candidate_features.items()):
        _validate_feature_entry(candidate_feature, f"candidate.features.{feature_name}")
        reference_feature = reference_features.get(feature_name)
        if reference_feature is None:
            raise Phase29EvidentlyDriftVisibilityError(
                "reference snapshot is missing candidate feature baseline: "
                f"{feature_name}"
            )
        _validate_feature_entry(reference_feature, f"reference.features.{feature_name}")

        health_entry = _build_feature_health(
            feature_name=feature_name,
            candidate_feature=candidate_feature,
            rendered_at=rendered_at,
            stale_feature_after=stale_feature_after,
            source_health_state=source_health_state,
            source_health_ingest_disposition=source_health_ingest_disposition,
        )
        feature_health[feature_name] = health_entry
        if health_entry["status"] in {"stale", "degraded"}:
            degraded_feature_seen = True

        candidate_value = candidate_feature["value"]
        reference_value = reference_feature["value"]
        if candidate_value != reference_value:
            drifted_features[feature_name] = {
                "reference_value": reference_value,
                "candidate_value": candidate_value,
                "provenance": dict(candidate_feature["provenance"]),
            }

    feature_total = max(len(candidate_features), 1)
    feature_drift_count = len(drifted_features)
    shadow_data_drift_ratio = round(feature_drift_count / feature_total, 6)

    correlation_status = "stable"
    if (
        source_health_state in _DEGRADED_SOURCE_HEALTH_STATES
        or source_health_ingest_disposition in _DEGRADED_SOURCE_HEALTH_DISPOSITIONS
    ):
        if feature_drift_count or degraded_feature_seen:
            correlation_status = "source-health-correlated"
        else:
            correlation_status = "source-health-degraded"
    elif feature_drift_count:
        correlation_status = "drift-detected"

    status = "shadow-ready"
    if correlation_status in {"source-health-correlated", "source-health-degraded"}:
        status = "degraded"
    elif degraded_feature_seen:
        status = "degraded"
    elif correlation_status == "drift-detected":
        status = "unresolved"

    return Phase29SubjectDriftVisibility(
        subject_record_family=subject_record_family,
        subject_record_id=subject_record_id,
        source_health_state=source_health_state,
        source_health_ingest_disposition=source_health_ingest_disposition,
        status=status,
        correlation_status=correlation_status,
        feature_drift_count=feature_drift_count,
        shadow_data_drift_ratio=shadow_data_drift_ratio,
        drifted_features=drifted_features,
        feature_health=feature_health,
    )


def _build_feature_health(
    *,
    feature_name: str,
    candidate_feature: Mapping[str, object],
    rendered_at: datetime,
    stale_feature_after: timedelta,
    source_health_state: str,
    source_health_ingest_disposition: str,
) -> Mapping[str, object]:
    provenance = _expect_mapping(
        candidate_feature.get("provenance"),
        f"candidate.features.{feature_name}.provenance",
    )
    feature_snapshot_timestamp = _require_timestamp_string(
        provenance.get("feature_snapshot_timestamp"),
        f"candidate.features.{feature_name}.provenance.feature_snapshot_timestamp",
    )
    feature_snapshot_time = datetime.fromisoformat(
        feature_snapshot_timestamp.replace("Z", "+00:00")
    )
    feature_age = rendered_at - feature_snapshot_time
    status = "healthy"
    reason = "reviewed feature remains within freshness window"

    if feature_name in _REQUIRED_SOURCE_HEALTH_FEATURES and (
        source_health_state in _DEGRADED_SOURCE_HEALTH_STATES
        or source_health_ingest_disposition in _DEGRADED_SOURCE_HEALTH_DISPOSITIONS
    ):
        status = "degraded"
        reason = "reviewed source health is degraded for this subject"
    elif feature_age > stale_feature_after:
        status = "stale"
        reason = "feature snapshot is older than the reviewed freshness window"

    return {
        "status": status,
        "reason": reason,
        "feature_snapshot_timestamp": feature_snapshot_timestamp,
        "feature_age_seconds": round(feature_age.total_seconds(), 6),
        "linked_source_health_state": source_health_state,
        "linked_source_health_ingest_disposition": source_health_ingest_disposition,
        "provenance": dict(provenance),
    }


def _examples_by_subject(
    snapshot: Phase29ShadowDatasetSnapshot,
    snapshot_label: str,
) -> dict[tuple[str, str], Mapping[str, object]]:
    examples: dict[tuple[str, str], Mapping[str, object]] = {}
    for example in snapshot.examples:
        subject_record_family = _require_non_empty_string(
            example.get("subject_record_family"),
            f"{snapshot_label}.subject_record_family",
        )
        subject_record_id = _require_non_empty_string(
            example.get("subject_record_id"),
            f"{snapshot_label}.subject_record_id",
        )
        subject_key = (subject_record_family, subject_record_id)
        if subject_key in examples:
            raise Phase29EvidentlyDriftVisibilityError(
                "snapshot contains duplicate reviewed subject: "
                f"{subject_record_family} {subject_record_id}"
            )
        examples[subject_key] = example
    return examples


def _validate_snapshot(
    snapshot: Phase29ShadowDatasetSnapshot,
    field_name: str,
) -> None:
    if snapshot.example_count != len(snapshot.examples):
        raise Phase29EvidentlyDriftVisibilityError(
            f"{field_name}.example_count must match examples payload length"
        )


def _validate_feature_entry(feature_entry: object, field_name: str) -> None:
    if not isinstance(feature_entry, Mapping):
        raise Phase29EvidentlyDriftVisibilityError(f"{field_name} must be a mapping")
    if "value" not in feature_entry or feature_entry["value"] is None:
        raise Phase29EvidentlyDriftVisibilityError(
            f"{field_name} is missing reviewed feature value"
        )
    provenance = _expect_mapping(feature_entry.get("provenance"), f"{field_name}.provenance")
    missing_fields = [
        required_field
        for required_field in (
            "feature_source_record_family",
            "feature_source_record_id",
            "feature_source_field_path",
            "feature_extraction_spec_version",
            "feature_snapshot_timestamp",
            "feature_reviewed_linkage",
        )
        if _optional_string(provenance.get(required_field)) is None
    ]
    if missing_fields:
        raise Phase29EvidentlyDriftVisibilityError(
            f"{field_name} is missing required feature provenance: {', '.join(missing_fields)}"
        )


def _expect_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Phase29EvidentlyDriftVisibilityError(f"{field_name} must be a mapping")
    return value


def _require_timestamp_string(value: object, field_name: str) -> str:
    normalized = _require_non_empty_string(value, field_name)
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise Phase29EvidentlyDriftVisibilityError(
            f"{field_name} must be a valid ISO-8601 timestamp: {normalized}"
        ) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise Phase29EvidentlyDriftVisibilityError(
            f"{field_name} must include a timezone offset: {normalized}"
        )
    return normalized


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise Phase29EvidentlyDriftVisibilityError(
            f"{field_name} must be a timezone-aware datetime"
        )
    return value


def _require_non_empty_string(value: object, field_name: str) -> str:
    normalized = _optional_string(value)
    if normalized is None:
        raise Phase29EvidentlyDriftVisibilityError(f"{field_name} must be a non-empty string")
    return normalized


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None
