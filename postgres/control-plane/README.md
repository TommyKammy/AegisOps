# Control-Plane Schema v1

This directory reserves the reviewed repository home for future AegisOps-owned control-plane schema and migration assets.

It also documents the reviewed runtime-ready control-plane schema baseline for the AegisOps-owned PostgreSQL boundary.

The schema remains separate from n8n-owned PostgreSQL metadata and execution-state tables even when both live on the same engine class.

These repository assets do not authorize live deployment, production data migration, or credentials.

The v1 baseline materializes the approved control-plane record families:

- `alert_records`
- `case_records`
- `evidence_records`
- `observation_records`
- `lead_records`
- `recommendation_records`
- `approval_decision_records`
- `action_request_records`
- `hunt_records`
- `hunt_run_records`
- `ai_trace_records`
- `reconciliation_records`

The schema keeps the reconciliation boundary explicit by recording cross-system linkage and mismatch state in dedicated control-plane tables rather than collapsing that state into n8n-owned execution metadata.

`reconciliation_records.ingest_disposition` covers both analytic-ingest outcomes (`created`, `updated`, `deduplicated`, `restated`, `matched`) and execution-correlation exceptions (`missing`, `duplicate`, `mismatch`, `stale`) so operators can distinguish downstream execution gaps from normal alert lifecycle state.

Future work remains explicit: online rollout sequencing, environment-specific access controls, stricter foreign-key enforcement across cyclic record families, and additional index tuning stay out of scope for this baseline.
