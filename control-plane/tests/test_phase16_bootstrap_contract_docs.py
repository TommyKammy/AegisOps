from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase16BootstrapContractDocsTests(unittest.TestCase):
    @staticmethod
    def _scope_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-16-release-state-and-first-boot-scope.md"

    def test_phase16_scope_doc_exists(self) -> None:
        design_doc = self._scope_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 16 design doc at {design_doc}")

    def test_phase16_scope_doc_defines_bootstrap_contracts(self) -> None:
        design_doc = self._scope_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 16 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "Bootstrap Environment Contract",
            "Migration Bootstrap Contract",
            "Healthcheck and Readiness Contract",
            "Deployment-Entrypoint Contract",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN",
            "must fail closed",
            "migration bootstrap",
            "Healthcheck success",
            "readiness",
            "deployment entrypoint",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
