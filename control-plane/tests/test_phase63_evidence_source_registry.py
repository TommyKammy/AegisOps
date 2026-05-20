from __future__ import annotations

import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.evidence.evidence_source_registry import (  # noqa: E402
    PHASE63_EVIDENCE_SOURCE_REGISTRY,
    validate_phase63_evidence_source_entry,
    validate_phase63_evidence_source_registry,
    validate_phase63_evidence_source_use,
)


class Phase63EvidenceSourceRegistryTests(unittest.TestCase):
    def _valid_osquery_entry(self) -> dict[str, object]:
        return {
            "source_id": "osquery_host_state",
            "source_type": "osquery",
            "owner": "IT Operations, Information Systems Department",
            "allowed_target_class": "explicitly_bound_host",
            "custody_requirements": (
                "reviewed query id, operator or automation attribution, "
                "collection timestamp, host binding, and AegisOps evidence record id"
            ),
            "freshness_window": "PT24H",
            "confidence_posture": "observed_host_state_subordinate_context",
            "status": "enabled",
            "degraded_states": ("missing_host_binding", "stale_collection"),
            "disabled_states": ("disabled_by_policy", "missing_custody"),
            "authority_posture": "subordinate_evidence_context_only",
        }

    def test_registry_contains_osquery_and_one_bounded_enrichment_source(self) -> None:
        self.assertEqual(
            set(PHASE63_EVIDENCE_SOURCE_REGISTRY),
            {"osquery_host_state", "malwarebazaar_hash_reputation"},
        )
        self.assertEqual(
            {
                entry.source_type
                for entry in PHASE63_EVIDENCE_SOURCE_REGISTRY.values()
            },
            {"osquery", "malwarebazaar_hash_reputation"},
        )
        for entry in PHASE63_EVIDENCE_SOURCE_REGISTRY.values():
            self.assertEqual(entry.authority_posture, "subordinate_evidence_context_only")
            self.assertEqual(entry.status, "enabled")
            self.assertTrue(entry.owner)
            self.assertTrue(entry.custody_requirements)
            self.assertTrue(entry.freshness_window)

    def test_entry_validation_rejects_required_field_gaps(self) -> None:
        cases = {
            "missing_owner": ({"owner": ""}, "missing_owner"),
            "missing_freshness": ({"freshness_window": ""}, "missing_freshness_window"),
            "missing_custody": (
                {"custody_requirements": ""},
                "missing_custody_requirements",
            ),
            "missing_target": (
                {"allowed_target_class": ""},
                "missing_allowed_target_class",
            ),
        }
        for label, (override, expected_error) in cases.items():
            with self.subTest(label=label):
                errors = validate_phase63_evidence_source_entry(
                    {**self._valid_osquery_entry(), **override}
                )
                self.assertIn(expected_error, errors)

    def test_review_thread_activated_detector_variants_fail_closed(
        self,
    ) -> None:
        cases = (
            (
                "owner_activated_detector",
                {"owner": "activated detector"},
                "owner_promotes_workflow_authority",
            ),
            (
                "owner_detector_activation",
                {"owner": "detector activation"},
                "owner_promotes_workflow_authority",
            ),
            (
                "custody_detector_activated",
                {"custody_requirements": "detector activated"},
                "custody_requirements_promote_workflow_authority",
            ),
            (
                "custody_activate_a_detector",
                {"custody_requirements": "activate a detector"},
                "custody_requirements_promote_workflow_authority",
            ),
            (
                "custody_activate_the_detector",
                {"custody_requirements": "activate the detector"},
                "custody_requirements_promote_workflow_authority",
            ),
        )
        for label, override, expected_error in cases:
            with self.subTest(label=label):
                entry = {**self._valid_osquery_entry(), **override}
                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )

                self.assertIn(expected_error, entry_errors)
                self.assertIn(expected_error, use_errors)

    def test_review_thread_approval_and_alert_admission_variants_fail_closed(
        self,
    ) -> None:
        cases = (
            (
                "owner_approving_cases",
                {"owner": "approving cases"},
                "owner_promotes_workflow_authority",
            ),
            (
                "owner_may_admit_alerts",
                {"owner": "may admit alerts"},
                "owner_promotes_workflow_authority",
            ),
            (
                "owner_approvals",
                {"owner": "approvals owner"},
                "owner_promotes_workflow_authority",
            ),
            (
                "owner_action_requests",
                {"owner": "action requests owner"},
                "owner_promotes_workflow_authority",
            ),
            (
                "owner_evidence_requests",
                {"owner": "evidence requests owner"},
                "owner_promotes_workflow_authority",
            ),
            (
                "confidence_admit_alert",
                {"confidence_posture": "admit alert"},
                "confidence_posture_promotes_workflow_authority",
            ),
            (
                "custody_alert_admission",
                {"custody_requirements": "alert admission"},
                "custody_requirements_promote_workflow_authority",
            ),
        )
        for label, override, expected_error in cases:
            with self.subTest(label=label):
                entry = {**self._valid_osquery_entry(), **override}
                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )

                self.assertIn(expected_error, entry_errors)
                self.assertIn(expected_error, use_errors)

    def test_review_thread_past_tense_authority_verbs_fail_closed(
        self,
    ) -> None:
        cases = (
            (
                "owner_executed_workflows",
                {"owner": "executed workflows"},
                "owner_promotes_workflow_authority",
            ),
            (
                "owner_reconciled_cases",
                {"owner": "reconciled cases"},
                "owner_promotes_workflow_authority",
            ),
            (
                "owner_closed_records",
                {"owner": "closed records"},
                "owner_promotes_workflow_authority",
            ),
        )
        for label, override, expected_error in cases:
            with self.subTest(label=label):
                entry = {**self._valid_osquery_entry(), **override}
                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )

                self.assertIn(expected_error, entry_errors)
                self.assertIn(expected_error, use_errors)

    def test_review_thread_record_owner_authority_claims_fail_closed(
        self,
    ) -> None:
        cases = (
            (
                "custody_case_owner",
                {
                    "custody_requirements": (
                        self._valid_osquery_entry()["custody_requirements"]
                        + ", case owner"
                    )
                },
                "custody_requirements_promote_workflow_authority",
            ),
            (
                "custody_audit_owner",
                {
                    "custody_requirements": (
                        self._valid_osquery_entry()["custody_requirements"]
                        + ", audit owner"
                    )
                },
                "custody_requirements_promote_workflow_authority",
            ),
            (
                "custody_release_owner",
                {
                    "custody_requirements": (
                        self._valid_osquery_entry()["custody_requirements"]
                        + ", release owner"
                    )
                },
                "custody_requirements_promote_workflow_authority",
            ),
        )
        for label, override, expected_error in cases:
            with self.subTest(label=label):
                entry = {**self._valid_osquery_entry(), **override}
                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )

                self.assertIn(expected_error, entry_errors)
                self.assertIn(expected_error, use_errors)

    def test_registry_rejects_broad_and_deferred_sources(self) -> None:
        cases = {
            "velociraptor": "Velociraptor",
            "yara": "YARA",
            "capa": "capa",
            "misp": "MISP",
            "misp_breadth": "MISP breadth",
            "suricata": "Suricata",
            "intelowl_bare": "IntelOwl",
            "intelowl": "IntelOwl breadth",
            "default_source_list": "default evidence source list",
            "marketplace": "evidence source marketplace",
            "marketplaces": "evidence source marketplaces",
            "public_pivots": "public internet pivots",
        }
        for label, source_type in cases.items():
            with self.subTest(label=label):
                errors = validate_phase63_evidence_source_entry(
                    {
                        **self._valid_osquery_entry(),
                        "source_id": f"{label}_source",
                        "source_type": source_type,
                    }
                )
                self.assertIn("unsupported_source_type", errors)

    def test_disabled_and_degraded_source_use_fails_closed(self) -> None:
        self.assertIn(
            "source_disabled",
            validate_phase63_evidence_source_use(
                {**self._valid_osquery_entry(), "status": "disabled"},
                target_class="explicitly_bound_host",
            ),
        )
        self.assertIn(
            "source_degraded",
            validate_phase63_evidence_source_use(
                {**self._valid_osquery_entry(), "status": "degraded"},
                target_class="explicitly_bound_host",
            ),
        )
        self.assertIn(
            "target_class_not_allowed",
            validate_phase63_evidence_source_use(
                self._valid_osquery_entry(),
                target_class="case_truth",
            ),
        )

    def test_authority_boundary_claims_are_rejected(self) -> None:
        for authority_posture in (
            "authoritative_workflow_truth",
            "approves_cases",
            "execution_receipt_truth",
            "reconciliation_truth",
            "detector_activation_truth",
            "release_gate_truth",
        ):
            with self.subTest(authority_posture=authority_posture):
                errors = validate_phase63_evidence_source_entry(
                    {
                        **self._valid_osquery_entry(),
                        "authority_posture": authority_posture,
                    }
                )
                self.assertIn("authority_posture_not_subordinate", errors)

    def test_authority_boundary_terms_are_rejected_in_entry_text(self) -> None:
        for prohibited_claim in (
            "alert_truth",
            "release_truth",
            "gate_truth",
            "closeout_truth",
            "readiness_truth",
            "closeout-state-truth",
            "Readiness Truth",
            "evidence_request_truth",
            "audit_truth",
            "limitation_truth",
            "workflow authority",
            "admitted alert workflow owner",
            "evidence request owner",
            "action request owner",
            "execution receipt owner",
            "execution receipts owner",
            "may execute workflows",
            "can reconcile cases",
            "reconciliation owner",
            "reconciliation ownership",
            "may close records",
            "release gates own readiness",
            "gate release",
            "limitations owner",
            "activate detectors",
            "activated detector",
            "detector activated",
            "detector activation",
            "claim readiness",
            "claims readiness",
            "claimed readiness",
            "readiness claimed",
            "a.p.p.r.o.v.a.l owner",
            "c.a.s.e truth",
            "e.x.e.c.u.t.e workflows",
        ):
            with self.subTest(prohibited_claim=prohibited_claim):
                errors = validate_phase63_evidence_source_entry(
                    {
                        **self._valid_osquery_entry(),
                        "confidence_posture": prohibited_claim,
                    }
                )
                self.assertIn("confidence_posture_promotes_workflow_authority", errors)

                custody_errors = validate_phase63_evidence_source_entry(
                    {
                        **self._valid_osquery_entry(),
                        "custody_requirements": prohibited_claim,
                    }
                )
                self.assertIn(
                    "custody_requirements_promote_workflow_authority",
                    custody_errors,
                )

    def test_authority_boundary_terms_require_word_boundaries(self) -> None:
        entry = {
            **self._valid_osquery_entry(),
            "custody_requirements": (
                self._valid_osquery_entry()["custody_requirements"]
                + ", enclosed support bundle reference"
            ),
        }

        self.assertEqual(validate_phase63_evidence_source_entry(entry), ())

    def test_authority_boundary_terms_are_rejected_in_all_registry_fields(
        self,
    ) -> None:
        cases = {
            "source_id": (
                {"source_id": "alert_truth_source"},
                "source_id_promotes_workflow_authority",
            ),
            "source_type": (
                {"source_type": "approval_truth"},
                "source_type_promotes_workflow_authority",
            ),
            "owner": (
                {"owner": "release_truth_owner"},
                "owner_promotes_workflow_authority",
            ),
            "allowed_target_class": (
                {"allowed_target_class": "case_truth"},
                "allowed_target_class_promotes_workflow_authority",
            ),
            "freshness_window": (
                {"freshness_window": "readiness_truth"},
                "freshness_window_promotes_workflow_authority",
            ),
            "status": (
                {"status": "approval_truth"},
                "status_promotes_workflow_authority",
            ),
            "degraded_states": (
                {"degraded_states": ("approval_truth",)},
                "degraded_states_promotes_workflow_authority",
            ),
            "disabled_states": (
                {"disabled_states": ("case_truth",)},
                "disabled_states_promotes_workflow_authority",
            ),
            "authority_posture": (
                {"authority_posture": "workflow authority"},
                "authority_posture_promotes_workflow_authority",
            ),
        }
        for label, (override, expected_error) in cases.items():
            with self.subTest(label=label):
                errors = validate_phase63_evidence_source_entry(
                    {**self._valid_osquery_entry(), **override}
                )
                self.assertIn(expected_error, errors)

    def test_unknown_mapping_fields_fail_closed_before_coercion(self) -> None:
        errors = validate_phase63_evidence_source_entry(
            {
                **self._valid_osquery_entry(),
                "additional_sources": ["Velociraptor"],
                "workflow_authority": "approval_truth",
            }
        )

        self.assertIn("unknown_registry_entry_field", errors)

    def test_source_use_validates_mapping_fields_before_coercion(self) -> None:
        errors = validate_phase63_evidence_source_use(
            {
                **self._valid_osquery_entry(),
                "additional_sources": ["Velociraptor"],
                "workflow_authority": "approval_truth",
            },
            target_class="explicitly_bound_host",
        )

        self.assertIn("unknown_registry_entry_field", errors)

    def test_mapping_state_lists_reject_mapping_values_before_coercion(self) -> None:
        cases = {
            "degraded_states": (
                {
                    "degraded_states": {
                        "missing_host_binding": "approval_truth",
                        "stale_collection": "Velociraptor",
                    }
                },
                "degraded_states_not_sequence",
            ),
            "disabled_states": (
                {
                    "disabled_states": {
                        "disabled_by_policy": "case_truth",
                        "missing_custody": "MISP",
                    }
                },
                "disabled_states_not_sequence",
            ),
        }
        for label, (override, expected_error) in cases.items():
            with self.subTest(label=label):
                entry = {**self._valid_osquery_entry(), **override}
                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )

                self.assertIn(expected_error, entry_errors)
                self.assertIn(expected_error, use_errors)

    def test_required_state_lists_compare_without_order_dependence(self) -> None:
        entry = {
            **self._valid_osquery_entry(),
            "degraded_states": ("stale_collection", "missing_host_binding"),
            "disabled_states": ("missing_custody", "disabled_by_policy"),
        }

        self.assertEqual(validate_phase63_evidence_source_entry(entry), ())
        self.assertEqual(
            validate_phase63_evidence_source_use(
                entry,
                target_class="explicitly_bound_host",
            ),
            (),
        )

    def test_required_state_lists_reject_duplicate_bounded_states(self) -> None:
        cases = {
            "degraded_states": (
                {
                    "degraded_states": (
                        "missing_host_binding",
                        "stale_collection",
                        "stale_collection",
                    )
                },
                "source_identity_degraded_states_mismatch",
            ),
            "disabled_states": (
                {
                    "disabled_states": (
                        "disabled_by_policy",
                        "missing_custody",
                        "missing_custody",
                    )
                },
                "source_identity_disabled_states_mismatch",
            ),
        }
        for label, (override, expected_error) in cases.items():
            with self.subTest(label=label):
                errors = validate_phase63_evidence_source_entry(
                    {**self._valid_osquery_entry(), **override}
                )

                self.assertIn(expected_error, errors)

    def test_broad_sources_are_rejected_in_known_entry_fields(self) -> None:
        cases = {
            "source_id": {"source_id": "MISP"},
            "source_type": {"source_type": "IntelOwl"},
            "custody": {
                "custody_requirements": (
                    self._valid_osquery_entry()["custody_requirements"]
                    + ", Velociraptor flow id"
                )
            },
            "confidence": {"confidence_posture": "YARA match subordinate context"},
            "default_sources": {"confidence_posture": "default evidence source lists"},
            "marketplaces": {"confidence_posture": "evidence source marketplaces"},
            "public_pivots": {"confidence_posture": "public internet pivots"},
            "owner": {"owner": "MISP enrichment owner"},
            "degraded": {"degraded_states": ("Suricata alert linked",)},
            "disabled": {"disabled_states": ("IntelOwl lookup missing",)},
        }
        for label, override in cases.items():
            with self.subTest(label=label):
                errors = validate_phase63_evidence_source_entry(
                    {**self._valid_osquery_entry(), **override}
                )
                self.assertIn("unsupported_broad_source_reference", errors)

    def test_review_thread_bare_misp_and_intelowl_claims_fail_closed(
        self,
    ) -> None:
        cases = (
            ("bare_misp_owner", {"owner": "MISP"}),
            ("bare_misp_custody", {"custody_requirements": "MISP"}),
            ("bare_intelowl_owner", {"owner": "IntelOwl"}),
            ("bare_intelowl_disabled_state", {"disabled_states": ("IntelOwl",)}),
        )
        for label, override in cases:
            with self.subTest(label=label):
                entry = {**self._valid_osquery_entry(), **override}
                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )

                self.assertIn("unsupported_broad_source_reference", entry_errors)
                self.assertIn("unsupported_broad_source_reference", use_errors)

    def test_review_thread_punctuated_broad_source_claims_fail_closed(
        self,
    ) -> None:
        cases = (
            ("punctuated_misp", {"owner": "M.I.S.P. enrichment owner"}),
            ("punctuated_yara", {"confidence_posture": "Y.A.R.A match"}),
            ("punctuated_capa", {"custody_requirements": "C.A.P.A output"}),
            ("punctuated_intelowl", {"disabled_states": ("Intel.Owl lookup",)}),
            ("fully_punctuated_suricata", {"custody_requirements": "S.U.R.I.C.A.T.A"}),
            (
                "fully_punctuated_velociraptor",
                {"confidence_posture": "V.E.L.O.C.I.R.A.P.T.O.R context"},
            ),
            ("fully_punctuated_intelowl", {"owner": "I.N.T.E.L.O.W.L"}),
        )
        for label, override in cases:
            with self.subTest(label=label):
                entry = {**self._valid_osquery_entry(), **override}
                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )

                self.assertIn("unsupported_broad_source_reference", entry_errors)
                self.assertIn("unsupported_broad_source_reference", use_errors)

    def test_osquery_custody_requires_operator_or_automation_attribution(
        self,
    ) -> None:
        entry = {
            **self._valid_osquery_entry(),
            "custody_requirements": (
                "reviewed query id, collection timestamp, host binding, "
                "and AegisOps evidence record id"
            ),
        }

        for label, errors in (
            ("entry", validate_phase63_evidence_source_entry(entry)),
            (
                "source_use",
                validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                ),
            ),
            (
                "registry",
                validate_phase63_evidence_source_registry(
                    {
                        "osquery_host_state": entry,
                        "malwarebazaar_hash_reputation": (
                            PHASE63_EVIDENCE_SOURCE_REGISTRY[
                                "malwarebazaar_hash_reputation"
                            ]
                        ),
                    }
                ),
            ),
        ):
            with self.subTest(label=label):
                self.assertIn("source_identity_custody_requirements_mismatch", errors)

    def test_unreviewed_custody_terms_do_not_satisfy_reviewed_requirements(
        self,
    ) -> None:
        cases = {
            "osquery": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "unreviewed query id, operator or automation attribution, "
                    "collection timestamp, host binding, "
                    "and AegisOps evidence record id"
                ),
            },
            "malwarebazaar": {
                **PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ].as_dict(),
                "custody_requirements": (
                    "unreviewed file hash, enrichment request id, collection timestamp, "
                    "response digest, and AegisOps evidence record id"
                ),
            },
        }
        for label, entry in cases.items():
            with self.subTest(label=label):
                errors = validate_phase63_evidence_source_entry(entry)
                self.assertIn(
                    "source_identity_custody_requirements_mismatch", errors
                )

    def test_negated_reviewed_custody_terms_do_not_satisfy_requirements(
        self,
    ) -> None:
        cases = {
            "osquery_not_reviewed": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "not reviewed query id, operator or automation attribution, "
                    "collection timestamp, host binding, "
                    "and AegisOps evidence record id"
                ),
            },
            "malwarebazaar_not_reviewed": {
                **PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ].as_dict(),
                "custody_requirements": (
                    "not reviewed file hash, enrichment request id, "
                    "collection timestamp, response digest, "
                    "and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_missing": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id missing, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "malwarebazaar_reviewed_term_absent": {
                **PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ].as_dict(),
                "custody_requirements": (
                    "reviewed file hash absent, enrichment request id, "
                    "collection timestamp, response digest, "
                    "and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_is_missing": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id is missing, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_is_not_available": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id is not available, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_is_not_verified": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id is not verified, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_not_reviewed": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id not reviewed, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_isnt_available": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id isn't available, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "osquery_missing_the_reviewed_term": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "missing the reviewed query id, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "malwarebazaar_without_the_reviewed_term": {
                **PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ].as_dict(),
                "custody_requirements": (
                    "without the reviewed file hash, enrichment request id, "
                    "collection timestamp, response digest, "
                    "and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_is_no_longer_available": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id is no longer available, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "malwarebazaar_reviewed_term_is_absent": {
                **PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ].as_dict(),
                "custody_requirements": (
                    "reviewed file hash is absent, enrichment request id, "
                    "collection timestamp, response digest, "
                    "and AegisOps evidence record id"
                ),
            },
            "osquery_missing_reviewed_term": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "missing reviewed query id, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "malwarebazaar_without_any_reviewed_term": {
                **PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ].as_dict(),
                "custody_requirements": (
                    "without any reviewed file hash, enrichment request id, "
                    "collection timestamp, response digest, "
                    "and AegisOps evidence record id"
                ),
            },
            "osquery_not_yet_reviewed_term": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "not yet reviewed query id, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_is_currently_unavailable": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id is currently unavailable, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
            "osquery_reviewed_term_is_no_longer_verified": {
                **self._valid_osquery_entry(),
                "custody_requirements": (
                    "reviewed query id is no longer verified, "
                    "operator or automation attribution, collection timestamp, "
                    "host binding, and AegisOps evidence record id"
                ),
            },
        }
        for label, entry in cases.items():
            with self.subTest(label=label):
                errors = validate_phase63_evidence_source_entry(entry)
                self.assertIn(
                    "source_identity_custody_requirements_mismatch", errors
                )

    def test_review_thread_owner_must_match_reviewed_profile_value(self) -> None:
        entry = {
            **self._valid_osquery_entry(),
            "owner": "Unreviewed External Team",
        }

        entry_errors = validate_phase63_evidence_source_entry(entry)
        use_errors = validate_phase63_evidence_source_use(
            entry,
            target_class="explicitly_bound_host",
        )
        registry_errors = validate_phase63_evidence_source_registry(
            {
                "osquery_host_state": entry,
                "malwarebazaar_hash_reputation": PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ],
            }
        )

        self.assertIn("source_identity_owner_mismatch", entry_errors)
        self.assertIn("source_identity_owner_mismatch", use_errors)
        self.assertIn("registry_key_owner_mismatch", registry_errors)

    def test_mapping_without_authority_posture_uses_subordinate_default(
        self,
    ) -> None:
        entry = self._valid_osquery_entry()
        entry.pop("authority_posture")

        self.assertEqual(validate_phase63_evidence_source_entry(entry), ())

    def test_review_thread_source_identity_values_reject_whitespace_drift(
        self,
    ) -> None:
        cases = {
            "source_id": (
                {"source_id": " osquery_host_state "},
                "source_id_whitespace_drift",
            ),
            "source_type": (
                {"source_type": " osquery "},
                "source_type_whitespace_drift",
            ),
        }
        for label, (override, expected_error) in cases.items():
            with self.subTest(label=label):
                entry = {**self._valid_osquery_entry(), **override}
                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )
                registry_errors = validate_phase63_evidence_source_registry(
                    {
                        "osquery_host_state": entry,
                        "malwarebazaar_hash_reputation": (
                            PHASE63_EVIDENCE_SOURCE_REGISTRY[
                                "malwarebazaar_hash_reputation"
                            ]
                        ),
                    }
                )

                self.assertIn(expected_error, entry_errors)
                self.assertIn(expected_error, use_errors)
                self.assertIn(expected_error, registry_errors)

    def test_review_thread_workflow_truth_terms_fail_closed_after_normalization(
        self,
    ) -> None:
        cases = {
            "alert_truth": "alert_truth",
            "release_truth": "release-truth",
            "gate_truth": "Gate Truth",
            "closeout_truth": "closeout_truth",
            "readiness_truth": "readiness truth",
            "production_truth": "production_truth",
            "production truth": "production truth",
            "case_truth": "case.truth",
            "source_truth": "source/truth",
            "source_of_truth": "source of truth",
            "evidence_truth": "evidence:truth",
            "readiness_dot_truth": "readiness.truth",
        }
        for label, prohibited_claim in cases.items():
            with self.subTest(label=label):
                confidence_errors = validate_phase63_evidence_source_entry(
                    {
                        **self._valid_osquery_entry(),
                        "confidence_posture": prohibited_claim,
                    }
                )
                self.assertIn(
                    "confidence_posture_promotes_workflow_authority",
                    confidence_errors,
                )

                custody_errors = validate_phase63_evidence_source_entry(
                    {
                        **self._valid_osquery_entry(),
                        "custody_requirements": prohibited_claim,
                    }
                )
                self.assertIn(
                    "custody_requirements_promote_workflow_authority",
                    custody_errors,
                )

    def test_review_thread_production_truth_owner_examples_fail_closed(
        self,
    ) -> None:
        for owner in ("production_truth", "production truth"):
            with self.subTest(owner=owner):
                entry = {**self._valid_osquery_entry(), "owner": owner}

                entry_errors = validate_phase63_evidence_source_entry(entry)
                use_errors = validate_phase63_evidence_source_use(
                    entry,
                    target_class="explicitly_bound_host",
                )

                self.assertIn("owner_promotes_workflow_authority", entry_errors)
                self.assertIn("owner_promotes_workflow_authority", use_errors)

    def test_malformed_freshness_windows_fail_closed(self) -> None:
        for freshness_window in ("PT", "PTbananas", "PT-6H", "P1D", "PT0H"):
            with self.subTest(freshness_window=freshness_window):
                errors = validate_phase63_evidence_source_entry(
                    {
                        **self._valid_osquery_entry(),
                        "freshness_window": freshness_window,
                    }
                )
                self.assertIn("freshness_window_not_duration", errors)

    def test_registry_rejects_swapped_source_identity_pairings(self) -> None:
        malware_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[
            "malwarebazaar_hash_reputation"
        ].as_dict()
        osquery_entry = self._valid_osquery_entry()

        errors = validate_phase63_evidence_source_registry(
            [
                {
                    **osquery_entry,
                    "source_type": malware_entry["source_type"],
                    "allowed_target_class": malware_entry["allowed_target_class"],
                    "freshness_window": malware_entry["freshness_window"],
                },
                {
                    **malware_entry,
                    "source_type": osquery_entry["source_type"],
                    "allowed_target_class": osquery_entry["allowed_target_class"],
                    "freshness_window": osquery_entry["freshness_window"],
                },
            ]
        )

        self.assertIn("source_identity_type_mismatch", errors)
        self.assertIn("source_identity_target_class_mismatch", errors)
        self.assertIn("source_identity_freshness_window_mismatch", errors)

    def test_registry_rejects_swapped_source_confidence_and_states(self) -> None:
        malware_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[
            "malwarebazaar_hash_reputation"
        ].as_dict()
        osquery_entry = self._valid_osquery_entry()

        errors = validate_phase63_evidence_source_registry(
            {
                "osquery_host_state": {
                    **osquery_entry,
                    "confidence_posture": malware_entry["confidence_posture"],
                    "degraded_states": malware_entry["degraded_states"],
                    "disabled_states": malware_entry["disabled_states"],
                },
                "malwarebazaar_hash_reputation": {
                    **malware_entry,
                    "confidence_posture": osquery_entry["confidence_posture"],
                    "degraded_states": osquery_entry["degraded_states"],
                    "disabled_states": osquery_entry["disabled_states"],
                },
            }
        )

        self.assertIn("source_identity_confidence_posture_mismatch", errors)
        self.assertIn("source_identity_degraded_states_mismatch", errors)
        self.assertIn("source_identity_disabled_states_mismatch", errors)
        self.assertIn("registry_key_confidence_posture_mismatch", errors)
        self.assertIn("registry_key_degraded_states_mismatch", errors)
        self.assertIn("registry_key_disabled_states_mismatch", errors)

    def test_entry_and_source_use_reject_swapped_confidence_and_states(
        self,
    ) -> None:
        malware_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[
            "malwarebazaar_hash_reputation"
        ].as_dict()
        entry = {
            **self._valid_osquery_entry(),
            "confidence_posture": malware_entry["confidence_posture"],
            "degraded_states": malware_entry["degraded_states"],
            "disabled_states": malware_entry["disabled_states"],
        }

        entry_errors = validate_phase63_evidence_source_entry(entry)
        use_errors = validate_phase63_evidence_source_use(
            entry,
            target_class="explicitly_bound_host",
        )

        for errors in (entry_errors, use_errors):
            self.assertIn("source_identity_confidence_posture_mismatch", errors)
            self.assertIn("source_identity_degraded_states_mismatch", errors)
            self.assertIn("source_identity_disabled_states_mismatch", errors)

    def test_registry_rejects_swapped_source_custody_requirements(self) -> None:
        malware_entry = PHASE63_EVIDENCE_SOURCE_REGISTRY[
            "malwarebazaar_hash_reputation"
        ].as_dict()
        osquery_entry = self._valid_osquery_entry()

        errors = validate_phase63_evidence_source_registry(
            {
                "osquery_host_state": {
                    **osquery_entry,
                    "custody_requirements": malware_entry["custody_requirements"],
                },
                "malwarebazaar_hash_reputation": {
                    **malware_entry,
                    "custody_requirements": osquery_entry["custody_requirements"],
                },
            }
        )

        self.assertIn("source_identity_custody_requirements_mismatch", errors)
        self.assertIn("registry_key_custody_requirements_mismatch", errors)

    def test_registry_accepts_exported_mapping_shape(self) -> None:
        self.assertEqual(
            validate_phase63_evidence_source_registry(
                PHASE63_EVIDENCE_SOURCE_REGISTRY
            ),
            (),
        )

    def test_registry_rejects_mapping_key_source_id_drift(self) -> None:
        errors = validate_phase63_evidence_source_registry(
            {
                "osquery_host_state": PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "osquery_host_state"
                ],
                "unexpected_hash_source": PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ],
            }
        )
        self.assertIn("registry_key_source_id_mismatch", errors)

    def test_registry_rejects_whitespace_drifted_mapping_keys(self) -> None:
        errors = validate_phase63_evidence_source_registry(
            {
                " osquery_host_state ": PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "osquery_host_state"
                ],
                " malwarebazaar_hash_reputation ": PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ],
            }
        )
        self.assertIn("registry_key_source_id_mismatch", errors)
        self.assertIn("registry_key_entry_source_id_mismatch", errors)

    def test_registry_rejects_mapping_key_entry_source_id_swaps(self) -> None:
        errors = validate_phase63_evidence_source_registry(
            {
                "osquery_host_state": PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "malwarebazaar_hash_reputation"
                ],
                "malwarebazaar_hash_reputation": PHASE63_EVIDENCE_SOURCE_REGISTRY[
                    "osquery_host_state"
                ],
            }
        )
        self.assertIn("registry_key_entry_source_id_mismatch", errors)
        self.assertIn("registry_key_source_type_mismatch", errors)
        self.assertIn("registry_key_target_class_mismatch", errors)
        self.assertIn("registry_key_freshness_window_mismatch", errors)
        self.assertIn("registry_key_confidence_posture_mismatch", errors)
        self.assertIn("registry_key_degraded_states_mismatch", errors)
        self.assertIn("registry_key_disabled_states_mismatch", errors)


if __name__ == "__main__":
    unittest.main()
