# AegisOps Phase 30C Bounded Write Actions UI Boundary

## 1. Purpose

This document defines the reviewed Phase 30C boundary for bounded write actions in the React-Admin operator console before implementation introduces task forms, mutation clients, or browser-side workflow shortcuts.

It supplements `docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md`, `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md`, `docs/control-plane-state-model.md`, `docs/response-action-safety-model.md`, and `docs/architecture.md`.

This document defines the bounded write actions posture, task-form rules, authoritative re-read contract, role and authorization posture, degraded-state handling, and implementation sequence only. It does not approve approval decisions, execution controls, reconciliation mutation, substrate-owned forms, or assistant-owned authority.

## 2. Reviewed Phase 30C Boundary

Phase 30C introduces bounded write actions as a task-oriented client above already reviewed AegisOps write paths.

The Reviewed Phase 30C Boundary is intentionally narrow:

- the browser may collect reviewed operator intent for bounded write actions;
- the browser may show task forms, actor and provenance visibility, and confirmation affordances for one reviewed task at a time; and
- the browser must submit that intent to reviewed backend endpoints and then recover authoritative state from the backend before presenting the post-submit result.

Phase 30C only works safely when the browser stays a task-oriented client and must not inherit generic create and edit semantics from React-Admin.

Generic CRUD fallback remains prohibited.

Phase 30C does not authorize browser-owned workflow truth, optimistic authority shortcuts, synthetic success derived from local state, or mutation contracts invented page by page.

## 3. Approved Bounded Write-Action Ceiling

Approved bounded write-action ceiling for this phase is limited to:

- alert-to-case promotion;
- case observation;
- case lead;
- case recommendation;
- reviewed action-request creation; and
- manual fallback or escalation notes.

These bounded write actions are task-oriented casework steps, not generic record administration.

Each action must remain tied to one authoritative target record, one reviewed operator intent, one reviewed role context, and one backend-enforced authorization decision.

Phase 30C does not approve:

- generic create, edit, delete, or bulk mutation behavior because React-Admin exposes those concepts by default;
- approval decisions, execution controls, or reconciliation mutation from the browser;
- substrate-owned forms that bypass AegisOps task binding;
- assistant-authored submissions or assistant-owned authority; or
- any broader workflow step outside the Approved bounded write-action ceiling.

## 4. Task-Form Posture

Task forms are the required UI posture for all bounded write actions in this phase.

Task forms must:

- stay action-specific instead of exposing free-form entity editors;
- identify the authoritative anchor record and the exact task being requested;
- show actor and provenance visibility before submit, including the reviewed case, alert, recommendation, or action-request binding that the task depends on;
- show the current authoritative lifecycle state that the operator is acting on;
- present confirmation affordances when the operator is about to create or append reviewed workflow state; and
- fail closed when binding, actor, provenance, or prerequisite review state is missing, stale, or not trusted.

Task forms must not:

- present browser-owned defaults as if they were authoritative workflow truth;
- silently fill missing case, tenant, repository, issue, or environment binding from route shape or client guesses;
- let page-local code reinterpret lifecycle state outside backend rules; or
- preserve stale hidden fields after the authoritative target record has changed.

## 5. Write Client Boundary and React-Admin Posture

Shared write-action clients may exist, but they must live in a bounded task-action layer rather than re-enabling generic React-Admin mutations on the read-oriented `dataProvider`.

The reviewed client split is:

- `dataProvider` remains the read contract and must not become the default mutation surface;
- shared write-action clients live beside the `dataProvider` in a separate bounded task-action layer; and
- each task-action helper must call a reviewed backend endpoint whose semantics are already defined by AegisOps records and authorization rules.

Generic React-Admin mutations stay disabled by default.

That means Phase 30C must reject or avoid:

- framework-default `create`, `update`, `updateMany`, `delete`, and `deleteMany`;
- resource-level mutation screens generated from entity shape alone; and
- page-local shortcuts that map a generic mutation verb to a workflow task without a reviewed contract.

If a bounded write action cannot fit through the bounded task-action layer without weakening backend semantics, the action is not approved for this phase.

## 6. Role-Gating and Authorization Posture

Role-gating and route protection are required for discoverability control, but reviewed backend authorization remains primary.

Role-gating rules are:

- route protection must block access to write-capable pages or drawers when the reviewed session is absent, malformed, expired, or unauthorized;
- role-gating may suppress controls the current role cannot use, but hidden controls are not an authorization decision;
- reviewed backend authorization must still evaluate every bounded write request even when the UI exposed the control; and
- unauthorized, forbidden, or unbound requests must fail closed and remain visible to the operator as authorization outcomes rather than empty-state success.

The browser may help the operator avoid obviously unavailable tasks, but it must not become the source of truth for whether a write was allowed.

## 7. Authoritative Re-Read and Refresh Contract

Every Phase 30C submission requires an authoritative re-read.

The authoritative refresh sequence is:

1. render the task form from the current authoritative record snapshot;
2. submit one bounded request to the reviewed backend endpoint;
3. treat the mutation response as an acknowledgment or error carrier, not as standalone workflow truth;
4. perform an authoritative re-read of the mutated record family and any directly affected task surface; and
5. render the post-submit state from that authoritative refresh result.

Authoritative re-read is mandatory because the control plane, not the browser, owns lifecycle truth, actor binding, authorization outcomes, and conflict handling.

The browser must not treat the initial submit response, a local patch, or a cached optimistic row as sufficient proof of durable workflow state.

If the authoritative re-read fails, the UI must preserve uncertainty explicitly rather than implying success from the prior request.

## 8. Error, Conflict, and Degraded-State Visibility

Phase 30C must keep degraded, unauthorized, stale, conflict, and failed-submit outcomes explicit.

Minimum visibility expectations are:

- degraded: the request path or refresh path is partially unavailable, so the UI must preserve the last known authoritative state and mark the write result as unresolved;
- unauthorized: the operator saw a control or deep-linked a route, but reviewed backend authorization denied the request and the denial must stay visible;
- stale: the form was built from an outdated authoritative record and the operator must refresh against current state before retrying;
- conflict: the backend accepted neither the old assumption nor an unsafe overwrite, and the UI must preserve the conflict rather than auto-merging browser state; and
- failed-submit: transport, validation, or server failure prevented a clean bounded write and the UI must not imply that durable workflow state changed.

These outcomes must not collapse into generic toast success, silent retries that hide lifecycle truth, or convenience banners that outrank the authoritative record chain.

## 9. Actor, Provenance, and Binding Expectations

Bounded write actions must keep actor, provenance visibility, and binding signals primary before and after submit.

At minimum, the operator should be able to see:

- which authoritative record is being acted on;
- which reviewed actor identity and role context is attempting the action;
- which provenance, recommendation, or review context the action is bound to; and
- which backend-owned lifecycle or authorization rule accepted, rejected, or blocked the task.

The browser must not widen advisory lineage or same-parent context beyond the directly linked authoritative record.

If a recommendation, evidence snippet, or fallback note attaches to one record only, the task form and the post-submit refresh must not silently generalize that context to sibling records without an explicit authoritative link.

## 10. Safe Implementation Sequence

Safe implementation sequence for Phase 30C is:

1. shared primitives
2. core casework actions
3. action-request and fallback flows
4. validation

More specifically:

1. shared primitives come first so route protection, form-shell state, confirmation affordances, bounded task-action clients, and authoritative refresh helpers are defined once.
2. core casework actions come second so alert-to-case promotion, case observation, case lead, and case recommendation all adopt one reviewed posture instead of inventing page-local mutation behavior.
3. action-request and fallback flows come third so reviewed action-request creation and manual fallback or escalation notes reuse the same bounded task contract without widening into approval or execution authority.
4. validation comes last so tests can prove the bounded write contract, authoritative re-read behavior, and degraded-state handling after the implementation path is fixed.

Safe implementation sequence is mandatory because action-first implementation would encourage per-page mutation helpers, CRUD fallback, and inconsistent post-submit truth handling.

## 11. Validation Expectations

Validation for this issue must remain narrow and contract-focused before broader UI implementation begins.

At minimum, validation should prove:

- a reviewed Phase 30C design document exists for bounded write actions, task forms, authoritative re-read behavior, and degraded-state handling;
- the design explicitly says the browser must not inherit generic create and edit semantics from React-Admin;
- Generic CRUD fallback remains prohibited and Generic React-Admin mutations stay disabled by default;
- the design keeps reviewed backend authorization, role-gating, route protection, actor and provenance visibility, and the authoritative refresh sequence explicit; and
- later implementation issues can execute against one reviewed bounded task-action layer instead of inventing local mutation behavior ad hoc.

The narrowest first regression test for this issue is a documentation test that locks the write-action ceiling, task-form posture, and authoritative refresh contract in place before implementation expands around them.

## 12. Alignment and Non-Expansion Rules

`docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md` remains the normative source for the read-only shell, route, and adapter boundary that Phase 30C extends without broadening into generic admin CRUD.

`docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md` remains the normative source for the operator workflow shape that bounded write actions must serve rather than redefine.

`docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md` remains the normative source for explicit mismatch visibility, lifecycle honesty, and the rule that operator-facing convenience must not replace authoritative truth.

`docs/control-plane-state-model.md` remains the normative source for lifecycle-bearing authoritative records and the requirement that the browser re-read those records instead of inventing state locally.

`docs/response-action-safety-model.md` remains the normative source for approval-sensitive workflow separation and the rule that reviewed action-request creation does not imply approval decisions or execution controls.

`docs/architecture.md` remains the normative source for the authority boundary where AegisOps owns policy-sensitive workflow truth above subordinate substrates.

Phase 30C therefore approves bounded write actions only as a reviewed task-oriented client over existing AegisOps write paths. It does not approve browser-owned workflow truth, optimistic authority shortcuts, approval decisions, execution controls, reconciliation mutation, substrate-owned forms, or assistant-owned authority.
