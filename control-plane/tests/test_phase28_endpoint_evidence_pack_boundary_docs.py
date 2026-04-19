from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase28EndpointEvidencePackBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase28_design_doc_exists_and_keeps_endpoint_evidence_subordinate(
        self,
    ) -> None:
        text = self._read("docs/phase-28-optional-endpoint-evidence-pack-boundary.md")

        for term in (
            "# AegisOps Phase 28 Optional Endpoint Evidence-Pack Boundary",
            "This document defines the reviewed optional endpoint evidence-pack boundary for Phase 28.",
            "Velociraptor is approved only as a subordinate read and evidence-collection substrate for this slice.",
            "YARA and capa are approved only as subordinate evidence-pack analysis tools for collected files or binaries inside this same boundary.",
            "Endpoint evidence packs are optional augmentation, not a mandatory platform dependency or case-truth authority surface.",
            "A reviewed endpoint evidence pack may be used only when an existing operating need or explicit evidence gap is already present on the reviewed case chain.",
            "Endpoint evidence collection must start from an existing AegisOps-owned case, evidence record, or reviewed follow-up decision rather than from free-form endpoint hunting.",
            "The approved artifact classes for this boundary are:",
            "`collection_manifest`",
            "`triage_bundle`",
            "`file_sample`",
            "`binary_analysis`",
            "`tool_output_receipt`",
            "Every collected or derived artifact must preserve provenance that identifies the source host binding, collector or tool identity, collection or analysis time, reviewed operator attribution, and the AegisOps evidence record that admitted it.",
            "Collected endpoint artifacts and derived YARA or capa outputs must be cited as subordinate evidence linked to an AegisOps-owned evidence record.",
            "Endpoint evidence packs must not replace AegisOps-owned case truth, actor truth, approval truth, or reconciliation truth.",
            "This boundary does not approve mandatory agent rollout, endpoint-first product repositioning, background fleet sweeps, autonomous collection, or endpoint-tool authority expansion.",
        ):
            self.assertIn(term, text)

    def test_phase28_validation_doc_records_roadmap_and_baseline_review(self) -> None:
        text = self._read(
            "docs/phase-28-optional-endpoint-evidence-pack-boundary-validation.md"
        )

        for term in (
            "# Phase 28 Optional Endpoint Evidence-Pack Boundary Validation",
            "Validation status: PASS",
            "docs/Revised Phase23-20 Epic Roadmap.md",
            "docs/requirements-baseline.md",
            "docs/architecture.md",
            "docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md",
            "docs/phase-25-multi-source-case-review-and-osquery-evidence-runbook.md",
            "Velociraptor remains subordinate to the AegisOps control-plane authority model.",
            "YARA and capa remain subordinate evidence-analysis tools rather than authority surfaces.",
            "Endpoint evidence packs remain optional, provenance-preserving, and fail closed when prerequisite case-chain linkage or provenance is incomplete.",
            'python3 -m unittest control-plane.tests.test_phase28_endpoint_evidence_pack_boundary_docs',
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
