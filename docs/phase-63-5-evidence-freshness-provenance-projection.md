# AegisOps Phase 63.5 Evidence Freshness and Provenance Projection

Phase 63.5 projects evidence freshness, custody, confidence, provenance, conflict, source mismatch, unavailable-source, and uncertainty posture for case workbench and AI-grounding consumers.

The projection starts from a directly linked `BoundedEnrichmentEvidencePack` and does not redefine AegisOps workflow truth. It is a derived operator and AI-grounding surface only; AegisOps records remain authoritative for alert, case, evidence request, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

## Projection Contract

The projection entry point is `project_evidence_freshness_provenance`. It accepts `EvidenceFreshnessProvenanceProjectionInput` with the evidence pack, consumer, expected source id, expected case id, and requested workflow authority.

Allowed consumers are `case_workbench` and `ai_grounding`. Any other consumer is rejected until a later reviewed issue defines the boundary.

The projection requires explicit custody, confidence, provenance, uncertainty, source, and case bindings before it returns a projection. Missing custody, missing confidence, missing provenance, missing uncertainty, source mismatch, case mismatch, or requested projection-driven workflow authority fails closed.

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
