from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase17RuntimeConfigContractDocsTests(unittest.TestCase):
    @staticmethod
    def _contract_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-17-runtime-config-contract-and-boot-command-expectations.md"

    def test_phase17_contract_doc_exists(self) -> None:
        contract_doc = self._contract_doc()

        self.assertTrue(contract_doc.exists(), f"expected Phase 17 contract doc at {contract_doc}")

    def test_phase17_contract_doc_defines_runtime_config_and_boot_expectations(self) -> None:
        contract_doc = self._contract_doc()
        self.assertTrue(contract_doc.exists(), f"expected Phase 17 contract doc at {contract_doc}")
        text = contract_doc.read_text(encoding="utf-8")

        for term in (
            "Runtime Config Contract",
            "Boot Command Expectations",
            "Approved Required Runtime Environment Keys",
            "Approved Optional and Deferred Environment Keys",
            "AEGISOPS_CONTROL_PLANE_HOST",
            "AEGISOPS_CONTROL_PLANE_PORT",
            "AEGISOPS_CONTROL_PLANE_POSTGRES_DSN",
            "AEGISOPS_CONTROL_PLANE_BOOT_MODE",
            "AEGISOPS_CONTROL_PLANE_LOG_LEVEL",
            "control-plane service process",
            "migration bootstrap",
            "reverse proxy",
            "must fail closed",
            "must not publish the control-plane backend port directly",
            "Phase 16 placeholders become concrete runtime expectations",
            "remain deferred",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
