# AegisOps Non-Goals and Expansion Guardrails

This document is the canonical cross-phase reference for the expansions AegisOps must continue to reject even as optional extensions, assistant paths, ML shadow mode, evidence-pack families, and coordination integrations grow around the reviewed control-plane core.

Use this registry when evaluating roadmap proposals, ADRs, design docs, implementation issues, PRs, validation notes, and review comments that could widen AegisOps beyond the approved control-plane thesis.

## 1. Purpose

AegisOps is a governed SecOps control plane above external detection and automation substrates.

This registry consolidates the already accepted cross-phase boundaries that answer the question: what must AegisOps continue not to become?

Future roadmap work, PRs, ADRs, and validation notes should cite this registry when checking whether a proposed expansion widens AegisOps beyond the approved control-plane thesis.

## 2. Product-Thesis Guardrails

AegisOps must not become a self-built replacement for all SIEM features or all SOAR features.

AegisOps must not become a broad autonomous response platform, a broad source-coverage platform, or a product thesis defined around any one analytics, ticketing, enrichment, or orchestration substrate.

AegisOps must not become a 24x7 SOC product, a multi-tenant MSSP control plane, or a broad browser-first product expansion that outranks reviewed control-plane depth, bootability, and deployability priorities.

The approved growth model remains narrow, reviewed, fail-closed expansion of the control-plane record chain and its bounded operator workflows one slice at a time.

## 3. Authority Guardrails

AegisOps remains authoritative for alert, case, evidence, recommendation, approval, action-intent, action-execution, and reconciliation truth.

Detection substrates, automation substrates, optional enrichers, ticketing systems, and external evidence sources must remain subordinate to that authority boundary.

No optional path may silently mint or overwrite approval truth, execution truth, case truth, or reconciliation truth.

## 4. Assistant and ML Guardrails

Assistant and ML paths remain advisory-only and non-authoritative.

Assistant output must not become approval authority, delegation authority, execution authority, reconciliation authority, or case-truth authority.

Reviewed ML shadow-mode output must remain outside the authoritative workflow path and must not silently promote itself into alerts, approvals, execution policy, or lifecycle-bearing control-plane state.

If reviewed grounding, citations, labels, provenance, or scope constraints are missing, the assistant or ML path must remain unresolved, degraded, or blocked rather than silently widening authority.

## 5. Optional-Substrate Guardrails

Optional or transitional substrates remain subordinate to the AegisOps control-plane authority model.

OpenSearch, Sigma, n8n, optional network evidence-pack paths, optional endpoint evidence-pack paths, and bounded external enrichment adapters may support reviewed analysis, enrichment, or delegated execution only within explicitly approved boundaries.

Those optional or transitional paths must not redefine the product core, become mandatory mainline dependencies without review, or reframe AegisOps as a substrate-led platform.

## 6. Evidence-Pack and Enrichment Guardrails

Subordinate evidence packs remain optional augmentation, not a new product core or authority surface.

Endpoint, network, or external-enrichment material may support reviewed notes, analyst explanation, or bounded recommendations only when it preserves explicit provenance and stays linked to the authoritative AegisOps-owned record chain.

Subordinate evidence-pack and enrichment outputs must not replace AegisOps-owned alert truth, case truth, evidence truth, approval truth, execution truth, or reconciliation truth.

## 7. Coordination and Ticketing Guardrails

External coordination or ticketing systems remain non-authoritative coordination targets.

Link-first ticket references, downstream ticket identifiers, assignee metadata, comments, queue movement, SLA state, workflow status, or closure flags may be stored as coordination context or receipts, but they must remain subordinate evidence rather than lifecycle authority.

External coordination state must not be treated as approval proof, execution proof, case closure, or reconciliation completion on its own.

## 8. Fail-Closed Expansion Guardrail

Fail-closed handling remains mandatory when reviewed provenance, scope, auth context, or boundary signals are missing, malformed, or only partially trusted.

Missing or obviously fake secrets, placeholder credentials, unsigned tokens, inferred tenant linkage, untrusted forwarded headers, partial evidence-pack provenance, missing authoritative bindings, or mixed-snapshot reads must stay blocked, rejected, degraded explicitly, or escalated for a real prerequisite rather than being treated as success.

When expansion depends on a later authorization, provenance, or scope-validation step, the reviewed proof must anchor at that real enforcement boundary instead of treating an earlier setup step as sufficient evidence.

## 9. Phase 44-47 Closed Pilot-Readiness Guardrails

The closed Phase 44-47 contracts cover pilot ingress, daily SOC queue, approval/execution/reconciliation operations, and control-plane responsibility decomposition.

AegisOps control-plane records remain authoritative.

No later roadmap item may use these closed phases to infer new runtime behavior, browser authority, ticket authority, assistant authority, optional-evidence authority, or commercial-readiness claims.

Phase 44-47 boundary docs:

- `docs/phase-44-pilot-ingress-and-operator-surface-closure-boundary.md`
- `docs/phase-45-daily-soc-queue-and-operator-ux-hardening-boundary.md`
- `docs/phase-46-approval-execution-reconciliation-operations-pack-boundary.md`
- `docs/phase-47-control-plane-responsibility-decomposition-boundary.md`

## 10. Review Use

Use this registry as the default anti-expansion citation target when a proposal touches:

- assistant scope
- ML lineage or shadow-mode surfaces
- optional or transitional substrates
- evidence-pack families
- external enrichment
- coordination or ticketing integrations
- any path that could widen authority, source breadth, or automation breadth

If a proposal conflicts with this registry, treat it as out of scope until an ADR explicitly changes the approved boundary.
