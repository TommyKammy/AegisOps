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
    "aegisops_control_plane.action_lifecycle_write_coordinator": "aegisops_control_plane.actions.action_lifecycle_write_coordinator",
    "aegisops_control_plane.action_policy": "aegisops_control_plane.actions.action_policy",
    "aegisops_control_plane.action_receipt_validation": "aegisops_control_plane.actions.action_receipt_validation",
    "aegisops_control_plane.action_reconciliation_orchestration": "aegisops_control_plane.actions.action_reconciliation_orchestration",
    "aegisops_control_plane.action_review_chain": "aegisops_control_plane.actions.review.action_review_chain",
    "aegisops_control_plane.action_review_coordination": "aegisops_control_plane.actions.review.action_review_coordination",
    "aegisops_control_plane.action_review_index": "aegisops_control_plane.actions.review.action_review_index",
    "aegisops_control_plane.action_review_inspection": "aegisops_control_plane.actions.review.action_review_inspection",
    "aegisops_control_plane.action_review_path_health": "aegisops_control_plane.actions.review.action_review_path_health",
    "aegisops_control_plane.action_review_projection": "aegisops_control_plane.actions.review.action_review_projection",
    "aegisops_control_plane.action_review_timeline": "aegisops_control_plane.actions.review.action_review_timeline",
    "aegisops_control_plane.action_review_visibility": "aegisops_control_plane.actions.review.action_review_visibility",
    "aegisops_control_plane.action_review_write_surface": "aegisops_control_plane.actions.review.action_review_write_surface",
    "aegisops_control_plane.ai_trace_lifecycle": "aegisops_control_plane.assistant.ai_trace_lifecycle",
    "aegisops_control_plane.assistant_advisory": "aegisops_control_plane.assistant.assistant_advisory",
    "aegisops_control_plane.assistant_context": "aegisops_control_plane.assistant.assistant_context",
    "aegisops_control_plane.assistant_provider": "aegisops_control_plane.assistant.assistant_provider",
    "aegisops_control_plane.case_workflow": "aegisops_control_plane.ingestion.case_workflow",
    "aegisops_control_plane.detection_lifecycle": "aegisops_control_plane.ingestion.detection_lifecycle",
    "aegisops_control_plane.detection_lifecycle_helpers": "aegisops_control_plane.ingestion.detection_lifecycle_helpers",
    "aegisops_control_plane.detection_native_context": "aegisops_control_plane.ingestion.detection_native_context",
    "aegisops_control_plane.evidence_linkage": "aegisops_control_plane.ingestion.evidence_linkage",
    "aegisops_control_plane.entrypoint_support": "aegisops_control_plane.api.entrypoint_support",
    "aegisops_control_plane.execution_coordinator": "aegisops_control_plane.actions.execution_coordinator",
    "aegisops_control_plane.execution_coordinator_action_requests": "aegisops_control_plane.actions.execution_coordinator_action_requests",
    "aegisops_control_plane.execution_coordinator_delegation": "aegisops_control_plane.actions.execution_coordinator_delegation",
    "aegisops_control_plane.execution_coordinator_reconciliation": "aegisops_control_plane.actions.execution_coordinator_reconciliation",
    "aegisops_control_plane.external_evidence_boundary": "aegisops_control_plane.evidence.external_evidence_boundary",
    "aegisops_control_plane.external_evidence_endpoint": "aegisops_control_plane.evidence.external_evidence_endpoint",
    "aegisops_control_plane.external_evidence_facade": "aegisops_control_plane.evidence.external_evidence_facade",
    "aegisops_control_plane.external_evidence_misp": "aegisops_control_plane.evidence.external_evidence_misp",
    "aegisops_control_plane.external_evidence_osquery": "aegisops_control_plane.evidence.external_evidence_osquery",
    "aegisops_control_plane.http_protected_surface": "aegisops_control_plane.api.http_protected_surface",
    "aegisops_control_plane.http_runtime_surface": "aegisops_control_plane.api.http_runtime_surface",
    "aegisops_control_plane.http_surface": "aegisops_control_plane.api.http_surface",
    "aegisops_control_plane.live_assistant_workflow": "aegisops_control_plane.assistant.live_assistant_workflow",
    "aegisops_control_plane.operations": "aegisops_control_plane.runtime.operations",
    "aegisops_control_plane.pilot_reporting_export": "aegisops_control_plane.reporting.pilot_reporting_export",
    "aegisops_control_plane.readiness_contracts": "aegisops_control_plane.runtime.readiness_contracts",
    "aegisops_control_plane.readiness_operability": "aegisops_control_plane.runtime.readiness_operability",
    "aegisops_control_plane.restore_readiness": "aegisops_control_plane.runtime.restore_readiness",
    "aegisops_control_plane.restore_readiness_backup_restore": "aegisops_control_plane.runtime.restore_readiness_backup_restore",
    "aegisops_control_plane.restore_readiness_projection": "aegisops_control_plane.runtime.restore_readiness_projection",
    "aegisops_control_plane.runtime_boundary": "aegisops_control_plane.runtime.runtime_boundary",
    "aegisops_control_plane.runtime_restore_readiness_diagnostics": "aegisops_control_plane.runtime.runtime_restore_readiness_diagnostics",
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

    def test_public_root_owners_remain_in_canonical_physical_package(self) -> None:
        retained = {
            "models.py",
            "service.py",
            "config.py",
            "cli.py",
            "record_validation.py",
            "operator_inspection.py",
            "persistence_lifecycle.py",
            "publishable_paths.py",
            "reviewed_slice_policy.py",
            "service_composition.py",
            "structured_events.py",
        }

        missing = sorted(
            name for name in retained if not (CANONICAL_PACKAGE_ROOT / name).is_file()
        )
        self.assertEqual(missing, [])
        removed = {
            module.rsplit(".", 1)[-1] + ".py"
            for module in REMOVED_ROOT_SHIM_ALIASES
        }
        canonical_shim_files = sorted(
            name for name in removed if (CANONICAL_PACKAGE_ROOT / name).exists()
        )
        self.assertEqual(canonical_shim_files, [])
        legacy_shim_files = sorted(
            name for name in retained | removed if (LEGACY_PACKAGE_ROOT / name).exists()
        )
        self.assertEqual(legacy_shim_files, [])


if __name__ == "__main__":
    unittest.main()
