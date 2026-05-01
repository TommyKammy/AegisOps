from __future__ import annotations

from dataclasses import replace
from datetime import timedelta
import pathlib
import sys


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


from aegisops_control_plane.models import EvidenceRecord, ReconciliationRecord
from aegisops_control_plane.ml_shadow.dataset import (
    Phase29ShadowDatasetGenerationError,
    generate_reviewed_shadow_dataset,
)
from tests.test_service_persistence import ServicePersistenceTestBase


class _UnsortedLifecycleTransitionService:
    def __init__(self, inner: object) -> None:
        self._inner = inner
        self._store = inner._store

    def list_lifecycle_transitions(
        self,
        record_family: str,
        record_id: str,
    ) -> tuple[object, ...]:
        return tuple(
            reversed(self._inner.list_lifecycle_transitions(record_family, record_id))
        )


class Phase29ShadowDatasetGenerationValidationTests(ServicePersistenceTestBase):
    def test_generator_emits_reproducible_shadow_examples_with_lineage(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
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

        first_snapshot = generate_reviewed_shadow_dataset(
            service,
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=decided_at,
        )
        second_snapshot = generate_reviewed_shadow_dataset(
            service,
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=decided_at,
        )

        self.assertEqual(first_snapshot.snapshot_id, second_snapshot.snapshot_id)
        self.assertEqual(first_snapshot.example_count, 1)
        self.assertEqual(first_snapshot.examples, second_snapshot.examples)

        example = first_snapshot.examples[0]
        self.assertEqual(example["subject_record_family"], "recommendation")
        self.assertEqual(
            example["subject_record_id"],
            accepted_recommendation.recommendation_id,
        )
        self.assertEqual(example["label"]["value"], "accepted")
        self.assertEqual(example["label"]["provenance"]["label_record_family"], "Recommendation")
        self.assertEqual(
            example["label"]["provenance"]["label_record_id"],
            accepted_recommendation.recommendation_id,
        )
        self.assertEqual(
            example["features"]["case_triage_disposition"]["value"],
            "business_hours_handoff",
        )
        self.assertEqual(
            example["features"]["source_family"]["value"],
            "github_audit",
        )
        self.assertEqual(
            example["features"]["source_health_state"]["value"],
            "stale",
        )
        self.assertEqual(
            example["features"]["ambiguity_badges"]["value"],
            ["unresolved"],
        )
        self.assertEqual(
            example["features"]["ambiguity_badges"]["provenance"][
                "feature_source_record_family"
            ],
            "Evidence",
        )

    def test_generator_fails_closed_when_anchor_provenance_is_missing(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Missing lineage must block shadow dataset generation.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Fail closed when reviewed provenance is incomplete.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Do not synthesize training lineage from incomplete records.",
        )
        service.persist_record(
            replace(
                recommendation,
                lifecycle_state="accepted",
            ),
            transitioned_at=reviewed_at + timedelta(minutes=5),
        )
        broken_anchor = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-shadow-broken-001",
                source_record_id="reviewed-source-phase29-broken-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/broken",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                },
                content={"summary": {"kind": "broken-anchor"}},
            )
        )
        service.persist_record(
            replace(
                promoted_case,
                evidence_ids=(*promoted_case.evidence_ids, broken_anchor.evidence_id),
            )
        )

        with self.assertRaisesRegex(
            Phase29ShadowDatasetGenerationError,
            "missing required reviewed provenance",
        ):
            generate_reviewed_shadow_dataset(
                service,
                extraction_spec_version="phase29-shadow-dataset-v1",
                snapshot_timestamp=reviewed_at + timedelta(minutes=5),
            )

    def test_generator_uses_snapshot_timestamp_as_authoritative_cutoff(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Historical snapshots must not drift after later reviews.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Snapshot generation must honor authoritative review timing.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Keep offline shadow labels reproducible.",
        )
        accepted_at = reviewed_at + timedelta(minutes=5)
        accepted_recommendation = service.persist_record(
            replace(recommendation, lifecycle_state="accepted"),
            transitioned_at=accepted_at,
        )
        anchor_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-snapshot-anchor-001",
                source_record_id="reviewed-source-phase29-snapshot-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/snapshot-anchor",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-snapshot-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "ambiguity_badge": "unresolved",
                },
                content={"summary": {"kind": "snapshot-anchor"}},
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
                reconciliation_id="reconciliation-phase29-snapshot-001",
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
                correlation_key=f"case:{linked_case.case_id}:snapshot-health",
                first_seen_at=reviewed_at,
                last_seen_at=accepted_at,
                ingest_disposition="stale",
                mismatch_summary="Historical source-health state",
                compared_at=accepted_at,
                lifecycle_state="stale",
            )
        )

        later_reviewed_at = accepted_at + timedelta(minutes=10)
        service.persist_record(
            replace(accepted_recommendation, lifecycle_state="rejected"),
            transitioned_at=later_reviewed_at,
        )
        service.persist_record(
            ReconciliationRecord(
                reconciliation_id="reconciliation-phase29-snapshot-002",
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
                correlation_key=f"case:{linked_case.case_id}:snapshot-health",
                first_seen_at=later_reviewed_at,
                last_seen_at=later_reviewed_at,
                ingest_disposition="updated",
                mismatch_summary="Later state that must not leak into the older snapshot",
                compared_at=later_reviewed_at,
                lifecycle_state="resolved",
            )
        )

        historical_snapshot = generate_reviewed_shadow_dataset(
            service,
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=accepted_at,
        )

        self.assertEqual(historical_snapshot.example_count, 1)
        example = historical_snapshot.examples[0]
        self.assertEqual(example["label"]["value"], "accepted")
        self.assertEqual(
            example["label"]["provenance"]["label_decided_at"],
            accepted_at.isoformat(),
        )
        self.assertEqual(
            example["features"]["source_health_state"]["value"],
            "stale",
        )
        self.assertEqual(
            example["features"]["source_health_ingest_disposition"]["value"],
            "stale",
        )

    def test_generator_selects_latest_lifecycle_transition_from_unsorted_listing(
        self,
    ) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Dataset labels must not depend on lifecycle list ordering.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="The authoritative timestamp selects the label transition.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Keep shadow labels deterministic for unsorted stores.",
        )
        decided_at = reviewed_at + timedelta(minutes=5)
        accepted_recommendation = service.persist_record(
            replace(recommendation, lifecycle_state="accepted"),
            transitioned_at=decided_at,
        )
        anchor_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-unsorted-transition-anchor-001",
                source_record_id="reviewed-source-phase29-unsorted-transition-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/unsorted-transition-anchor",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-unsorted-transition-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "ambiguity_badge": "unresolved",
                },
                content={"summary": {"kind": "unsorted-transition-anchor"}},
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
                reconciliation_id="reconciliation-phase29-unsorted-transition-001",
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
                correlation_key=f"case:{linked_case.case_id}:unsorted-transition-health",
                first_seen_at=reviewed_at,
                last_seen_at=decided_at,
                ingest_disposition="matched",
                mismatch_summary="Lifecycle ordering should not affect source-health state",
                compared_at=decided_at,
                lifecycle_state="resolved",
            )
        )

        snapshot = generate_reviewed_shadow_dataset(
            _UnsortedLifecycleTransitionService(service),
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=decided_at,
        )

        self.assertEqual(snapshot.example_count, 1)
        example = snapshot.examples[0]
        self.assertEqual(
            example["subject_record_id"],
            accepted_recommendation.recommendation_id,
        )
        self.assertEqual(example["label"]["value"], "accepted")
        self.assertEqual(
            example["label"]["provenance"]["label_decided_at"],
            decided_at.isoformat(),
        )

    def test_generator_fails_closed_when_subject_records_mutate_after_snapshot(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Historical snapshots must reject newer subject record bodies.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Do not infer historical feature state from current records.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Keep shadow snapshots reproducible.",
        )
        decided_at = reviewed_at + timedelta(minutes=5)
        accepted_recommendation = service.persist_record(
            replace(recommendation, lifecycle_state="accepted"),
            transitioned_at=decided_at,
        )
        anchor_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-post-snapshot-anchor-001",
                source_record_id="reviewed-source-phase29-post-snapshot-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/post-snapshot-anchor",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-post-snapshot-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "ambiguity_badge": "unresolved",
                },
                content={"summary": {"kind": "post-snapshot-anchor"}},
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
                reconciliation_id="reconciliation-phase29-post-snapshot-001",
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
                correlation_key=f"case:{linked_case.case_id}:post-snapshot-health",
                first_seen_at=reviewed_at,
                last_seen_at=decided_at,
                ingest_disposition="matched",
                mismatch_summary="Historical source-health state",
                compared_at=decided_at,
                lifecycle_state="resolved",
            )
        )
        service.record_case_disposition(
            case_id=linked_case.case_id,
            disposition="closed_resolved",
            rationale="Later subject state must not rewrite the historical snapshot.",
            recorded_at=decided_at + timedelta(minutes=10),
        )

        with self.assertRaisesRegex(
            Phase29ShadowDatasetGenerationError,
            "post-snapshot lifecycle mutations",
        ):
            generate_reviewed_shadow_dataset(
                service,
                extraction_spec_version="phase29-shadow-dataset-v1",
                snapshot_timestamp=decided_at,
            )

    def test_generator_wraps_malformed_anchor_timestamp_in_dataset_error(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Malformed provenance timestamps must stay in dataset errors.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Timestamp parsing failures must not leak raw exceptions.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Block malformed reviewed provenance.",
        )
        decided_at = reviewed_at + timedelta(minutes=5)
        service.persist_record(
            replace(recommendation, lifecycle_state="accepted"),
            transitioned_at=decided_at,
        )
        broken_anchor = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-malformed-timestamp-001",
                source_record_id="reviewed-source-phase29-malformed-timestamp-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/malformed-timestamp",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-malformed-timestamp-001",
                    "timestamp": "not-a-timestamp",
                    "reviewed_by": "analyst-001",
                },
                content={"summary": {"kind": "malformed-timestamp"}},
            )
        )
        service.persist_record(
            replace(
                promoted_case,
                evidence_ids=(*promoted_case.evidence_ids, broken_anchor.evidence_id),
            )
        )

        with self.assertRaisesRegex(
            Phase29ShadowDatasetGenerationError,
            "expected timezone-aware ISO timestamp",
        ):
            generate_reviewed_shadow_dataset(
                service,
                extraction_spec_version="phase29-shadow-dataset-v1",
                snapshot_timestamp=decided_at,
            )

    def test_generator_emits_per_evidence_ambiguity_provenance(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Ambiguity features must preserve every contributing record.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Keep aggregate ambiguity lineage reconstructible.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Preserve per-record badge provenance.",
        )
        decided_at = reviewed_at + timedelta(minutes=5)
        accepted_recommendation = service.persist_record(
            replace(recommendation, lifecycle_state="accepted"),
            transitioned_at=decided_at,
        )
        anchor_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-ambiguity-anchor-001",
                source_record_id="reviewed-source-phase29-ambiguity-anchor-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/ambiguity-anchor",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-ambiguity-anchor-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "ambiguity_badge": "unresolved",
                },
                content={"summary": {"kind": "anchor"}},
            )
        )
        secondary_evidence = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-ambiguity-secondary-001",
                source_record_id="reviewed-source-phase29-ambiguity-secondary-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/ambiguity-secondary",
                acquired_at=reviewed_at + timedelta(minutes=1),
                derivation_relationship="reviewed_context_supporting",
                lifecycle_state="linked",
                provenance={
                    "classification": "reviewed-supporting",
                    "source_id": "github-audit-event-ambiguity-secondary-001",
                    "timestamp": (reviewed_at + timedelta(minutes=1)).isoformat(),
                    "reviewed_by": "analyst-002",
                    "ambiguity_badge": "related-entity",
                },
                content={"summary": {"kind": "supporting"}},
            )
        )
        service.persist_record(
            replace(
                promoted_case,
                evidence_ids=(
                    *promoted_case.evidence_ids,
                    anchor_evidence.evidence_id,
                    secondary_evidence.evidence_id,
                ),
            )
        )

        snapshot = generate_reviewed_shadow_dataset(
            service,
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=decided_at,
        )

        self.assertEqual(snapshot.example_count, 1)
        example = snapshot.examples[0]
        self.assertEqual(example["subject_record_id"], accepted_recommendation.recommendation_id)
        self.assertEqual(
            example["features"]["ambiguity_badges"]["value"],
            ["related-entity", "unresolved"],
        )
        contributors = example["features"]["ambiguity_badges"]["provenance"][
            "feature_source_contributors"
        ]
        self.assertEqual(len(contributors), 2)
        self.assertEqual(
            {
                (entry["feature_source_record_id"], entry["feature_source_badge_value"])
                for entry in contributors
            },
            {
                (anchor_evidence.evidence_id, "unresolved"),
                (secondary_evidence.evidence_id, "related-entity"),
            },
        )

    def test_generator_ignores_unlinked_sibling_evidence(self) -> None:
        _store, service, promoted_case, evidence_id, reviewed_at = (
            self._build_phase19_in_scope_case()
        )
        observation = service.record_case_observation(
            case_id=promoted_case.case_id,
            author_identity="analyst-001",
            observed_at=reviewed_at,
            scope_statement="Extraction must stay within explicit reviewed evidence linkage.",
            supporting_evidence_ids=(evidence_id,),
        )
        lead = service.record_case_lead(
            case_id=promoted_case.case_id,
            observation_id=observation.observation_id,
            triage_owner="analyst-001",
            triage_rationale="Exclude sibling evidence that was never linked on the case.",
        )
        recommendation = service.record_case_recommendation(
            case_id=promoted_case.case_id,
            lead_id=lead.lead_id,
            review_owner="analyst-001",
            intended_outcome="Keep Phase 29 extraction on explicit reviewed evidence only.",
        )
        decided_at = reviewed_at + timedelta(minutes=5)
        service.persist_record(
            replace(recommendation, lifecycle_state="accepted"),
            transitioned_at=decided_at,
        )
        linked_anchor = service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-linked-anchor-001",
                source_record_id="reviewed-source-phase29-linked-anchor-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/linked-anchor",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-linked-anchor-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-001",
                    "ambiguity_badge": "unresolved",
                },
                content={"summary": {"kind": "linked-anchor"}},
            )
        )
        service.persist_record(
            replace(
                promoted_case,
                evidence_ids=(*promoted_case.evidence_ids, linked_anchor.evidence_id),
            )
        )
        service.persist_record(
            EvidenceRecord(
                evidence_id="evidence-phase29-unlinked-sibling-001",
                source_record_id="reviewed-source-phase29-unlinked-sibling-001",
                alert_id=promoted_case.alert_id,
                case_id=promoted_case.case_id,
                source_system="github_audit",
                collector_identity="fixture://reviewed/unlinked-sibling",
                acquired_at=reviewed_at,
                derivation_relationship="reviewed_context_anchor",
                lifecycle_state="linked",
                provenance={
                    "classification": "authoritative-anchor",
                    "source_id": "github-audit-event-unlinked-sibling-001",
                    "timestamp": reviewed_at.isoformat(),
                    "reviewed_by": "analyst-002",
                    "ambiguity_badge": "related-entity",
                },
                content={"summary": {"kind": "unlinked-sibling"}},
            )
        )

        snapshot = generate_reviewed_shadow_dataset(
            service,
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=decided_at,
        )

        self.assertEqual(snapshot.example_count, 1)
        example = snapshot.examples[0]
        self.assertEqual(example["features"]["ambiguity_badges"]["value"], ["unresolved"])
        contributors = example["features"]["ambiguity_badges"]["provenance"][
            "feature_source_contributors"
        ]
        self.assertEqual(len(contributors), 1)
        self.assertEqual(
            contributors[0]["feature_source_record_id"],
            linked_anchor.evidence_id,
        )
