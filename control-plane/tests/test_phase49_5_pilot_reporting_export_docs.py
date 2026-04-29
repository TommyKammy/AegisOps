from __future__ import annotations

import pathlib
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]


class Phase495PilotReportingExportDocsTests(unittest.TestCase):
    def test_phase49_5_validation_doc_records_bounded_export_contract(self) -> None:
        path = (
            REPO_ROOT
            / "docs/phase-49-5-pilot-reporting-executive-summary-export-validation.md"
        )
        text = path.read_text(encoding="utf-8")

        for term in (
            "Phase 49.5 Pilot Reporting and Executive Summary Export Validation",
            "Validation status: PASS",
            "export_pilot_executive_summary",
            "control-plane/aegisops_control_plane/pilot_reporting_export.py",
            "AegisOps authoritative case records",
            "explicit reviewed pilot release identifier",
            "one repeatable-read snapshot",
            "subordinate_evidence",
            "promotion_allowed: false",
            "do not become workflow truth",
            "compliance certification",
            "SLA guarantees",
            "autonomous response",
            "customer portal availability",
            "multi-tenant reporting",
            "fail closed",
            "secret-looking",
            "workstation-local path",
            "python3 -m unittest control-plane/tests/test_phase49_5_pilot_reporting_export.py",
            "bash scripts/verify-publishable-path-hygiene.sh",
            "No runtime authority, approval, execution, reconciliation, ticket, assistant, optional-extension, or production write behavior changes are introduced by this export.",
        ):
            self.assertIn(term, text)


if __name__ == "__main__":
    unittest.main()
