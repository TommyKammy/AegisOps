from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase45DailySocQueueDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase45_boundary_doc_defines_daily_queue_contract(self) -> None:
        text = self._read(
            "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md"
        )

        for term in (
            "AegisOps Phase 45 Daily SOC Queue and Operator UX Hardening Boundary",
            "In Scope",
            "Out of Scope",
            "Fail-Closed Conditions",
            "queue priority projection",
            "mismatch and degraded lanes",
            "alert, case, provenance, and action-review drilldowns",
            "operator training alignment",
            "structured stale receipt status",
            "AegisOps control-plane records remain authoritative",
            "daily SOC queue projection and drilldown UI do not become workflow truth",
            "operator-readable summaries are explanatory details, not authority",
        ):
            self.assertIn(term, text)

    def test_phase45_validation_doc_records_verifier_references_and_no_behavior_change(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-validation.md"
        )

        for term in (
            "Phase 45 Daily SOC Queue and Operator UX Hardening Validation",
            "Validation status: PASS",
            "docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md",
            "control-plane/aegisops_control_plane/operator_inspection.py",
            "control-plane/tests/test_operator_inspection_boundary.py",
            "control-plane/tests/test_service_persistence_ingest_case_lifecycle.py",
            "apps/operator-ui/src/app/OperatorRoutes.casework.testSuite.tsx",
            "apps/operator-ui/src/app/OperatorRoutes.actionReview.testSuite.tsx",
            "docs/deployment/operator-training-handoff-packet.md",
            "scripts/verify-operator-training-handoff-packet.sh",
            "bash scripts/verify-pilot-readiness-checklist.sh",
            "python3 -m unittest control-plane.tests.test_phase45_daily_soc_queue_docs",
            "node <codex-supervisor-root>/dist/index.js issue-lint 891 --config <supervisor-config-path>",
            "No operator behavior, backend lifecycle behavior, or authority posture changes are introduced by this validation document.",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
