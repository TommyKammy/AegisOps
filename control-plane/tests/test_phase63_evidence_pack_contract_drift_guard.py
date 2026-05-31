from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
REPO_ROOT = CONTROL_PLANE_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.phase63_evidence_pack_contract_guard import (  # noqa: E402
    assert_phase63_evidence_pack_contract_aligned,
    contract_with_drift,
    contract_with_label_drift,
    load_phase63_evidence_pack_contracts,
)


class Phase63EvidencePackContractDriftGuardTests(unittest.TestCase):
    def test_phase63_evidence_pack_contracts_stay_aligned(self) -> None:
        assert_phase63_evidence_pack_contract_aligned(REPO_ROOT)

    def test_drift_guard_fails_on_representative_contract_mismatches(self) -> None:
        backend, ui, ai = load_phase63_evidence_pack_contracts(REPO_ROOT)
        mismatch_cases = (
            (
                "label",
                {
                    "operator_ui_contract": contract_with_label_drift(
                        ui,
                        "status",
                        frozenset({"available"}),
                    )
                },
                "status labels",
            ),
            (
                "degraded reason",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "degraded_reasons",
                        frozenset({"stale_reputation"}),
                    )
                },
                "degraded reasons",
            ),
            (
                "custody field",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "required_custody_fields",
                        ui.required_custody_fields - frozenset({"response_digest"}),
                    )
                },
                "custody fields",
            ),
            (
                "provenance field",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "required_provenance_fields",
                        ui.required_provenance_fields
                        - frozenset({"custody_reference"}),
                    )
                },
                "provenance fields",
            ),
            (
                "confidence field",
                {
                    "ai_grounding_contract": contract_with_drift(
                        ai,
                        "required_confidence_fields",
                        ai.required_confidence_fields
                        - frozenset({"ambiguity_badge"}),
                    )
                },
                "confidence fields",
            ),
            (
                "source ID",
                {
                    "ai_grounding_contract": contract_with_drift(
                        ai,
                        "supported_source_ids",
                        frozenset({"sample_hash_reputation"}),
                    )
                },
                "source IDs",
            ),
            (
                "freshness window",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "freshness_window_seconds",
                        ui.freshness_window_seconds + 1,
                    )
                },
                "freshness window",
            ),
            (
                "uncertainty label",
                {
                    "ai_grounding_contract": contract_with_label_drift(
                        ai,
                        "uncertainty_label",
                        ai.labels["uncertainty_label"]
                        - frozenset({"source_unavailable"}),
                    )
                },
                "uncertainty_label labels",
            ),
            (
                "forbidden projection source",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "forbidden_projection_sources",
                        ui.forbidden_projection_sources - frozenset({"browser_state"}),
                    )
                },
                "forbidden projection sources",
            ),
            (
                "readiness claim",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "forbidden_readiness_claim_fields",
                        ui.forbidden_readiness_claim_fields
                        - frozenset({"gate_readiness_claim"}),
                    )
                },
                "readiness claim fields",
            ),
            (
                "authority truth denial",
                {
                    "ai_grounding_contract": contract_with_drift(
                        ai,
                        "authority_truth_denials",
                        ai.authority_truth_denials - frozenset({"readiness_truth"}),
                    )
                },
                "AI authority truth denial posture",
            ),
            (
                "verifier source truth",
                {
                    "backend_contract": contract_with_drift(
                        backend,
                        "no_workflow_authority",
                        "verifier_truth",
                    )
                },
                "no workflow authority",
            ),
        )

        for label, overrides, expected_message in mismatch_cases:
            with self.subTest(label=label):
                with self.assertRaisesRegex(AssertionError, expected_message):
                    assert_phase63_evidence_pack_contract_aligned(
                        REPO_ROOT,
                        backend_contract=overrides.get("backend_contract", backend),
                        operator_ui_contract=overrides.get("operator_ui_contract", ui),
                        ai_grounding_contract=overrides.get(
                            "ai_grounding_contract",
                            ai,
                        ),
                    )


if __name__ == "__main__":
    unittest.main()
