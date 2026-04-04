-- Control-plane schema skeleton for the future AegisOps-owned PostgreSQL boundary.
-- Placeholder only. Not production-ready.
-- schema: aegisops_control
create schema if not exists aegisops_control;

-- table: alert_records
-- immutable alert_id plus upstream finding_id and optional analytic_signal_id linkage

-- table: case_records
-- immutable case_id plus alert linkage, finding linkage, and explicit evidence references

-- table: evidence_records
-- immutable evidence_id plus provenance and bounded alert or case linkage

-- table: observation_records
-- immutable observation_id plus scoped authorship and supporting evidence linkage

-- table: lead_records
-- immutable lead_id plus originating observation, finding, or hunt-run linkage

-- table: recommendation_records
-- immutable recommendation_id plus upstream work-item linkage and optional ai_trace linkage

-- table: approval_decision_records
-- immutable approval_decision_id plus request binding, reviewer, and decision state

-- table: action_request_records
-- immutable action_request_id plus approved target scope, expiry, and execution binding

-- table: hunt_records
-- immutable hunt_id plus ownership, hypothesis linkage, and lifecycle state

-- table: hunt_run_records
-- immutable hunt_run_id plus one bounded run outcome for a linked hunt_id

-- table: ai_trace_records
-- immutable ai_trace_id plus prompt, model, review, and downstream linkage context

-- table: reconciliation_records
-- immutable reconciliation_id plus cross-system correlation keys, mismatch state, and resolution linkage
