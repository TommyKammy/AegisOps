from __future__ import annotations

from datetime import datetime, timedelta, timezone
import pathlib
import sys
import unittest

TESTS_ROOT = pathlib.Path(__file__).resolve().parent
CONTROL_PLANE_ROOT = TESTS_ROOT.parent
if str(CONTROL_PLANE_ROOT) not in sys.path:
    sys.path.insert(0, str(CONTROL_PLANE_ROOT))

from aegisops.control_plane.actions.action_policy_registry import (  # noqa: E402
    PHASE62_ACTION_POLICIES,
    PHASE62_MANUAL_FALLBACK_REQUIREMENTS,
    PHASE62_SIMULATOR_CONTRACTS,
    PHASE62_SHUFFLE_WORKFLOW_MAPPINGS,
    evaluate_phase62_action_policy,
    validate_phase62_manual_fallback_record,
    validate_phase62_simulator_output,
    validate_phase62_shuffle_workflow_mapping,
)


class Phase62ActionPolicyRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.now = datetime(2026, 5, 17, 8, 30, tzinfo=timezone.utc)

    def _valid_simulator_output(
        self,
        catalog_action: str = "operator_notification",
    ) -> dict[str, object]:
        return {
            "mode": "demo",
            "catalog_action": catalog_action,
            "action_request_id": "action-request-phase62-sim-001",
            "simulation_run_id": "simulation-run-phase62-001",
            "reviewed_template_version": "operator_notification-v1-reviewed-2026-05-03",
            "correlation_id": "correlation-phase62-sim-001",
            "simulated_started_at": "2026-05-17T08:30:00Z",
            "simulated_finished_at": "2026-05-17T08:30:05Z",
            "simulated_status": "simulated_success",
            "demo_test_label": "demo/test evidence only",
            "production_exclusion": (
                "Simulator output is excluded from production execution receipt "
                "and reconciliation truth."
            ),
            "authority_posture": "non_authoritative_demo_test_evidence",
            "live_secret_ref": "not_used",
            "customer_data_classification": "synthetic_only",
            "simulated_evidence_ref": "synthetic-demo-evidence-001",
        }

    def test_registry_contains_reviewed_phase62_actions(self) -> None:
        self.assertEqual(
            set(PHASE62_ACTION_POLICIES),
            {
                "enrichment_only_lookup",
                "operator_notification",
                "manual_escalation_request",
                "create_tracking_ticket",
            },
        )
        self.assertEqual(
            PHASE62_ACTION_POLICIES["create_tracking_ticket"].registry_id,
            "phase62.2:create_tracking_ticket",
        )
        self.assertEqual(
            PHASE62_ACTION_POLICIES["create_tracking_ticket"].allowed_reviewer_roles,
            ("approver",),
        )
        for policy in PHASE62_ACTION_POLICIES.values():
            self.assertIn("correlation_id", policy.expected_receipt_fields)
            self.assertIn("expected_execution_receipt_id", policy.correlation_fields)
            self.assertEqual(
                policy.reconciliation_outcomes,
                (
                    "success",
                    "failure",
                    "missing",
                    "stale",
                    "mismatched",
                    "duplicate",
                    "wrong_correlation",
                    "manual_review",
                ),
            )

    def test_simulator_contract_covers_reviewed_actions_in_demo_test_mode_only(
        self,
    ) -> None:
        self.assertEqual(
            set(PHASE62_SIMULATOR_CONTRACTS),
            set(PHASE62_ACTION_POLICIES),
        )

        for action, contract in PHASE62_SIMULATOR_CONTRACTS.items():
            with self.subTest(action=action):
                self.assertEqual(contract.catalog_action, action)
                self.assertEqual(contract.allowed_modes, ("demo", "test"))
                self.assertEqual(
                    contract.authority_posture,
                    "non_authoritative_demo_test_evidence",
                )
                self.assertEqual(
                    contract.production_exclusion,
                    "excluded_from_production_execution_receipt_and_reconciliation_truth",
                )
                self.assertIn("demo_test_label", contract.required_output_fields)
                self.assertIn("production_exclusion", contract.required_output_fields)
                self.assertIn("authority_posture", contract.required_output_fields)

    def test_simulator_validation_accepts_labeled_demo_test_output(self) -> None:
        self.assertEqual(
            validate_phase62_simulator_output(
                catalog_action="operator_notification",
                output=self._valid_simulator_output(),
            ),
            (),
        )

        self.assertEqual(
            validate_phase62_simulator_output(
                catalog_action="operator_notification",
                output={**self._valid_simulator_output(), "mode": "test"},
            ),
            (),
        )

        self.assertEqual(
            validate_phase62_simulator_output(
                catalog_action="operator_notification",
                output={
                    **self._valid_simulator_output(),
                    "production_exclusion": (
                        "Simulator output excludes production execution receipt "
                        "and reconciliation truth."
                    ),
                },
            ),
            (),
        )

    def test_simulator_validation_rejects_production_truth_overclaims(self) -> None:
        cases = {
            "production_mode": ({"mode": "production"}, "unsupported_mode"),
            "missing_demo_label": ({"demo_test_label": ""}, "missing_demo_test_label"),
            "demo_label_production_truth": (
                {
                    "demo_test_label": (
                        "demo/test evidence only and production execution receipt truth"
                    ),
                },
                "demo_test_label_promotes_production_truth",
            ),
            "receipt_truth": (
                {
                    "production_exclusion": (
                        "Simulator output is production execution receipt truth."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "reconciliation_truth": (
                {
                    "production_exclusion": (
                        "Simulator state is production reconciliation truth."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "excluded_then_truth": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth. It is production reconciliation truth."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "excluded_preamble_then_truth": (
                {
                    "production_exclusion": (
                        "excluded from production execution receipt truth therefore "
                        "production reconciliation truth"
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "unrelated_exclusion": (
                {"production_exclusion": "excluded for audit cleanup"},
                "missing_production_exclusion",
            ),
            "case_closed": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "truth and case closed."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "ticket_closed": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "truth and ticket closed."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "production_workflow_delegation": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "truth and delegates production workflow launch."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "authoritative": (
                {"authority_posture": "authoritative_execution_receipt"},
                "authority_posture_mismatch",
            ),
            "live_secret": (
                {"live_secret_ref": "shuffle-prod-secret"},
                "live_secret_ref_forbidden",
            ),
            "customer_data": (
                {"customer_data_classification": "customer_private"},
                "customer_data_forbidden",
            ),
            "direct_execution": (
                {"simulated_status": "production_execution_success"},
                "unsupported_simulated_status",
            ),
            "catalog_mismatch": (
                {"catalog_action": "create_tracking_ticket"},
                "catalog_action_mismatch",
            ),
            "unsupported_action": (
                {"catalog_action": "disable_account"},
                "unsupported_action",
            ),
        }

        for label, (override, expected_error) in cases.items():
            with self.subTest(label=label):
                catalog_action = (
                    "disable_account"
                    if label == "unsupported_action"
                    else "operator_notification"
                )
                errors = validate_phase62_simulator_output(
                    catalog_action=catalog_action,
                    output={**self._valid_simulator_output(), **override},
                )
                self.assertIn(expected_error, errors)

    def test_simulator_validation_covers_unresolved_connector_thread_cluster(
        self,
    ) -> None:
        cases = {
            "PRRT_kwDOR2iDUc6Cr1WG": (
                {
                    "demo_test_label": (
                        "demo test evidence only; production execution receipt truth"
                    ),
                },
                "demo_test_label_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr4V3": (
                {"production_exclusion": "excluded for audit cleanup"},
                "missing_production_exclusion",
            ),
            "PRRT_kwDOR2iDUc6Cr4V5_case": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "truth and case closed."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr4V5_ticket": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "truth and ticket closed."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr4V7": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "truth and delegates production workflow launch."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
        }

        for thread_id, (override, expected_error) in cases.items():
            with self.subTest(thread_id=thread_id):
                errors = validate_phase62_simulator_output(
                    catalog_action="operator_notification",
                    output={**self._valid_simulator_output(), **override},
                )
                self.assertIn(expected_error, errors)

        self.assertEqual(
            validate_phase62_simulator_output(
                catalog_action="operator_notification",
                output={
                    **self._valid_simulator_output(),
                    "production_exclusion": (
                        "Simulator output excludes production execution receipt "
                        "and reconciliation truth."
                    ),
                },
            ),
            (),
        )

    def test_simulator_validation_covers_current_head_connector_followups(
        self,
    ) -> None:
        cases = {
            "PRRT_kwDOR2iDUc6Cr1WG_demo_label_production_truth": (
                {
                    "demo_test_label": (
                        "demo test evidence only; production execution receipt truth"
                    ),
                },
                "demo_test_label_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr4V5_case_closed": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and case closed."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr4V5_ticket_closed": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and ticket closed."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr4V7_delegates_production_workflow": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and delegates production workflow launch."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr6vQ_partial_exclusion": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution."
                    ),
                },
                "missing_production_exclusion",
            ),
            "PRRT_kwDOR2iDUc6Cr6vS_delegated": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and production workflow delegated."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr6vU_direct_ad_hoc": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and uses direct ad hoc execution."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr6vW_not_excluded": (
                {
                    "production_exclusion": (
                        "Simulator output is not excluded from production execution "
                        "receipt and reconciliation truth."
                    ),
                },
                "missing_production_exclusion",
            ),
            "PRRT_kwDOR2iDUc6Cr6vX_authoritative_truth": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and simulator state is authoritative truth."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr838_case_closure": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and case closure."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr838_ticket_closure": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and ticket closure."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr83__production_receipts": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and writes production receipts."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr83__production_reconciliation_state": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and sets production reconciliation state."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr84B_standalone_authority": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and simulator output has authority."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cr84E_ready_for_production": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and is ready for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6CsBlB_contract_default": (
                {
                    "production_exclusion": PHASE62_SIMULATOR_CONTRACTS[
                        "operator_notification"
                    ].production_exclusion,
                },
                None,
            ),
            "PRRT_kwDOR2iDUc6CsBlE_standalone_authoritative": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and simulator output is authoritative."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6CsBlF_delegation_of_production_workflow": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and delegation of production workflow."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6CsBlF_delegates_workflow_for_production": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and delegates workflow for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6CsBlH_launch_workflow_for_production": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and launch workflow for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6CsBlJ_execution_ad_hoc": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and execution ad hoc."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6CseaP_demo_label_non_authoritative": (
                {"demo_test_label": "demo/test non-authoritative evidence"},
                None,
            ),
            "PRRT_kwDOR2iDUc6CseaS_authoritatively": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and authoritatively confirms."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6CseaU_standalone_closure": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and closure."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6CseaV_non_authority": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and non-authority evidence."
                    ),
                },
                None,
            ),
            "PRRT_kwDOR2iDUc6CseaW_comma_after_excluded": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded, from production execution "
                        "receipt and reconciliation truth."
                    ),
                },
                None,
            ),
            "PRRT_kwDOR2iDUc6CseaW_comma_then_truth_claim": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded, this is production execution "
                        "receipt truth."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cskjz_launching_production_workflow": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and launching production workflow."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Cskj0_post_term_negated_launch": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth; production workflow launch is not used."
                    ),
                },
                None,
            ),
            "PRRT_kwDOR2iDUc6Cskj6_non_authoritatively_exclusion": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and non-authoritatively described."
                    ),
                },
                None,
            ),
            "PRRT_kwDOR2iDUc6Cskj6_non_authoritatively_label": (
                {"demo_test_label": "demo/test non-authoritatively described evidence"},
                None,
            ),
            "PRRT_kwDOR2iDUc6Cskj9_delegating_production_workflow": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and delegating production workflow."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Csn1__production_workflow_launched": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and production workflow launched."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Csn1__launched_production_workflow": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and launched production workflow."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Csn1__launched_workflow_for_production": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and launched workflow for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_workflow_delegation_with_filler": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and workflow is delegated for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_workflow_launch_with_filler": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and workflow was triggered for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_workflow_start_synonym": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and started production workflow."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_workflow_invoke_synonym": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and production workflow invoked."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_case_closure_with_filler": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and the case is now closing."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_ticket_closure_with_filler": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and the ticket is already closed."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_receipt_generated_for_production": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and receipt generated for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_reconciliation_state_set_for_production": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and reconciliation state set for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Css0x_production_receipt_generated": (
                {
                    "production_exclusion": (
                        "Simulator output excludes production execution receipt "
                        "and reconciliation truth and production receipt generated."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Css00_case_closing": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and case closing."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Css04_workflow_delegating_for_production": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and workflow delegating for production."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "PRRT_kwDOR2iDUc6Css06_production_readied": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth and production readied."
                    ),
                },
                "production_exclusion_promotes_production_truth",
            ),
            "root_cause_negated_workflow_launch_with_filler": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth; workflow was triggered for production "
                        "is not the simulator claim."
                    ),
                },
                None,
            ),
            "root_cause_negated_receipt_generation_with_filler": (
                {
                    "production_exclusion": (
                        "Simulator output is excluded from production execution receipt "
                        "and reconciliation truth; receipt generated for production "
                        "is not part of the simulator output."
                    ),
                },
                None,
            ),
        }

        for thread_id, (override, expected_error) in cases.items():
            with self.subTest(thread_id=thread_id):
                errors = validate_phase62_simulator_output(
                    catalog_action="operator_notification",
                    output={**self._valid_simulator_output(), **override},
                )
                if expected_error is None:
                    self.assertEqual(errors, ())
                else:
                    self.assertIn(expected_error, errors)

    def test_manual_fallback_requirements_cover_every_reviewed_action(self) -> None:
        self.assertEqual(
            set(PHASE62_MANUAL_FALLBACK_REQUIREMENTS),
            set(PHASE62_ACTION_POLICIES),
        )

        for action, requirement in PHASE62_MANUAL_FALLBACK_REQUIREMENTS.items():
            self.assertEqual(requirement.catalog_action, action)
            self.assertEqual(requirement.affected_action, action)
            self.assertEqual(
                requirement.fallback_states,
                (
                    "shuffle_unavailable",
                    "execution_rejected",
                    "missing_receipt",
                    "stale_receipt",
                    "mismatched_receipt",
                ),
            )
            self.assertEqual(
                requirement.required_record_fields,
                (
                    "fallback_owner_id",
                    "operator_note",
                    "affected_action",
                    "fallback_state",
                    "blocked_reason",
                    "expected_evidence",
                    "follow_up_state",
                ),
            )
            self.assertEqual(requirement.manual_fallback_role, "subordinate_guidance")
            self.assertEqual(requirement.approval_bypass, "forbidden")
            self.assertEqual(requirement.execution_truth, "execution_receipt_required")
            self.assertEqual(
                requirement.reconciliation_truth,
                "aegisops_reconciliation_required",
            )

    def test_manual_fallback_validation_rejects_missing_and_authority_bypass_fields(
        self,
    ) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "shuffle_unavailable",
            "blocked_reason": "reviewed Shuffle route unavailable",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }
        blocked_reasons = {
            "shuffle_unavailable": "reviewed Shuffle route unavailable",
            "execution_rejected": "reviewed Shuffle execution rejected",
            "missing_receipt": "bound AegisOps execution receipt missing",
            "stale_receipt": "bound AegisOps execution receipt stale",
            "mismatched_receipt": "bound AegisOps execution receipt mismatched",
        }

        for fallback_state in (
            "shuffle_unavailable",
            "execution_rejected",
            "missing_receipt",
            "stale_receipt",
            "mismatched_receipt",
        ):
            with self.subTest(valid_fallback_state=fallback_state):
                self.assertEqual(
                    validate_phase62_manual_fallback_record(
                        catalog_action="operator_notification",
                        record={
                            **valid_record,
                            "fallback_state": fallback_state,
                            "blocked_reason": blocked_reasons[fallback_state],
                        },
                    ),
                    (),
                )

        cases = {
            "shuffle_unavailable": {"fallback_owner_id": ""},
            "execution_rejected": {"operator_note": ""},
            "missing_receipt": {"expected_evidence": ""},
            "stale_receipt": {"affected_action": "create_tracking_ticket"},
            "mismatched_receipt": {"fallback_state": "success"},
            "missing_operator_note": {
                "operator_note": "This note bypasses approval and proves execution.",
            },
            "operator_note_proves_receipt": {
                "operator_note": "Operator note proves receipt.",
            },
            "operator_note_proves_reconciliation": {
                "operator_note": "Operator note proves the reconciliation.",
            },
            "operator_note_confirms_execution": {
                "operator_note": "Operator note confirms execution.",
            },
            "operator_note_confirms_receipt": {
                "operator_note": "Operator note confirms receipt.",
            },
            "operator_note_validates_execution": {
                "operator_note": "Operator note validates execution.",
            },
            "operator_note_validates_reconciliation": {
                "operator_note": "Operator note validates reconciliation.",
            },
            "operator_note_execution_authority": {
                "operator_note": "Operator note is execution authority.",
            },
            "missing_follow_up_state": {"follow_up_state": ""},
            "fallback_as_reconciliation_truth": {
                "operator_note": "Operator note is reconciliation truth.",
            },
            "repeated_bypass_after_sentence_boundary": {
                "operator_note": "Manual fallback cannot bypass approval. bypass approval.",
            },
            "operator_note_bypasses_approval": {
                "operator_note": "Manual fallback bypasses approval.",
            },
            "operator_note_bypassed_approval": {
                "operator_note": "Manual fallback bypassed approval.",
            },
            "operator_note_confirmed_execution": {
                "operator_note": "Operator note confirmed execution.",
            },
            "operator_note_validated_receipt": {
                "operator_note": "Operator note validated receipt.",
            },
            "operator_note_closes_ticket": {
                "operator_note": "Manual fallback closes ticket.",
            },
            "operator_note_closes_case": {
                "operator_note": "Manual fallback closes case.",
            },
            "operator_note_closing_case": {
                "operator_note": "Manual fallback is closing the case.",
            },
            "operator_note_close_case": {
                "operator_note": "Manual fallback can close the case.",
            },
            "operator_note_close_case_exact": {
                "operator_note": "Manual fallback close case.",
            },
            "operator_note_closed_case": {
                "operator_note": "Manual fallback closed the case.",
            },
            "operator_note_closed_case_exact": {
                "operator_note": "Manual fallback closed case.",
            },
            "operator_note_case_closed": {
                "operator_note": "Manual fallback marks the case closed.",
            },
            "operator_note_ticket_closed": {
                "operator_note": "Manual fallback says ticket closed.",
            },
            "operator_note_ticket_closure": {
                "operator_note": "Manual fallback supplies ticket closure.",
            },
            "operator_note_closure_of_case": {
                "operator_note": "Manual fallback supplies closure of case.",
            },
            "operator_note_closure_of_ticket": {
                "operator_note": "Manual fallback supplies closure of ticket.",
            },
            "operator_note_execution_successful": {
                "operator_note": "Manual fallback marks execution successful.",
            },
            "operator_note_successful_execution": {
                "operator_note": "Manual fallback marks successful execution.",
            },
            "operator_note_receipt_confirmed": {
                "operator_note": "Manual fallback says receipt confirmed.",
            },
            "operator_note_execution_confirmed": {
                "operator_note": "Manual fallback says execution confirmed.",
            },
            "operator_note_receipt_validated": {
                "operator_note": "Manual fallback says receipt validated.",
            },
            "operator_note_confirm_execution": {
                "operator_note": "Manual fallback can confirm execution.",
            },
            "operator_note_prove_receipt": {
                "operator_note": "Manual fallback can prove receipt.",
            },
            "operator_note_reconciliation_validates": {
                "operator_note": "Manual fallback says reconciliation validates the action.",
            },
            "operator_note_confirming_execution": {
                "operator_note": "Manual fallback confirming execution.",
            },
            "operator_note_validating_receipt": {
                "operator_note": "Manual fallback validating receipt.",
            },
            "operator_note_proving_execution": {
                "operator_note": "Manual fallback proving execution.",
            },
            "operator_note_proven_execution": {
                "operator_note": "Manual fallback has proven execution.",
            },
            "operator_note_proof_of_execution": {
                "operator_note": "Manual fallback is proof of execution.",
            },
            "operator_note_confirmation_of_execution": {
                "operator_note": "Manual fallback is confirmation of execution.",
            },
            "operator_note_validation_of_receipt": {
                "operator_note": "Manual fallback is validation of receipt.",
            },
            "operator_note_not_only_bypasses_approval": {
                "operator_note": "Manual fallback not only bypasses approval.",
            },
            "operator_note_not_only_confirmed_execution": {
                "operator_note": "Manual fallback not only confirmed execution.",
            },
            "operator_note_closes_cases": {
                "operator_note": "Manual fallback closes cases.",
            },
            "operator_note_tickets_closed": {
                "operator_note": "Manual fallback marks tickets closed.",
            },
            "missing_receipt_without_receipt_context": {
                "fallback_state": "missing_receipt",
                "blocked_reason": "fallback owner missing from rotation",
            },
            "stale_receipt_without_receipt_context": {
                "fallback_state": "stale_receipt",
                "blocked_reason": "stale operator note present",
            },
            "mismatched_receipt_without_receipt_context": {
                "fallback_state": "mismatched_receipt",
                "blocked_reason": "mismatched owner roster entry",
            },
            "follow_up_state_completes": {
                "follow_up_state": "manual follow-up completes the action",
            },
            "follow_up_state_reconciles": {
                "follow_up_state": "manual follow-up reconciles the action",
            },
            "follow_up_state_closing": {
                "follow_up_state": "manual follow-up closing ticket",
            },
        }

        for label, override in cases.items():
            with self.subTest(label=label):
                candidate = {**valid_record, **override}
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record=candidate,
                )
                self.assertTrue(errors, label)

        for operator_note in (
            "Manual fallback can't bypass approval.",
            "Manual fallback can\u2019t bypass approval.",
            "Manual fallback cannot under any circumstances bypass approval.",
        ):
            with self.subTest(negated_operator_note=operator_note):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "operator_note": operator_note},
                )
                self.assertNotIn("operator_note_promotes_authority", errors)

        for operator_note in (
            "Manual fallback says execution is not truth.",
            "Manual fallback says receipt is not proof.",
        ):
            with self.subTest(negated_term_group_operator_note=operator_note):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "operator_note": operator_note},
                )
                self.assertNotIn("operator_note_promotes_authority", errors)

    def test_manual_fallback_validation_rejects_non_authoritative_evidence_claims(
        self,
    ) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "missing_receipt",
            "blocked_reason": "bound AegisOps execution receipt missing",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }

        for expected_evidence in (
            "ticket state confirms execution",
            "issue-lint output is authoritative",
            "Shuffle workflow state is execution truth",
            "UI cache proves receipt",
            "browser state confirms reconciliation",
            "AI output is authoritative for receipt proof",
            "verifier output proves execution",
            "operator note is reconciliation truth",
            "ticket output is authoritative",
            "Shuffle result is truth",
            "workflow result confirms receipt",
            "ticket state can confirm receipt",
            "ticket state confirms the receipt",
            "ticket state proves the execution",
            "issue lint report is receipt proof",
            "browser state is reconciliation proof",
            "AI output validates receipt",
            "AI output says receipt validates",
            "receipt proof comes from ticket state",
            "ticket output cannot prove execution; ticket state confirms receipt",
            "ticket output confirmed execution",
            "ticket output validate receipt",
            "workflow result validated receipt",
            "workflow result says receipt validated",
            "workflow result says receipt validates execution",
            "issue lint a b c d e lint output is authoritative",
            "output from ticket is authoritative",
            "state from workflow confirms receipt",
            "result from Shuffle proves execution",
            "ticket output not delayed and authoritative",
            (
                "ticket output is authoritative and bound AegisOps execution "
                "receipt remains required"
            ),
            "ticket state is proof of receipt",
            "workflow result is confirmation of execution",
            "browser state is validation of receipt",
            "Shuffle results prove execution",
            "workflow outputs are authoritative",
            "ticket states confirm receipt",
            "browser outputs validate reconciliation",
            "operator notes are reconciliation truth",
        ):
            with self.subTest(expected_evidence=expected_evidence):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={
                        **valid_record,
                        "expected_evidence": expected_evidence,
                    },
                )
                self.assertIn(
                    "expected_evidence_promotes_non_authoritative_truth",
                    errors,
                )

        compliant_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "bound AegisOps receipt proof and reconciliation review; "
                    "retain the ticket artifact reference as subordinate context"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            compliant_errors,
        )

        separated_authority_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "retain ticket output as subordinate context; bound AegisOps "
                    "receipt proof remains required"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            separated_authority_errors,
        )

        source_context_authoritative_aegisops_errors = (
            validate_phase62_manual_fallback_record(
                catalog_action="operator_notification",
                record={
                    **valid_record,
                    "expected_evidence": (
                        "ticket output retained only as context; authoritative "
                        "AegisOps receipt remains required"
                    ),
                },
            )
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            source_context_authoritative_aegisops_errors,
        )

        source_context_aegisops_authoritative_errors = (
            validate_phase62_manual_fallback_record(
                catalog_action="operator_notification",
                record={
                    **valid_record,
                    "expected_evidence": (
                        "ticket output retained only as context; AegisOps "
                        "receipt is authoritative"
                    ),
                },
            )
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            source_context_aegisops_authoritative_errors,
        )

        adjacent_aegisops_receipt_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "ticket output and authoritative AegisOps receipt remains "
                    "required"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            adjacent_aegisops_receipt_errors,
        )

        source_context_sentence_authority_errors = (
            validate_phase62_manual_fallback_record(
                catalog_action="operator_notification",
                record={
                    **valid_record,
                    "expected_evidence": (
                        "ticket output retained only as context. authoritative "
                        "AegisOps receipt remains required"
                    ),
                },
            )
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            source_context_sentence_authority_errors,
        )

        reverse_context_sentence_authority_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "bound AegisOps receipt is authoritative; ticket output "
                    "remains context"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            reverse_context_sentence_authority_errors,
        )

        negated_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "ticket output cannot prove execution and cannot replace the "
                    "bound AegisOps receipt"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            negated_errors,
        )

        contraction_negated_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "ticket output isn't authoritative and cannot replace the "
                    "bound AegisOps receipt"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            contraction_negated_errors,
        )

        smart_quote_contraction_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "ticket output isn\u2019t authoritative and cannot replace the "
                    "bound AegisOps receipt"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            smart_quote_contraction_errors,
        )

        long_form_negation_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "ticket output does not by itself become authoritative and "
                    "cannot replace the bound AegisOps receipt"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            long_form_negation_errors,
        )

        long_form_source_negation_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "ticket output is not under any circumstances authoritative "
                    "and cannot replace the bound AegisOps receipt"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            long_form_source_negation_errors,
        )

    def test_manual_fallback_validation_covers_current_head_review_examples(
        self,
    ) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "missing_receipt",
            "blocked_reason": "bound AegisOps execution receipt missing",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }

        for operator_note in (
            "manual fallback closed case",
            "manual fallback close case",
            "manual fallback closes cases",
            "manual fallback closes tickets",
            "manual fallback supplies closure of case",
            "manual fallback supplies closure of tickets",
            "manual fallback is closing cases",
            "execution confirmed",
            "receipt validated",
            "execution proven",
            "receipt proven",
            "ticket closed",
            "case closed",
            "operator note prove execution",
            "manual fallback confirming execution",
            "manual fallback validating receipt",
            "manual fallback proving execution",
            "manual fallback says execution succeeds",
            "manual fallback is authority for execution",
            "manual fallback is authoritative for execution",
            "manual fallback not only bypasses approval",
            "manual fallback not only confirmed execution",
            "manual fallback is proof of execution",
            "manual fallback is confirmation of execution",
            "manual fallback is validation of receipt",
        ):
            with self.subTest(operator_note=operator_note):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "operator_note": operator_note},
                )
                self.assertIn("operator_note_promotes_authority", errors)

        for expected_evidence in (
            "ticket output validate receipt",
            "output from ticket is authoritative",
            "ticket output confirmed execution",
            "ticket outputs are authoritative",
            "workflow outputs are authoritative",
            "ticket state is proof of receipt",
            "workflow result is confirmation of execution",
            "browser state is validation of receipt",
        ):
            with self.subTest(expected_evidence=expected_evidence):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "expected_evidence": expected_evidence},
                )
                self.assertIn(
                    "expected_evidence_promotes_non_authoritative_truth",
                    errors,
                )

        for expected_evidence in (
            "ticket output is not under any circumstances authoritative",
            "ticket state is receipt not proof",
            "ticket state is receipt not validation",
            "ticket state isnt receipt proof",
            "ticket output cannot prove execution, validate receipt, or bypass approval",
            "manual fallback does not prove execution, validate receipt, or bypass approval",
            (
                "bound AegisOps receipt is authoritative; ticket output "
                "remains context"
            ),
            (
                "bound AegisOps receipt is authoritative and ticket output "
                "remains context"
            ),
        ):
            with self.subTest(compliant_expected_evidence=expected_evidence):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "expected_evidence": expected_evidence},
                )
                self.assertNotIn(
                    "expected_evidence_promotes_non_authoritative_truth",
                    errors,
                )

        source_context_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "ticket output and analyst context, then confirms receipt"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            source_context_errors,
        )
        self.assertIn("expected_evidence_promotes_authority", source_context_errors)

        separated_source_context_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "ticket state includes owner shift case account route queue ticket "
                    "and analyst context, then confirms receipt"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            separated_source_context_errors,
        )
        self.assertIn(
            "expected_evidence_promotes_authority",
            separated_source_context_errors,
        )

        negated_operator_note_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "operator_note": (
                    "Manual fallback does not prove execution, validate receipt, "
                    "or bypass approval."
                ),
            },
        )
        self.assertNotIn(
            "operator_note_promotes_authority",
            negated_operator_note_errors,
        )

        for follow_up_state in (
            "execution succeeds",
            "ticket closes",
            "manual follow-up completes the action",
        ):
            with self.subTest(follow_up_state=follow_up_state):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "follow_up_state": follow_up_state},
                )
                self.assertIn("follow_up_state_promotes_completion", errors)

        errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "blocked_reason": "receipt missing after execution succeeds",
            },
        )
        self.assertIn("blocked_reason_promotes_success", errors)

    def test_manual_fallback_validation_covers_unresolved_connector_thread_cluster(
        self,
    ) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "missing_receipt",
            "blocked_reason": "bound AegisOps execution receipt missing",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }

        operator_authority_examples = (
            "manual fallback closed case",
            "manual fallback close case",
            "execution confirmed",
            "receipt validated",
            "ticket closed",
            "case closed",
            "operator note prove execution",
            "manual fallback confirming execution",
            "manual fallback validating receipt",
            "manual fallback proving execution",
            "manual fallback not only bypasses approval",
            "manual fallback not only confirmed execution",
            "manual fallback is proof of execution",
            "manual fallback is confirmation of execution",
            "manual fallback is validation of receipt",
            "manual fallback closes cases",
            "manual fallback closes tickets",
            "execution proven",
            "receipt proven",
            "manual fallback says execution succeeds",
            "manual fallback says execution succeeding",
            "manual fallback is authority for execution",
            "manual fallback is authoritative for execution",
        )
        for operator_note in operator_authority_examples:
            with self.subTest(operator_note=operator_note):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "operator_note": operator_note},
                )
                self.assertIn("operator_note_promotes_authority", errors)

        evidence_truth_examples = (
            "ticket output validate receipt",
            "output from ticket is authoritative",
            "state from workflow confirms receipt",
            "ticket state is proof of receipt",
            "workflow result is confirmation of execution",
            "ticket outputs are authoritative",
            "workflow outputs are authoritative",
        )
        for expected_evidence in evidence_truth_examples:
            with self.subTest(expected_evidence=expected_evidence):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "expected_evidence": expected_evidence},
                )
                self.assertIn(
                    "expected_evidence_promotes_non_authoritative_truth",
                    errors,
                )

        expected_evidence_authority_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={**valid_record, "expected_evidence": "execution succeeding"},
        )
        self.assertIn(
            "expected_evidence_promotes_authority",
            expected_evidence_authority_errors,
        )

        scoped_authority_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "bound AegisOps receipt is authoritative; ticket output "
                    "remains context"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            scoped_authority_errors,
        )
        comma_scoped_authority_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "expected_evidence": (
                    "bound AegisOps receipt is authoritative, ticket output "
                    "remains context"
                ),
            },
        )
        self.assertNotIn(
            "expected_evidence_promotes_non_authoritative_truth",
            comma_scoped_authority_errors,
        )

        category_examples = (
            ("shuffle_unavailable", "reviewed Shuffle execution timeout"),
            ("shuffle_unavailable", "reviewed Shuffle execution timed out"),
            ("execution_rejected", "reviewed Shuffle execution rejection before receipt"),
            ("execution_rejected", "reviewed Shuffle execution reject before receipt"),
            ("execution_rejected", "reviewed Shuffle execution rejects before receipt"),
            ("execution_rejected", "reviewed Shuffle execution rejecting before receipt"),
            ("execution_rejected", "reviewed Shuffle execution cancel before receipt"),
            ("execution_rejected", "reviewed Shuffle execution cancels before receipt"),
            ("execution_rejected", "reviewed Shuffle execution canceling before receipt"),
            ("missing_receipt", "bound AegisOps receipt absent"),
            ("missing_receipt", "bound AegisOps receipt missed"),
        )
        for fallback_state, blocked_reason in category_examples:
            with self.subTest(
                fallback_state=fallback_state,
                blocked_reason=blocked_reason,
            ):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={
                        **valid_record,
                        "fallback_state": fallback_state,
                        "blocked_reason": blocked_reason,
                    },
                )
                self.assertNotIn(
                    "blocked_reason_missing_failure_category",
                    errors,
                )

        success_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "blocked_reason": "receipt missing after execution succeeds",
            },
        )
        self.assertIn("blocked_reason_promotes_success", success_errors)
        progressing_success_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "blocked_reason": "receipt missing while execution succeeding",
            },
        )
        self.assertIn("blocked_reason_promotes_success", progressing_success_errors)

        for follow_up_state in ("execution succeeds", "ticket closes"):
            with self.subTest(follow_up_state=follow_up_state):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "follow_up_state": follow_up_state},
                )
                self.assertIn("follow_up_state_promotes_completion", errors)

    def test_manual_fallback_validation_rejects_closure_readiness_follow_up_state(
        self,
    ) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "missing_receipt",
            "blocked_reason": "bound AegisOps execution receipt missing",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }

        for follow_up_state in (
            "ticket_closure_ready",
            "case_closed",
            "ga_ready",
            "beta_readiness_claimed",
            "rc_ready",
            "commercial_replacement_readiness",
            "reconciliation_complete",
        ):
            with self.subTest(follow_up_state=follow_up_state):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "follow_up_state": follow_up_state},
                )
                self.assertIn("follow_up_state_promotes_completion", errors)

        for follow_up_state in (
            "not_ready_for_case_closure",
            "not_ready_for_reconciliation_complete",
            "wasn't_successful",
            "wasn\u2019t_successful",
            "manual_replacement_pending",
        ):
            with self.subTest(negated_follow_up_state=follow_up_state):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={**valid_record, "follow_up_state": follow_up_state},
                )
                self.assertNotIn("follow_up_state_promotes_completion", errors)

    def test_manual_fallback_validation_requires_blocked_reason_category(self) -> None:
        valid_record = {
            "fallback_owner_id": "it-operations-duty-owner",
            "operator_note": (
                "Manual follow-up required because Shuffle did not produce a "
                "bound AegisOps receipt; preserve approval and reconciliation review."
            ),
            "affected_action": "operator_notification",
            "fallback_state": "missing_receipt",
            "blocked_reason": "bound AegisOps execution receipt missing",
            "expected_evidence": (
                "bound AegisOps execution receipt and reconciliation review"
            ),
            "follow_up_state": "manual_follow_up_pending",
        }

        cases = {
            "shuffle_unavailable": "investigate later",
            "execution_rejected": "operator needs to review",
            "missing_receipt": "investigate later",
            "stale_receipt": "operator needs to review",
            "mismatched_receipt": "investigate later",
        }
        for fallback_state, blocked_reason in cases.items():
            with self.subTest(fallback_state=fallback_state):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={
                        **valid_record,
                        "fallback_state": fallback_state,
                        "blocked_reason": blocked_reason,
                    },
                )
                self.assertIn("blocked_reason_missing_failure_category", errors)

        negated_reason_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "fallback_state": "missing_receipt",
                "blocked_reason": "bound AegisOps execution receipt not missing",
            },
        )
        self.assertIn(
            "blocked_reason_missing_failure_category",
            negated_reason_errors,
        )

        success_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "fallback_state": "missing_receipt",
                "blocked_reason": (
                    "bound AegisOps execution receipt missing after unsuccessful "
                    "Shuffle handoff"
                ),
            },
        )
        self.assertNotIn("blocked_reason_promotes_success", success_errors)

        succeeded_errors = validate_phase62_manual_fallback_record(
            catalog_action="operator_notification",
            record={
                **valid_record,
                "fallback_state": "missing_receipt",
                "blocked_reason": "receipt missing after execution succeeded",
            },
        )
        self.assertIn("blocked_reason_promotes_success", succeeded_errors)

        for canceled_reason in (
            "reviewed Shuffle execution rejection before receipt emission",
            "reviewed Shuffle execution canceled before receipt emission",
            "reviewed Shuffle execution cancelled before receipt emission",
        ):
            with self.subTest(canceled_reason=canceled_reason):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={
                        **valid_record,
                        "fallback_state": "execution_rejected",
                        "blocked_reason": canceled_reason,
                    },
                )
                self.assertNotIn("blocked_reason_missing_failure_category", errors)

        mismatch_cases = {
            "shuffle_unavailable": "bound AegisOps receipt missing",
            "execution_rejected": "bound AegisOps receipt stale",
            "missing_receipt": "reviewed Shuffle route unavailable",
            "stale_receipt": "bound AegisOps execution receipt mismatched",
            "mismatched_receipt": "reviewed Shuffle execution rejected",
        }
        for fallback_state, blocked_reason in mismatch_cases.items():
            with self.subTest(mismatched_category=fallback_state):
                errors = validate_phase62_manual_fallback_record(
                    catalog_action="operator_notification",
                    record={
                        **valid_record,
                        "fallback_state": fallback_state,
                        "blocked_reason": blocked_reason,
                    },
                )
                self.assertIn("blocked_reason_missing_failure_category", errors)

    def test_shuffle_mapping_contains_reviewed_catalog_actions(self) -> None:
        self.assertEqual(
            set(PHASE62_SHUFFLE_WORKFLOW_MAPPINGS),
            set(PHASE62_ACTION_POLICIES),
        )

        tracking_ticket = PHASE62_SHUFFLE_WORKFLOW_MAPPINGS[
            "create_tracking_ticket"
        ]
        self.assertEqual(tracking_ticket.workflow_template_id, "create_tracking_ticket")
        self.assertEqual(
            tracking_ticket.reviewed_template_version,
            "create_tracking_ticket-v1-reviewed-2026-05-03",
        )
        self.assertEqual(tracking_ticket.family, "Soft Write")
        self.assertIn("correlation_id", tracking_ticket.correlation_fields)
        self.assertIn(
            "expected_execution_receipt_id",
            tracking_ticket.correlation_fields,
        )

        validation = validate_phase62_shuffle_workflow_mapping(
            catalog_action="create_tracking_ticket",
            workflow_template_id="create_tracking_ticket",
            reviewed_template_version="create_tracking_ticket-v1-reviewed-2026-05-03",
            family="Soft Write",
            required_inputs=tracking_ticket.required_inputs,
            expected_outputs=tracking_ticket.expected_outputs,
            correlation_fields=tracking_ticket.correlation_fields,
            policy_registry_id="phase62.2:create_tracking_ticket",
            review_status=tracking_ticket.review_status,
            import_eligible=tracking_ticket.import_eligible,
        )

        self.assertEqual(validation, ())

    def test_shuffle_mapping_validation_fails_closed_for_drift(self) -> None:
        reviewed_mapping = PHASE62_SHUFFLE_WORKFLOW_MAPPINGS["operator_notification"]

        missing_template = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        version_mismatch = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version="operator_notification-v2-unreviewed",
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        unreviewed_template = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:operator_notification",
            review_status="draft",
            import_eligible=False,
        )
        family_mismatch = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family="Hard Write",
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        missing_correlation = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=("action_request_id",),
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        unexpected_contract_fields = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs
            + ("unreviewed_operator_hint",),
            expected_outputs=reviewed_mapping.expected_outputs
            + ("unreviewed_delivery_receipt",),
            correlation_fields=reviewed_mapping.correlation_fields
            + ("unreviewed_correlation_hint",),
            policy_registry_id="phase62.2:operator_notification",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        policy_incompatibility = validate_phase62_shuffle_workflow_mapping(
            catalog_action="operator_notification",
            workflow_template_id="operator_notification",
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs,
            expected_outputs=reviewed_mapping.expected_outputs,
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id="phase62.2:create_tracking_ticket",
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )
        unsupported_action = validate_phase62_shuffle_workflow_mapping(
            catalog_action="disable_account",
            workflow_template_id="disable_account",
            reviewed_template_version="disable_account-v1-reviewed",
            family="Hard Write",
            required_inputs=("action_request_id",),
            expected_outputs=("execution_receipt_id",),
            correlation_fields=("correlation_id",),
            policy_registry_id="phase62.2:disable_account",
            review_status="reviewed",
            import_eligible=True,
        )

        self.assertIn("missing_template", missing_template)
        self.assertIn("version_mismatch", version_mismatch)
        self.assertIn("unreviewed_template", unreviewed_template)
        self.assertIn("family_mismatch", family_mismatch)
        self.assertIn("missing_correlation", missing_correlation)
        self.assertIn("unexpected_required_input", unexpected_contract_fields)
        self.assertIn("unexpected_expected_output", unexpected_contract_fields)
        self.assertIn("unexpected_correlation", unexpected_contract_fields)
        self.assertIn("policy_incompatibility", policy_incompatibility)
        self.assertIn("unsupported_action", unsupported_action)

    def test_shuffle_mapping_validation_rejects_action_specific_contract_drift(
        self,
    ) -> None:
        reviewed_mapping = PHASE62_SHUFFLE_WORKFLOW_MAPPINGS["create_tracking_ticket"]

        validation = validate_phase62_shuffle_workflow_mapping(
            catalog_action="create_tracking_ticket",
            workflow_template_id=reviewed_mapping.workflow_template_id,
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=tuple(
                field
                for field in reviewed_mapping.required_inputs
                if field not in {"ticket_pointer_id", "ticket_system_id"}
            ),
            expected_outputs=tuple(
                field
                for field in reviewed_mapping.expected_outputs
                if field not in {"ticket_pointer_id", "ticket_system_id"}
            ),
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id=reviewed_mapping.policy_registry_id,
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )

        self.assertIn("missing_required_input", validation)
        self.assertIn("missing_expected_output", validation)

        unexpected_validation = validate_phase62_shuffle_workflow_mapping(
            catalog_action="create_tracking_ticket",
            workflow_template_id=reviewed_mapping.workflow_template_id,
            reviewed_template_version=reviewed_mapping.reviewed_template_version,
            family=reviewed_mapping.family,
            required_inputs=reviewed_mapping.required_inputs
            + ("unreviewed_ticket_priority",),
            expected_outputs=reviewed_mapping.expected_outputs
            + ("unreviewed_ticket_url",),
            correlation_fields=reviewed_mapping.correlation_fields,
            policy_registry_id=reviewed_mapping.policy_registry_id,
            review_status=reviewed_mapping.review_status,
            import_eligible=reviewed_mapping.import_eligible,
        )

        self.assertIn("unexpected_required_input", unexpected_validation)
        self.assertIn("unexpected_expected_output", unexpected_validation)

    def test_validation_allows_reviewed_tracking_ticket_policy(self) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="create_tracking_ticket",
            requester_identity="analyst-phase62-001",
            target_scope={
                "case_id": "case-001",
                "coordination_reference_id": "coordination-ref-001",
                "coordination_target_type": "zammad",
            },
            expires_at=self.now + timedelta(hours=4),
            idempotency_key="create-tracking-ticket:abc",
            now=self.now,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.decision, "allowed")
        self.assertEqual(decision.denial_reasons, ())

    def test_validation_denies_missing_policy(self) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="disable_account",
            requester_identity="analyst-001",
            target_scope={"case_id": "case-001"},
            expires_at=self.now + timedelta(hours=4),
            idempotency_key="disable-account:abc",
            now=self.now,
        )

        self.assertFalse(decision.allowed)
        self.assertIn("missing_reviewed_policy", decision.denial_reasons)

    def test_validation_denies_expired_wrong_role_wrong_scope_and_missing_idempotency(
        self,
    ) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="create_tracking_ticket",
            requester_identity="read-only-auditor-001",
            target_scope={
                "case_id": "case-001",
                "coordination_reference_id": "coordination-ref-001",
                "coordination_target_type": "unreviewed-ticket-system",
            },
            expires_at=self.now - timedelta(minutes=1),
            idempotency_key=None,
            now=self.now,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(
            decision.denial_reasons,
            (
                "requester_role_not_allowed",
                "policy_expired",
                "missing_idempotency_key",
                "target_scope_not_allowed",
            ),
        )

    def test_validation_denies_protected_target_misuse(self) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="operator_notification",
            requester_identity="analyst-001",
            target_scope={
                "recipient_identity": "operator-001",
                "protected_target": True,
            },
            expires_at=self.now + timedelta(hours=4),
            idempotency_key="operator-notification:abc",
            now=self.now,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.denial_reasons, ("protected_target_misuse",))

    def test_validation_routes_protected_manual_escalation_to_approval(self) -> None:
        decision = evaluate_phase62_action_policy(
            action_type="manual_escalation_request",
            requester_identity="analyst-001",
            target_scope={
                "escalation_owner_ref": "it-operations-duty-owner",
                "protected_target": True,
            },
            expires_at=self.now + timedelta(hours=4),
            idempotency_key="manual-escalation:abc",
            now=self.now,
        )

        self.assertTrue(decision.allowed)
        self.assertEqual(decision.denial_reasons, ())
        self.assertEqual(
            decision.as_policy_evaluation()["approval_requirement"],
            "human_required_for_protected_follow_up",
        )
        self.assertEqual(decision.as_policy_evaluation()["routing_target"], "approval")


if __name__ == "__main__":
    unittest.main()
