# AegisOps Phase 30 React-Admin Foundation and Read-Only Operator Console Boundary

## 1. Purpose

This document defines the reviewed Phase 30 boundary for a React-Admin-based operator console before implementation introduces a frontend shell, adapter, or read-only operator pages.

It supplements `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md`, `docs/auth-baseline.md`, `docs/control-plane-state-model.md`, `docs/response-action-safety-model.md`, `docs/automation-substrate-contract.md`, and `docs/architecture.md`.

This document defines UI-boundary, authentication, adapter, resource-mapping, and implementation-sequencing rules only. It does not approve write actions, approval decisions, optimistic updates, or substrate-first primary UI ownership.

## 2. Reviewed Phase 30 Boundary

Phase 30 introduces a thin React-Admin client for operator-facing navigation and inspection only.

The reviewed Phase 30 boundary is a shell and read-only presentation phase around the already-approved AegisOps operator path rather than a generic admin-console expansion.

AegisOps backend responses remain the sole authority source for queue, alert, case, evidence, provenance, advisory, action-review, and reconciliation truth.

React-Admin may provide list, show, layout, navigation, route handling, and read-only composition behavior, but it must not redefine workflow state semantics, synthesize authority from browser state, or promote generic CRUD assumptions into the control plane.

Phase 30 is split into two narrow slices:

- `Phase 30A` is the reviewed shell, authentication boundary, route protection, role-aware navigation, and adapter groundwork for read-only operator inspection.
- `Phase 30B` is the reviewed first read-only operator pages that render already-approved operator concepts through the Phase 30A shell and adapter contract.

Phase 30 does not authorize:

- generic create, edit, delete, or bulk-mutation behavior because React-Admin exposes those concepts by default;
- write actions, approval decisions, or action execution from the browser shell;
- optimistic updates, speculative success banners, or client-owned lifecycle mutation;
- a substrate-first daily work surface that displaces AegisOps authority; or
- any UI-owned authority that could outrank control-plane records.

## 3. Thin React-Admin Client Ceiling

The React-Admin operator console must remain a thin React-Admin client above reviewed AegisOps interfaces rather than a new workflow authority layer.

The client ceiling is:

- route selection;
- role-aware navigation;
- read-only list and detail composition;
- bounded filter and sort controls over backend-approved query parameters;
- session-aware rendering through reviewed identity claims; and
- visual separation between authoritative anchor records and subordinate substrate detail.

The client ceiling explicitly excludes:

- local authority derivation from cached rows, optimistic state, or browser-only badges;
- generic resource mutation wiring such as create or edit forms merely because the framework supports them;
- direct calls from arbitrary pages to substrate APIs;
- direct trust in forwarded identity headers emitted by the browser; and
- workflow-local state machines that reinterpret approval, execution, or reconciliation truth.

If React-Admin convenience features conflict with AegisOps authority rules, the convenience feature must be disabled or wrapped rather than weakening the control-plane boundary.

## 4. Authentik and OIDC Authentication Boundary

Phase 30 authentication must preserve the reviewed reverse-proxy and identity-provider boundary already described in `docs/auth-baseline.md`.

Authentik and OIDC Authentication Boundary rules are:

- Authentik remains the preferred reviewed human IdP boundary when a concrete provider is needed.
- OIDC-backed login must terminate at the approved reverse-proxy and backend-controlled session boundary rather than letting the browser invent or normalize identity.
- `authProvider` may only consume reviewed session and role information that the backend has already authenticated and normalized.
- `authProvider` must fail closed when session, provider, subject, or role signals are missing, malformed, expired, or inconsistent with the reviewed backend session.
- protected routes must redirect unauthenticated or unauthorized users to the reviewed login path or a reviewed forbidden path instead of rendering partial operator data.
- login must initiate the reviewed OIDC sign-in path only and must not accept placeholder credentials, test secrets, or client-supplied identity assertions as valid authority.
- logout must clear the reviewed backend session and remove any browser-cached operator data derived from that session.
- role-aware navigation must be derived from reviewed backend role assertions rather than inferred from route naming, hidden links, or client feature flags.

The minimum reviewed role expectations remain aligned to `Analyst`, `Approver`, and `Platform Administrator`.

Phase 30 may hide or show navigation entries by role, but role-aware navigation must not be treated as the primary authorization boundary. Every protected route and every backend read must still enforce the reviewed role contract server-side.

## 5. Adapter and `dataProvider` Contract

Phase 30 requires an adapter or BFF between React-Admin conventions and task-oriented AegisOps endpoints.

Adapter and `dataProvider` Contract rules are:

- the adapter maps task-oriented AegisOps responses into React-Admin resource and route semantics and must not force generic create or edit behavior;
- the adapter must preserve authoritative identifiers, authoritative status fields, timestamps, and linkage references exactly as emitted by the backend;
- the adapter may normalize shape for rendering consistency, but it must not reinterpret approval state, action-review state, provenance, or reconciliation outcomes;
- the adapter must keep backend-owned pagination, filtering, and sorting as the authority source;
- the adapter must pass through authoritative read failures, forbidden outcomes, and missing-prerequisite errors instead of degrading to empty-success behavior;
- the adapter must not silently fill missing auth, tenant, repository, issue, or environment context from route shape or client guesses; and
- the adapter must disable unsupported React-Admin mutation verbs rather than mapping them to placeholder no-ops.

The reviewed `dataProvider` surface for Phase 30 is read-only. Supported operations are limited to read semantics such as `getList`, `getOne`, and reviewed reference lookups that remain subordinate to backend authority.

The adapter contract must reject or omit:

- `create`;
- `update`;
- `updateMany`;
- `delete`;
- `deleteMany`; and
- any synthetic bulk action that would imply write ownership in the UI shell.

If a future page requires a write path, that path needs a separate reviewed contract instead of piggybacking on the Phase 30 read-only adapter.

## 6. Resource and Route Mapping

Phase 30 uses React-Admin resource and route semantics as a presentation convenience only.

Those resource and route semantics must map to AegisOps operator concepts rather than to generic admin entities.

The approved initial read-only operator concepts are:

- `queue` for the reviewed skim surface and operator work selection;
- `alert` for authoritative alert inspection;
- `case` for authoritative case coordination and state inspection;
- `provenance` for evidence lineage, anchor linkage, and supporting traceability views;
- `readiness` for reviewed runtime and optional-extension readiness inspection;
- `reconciliation` for authoritative reconciliation status and mismatch visibility;
- `advisory output` for bounded advisory review anchored to reviewed records; and
- `action review` for inspection of action-request, approval, delegation, execution, and related review state without authorizing mutation.

React-Admin resources may be named or grouped to support routing, but the underlying page semantics must stay task-oriented:

- queue pages are selection and skim pages, not generic inbox administration;
- alert and case pages are authoritative inspection surfaces, not free-form record editors;
- provenance pages are evidence-lineage views, not substrate-console replacements;
- readiness pages are reviewed status views, not hidden ops consoles for internal services;
- reconciliation pages are mismatch-preserving views, not workflow-success dashboards;
- advisory output pages are citation-first review surfaces, not free-form assistant chat; and
- action review pages are inspection-only until a later reviewed write contract exists.

## 7. Authoritative and Subordinate Presentation Split

Phase 30 must make the visual and semantic split between authoritative anchor records and subordinate Wazuh or Shuffle or optional-context detail explicit.

Authoritative anchor records are the AegisOps-owned records that carry the approved truth for queue state, alert state, case state, evidence linkage, recommendation lineage, action review, approval review, execution review, and reconciliation review.

Subordinate detail includes upstream or downstream context such as subordinate Wazuh alert payloads, Shuffle workflow receipts, optional enrichment, and other secondary context that may assist the operator without becoming the authority source.

Presentation rules are:

- authoritative anchor records must appear as the primary header, status, identity, and lifecycle context on each page;
- subordinate Wazuh, Shuffle, or optional detail must be visually secondary and clearly labeled as supporting context;
- subordinate detail may explain or corroborate, but it must not overwrite authoritative status text, outcome badges, or record selection;
- when authoritative and subordinate views disagree, the UI must preserve the disagreement and keep the AegisOps-owned record as the controlling state;
- optional-context absence, degradation, or delay must remain visible without blocking the authoritative record view; and
- advisory or subordinate lineage attached to one authoritative record must not be generalized to sibling or parent records without an explicit authoritative link.

This split is required because a React-Admin layout can otherwise make every panel look equivalent even when some panels represent derived or subordinate context only.

## 8. Read-Only Sequencing

The fixed reviewed Phase 30 implementation order is:

`shell and auth -> adapter and dataProvider -> read-only pages -> validation`

More specifically:

1. `shell and auth` comes first so protected routes, login, logout, and reviewed role handling exist before any operator data is rendered.
2. `adapter and dataProvider` comes second so the adapter and `dataProvider` integration are constrained to a reviewed read-only contract before page work begins.
3. `read-only pages` comes third so queue, alert, case, provenance, readiness, reconciliation, advisory output, and action review surfaces all implement against one reviewed contract instead of inventing page-local boundary rules.
4. `validation` comes last so tests can assert the reviewed boundary, role-gating expectations, route protection behavior, and authority split after the shell and pages are fixed.

Read-Only Sequencing is mandatory because page-first implementation would encourage route-local CRUD defaults, page-local auth shortcuts, and ad hoc authority decisions.

## 9. Validation Expectations

Phase 30 validation must stay narrow and boundary-focused before broader UI implementation starts.

At minimum, validation must prove:

- the reviewed design document exists and remains explicit about the React-Admin boundary;
- route protection behavior fails closed for missing or malformed session state;
- unsupported mutation verbs remain disabled at the adapter boundary;
- read-only pages render authoritative anchor records as primary state; and
- subordinate Wazuh, Shuffle, or optional-context detail remains visually and semantically secondary.

The narrowest first regression test for this issue is a documentation test that locks the reviewed boundary terms in place so follow-up implementation issues cannot invent their own contract ad hoc.

## 10. Alignment and Non-Expansion Rules

`docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md` remains the normative source for the approved operator workflow shape that Phase 30 renders rather than broadens.

`docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md` remains the normative source for review-state semantics, mismatch visibility, handoff visibility, and the rule that workflow-local status must not become the authoritative source of truth.

`docs/auth-baseline.md` remains the normative source for the reviewed identity-provider boundary, role separation, and fail-closed handling of missing identity signals.

`docs/control-plane-state-model.md` remains the normative source for authoritative lifecycle-bearing control-plane records.

`docs/response-action-safety-model.md` remains the normative source for approval-sensitive separation and for the rule that approval decisions do not collapse into UI convenience.

`docs/automation-substrate-contract.md` remains the normative source for subordinate automation-substrate identity, payload binding, and execution receipts.

`docs/architecture.md` remains the normative source for the rule that AegisOps owns policy-sensitive workflow truth and that external detection or automation substrates remain subordinate.

Phase 30 therefore approves a reviewed read-only operator console boundary only. It does not approve generic admin CRUD, browser-owned authority, substrate-owned truth, or write shortcuts dressed up as frontend productivity.
