from __future__ import annotations

import pathlib
import sys
import unittest
from unittest import mock

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
REPO_ROOT = CONTROL_PLANE_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from scripts.phase63_evidence_pack_contract_guard import (  # noqa: E402
    assert_phase63_evidence_pack_contract_aligned,
    contract_with_drift,
    contract_with_label_drift,
    load_phase63_evidence_pack_contracts,
    _backend_no_workflow_authority_rejection,
    _py_projection_get_string_rejection_labels,
    _AI_GROUNDING_SINGLETON_LABEL_FIELDS,
    _ts_forbidden_defined_pack_fields,
    _ts_rejected_pack_string_field,
)


OPERATOR_UI_VALIDATOR = (
    REPO_ROOT
    / "apps"
    / "operator-ui"
    / "src"
    / "operatorDataProvider"
    / "linkedEvidencePackValidator.ts"
)
BACKEND_EVIDENCE_PACK_PROJECTION = (
    REPO_ROOT
    / "control-plane"
    / "aegisops"
    / "control_plane"
    / "inspection"
    / "evidence_pack_projection.py"
)
AI_GROUNDING_VALIDATOR = (
    REPO_ROOT
    / "control-plane"
    / "aegisops"
    / "control_plane"
    / "assistant"
    / "ai_grounding_validation.py"
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

    def test_operator_ui_authority_and_readiness_denials_are_parsed(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            _ts_rejected_pack_string_field(source, "workflow_authority"),
            "none",
        )
        self.assertEqual(
            _ts_forbidden_defined_pack_fields(
                source,
                "cannot claim release readiness",
            ),
            frozenset(
                {
                    "release_readiness_claim",
                    "rc_readiness_claim",
                    "gate_readiness_claim",
                }
            ),
        )

    def test_operator_ui_denial_parser_observes_representative_drift(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")

        workflow_drift = source.replace(
            'workflowAuthority !== "none"',
            'workflowAuthority !== "advisory_only"',
        )
        self.assertEqual(
            _ts_rejected_pack_string_field(workflow_drift, "workflow_authority"),
            "advisory_only",
        )

        readiness_drift = source.replace(
            "      pack.gate_readiness_claim !== undefined\n",
            "",
        )
        self.assertEqual(
            _ts_forbidden_defined_pack_fields(
                readiness_drift,
                "cannot claim release readiness",
            ),
            frozenset({"release_readiness_claim", "rc_readiness_claim"}),
        )

    def test_backend_authority_parser_observes_representative_drift(self) -> None:
        source = BACKEND_EVIDENCE_PACK_PROJECTION.read_text(encoding="utf-8")
        self.assertEqual(_backend_no_workflow_authority_rejection(source), "none")

        drifted_source = source.replace(
            'typed_values["workflow_authority"] != "none"',
            'typed_values["workflow_authority"] != "advisory_only"',
        )
        with self.assertRaisesRegex(AssertionError, "backend workflow authority"):
            _backend_no_workflow_authority_rejection(drifted_source)

    def test_ai_singleton_label_parser_observes_representative_drift(self) -> None:
        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            _py_projection_get_string_rejection_labels(
                source,
                _AI_GROUNDING_SINGLETON_LABEL_FIELDS,
            ),
            {
                "custody_state": frozenset({"complete"}),
                "provenance_state": frozenset({"bound"}),
                "confidence_state": frozenset({"present"}),
            },
        )

        drifted_source = source.replace(
            'projection.get("custody_state") != "complete"',
            'projection.get("custody_state") != "reviewed"',
        )
        self.assertEqual(
            _py_projection_get_string_rejection_labels(
                drifted_source,
                _AI_GROUNDING_SINGLETON_LABEL_FIELDS,
            )["custody_state"],
            frozenset({"reviewed"}),
        )

    def test_ai_authority_truth_denials_follow_scanner(self) -> None:
        from aegisops.control_plane.assistant import ai_grounding_validation

        original_scanner = ai_grounding_validation._scan_for_authority_claim

        def scanner_with_gap(value: object) -> bool:
            if value == "readiness_truth":
                return False
            return original_scanner(value)

        with mock.patch.object(
            ai_grounding_validation,
            "_scan_for_authority_claim",
            side_effect=scanner_with_gap,
        ):
            _, _, ai = load_phase63_evidence_pack_contracts(REPO_ROOT)

        self.assertNotIn("readiness_truth", ai.authority_truth_denials)


if __name__ == "__main__":
    unittest.main()
