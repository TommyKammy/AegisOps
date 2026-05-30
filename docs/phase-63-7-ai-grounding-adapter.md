# AegisOps Phase 63.7 AI Grounding Adapter

Phase 63.7 adds a bounded AI grounding adapter for Evidence Expansion v1.

The adapter consumes already reviewed Phase 63 evidence freshness and provenance projections for the `ai_grounding` consumer. It prepares cited advisory grounding only. AegisOps records remain authoritative for alert, case, evidence request, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

## Adapter Contract

The adapter entry point is `build_ai_grounding_adapter`.

Input must use contract version `phase-63-7`, a directly bound case review anchor, and one or more evidence projections from `project_evidence_freshness_provenance` with `consumer=ai_grounding`.

Each projection must preserve:

- case, source, evidence request, and evidence-record citations;
- complete custody;
- bound provenance;
- present confidence;
- freshness state;
- conflict state;
- source state;
- uncertainty label;
- `authoritative_workflow_truth=false`;
- `workflow_authority=none`;
- subordinate evidence authority posture.

Missing citation, missing custody, missing provenance, missing confidence, missing uncertainty, unsupported consumer, case-anchor mismatch, unsupported status, unsupported source state, unsupported conflict state, or any requested authority promotion fails closed with `decision=fallback`.

Prompt pressure to hide citations, suppress uncertainty, treat evidence as case truth, approve, execute, reconcile, close a case, activate a detector, create source or evidence truth, or mark release/readiness/gate truth is blocked with `decision=blocked`.

When AI advisory posture is disabled or degraded, the adapter returns a fallback with AI generation and trace creation disabled while preserving the non-AI evidence review path.

## Authority Boundary

The adapter is read-only and advisory-only. It cannot approve, execute, reconcile, close cases, activate detectors, create source truth, create evidence truth, gate release, claim readiness, mutate protected targets, remediate endpoints, or create workflow truth.

Stale evidence remains `stale_review_required`. Conflicting evidence remains `unresolved_conflict`. Unavailable evidence remains `source_unavailable`. Fresh related evidence remains `related_entity_not_authoritative`.

AI output, evidence projections, source-native status, verifier output, issue-lint output, and registry rows remain subordinate context only.

## Scope Boundary

This slice does not add endpoint remediation, containment, quarantine, broad evidence-source breadth, autonomous AI authority, source-native truth, Controlled Write, Hard Write, Beta, RC, GA, commercial replacement readiness, or Phase 64/65/66/67 work.
