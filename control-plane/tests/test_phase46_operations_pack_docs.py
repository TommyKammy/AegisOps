from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase46OperationsPackDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected file at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase46_boundary_doc_defines_operations_pack_contract(self) -> None:
        text = self._read(
            "docs/phase-46-approval-execution-reconciliation-operations-pack-boundary.md"
        )

        for term in (
            "AegisOps Phase 46 Approval, Execution, and Reconciliation Operations Pack Boundary",
            "In Scope",
            "Out of Scope",
            "Fail-Closed Conditions",
            "approval role matrix",
            "fallback and escalation rehearsal",
            "reconciliation mismatch closeout",
            "Zammad non-authority rehearsal",
            "focused Zammad verifier self-test fixtures",
            "Zammad close does not close AegisOps case",
            "AegisOps control-plane records remain authoritative",
            "Approval, execution, and reconciliation remain separate first-class records",
            "Zammad and downstream receipts remain non-authoritative",
        ):
            self.assertIn(term, text)

    def test_phase46_validation_doc_records_verifier_references_and_no_behavior_change(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-46-approval-execution-reconciliation-operations-pack-validation.md"
        )

        for term in (
            "Phase 46 Approval, Execution, and Reconciliation Operations Pack Validation",
            "Validation status: PASS",
            "docs/phase-46-approval-execution-reconciliation-operations-pack-boundary.md",
            "docs/runbook.md",
            "docs/secops-domain-model.md",
            "docs/deployment/operator-training-handoff-packet.md",
            "docs/deployment/support-playbook-break-glass-rehearsal.md",
            "docs/operations-zammad-live-pilot-boundary.md",
            "control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json",
            "control-plane/tests/fixtures/zammad/non-authority-coordination-rehearsal.json",
            "scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh",
            "bash scripts/verify-zammad-live-pilot-boundary.sh",
            "bash scripts/test-verify-zammad-live-pilot-boundary.sh",
            "python3 -m unittest control-plane/tests/test_phase46_operations_pack_docs.py",
            "node <codex-supervisor-root>/dist/index.js issue-lint 890 --config <supervisor-config-path>",
            "No approval behavior, execution behavior, reconciliation behavior, Zammad behavior, or runtime behavior changes are introduced by this validation document.",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
