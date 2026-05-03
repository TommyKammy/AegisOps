# Phase 56.1 Today View Backend Projection Contract

- **Status**: Accepted contract
- **Date**: 2026-05-04
- **Owner**: AegisOps maintainers
- **Related Issues**: #1190, #1191
- **Related Baseline**: `docs/phase-55-closeout-evaluation.md`, `docs/phase-51-6-authority-boundary-negative-test-policy.md`

This contract defines the backend projection shape that powers the Daily SOC Workbench `Today` view. The required structured artifact is `docs/deployment/profiles/smb-single-node/today-view-projection.yaml`.

## 1. Purpose

The Today projection gives a low-staff SMB operator one backend-owned work-focus surface for the current operating day. It may rank, group, and summarize records, but it must not create workflow truth.

The projection lanes are:

| Lane | Purpose | Authority posture |
| --- | --- | --- |
| priority | Show the highest-priority AegisOps-owned work items for review. | Derived from authoritative AegisOps alert, case, approval, action request, receipt, reconciliation, gate, limitation, and closeout records. |
| stale_work | Show authoritative records whose reviewed freshness or lifecycle timestamps require attention. | Uses AegisOps lifecycle timestamps; stale projection text is not current truth. |
| pending_approvals | Show approval-bound action reviews that need an approver decision. | Approval truth remains the AegisOps approval record, not the Today lane. |
| degraded_sources | Show subordinate source-health context that may affect review confidence. | Wazuh, Shuffle, ticket, report, and health-summary state remain subordinate context. |
| reconciliation_mismatches | Show action, receipt, and reconciliation records with mismatch or unresolved status. | Reconciliation truth remains the AegisOps reconciliation record. |
| evidence_gaps | Show cases or action reviews missing required linked evidence, custody, or scope-binding records. | Evidence truth remains explicit AegisOps evidence records. |
| ai_suggested_focus | Show advisory-only focus hints grounded in directly linked AegisOps records. | AI-suggested focus is advisory-only and cannot approve, execute, reconcile, close, gate, or mutate records. |

## 2. Authority Boundary

AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, approval, action request, receipt, reconciliation, audit, limitation, gate, release, and closeout truth.

The Today projection can prioritize and summarize work, but it cannot create workflow truth. Stale or cached Today projection output cannot satisfy authority, approval, execution, or reconciliation truth.

UI, browser cache, AI focus hints, Wazuh state, Shuffle state, tickets, reports, and health summaries are subordinate to backend AegisOps control-plane records. If these surfaces drift from the authoritative record chain, repair or reject the projection instead of redefining truth around the summary.

This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI, Wazuh, Shuffle, tickets, browser state, UI cache, downstream receipts, and derived projection shortcut rejection.

## 3. Projection Inputs

| Input | Required binding |
| --- | --- |
| AegisOps alert records | Durable alert identifier, lifecycle state, severity, source admission binding, authoritative timestamps. |
| AegisOps case records | Durable case identifier, lifecycle state, owner or queue assignment, authoritative timestamps. |
| AegisOps evidence records | Evidence identifier, custody posture, scope binding, linked case or action-review record. |
| AegisOps recommendation records | Recommendation identifier, directly linked subject record, advisory lineage, freshness. |
| AegisOps approval and action review records | Review identifier, requested action, approver state, separation and decision posture. |
| AegisOps receipt and reconciliation records | Action request identifier, receipt identifier, reconciliation state, mismatch or unresolved marker. |
| Subordinate Wazuh, Shuffle, ticket, report, and health context | Explicit linkage to an AegisOps record and non-authority posture. |

## 4. Projection States

| State | Meaning | Required behavior |
| --- | --- | --- |
| empty | No eligible authoritative work records exist for the operator scope. | Return an empty lane set with explicit non-authority posture. |
| normal | Eligible records are current and directly linked to authoritative AegisOps records. | Rank and summarize without mutating truth. |
| degraded | One or more subordinate reads, source-health contexts, tickets, reports, or health summaries are unavailable or incomplete. | Preserve authoritative records and mark subordinate context degraded. |
| stale | One or more authoritative records require attention based on AegisOps timestamps, or a projection snapshot is stale. | Surface stale work, but reject stale projection output as current truth. |
| mismatch | A directly linked AegisOps receipt, reconciliation, or source-linkage record disagrees with expected state. | Keep mismatch visible and do not close or reconcile from subordinate state. |
| evidence_gap | Required evidence, custody, or scope binding is absent for a directly linked case or action review. | Surface the gap and keep authority anchored to AegisOps evidence records. |

## 5. Projection Rules

| Rule | Required behavior |
| --- | --- |
| all-required-lanes-present | The backend contract and artifact name priority, stale_work, pending_approvals, degraded_sources, reconciliation_mismatches, evidence_gaps, and ai_suggested_focus. |
| empty-state-visible | Empty output must be explicit and must not imply healthy production readiness or completed workflow truth. |
| normal-state-authoritative-anchors | Normal output must point to authoritative AegisOps record identifiers for every lane item. |
| degraded-subordinate-context-visible | Missing Wazuh, Shuffle, ticket, report, or health context must be labeled subordinate and degraded. |
| stale-projection-rejected-as-truth | Cached or stale projection output cannot satisfy current authority, approval, execution, or reconciliation truth. |
| mismatch-preserved | Reconciliation mismatch and source-link mismatch must remain visible until the AegisOps reconciliation or linkage record is corrected. |
| evidence-gap-preserved | Missing evidence or custody linkage must stay visible and cannot be hidden by summary status. |
| ai-focus-advisory-only | AI-suggested focus remains advisory-only and directly linked to authoritative AegisOps records. |
| no-authority-mutation | The Today projection cannot close, approve, execute, reconcile, gate, release, or mutate authoritative records. |

## 6. Validation Rules

Focused backend tests must cover empty, normal, degraded, stale, mismatch, and evidence_gap states. The tests must also reject stale projection output as current truth, AI-suggested focus as authority, Wazuh/Shuffle/ticket state as authoritative closeout, and Today summary state as approval, execution, or reconciliation truth.

## 7. Forbidden Claims

- Today projection is AegisOps approval truth.
- Today projection is AegisOps execution truth.
- Today projection is AegisOps reconciliation truth.
- Today projection closes AegisOps cases.
- Stale Today projection output is current AegisOps truth.
- Cached Today view output satisfies approval truth.
- AI-suggested focus approves actions.
- AI-suggested focus executes actions.
- AI-suggested focus reconciles actions.
- Wazuh state closes Today work.
- Shuffle state closes Today work.
- Ticket state closes Today work.
- Health summary state is AegisOps workflow truth.
- Report output is AegisOps closeout truth.
- Phase 56.1 implements the Today UI.
- Phase 56.1 claims Beta, RC, GA, or commercial readiness.

## 8. Validation

Run `python3 -m unittest control-plane.tests.test_phase56_1_today_projection_contract`.

Run `bash scripts/verify-phase-56-1-today-view-projection-contract.sh`.

Run `bash scripts/test-verify-phase-56-1-today-view-projection-contract.sh`.

Run `bash scripts/verify-publishable-path-hygiene.sh`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1190 --config <supervisor-config-path>`.

Run `node <codex-supervisor-root>/dist/index.js issue-lint 1191 --config <supervisor-config-path>`.

## 9. Non-Goals

Phase 56.1 does not implement Today UI, browser cache behavior, case timeline projection, task cards, handoff UI, navigation, health summary, admin/RBAC, supportability, reporting breadth, SOAR breadth, RC readiness, GA readiness, or commercial readiness.

Phase 56.1 does not make UI, browser cache, AI focus hints, Wazuh state, Shuffle state, tickets, reports, health summaries, verifier output, or issue-lint output authoritative AegisOps truth.
