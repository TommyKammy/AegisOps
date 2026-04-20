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
from aegisops_control_plane.phase29_mlflow_shadow_model_registry import (
    Phase29MlflowShadowModelRegistryError,
    track_shadow_model_with_mlflow,
)
from aegisops_control_plane.phase29_shadow_dataset import (
    Phase29ShadowDatasetSnapshot,
    generate_reviewed_shadow_dataset,
)
from support.service_persistence import ServicePersistenceTestBase


class _FakeRunInfo:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id


class _FakeRun:
    def __init__(self, run_id: str) -> None:
        self.info = _FakeRunInfo(run_id)


class _FakeExperiment:
    def __init__(self, experiment_id: str, name: str) -> None:
        self.experiment_id = experiment_id
        self.name = name


class _FakeRegisteredModel:
    def __init__(self, name: str) -> None:
        self.name = name


class _FakeModelVersion:
    def __init__(self, name: str, version: str, source: str, run_id: str) -> None:
        self.name = name
        self.version = version
        self.source = source
        self.run_id = run_id


class FakeMlflowClient:
    def __init__(self) -> None:
        self._experiments_by_name: dict[str, _FakeExperiment] = {}
        self.run_params: dict[str, dict[str, str]] = {}
        self.run_tags: dict[str, dict[str, str]] = {}
        self.run_metrics: dict[str, dict[str, float]] = {}
        self.registered_models: dict[str, dict[str, object]] = {}
        self.model_versions: dict[tuple[str, str], dict[str, object]] = {}

    def get_experiment_by_name(self, name: str) -> _FakeExperiment | None:
        return self._experiments_by_name.get(name)

    def create_experiment(
        self,
        name: str,
        tags: dict[str, str] | None = None,
    ) -> str:
        experiment_id = f"exp-{len(self._experiments_by_name) + 1}"
        self._experiments_by_name[name] = _FakeExperiment(experiment_id, name)
        return experiment_id

    def create_run(
        self,
        experiment_id: str,
        tags: dict[str, str] | None = None,
        run_name: str | None = None,
    ) -> _FakeRun:
        run_id = f"run-{len(self.run_tags) + 1}"
        tag_bucket = dict(tags or {})
        if run_name is not None:
            tag_bucket["mlflow.runName"] = run_name
        self.run_tags[run_id] = tag_bucket
        self.run_params[run_id] = {}
        self.run_metrics[run_id] = {}
        return _FakeRun(run_id)

    def log_param(self, run_id: str, key: str, value: object) -> None:
        self.run_params[run_id][key] = str(value)

    def set_tag(self, run_id: str, key: str, value: object) -> None:
        self.run_tags[run_id][key] = str(value)

    def log_metric(
        self,
        run_id: str,
        key: str,
        value: float,
        timestamp: int | None = None,
        step: int = 0,
    ) -> None:
        del timestamp, step
        self.run_metrics[run_id][key] = float(value)

    def get_registered_model(self, name: str) -> _FakeRegisteredModel | None:
        payload = self.registered_models.get(name)
        if payload is None:
            return None
        return _FakeRegisteredModel(name)

    def create_registered_model(
        self,
        name: str,
        tags: dict[str, str] | None = None,
        description: str | None = None,
    ) -> _FakeRegisteredModel:
        self.registered_models[name] = {
            "tags": dict(tags or {}),
            "description": description,
        }
        return _FakeRegisteredModel(name)

    def create_model_version(
        self,
        name: str,
        source: str,
        run_id: str | None = None,
        tags: dict[str, str] | None = None,
        description: str | None = None,
    ) -> _FakeModelVersion:
        matching_versions = [
            version
            for registered_name, version in self.model_versions
            if registered_name == name
        ]
        version = str(len(matching_versions) + 1)
        self.model_versions[(name, version)] = {
            "source": source,
            "run_id": run_id,
            "tags": dict(tags or {}),
            "description": description,
        }
        return _FakeModelVersion(name=name, version=version, source=source, run_id=run_id or "")


class Phase29MlflowShadowModelRegistryValidationTests(ServicePersistenceTestBase):
    def test_tracker_records_mlflow_shadow_run_and_registry_lineage(self) -> None:
        store, service, dataset_snapshot, decided_at = self._build_shadow_dataset_snapshot()
        initial_record_counts = {
            record_type.__name__: len(store.list(record_type))
            for record_type in (EvidenceRecord, ReconciliationRecord)
        }
        client = FakeMlflowClient()

        result = track_shadow_model_with_mlflow(
            client=client,
            dataset_snapshot=dataset_snapshot,
            experiment_name="phase29-shadow-model-training",
            run_name="xgboost-github-audit-candidate",
            registered_model_name="shadow.models.github_audit_xgboost",
            model_source_uri="models:/shadow.models.github_audit_xgboost/artifacts/model.pkl",
            model_family="xgboost",
            model_version="candidate-2026-04-20",
            training_spec_version="phase29-shadow-training-v1",
            feature_schema_version="phase29-shadow-features-v1",
            label_schema_version="phase29-shadow-labels-v1",
            lineage_review_note_id="note-phase29-shadow-001",
            evaluation_metrics={
                "precision_at_5": 0.8,
                "recall_at_5": 0.6,
            },
            evaluation_metadata={
                "evaluation_window": "2026-04-01/2026-04-20",
                "candidate_ranker": "top_k_review_queue",
            },
            run_timestamp=decided_at,
        )

        self.assertEqual(result.dataset_snapshot_id, dataset_snapshot.snapshot_id)
        self.assertEqual(result.model_family, "xgboost")
        self.assertEqual(result.model_version, "candidate-2026-04-20")
        self.assertEqual(result.registry_posture, "shadow-only")
        self.assertEqual(result.registered_model_name, "shadow.models.github_audit_xgboost")
        self.assertEqual(result.registered_model_version, "1")

        self.assertIn(result.run_id, client.run_params)
        self.assertEqual(
            client.run_params[result.run_id]["training_data_snapshot_id"],
            dataset_snapshot.snapshot_id,
        )
        self.assertEqual(
            client.run_params[result.run_id]["feature_schema_version"],
            "phase29-shadow-features-v1",
        )
        self.assertEqual(
            client.run_params[result.run_id]["label_schema_version"],
            "phase29-shadow-labels-v1",
        )
        self.assertEqual(
            client.run_params[result.run_id]["evaluation_window"],
            "2026-04-01/2026-04-20",
        )
        self.assertEqual(
            client.run_tags[result.run_id]["aegisops.registry_posture"],
            "shadow-only",
        )
        self.assertEqual(
            client.run_tags[result.run_id]["aegisops.authority_path"],
            "outside-control-plane",
        )
        self.assertEqual(
            client.model_versions[
                (result.registered_model_name, result.registered_model_version)
            ]["tags"]["aegisops.training_data_snapshot_id"],
            dataset_snapshot.snapshot_id,
        )
        self.assertEqual(
            client.model_versions[
                (result.registered_model_name, result.registered_model_version)
            ]["tags"]["aegisops.candidate_ranker"],
            "top_k_review_queue",
        )
        self.assertEqual(client.run_metrics[result.run_id]["precision_at_5"], 0.8)
        self.assertEqual(client.run_metrics[result.run_id]["recall_at_5"], 0.6)

        final_record_counts = {
            record_type.__name__: len(store.list(record_type))
            for record_type in (EvidenceRecord, ReconciliationRecord)
        }
        self.assertEqual(final_record_counts, initial_record_counts)

    def test_tracker_fails_closed_when_feature_provenance_is_missing(self) -> None:
        snapshot = Phase29ShadowDatasetSnapshot(
            snapshot_id="snapshot-missing-feature-provenance",
            extraction_spec_version="phase29-shadow-dataset-v1",
            snapshot_timestamp=datetime(2026, 4, 20, 0, 0, tzinfo=timezone.utc).isoformat(),
            example_count=1,
            examples=(
                {
                    "subject_record_family": "recommendation",
                    "subject_record_id": "recommendation-001",
                    "linked_case_id": "case-001",
                    "linked_alert_id": "alert-001",
                    "features": {
                        "source_family": {
                            "value": "github_audit",
                            "provenance": {
                                "feature_source_record_family": "Alert",
                                "feature_source_field_path": "reviewed_context.source.source_family",
                                "feature_extraction_spec_version": "phase29-shadow-dataset-v1",
                                "feature_snapshot_timestamp": datetime(
                                    2026, 4, 20, 0, 0, tzinfo=timezone.utc
                                ).isoformat(),
                                "feature_reviewed_linkage": "subject-alert-link",
                                "feature_source_provenance_classification": None,
                                "feature_source_reviewed_by": "analyst-001",
                            },
                        }
                    },
                    "label": {
                        "value": "accepted",
                        "provenance": {
                            "label_record_family": "Recommendation",
                            "label_record_id": "recommendation-001",
                            "label_field_path": "lifecycle_state",
                            "label_decision_basis": "reviewed recommendation lifecycle_state",
                            "label_decided_at": datetime(
                                2026, 4, 20, 0, 5, tzinfo=timezone.utc
                            ).isoformat(),
                            "label_reviewed_by": "analyst-001",
                            "label_linked_subject_record_id": "recommendation-001",
                        },
                    },
                },
            ),
        )

        with self.assertRaisesRegex(
            Phase29MlflowShadowModelRegistryError,
            "missing required feature provenance",
        ):
            track_shadow_model_with_mlflow(
                client=FakeMlflowClient(),
                dataset_snapshot=snapshot,
                experiment_name="phase29-shadow-model-training",
                run_name="broken-run",
                registered_model_name="shadow.models.broken",
                model_source_uri="models:/shadow.models.broken/model.pkl",
                model_family="xgboost",
                model_version="broken-candidate",
                training_spec_version="phase29-shadow-training-v1",
                feature_schema_version="phase29-shadow-features-v1",
                label_schema_version="phase29-shadow-labels-v1",
                lineage_review_note_id="note-phase29-shadow-001",
                evaluation_metrics={"precision_at_5": 0.8},
                evaluation_metadata={"evaluation_window": "2026-04-01/2026-04-20"},
                run_timestamp=datetime(2026, 4, 20, 0, 10, tzinfo=timezone.utc),
            )

    def test_tracker_requires_lineage_review_note_for_registry_entries(self) -> None:
        _store, _service, dataset_snapshot, decided_at = self._build_shadow_dataset_snapshot()

        with self.assertRaisesRegex(
            Phase29MlflowShadowModelRegistryError,
            "lineage_review_note_id must be a non-empty string",
        ):
            track_shadow_model_with_mlflow(
                client=FakeMlflowClient(),
                dataset_snapshot=dataset_snapshot,
                experiment_name="phase29-shadow-model-training",
                run_name="missing-lineage-review-note",
                registered_model_name="shadow.models.github_audit_xgboost",
                model_source_uri="models:/shadow.models.github_audit_xgboost/model.pkl",
                model_family="xgboost",
                model_version="candidate-2026-04-20",
                training_spec_version="phase29-shadow-training-v1",
                feature_schema_version="phase29-shadow-features-v1",
                label_schema_version="phase29-shadow-labels-v1",
                lineage_review_note_id="   ",
                evaluation_metrics={"precision_at_5": 0.8},
                evaluation_metadata={"evaluation_window": "2026-04-01/2026-04-20"},
                run_timestamp=decided_at,
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
