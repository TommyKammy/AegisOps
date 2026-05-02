from __future__ import annotations

import importlib
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
LEGACY_PACKAGE_ROOT = CONTROL_PLANE_ROOT / "aegisops_control_plane"
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


PHASE29_LEGACY_IMPORTS = {
    "aegisops_control_plane.phase29_shadow_dataset": (
        "aegisops_control_plane.ml_shadow.dataset",
        "Phase29ShadowDatasetSnapshot",
    ),
    "aegisops_control_plane.phase29_evidently_drift_visibility": (
        "aegisops_control_plane.ml_shadow.drift_visibility",
        "Phase29EvidentlyDriftVisibilityReport",
    ),
    "aegisops_control_plane.phase29_mlflow_shadow_model_registry": (
        "aegisops_control_plane.ml_shadow.mlflow_registry",
        "Phase29MlflowShadowModelTrackingResult",
    ),
}


class Phase5265Phase29RootFilenameRetirementTests(unittest.TestCase):
    def test_phase29_root_files_are_retired_to_registered_aliases(self) -> None:
        registry = importlib.import_module(
            "aegisops_control_plane.core.legacy_import_aliases"
        )

        expected_aliases = {
            **{
                legacy_module: target_module
                for legacy_module, (target_module, _attribute) in PHASE29_LEGACY_IMPORTS.items()
            },
            "aegisops_control_plane.phase29_shadow_scoring": (
                "aegisops_control_plane.ml_shadow.legacy_scoring_adapter"
            ),
        }

        for legacy_module, target_module in expected_aliases.items():
            with self.subTest(legacy_module=legacy_module):
                legacy_file = (
                    LEGACY_PACKAGE_ROOT / f"{legacy_module.rsplit('.', 1)[-1]}.py"
                )
                self.assertFalse(legacy_file.exists(), legacy_file)
                self.assertIn(legacy_module, registry.LEGACY_IMPORT_ALIASES)
                self.assertEqual(
                    registry.LEGACY_IMPORT_ALIASES[legacy_module].target_module,
                    target_module,
                )
                self.assertEqual(
                    registry.LEGACY_IMPORT_ALIASES[legacy_module].target_family,
                    "ml_shadow",
                )
                self.assertNotIn(legacy_module, registry.RETAINED_COMPATIBILITY_BLOCKERS)

    def test_phase29_legacy_imports_preserve_required_compatibility_surface(self) -> None:
        for legacy_module, (target_module, attribute) in PHASE29_LEGACY_IMPORTS.items():
            with self.subTest(legacy_module=legacy_module):
                legacy = importlib.import_module(legacy_module)
                target = importlib.import_module(target_module)
                self.assertIs(legacy, target)
                self.assertIs(getattr(legacy, attribute), getattr(target, attribute))

        legacy_scoring = importlib.import_module(
            "aegisops_control_plane.phase29_shadow_scoring"
        )
        canonical_scoring = importlib.import_module("aegisops_control_plane.ml_shadow.scoring")

        self.assertIsNot(legacy_scoring, canonical_scoring)
        self.assertIs(
            legacy_scoring.Phase29ShadowScoringError,
            canonical_scoring.Phase29ShadowScoringError,
        )
        self.assertTrue(
            hasattr(
                legacy_scoring.Phase29ShadowScoreResult,
                "feature_frequencies_at_inference_time",
            )
        )
        self.assertTrue(
            hasattr(
                legacy_scoring.Phase29OfflineShadowScoringSnapshot,
                "scored_examples",
            )
        )


if __name__ == "__main__":
    unittest.main()
