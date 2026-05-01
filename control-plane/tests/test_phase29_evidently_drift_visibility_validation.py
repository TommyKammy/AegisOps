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


from aegisops_control_plane.models import EvidenceRecord, ReconciliationRecord
from aegisops_control_plane.ml_shadow.drift_visibility import (
    Phase29EvidentlyDriftVisibilityError,
    build_phase29_evidently_drift_visibility_report,
)
from aegisops_control_plane.ml_shadow.dataset import (
    Phase29ShadowDatasetSnapshot,
    generate_reviewed_shadow_dataset,
)
from support.service_persistence import ServicePersistenceTestBase


class Phase29EvidentlyDriftVisibilityValidationTests(ServicePersistenceTestBase):
    def test_drift_report_stays_shadow_only_and_correlates_source_and_feature_health(
        self,
    ) -> None:
        _store, _service, reference_snapshot, candidate_snapshot, rendered_at = (
            self._build_drift_snapshots()
        )

        report = build_phase29_evidently_drift_visibility_report(
            reference_snapshot=reference_snapshot,
            candidate_snapshot=candidate_snapshot,
            rendered_at=rendered_at,
            stale_feature_after=timedelta(minutes=30),
        )

        self.assertEqual(report.registry_posture, "shadow-only")
        self.assertEqual(report.authority_posture, "non-authoritative")
        self.assertEqual(report.status, "degraded")
        self.assertEqual(report.drift_surface, "reviewed-equivalent")
        self.assertEqual(report.reference_snapshot_id, reference_snapshot.snapshot_id)
        self.assertEqual(report.candidate_snapshot_id, candidate_snapshot.snapshot_id)
        self.assertEqual(report.subject_count, 1)

        subject = report.subjects[0]
        self.assertEqual(subject.subject_record_family, "recommendation")
        self.assertEqual(subject.source_health_state, "stale")
        self.assertEqual(subject.source_health_ingest_disposition, "stale")
        self.assertEqual(subject.correlation_status, "source-health-correlated")
        self.assertEqual(subject.feature_drift_count, 2)
        self.assertGreater(subject.shadow_data_drift_ratio, 0.0)
        self.assertEqual(subject.feature_health["source_family"]["status"], "stale")
        self.assertEqual(
            subject.feature_health["source_health_state"]["status"],
            "degraded",
        )
        self.assertEqual(
            subject.feature_health["source_health_state"]["linked_source_health_state"],
            "stale",
        )
        self.assertEqual(
            subject.drifted_features["source_health_state"]["candidate_value"],
            "stale",
        )
        self.assertEqual(
            subject.drifted_features["source_health_state"]["reference_value"],
            "resolved",
        )
        self.assertEqual(
            subject.feature_health["source_family"]["provenance"][
                "feature_source_record_family"
            ],
            "Alert",
        )

    def test_drift_report_fails_closed_when_candidate_snapshot_lacks_source_health(self) -> None:
        _store, _service, reference_snapshot, candidate_snapshot, rendered_at = (
            self._build_drift_snapshots()
        )
        broken_candidate = Phase29ShadowDatasetSnapshot(
            snapshot_id=candidate_snapshot.snapshot_id,
            extraction_spec_version=candidate_snapshot.extraction_spec_version,
            snapshot_timestamp=candidate_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **candidate_snapshot.examples[0],
                    "features": {
                        key: value
                        for key, value in candidate_snapshot.examples[0]["features"].items()
                        if key != "source_health_state"
                    },
                },
            ),
        )

        with self.assertRaisesRegex(
            Phase29EvidentlyDriftVisibilityError,
            "candidate snapshot is missing required source-health feature",
        ):
            build_phase29_evidently_drift_visibility_report(
                reference_snapshot=reference_snapshot,
                candidate_snapshot=broken_candidate,
                rendered_at=rendered_at,
                stale_feature_after=timedelta(minutes=30),
            )

    def test_drift_report_fails_closed_when_required_feature_entry_is_not_a_mapping(
        self,
    ) -> None:
        _store, _service, reference_snapshot, candidate_snapshot, rendered_at = (
            self._build_drift_snapshots()
        )
        broken_candidate = Phase29ShadowDatasetSnapshot(
            snapshot_id=candidate_snapshot.snapshot_id,
            extraction_spec_version=candidate_snapshot.extraction_spec_version,
            snapshot_timestamp=candidate_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **candidate_snapshot.examples[0],
                    "features": {
                        **candidate_snapshot.examples[0]["features"],
                        "source_health_state": "stale",
                    },
                },
            ),
        )

        with self.assertRaisesRegex(
            Phase29EvidentlyDriftVisibilityError,
            "candidate\\.features\\.source_health_state must be a mapping",
        ):
            build_phase29_evidently_drift_visibility_report(
                reference_snapshot=reference_snapshot,
                candidate_snapshot=broken_candidate,
                rendered_at=rendered_at,
                stale_feature_after=timedelta(minutes=30),
            )

    def test_drift_report_fails_closed_when_candidate_omits_reviewed_baseline_feature(
        self,
    ) -> None:
        _store, _service, reference_snapshot, candidate_snapshot, rendered_at = (
            self._build_drift_snapshots()
        )
        broken_candidate = Phase29ShadowDatasetSnapshot(
            snapshot_id=candidate_snapshot.snapshot_id,
            extraction_spec_version=candidate_snapshot.extraction_spec_version,
            snapshot_timestamp=candidate_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **candidate_snapshot.examples[0],
                    "features": {
                        key: value
                        for key, value in candidate_snapshot.examples[0]["features"].items()
                        if key != "source_family"
                    },
                },
            ),
        )

        with self.assertRaisesRegex(
            Phase29EvidentlyDriftVisibilityError,
            "candidate snapshot is missing reviewed baseline features: source_family",
        ):
            build_phase29_evidently_drift_visibility_report(
                reference_snapshot=reference_snapshot,
                candidate_snapshot=broken_candidate,
                rendered_at=rendered_at,
                stale_feature_after=timedelta(minutes=30),
            )

    def test_drift_only_subject_rolls_up_as_drift_detected(self) -> None:
        _store, _service, reference_snapshot, _candidate_snapshot, rendered_at = (
            self._build_drift_snapshots()
        )
        reference_example = reference_snapshot.examples[0]
        candidate_snapshot = Phase29ShadowDatasetSnapshot(
            snapshot_id="snapshot-phase29-drift-only-candidate",
            extraction_spec_version=reference_snapshot.extraction_spec_version,
            snapshot_timestamp=reference_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **reference_example,
                    "features": {
                        **reference_example["features"],
                        "source_family": {
                            **reference_example["features"]["source_family"],
                            "value": "entra_id",
                        },
                    },
                },
            ),
        )

        report = build_phase29_evidently_drift_visibility_report(
            reference_snapshot=reference_snapshot,
            candidate_snapshot=candidate_snapshot,
            rendered_at=rendered_at,
            stale_feature_after=timedelta(days=1),
        )

        self.assertEqual(report.status, "drift-detected")
        subject = report.subjects[0]
        self.assertEqual(subject.correlation_status, "drift-detected")
        self.assertEqual(subject.status, "unresolved")
        self.assertEqual(subject.feature_drift_count, 1)

    def _build_drift_snapshots(
        self,
    ) -> tuple[object, object, Phase29ShadowDatasetSnapshot, Phase29ShadowDatasetSnapshot, datetime]:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Phase 29 drift visibility must stay tied to reviewed evidence.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Track whether source substrate drift explains shadow-model instability.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Keep drift visibility advisory and anchored to reviewed source health.",
        )
        decided_at = reviewed_at + timedelta(minutes=5)
        accepted_recommendation = service.persist_record(
            replace(recommendation, lifecycle_state="accepted"),
            transitioned_at=decided_at,
        )
        anchor_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-drift-anchor-001",
                source_record_id="reviewed-source-phase29-drift-anchor-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/drift-anchor",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-drift-anchor-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "ambiguity_badge": "unresolved",
                },
                content={"summary": {"kind": "anchor"}},
            )
        )
        linked_case = service.persist_record(
            replace(
                promoted_case,
                evidence_ids=(*promoted_case.evidence_ids, anchor_evidence.evidence_id),
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase29-drift-healthy-001",
                subject_linkage={
                    "alert_ids": (linked_case.alert_id,),
                    "case_ids": (linked_case.case_id,),
                    "recommendation_ids": (accepted_recommendation.recommendation_id,),
                },
                alert_id=linked_case.alert_id,
                finding_id=linked_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=f"case:{linked_case.case_id}:source-health",
                first_seen_at=reviewed_at,
                last_seen_at=decided_at,
                ingest_disposition="matched",
                mismatch_summary="Reviewed source-health baseline is matched and resolved.",
                compared_at=decided_at,
                lifecycle_state="resolved",
            )
        )

        reference_snapshot = generate_reviewed_shadow_dataset(
            service,
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=decided_at,
        )

        degraded_at = decided_at + timedelta(hours=2)
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase29-drift-stale-001",
                subject_linkage={
                    "alert_ids": (linked_case.alert_id,),
                    "case_ids": (linked_case.case_id,),
                    "recommendation_ids": (accepted_recommendation.recommendation_id,),
                },
                alert_id=linked_case.alert_id,
                finding_id=linked_case.finding_id,
                analytic_signal_id=None,
                execution_run_id=None,
                linked_execution_run_ids=(),
                correlation_key=f"case:{linked_case.case_id}:source-health",
                first_seen_at=reviewed_at,
                last_seen_at=degraded_at,
                ingest_disposition="stale",
                mismatch_summary="Reviewed source drift made feature inputs stale.",
                compared_at=degraded_at,
                lifecycle_state="stale",
            )
        )

        candidate_snapshot = generate_reviewed_shadow_dataset(
            service,
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=degraded_at,
        )
        candidate_example = candidate_snapshot.examples[0]
        candidate_snapshot = Phase29ShadowDatasetSnapshot(
            snapshot_id=candidate_snapshot.snapshot_id,
            extraction_spec_version=candidate_snapshot.extraction_spec_version,
            snapshot_timestamp=candidate_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **candidate_example,
                    "features": {
                        **candidate_example["features"],
                        "source_family": {
                            **candidate_example["features"]["source_family"],
                            "provenance": {
                                **candidate_example["features"]["source_family"]["provenance"],
                                "feature_snapshot_timestamp": reviewed_at.isoformat(),
                            },
                        },
                    },
                },
            ),
        )
        return store, service, reference_snapshot, candidate_snapshot, degraded_at


if __name__ == "__main__":
    import unittest

    unittest.main()
