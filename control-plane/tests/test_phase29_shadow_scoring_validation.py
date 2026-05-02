from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pathlib
import sys


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
for candidate in (CONTROL_PLANE_ROOT, TESTS_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


from aegisops.control_plane.models import EvidenceRecord, ReconciliationRecord
from aegisops.control_plane.ml_shadow.dataset import (
    Phase29ShadowDatasetSnapshot,
    generate_reviewed_shadow_dataset,
)
from aegisops.control_plane.ml_shadow.scoring import (
    Phase29ShadowScoringError,
    Phase29ShadowStreamingBaselineScorer,
    score_shadow_dataset_offline,
)
import aegisops_control_plane.phase29_shadow_scoring as legacy_shadow_scoring
from support.service_persistence import ServicePersistenceTestBase


class Phase29ShadowScoringValidationTests(ServicePersistenceTestBase):
    def test_offline_shadow_scoring_emits_lineage_backed_shadow_only_results(self) -> None:
        store, _service, dataset_snapshot, decided_at = self._build_shadow_dataset_snapshot()
        initial_record_counts = {
            record_type.__name__: len(store.list(record_type))
            for record_type in (EvidenceRecord, ReconciliationRecord)
        }

        scored_snapshot = score_shadow_dataset_offline(
            dataset_snapshot=dataset_snapshot,
            scoring_spec_version="phase29-shadow-scoring-v1",
            model_family="baseline-isolation-forest",
            model_version="candidate-2026-04-20",
            training_data_snapshot_id=dataset_snapshot.snapshot_id,
            feature_schema_version="phase29-shadow-features-v1",
            label_schema_version="phase29-shadow-labels-v1",
            lineage_review_note_id="note-phase29-shadow-001",
            scored_at=decided_at + timedelta(minutes=1),
        )

        self.assertEqual(scored_snapshot.snapshot_id, dataset_snapshot.snapshot_id)
        self.assertEqual(scored_snapshot.scoring_spec_version, "phase29-shadow-scoring-v1")
        self.assertEqual(scored_snapshot.shadow_output_type, "recommendation_draft")
        self.assertEqual(scored_snapshot.registry_posture, "shadow-only")
        self.assertEqual(scored_snapshot.authority_posture, "non-authoritative")
        self.assertEqual(scored_snapshot.example_count, dataset_snapshot.example_count)
        self.assertEqual(len(scored_snapshot.results), dataset_snapshot.example_count)

        result = scored_snapshot.results[0]
        self.assertEqual(result.subject_record_family, "recommendation")
        self.assertEqual(result.subject_record_id, dataset_snapshot.examples[0]["subject_record_id"])
        self.assertEqual(result.status, "shadow-ready")
        self.assertTrue(result.review_required)
        self.assertEqual(result.shadow_output_type, "recommendation_draft")
        self.assertEqual(result.registry_posture, "shadow-only")
        self.assertEqual(result.authority_posture, "non-authoritative")
        self.assertEqual(result.input_snapshot_id, dataset_snapshot.snapshot_id)
        self.assertGreaterEqual(result.anomaly_score, 0.0)
        self.assertLessEqual(result.anomaly_score, 1.0)
        self.assertEqual(result.feature_provenance["source_family"]["feature_source_record_family"], "Alert")
        self.assertEqual(
            result.feature_provenance["case_lifecycle_state"]["feature_source_record_family"],
            "Case",
        )
        self.assertIn("shadow/non-authoritative", result.operator_summary["summary"])
        self.assertEqual(
            result.operator_summary["candidate_recommendations"][0]["shadow_posture"],
            "shadow/non-authoritative",
        )

        final_record_counts = {
            record_type.__name__: len(store.list(record_type))
            for record_type in (EvidenceRecord, ReconciliationRecord)
        }
        self.assertEqual(final_record_counts, initial_record_counts)

    def test_legacy_shadow_scoring_import_path_preserves_adapter_surface(self) -> None:
        _store, _service, dataset_snapshot, decided_at = self._build_shadow_dataset_snapshot()

        scored_snapshot = legacy_shadow_scoring.score_shadow_dataset_offline(
            dataset_snapshot=dataset_snapshot,
            scoring_spec_version="phase29-shadow-scoring-v1",
            model_family="baseline-isolation-forest",
            model_version="candidate-2026-04-20",
            training_data_snapshot_id=dataset_snapshot.snapshot_id,
            feature_schema_version="phase29-shadow-features-v1",
            label_schema_version="phase29-shadow-labels-v1",
            lineage_review_note_id="note-phase29-shadow-001",
            scored_at=decided_at + timedelta(minutes=1),
            shadow_output_type="legacy_shadow_recommendation",
        )

        self.assertIsInstance(
            scored_snapshot,
            legacy_shadow_scoring.Phase29OfflineShadowScoringSnapshot,
        )
        self.assertEqual(scored_snapshot.shadow_output_type, "legacy_shadow_recommendation")
        self.assertEqual(scored_snapshot.scored_examples, scored_snapshot.results)
        result = scored_snapshot.scored_examples[0]
        self.assertIsInstance(result, legacy_shadow_scoring.Phase29ShadowScoreResult)
        self.assertEqual(result.shadow_output_type, "legacy_shadow_recommendation")
        self.assertEqual(result.feature_frequencies_at_inference_time, {})

        scorer = legacy_shadow_scoring.Phase29ShadowStreamingBaselineScorer(
            scoring_spec_version="phase29-shadow-streaming-v1",
            model_family="river-half-space-trees",
            model_version="shadow-stream-2026-04-20",
            feature_schema_version="phase29-shadow-features-v1",
            label_schema_version="phase29-shadow-labels-v1",
            lineage_review_note_id="note-phase29-shadow-001",
            shadow_output_type="legacy_stream_recommendation",
        )
        streaming_result = scorer.score_example(
            dataset_example=dataset_snapshot.examples[0],
            input_snapshot_id=dataset_snapshot.snapshot_id,
            rendered_at=decided_at + timedelta(minutes=2),
        )

        self.assertIsInstance(streaming_result, legacy_shadow_scoring.Phase29ShadowScoreResult)
        self.assertEqual(streaming_result.shadow_output_type, "legacy_stream_recommendation")
        self.assertEqual(streaming_result.feature_frequencies_at_inference_time, {})

    def test_offline_shadow_scoring_fails_closed_when_training_snapshot_binding_drifts(self) -> None:
        _store, _service, dataset_snapshot, decided_at = self._build_shadow_dataset_snapshot()

        with self.assertRaisesRegex(
            Phase29ShadowScoringError,
            "training_data_snapshot_id must match dataset_snapshot.snapshot_id",
        ):
            score_shadow_dataset_offline(
                dataset_snapshot=dataset_snapshot,
                scoring_spec_version="phase29-shadow-scoring-v1",
                model_family="baseline-isolation-forest",
                model_version="candidate-2026-04-20",
                training_data_snapshot_id="snapshot-drifted",
                feature_schema_version="phase29-shadow-features-v1",
                label_schema_version="phase29-shadow-labels-v1",
                lineage_review_note_id="note-phase29-shadow-001",
                scored_at=decided_at + timedelta(minutes=1),
            )

    def test_online_shadow_scoring_stays_shadow_only_and_requires_lineage(self) -> None:
        _store, _service, dataset_snapshot, decided_at = self._build_shadow_dataset_snapshot()
        scorer = Phase29ShadowStreamingBaselineScorer(
            scoring_spec_version="phase29-shadow-streaming-v1",
            model_family="river-half-space-trees",
            model_version="shadow-stream-2026-04-20",
            feature_schema_version="phase29-shadow-features-v1",
            label_schema_version="phase29-shadow-labels-v1",
            lineage_review_note_id="note-phase29-shadow-001",
        )

        result = scorer.score_example(
            dataset_example=dataset_snapshot.examples[0],
            input_snapshot_id=dataset_snapshot.snapshot_id,
            rendered_at=decided_at + timedelta(minutes=2),
        )

        self.assertEqual(result.registry_posture, "shadow-only")
        self.assertEqual(result.authority_posture, "non-authoritative")
        self.assertTrue(result.review_required)
        self.assertIn("shadow/non-authoritative", result.operator_summary["summary"])
        self.assertEqual(result.supporting_feature_snapshot_id, dataset_snapshot.snapshot_id)

        broken_snapshot = Phase29ShadowDatasetSnapshot(
            snapshot_id="snapshot-broken",
            extraction_spec_version=dataset_snapshot.extraction_spec_version,
            snapshot_timestamp=dataset_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **dataset_snapshot.examples[0],
                    "features": {
                        **dataset_snapshot.examples[0]["features"],
                        "source_family": {
                            "value": "github_audit",
                            "provenance": {
                                "feature_source_record_family": "Alert",
                                "feature_source_record_id": "alert-broken",
                                "feature_source_field_path": "reviewed_context.source.source_family",
                                "feature_extraction_spec_version": "phase29-shadow-dataset-v1",
                                "feature_reviewed_linkage": "subject-alert-link",
                                "feature_source_provenance_classification": None,
                                "feature_source_reviewed_by": "analyst-001",
                            },
                        },
                    },
                },
            ),
        )

        with self.assertRaisesRegex(
            Phase29ShadowScoringError,
            "missing required feature provenance",
        ):
            scorer.score_example(
                dataset_example=broken_snapshot.examples[0],
                input_snapshot_id=broken_snapshot.snapshot_id,
                rendered_at=decided_at + timedelta(minutes=3),
            )

    def test_shadow_scoring_fails_closed_when_feature_value_is_missing(self) -> None:
        _store, _service, dataset_snapshot, decided_at = self._build_shadow_dataset_snapshot()
        broken_snapshot = Phase29ShadowDatasetSnapshot(
            snapshot_id=dataset_snapshot.snapshot_id,
            extraction_spec_version=dataset_snapshot.extraction_spec_version,
            snapshot_timestamp=dataset_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **dataset_snapshot.examples[0],
                    "features": {
                        **dataset_snapshot.examples[0]["features"],
                        "source_family": {
                            "provenance": dataset_snapshot.examples[0]["features"]["source_family"][
                                "provenance"
                            ],
                        },
                    },
                },
            ),
        )

        with self.assertRaisesRegex(
            Phase29ShadowScoringError,
            "missing required feature value on source_family",
        ):
            score_shadow_dataset_offline(
                dataset_snapshot=broken_snapshot,
                scoring_spec_version="phase29-shadow-scoring-v1",
                model_family="baseline-isolation-forest",
                model_version="candidate-2026-04-20",
                training_data_snapshot_id=broken_snapshot.snapshot_id,
                feature_schema_version="phase29-shadow-features-v1",
                label_schema_version="phase29-shadow-labels-v1",
                lineage_review_note_id="note-phase29-shadow-001",
                scored_at=decided_at + timedelta(minutes=1),
            )

    def test_shadow_scoring_fails_closed_for_invalid_or_naive_feature_timestamps(self) -> None:
        _store, _service, dataset_snapshot, decided_at = self._build_shadow_dataset_snapshot()

        for bad_timestamp, expected_message in (
            (
                "not-a-timestamp",
                "source_family.feature_snapshot_timestamp must be a valid ISO-8601 timestamp",
            ),
            (
                "2026-04-20T10:00:00",
                "source_family.feature_snapshot_timestamp must include a timezone offset",
            ),
        ):
            with self.subTest(bad_timestamp=bad_timestamp):
                broken_snapshot = Phase29ShadowDatasetSnapshot(
                    snapshot_id=dataset_snapshot.snapshot_id,
                    extraction_spec_version=dataset_snapshot.extraction_spec_version,
                    snapshot_timestamp=dataset_snapshot.snapshot_timestamp,
                    example_count=1,
                    examples=(
                        {
                            **dataset_snapshot.examples[0],
                            "features": {
                                **dataset_snapshot.examples[0]["features"],
                                "source_family": {
                                    **dataset_snapshot.examples[0]["features"]["source_family"],
                                    "provenance": {
                                        **dataset_snapshot.examples[0]["features"]["source_family"][
                                            "provenance"
                                        ],
                                        "feature_snapshot_timestamp": bad_timestamp,
                                    },
                                },
                            },
                        },
                    ),
                )

                with self.assertRaisesRegex(
                    Phase29ShadowScoringError,
                    expected_message,
                ):
                    score_shadow_dataset_offline(
                        dataset_snapshot=broken_snapshot,
                        scoring_spec_version="phase29-shadow-scoring-v1",
                        model_family="baseline-isolation-forest",
                        model_version="candidate-2026-04-20",
                        training_data_snapshot_id=broken_snapshot.snapshot_id,
                        feature_schema_version="phase29-shadow-features-v1",
                        label_schema_version="phase29-shadow-labels-v1",
                        lineage_review_note_id="note-phase29-shadow-001",
                        scored_at=decided_at + timedelta(minutes=1),
                    )

    def _build_shadow_dataset_snapshot(
        self,
    ) -> tuple[object, object, Phase29ShadowDatasetSnapshot, datetime]:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Reviewed feature extraction must stay anchored to the case.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Privilege-impacting repository change requires bounded review.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Confirm the reviewed recommendation remains advisory-only.",
        )
        decided_at = reviewed_at + timedelta(minutes=5)
        accepted_recommendation = service.persist_record(
            replace(
                recommendation,
                lifecycle_state="accepted",
            ),
            transitioned_at=decided_at,
        )
        disposed_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Preserve the reviewed business-hours handoff as bounded context.",
            recorded_at=decided_at,
        )
        anchored_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-shadow-anchor-001",
                source_record_id="reviewed-source-phase29-001",
                alert_id=disposed_case.alert_id,
                case_id=disposed_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/source-health",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "ambiguity_badge": "unresolved",
                },
                content={"summary": {"kind": "anchor"}},
            )
        )
        service.persist_record(
            replace(
                disposed_case,
                evidence_ids=(*disposed_case.evidence_ids, anchored_evidence.evidence_id),
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase29-shadow-001",
                subject_linkage={
                    "alert_ids": (disposed_case.alert_id,),
                    "case_ids": (disposed_case.case_id,),
                    "recommendation_ids": (accepted_recommendation.recommendation_id,),
                },
                alert_id=disposed_case.alert_id,
                finding_id=disposed_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=f"case:{disposed_case.case_id}:source-health",
                first_seen_at=reviewed_at,
                last_seen_at=decided_at,
                ingest_disposition="stale",
                mismatch_summary="reviewed source-health context only",
                compared_at=decided_at,
                lifecycle_state="stale",
            )
        )
        return (
            store,
            service,
            generate_reviewed_shadow_dataset(
                service,
                extraction_spec_version="phase29-shadow-dataset-v1",
                snapshot_timestamp=decided_at,
            ),
            decided_at,
        )
