from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
import hashlib
import json
from typing import Mapping, Sequence

from .phase29_shadow_dataset import Phase29ShadowDatasetSnapshot


_REQUIRED_FEATURE_PROVENANCE_FIELDS = (
    "feature_source_record_family",
    "feature_source_record_id",
    "feature_source_field_path",
    "feature_extraction_spec_version",
    "feature_snapshot_timestamp",
    "feature_reviewed_linkage",
)
_REQUIRED_LABEL_PROVENANCE_FIELDS = (
    "label_record_family",
    "label_record_id",
    "label_field_path",
    "label_decision_basis",
    "label_decided_at",
    "label_linked_subject_record_id",
)


class Phase29ShadowScoringError(ValueError):
    """Raised when shadow scoring cannot stay within the reviewed Phase 29 boundary."""


@dataclass(frozen=True)
class Phase29ShadowScoreResult:
    shadow_output_id: str
    shadow_output_type: str
    model_family: str
    model_version: str
    input_snapshot_id: str
    rendered_at: str
    subject_record_family: str
    subject_record_id: str
    supporting_feature_snapshot_id: str
    review_required: bool
    registry_posture: str
    authority_posture: str
    status: str
    anomaly_score: float
    feature_provenance: Mapping[str, Mapping[str, object]]
    label_provenance: Mapping[str, object]
    operator_summary: Mapping[str, object]


@dataclass(frozen=True)
class Phase29OfflineShadowScoringSnapshot:
    snapshot_id: str
    scoring_spec_version: str
    shadow_output_type: str
    registry_posture: str
    authority_posture: str
    example_count: int
    results: tuple[Phase29ShadowScoreResult, ...]


def score_shadow_dataset_offline(
    *,
    dataset_snapshot: Phase29ShadowDatasetSnapshot,
    scoring_spec_version: str,
    model_family: str,
    model_version: str,
    training_data_snapshot_id: str,
    feature_schema_version: str,
    label_schema_version: str,
    lineage_review_note_id: str,
    scored_at: datetime,
) -> Phase29OfflineShadowScoringSnapshot:
    if not isinstance(dataset_snapshot, Phase29ShadowDatasetSnapshot):
        raise TypeError("dataset_snapshot must be a Phase29ShadowDatasetSnapshot")
    if dataset_snapshot.example_count != len(dataset_snapshot.examples):
        raise Phase29ShadowScoringError(
            "dataset_snapshot.example_count must match examples payload length"
        )
    if training_data_snapshot_id != dataset_snapshot.snapshot_id:
        raise Phase29ShadowScoringError(
            "training_data_snapshot_id must match dataset_snapshot.snapshot_id"
        )
    scoring_spec_version = _require_non_empty_string(
        scoring_spec_version,
        "scoring_spec_version",
    )
    model_family = _require_non_empty_string(model_family, "model_family")
    model_version = _require_non_empty_string(model_version, "model_version")
    _require_non_empty_string(feature_schema_version, "feature_schema_version")
    _require_non_empty_string(label_schema_version, "label_schema_version")
    lineage_review_note_id = _require_non_empty_string(
        lineage_review_note_id,
        "lineage_review_note_id",
    )
    scored_at_iso = _require_aware_datetime(scored_at, "scored_at").isoformat()

    examples = tuple(dataset_snapshot.examples)
    for example in examples:
        _validate_dataset_example(example)

    cohort_frequencies = _build_feature_value_frequencies(examples)
    results = tuple(
        _score_dataset_example(
            dataset_example=example,
            input_snapshot_id=dataset_snapshot.snapshot_id,
            supporting_feature_snapshot_id=dataset_snapshot.snapshot_id,
            model_family=model_family,
            model_version=model_version,
            rendered_at_iso=scored_at_iso,
            lineage_review_note_id=lineage_review_note_id,
            cohort_frequencies=cohort_frequencies,
        )
        for example in examples
    )
    return Phase29OfflineShadowScoringSnapshot(
        snapshot_id=dataset_snapshot.snapshot_id,
        scoring_spec_version=scoring_spec_version,
        shadow_output_type="recommendation_draft",
        registry_posture="shadow-only",
        authority_posture="non-authoritative",
        example_count=len(results),
        results=results,
    )


class Phase29ShadowStreamingBaselineScorer:
    def __init__(
        self,
        *,
        scoring_spec_version: str,
        model_family: str,
        model_version: str,
        feature_schema_version: str,
        label_schema_version: str,
        lineage_review_note_id: str,
    ) -> None:
        self.scoring_spec_version = _require_non_empty_string(
            scoring_spec_version,
            "scoring_spec_version",
        )
        self.model_family = _require_non_empty_string(model_family, "model_family")
        self.model_version = _require_non_empty_string(model_version, "model_version")
        self.feature_schema_version = _require_non_empty_string(
            feature_schema_version,
            "feature_schema_version",
        )
        self.label_schema_version = _require_non_empty_string(
            label_schema_version,
            "label_schema_version",
        )
        self.lineage_review_note_id = _require_non_empty_string(
            lineage_review_note_id,
            "lineage_review_note_id",
        )
        self._feature_frequencies: dict[str, Counter[str]] = defaultdict(Counter)
        self._examples_seen = 0

    def score_example(
        self,
        *,
        dataset_example: Mapping[str, object],
        input_snapshot_id: str,
        rendered_at: datetime,
    ) -> Phase29ShadowScoreResult:
        _require_non_empty_string(input_snapshot_id, "input_snapshot_id")
        rendered_at_iso = _require_aware_datetime(rendered_at, "rendered_at").isoformat()
        _validate_dataset_example(dataset_example)
        features = _expect_mapping(dataset_example.get("features"), "features")

        contributions: list[float] = []
        for feature_name, feature_entry in sorted(features.items()):
            del feature_entry
            value_key = _feature_value_key(features[feature_name]["value"])
            prior_occurrences = self._feature_frequencies[feature_name][value_key]
            denominator = max(self._examples_seen, 1)
            novelty_score = 1.0 - min(prior_occurrences / denominator, 1.0)
            contributions.append(novelty_score)

        anomaly_score = round(sum(contributions) / max(len(contributions), 1), 6)
        result = _score_dataset_example(
            dataset_example=dataset_example,
            input_snapshot_id=input_snapshot_id,
            supporting_feature_snapshot_id=input_snapshot_id,
            model_family=self.model_family,
            model_version=self.model_version,
            rendered_at_iso=rendered_at_iso,
            lineage_review_note_id=self.lineage_review_note_id,
            cohort_frequencies=None,
            explicit_score=anomaly_score,
        )
        self._examples_seen += 1
        for feature_name, feature_entry in sorted(features.items()):
            self._feature_frequencies[feature_name][_feature_value_key(feature_entry["value"])] += 1
        return result


def _score_dataset_example(
    *,
    dataset_example: Mapping[str, object],
    input_snapshot_id: str,
    supporting_feature_snapshot_id: str,
    model_family: str,
    model_version: str,
    rendered_at_iso: str,
    lineage_review_note_id: str,
    cohort_frequencies: Mapping[str, Counter[str]] | None,
    explicit_score: float | None = None,
) -> Phase29ShadowScoreResult:
    subject_record_family = _require_non_empty_string(
        dataset_example.get("subject_record_family"),
        "subject_record_family",
    )
    subject_record_id = _require_non_empty_string(
        dataset_example.get("subject_record_id"),
        "subject_record_id",
    )
    features = _expect_mapping(dataset_example.get("features"), "features")
    label = _expect_mapping(dataset_example.get("label"), "label")
    label_provenance = _expect_mapping(label.get("provenance"), "label.provenance")

    feature_provenance = {
        feature_name: dict(_validate_feature_entry(feature_name, feature_entry))
        for feature_name, feature_entry in sorted(features.items())
    }
    validated_label_provenance = dict(_validate_label_provenance(label_provenance))

    if explicit_score is None:
        explicit_score = _compute_offline_anomaly_score(
            features=features,
            cohort_frequencies=cohort_frequencies or {},
        )

    operator_summary = _build_operator_summary(
        subject_record_family=subject_record_family,
        subject_record_id=subject_record_id,
        anomaly_score=explicit_score,
        label_value=_require_non_empty_string(label.get("value"), "label.value"),
        rendered_at_iso=rendered_at_iso,
        lineage_review_note_id=lineage_review_note_id,
    )
    shadow_output_id = _shadow_output_id(
        subject_record_family=subject_record_family,
        subject_record_id=subject_record_id,
        model_family=model_family,
        model_version=model_version,
        input_snapshot_id=input_snapshot_id,
        rendered_at_iso=rendered_at_iso,
    )
    return Phase29ShadowScoreResult(
        shadow_output_id=shadow_output_id,
        shadow_output_type="recommendation_draft",
        model_family=model_family,
        model_version=model_version,
        input_snapshot_id=input_snapshot_id,
        rendered_at=rendered_at_iso,
        subject_record_family=subject_record_family,
        subject_record_id=subject_record_id,
        supporting_feature_snapshot_id=supporting_feature_snapshot_id,
        review_required=True,
        registry_posture="shadow-only",
        authority_posture="non-authoritative",
        status="shadow-ready",
        anomaly_score=explicit_score,
        feature_provenance=feature_provenance,
        label_provenance=validated_label_provenance,
        operator_summary=operator_summary,
    )


def _compute_offline_anomaly_score(
    *,
    features: Mapping[str, Mapping[str, object]],
    cohort_frequencies: Mapping[str, Counter[str]],
) -> float:
    contributions: list[float] = []
    for feature_name, feature_entry in sorted(features.items()):
        value_key = _feature_value_key(feature_entry["value"])
        total = sum(cohort_frequencies.get(feature_name, Counter()).values())
        if total <= 1:
            rarity_score = 1.0
        else:
            occurrences = cohort_frequencies[feature_name][value_key]
            rarity_score = 1.0 - min(occurrences / total, 1.0)
        if feature_name == "ambiguity_badges" and feature_entry["value"]:
            rarity_score = max(rarity_score, 0.95)
        if feature_name == "source_health_state" and feature_entry["value"] in {"stale", "degraded", "unresolved"}:
            rarity_score = max(rarity_score, 0.9)
        contributions.append(rarity_score)
    return round(sum(contributions) / max(len(contributions), 1), 6)


def _build_feature_value_frequencies(
    examples: Sequence[Mapping[str, object]],
) -> dict[str, Counter[str]]:
    frequencies: dict[str, Counter[str]] = defaultdict(Counter)
    for example in examples:
        features = _expect_mapping(example.get("features"), "features")
        for feature_name, feature_entry in sorted(features.items()):
            frequencies[feature_name][_feature_value_key(feature_entry["value"])] += 1
    return dict(frequencies)


def _validate_dataset_example(dataset_example: Mapping[str, object]) -> None:
    if not isinstance(dataset_example, Mapping):
        raise Phase29ShadowScoringError("dataset_example must be a mapping")
    features = _expect_mapping(dataset_example.get("features"), "features")
    if not features:
        raise Phase29ShadowScoringError("dataset_example.features must not be empty")
    for feature_name, feature_entry in sorted(features.items()):
        _validate_feature_entry(feature_name, feature_entry)
    label = _expect_mapping(dataset_example.get("label"), "label")
    _validate_label_provenance(_expect_mapping(label.get("provenance"), "label.provenance"))


def _validate_feature_entry(
    feature_name: str,
    feature_entry: Mapping[str, object],
) -> Mapping[str, object]:
    normalized_feature_name = _require_non_empty_string(feature_name, "feature_name")
    if not isinstance(feature_entry, Mapping):
        raise Phase29ShadowScoringError(
            f"feature {normalized_feature_name} must be a mapping"
        )
    provenance = _expect_mapping(feature_entry.get("provenance"), f"{normalized_feature_name}.provenance")
    missing_fields = [
        field_name
        for field_name in _REQUIRED_FEATURE_PROVENANCE_FIELDS
        if _optional_string(provenance.get(field_name)) is None
    ]
    if missing_fields:
        raise Phase29ShadowScoringError(
            "missing required feature provenance on "
            f"{normalized_feature_name}: {', '.join(missing_fields)}"
        )
    _require_timestamp_string(
        provenance["feature_snapshot_timestamp"],
        f"{normalized_feature_name}.feature_snapshot_timestamp",
    )
    return provenance


def _validate_label_provenance(
    label_provenance: Mapping[str, object],
) -> Mapping[str, object]:
    missing_fields = [
        field_name
        for field_name in _REQUIRED_LABEL_PROVENANCE_FIELDS
        if _optional_string(label_provenance.get(field_name)) is None
    ]
    if missing_fields:
        raise Phase29ShadowScoringError(
            "missing required label provenance: " + ", ".join(missing_fields)
        )
    _require_timestamp_string(
        label_provenance["label_decided_at"],
        "label_decided_at",
    )
    return label_provenance


def _build_operator_summary(
    *,
    subject_record_family: str,
    subject_record_id: str,
    anomaly_score: float,
    label_value: str,
    rendered_at_iso: str,
    lineage_review_note_id: str,
) -> dict[str, object]:
    rounded_score = round(anomaly_score, 6)
    return {
        "summary": (
            "shadow/non-authoritative anomaly score for reviewed "
            f"{subject_record_family} {subject_record_id}: {rounded_score:.6f}"
        ),
        "rendered_at": rendered_at_iso,
        "lineage_review_note_id": lineage_review_note_id,
        "candidate_recommendations": [
            {
                "shadow_posture": "shadow/non-authoritative",
                "review_required": True,
                "recommended_action": (
                    "Review the scored recommendation manually before any workflow mutation."
                ),
                "observed_label": label_value,
                "anomaly_score": rounded_score,
            }
        ],
    }


def _shadow_output_id(
    *,
    subject_record_family: str,
    subject_record_id: str,
    model_family: str,
    model_version: str,
    input_snapshot_id: str,
    rendered_at_iso: str,
) -> str:
    payload = {
        "subject_record_family": subject_record_family,
        "subject_record_id": subject_record_id,
        "model_family": model_family,
        "model_version": model_version,
        "input_snapshot_id": input_snapshot_id,
        "rendered_at": rendered_at_iso,
    }
    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _canonical_json(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _feature_value_key(value: object) -> str:
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def _expect_mapping(value: object, field_name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise Phase29ShadowScoringError(f"{field_name} must be a mapping")
    return value


def _require_timestamp_string(value: object, field_name: str) -> str:
    normalized = _require_non_empty_string(value, field_name)
    datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    return normalized


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise Phase29ShadowScoringError(f"{field_name} must be a timezone-aware datetime")
    return value


def _require_non_empty_string(value: object, field_name: str) -> str:
    normalized = _optional_string(value)
    if normalized is None:
        raise Phase29ShadowScoringError(f"{field_name} must be a non-empty string")
    return normalized


def _optional_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped if stripped else None
