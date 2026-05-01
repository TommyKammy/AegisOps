"""Compatibility shim for the legacy Phase 29 shadow scoring import path."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime
from typing import Mapping

from .ml_shadow import scoring as _impl


Phase29ShadowScoringError = _impl.Phase29ShadowScoringError


class Phase29ShadowScoreResult(_impl.Phase29ShadowScoreResult):
    @property
    def feature_frequencies_at_inference_time(self) -> Mapping[str, object]:
        return {}


class Phase29OfflineShadowScoringSnapshot(_impl.Phase29OfflineShadowScoringSnapshot):
    @property
    def scored_examples(self) -> tuple[Phase29ShadowScoreResult, ...]:
        return self.results


def score_shadow_dataset_offline(
    *,
    dataset_snapshot: _impl.Phase29ShadowDatasetSnapshot,
    scoring_spec_version: str,
    model_family: str,
    model_version: str,
    training_data_snapshot_id: str,
    feature_schema_version: str,
    label_schema_version: str,
    lineage_review_note_id: str,
    scored_at: datetime,
    shadow_output_type: str = "recommendation_draft",
) -> Phase29OfflineShadowScoringSnapshot:
    snapshot = _impl.score_shadow_dataset_offline(
        dataset_snapshot=dataset_snapshot,
        scoring_spec_version=scoring_spec_version,
        model_family=model_family,
        model_version=model_version,
        training_data_snapshot_id=training_data_snapshot_id,
        feature_schema_version=feature_schema_version,
        label_schema_version=label_schema_version,
        lineage_review_note_id=lineage_review_note_id,
        scored_at=scored_at,
    )
    return _wrap_snapshot(snapshot, shadow_output_type=shadow_output_type)


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
        shadow_output_type: str = "recommendation_draft",
    ) -> None:
        self._shadow_output_type = shadow_output_type
        self._impl = _impl.Phase29ShadowStreamingBaselineScorer(
            scoring_spec_version=scoring_spec_version,
            model_family=model_family,
            model_version=model_version,
            feature_schema_version=feature_schema_version,
            label_schema_version=label_schema_version,
            lineage_review_note_id=lineage_review_note_id,
        )

    def __getattr__(self, name: str) -> object:
        return getattr(self._impl, name)

    def score_example(
        self,
        *,
        dataset_example: Mapping[str, object],
        input_snapshot_id: str,
        rendered_at: datetime,
    ) -> Phase29ShadowScoreResult:
        result = self._impl.score_example(
            dataset_example=dataset_example,
            input_snapshot_id=input_snapshot_id,
            rendered_at=rendered_at,
        )
        return _wrap_result(result, shadow_output_type=self._shadow_output_type)


def _wrap_snapshot(
    snapshot: _impl.Phase29OfflineShadowScoringSnapshot,
    *,
    shadow_output_type: str,
) -> Phase29OfflineShadowScoringSnapshot:
    results = tuple(
        _wrap_result(result, shadow_output_type=shadow_output_type)
        for result in snapshot.results
    )
    return Phase29OfflineShadowScoringSnapshot(
        snapshot_id=snapshot.snapshot_id,
        scoring_spec_version=snapshot.scoring_spec_version,
        shadow_output_type=shadow_output_type,
        registry_posture=snapshot.registry_posture,
        authority_posture=snapshot.authority_posture,
        example_count=snapshot.example_count,
        results=results,
    )


def _wrap_result(
    result: _impl.Phase29ShadowScoreResult,
    *,
    shadow_output_type: str,
) -> Phase29ShadowScoreResult:
    adjusted = replace(result, shadow_output_type=shadow_output_type)
    return Phase29ShadowScoreResult(
        shadow_output_id=adjusted.shadow_output_id,
        shadow_output_type=adjusted.shadow_output_type,
        model_family=adjusted.model_family,
        model_version=adjusted.model_version,
        input_snapshot_id=adjusted.input_snapshot_id,
        rendered_at=adjusted.rendered_at,
        subject_record_family=adjusted.subject_record_family,
        subject_record_id=adjusted.subject_record_id,
        supporting_feature_snapshot_id=adjusted.supporting_feature_snapshot_id,
        review_required=adjusted.review_required,
        registry_posture=adjusted.registry_posture,
        authority_posture=adjusted.authority_posture,
        status=adjusted.status,
        anomaly_score=adjusted.anomaly_score,
        feature_provenance=adjusted.feature_provenance,
        label_provenance=adjusted.label_provenance,
        operator_summary=adjusted.operator_summary,
    )


def __getattr__(name: str) -> object:
    return getattr(_impl, name)


__all__ = [
    "Phase29OfflineShadowScoringSnapshot",
    "Phase29ShadowScoreResult",
    "Phase29ShadowScoringError",
    "Phase29ShadowStreamingBaselineScorer",
    "score_shadow_dataset_offline",
]
