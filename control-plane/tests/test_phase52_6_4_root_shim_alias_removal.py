from __future__ import annotations

import importlib
import pathlib
import sys
import unittest


CONTROL_PLANE_ROOT = pathlib.Path(__file__).resolve().parents[1]
CANONICAL_PACKAGE_ROOT = CONTROL_PLANE_ROOT / "aegisops" / "control_plane"
LEGACY_PACKAGE_ROOT = CONTROL_PLANE_ROOT / "aegisops_control_plane"
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))


REMOVED_ROOT_SHIM_ALIASES = {
    "aegisops_control_plane.action_receipt_validation": "aegisops_control_plane.actions.action_receipt_validation",
    "aegisops_control_plane.action_review_chain": "aegisops_control_plane.actions.review.action_review_chain",
    "aegisops_control_plane.action_review_coordination": "aegisops_control_plane.actions.review.action_review_coordination",
    "aegisops_control_plane.action_review_index": "aegisops_control_plane.actions.review.action_review_index",
    "aegisops_control_plane.action_review_inspection": "aegisops_control_plane.actions.review.action_review_inspection",
    "aegisops_control_plane.action_review_path_health": "aegisops_control_plane.actions.review.action_review_path_health",
    "aegisops_control_plane.action_review_timeline": "aegisops_control_plane.actions.review.action_review_timeline",
    "aegisops_control_plane.action_review_visibility": "aegisops_control_plane.actions.review.action_review_visibility",
    "aegisops_control_plane.assistant_provider": "aegisops_control_plane.assistant.assistant_provider",
    "aegisops_control_plane.detection_lifecycle_helpers": "aegisops_control_plane.ingestion.detection_lifecycle_helpers",
    "aegisops_control_plane.detection_native_context": "aegisops_control_plane.ingestion.detection_native_context",
    "aegisops_control_plane.entrypoint_support": "aegisops_control_plane.api.entrypoint_support",
    "aegisops_control_plane.execution_coordinator": "aegisops_control_plane.actions.execution_coordinator",
    "aegisops_control_plane.execution_coordinator_delegation": "aegisops_control_plane.actions.execution_coordinator_delegation",
    "aegisops_control_plane.execution_coordinator_reconciliation": "aegisops_control_plane.actions.execution_coordinator_reconciliation",
    "aegisops_control_plane.external_evidence_endpoint": "aegisops_control_plane.evidence.external_evidence_endpoint",
    "aegisops_control_plane.external_evidence_facade": "aegisops_control_plane.evidence.external_evidence_facade",
    "aegisops_control_plane.external_evidence_misp": "aegisops_control_plane.evidence.external_evidence_misp",
    "aegisops_control_plane.external_evidence_osquery": "aegisops_control_plane.evidence.external_evidence_osquery",
    "aegisops_control_plane.operations": "aegisops_control_plane.runtime.operations",
    "aegisops_control_plane.service_snapshots": "aegisops_control_plane.runtime.service_snapshots",
}


class Phase5264RootShimAliasRemovalTests(unittest.TestCase):
    def test_removed_root_shims_are_registry_aliases(self) -> None:
        registry = importlib.import_module(
            "aegisops_control_plane.core.legacy_import_aliases"
        )

        for legacy_module, target_module in REMOVED_ROOT_SHIM_ALIASES.items():
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
                self.assertIs(
                    importlib.import_module(legacy_module),
                    importlib.import_module(target_module),
                )

    def test_public_root_owners_moved_to_canonical_physical_package(self) -> None:
        retained = {
            "models.py",
            "service.py",
            "config.py",
            "record_validation.py",
            "assistant_context.py",
            "action_lifecycle_write_coordinator.py",
            "action_policy.py",
            "action_reconciliation_orchestration.py",
            "action_review_projection.py",
            "action_review_write_surface.py",
            "ai_trace_lifecycle.py",
            "assistant_advisory.py",
            "case_workflow.py",
            "cli.py",
            "detection_lifecycle.py",
            "evidence_linkage.py",
            "execution_coordinator_action_requests.py",
            "external_evidence_boundary.py",
            "http_protected_surface.py",
            "http_runtime_surface.py",
            "http_surface.py",
            "live_assistant_workflow.py",
            "pilot_reporting_export.py",
            "readiness_contracts.py",
            "readiness_operability.py",
            "restore_readiness.py",
            "restore_readiness_backup_restore.py",
            "restore_readiness_projection.py",
            "runtime_boundary.py",
            "runtime_restore_readiness_diagnostics.py",
        }

        missing = sorted(
            name for name in retained if not (CANONICAL_PACKAGE_ROOT / name).is_file()
        )
        self.assertEqual(missing, [])
        legacy_files = sorted(
            name for name in retained if (LEGACY_PACKAGE_ROOT / name).exists()
        )
        self.assertEqual(legacy_files, [])


if __name__ == "__main__":
    unittest.main()
