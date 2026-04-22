# AegisOps Phase 30E Assistant and Advisory UI Boundary

## 1. Purpose

This document defines the reviewed Phase 30E boundary for assistant and advisory surfaces in the React-Admin operator console before implementation introduces operator-facing advisory detail pages, assistant context inspection panels, or recommendation-draft rendering.

It supplements `docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md`, `docs/phase-30c-bounded-write-actions-ui-boundary.md`, `docs/phase-30d-approval-execution-reconciliation-ui-boundary.md`, `docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md`, `docs/phase-15-identity-grounded-analyst-assistant-boundary.md`, `docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md`, `docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md`, `docs/control-plane-state-model.md`, and `docs/architecture.md`.

This document defines browser boundary, citation posture, ambiguity visibility, draft-versus-authoritative split, and no-authority semantics only. It does not approve new assistant workflow families, provider-selection logic, free-form chat, browser-owned authority, approval guidance, execution guidance, or reconciliation truth derived from assistant output.

## 2. Reviewed Phase 30E Boundary

Phase 30E introduces a reviewed operator surface for cited advisory output, assistant context inspection, bounded recommendation draft rendering, and unresolved or citation-failure visibility.

The Reviewed Phase 30E Boundary is intentionally narrow:

- the browser may show one advisory output detail anchored to one authoritative anchor record at a time;
- the browser may show one assistant context inspection view for the same authoritative record and its directly linked reviewed inputs;
- the browser may show one recommendation draft rendering when that draft already exists inside the reviewed advisory-output contract; and
- the browser must keep the assistant path citation-first, ambiguity-visible, unresolved-preserving, and explicitly non-authoritative.

Phase 30E remains a review surface rather than a chat surface, decision surface, or workflow-authority surface.

Phase 30E does not authorize:

- free-form assistant chat;
- browser-owned assistant workflow truth;
- approval suggestions presented as decisions;
- execution instructions presented as authorized action;
- reconciliation conclusions presented as final workflow truth; or
- generic CRUD expansion.

## 3. Approved Surface Contract

The approved Phase 30E surface contract is limited to four operator-facing areas:

- `advisory output detail` as the cited summary view for one reviewed output snapshot anchored to one authoritative record;
- `assistant context inspection` as the supporting inspection view of the reviewed records, linked evidence, and reviewed context identifiers that grounded that advisory output;
- `recommendation draft rendering` as the bounded rendering of already-reviewed draft next steps that remain proposals rather than decisions; and
- `unresolved and citation-failure visibility` as the required rendering of missing citations, conflicting context, ambiguity, degraded supporting reads, or unresolved output state.

Each area must stay anchored to the same authoritative anchor record and the same assistant context snapshot. The browser must not combine multiple advisory outputs, multiple context snapshots, or sibling record lineage into one synthetic assistant answer.

## 4. Citation-First Rendering Rules

Citation-first rendering is mandatory rather than optional polish.

Every advisory output detail must render:

- the cited summary first, with citations attached to every material claim;
- visible citation structure that lets the operator trace a claim back to reviewed record family, stable identifier, and linked reviewed context;
- unresolved questions and uncertainty flags alongside the cited summary rather than hidden behind expansion affordances; and
- recommendation draft rendering only after the cited summary and uncertainty posture are visible.

The browser must not render assistant prose as a clean supported answer when citations are absent, malformed, incomplete, or internally inconsistent.

If citation requirements fail, the browser must present a missing-citation failure state rather than a polished summary card.

## 5. Ambiguity, Conflict, and Unresolved Visibility

Phase 30E must keep conflicting context, ambiguity, and unresolved state explicit.

Minimum reviewed visibility is:

- `unresolved` remains a first-class outcome when reviewed grounding is incomplete, conflicting, or blocked by missing citation support;
- conflicting context must stay visible when reviewed records disagree on lifecycle state, identity, scope, ownership, or evidence-backed claims;
- identity ambiguity must remain visible when assistant context depends on alias-style metadata, same-name records, or unresolved lineage rather than stable identifiers and reviewed linkage;
- degraded supporting reads must remain visible when assistant context inspection cannot load all directly linked reviewed inputs; and
- recommendation draft rendering must remain visibly tentative when uncertainty flags or unresolved questions remain open.

The browser must not collapse ambiguity into cleaner prose, choose one conflicting reviewed record silently, or hide unresolved state because the advisory text sounds confident.

## 6. Draft-Versus-Authoritative Separation

Phase 30E must keep draft and authoritative state visually and semantically separate.

The authoritative anchor record remains the primary source for case state, alert state, recommendation lifecycle, approval state, execution state, and reconciliation truth.

Assistant and advisory surfaces are subordinate review aids that render from assistant context snapshot data.

The browser must make this split explicit:

- authoritative anchor record headers, lifecycle chips, and reviewed control-plane facts must appear separately from assistant content;
- recommendation draft card content must be labeled as draft guidance and must not visually resemble an approved decision or durable record mutation;
- cited advisory output must be labeled as non-authoritative and must remain subordinate to the authoritative anchor record;
- unresolved or degraded advisory output must not overwrite authoritative lifecycle text with a stronger assistant summary; and
- assistant context inspection must show supporting reviewed inputs as evidence for the advisory output, not as a second authority layer.

## 7. No-Authority Posture

The no-authority posture is mandatory.

Phase 30E must state and render that assistant output is non-authoritative.

The browser must not present assistant output as a final answer.

The browser must not present assistant output as an approved decision.

The browser must not present assistant output as an execution fact.

The browser must not present assistant output as a reconciliation fact.

The browser must not imply that a cited recommendation draft is already accepted, approved, executed, or reconciled merely because it is present on the page.

If assistant content and authoritative workflow state appear together, AegisOps-owned reviewed records remain authoritative and the no-authority posture must stay explicit.

## 8. Browser Show and Prohibited Behavior

The browser may show:

- one advisory output detail for one authoritative record family and record id;
- one assistant context panel for the same authoritative scope;
- cited summary, key observations, unresolved questions, citations, uncertainty flags, and recommendation draft card content from the reviewed advisory-output contract;
- missing-citation failure, ambiguity, conflicting context, unresolved, and degraded states; and
- direct links back to the authoritative anchor record detail page or directly linked reviewed inputs.

The browser must not:

- invent advisory output from local state or prompt text;
- infer record scope from route shape alone without authoritative record family and record id binding;
- widen one record's assistant context snapshot to sibling, parent, or same-parent records without an explicit authoritative link;
- render free-form assistant chat alongside reviewed advisory detail in a way that blurs the contract boundary;
- treat recommendation draft rendering as a substitute for reviewed recommendation lifecycle state; or
- present advisory content as if operator approval, execution receipt, or reconciliation outcome has already occurred.

## 9. Route, Binding, and Read Contract

Phase 30E must reuse the reviewed Phase 30 route-gating and adapter posture.

The advisory detail route must require an authoritative record family and record id binding before the page renders.

The assistant context panel must read from the same authoritative scope as the advisory detail route.

If route metadata, binding metadata, or authoritative identifiers are missing, malformed, or inconsistent, the route must fail closed instead of rendering a guessed assistant surface.

The browser must treat `/inspect-advisory-output` and directly linked authoritative detail reads as backend-owned authority sources. Client-local guesses, cached fragments, or prompt-carried scope hints do not count as authoritative binding.

## 10. Relationship to Approval, Execution, and Reconciliation Surfaces

Phase 30E may coexist with reviewed action-review or case detail surfaces, but it must not flatten their meanings.

If an advisory output references an existing recommendation, action request, approval decision, action execution, or reconciliation record, the browser must render that linkage as cited supporting context only.

Approval state, execution outcome, and reconciliation outcome continue to belong to the authoritative workflow surfaces defined elsewhere.

Recommendation draft rendering therefore must not inherit the visual posture of approval controls, execution receipts, or reconciliation summaries.

## 11. Safe Implementation Sequence

Safe implementation sequence for Phase 30E is:

1. advisory detail route
2. assistant context panel
3. recommendation draft card
4. validation

More specifically:

1. `advisory detail route` comes first so authoritative scope binding and citation-first layout exist before richer assistant rendering lands.
2. `assistant context panel` comes second so operators can inspect the reviewed grounding set before the UI adds richer draft affordances.
3. `recommendation draft card` comes third so draft rendering inherits the explicit citation and no-authority posture instead of inventing a looser assistant pattern.
4. `validation` comes last so documentation and focused UI tests can lock citation-first rendering, ambiguity visibility, and the draft-versus-authoritative split after the contract is fixed.

Safe implementation sequence is mandatory because page-first assistant rendering would otherwise encourage chat-like shortcuts, hidden citation state, and visual collapse between advisory drafts and workflow authority.

## 12. Validation Expectations

Validation for this issue must remain narrow and boundary-focused before broader implementation begins.

At minimum, validation should prove:

- a reviewed Phase 30E design document exists for advisory output detail, assistant context inspection, recommendation draft rendering, unresolved visibility, and no-authority posture;
- the design makes citation-first rendering, ambiguity visibility, and missing-citation failure mandatory;
- the design keeps draft-versus-authoritative separation explicit so assistant output cannot masquerade as final workflow truth; and
- later implementation issues can build routes, cards, badges, and guardrails against one reviewed trust boundary instead of inventing page-local assistant behavior.

The narrowest first regression test for this issue is a documentation test that locks the assistant and advisory UI boundary, citation posture, ambiguity handling, and no-authority semantics in place before broader operator-ui work begins.

## 13. Alignment and Non-Expansion Rules

`docs/phase-30-react-admin-foundation-and-read-only-operator-console-boundary.md` remains the normative source for the thin React-Admin shell, route protection, and adapter posture that Phase 30E extends.

`docs/phase-30c-bounded-write-actions-ui-boundary.md` remains the normative source for the rule that write behavior requires a separate reviewed contract and must not be smuggled in through assistant interaction.

`docs/phase-30d-approval-execution-reconciliation-ui-boundary.md` remains the normative source for approval, execution, and reconciliation state semantics that assistant output must not impersonate.

`docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md` remains the normative source for bounded assistant workflow-family scope and trusted output contract shape.

`docs/phase-15-identity-grounded-analyst-assistant-boundary.md` and `docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md` remain the normative sources for citation completeness, fail-closed unresolved handling, ambiguity preservation, and advisory-only assistant behavior.

`docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md` remains the normative source for the approved cited advisory review path inside the daily operator workflow.

`docs/control-plane-state-model.md` remains the normative source for authoritative lifecycle-bearing records and reviewed workflow truth.

`docs/architecture.md` remains the normative source for the control-plane thesis in which AegisOps stays authoritative above subordinate detection, automation, execution, and assistant surfaces.

Phase 30E therefore approves a reviewed browser contract for advisory output detail, assistant context inspection, recommendation draft rendering, and unresolved or citation-failure visibility only. It does not approve free-form chat, assistant-owned workflow truth, new assistant workflow families, provider-selection policy, approval shortcuts, execution shortcuts, or reconciliation truth by assistant narration.
