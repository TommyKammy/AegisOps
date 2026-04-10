from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase18WazuhLabTopologyDocsTests(unittest.TestCase):
    @staticmethod
    def _design_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-18-wazuh-lab-topology-and-live-ingest-contract.md"

    @staticmethod
    def _validation_doc() -> pathlib.Path:
        return REPO_ROOT / "docs" / "phase-18-wazuh-lab-topology-validation.md"

    def test_phase18_design_doc_exists(self) -> None:
        design_doc = self._design_doc()

        self.assertTrue(design_doc.exists(), f"expected Phase 18 design doc at {design_doc}")

    def test_phase18_design_doc_defines_topology_source_family_and_ingest_contract(self) -> None:
        design_doc = self._design_doc()
        self.assertTrue(design_doc.exists(), f"expected Phase 18 design doc at {design_doc}")
        text = design_doc.read_text(encoding="utf-8")

        for term in (
            "Approved Phase 18 Lab Topology",
            "single-node Wazuh",
            "bootable AegisOps control-plane runtime boundary",
            "Approved First Live Source Family",
            "GitHub audit",
            "reviewed Wazuh custom integration",
            "HTTPS POST",
            "Authorization: Bearer",
            "shared secret",
            "must fail closed",
            "Wazuh -> AegisOps",
            "must not make `Wazuh -> Shuffle` part of the first live slice",
            "OpenSearch runtime enrichment",
            "thin operator UI",
            "guarded automation live wiring",
        ):
            self.assertIn(term, text)

    def test_phase18_validation_doc_exists_and_records_deferred_scope(self) -> None:
        validation_doc = self._validation_doc()
        self.assertTrue(
            validation_doc.exists(),
            f"expected Phase 18 validation doc at {validation_doc}",
        )
        text = validation_doc.read_text(encoding="utf-8")

        for term in (
            "Phase 18 Wazuh Lab Topology and Live Ingest Contract Validation",
            "Validation status: PASS",
            "single-node Wazuh lab target",
            "GitHub audit as the approved first live source family",
            "Wazuh -> AegisOps as the mainline live path",
            "fail-closed expectations for transport, authentication, and payload admission",
            "OpenSearch runtime enrichment, thin operator UI, and guarded automation live wiring remain deferred",
            "Phase 16-21 Epic Roadmap.md",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
