from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase44PilotIngressOperatorSurfaceDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase44_boundary_doc_defines_closed_pilot_ingress_contract(self) -> None:
        text = self._read(
            "docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md"
        )

        for term in (
            "AegisOps Phase 44 Pilot Ingress and Operator Surface Closure Boundary",
            "In Scope",
            "Out of Scope",
            "Fail-Closed Conditions",
            "first-boot proxy operator surface",
            "protected identity header normalization",
            "backend and operator-ui role canonicalization",
            "runtime smoke ingress evidence",
            "operator-ui CI gate",
            "AegisOps backend records remain authoritative",
            "operator UI and proxy evidence do not become workflow truth",
            "direct backend exposure",
            "Browser state, operator UI state, external tickets, assistant output, and downstream receipts remain subordinate context",
        ):
            self.assertIn(term, text)

    def test_phase44_validation_doc_records_verifier_references_and_no_behavior_change(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-44-pilot-ingress-and-operator-surface-closure-validation.md"
        )

        for term in (
            "Phase 44 Pilot Ingress and Operator Surface Closure Validation",
            "Validation status: PASS",
            "docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md",
            "control-plane/deployment/first-boot/docker-compose.yml",
            "proxy/nginx/conf.d-first-boot/control-plane.conf",
            "control-plane/tests/test_phase17_first_boot_runtime_artifacts.py",
            "control-plane/tests/test_phase21_runtime_auth_validation.py",
            "apps/operator-ui/src/auth/session.test.ts",
            "scripts/run-phase-37-runtime-smoke-gate.sh",
            "scripts/test-verify-ci-operator-ui-workflow-coverage.sh",
            "bash scripts/verify-architecture-runbook-validation.sh",
            "python3 -m unittest control-plane.tests.test_phase44_pilot_ingress_operator_surface_docs",
            "node <codex-supervisor-root>/dist/index.js issue-lint 889 --config <supervisor-config-path>",
            "No runtime behavior, operator UI behavior, or authority posture changes are introduced by this validation document.",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
