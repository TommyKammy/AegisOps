# Control-Plane Schema Skeleton

This directory reserves the reviewed repository home for future AegisOps-owned control-plane schema and migration assets.

These files are placeholders only, are not production-ready, and do not authorize a live service, datastore deployment, credentials, or runtime migration execution.

The reserved schema boundary is `aegisops_control`, kept separate from n8n-owned PostgreSQL metadata and execution-state tables.

Executable runtime-oriented SQL such as `CREATE TABLE`, `ALTER TABLE`, index creation, constraint DDL, and seed data is out of bounds for this placeholder-only directory until control-plane persistence implementation is explicitly approved.

Placeholder comments may describe future reviewed DDL intent, but executable live-ish SQL must fail closed during validation.

The initial placeholder record-family homes tracked here are:

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

Future issues may replace placeholder comments with reviewed DDL once control-plane persistence implementation is explicitly approved.
