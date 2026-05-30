# AegisOps Phase 63.7 AI Grounding Adapter

Phase 63.7 adds a bounded AI grounding adapter for Evidence Expansion v1.

The adapter consumes already reviewed Phase 63 evidence freshness and provenance projections for the `ai_grounding` consumer. It prepares cited advisory grounding only. AegisOps records remain authoritative for alert, case, evidence request, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth.

## Adapter Contract

The adapter entry point is `build_ai_grounding_adapter`.

Input must use contract version `phase-63-7`, a directly bound case review anchor, the reviewed file hash, reviewed custody reference, and evidence record id for each evidence request, and one or more evidence projections from `project_evidence_freshness_provenance` with `consumer=ai_grounding`. Projection freshness is recomputed against the adapter's current trusted grounding time before grounding; caller-supplied payload timestamps are not trusted to keep cached projections fresh.

The adapter is registered as `ai_grounding_adapter` with the `evidence_grounding` tool in the executable AI agent and tool registries.

Each projection must preserve:

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

The adapter derives case, evidence request, evidence-record, and source citations from the reviewed projection fields after matching the projection source and evidence record id against the directly bound review anchor. If a caller supplies `citation_ids`, they must match that derived projection-local set exactly; missing required citation IDs or extra out-of-scope citation IDs fail closed.

Custody, provenance, and confidence metadata maps must match the Phase 63.5 projection contract exactly. Extra metadata fields or authority-bearing metadata values fail closed before grounding.

Missing reviewed-file-hash binding, missing custody-reference binding, missing evidence-record binding, malformed response digest, missing custody, missing provenance, missing confidence, missing uncertainty, state/uncertainty mismatch, stale cached freshness, internally inconsistent state fields, unsupported consumer, case-anchor mismatch, unsupported status, unsupported source, unsupported source state, unsupported conflict state, or any requested authority promotion fails closed with `decision=fallback`.

Per-item citations remain scoped to the projection that produced that item. If any projection is malformed, cross-anchor, missing custody, or otherwise untrusted, its citations are not exported in the adapter response.

Prompt pressure to hide citations, suppress uncertainty, treat evidence as case truth, approve, execute, reconcile, close a case, activate a detector, bypass policy, remediate endpoints, mutate protected targets, create source or evidence truth, or mark release/readiness/gate truth is blocked with `decision=blocked`.

When AI advisory posture is disabled or degraded, the adapter returns a fallback with AI generation and trace creation disabled while preserving the non-AI evidence review path.

## Authority Boundary

The adapter is read-only and advisory-only. It cannot approve, execute, reconcile, close cases, activate detectors, create source truth, create evidence truth, gate release, claim readiness, mutate protected targets, remediate endpoints, or create workflow truth.

Stale evidence remains `stale_review_required`. Conflicting evidence remains `unresolved_conflict`. Unavailable evidence remains `source_unavailable`. Fresh related evidence remains `related_entity_not_authoritative`.

AI output, evidence projections, source-native status, verifier output, issue-lint output, and registry rows remain subordinate context only.

## Scope Boundary

This slice does not add endpoint remediation, containment, quarantine, broad evidence-source breadth, autonomous AI authority, source-native truth, Controlled Write, Hard Write, Beta, RC, GA, commercial replacement readiness, or Phase 64/65/66/67 work.
