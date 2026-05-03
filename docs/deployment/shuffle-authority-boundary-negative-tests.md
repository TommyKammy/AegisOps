# Phase 54.9 Shuffle Authority-Boundary Negative Tests

- **Status**: Accepted negative-test slice
- **Date**: 2026-05-03
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/deployment/shuffle-smb-single-node-profile-contract.md`, `docs/deployment/shuffle-reviewed-workflow-template-contract.md`, `docs/deployment/shuffle-manual-fallback-contract.md`
- **Related Issues**: #1154, #1160, #1161, #1163

This slice makes the Shuffle authority-boundary negative tests directly runnable for the Phase 54 Shuffle product profile MVP.

It does not implement profile generation, template import behavior, receipt normalization, broad SOAR action catalog expansion, Controlled Write or Hard Write default enablement, release-candidate behavior, general-availability behavior, commercial readiness, or broad SOAR replacement readiness.

## 1. Purpose

Phase 54.9 proves that Shuffle remains subordinate routine automation substrate context when direct launch, workflow success, ticket state, callback payloads, workflow canvas state, or execution logs are presented as AegisOps workflow truth.

The focused enforcement tests live in `control-plane/tests/test_cross_boundary_negative_e2e_validation.py`.

## 2. Authority Boundary

Shuffle executes delegated routine work only after AegisOps records the action request, approval posture, delegation, execution receipt, and reconciliation records required by policy.

AegisOps control-plane records remain authoritative for approval, action request, execution receipt, reconciliation, case lifecycle, audit, limitation, release, gate, and closeout truth.

This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.

Shuffle workflow status, workflow success, workflow failure, retry state, callback payloads, workflow canvas state, execution logs, generated config, tickets, assistant output, browser state, UI cache, optional evidence, verifier output, issue-lint output, and downstream receipts cannot close, approve, execute, reconcile, release, gate, or otherwise mutate authoritative AegisOps records without explicit AegisOps approval, action request, delegation, execution receipt, and reconciliation records.

## 3. Required Negative Tests

| Negative test | Enforcement boundary | Expected result |
| --- | --- | --- |
| Direct ad-hoc Shuffle launch bypassing AegisOps approval. | `delegate_approved_action_to_shuffle` | Reject the launch before dispatch and leave case, action execution, and reconciliation records unchanged. |
| Shuffle workflow success is presented as reconciliation truth without AegisOps delegation. | `reconcile_action_execution` | Record a mismatched reconciliation and do not create or infer an action execution record. |
| Ticket state, callback payload, workflow canvas state, or logs are presented as AegisOps case truth. | `reconcile_action_execution` and case record inspection | Keep the matched execution receipt subordinate to the AegisOps reconciliation record and leave case and alert lifecycle state unchanged. |

## 4. Validation

Run `bash scripts/verify-phase-54-9-shuffle-authority-boundary-negative-tests.sh`.

From the repository root, run `PYTHONPATH="${PWD}/control-plane:${PWD}/control-plane/tests" python3 -m unittest test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_direct_ad_hoc_shuffle_launch_without_aegisops_approval_fails_closed test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_shuffle_success_without_aegisops_delegation_is_mismatched_not_truth test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_ticket_callback_canvas_and_logs_do_not_close_case_after_shuffle_success`.

Run affected Shuffle delegation and reconciliation tests with `PYTHONPATH="${PWD}/control-plane:${PWD}/control-plane/tests" python3 -m unittest test_service_persistence_action_reconciliation_create_tracking_ticket test_service_persistence_action_reconciliation_reconciliation`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1163 --config <supervisor-config-path>`.

## 5. Non-Goals

- No direct ad-hoc Shuffle launch path is approved.
- No Shuffle workflow status, success, failure, callback payload, workflow canvas state, execution log, ticket state, verifier output, or issue-lint output becomes AegisOps workflow truth.
- No template import, receipt normalization, profile generation, broad SOAR action catalog, Controlled Write default enablement, Hard Write default enablement, Beta, RC, GA, commercial readiness, or broad SOAR replacement readiness is implemented here.
