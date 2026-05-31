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
    _py_ai_enforced_freshness_window_milliseconds,
    _py_backend_enforced_label_sets,
    _py_backend_enforced_freshness_window_milliseconds,
    _py_backend_enforced_metadata_fields,
    _py_ai_state_reason_consistency_rules,
    _py_backend_state_reason_consistency_rules,
    _py_enforced_metadata_fields,
    _py_projection_get_string_rejection_labels,
    _py_projection_get_membership_labels,
    _py_rejected_boolean_value,
    _AI_GROUNDING_SINGLETON_LABEL_FIELDS,
    _ts_enforced_freshness_window_milliseconds,
    _ts_forbidden_projection_sources_rejection,
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

    def test_direct_script_entrypoint_runs_guard(self) -> None:
        with mock.patch.object(
            contract_guard,
            "assert_phase63_evidence_pack_contract_aligned",
        ) as guard:
            with mock.patch("builtins.print") as mocked_print:
                contract_guard._main()

        guard.assert_called_once_with()
        mocked_print.assert_called_once_with(
            "Phase 63 evidence-pack contract guard passed"
        )

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
                "provenance binding rule",
                {
                    "backend_contract": contract_with_drift(
                        backend,
                        "provenance_binding_rules",
                        backend.provenance_binding_rules
                        - frozenset({"custody_reference"}),
                    )
                },
                "provenance binding rules",
            ),
            (
                "metadata format rule",
                {
                    "ai_grounding_contract": contract_with_drift(
                        ai,
                        "metadata_format_rules",
                        ai.metadata_format_rules
                        - frozenset({"response_digest"}),
                    )
                },
                "metadata format rules",
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
                "cache-sourced boolean",
                {
                    "operator_ui_contract": contract_with_drift(
                        ui,
                        "cache_boolean_false_fields",
                        ui.cache_boolean_false_fields
                        - frozenset({"stale_cache"}),
                    )
                },
                "cache-sourced boolean denials",
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

        helper_drift = source.replace(
            "  if (!EVIDENCE_PACK_ALLOWED_LABELS[fieldName].has(value)) {\n",
            "  if (false) {\n",
        )
        with self.assertRaisesRegex(AssertionError, "label validator semantics"):
            _operator_ui_contract_from_source(helper_drift)

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

        reason_helper_drift = source.replace(
            "    if (!asString(reason) || !allowedReasons.has(asString(reason) ?? \"\")) {\n",
            "    if (!asString(reason)) {\n",
        )
        with self.assertRaisesRegex(AssertionError, "reason validator semantics"):
            _operator_ui_contract_from_source(reason_helper_drift)

        metadata_helper_drift = source.replace(
            "    fieldNames.length !== requiredFields.size ||\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "metadata-map validator semantics"):
            _operator_ui_contract_from_source(metadata_helper_drift)

    def test_operator_ui_source_authority_and_projection_source_checks_are_parsed(
        self,
    ) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        contract = _operator_ui_contract_from_source(source)
        self.assertEqual(
            contract.supported_source_ids,
            frozenset({"malwarebazaar_hash_reputation"}),
        )
        self.assertEqual(
            contract.subordinate_authority_posture,
            "subordinate_evidence_context_only",
        )
        self.assertEqual(
            _ts_forbidden_projection_sources_rejection(source),
            frozenset({"browser_state", "browser_cache", "ui_cache", "cache"}),
        )

        source_id_drift = source.replace(
            "    if (sourceId !== EVIDENCE_PACK_SUPPORTED_SOURCE_ID) {\n"
            "      throw new OperatorDataProviderContractError(\n"
            "        `Resource cases linked_evidence_packs item ${evidenceRequestId} has an unsupported evidence-pack source.`,\n"
            "      );\n"
            "    }\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "source_id"):
            _operator_ui_contract_from_source(source_id_drift)

        authority_posture_drift = source.replace(
            "      authorityPosture !== EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE ||\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "authority_posture"):
            _operator_ui_contract_from_source(authority_posture_drift)

        projection_source_drift = source.replace(
            "      EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES.has(projectionSource ?? \"\")\n",
            "      false\n",
        )
        with self.assertRaisesRegex(AssertionError, "projection-source"):
            _operator_ui_contract_from_source(projection_source_drift)

        cache_boolean_drift = source.replace(
            "      (pack.stale_cache !== undefined && pack.stale_cache !== false) ||\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "cache-sourced boolean"):
            _operator_ui_contract_from_source(cache_boolean_drift)

    def test_operator_ui_provenance_and_metadata_formats_are_enforced(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        self.assertIn(
            "custody_reference",
            contract_guard._ts_provenance_binding_rules(source),
        )
        self.assertIn(
            "response_digest",
            contract_guard._ts_metadata_format_rules(source),
        )

        provenance_drift = source.replace(
            "      asString(provenance.custody_reference) !==\n"
            "        linkedEvidenceRecordCustodyReference(\n"
            "          response,\n"
            "          evidenceRecordId,\n"
            "          evidenceRequestId,\n"
            "        )\n",
            "      false\n",
        )
        with self.assertRaisesRegex(AssertionError, "provenance binding"):
            contract_guard._ts_provenance_binding_rules(provenance_drift)

        metadata_format_drift = source.replace(
            "    !isSha256Digest(asString(custody.response_digest)) ||\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "metadata format"):
            contract_guard._ts_metadata_format_rules(metadata_format_drift)

    def test_operator_ui_recognized_fields_follow_spread_set(self) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")
        contract = _operator_ui_contract_from_source(source)
        self.assertIn("operator_visible", contract.recognized_fields)

        drifted_source = source.replace('  "operator_visible",\n', "")
        self.assertNotIn(
            "operator_visible",
            _operator_ui_contract_from_source(drifted_source).recognized_fields,
        )

    def test_operator_ui_authority_visibility_and_recognized_rejections_are_enforced(
        self,
    ) -> None:
        source = OPERATOR_UI_VALIDATOR.read_text(encoding="utf-8")

        self.assertEqual(
            contract_guard._ts_subordinate_authority_posture_rejection(source),
            "subordinate_evidence_context_only",
        )
        self.assertTrue(
            contract_guard._ts_rejected_optional_pack_boolean_field(
                source,
                "operator_visible",
            )
        )
        self.assertIn("operator_visible", contract_guard._ts_recognized_fields_rejection(source))

        provenance_authority_drift = source.replace(
            "    if (\n"
            "      asString(provenance.authority_posture) !==\n"
            "      EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE\n"
            "    ) {\n"
            "      throw new OperatorDataProviderContractError(\n"
            "        `Resource cases linked_evidence_packs item ${evidenceRequestId} must keep provenance subordinate.`,\n"
            "      );\n"
            "    }\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "authority_posture"):
            contract_guard._ts_subordinate_authority_posture_rejection(
                provenance_authority_drift,
            )

        operator_visible_drift = source.replace(
            "pack.operator_visible !== true",
            "pack.operator_visible !== false",
        )
        self.assertFalse(
            contract_guard._ts_rejected_optional_pack_boolean_field(
                operator_visible_drift,
                "operator_visible",
            )
        )

        recognized_rejection_drift = source.replace(
            "    if (\n"
            "      Object.keys(pack).some(\n"
            "        (fieldName) => !EVIDENCE_PACK_RECOGNIZED_FIELDS.has(fieldName),\n"
            "      )\n"
            "    ) {\n"
            "      throw new OperatorDataProviderContractError(\n"
            "        `Resource cases linked_evidence_packs item ${evidenceRequestId} has unexpected evidence-pack fields.`,\n"
            "      );\n"
            "    }\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "recognized-field"):
            contract_guard._ts_recognized_fields_rejection(recognized_rejection_drift)

    def test_backend_authority_parser_observes_representative_drift(self) -> None:
        source = BACKEND_EVIDENCE_PACK_PROJECTION.read_text(encoding="utf-8")
        self.assertEqual(_backend_no_workflow_authority_rejection(source), "none")

        drifted_source = source.replace(
            'typed_values["workflow_authority"] != "none"',
            'typed_values["workflow_authority"] != "advisory_only"',
        )
        with self.assertRaisesRegex(AssertionError, "backend workflow authority"):
            _backend_no_workflow_authority_rejection(drifted_source)

    def test_backend_authority_reason_and_boundary_rejections_are_enforced(self) -> None:
        from aegisops.control_plane.inspection import evidence_pack_projection

        source = BACKEND_EVIDENCE_PACK_PROJECTION.read_text(encoding="utf-8")

        self.assertEqual(
            contract_guard._backend_subordinate_authority_posture_rejection(source),
            "subordinate_evidence_context_only",
        )
        self.assertTrue(
            contract_guard._py_rejected_optional_boolean_value(
                source,
                ("get", "projection", "operator_visible"),
            )
        )
        self.assertEqual(
            contract_guard._py_backend_enforced_reason_sets(
                source,
                evidence_pack_projection,
            )["degraded_reasons"],
            evidence_pack_projection._EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS,
        )
        self.assertIn(
            "operator_visible",
            contract_guard._py_backend_recognized_fields_rejection(
                source,
                evidence_pack_projection,
            ),
        )
        self.assertEqual(
            contract_guard._py_backend_forbidden_projection_sources_rejection(
                source,
                evidence_pack_projection,
            ),
            evidence_pack_projection._EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES,
        )
        self.assertIn(
            "custody_reference",
            contract_guard._py_backend_provenance_binding_rules(source),
        )
        self.assertIn(
            "response_digest",
            contract_guard._py_backend_metadata_format_rules(source),
        )
        self.assertEqual(
            contract_guard._py_backend_cache_boolean_rejections(source),
            frozenset({"cache_sourced", "stale_cache"}),
        )
        self.assertEqual(
            contract_guard._py_backend_forbidden_readiness_claim_rejection(
                source,
                evidence_pack_projection,
            ),
            evidence_pack_projection._EVIDENCE_PACK_FORBIDDEN_READINESS_CLAIMS,
        )

        provenance_authority_drift = source.replace(
            '    if (\n'
            '        _optional_string_from_mapping(provenance, "authority_posture")\n'
            "        != _EVIDENCE_PACK_SUBORDINATE_AUTHORITY_POSTURE\n"
            "    ):\n"
            '        raise ValueError("linked evidence-pack projection must stay subordinate")\n',
            "",
        )
        with self.assertRaisesRegex(AssertionError, "authority posture"):
            contract_guard._backend_subordinate_authority_posture_rejection(
                provenance_authority_drift,
            )

        reason_drift = source.replace(
            "    if any(\n"
            "        reason not in _EVIDENCE_PACK_ALLOWED_DEGRADED_REASONS\n"
            "        for reason in degraded_reasons\n"
            "    ) or any(\n"
            "        reason not in _EVIDENCE_PACK_ALLOWED_UNAVAILABLE_REASONS\n"
            "        for reason in unavailable_reasons\n"
            "    ):\n"
            "        raise ValueError(\n"
            "            \"linked evidence-pack projection has unsupported evidence-pack projection reason\"\n"
            "        )\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "reason enforcement"):
            contract_guard._py_backend_enforced_reason_sets(
                reason_drift,
                evidence_pack_projection,
            )

        forbidden_source_drift = source.replace(
            "        or projection_source in _EVIDENCE_PACK_FORBIDDEN_PROJECTION_SOURCES\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "projection-source"):
            contract_guard._py_backend_forbidden_projection_sources_rejection(
                forbidden_source_drift,
                evidence_pack_projection,
            )

        cache_boolean_drift = source.replace(
            "        or (stale_cache is not None and stale_cache is not False)\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "cache-sourced boolean"):
            contract_guard._py_backend_cache_boolean_rejections(cache_boolean_drift)

        provenance_binding_drift = source.replace(
            '        "custody_reference": record_custody_reference,\n',
            "",
        )
        with self.assertRaisesRegex(AssertionError, "provenance binding"):
            contract_guard._py_backend_provenance_binding_rules(
                provenance_binding_drift,
            )

        metadata_format_drift = source.replace(
            "    ) or not _is_sha256_digest(\n"
            "        _optional_string_from_mapping(custody, \"response_digest\")\n"
            "    ):\n",
            "    ):\n",
        )
        with self.assertRaisesRegex(AssertionError, "metadata format"):
            contract_guard._py_backend_metadata_format_rules(metadata_format_drift)

        readiness_drift = source.replace(
            "    if any(\n"
            "        claim_name in projection\n"
            "        for claim_name in _EVIDENCE_PACK_FORBIDDEN_READINESS_CLAIMS\n"
            "    ):\n"
            "        raise ValueError(\"linked evidence-pack projection cannot claim release readiness\")\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "readiness-claim"):
            contract_guard._py_backend_forbidden_readiness_claim_rejection(
                readiness_drift,
                evidence_pack_projection,
            )

        recognized_drift = source.replace(
            "    unexpected_fields = (\n"
            "        frozenset(projection) - _EVIDENCE_PACK_PROJECTION_RECOGNIZED_FIELDS\n"
            "    )\n"
            "    if unexpected_fields:\n"
            "        raise ValueError(\n"
            "            \"linked evidence-pack projection has unexpected evidence-pack projection field\"\n"
            "        )\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "recognized-field"):
            contract_guard._py_backend_recognized_fields_rejection(
                recognized_drift,
                evidence_pack_projection,
            )

    def test_backend_label_source_and_metadata_enforcement_are_parsed(self) -> None:
        from aegisops.control_plane.inspection import evidence_pack_projection

        source = BACKEND_EVIDENCE_PACK_PROJECTION.read_text(encoding="utf-8")
        self.assertEqual(
            _py_backend_enforced_label_sets(
                source,
                evidence_pack_projection,
            )["status"],
            frozenset({"available", "degraded", "unavailable"}),
        )
        self.assertEqual(
            contract_guard._py_rejected_string_values(
                source,
                ("subscript", "values", "source_id"),
            ),
            frozenset({"malwarebazaar_hash_reputation"}),
        )
        self.assertEqual(
            _py_backend_enforced_metadata_fields(
                source,
                evidence_pack_projection,
            )["confidence"],
            evidence_pack_projection._EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS,
        )

        label_drift = source.replace(
            "    for field_name, allowed_values in _EVIDENCE_PACK_ALLOWED_PROJECTION_LABELS.items():\n"
            "        if values[field_name] not in allowed_values:\n"
            "            raise ValueError(\n"
            "                \"linked evidence-pack projection has unsupported evidence-pack projection label\"\n"
            "            )\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "label enforcement"):
            _py_backend_enforced_label_sets(label_drift, evidence_pack_projection)

        source_id_drift = source.replace(
            "    if values[\"source_id\"] != _EVIDENCE_PACK_SUPPORTED_SOURCE_ID:\n"
            "        raise ValueError(\n"
            "            \"linked evidence-pack projection has unsupported evidence-pack projection source\"\n"
            "        )\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "source_id"):
            contract_guard._py_rejected_string_values(
                source_id_drift,
                ("subscript", "values", "source_id"),
            )

        metadata_drift = source.replace(
            "    _required_metadata_map_fields(\n"
            "        confidence,\n"
            "        _EVIDENCE_PACK_REQUIRED_CONFIDENCE_FIELDS,\n"
            "    )\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "metadata enforcement"):
            _py_backend_enforced_metadata_fields(
                metadata_drift,
                evidence_pack_projection,
            )

    def test_backend_freshness_window_enforcement_is_parsed(self) -> None:
        from aegisops.control_plane.evidence import (
            evidence_freshness_provenance_projection,
        )

        source = BACKEND_EVIDENCE_PACK_PROJECTION.read_text(encoding="utf-8")
        self.assertEqual(
            _py_backend_enforced_freshness_window_milliseconds(
                source,
                "PT6H",
                evidence_freshness_provenance_projection,
            ),
            21600000,
        )

        missing_call_drift = source.replace(
            "    _validate_linked_evidence_pack_freshness_window(\n"
            "        values=typed_values,\n"
            "        custody=custody,\n"
            "    )\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "freshness-window enforcement call"):
            _py_backend_enforced_freshness_window_milliseconds(
                missing_call_drift,
                "PT6H",
                evidence_freshness_provenance_projection,
            )

        missing_registry_window_drift = source.replace(
            "_parse_duration_seconds(registry_entry.freshness_window)",
            '_parse_duration_seconds("PT6H")',
        )
        with self.assertRaisesRegex(AssertionError, "freshness-window enforcement"):
            _py_backend_enforced_freshness_window_milliseconds(
                missing_registry_window_drift,
                "PT6H",
                evidence_freshness_provenance_projection,
            )

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

    def test_ai_source_provenance_and_metadata_enforcement_are_parsed(self) -> None:
        from aegisops.control_plane.assistant import ai_grounding_validation

        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            contract_guard._py_ai_supported_source_ids_rejection(
                source,
                ai_grounding_validation,
            ),
            frozenset({"malwarebazaar_hash_reputation"}),
        )
        self.assertIn(
            "custody_reference",
            contract_guard._py_ai_provenance_binding_rules(source),
        )
        self.assertIn(
            "response_digest",
            contract_guard._py_ai_metadata_format_rules(source),
        )

        source_id_drift = source.replace(
            "    if registry_entry is None or source_id not in _SUPPORTED_GROUNDING_SOURCE_IDS:\n",
            "    if registry_entry is None:\n",
        )
        with self.assertRaisesRegex(AssertionError, "source-id"):
            contract_guard._py_ai_supported_source_ids_rejection(
                source_id_drift,
                ai_grounding_validation,
            )

        provenance_drift = source.replace(
            '        "custody_reference": expected_custody_reference,\n',
            "",
        )
        with self.assertRaisesRegex(AssertionError, "provenance binding"):
            contract_guard._py_ai_provenance_binding_rules(provenance_drift)

        metadata_format_drift = source.replace(
            "        or _SHA256_DIGEST_PATTERN.fullmatch(response_digest) is None\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "response-digest format"):
            contract_guard._py_ai_metadata_format_rules(metadata_format_drift)

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

    def test_ai_authority_posture_and_reason_vocabulary_are_enforced(self) -> None:
        from aegisops.control_plane.assistant import ai_grounding_validation

        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            contract_guard._ai_subordinate_authority_posture_rejection(source),
            "subordinate_evidence_context_only",
        )
        self.assertEqual(
            contract_guard._py_ai_enforced_reason_sets(
                source,
                ai_grounding_validation,
            )["unavailable_reasons"],
            ai_grounding_validation._ALLOWED_UNAVAILABLE_REASONS,
        )

        provenance_authority_drift = source.replace(
            "        if provenance.get(\"authority_posture\") != _SUBORDINATE_AUTHORITY_POSTURE:\n"
            "            reasons.append(\"grounding_authority_promotion_attempt\")\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "AI authority posture"):
            contract_guard._ai_subordinate_authority_posture_rejection(
                provenance_authority_drift,
            )

        missing_reason_call_drift = source.replace(
            "    reasons.extend(_unsupported_projection_reason_reasons(projection))\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "reason vocabulary"):
            contract_guard._py_ai_enforced_reason_sets(
                missing_reason_call_drift,
                ai_grounding_validation,
            )

        reason_constant_drift = source.replace(
            "    if any(\n"
            "        reason not in _ALLOWED_UNAVAILABLE_REASONS\n"
            "        for reason in unavailable_reasons\n"
            "    ):\n"
            "        return (\"unsupported_grounding_reason\",)\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "reason vocabulary"):
            contract_guard._py_ai_enforced_reason_sets(
                reason_constant_drift,
                ai_grounding_validation,
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

    def test_ai_freshness_recomputation_enforcement_is_parsed(self) -> None:
        from aegisops.control_plane.evidence import (
            evidence_freshness_provenance_projection,
        )

        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
        self.assertEqual(
            _py_ai_enforced_freshness_window_milliseconds(
                source,
                "PT6H",
                evidence_freshness_provenance_projection,
            ),
            21600000,
        )

        missing_call_drift = source.replace(
            "    reasons.extend(\n"
            "        _freshness_recomputation_reasons(\n"
            "            projection,\n"
            "            grounded_at,\n"
            "            expected_collection_timestamp,\n"
            "        )\n"
            "    )\n",
            "",
        )
        with self.assertRaisesRegex(AssertionError, "freshness recomputation"):
            _py_ai_enforced_freshness_window_milliseconds(
                missing_call_drift,
                "PT6H",
                evidence_freshness_provenance_projection,
            )

        missing_registry_window_drift = source.replace(
            "_parse_duration_seconds(registry_entry.freshness_window)",
            '_parse_duration_seconds("PT6H")',
        )
        with self.assertRaisesRegex(AssertionError, "freshness recomputation"):
            _py_ai_enforced_freshness_window_milliseconds(
                missing_registry_window_drift,
                "PT6H",
                evidence_freshness_provenance_projection,
            )

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

        source = AI_GROUNDING_VALIDATOR.read_text(encoding="utf-8")
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

        scanner_call_drift = source.replace(
            "            if _scan_for_authority_claim(\n"
            "                scan_value\n"
            "            ) or _scan_for_endpoint_command_language(scan_value):\n",
            "            if _scan_for_endpoint_command_language(scan_value):\n",
        )
        with self.assertRaisesRegex(AssertionError, "authority-scan enforcement"):
            contract_guard._py_ai_authority_truth_denials(
                scanner_call_drift,
                ai_grounding_validation,
            )

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
