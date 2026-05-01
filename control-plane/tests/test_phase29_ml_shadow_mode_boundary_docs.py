from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase29MlShadowModeBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase29_design_doc_exists_and_defines_shadow_mode_boundary(self) -> None:
        text = self._read("docs/phase-29-reviewed-ml-shadow-mode-boundary.md")

        for term in (
            "AegisOps Phase 29 Reviewed ML Shadow-Mode Boundary",
            "reviewed ML shadow-mode boundary",
            "advisory-only",
            "Observation",
            "Lead",
            "Recommendation draft",
            "must remain outside the authority path",
            "alert admission",
            "approval grant or reject",
            "execution policy",
            "reconciliation truth",
            "case truth promotion",
        ):
            self.assertIn(term, text)

    def test_phase29_design_doc_defines_allowed_features_labels_and_provenance(self) -> None:
        text = self._read("docs/phase-29-reviewed-ml-shadow-mode-boundary.md")

        for term in (
            "Allowed reviewed feature sources",
            "Allowed reviewed labels",
            "ML lineage envelope semantics",
            "MLflow experiment tracking",
            "MLflow model registry",
            "Evidently",
            "reviewed-equivalent drift surface",
            "source-feature health correlation",
            "shadow-data drift",
            "separate ML lineage envelope namespace",
            "`provenance.source_family`",
            "`provenance.source_system`",
            "`provenance.source_id`",
            "Feature provenance contract",
            "Label provenance contract",
            "Model lineage contract",
            "Shadow output lineage contract",
            "Drift visibility contract",
            "`feature_source_record_family`",
            "`feature_source_record_id`",
            "`feature_source_field_path`",
            "`feature_extraction_spec_version`",
            "`feature_source_provenance_classification`",
            "`feature_source_reviewed_by`",
            "`label_record_family`",
            "`label_record_id`",
            "`label_decision_basis`",
            "`label_linked_subject_record_id`",
            "`model_family`",
            "`model_version`",
            "`training_data_snapshot_id`",
            "candidate shadow-model records",
            "`shadow_output_id`",
        ):
            self.assertIn(term, text)

    def test_phase29_design_doc_fails_closed_on_missing_or_stale_signals(self) -> None:
        text = self._read("docs/phase-29-reviewed-ml-shadow-mode-boundary.md")

        for term in (
            "must fail closed",
            "missing labels",
            "source-health degradation",
            "stale features",
            "degraded or stale feature inputs must become visible",
            "unresolved",
            "degraded",
            "must not silently emit",
            "must not infer a label",
            "must not widen scope",
        ):
            self.assertIn(term, text)

    def test_phase29_design_doc_records_module_naming_posture(self) -> None:
        text = self._read("docs/phase-29-reviewed-ml-shadow-mode-boundary.md")

        for term in (
            "Module naming posture",
            "`ml_shadow/dataset.py`",
            "`ml_shadow/scoring.py`",
            "`ml_shadow/mlflow_registry.py`",
            "`ml_shadow/drift_visibility.py`",
            "`phase29_shadow_dataset.py`",
            "`phase29_shadow_scoring.py`",
            "`phase29_mlflow_shadow_model_registry.py`",
            "`phase29_evidently_drift_visibility.py`",
            "compatibility shims only",
            "bounded Phase 29 slice",
            "domain-oriented",
            "production identity",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
