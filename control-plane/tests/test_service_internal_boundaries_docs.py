from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class ServiceInternalBoundariesDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "control-plane-service-internal-boundaries.md"

    def test_service_internal_boundaries_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(
            design_doc.exists(),
            f"expected service boundary design doc at {design_doc}",
        )

    def test_service_internal_boundaries_design_doc_covers_target_decomposition(self) -> None:
        design_doc = self._design_doc()
        self.assertTrue(
            design_doc.exists(),
            f"expected service boundary design doc at {design_doc}",
        )
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "AegisOps Control-Plane Service Internal Boundaries",
            "Current Responsibility Clusters",
            "Target Internal Collaborators",
            "Facade Responsibilities",
            "Shared Helper Placement Rules",
            "Safest Extraction Order",
            "assistant/advisory assembly",
            "action/delegation/reconciliation",
            "runtime/readiness/restore",
            "Phase 19 slice policy boundaries",
            "AegisOpsControlPlaneService remains the public facade",
            "RuntimeBoundaryService",
            "DetectionIntakeService",
            "AnalystWorkflowService",
            "AssistantAdvisoryService",
            "ActionGovernanceService",
            "RestoreReadinessService",
            "restore_readiness_projection.py",
            "restore_readiness_backup_restore.py",
            "readiness_contracts.py",
            "Phase19Policy",
            "module-level",
            "reusable policy",
            "dependency direction",
            "Phase 19-21 reviewed behavior",
            "fail closed",
            "Non-Goals",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
