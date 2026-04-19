# AegisOps Phase 28 Bounded External Enrichment Direct-Adapter Boundary

## 1. Purpose

This document defines the reviewed bounded external enrichment contract for direct read-only adapters first.

It supplements `docs/requirements-baseline.md`, `docs/architecture.md`, `docs/phase-15-identity-grounded-analyst-assistant-boundary.md`, `docs/phase-25-reviewed-multi-source-case-admission-and-ambiguity-taxonomy.md`, and `docs/safe-query-gateway-and-tool-policy.md` by defining how optional external context may be attached without promoting external services into authority surfaces.

This document defines reviewed design scope only. It does not approve aggregator-first architecture, automated write-back, live credential wiring, runtime orchestration, or any path that would let external-source output replace AegisOps-owned evidence and case truth.

## 2. Reviewed Role and Starting Pattern

External enrichment remains subordinate to AegisOps-owned evidence and case truth.

Direct read-only adapters are the approved starting pattern for this slice.

The approved role of this boundary is to let reviewed casework attach bounded external observations from explicitly named services when an existing AegisOps-owned record already needs additional context for review, triage, or explanation.

Aggregator-first architecture is not approved for this boundary.

The reviewed path starts with one adapter per reviewed source so provenance, staleness, scope, and conflict handling remain explicit at the AegisOps boundary instead of being hidden behind a broker or convenience abstraction.

External source output must not replace or overwrite AegisOps-owned case truth, evidence truth, approval truth, or reconciliation truth.

## 3. Admission Preconditions and Fail-Closed Rules

External enrichment may be attached only to an existing AegisOps-owned case, evidence record, finding, or reviewed assistant context snapshot.

The attachment must work outward from that reviewed anchor rather than from free-form browsing, substrate-led hunting, or opportunistic pivots.

The path must fail closed when provenance, source scope, citation anchors, or staleness details are missing, malformed, or only partially trusted.

The path must also fail closed when:

- the lookup target is inferred only from nearby metadata, analyst memory, naming similarity, or weak linkage;
- the queried object is not already present as reviewed case context, reviewed evidence context, or an explicitly reviewed assistant-context field;
- the adapter cannot identify which reviewed source, object type, and object value it queried; or
- the returned material cannot be attached as subordinate context without overstating what the external service actually proved.

If a reviewed operator cannot explain why the lookup is attached to the current reviewed record chain, the enrichment must stay out of the case surface.

## 4. Approved Source Classes for the First Slice

The approved first source classes for this reviewed slice are bounded reputation and scan-lookback services queried through direct read-only adapters.

The first reviewed source examples for this slice are:

- `VirusTotal` for bounded file hash, URL, domain, or IP observations exposed through reviewed direct lookups;
- `urlscan` for bounded URL or domain scan history and scan-result references exposed through reviewed direct lookups; and
- `AbuseIPDB` for bounded IP reputation and reporting context exposed through reviewed direct lookups.

These source classes fit the reviewed Phase 28 posture because they can contribute narrow read-only observations tied to a reviewed object without asking AegisOps to delegate authority, accept broad third-party workflow ownership, or adopt an aggregator-first design.

This slice does not approve free-form public-internet pivots, broad threat-intel aggregation planes, or open-ended external search as part of normal case review.

## 5. Attachment Artifacts and Citation Contract

The approved artifact classes for this boundary are:

- `lookup_receipt` for the reviewed record of which direct adapter ran, which service it targeted, which object type and value it queried, and when the lookup occurred;
- `source_observation` for bounded external-source output that remains attributable to one reviewed service response and one reviewed lookup target;
- `citation_attachment` for the reviewed citation payload that lets an operator trace the observation back to the service, queried object, and lookup time;
- `conflict_marker` for an explicit note that external-source output disagrees with reviewed AegisOps-owned records or other reviewed external observations; and
- `staleness_marker` for an explicit note that the returned external context is aged, incomplete, or otherwise unsuitable for stronger interpretation.

The contract must preserve source identity, lookup time, source-specific object queried, response freshness, and the reviewed AegisOps anchor that admitted the attachment.

Every attached observation must preserve enough citation detail for a reviewer to answer:

- which reviewed direct adapter produced it;
- which external service returned it;
- which object was queried;
- when the query ran;
- what freshness or age statement applied at the time of admission; and
- which case, evidence record, finding, or assistant-context snapshot admitted it.

External-source output may support reviewed notes, analyst explanation, and bounded candidate recommendations, but it must remain subordinate context rather than authority-bearing truth.

## 6. Provenance, Staleness, and Conflict Handling

Every reviewed attachment must preserve provenance that identifies the service, adapter identity, queried object, lookup timestamp, and admitting AegisOps anchor.

Staleness must remain explicit.

If a source response carries a vendor freshness indicator, cache age, last-analysis time, or equivalent timing signal, the attachment must preserve it rather than flattening the response into timeless truth.

If freshness cannot be established, the attachment must carry a `staleness_marker` or remain excluded from reviewed case surfaces.

Conflicts between external source output and AegisOps-owned records must stay explicit and must not be collapsed into one preferred summary by convenience.

Conflicts between one external source and another external source must also stay explicit unless a later reviewed AegisOps-owned record resolves the discrepancy.

External output may corroborate or challenge a reviewed hypothesis, but it must not silently redefine case scope, actor identity, asset identity, repository identity, tenant identity, or remediation status.

## 7. Authority and Boundary Notes

This boundary keeps AegisOps as the owner of reviewed alert, case, evidence, approval, action, and reconciliation truth.

External enrichment services are read-only context substrates for this slice, not workflow owners and not reviewed system-of-record surfaces.

Any later implementation for this boundary must continue to treat external-source context as optional and subordinate.

If external services are absent, rate-limited, stale, contradictory, or unavailable, the reviewed case path must continue with AegisOps-owned records rather than treating external enrichment as a prerequisite.

## 8. Non-Goals

This reviewed slice does not approve:

- aggregator-first design or broker-led normalization before direct adapters are reviewed individually;
- IntelOwl-first architecture, automated write-back, external-truth replacement, and free-form public-internet pivots remain out of scope;
- any path that would let a third-party score, label, verdict, or summary become the authoritative case conclusion by convenience;
- automatic fan-out from one reviewed lookup target into unrelated sibling objects or broad neighborhood searches; or
- hiding provenance, staleness, or conflict state behind simplified badges or operator-facing summaries.

IntelOwl-first architecture, automated write-back, external-truth replacement, and free-form public-internet pivots remain out of scope.

## 9. Repository-Local Verification Commands

The repository-local verification command for this boundary is:

- `python3 -m unittest control-plane.tests.test_phase28_external_enrichment_boundary_docs`
