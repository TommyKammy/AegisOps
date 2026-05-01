from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
TESTS_ROOT = pathlib.Path(__file__).resolve().parent
REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
for candidate in (CONTROL_PLANE_ROOT, TESTS_ROOT):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))


from aegisops_control_plane.models import (
    ActionExecutionRecord,
    ActionRequestRecord,
    AlertRecord,
    ApprovalDecisionRecord,
    CaseRecord,
    EvidenceRecord,
    LeadRecord,
    ObservationRecord,
    RecommendationRecord,
    ReconciliationRecord,
)
from aegisops_control_plane.ml_shadow.drift_visibility import (
    Phase29EvidentlyDriftVisibilityError,
    build_phase29_evidently_drift_visibility_report,
)
from aegisops_control_plane.ml_shadow.dataset import (
    Phase29ShadowDatasetSnapshot,
    generate_reviewed_shadow_dataset,
)
from aegisops_control_plane.ml_shadow.scoring import (
    Phase29ShadowScoringError,
    score_shadow_dataset_offline,
)
from support.service_persistence import ServicePersistenceTestBase


_AUTHORITATIVE_RECORD_TYPES = (
    AlertRecord,
    CaseRecord,
    EvidenceRecord,
    ObservationRecord,
    LeadRecord,
    RecommendationRecord,
    ApprovalDecisionRecord,
    ActionRequestRecord,
    ActionExecutionRecord,
    ReconciliationRecord,
)


class Phase29NoAuthorityMlAndOptionalNetworkValidationTests(ServicePersistenceTestBase):
    def test_shadow_outputs_and_optional_network_context_stay_non_authoritative(self) -> None:
        (
            store,
            _service,
            linked_case,
            accepted_recommendation,
            reference_snapshot,
            candidate_snapshot,
            rendered_at,
        ) = self._build_phase29_shadow_and_optional_network_context()
        initial_counts = self._record_counts(store)

        scored_snapshot = score_shadow_dataset_offline(
            dataset_snapshot=candidate_snapshot,
            scoring_spec_version="phase29-shadow-scoring-v1",
            model_family="baseline-isolation-forest",
            model_version="candidate-2026-04-20",
            training_data_snapshot_id=candidate_snapshot.snapshot_id,
            feature_schema_version="phase29-shadow-features-v1",
            label_schema_version="phase29-shadow-labels-v1",
            lineage_review_note_id="note-phase29-shadow-001",
            scored_at=rendered_at,
        )
        drift_report = build_phase29_evidently_drift_visibility_report(
            reference_snapshot=reference_snapshot,
            candidate_snapshot=candidate_snapshot,
            rendered_at=rendered_at,
            stale_feature_after=timedelta(minutes=30),
        )

        self.assertEqual(scored_snapshot.registry_posture, "shadow-only")
        self.assertEqual(scored_snapshot.authority_posture, "non-authoritative")
        self.assertEqual(scored_snapshot.results[0].status, "shadow-ready")
        self.assertTrue(scored_snapshot.results[0].review_required)
        self.assertEqual(drift_report.registry_posture, "shadow-only")
        self.assertEqual(drift_report.authority_posture, "non-authoritative")
        self.assertEqual(drift_report.status, "degraded")
        self.assertEqual(drift_report.subjects[0].correlation_status, "source-health-correlated")
        self.assertEqual(drift_report.subjects[0].source_health_state, "stale")

        current_case = store.get(CaseRecord, linked_case.case_id)
        current_recommendation = store.get(
            RecommendationRecord,
            accepted_recommendation.recommendation_id,
        )
        self.assertIsNotNone(current_case)
        self.assertIsNotNone(current_recommendation)
        self.assertEqual(current_case.lifecycle_state, linked_case.lifecycle_state)
        self.assertEqual(current_case.evidence_ids, linked_case.evidence_ids)
        self.assertEqual(
            current_recommendation.lifecycle_state,
            accepted_recommendation.lifecycle_state,
        )
        self.assertEqual(
            self._record_counts(store),
            initial_counts,
        )

    def test_shadow_scoring_fails_closed_when_label_provenance_is_missing(self) -> None:
        (
            _store,
            _service,
            _linked_case,
            _accepted_recommendation,
            _reference_snapshot,
            candidate_snapshot,
            rendered_at,
        ) = self._build_phase29_shadow_and_optional_network_context()

        example = candidate_snapshot.examples[0]
        broken_snapshot = Phase29ShadowDatasetSnapshot(
            snapshot_id=candidate_snapshot.snapshot_id,
            extraction_spec_version=candidate_snapshot.extraction_spec_version,
            snapshot_timestamp=candidate_snapshot.snapshot_timestamp,
            example_count=1,
            examples=(
                {
                    **example,
                    "label": {
                        **example["label"],
                        "provenance": {
                            key: value
                            for key, value in example["label"]["provenance"].items()
                            if key != "label_record_id"
                        },
                    },
                },
            ),
        )

        with self.assertRaisesRegex(
            Phase29ShadowScoringError,
            "missing required label provenance: label_record_id",
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
                scored_at=rendered_at,
            )

    def test_optional_network_boundary_docs_and_validation_artifacts_exist(self) -> None:
        design_text = self._read(
            "docs/phase-29-optional-suricata-evidence-pack-boundary.md"
        )
        validation_text = self._read(
            "docs/phase-29-reviewed-ml-shadow-mode-and-optional-network-evidence-pack-validation.md"
        )
        script_text = self._read(
            "scripts/verify-phase-29-reviewed-ml-shadow-mode-and-optional-network-evidence-pack.sh"
        )

        for term in (
            "Suricata integration is optional, disabled by default, and subordinate to the AegisOps-owned control-plane record chain.",
            "Suricata-derived output must not replace AegisOps-owned alert truth, case truth, evidence truth, approval truth, execution truth, or reconciliation truth.",
            "The path must fail closed when provenance is partial",
        ):
            self.assertIn(term, design_text)

        for term in (
            "# Phase 29 Reviewed ML Shadow-Mode and Optional Network Evidence-Pack Validation",
            "Validation status: PASS",
            "ML scores, drift surfaces, and shadow recommendations remain advisory-only and non-authoritative.",
            "Optional network evidence remains disabled by default, subordinate, and unable to become alert, case, approval, execution, or reconciliation truth.",
            "Missing provenance, missing labels, stale features, drift alarms, disabled optional-network paths, and optional-network outage paths all fail closed or degrade explicitly.",
            "python3 -m unittest control-plane.tests.test_phase29_no_authority_ml_and_optional_network_validation",
            "bash scripts/verify-phase-29-reviewed-ml-shadow-mode-and-optional-network-evidence-pack.sh",
        ):
            self.assertIn(term, validation_text)

        for term in (
            'validation_doc="${repo_root}/docs/phase-29-reviewed-ml-shadow-mode-and-optional-network-evidence-pack-validation.md"',
            'docs_test="${repo_root}/control-plane/tests/test_phase29_no_authority_ml_and_optional_network_validation.py"',
            'require_fixed_line "${validation_doc}"',
            'Phase 29 ML shadow-mode and optional network validation artifacts are present and aligned.',
        ):
            self.assertIn(term, script_text)

    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _record_counts(store: object) -> dict[str, int]:
        return {
            record_type.__name__: len(store.list(record_type))
            for record_type in _AUTHORITATIVE_RECORD_TYPES
        }

    def _build_phase29_shadow_and_optional_network_context(
        self,
    ) -> tuple[
        object,
        object,
        CaseRecord,
        RecommendationRecord,
        Phase29ShadowDatasetSnapshot,
        Phase29ShadowDatasetSnapshot,
        datetime,
    ]:
        store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement=(
                "Phase 29 validation keeps ML shadow outputs and optional network evidence "
                "subordinate to reviewed case truth."
            ),
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale=(
                "Track reviewed source-health drift without widening authority."
            ),
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome=(
                "Keep Phase 29 ML and optional network evidence advisory-only."
            ),
        )
        decided_at = reviewed_at + timedelta(minutes=5)
        accepted_recommendation = service.persist_record(
            replace(recommendation, lifecycle_state="accepted"),
            transitioned_at=decided_at,
        )
        linked_case = service.record_case_disposition(
            case_id=promoted_case.case_id,
            disposition="business_hours_handoff",
            rationale="Preserve explicit reviewed workflow state before any shadow analysis.",
            recorded_at=decided_at,
        )
        anchor_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-shadow-anchor-001",
                source_record_id="reviewed-source-phase29-001",
                alert_id=linked_case.alert_id,
                case_id=linked_case.case_id,
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
                content={
                    "summary": {"kind": "anchor"},
                    "optional_network": {
                        "path_status": "disabled",
                        "pack_role": "subordinate-evidence-pack",
                        "outage_disposition": "degrade-explicitly",
                    },
                },
            )
        )
        linked_case = service.persist_record(
            replace(
                linked_case,
                evidence_ids=(*linked_case.evidence_ids, anchor_evidence.evidence_id),
            )
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase29-shadow-healthy-001",
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
                reconciliation_id="reconciliation-phase29-shadow-stale-001",
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
                mismatch_summary=(
                    "Reviewed source drift made shadow inputs stale while optional network "
                    "evidence stayed disabled."
                ),
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

        return (
            store,
            service,
            linked_case,
            accepted_recommendation,
            reference_snapshot,
            candidate_snapshot,
            degraded_at.replace(tzinfo=timezone.utc)
            if degraded_at.tzinfo is None
            else degraded_at,
        )


if __name__ == "__main__":
    unittest.main()
