from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase47ResponsibilityDecompositionDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase47_boundary_doc_defines_decomposition_contract(self) -> None:
        text = self._read(
            "docs/phase-47-control-plane-responsibility-decomposition-boundary.md"
        )

        for term in (
            "AegisOps Phase 47 Control-Plane Responsibility Decomposition Boundary",
            "In Scope",
            "Out of Scope",
            "Fail-Closed Conditions",
            "action lifecycle write routing",
            "readiness runtime status coordination",
            "external evidence coordination",
            "assistant advisory coordination",
            "maintainability hotspot verifier",
            "AegisOpsControlPlaneService",
            "Phase 49.0",
            "AegisOps control-plane records remain authoritative",
            "`service.py` remains a reviewed maintainability hotspot",
        ):
            self.assertIn(term, text)

    def test_phase47_validation_doc_records_verifier_references_and_no_readiness_claim(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-47-control-plane-responsibility-decomposition-validation.md"
        )

        for term in (
            "Phase 47 Control-Plane Responsibility Decomposition Validation",
            "Validation status: PASS",
            "docs/phase-47-control-plane-responsibility-decomposition-boundary.md",
            "docs/control-plane-service-internal-boundaries.md",
            "docs/maintainability-decomposition-thresholds.md",
            "docs/maintainability-hotspot-baseline.txt",
            "control-plane/aegisops_control_plane/action_lifecycle_write_coordinator.py",
            "control-plane/aegisops_control_plane/readiness_contracts.py",
            "control-plane/aegisops_control_plane/external_evidence_boundary.py",
            "control-plane/aegisops_control_plane/assistant_advisory.py",
            "bash scripts/verify-maintainability-hotspots.sh",
            "python3 -m unittest control-plane/tests/test_phase47_responsibility_decomposition_docs.py",
            "node <codex-supervisor-root>/dist/index.js issue-lint 888 --config <supervisor-config-path>",
            "No runtime behavior, authority posture, or commercial readiness claim is introduced by this validation document.",
            "Phase 49.0 owns the remaining service.py responsibility concentration follow-up.",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
