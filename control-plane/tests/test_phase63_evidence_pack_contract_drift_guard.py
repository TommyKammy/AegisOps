from __future__ import annotations

import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest import mock

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
REPO_ROOT = CONTROL_PLANE_ROOT.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from scripts import phase63_evidence_pack_contract_guard as contract_guard  # noqa: E402
from scripts.phase63_evidence_pack_contract_guard import (  # noqa: E402
    _AI_GROUNDING_ALLOWED_LABEL_FIELDS,
    _ai_confidence_posture_rejection,
    _ai_no_workflow_authority_rejection,
    assert_phase63_evidence_pack_contract_aligned,
    contract_with_drift,
    contract_with_label_drift,
    load_phase63_evidence_pack_contracts,
    _backend_no_workflow_authority_rejection,
    _backend_confidence_posture_rejection,
    _py_ai_state_reason_consistency_rules,
    _py_backend_state_reason_consistency_rules,
    _py_enforced_metadata_fields,
    _py_projection_get_string_rejection_labels,
    _py_projection_get_membership_labels,
    _py_rejected_boolean_value,
    _AI_GROUNDING_SINGLETON_LABEL_FIELDS,
    _ts_enforced_freshness_window_milliseconds,
    _operator_ui_contract_from_source,
    _py_string_constant,
    _ts_forbidden_defined_pack_fields,
    _ts_no_workflow_authority_rejection,
    _ts_rejected_mapping_string_field,
    _ts_rejected_pack_boolean_field,
    _ts_rejected_pack_string_field,
    _ts_state_reason_consistency_rules,
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
                "recognized field",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "recognized_fields",
                        ui.recognized_fields - frozenset({"operator_visible"}),
                    )
                },
                "recognized fields",
            ),
            (
                "freshness window",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "freshness_window_milliseconds",
                        ui.freshness_window_milliseconds + 1,
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
            (
                "workflow truth denial",
                {
                    "ai_grounding_contract": contract_with_drift(
                        ai,
                        "authoritative_workflow_truth",
                        True,
                    )
                },
                "authoritative workflow truth denial",
            ),
            (
                "state reason consistency",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "state_reason_consistency_rules",
                        ui.state_reason_consistency_rules
                        - frozenset({"uncertainty_label_matches_state"}),
                    )
                },
                "state/reason consistency rules",
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
        self.assertEqual(_ts_no_workflow_authority_rejection(source), "none")
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

        confidence_authority_drift = source.replace(
            'asString(confidence.source_native_score_authority) !== "none"',
            'asString(confidence.source_native_score_authority) !== "advisory_only"',
        )
        with self.assertRaisesRegex(AssertionError, "workflow authority"):
            _ts_no_workflow_authority_rejection(confidence_authority_drift)

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

    def test_operator_ui_freshness_window_preserves_millisecond_precision(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            _operator_ui_contract_from_source(source).freshness_window_milliseconds,
            21600000,
        )

        drifted_source = source.replace(
            "6 * 60 * 60 * 1000",
            "6 * 60 * 60 * 1000 + 500",
        )

        self.assertEqual(
            _operator_ui_contract_from_source(
                drifted_source,
            ).freshness_window_milliseconds,
            21600500,
        )

    def test_operator_ui_freshness_window_requires_validator_call(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        drifted_source = source.replace(
            "    validateEvidencePackFreshnessWindow(\n"
            "      custody,\n"
            "      freshnessState,\n"
            "      evidenceRequestId,\n"
            "    );\n",
            "",
        )

        with self.assertRaisesRegex(AssertionError, "FreshnessWindow"):
            _ts_enforced_freshness_window_milliseconds(drifted_source)

    def test_operator_ui_confidence_posture_uses_validator_check(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            _ts_rejected_mapping_string_field(source, "confidence", "posture"),
            "external_hash_reputation_subordinate_context",
        )

        literal_drift = source.replace(
            "asString(confidence.posture) !== EVIDENCE_PACK_CONFIDENCE_POSTURE",
            'asString(confidence.posture) !== "workflow_truth_confidence"',
        )
        self.assertEqual(
            _ts_rejected_mapping_string_field(literal_drift, "confidence", "posture"),
            "workflow_truth_confidence",
        )

        missing_check = source.replace(
            "    if (asString(confidence.posture) !== EVIDENCE_PACK_CONFIDENCE_POSTURE) {\n"
            "      throw new OperatorDataProviderContractError(\n"
            "        `Resource cases linked_evidence_packs item ${evidenceRequestId} has an unsupported confidence posture.`,\n"
            "      );\n"
            "    }\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "confidence.posture"):
            _ts_rejected_mapping_string_field(missing_check, "confidence", "posture")

    def test_operator_ui_label_contract_requires_enforcement_calls(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        drifted_source = source.replace(
            '    validateEvidencePackLabel("source_state", sourceState, evidenceRequestId);\n',
            "",
        )

        with self.assertRaisesRegex(AssertionError, "label enforcement"):
            _operator_ui_contract_from_source(drifted_source)

    def test_operator_ui_metadata_contract_requires_enforcement_calls(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")

        reason_drift = source.replace(
            "    validateEvidencePackReasons(\n"
            "      pack.degraded_reasons,\n"
            "      EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS,\n"
            "    );\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "reason enforcement"):
            _operator_ui_contract_from_source(reason_drift)

        metadata_drift = source.replace(
            "    validateEvidencePackMetadataMap(\n"
            "      confidence,\n"
            "      EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS,\n"
            "      evidenceRequestId,\n"
            "    );\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "metadata enforcement"):
            _operator_ui_contract_from_source(metadata_drift)

    def test_operator_ui_recognized_fields_follow_spread_set(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        contract = _operator_ui_contract_from_source(source)
        self.assertIn("operator_visible", contract.recognized_fields)

        drifted_source = source.replace('  "operator_visible",\n', "")
        self.assertNotIn(
            "operator_visible",
            _operator_ui_contract_from_source(drifted_source).recognized_fields,
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

    def test_backend_confidence_posture_parser_observes_representative_drift(
        self,
    ) -> None:
        source = BACKEND_EVIDENCE_PACK_PROJECTION.read_text(encoding="utf-8")
        self.assertEqual(
            _backend_confidence_posture_rejection(
                source,
                "external_hash_reputation_subordinate_context",
            ),
            "external_hash_reputation_subordinate_context",
        )

        literal_drift = source.replace(
            "registry_entry.confidence_posture",
            '"workflow_truth_confidence"',
        )
        self.assertEqual(
            _backend_confidence_posture_rejection(
                literal_drift,
                "external_hash_reputation_subordinate_context",
            ),
            "workflow_truth_confidence",
        )

        missing_check_drift = source.replace(
            '    if (\n'
            '        _optional_string_from_mapping(confidence, "posture")\n'
            "        != registry_entry.confidence_posture\n"
            "    ):\n"
            '        raise ValueError("linked evidence-pack projection confidence posture mismatch")\n',
            "",
        )
        with self.assertRaisesRegex(AssertionError, "confidence posture"):
            _backend_confidence_posture_rejection(
                missing_check_drift,
                "external_hash_reputation_subordinate_context",
            )

    def test_ai_singleton_label_parser_observes_representative_drift(self) -> None:
        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            _py_projection_get_string_rejection_labels(
                source,
                _AI_GROUNDING_SINGLETON_LABEL_FIELDS,
            ),
            {
                "consumer": frozenset({"ai_grounding"}),
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

    def test_ai_allowed_label_parser_observes_representative_drift(self) -> None:
        from aegisops.control_plane.assistant import ai_grounding_validation

        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            _py_projection_get_membership_labels(
                source,
                _AI_GROUNDING_ALLOWED_LABEL_FIELDS,
                ai_grounding_validation,
            )["status"],
            ai_grounding_validation._ALLOWED_STATUS,
        )

        missing_check = source.replace(
            '    if projection.get("status") not in _ALLOWED_STATUS:\n'
            '        reasons.append("unsupported_grounding_status")\n',
            "",
        )
        with self.assertRaisesRegex(AssertionError, "status"):
            _py_projection_get_membership_labels(
                missing_check,
                _AI_GROUNDING_ALLOWED_LABEL_FIELDS,
                ai_grounding_validation,
            )

        wrong_constant = source.replace(
            'projection.get("status") not in _ALLOWED_STATUS',
            'projection.get("status") not in _ALLOWED_FRESHNESS',
        )
        with self.assertRaisesRegex(AssertionError, "unexpected constant"):
            _py_projection_get_membership_labels(
                wrong_constant,
                _AI_GROUNDING_ALLOWED_LABEL_FIELDS,
                ai_grounding_validation,
            )

    def test_ai_no_workflow_authority_parser_observes_representative_drift(
        self,
    ) -> None:
        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(_ai_no_workflow_authority_rejection(source), "none")

        workflow_drift = source.replace(
            'projection.get("workflow_authority") != _NO_WORKFLOW_AUTHORITY',
            'projection.get("workflow_authority") != "advisory_only"',
        )
        with self.assertRaisesRegex(AssertionError, "AI workflow authority"):
            _ai_no_workflow_authority_rejection(workflow_drift)

        confidence_authority_drift = source.replace(
            'confidence.get("source_native_score_authority") != _NO_WORKFLOW_AUTHORITY',
            'confidence.get("source_native_score_authority") != "advisory_only"',
        )
        with self.assertRaisesRegex(AssertionError, "AI workflow authority"):
            _ai_no_workflow_authority_rejection(confidence_authority_drift)

    def test_ai_confidence_posture_parser_observes_representative_drift(self) -> None:
        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            _ai_confidence_posture_rejection(
                source,
                "external_hash_reputation_subordinate_context",
            ),
            "external_hash_reputation_subordinate_context",
        )

        literal_drift = source.replace(
            'confidence.get("posture") != registry_entry.confidence_posture',
            'confidence.get("posture") != "workflow_truth_confidence"',
        )
        self.assertEqual(
            _ai_confidence_posture_rejection(
                literal_drift,
                "external_hash_reputation_subordinate_context",
            ),
            "workflow_truth_confidence",
        )

        missing_reason_drift = source.replace(
            '"grounding_confidence_posture_mismatch"',
            '"grounding_confidence_posture_changed"',
        )
        with self.assertRaisesRegex(AssertionError, "AI confidence posture"):
            _ai_confidence_posture_rejection(
                missing_reason_drift,
                "external_hash_reputation_subordinate_context",
            )

    def test_ai_metadata_contract_uses_validator_allowed_fields(self) -> None:
        from aegisops.control_plane.assistant import ai_grounding_validation

        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        fields = _py_enforced_metadata_fields(source, ai_grounding_validation)
        self.assertEqual(
            fields["confidence"],
            ai_grounding_validation._ALLOWED_CONFIDENCE_FIELDS,
        )

        drifted_namespace = SimpleNamespace(
            _REQUIRED_CUSTODY_FIELDS=ai_grounding_validation._REQUIRED_CUSTODY_FIELDS,
            _REQUIRED_PROVENANCE_FIELDS=(
                ai_grounding_validation._REQUIRED_PROVENANCE_FIELDS
            ),
            _REQUIRED_CONFIDENCE_FIELDS=(
                tuple(
                    field
                    for field in ai_grounding_validation._REQUIRED_CONFIDENCE_FIELDS
                    if field != "ambiguity_badge"
                )
            ),
            _ALLOWED_CUSTODY_FIELDS=ai_grounding_validation._ALLOWED_CUSTODY_FIELDS,
            _ALLOWED_PROVENANCE_FIELDS=(
                ai_grounding_validation._ALLOWED_PROVENANCE_FIELDS
            ),
            _ALLOWED_CONFIDENCE_FIELDS=ai_grounding_validation._ALLOWED_CONFIDENCE_FIELDS,
        )
        with self.assertRaisesRegex(AssertionError, "metadata enforcement"):
            _py_enforced_metadata_fields(source, drifted_namespace)

    def test_workflow_truth_boolean_rejections_are_parsed(self) -> None:
        backend_source = BACKEND_EVIDENCE_PACK_PROJECTION.read_text(encoding="utf-8")
        ai_source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        ui_source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")

        self.assertFalse(
            _py_rejected_boolean_value(
                backend_source,
                ("get", "projection", "authoritative_workflow_truth"),
            )
        )
        self.assertFalse(
            _py_rejected_boolean_value(
                ai_source,
                ("get", "projection", "authoritative_workflow_truth"),
            )
        )
        self.assertFalse(
            _ts_rejected_pack_boolean_field(
                ui_source,
                "authoritative_workflow_truth",
            )
        )

        ui_drift = ui_source.replace(
            "pack.authoritative_workflow_truth !== false",
            "pack.authoritative_workflow_truth !== true",
        )
        self.assertTrue(
            _ts_rejected_pack_boolean_field(
                ui_drift,
                "authoritative_workflow_truth",
            )
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

    def test_state_reason_consistency_rules_are_loaded_from_validators(self) -> None:
        backend_source = BACKEND_EVIDENCE_PACK_PROJECTION.read_text(encoding="utf-8")
        ai_source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        ui_source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")

        self.assertIn(
            "uncertainty_label_matches_state",
            _py_backend_state_reason_consistency_rules(backend_source),
        )
        self.assertIn(
            "available_status_has_no_reasons",
            _py_ai_state_reason_consistency_rules(ai_source),
        )
        self.assertIn(
            "confidence_ambiguity_badge_matches_conflict",
            _ts_state_reason_consistency_rules(ui_source),
        )

        backend_drift = backend_source.replace(
            'values["status"] == "available"',
            'values["status"] == "ready"',
        )
        with self.assertRaisesRegex(AssertionError, "state/reason"):
            _py_backend_state_reason_consistency_rules(backend_drift)

        ai_drift = ai_source.replace(
            "    reasons.extend(_state_consistency_reasons(projection))\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "state/reason"):
            _py_ai_state_reason_consistency_rules(ai_drift)

        ui_drift = ui_source.replace(
            "    validateEvidencePackReasonConsistency(pack, confidence, {\n"
            "      status,\n"
            "      freshnessState,\n"
            "      conflictState,\n"
            "      sourceState,\n"
            "      uncertaintyLabel,\n"
            "    });\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "ReasonConsistency"):
            _ts_state_reason_consistency_rules(ui_drift)

    def test_python_string_constant_does_not_require_legacy_ast_str(self) -> None:
        legacy_ast_str = getattr(contract_guard.ast, "Str", None)
        if legacy_ast_str is not None:
            delattr(contract_guard.ast, "Str")
        try:
            self.assertIsNone(_py_string_constant(contract_guard.ast.Constant(value=1)))
            self.assertEqual(
                _py_string_constant(contract_guard.ast.Constant(value="none")),
                "none",
            )
        finally:
            if legacy_ast_str is not None:
                setattr(contract_guard.ast, "Str", legacy_ast_str)


if __name__ == "__main__":
    unittest.main()
