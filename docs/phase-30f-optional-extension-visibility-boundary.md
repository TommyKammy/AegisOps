# AegisOps Phase 30F Optional-Extension Visibility Boundary

## 1. Purpose

This document defines the reviewed Phase 30F boundary for optional-extension visibility in the React-Admin operator console before implementation introduces shared optional-extension cards, badges, or subordinate-status sections across operator-facing pages.

It supplements `README.md`, `docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md`, `docs/phase-30e-assistant-advisory-integration-boundary.md`, `docs/phase-28-optional-endpoint-evidence-pack-boundary.md`, `docs/phase-29-reviewed-ml-shadow-mode-boundary.md`, `docs/phase-29-optional-suricata-evidence-pack-boundary.md`, `docs/control-plane-state-model.md`, and `docs/architecture.md`.

This document defines browser taxonomy, subordinate-context posture, optional-service visibility, and no-authority rendering rules only. It does not approve new optional adapters, endpoint or network execution flows, ML workflow expansion, assistant authority expansion, or any change that would turn optional-extension state into workflow truth.

## 2. Reviewed Phase 30F Boundary

Phase 30F introduces one reviewed browser contract for showing optional-extension posture without turning optional-extension state into authoritative AegisOps lifecycle truth.

The Reviewed Phase 30F Boundary is intentionally narrow:

- the browser may show optional-extension posture for the reviewed extension families already described in approved boundary documents;
- the browser may show one shared status taxonomy for `enabled`, `disabled-by-default`, `unavailable`, and `degraded`;
- the browser may show subordinate explanatory context for optional endpoint evidence, optional network evidence, ML shadow mode, assistant availability, and degraded optional services; and
- the browser must keep mainline AegisOps-owned records, lifecycle chips, and workflow outcomes visually primary over optional-extension interpretation.

Phase 30F remains a visibility surface rather than an authority surface, enablement surface, or workflow-decision surface.

Phase 30F does not authorize:

- optional-extension state as case truth, approval truth, execution truth, reconciliation truth, or readiness truth for the mainline control plane;
- browser-local enablement inference from route shape, package presence, container presence, or external service naming;
- new workflow families for endpoint, network, ML, or assistant paths beyond the already reviewed bounded slices; or
- hidden escalation from optional-service trouble into generic operator error when the mainline path is still operating as designed.

## 3. Shared Optional-Extension Status Taxonomy

The browser must use one shared status taxonomy for reviewed optional-extension visibility:

- `enabled` means the reviewed optional path is intentionally activated for the current runtime or anchored subject and the backend-owned status source reports that the subordinate path is available for its reviewed role;
- `disabled-by-default` means the reviewed optional path is intentionally not activated and its absence is expected behavior rather than an operator error;
- `unavailable` means the reviewed optional path is not currently available to the runtime even though the browser can identify the extension family and explain the missing prerequisite, binding, provider, adapter, or reviewed service dependency; and
- `degraded` means the reviewed optional path is activated or expected, but the backend-owned status source reports partial, stale, lagging, or missing subordinate reads, receipts, refreshes, or supporting service health.

These terms are not interchangeable.

`disabled-by-default` is not an outage.

`unavailable` is not equivalent to intentionally disabled.

`degraded` is not equivalent to absent data.

If required enablement, provenance, or health signals are missing, malformed, or internally inconsistent, the browser must fail closed and render `unavailable` or `degraded` rather than guessing `enabled`.

## 4. Extension-Family Interpretation Rules

Phase 30F covers five reviewed optional-extension families:

- `assistant availability posture` for the bounded reviewed assistant and advisory path described in Phase 30E;
- `optional endpoint evidence` for the Phase 28 subordinate endpoint evidence-pack path;
- `optional network evidence` for the Phase 29 subordinate Suricata evidence-pack path;
- `ML shadow status` for the Phase 29 reviewed ML shadow-only path; and
- `degraded optional services` for reviewed optional-service trouble that affects subordinate context visibility without becoming mainline workflow authority.

Family-specific interpretation rules are:

- `assistant availability posture` may render `enabled`, `unavailable`, or `degraded` when the reviewed assistant path exists for the current runtime, but it must remain explicitly advisory-only and non-authoritative even when healthy;
- `optional endpoint evidence` should default to `disabled-by-default` until a reviewed endpoint evidence request is explicitly active for an already anchored case or evidence chain;
- `optional network evidence` should default to `disabled-by-default` until the reviewed subordinate network evidence path is intentionally activated for the bounded Phase 29 slice;
- `ML shadow status` should default to `disabled-by-default` until the reviewed shadow-only path is intentionally activated; and
- `degraded optional services` may appear only as subordinate visibility about already reviewed optional families and must not create a synthetic sixth authority-bearing workflow state.

The browser must not collapse family-specific meaning into a generic "missing data" badge.

## 5. Approved Surface Contract

The approved Phase 30F surface contract is limited to four operator-facing areas:

- `optional-extension summary section` as the shared list or card group that shows the reviewed taxonomy and a short explanation for each optional family;
- `family-specific detail panel` as the bounded supporting view that explains why a family is `enabled`, `disabled-by-default`, `unavailable`, or `degraded`;
- `mainline expectation note` as the explicit explanation of what the operator should expect when an optional path is absent, intentionally disabled, or partially unavailable; and
- `degraded optional-service visibility` as the required rendering of lagging, stale, or partially unavailable subordinate optional services without rewriting authoritative workflow outcomes.

Each area must render from backend-owned optional-extension interpretation rather than client-local guesses.

The browser may reuse this contract on readiness pages, authoritative detail pages, or advisory pages, but it must preserve the same shared terminology and subordinate posture each time.

## 6. Visual and Semantic Separation Rules

Phase 30F must keep optional-extension visibility visually and semantically separate from authoritative AegisOps-owned records.

The browser must make this split explicit:

- authoritative record headers, lifecycle chips, identifiers, and workflow outcomes must remain primary;
- optional-extension sections must be labeled as subordinate optional context or optional extension visibility;
- optional-extension badges must not reuse the same visual posture as case state, approval state, execution outcome, reconciliation outcome, or other authoritative lifecycle markers;
- subordinate optional detail may explain availability or trouble, but it must not overwrite authoritative status text, selection state, or record ordering; and
- if optional-extension visibility conflicts with an authoritative lifecycle record, the authoritative lifecycle record remains controlling and the optional surface must preserve the mismatch rather than normalize it away.

Optional-extension cards must not look like required platform dependency failures unless the reviewed backend contract explicitly says the mainline path is blocked.

Phase 30F therefore requires a visible distinction between:

- mainline AegisOps-owned truth; and
- subordinate optional context.

## 7. Mainline-Expected-Behavior Rendering

When an optional path is absent, intentionally disabled, or unavailable, the browser must explain mainline expected behavior explicitly.

Minimum reviewed behavior is:

- `disabled-by-default` must explain that the reviewed runtime is operating on the mainline path without that optional extension and that this is an expected posture;
- `unavailable` must explain which reviewed prerequisite or binding is missing without implying that authoritative queue, case, approval, execution, or reconciliation state has therefore failed;
- `degraded` must explain that subordinate optional context may be incomplete, stale, or delayed while keeping mainline workflow truth separate; and
- `enabled` must explain the reviewed optional role and keep clear that the extension remains subordinate even when healthy.

The browser must not present optional extension absence as a hidden operator mistake, a silent empty state, or a first-boot requirement that outranks the approved mainline architecture.

## 8. Browser Show and Prohibited Behavior

The browser may show:

- one shared optional-extension taxonomy across readiness, case detail, advisory detail, or other reviewed inspection pages;
- per-family reason text that states whether the path is optional, disabled by default, unavailable because of a missing prerequisite, or degraded because of partial service trouble;
- links back to the authoritative anchor record or reviewed boundary document family that the optional status supports; and
- explicit statements that optional endpoint, network, ML shadow, and assistant surfaces remain subordinate to AegisOps-owned records.

The browser must not:

- infer `enabled` from package installation, sidecar presence, route exposure, cached client state, or operator expectation alone;
- present `disabled-by-default`, `unavailable`, and `degraded` as one generic warning state;
- present optional-extension badges as if they were authoritative lifecycle outcomes;
- imply that optional-service degradation changes approval, execution, reconciliation, or case state by itself;
- widen one optional family status into sibling records, broader lineage, or platform-global truth without an explicit backend-owned binding; or
- hide the mainline path explanation when optional context is absent.

## 9. Safe Implementation Sequence

Safe implementation sequence for Phase 30F is:

1. shared taxonomy and wording
2. summary section and family cards
3. mainline expectation notes and degraded-service messaging
4. validation

More specifically:

1. `shared taxonomy and wording` comes first so every reviewed page uses the same meaning for `enabled`, `disabled-by-default`, `unavailable`, and `degraded`.
2. `summary section and family cards` comes second so the browser has one subordinate optional-context pattern instead of route-local badges with drifting semantics.
3. `mainline expectation notes and degraded-service messaging` comes third so absent or impaired optional paths do not get rendered as hidden operator errors or synthetic authority.
4. `validation` comes last so focused tests can lock the status taxonomy, subordinate-context posture, and non-authority split after the contract is fixed.

Safe implementation sequence is mandatory because page-first optional badges would otherwise encourage route-local status invention, authority drift, and generic missing-data handling.

## 10. Validation Expectations

Validation for this issue must remain narrow and boundary-focused before broader implementation begins.

At minimum, validation should prove:

- a reviewed Phase 30F design document exists for optional-extension visibility boundary, shared taxonomy, family-specific posture, and subordinate-context rendering;
- the design makes `enabled`, `disabled-by-default`, `unavailable`, and `degraded` explicit rather than collapsing them into generic missing-data semantics;
- the design keeps optional-extension visibility visually and semantically separate from authoritative workflow truth; and
- later implementation issues can build consistent cards, sections, route messaging, and tests without reopening the trust boundary.

The narrowest first regression test for this issue is a documentation test that locks the optional-extension visibility boundary, shared status taxonomy, and subordinate-context posture in place before broader UI work begins.

## 11. Alignment and Non-Expansion Rules

`README.md` remains the normative source for the high-level optional extension operability model and mainline guarantee.

`docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md` remains the normative source for the thin React-Admin shell, read-only adapter posture, and authoritative-versus-subordinate presentation split that Phase 30F extends.

`docs/phase-30e-assistant-advisory-integration-boundary.md` remains the normative source for assistant citation posture, no-authority semantics, and assistant-specific detail rendering.

`docs/phase-28-optional-endpoint-evidence-pack-boundary.md` remains the normative source for endpoint evidence-pack enablement, scope, provenance, and fail-closed rules.

`docs/phase-29-reviewed-ml-shadow-mode-boundary.md` remains the normative source for ML shadow-only posture and non-authoritative review scope.

`docs/phase-29-optional-suricata-evidence-pack-boundary.md` remains the normative source for optional network evidence scope, provenance, and fail-closed rules.

`docs/control-plane-state-model.md` remains the normative source for authoritative lifecycle-bearing control-plane records.

`docs/architecture.md` remains the normative source for the thesis that AegisOps owns policy-sensitive workflow truth above subordinate optional substrates and supporting services.

Phase 30F therefore approves one reviewed browser contract for optional-extension visibility only. It does not approve new optional adapters, browser-owned workflow truth, hidden required dependencies, assistant authority expansion, endpoint or network scope expansion, ML promotion out of shadow mode, or generic operational error semantics that would redefine the mainline architecture.
