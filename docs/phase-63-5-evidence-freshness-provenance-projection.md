# AegisOps Phase 63.5 Evidence Freshness and Provenance Projection

Phase 63.5 projects evidence freshness, custody, confidence, provenance, conflict, source mismatch, unavailable-source, and uncertainty posture for case workbench and AI-grounding consumers.

The projection starts from a directly linked `BoundedEnrichmentEvidencePack` and does not redefine AegisOps workflow truth. It is a derived operator and AI-grounding surface only; AegisOps records remain authoritative for alert, case, evidence request, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

## Projection Contract

The projection entry point is `project_evidence_freshness_provenance`. It accepts `EvidenceFreshnessProvenanceProjectionInput` with the evidence pack, consumer, expected source id, expected case id, requested workflow authority, and optional `projected_at` timestamp.

Allowed consumers are `case_workbench` and `ai_grounding`. Consumer names are normalized before projection, and any other consumer is rejected until a later reviewed issue defines the boundary.

The projection requires explicit custody, confidence, provenance, uncertainty, source, and case bindings before it returns a projection. Missing custody, missing confidence, missing provenance, missing uncertainty, source mismatch, case mismatch, non-bounded-enrichment source, custody binding mismatch, provenance binding mismatch, future lookup timestamps, response digest mismatch, confidence posture mismatch, confidence ambiguity badge mismatch, unexpected pack status, status without a matching reason, unexpected reason code, unexpected metadata field, unexpected source status, hidden metadata authority claim, or requested projection-driven workflow authority fails closed.

Projection freshness is recalculated from the pack lookup time and the authoritative source registry freshness window each time the surface is projected. Persisted packs that were fresh when collected project as stale once `projected_at` falls outside the source freshness window, and lookup timestamps later than `projected_at` are rejected instead of projected.

Projection source status is recalculated from the current authoritative source registry status each time the surface is projected. A now-disabled source projects unavailable with `source_denied`; a now-degraded source projects degraded with `source_stale`.

`custody_state=complete` is returned only when the pack custody reviewed file hash, collection timestamp, response hash, response status, response authority posture, and response digest remain bound to the pack file hash, lookup time, and canonical packed reputation response.

`provenance_state=bound` is returned only when the pack provenance values remain bound to the pack's request, case, target, source, enrichment request, collection timestamp, and response digest.

Returned custody, provenance, and confidence maps must exactly match the bounded enrichment projection contract and cannot contain extra authority-bearing fields or authority-bearing values.

Returned confidence freshness and ambiguity badge values are validated from the projected state. Conflicting evidence must carry the unresolved ambiguity badge; non-conflicting evidence must carry the related-entity badge.

## States

Stale evidence projects `stale_review_required`; conflicting evidence projects `unresolved_conflict`; unavailable sources project `source_unavailable`; fresh related evidence projects `related_entity_not_authoritative`.

The projection exposes:

- `freshness_state`
- `custody_state`
- `confidence_state`
- `provenance_state`
- `conflict_state`
- `source_state`
- `uncertainty_label`
- `authoritative_workflow_truth=false`
- `workflow_authority=none`

## Authority Boundary

Projection state cannot approve, execute, reconcile, close, activate detectors, create source truth, gate release, claim readiness, remediate endpoints, contain hosts, quarantine files, kill processes, mutate protected targets, or issue direct command authority.

The projection cites the Phase 51.6 authority-boundary negative-test policy. Stale, conflicting, unavailable, incomplete, mismatched, or subordinate evidence remains context for review and cannot become case truth, approval truth, reconciliation truth, release truth, gate truth, closeout truth, production truth, or readiness truth.

This slice does not add endpoint remediation, broad evidence-source breadth, autonomous AI authority, source-native truth, Controlled Write, Hard Write, Beta, RC, GA, commercial replacement readiness, or Phase 64/65/66/67 work.
