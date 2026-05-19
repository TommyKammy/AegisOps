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

    def test_registry_rejects_broad_and_deferred_sources(self) -> None:
        cases = {
            "velociraptor": "Velociraptor",
            "yara": "YARA",
            "capa": "capa",
            "misp_breadth": "MISP breadth",
            "suricata": "Suricata",
            "intelowl": "IntelOwl breadth",
            "default_source_list": "default evidence source list",
            "marketplace": "evidence source marketplace",
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
            "release gates own readiness",
            "gate release",
            "activate detectors",
            "claim readiness",
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

    def test_review_thread_workflow_truth_terms_fail_closed_after_normalization(
        self,
    ) -> None:
        cases = {
            "alert_truth": "alert_truth",
            "release_truth": "release-truth",
            "gate_truth": "Gate Truth",
            "closeout_truth": "closeout_truth",
            "readiness_truth": "readiness truth",
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


if __name__ == "__main__":
    unittest.main()
