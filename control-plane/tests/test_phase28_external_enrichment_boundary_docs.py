from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase28ExternalEnrichmentBoundaryDocsTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase28_design_doc_exists_and_defines_direct_adapter_first_contract(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-28-bounded-external-enrichment-direct-adapter-boundary.md"
        )

        for term in (
            "# AegisOps Phase 28 Bounded External Enrichment Direct-Adapter Boundary",
            "This document defines the reviewed bounded external enrichment contract for direct read-only adapters first.",
            "Direct read-only adapters are the approved starting pattern for this slice.",
            "Aggregator-first architecture is not approved for this boundary.",
            "External enrichment remains subordinate to AegisOps-owned evidence and case truth.",
            "External enrichment may be attached only to an existing AegisOps-owned case, evidence record, finding, or reviewed assistant context snapshot.",
            "The path must fail closed when provenance, source scope, citation anchors, or staleness details are missing, malformed, or only partially trusted.",
            "`lookup_receipt`",
            "`source_observation`",
            "`citation_attachment`",
            "`conflict_marker`",
            "`staleness_marker`",
            "VirusTotal",
            "urlscan",
            "AbuseIPDB",
            "The contract must preserve source identity, lookup time, source-specific object queried, response freshness, and the reviewed AegisOps anchor that admitted the attachment.",
            "External source output must not replace or overwrite AegisOps-owned case truth, evidence truth, approval truth, or reconciliation truth.",
            "Conflicts between external source output and AegisOps-owned records must stay explicit and must not be collapsed into one preferred summary by convenience.",
            "IntelOwl-first architecture, automated write-back, external-truth replacement, and free-form public-internet pivots remain out of scope.",
        ):
            self.assertIn(term, text)

    def test_phase28_validation_doc_records_alignment_with_roadmap_and_baselines(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-28-bounded-external-enrichment-direct-adapter-boundary-validation.md"
        )

        for term in (
            "# Phase 28 Bounded External Enrichment Direct-Adapter Boundary Validation",
            "Validation status: PASS",
            "ObsidianVault/Dev/AegisOps/Plan&Roadmap/Revised Phase23-29 Epic Roadmap.md",
            "docs/requirements-baseline.md",
            "docs/architecture.md",
            "docs/phase-15-identity-grounded-analyst-assistant-boundary.md",
            "docs/safe-query-gateway-and-tool-policy.md",
            "The reviewed boundary keeps direct external enrichment adapters read-only, bounded, and subordinate to AegisOps-owned truth.",
            "Aggregator-first design remains out of scope for this slice.",
            "Conflicts and stale external context stay visible as subordinate uncertainty rather than becoming case truth.",
            "python3 -m unittest control-plane.tests.test_phase28_external_enrichment_boundary_docs",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
