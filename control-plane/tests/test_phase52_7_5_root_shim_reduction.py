from __future__ import annotations

import importlib
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
CANONICAL_ROOT = CONTROL_PLANE_ROOT / "aegisops" / "control_plane"
LEGACY_ROOT = CONTROL_PLANE_ROOT / "aegisops_control_plane"
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


REMOVED_CANONICAL_ROOT_SHIM_ALIASES = {
    "aegisops.control_plane.action_lifecycle_write_coordinator": (
        "aegisops.control_plane.actions.action_lifecycle_write_coordinator"
    ),
    "aegisops.control_plane.action_policy": (
        "aegisops.control_plane.actions.action_policy"
    ),
    "aegisops.control_plane.action_reconciliation_orchestration": (
        "aegisops.control_plane.actions.action_reconciliation_orchestration"
    ),
    "aegisops.control_plane.action_review_projection": (
        "aegisops.control_plane.actions.review.action_review_projection"
    ),
    "aegisops.control_plane.action_review_write_surface": (
        "aegisops.control_plane.actions.review.action_review_write_surface"
    ),
    "aegisops.control_plane.ai_trace_lifecycle": (
        "aegisops.control_plane.assistant.ai_trace_lifecycle"
    ),
    "aegisops.control_plane.assistant_advisory": (
        "aegisops.control_plane.assistant.assistant_advisory"
    ),
    "aegisops.control_plane.assistant_context": (
        "aegisops.control_plane.assistant.assistant_context"
    ),
    "aegisops.control_plane.case_workflow": (
        "aegisops.control_plane.ingestion.case_workflow"
    ),
    "aegisops.control_plane.detection_lifecycle": (
        "aegisops.control_plane.ingestion.detection_lifecycle"
    ),
    "aegisops.control_plane.evidence_linkage": (
        "aegisops.control_plane.ingestion.evidence_linkage"
    ),
    "aegisops.control_plane.execution_coordinator_action_requests": (
        "aegisops.control_plane.actions.execution_coordinator_action_requests"
    ),
    "aegisops.control_plane.external_evidence_boundary": (
        "aegisops.control_plane.evidence.external_evidence_boundary"
    ),
    "aegisops.control_plane.http_protected_surface": (
        "aegisops.control_plane.api.http_protected_surface"
    ),
    "aegisops.control_plane.http_runtime_surface": (
        "aegisops.control_plane.api.http_runtime_surface"
    ),
    "aegisops.control_plane.http_surface": "aegisops.control_plane.api.http_surface",
    "aegisops.control_plane.live_assistant_workflow": (
        "aegisops.control_plane.assistant.live_assistant_workflow"
    ),
    "aegisops.control_plane.pilot_reporting_export": (
        "aegisops.control_plane.reporting.pilot_reporting_export"
    ),
    "aegisops.control_plane.readiness_contracts": (
        "aegisops.control_plane.runtime.readiness_contracts"
    ),
    "aegisops.control_plane.readiness_operability": (
        "aegisops.control_plane.runtime.readiness_operability"
    ),
    "aegisops.control_plane.restore_readiness": (
        "aegisops.control_plane.runtime.restore_readiness"
    ),
    "aegisops.control_plane.restore_readiness_backup_restore": (
        "aegisops.control_plane.runtime.restore_readiness_backup_restore"
    ),
    "aegisops.control_plane.restore_readiness_projection": (
        "aegisops.control_plane.runtime.restore_readiness_projection"
    ),
    "aegisops.control_plane.runtime_boundary": (
        "aegisops.control_plane.runtime.runtime_boundary"
    ),
    "aegisops.control_plane.runtime_restore_readiness_diagnostics": (
        "aegisops.control_plane.runtime.runtime_restore_readiness_diagnostics"
    ),
}

RETAINED_CANONICAL_ROOT_FILES = {
    "__init__.py",
    "config.py",
    "cli.py",
    "models.py",
    "operator_inspection.py",
    "persistence_lifecycle.py",
    "publishable_paths.py",
    "record_validation.py",
    "reviewed_slice_policy.py",
    "service.py",
    "service_composition.py",
    "structured_events.py",
}


class Phase5275RootShimReductionTests(unittest.TestCase):
    def test_simple_canonical_root_shims_are_removed(self) -> None:
        removed = {
            module.rsplit(".", 1)[-1] + ".py"
            for module in REMOVED_CANONICAL_ROOT_SHIM_ALIASES
        }
        self.assertEqual(
            sorted(path.name for path in CANONICAL_ROOT.glob("*.py")),
            sorted(RETAINED_CANONICAL_ROOT_FILES),
        )
        self.assertEqual(
            sorted(name for name in removed if (CANONICAL_ROOT / name).exists()),
            [],
        )
        self.assertEqual(
            sorted(path.name for path in LEGACY_ROOT.glob("*.py")),
            ["__init__.py"],
        )

    def test_canonical_flat_imports_alias_to_domain_module_identity(self) -> None:
        for canonical_flat, target_module in REMOVED_CANONICAL_ROOT_SHIM_ALIASES.items():
            with self.subTest(canonical_flat=canonical_flat):
                self.assertIs(
                    importlib.import_module(canonical_flat),
                    importlib.import_module(target_module),
                )

    def test_legacy_flat_imports_alias_to_domain_module_identity(self) -> None:
        for canonical_flat, target_module in REMOVED_CANONICAL_ROOT_SHIM_ALIASES.items():
            legacy_flat = canonical_flat.replace(
                "aegisops.control_plane", "aegisops_control_plane", 1
            )
            legacy_target = target_module.replace(
                "aegisops.control_plane", "aegisops_control_plane", 1
            )
            with self.subTest(legacy_flat=legacy_flat):
                self.assertIs(
                    importlib.import_module(legacy_flat),
                    importlib.import_module(legacy_target),
                )


if __name__ == "__main__":
    unittest.main()
