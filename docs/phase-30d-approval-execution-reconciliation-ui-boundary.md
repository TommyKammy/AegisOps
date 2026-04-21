# AegisOps Phase 30D Approval, Execution, and Reconciliation UI Boundary

## 1. Purpose

This document defines the reviewed Phase 30D boundary for approval, execution, and reconciliation surfaces in the React-Admin operator console before implementation introduces decision controls, action-review read support, or broader workflow views.

It supplements `docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md`, `docs/phase-30c-bounded-write-actions-ui-boundary.md`, `docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md`, `docs/response-action-safety-model.md`, `docs/control-plane-state-model.md`, `docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary.md`, and `docs/architecture.md`.

This document defines UI-boundary, lifecycle-rendering, authority-split, route-gating, authorization, authoritative re-read, and implementation-sequencing rules only. It does not approve browser-owned workflow truth, approval-by-toggle shortcuts, substrate-owned approval decisions, or generic CRUD expansion.

## 2. Reviewed Phase 30D Boundary

Phase 30D introduces a reviewed operator surface for action request detail, approval decision surface, action review timeline, execution receipt summary, reconciliation mismatch visibility, and coordination reference panel.

The Reviewed Phase 30D Boundary is intentionally narrow:

- the browser may show reviewed approval, execution, and reconciliation state for one authoritative action-review context at a time;
- the browser may submit one reviewed approval decision request through a bounded backend-owned contract when the operator role and backend authorization both permit it; and
- the browser must not invent lifecycle semantics, execution truth, or reconciliation truth from local state, cached state, or subordinate substrate context.

Phase 30D remains a task-oriented authority-preserving surface rather than a workflow engine in the browser.

The browser may show lifecycle state, actor identity, review history, execution receipts, and coordination references, but the backend-owned lifecycle truth and the authoritative record chain remain primary.

Phase 30D does not authorize:

- browser-owned workflow truth;
- approval-by-toggle shortcuts;
- substrate-owned approval decisions;
- implicit promotion of Shuffle-derived state into approval, execution, or reconciliation authority; or
- generic CRUD expansion.

## 3. Phase 30D Surface Contract

The approved Phase 30D surface contract is limited to six operator-facing areas:

- `action request detail` as the authoritative summary of the request under review, including target, payload binding, expiry, rationale, and directly linked recommendation or case context;
- `approval decision surface` as the bounded place where an approver can approve or reject the exact reviewed request under backend-controlled rules;
- `action review timeline` as the lifecycle-bearing chronology for request, approval, delegation, execution, and reconciliation events;
- `execution receipt summary` as the operator-facing view of backend-correlated execution receipts and execution outcome;
- `reconciliation mismatch visibility` as the required view for unresolved, degraded, or mismatched downstream state; and
- `coordination reference panel` as subordinate context for coordination links or receipts that assist review without becoming lifecycle authority.

Each area must stay anchored to one authoritative action-review context. The browser must not combine unrelated request, approval, execution, or reconciliation records into a synthetic workflow summary.

## 4. Lifecycle Rendering Semantics

Phase 30D must render lifecycle state explicitly rather than collapsing distinct meanings into generic status badges or toggle controls.

The reviewed lifecycle-bearing states for the operator surface are:

- `pending` when review is waiting for approval outcome or a required prerequisite;
- `approved` when the exact action request has a valid approval outcome within the approved binding window;
- `rejected` when approval outcome denied the request and execution must remain blocked;
- `expired` when the approval window or actionable request context is no longer valid for execution;
- `superseded` when a newer authoritative request, approval decision, or lifecycle record replaced the current one;
- `unresolved` when the request, execution, or reconciliation path remains open because authoritative completion is missing or inconclusive; and
- `degraded` when the operator can still inspect authoritative records but a required read, receipt, or refresh path is partially unavailable.

These states must render as lifecycle states with explicit labels and contextual explanation. Approval is not a toggle, and the operator UI must not present approval as a reversible switch detached from the authoritative approval record.

Execution success is not reconciliation success. Reconciliation mismatch visibility must remain separate from execution outcome even when the downstream executor reported success.

## 5. Outcome Separation Rules

Phase 30D must distinguish approval outcome, execution outcome, and reconciliation outcome everywhere the operator reviews action state.

The minimum reviewed split is:

- `approval outcome` answers whether the exact action request is authorized;
- `execution outcome` answers what the reviewed execution surface attempted or reported; and
- `reconciliation outcome` answers whether authoritative AegisOps reconciliation determined that observed execution behavior satisfied, diverged from, or failed to prove the approved intent.

This split is mandatory because execution success is not reconciliation success, and reconciliation mismatch visibility must remain visible even after a successful downstream receipt.

The operator console must not:

- infer approval from the existence of execution receipts;
- infer reconciliation success from a downstream completed status;
- treat the absence of mismatch detail as proof that reconciliation succeeded; or
- collapse approval outcome, execution outcome, and reconciliation outcome into one convenience badge.

## 6. Browser Show, Submit, and Prohibited Behavior

The browser may show:

- the current authoritative request and approval binding fields;
- lifecycle-bearing review history from the action review timeline;
- execution receipt summary fields that the backend correlated to the authoritative request;
- explicit reconciliation mismatch visibility, including unresolved and degraded outcomes; and
- coordination reference panel entries and bounded Shuffle-derived state as subordinate context.

The browser may submit:

- one reviewed approval decision request against the current authoritative action-review record when the operator role is allowed and backend authorization succeeds; and
- one explicit refresh request that triggers an authoritative re-read of the current action-review context.

The browser must not:

- approve or reject by mutating local state first and hoping later refresh makes it true;
- treat a control as allowed because a route rendered;
- synthesize approval, execution, or reconciliation state from route parameters, timing, or cached rows;
- generalize coordination references or Shuffle-derived state beyond the directly linked authoritative record; or
- downgrade missing or inconsistent lifecycle facts into apparent success.

## 7. Coordination and Substrate Context Boundary

Coordination references and Shuffle-derived state may appear only as subordinate context.

The coordination reference panel may show:

- ticket or coordination links that are directly linked to the current authoritative record;
- subordinate assignee, queue, comment, or external receipt details; and
- bounded Shuffle-derived state such as workflow receipt identifiers, run references, or correlated execution evidence.

That subordinate context must not become approval, execution, or reconciliation authority.

If coordination metadata or Shuffle-derived state disagrees with the authoritative action review timeline, approval outcome, execution outcome, or reconciliation outcome, AegisOps remains authoritative and the disagreement must stay visible.

The browser must not widen one coordination reference, one receipt, or one subordinate note into sibling or broader workflow authority without an explicit authoritative link.

## 8. Role-Gating, Route-Gating, and Backend Authorization

Route-gating and role-gating remain discoverability and posture controls only. Backend authorization remains the enforcement boundary.

The reviewed access posture is:

- route-gating must block missing, malformed, expired, or unauthorized sessions before a Phase 30D page or drawer renders protected workflow detail;
- role-gating may hide the approval decision surface from operators who lack reviewed approval authority;
- backend authorization must still validate every action-review read, approval decision request, and refresh attempt; and
- forbidden, unauthorized, stale, or unbound requests must fail closed and remain visible as explicit outcomes rather than empty success.

If a route becomes visible to an operator who is not actually allowed to review or decide, the backend authorization decision still controls and the operator console must preserve that denial as authoritative.

## 9. Authoritative Re-Read and Lifecycle Reread Contract

Every approval decision and every explicit refresh in Phase 30D requires an authoritative re-read.

The lifecycle reread sequence is:

1. render the current action request detail, approval decision surface, action review timeline, execution receipt summary, reconciliation mismatch visibility, and coordination reference panel from the current authoritative snapshot;
2. submit one reviewed approval decision request or one reviewed refresh request to the backend;
3. treat the initial mutation or refresh acknowledgment as transport feedback only, not as final lifecycle truth;
4. perform an authoritative re-read of the action-review record family and directly linked authoritative records; and
5. render the resulting lifecycle state from that authoritative re-read.

Authoritative re-read is mandatory because the backend-owned lifecycle truth, not the browser, selects the current approval, execution, and reconciliation state.

If lifecycle reread fails, the operator console must preserve uncertainty, degraded state, or unresolved state explicitly rather than implying durable success.

## 10. Degraded, Missing, and Mismatch Handling

Phase 30D must keep rejected, forbidden, expired, unresolved, and degraded states explicit, and mismatch must remain visible.

Minimum reviewed handling is:

- `rejected` keeps execution blocked and renders the approval outcome as denied rather than silently returning to pending;
- `expired` blocks execution and surfaces that prior approval no longer covers the current request context;
- `unresolved` stays visible when authoritative execution or reconciliation proof is incomplete;
- `degraded` stays visible when reread, receipt retrieval, or correlation is partially unavailable; and
- mismatch must remain visible when approval, execution, coordination, or reconciliation records disagree.

No Phase 30D surface may normalize disagreement away merely because the downstream receipt looked successful or because subordinate context is fresher than the authoritative record.

## 11. Safe Implementation Sequence

Safe implementation sequence for Phase 30D is:

1. action-review read support
2. approval decision surfaces
3. execution and reconciliation visibility
4. validation

More specifically:

1. `action-review read support` comes first so the route, resource, and backend-backed read contract exist before any approval or lifecycle rendering logic lands.
2. `approval decision surfaces` come second so reviewed approval submits inherit one bounded contract instead of page-local toggle behavior.
3. `execution and reconciliation visibility` comes third so execution receipt summary, reconciliation mismatch visibility, and coordination reference panel all render against the same authoritative split.
4. `validation` comes last so documentation and focused UI or contract tests can verify lifecycle semantics, authorization posture, and authoritative reread behavior after the contract is fixed.

Safe implementation sequence is mandatory because action-first UI shortcuts would otherwise encourage approval-by-toggle shortcuts, synthetic workflow truth, and page-local lifecycle semantics.

## 12. Validation Expectations

Validation for this issue must remain narrow and boundary-focused before broader implementation begins.

At minimum, validation should prove:

- a reviewed Phase 30D design document exists for approval, execution, reconciliation, and coordination visibility in the operator console;
- the design explicitly states that approval is not a toggle, execution success is not reconciliation success, and mismatch must remain visible;
- the design keeps role-gating, backend authorization, lifecycle reread, and degraded-state handling explicit so AegisOps remains authoritative; and
- later implementation issues can build against one reviewed lifecycle and visibility contract instead of inventing page-local workflow semantics.

The narrowest first regression test for this issue is a documentation test that locks the Phase 30D boundary, lifecycle semantics, and authoritative reread contract in place before implementation expands around them.

## 13. Alignment and Non-Expansion Rules

`docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md` remains the normative source for the read-only shell, route, and adapter posture that Phase 30D extends without turning the browser into workflow authority.

`docs/phase-30c-bounded-write-actions-ui-boundary.md` remains the normative source for bounded task submission posture and for the rule that write-capable client behavior requires a separate reviewed contract.

`docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md` remains the normative source for mismatch visibility, lifecycle honesty, and the rule that operator convenience must not overwrite authoritative state.

`docs/response-action-safety-model.md` remains the normative source for approval binding, expiry, supersession, and the rule that approval decisions remain separate from execution attempts.

`docs/control-plane-state-model.md` remains the normative source for backend-owned lifecycle truth, authoritative record selection, and the requirement that reconciliation remains a first-class control-plane concern.

`docs/phase-26-first-coordination-substrate-and-non-authoritative-ticket-boundary.md` remains the normative source for the rule that coordination references are subordinate context rather than control-plane authority.

`docs/architecture.md` remains the normative source for the governing authority boundary in which AegisOps remains authoritative above detection, automation, execution, and coordination substrates.

Phase 30D therefore approves a reviewed UI contract for action-review inspection, bounded approval submission, explicit execution receipt summary, explicit reconciliation mismatch visibility, and subordinate coordination context only. It does not approve browser-owned workflow truth, approval-by-toggle shortcuts, substrate-owned approval decisions, or generic CRUD expansion.
