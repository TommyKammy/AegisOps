from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase29SuricataEvidencePackBoundaryValidationTests(unittest.TestCase):
    @staticmethod
    def _read(relative_path: str) -> str:
        path = REPO_ROOT / relative_path
        if not path.exists():
            raise AssertionError(f"expected document at {path}")
        return path.read_text(encoding="utf-8")

    def test_phase29_suricata_design_doc_exists_and_keeps_suricata_subordinate(
        self,
    ) -> None:
        text = self._read("docs/phase-29-optional-suricata-evidence-pack-boundary.md")

        for term in (
            "# AegisOps Phase 29 Optional Suricata Evidence-Pack Boundary",
            "This document defines the reviewed optional Suricata evidence-pack boundary for Phase 29.",
            "Suricata integration is optional, disabled by default, and subordinate to the AegisOps-owned control-plane record chain.",
            "Suricata is approved only as a subordinate evidence-pack and shadow-correlation substrate for this reviewed slice.",
            "Suricata-derived output is optional augmentation, not a mandatory platform dependency or case-truth authority surface.",
            "A reviewed Suricata evidence pack may be used only when an existing operating need or explicit evidence gap is already present on the reviewed case chain.",
            "Suricata collection or parsing must start from an existing AegisOps-owned case, evidence record, or reviewed follow-up decision rather than from free-form network hunting or substrate-first alerting.",
            "The approved artifact classes for this boundary are:",
            "`collection_manifest`",
            "`alert_sample`",
            "`flow_excerpt`",
            "`shadow_correlation_note`",
            "`tool_output_receipt`",
            "Every Suricata-derived artifact must preserve provenance that identifies the reviewed observer or sensor binding, source family, source event or flow identifier when available, bounded time window, reviewed operator or reviewed automation attribution, and the AegisOps evidence record that admitted it.",
            "Suricata-derived artifacts and shadow correlation notes must be cited as subordinate evidence linked to an AegisOps-owned evidence record.",
            "Suricata-derived output must not replace AegisOps-owned alert truth, case truth, evidence truth, approval truth, execution truth, or reconciliation truth.",
            "This boundary does not approve network-first mainline detection, broad IDS-led workflow redesign, mandatory Suricata deployment, or substrate authority expansion.",
            "The path must fail closed when provenance is partial, the observer or subject scope is only inferred, the requested artifact class falls outside this reviewed slice, the boundary is enabled without an explicit reviewed need, or a citation would overstate what the subordinate network telemetry actually proved.",
        ):
            self.assertIn(term, text)

    def test_phase29_suricata_validation_doc_records_boundary_and_shadow_mode_review(
        self,
    ) -> None:
        text = self._read(
            "docs/phase-29-optional-suricata-evidence-pack-boundary-validation.md"
        )

        for term in (
            "# Phase 29 Optional Suricata Evidence-Pack Boundary Validation",
            "Validation status: PASS",
            "ObsidianVault/Dev/AegisOps/Plan&Roadmap/Revised Phase23-29 Epic Roadmap.md",
            "`README.md`",
            "`docs/architecture.md`",
            "`docs/canonical-telemetry-schema-baseline.md`",
            "`docs/phase-28-optional-endpoint-evidence-pack-boundary.md`",
            "`docs/phase-29-reviewed-ml-shadow-mode-boundary.md`",
            "The reviewed Suricata boundary remains optional, disabled by default, provenance-preserving, and fail closed when reviewed linkage or scope is incomplete.",
            "Suricata integration is optional, disabled by default, and subordinate to the AegisOps-owned control-plane record chain.",
            "Any Suricata-derived feature, note, or correlation signal must preserve explicit provenance and remain advisory-only.",
            "Suricata-derived output cannot become an authoritative label source and cannot silently promote network telemetry into mainline workflow truth.",
            "No reviewed language in this slice promotes network-first product positioning or broad IDS-led workflow redesign.",
            "python3 -m unittest control-plane.tests.test_phase29_suricata_evidence_pack_boundary_validation",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
