# Phase 56.3 Case Timeline Authority Projection Contract

- **Status**: Accepted contract
- **Date**: 2026-05-04
- **Owner**: AegisOps maintainers
- **Related Issues**: #1190, #1191, #1193
- **Related Baseline**: `docs/phase-51-6-authority-boundary-negative-test-policy.md`, `docs/deployment/today-view-backend-projection-contract.md`

This contract defines the backend case timeline projection that separates authoritative AegisOps record truth from subordinate Wazuh, Shuffle, AI, ticket, and report context. The required structured artifact is `docs/deployment/profiles/smb-single-node/case-timeline-projection.yaml`.

## 1. Purpose

The case timeline projection gives operators one ordered case-detail surface for the reviewed workflow chain. It may organize context, but it cannot create, replace, infer, or complete workflow truth.

The required timeline segments are:

| Segment | Purpose | Authority posture |
| --- | --- | --- |
| wazuh_signal | Show the directly admitted Wazuh-origin signal context for the case. | Subordinate context; Wazuh state cannot become AegisOps alert, case, evidence, receipt, reconciliation, or closeout truth. |
| aegisops_alert | Show the authoritative alert bound to the case. | Authoritative AegisOps alert record. |
| evidence | Show directly linked AegisOps evidence and custody posture. | Authoritative AegisOps evidence record; external evidence systems stay subordinate. |
| ai_summary | Show assistant summary or trace context. | Subordinate advisory context; AI cannot approve, execute, reconcile, close, gate, or mutate records. |
| recommendation | Show directly linked recommendation context. | Subordinate advisory context until translated into explicit AegisOps action-review records. |
| action_request | Show the reviewed action request. | Authoritative AegisOps action request record. |
| approval | Show the approval decision. | Authoritative AegisOps approval decision record. |
| shuffle_receipt | Show delegated execution receipt context. | Subordinate execution context bound through the AegisOps action execution record; Shuffle success cannot close or reconcile by itself. |
| reconciliation | Show comparison and closeout readiness. | Authoritative AegisOps reconciliation record. |

## 2. Authority Boundary

Only AegisOps control-plane records carry alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, gate, release, or closeout truth.

The timeline projection must reject inferred linkage from sibling records, parent records, timestamps, title text, UI cache, Wazuh state, Shuffle state, tickets, reports, or AI output. If a segment has no direct backend record binding, the segment remains visible with `missing`, `degraded`, `stale`, `mismatch`, or `unsupported` state instead of being silently treated as complete.

## 3. Segment States

| State | Required behavior |
| --- | --- |
| normal | A directly linked backend record exists and its authoritative lifecycle or subordinate context is current for display. |
| missing | A required direct binding is absent. Keep the segment visible. |
| degraded | A bound record exists but provenance, custody, source-health, advisory, or subordinate context is incomplete. |
| stale | A bound authoritative record or receipt is stale. Do not treat cached projection output as current truth. |
| mismatch | A bound reconciliation, receipt, or source-linkage record disagrees with the expected authoritative state. |
| unsupported | A bound state is outside the reviewed Phase 56.3 contract. Keep the segment visible and do not infer success. |

## 4. Projection Rules

| Rule | Required behavior |
| --- | --- |
| all-required-segments-present | The backend projection and artifact name `wazuh_signal`, `aegisops_alert`, `evidence`, `ai_summary`, `recommendation`, `action_request`, `approval`, `shuffle_receipt`, and `reconciliation`. |
| direct-binding-required | Every segment includes a backend record binding with a record family and record identifier or an explicit missing reason. |
| authority-posture-required | Every segment labels `authoritative_aegisops_record` or `subordinate_context`. |
| missing-degraded-visible | Missing, degraded, stale, mismatch, and unsupported segments remain visible and cannot be summarized away. |
| no-inferred-linkage | Sibling, parent, timestamp, title, UI cache, Wazuh, Shuffle, ticket, report, or AI-output hints cannot bind a segment. |
| no-projection-truth | Timeline projection output cannot close, approve, execute, reconcile, gate, release, mutate, or replace authoritative records. |

## 5. Validation

Run `PYTHONPATH=control-plane/tests python3 -m unittest control-plane.tests.test_phase56_3_case_timeline_projection`.

Run `python3 -m unittest control-plane.tests.test_phase56_3_case_timeline_projection_contract`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1190 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1193 --config <supervisor-config-path>`.

## 6. Non-Goals

Phase 56.3 does not implement visual timeline UI, task cards, handoff view, admin/RBAC, supportability, reporting breadth, SOAR breadth, RC readiness, GA readiness, or commercial readiness.

Phase 56.3 does not make UI cache, Wazuh state, Shuffle state, tickets, reports, AI output, verifier output, or issue-lint output authoritative AegisOps truth.
