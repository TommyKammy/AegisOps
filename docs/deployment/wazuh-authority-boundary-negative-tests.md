# Phase 53.8 Wazuh Authority-Boundary Negative Tests

- **Status**: Accepted negative-test slice
- **Date**: 2026-05-02
- **Owners**: AegisOps maintainers
- **Related Baseline**: `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/deployment/wazuh-manager-intake-binding-contract.md`, `docs/deployment/wazuh-source-health-projection-contract.md`
- **Related Issues**: #1135, #1138, #1141, #1143

This slice makes the Wazuh authority-boundary negative tests directly runnable for the Phase 53 Wazuh product profile MVP.

It does not implement Shuffle product profiles, Wazuh Active Response authority, Wazuh dashboard authority, fleet-scale Wazuh management, broad SIEM detector catalog, release-candidate behavior, general-availability behavior, or commercial readiness.

## 1. Purpose

Phase 53.8 proves that Wazuh remains subordinate detection substrate context when raw Wazuh status or Wazuh-origin automation evidence is presented as AegisOps workflow truth.

The focused enforcement tests live in `control-plane/tests/test_cross_boundary_negative_e2e_validation.py`.

## 2. Authority Boundary

Wazuh detections are analytic signals until admitted and linked by AegisOps.

AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth.

This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.

Wazuh status, Wazuh alert status, Wazuh dashboard state, Wazuh manager state, Wazuh Active Response state, Wazuh-triggered Shuffle runs, Shuffle workflow state, verifier output, issue-lint output, tickets, assistant output, browser state, UI cache, optional evidence, and downstream receipts cannot close, approve, execute, reconcile, release, gate, or otherwise mutate authoritative AegisOps records without explicit AegisOps admission, approval, delegation, execution, and reconciliation records.

## 3. Required Negative Tests

| Negative test | Enforcement boundary | Expected result |
| --- | --- | --- |
| Raw Wazuh alert status closes an AegisOps case. | `record_case_disposition` | Reject the closure and leave case and alert lifecycle state unchanged. |
| Wazuh-triggered Shuffle execution appears without AegisOps delegation. | `reconcile_action_execution` | Record a mismatched reconciliation and do not create or infer an action execution record. |
| Wazuh Active Response is presented as AegisOps authority. | Phase 53.5 and Phase 53.8 verifier references | Keep Active Response outside authority paths. |
| Wazuh dashboard state is presented as workflow truth. | Phase 53.6 and Phase 53.8 verifier references | Keep dashboard state subordinate source-health context only. |

## 4. Validation

Run `bash scripts/verify-phase-53-8-wazuh-authority-boundary-negative-tests.sh`.

From the repository root, run `PYTHONPATH="${PWD}/control-plane:${PWD}/control-plane/tests" python3 -m unittest test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_raw_wazuh_status_cannot_close_aegisops_case test_cross_boundary_negative_e2e_validation.CrossBoundaryNegativeE2EValidationTests.test_wazuh_triggered_shuffle_run_without_aegisops_delegation_is_mismatched`.

Run Wazuh source-health tests with `bash scripts/verify-phase-53-6-wazuh-source-health-projection.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1143 --config <supervisor-config-path>`.

## 5. Non-Goals

- No Wazuh Active Response authority path is implemented.
- No direct Wazuh-to-Shuffle shortcut is approved.
- No Wazuh alert status, dashboard state, manager state, source-health projection, verifier output, or issue-lint output becomes AegisOps workflow truth.
- No Phase 54 Shuffle product profile work is implemented.
