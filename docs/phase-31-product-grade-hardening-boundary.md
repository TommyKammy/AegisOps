# AegisOps Phase 31 Product-Grade Hardening Boundary

## 1. Purpose

This document defines the reviewed Phase 31 product-grade hardening boundary for the React-Admin operator console before implementation tightens browser semantics, deep-link handling, shell-state rendering, and client-event logging behavior across reviewed routes and pages.

It supplements `docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md`, `docs/phase-30d-approval-execution-reconciliation-ui-boundary.md`, `docs/phase-30e-assistant-advisory-integration-boundary.md`, `docs/phase-30f-optional-extension-visibility-boundary.md`, `docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md`, `docs/phase-21-production-like-hardening-boundary-and-sequence.md`, `docs/auth-baseline.md`, `docs/control-plane-state-model.md`, and `docs/architecture.md`.

This document defines browser boundary, deep-link policy, access posture, shell-state taxonomy, client-event logging constraints, and product-grade browser guardrails only. It does not approve backend auth-boundary changes, Playwright wiring, dev-only local mock access, generic CRUD expansion, or browser-owned workflow authority.

## 2. Reviewed Phase 31 Boundary

Phase 31 introduces one reviewed hardening contract for the operator browser shell now that the reviewed routes and pages are visible enough to inspect directly.

The Reviewed Phase 31 Boundary is intentionally narrow:

- the browser may enforce one reviewed route, menu, and page-level access posture around backend-authenticated session state and reviewed role claims;
- the browser may preserve one reviewed deep-link policy for login return paths and record-bound operator routes;
- the browser may render explicit operator-facing unauthorized, forbidden, invalid-session, empty, error, and degraded states across the shell;
- the browser may emit bounded client-event logging for browser-side navigation and rendering outcomes that remain subordinate to backend authority; and
- the browser must keep all workflow truth, authorization truth, lifecycle truth, and audit truth backend-authoritative.

Phase 31 remains a product-grade shell-hardening phase rather than a browser-authority phase, mock-access phase, or generic application-expansion phase.

Phase 31 does not authorize:

- browser-owned authorization truth;
- client-local inference of tenant, repository, issue, record, or environment binding;
- deep-link expansion that bypasses reviewed session or role checks;
- raw evidence, advisory, or secret-bearing client telemetry;
- generic CRUD expansion; or
- dev-only mock identities or placeholder credentials presented as approved access behavior.

## 3. Access Behavior and Gating Contract

Phase 31 must define one reviewed access contract across route selection, menu visibility, and page rendering.

The reviewed access contract is:

- `route-gating` blocks protected shell routes until the reviewed backend session has been revalidated;
- `menu-gating` is a discoverability control that may hide routes the current reviewed role should not browse toward casually;
- `page-gating` is the final browser-side rendering check for route-specific surfaces after session and route binding are known; and
- `backend authorization` remains the enforcement boundary for every protected read and every write-capable follow-on issue.

Menu visibility must not be treated as proof that a route is allowed.

Route visibility must not be treated as proof that a backend read is allowed.

If route-gating, page-gating, and backend authorization disagree, backend authorization remains authoritative and the browser must preserve that denial explicitly.

The approved minimum role posture remains aligned to `Analyst`, `Approver`, and `Platform Administrator`.

Phase 31 may keep route and menu affordances role-aware, but it must not infer access from route naming, cached shell state, or client feature flags.

## 4. Reviewed Deep-Link Policy

Deep-link handling must remain bounded, fail closed, and anchored to reviewed route families.

The reviewed deep-link policy is:

- the browser may preserve a reviewed `returnTo` path for the login handoff only when the target remains inside the reviewed operator base path and resolves to a reviewed route family;
- the browser may deep-link to record-bound pages only when authoritative identifiers and route bindings are present and internally consistent;
- the browser must reject or normalize malformed, cross-scope, or open-redirect-style deep links rather than preserving them optimistically;
- the browser must not infer missing record family, record id, or approval context from nearby route segments, menu state, or cached prior navigation; and
- the browser must re-run the normal reviewed session and role checks after login, refresh, reload, and back or forward navigation before protected content renders.

The approved route families for deep-link review are:

- queue and operator overview entry routes;
- alert detail routes bound to one authoritative alert identifier;
- case detail routes bound to one authoritative case identifier;
- provenance detail routes bound to one authoritative provenance family and record identifier;
- assistant advisory routes bound to one authoritative record family and record identifier;
- action-review routes bound to one authoritative action-request identifier; and
- reviewed readiness or reconciliation routes that do not rely on guessed sibling-record context.

Deep links are convenience entrypoints only.

They must not become a substitute for authoritative backend binding or a way to widen one record context into sibling or parent scope.

## 5. Shell State and Operator UX Contract

Phase 31 must define one shared shell-state taxonomy so route bodies and page components do not invent ad hoc browser semantics.

The minimum reviewed shell states are:

- `unauthorized` when no reviewed authenticated session is available and the browser must route the operator to the reviewed login path;
- `forbidden` when the session is authenticated but the reviewed role contract does not permit shell access or route access;
- `invalid-session` when the backend auth response is malformed, missing reviewed claims, expired, or internally inconsistent;
- `empty` when the reviewed route loaded correctly but the authoritative backend read returned an allowed no-data outcome for the current scope;
- `error` when the reviewed backend read failed in a way that does not preserve safe degraded inspection for the current route; and
- `degraded` when the operator may still inspect authoritative anchor records but one or more subordinate reads, refreshes, or supporting sections are partially unavailable, stale, or lagging.

These states are not interchangeable.

`unauthorized` is not `forbidden`.

`invalid-session` is not a generic error.

`empty` is not silent success for a failed read.

`degraded` is not equivalent to workflow failure.

If prerequisite auth, binding, or authoritative read signals are missing or malformed, the browser must fail closed into `unauthorized`, `forbidden`, `invalid-session`, or `error` instead of downgrading the condition into `empty`.

## 6. State-Specific Rendering Rules

Phase 31 must keep operator-facing rendering semantics explicit across the shell.

Minimum reviewed rendering rules are:

- `unauthorized` routes the operator to the reviewed login path and may show the bounded reviewed return path without exposing protected content;
- `forbidden` explains that the reviewed session is authenticated but lacks the required reviewed role posture and must not pretend the page is merely empty;
- `invalid-session` blocks the shell until a reviewed session is re-established and must not continue rendering cached protected data;
- `empty` explains the current reviewed scope and confirms that no authoritative data is available for that scope rather than implying the route failed;
- `error` preserves that the current route could not complete its required authoritative read and must not substitute guessed content; and
- `degraded` keeps the authoritative anchor record or approved mainline shell context visible while labeling subordinate sections as incomplete, stale, or unavailable.

State rendering must also preserve one operator UX contract:

- authoritative AegisOps-owned records remain primary over subordinate context, optional extensions, assistant output, coordination references, and workflow receipts;
- the shell must show the operator what remains safe to inspect and what remains blocked rather than hiding uncertainty behind generic banners;
- recoverable browser actions may offer reviewed retry or re-auth affordances, but those affordances must not imply that the browser can repair backend authority locally; and
- page-local copy, cards, or chips must reuse the shared state meanings instead of redefining them per route.

## 7. Browser Convenience Surfaces Versus Backend-Authoritative Truth

Phase 31 must make the browser contract explicit about which surfaces are convenience rendering and which truths remain backend-authoritative.

The browser may own convenience behavior such as:

- route selection;
- menu visibility;
- loading indicators;
- bounded return-path preservation;
- focus, retry, and reload affordances;
- layout composition; and
- subordinate degraded-state messaging.

The backend remains authoritative for:

- identity and role claims;
- route scope and record binding;
- alert, case, approval, execution, reconciliation, readiness, and advisory truth;
- audit records and operator-attribution truth; and
- the final meaning of allowed, forbidden, missing, unresolved, or degraded workflow outcomes.

The browser must not reinterpret backend lifecycle or authorization outcomes into smoother local success semantics.

The browser must not treat cached rows, prior route history, menu visibility, or optimistic status chips as authoritative workflow truth.

## 8. Client-Event Logging Boundary

Client-event logging in Phase 31 must remain audit-friendly, privacy-bounded, and explicitly subordinate to backend authority.

The browser may emit reviewed client events for:

- route entry and route denial outcomes;
- login redirect initiation and post-login return-path outcomes;
- explicit operator retry, refresh, or logout actions;
- transitions into `unauthorized`, `forbidden`, `invalid-session`, `empty`, `error`, or `degraded` shell states; and
- bounded page-performance timing for reviewed route families and reviewed data-load classes.

The browser must not emit:

- raw session tokens, forwarded headers, secret values, or placeholder credentials;
- full evidence payloads, assistant prompt bodies, advisory prose, substrate receipts, or other over-broad record content;
- guessed tenant, repository, case, alert, action, or environment linkage that was not already confirmed by authoritative backend binding; or
- browser-local audit conclusions that imply the client log is the system of record for operator action truth.

Client-event logging may support correlation and browser troubleshooting, but backend audit records remain authoritative for authentication, authorization, approval, execution, and reconciliation history.

## 9. Product-Grade Browser Guardrails

Phase 31 must define hardening guardrails for caching, refetch, performance, and fixed theming without widening the browser into workflow authority.

The reviewed browser guardrails are:

- `caching and session scope`: protected data caches remain scoped to one reviewed session and must be cleared on logout, invalid-session handling, or reviewed identity change;
- `authoritative refetch`: refresh after login return, explicit retry, and later write-capable follow-on work must rely on authoritative re-read rather than local status patching;
- `performance posture`: loading, retry, and render optimizations may reduce operator friction but must not suppress reviewed denied, degraded, or unresolved states;
- `fixed theming decisions`: shell theming may be standardized for product consistency, but theme choices must not become a second channel for lifecycle truth, role authority, or hidden severity signaling; and
- `browser semantics`: reload, refresh, and back or forward navigation must preserve the same fail-closed access checks and route-binding checks as first navigation.

Phase 31 does not approve:

- offline-first workflow behavior;
- browser-local draft authority for protected workflow state;
- persistent cross-session caching of protected operator data;
- route-local retry loops that hide repeated backend denial or failure; or
- per-role or per-environment theming semantics that imply authority or approval state outside reviewed labels and backend data.

## 10. Safe Implementation Sequence

Safe implementation sequence for Phase 31 is:

1. shared shell-state taxonomy and copy
2. deep-link normalization and return-path policy
3. route, menu, and page-level gating alignment
4. bounded client-event logging
5. caching, refetch, and fixed-theme guardrails
6. validation

More specifically:

1. `shared shell-state taxonomy and copy` comes first so later page changes inherit one reviewed meaning for unauthorized, forbidden, invalid-session, empty, error, and degraded.
2. `deep-link normalization and return-path policy` comes second so login handoff and record-bound route entry stay fail-closed before broader browser polish lands.
3. `route, menu, and page-level gating alignment` comes third so route families build against one reviewed access contract instead of route-local shortcuts.
4. `bounded client-event logging` comes fourth so browser telemetry reflects already-reviewed states and route outcomes instead of inventing its own audit semantics.
5. `caching, refetch, and fixed-theme guardrails` come fifth so product-grade browser polish stays subordinate to the reviewed authority boundary.
6. `validation` comes last so focused doc and route tests can lock the contract after the state taxonomy and guardrails are explicit.

Safe implementation sequence is mandatory because page-local hardening would otherwise drift into ad hoc deep-link rules, route-specific error semantics, and browser-local audit behavior.

## 11. Validation Expectations

Validation for this issue must remain narrow and boundary-focused before broader implementation begins.

At minimum, validation should prove:

- a reviewed Phase 31 design document exists for the product-grade hardening boundary, reviewed deep-link policy, shell-state taxonomy, client-event logging boundary, and browser guardrails;
- the design makes clear which states are browser-rendered convenience surfaces versus backend-authoritative workflow truth;
- the design keeps unauthorized, forbidden, invalid-session, empty, error, and degraded semantics explicit and non-interchangeable;
- the design keeps client-event logging subordinate to backend audit authority and blocks unsafe or over-broad data capture; and
- later implementation issues can tighten shell gating, fetch behavior, theming, and browser validation without reopening the trust boundary.

The narrowest first regression test for this issue is a documentation test that locks the Phase 31 hardening boundary, deep-link policy, shared shell-state taxonomy, and client-event logging limits in place before follow-on implementation broadens browser behavior.

## 12. Alignment and Non-Expansion Rules

`docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md` remains the normative source for the thin React-Admin shell, read-only posture, route protection, and authoritative-versus-subordinate presentation split that Phase 31 hardens.

`docs/phase-30d-approval-execution-reconciliation-ui-boundary.md` remains the normative source for lifecycle separation, action-review route semantics, and the rule that execution and reconciliation truth remain backend-authoritative.

`docs/phase-30e-assistant-advisory-integration-boundary.md` remains the normative source for advisory no-authority posture, route binding, and citation-first assistant rendering that Phase 31 must not weaken through browser polish.

`docs/phase-30f-optional-extension-visibility-boundary.md` remains the normative source for optional-extension degraded-state posture and subordinate optional-context semantics.

`docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md` remains the normative source for mismatch visibility, explicit workflow semantics, and the rule that operator convenience must not overwrite authoritative review state.

`docs/phase-21-production-like-hardening-boundary-and-sequence.md` remains the normative source for production-like hardening posture, reverse-proxy-first access assumptions, and fail-closed handling of missing identity or boundary signals.

`docs/auth-baseline.md` remains the normative source for reviewed human identity, role-claim, and fail-closed session requirements.

`docs/control-plane-state-model.md` remains the normative source for authoritative lifecycle-bearing records and backend-owned workflow truth.

`docs/architecture.md` remains the normative source for the product thesis that AegisOps is a governed SecOps control plane above subordinate detection, automation, and advisory surfaces.

Phase 31 therefore approves one reviewed browser hardening contract for access posture, deep-link handling, shell-state rendering, bounded client-event logging, and product-grade browser guardrails only. It does not approve backend auth-boundary changes, Playwright wiring, generic CRUD expansion, dev-only local mock access, or browser-owned workflow authority.
