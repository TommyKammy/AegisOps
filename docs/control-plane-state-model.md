# AegisOps Control-Plane State and Reconciliation Model

## 1. Purpose

This document defines the approved baseline control-plane state model for AegisOps before any dedicated control service or datastore is implemented.

It supplements `docs/architecture.md`, `docs/secops-domain-model.md`, and `docs/response-action-safety-model.md` by making state ownership, source-of-truth boundaries, and reconciliation duties explicit enough for future implementation and review work.

This document defines ownership, source-of-truth expectations, and recovery responsibilities only. It does not introduce a live datastore, schema migration, API service, or runtime deployment in this phase.

## 2. Baseline Design Constraints

The baseline must keep platform-owned control state explicit even though no dedicated AegisOps control service exists yet.

The design constraint is to prevent OpenSearch documents, OpenSearch alerting artifacts, n8n execution history, or ad hoc analyst notes from silently becoming the long-term database for case management, approval state, or execution policy.

Until a future implementation materializes a dedicated control schema or API boundary, this document is the normative definition of which component owns which state and what must later be reconciled across component boundaries.

No new live datastore is approved in this phase. PostgreSQL remains the backing store for n8n runtime metadata and workflow execution state only, and OpenSearch remains the analytics-plane store for telemetry and detection outputs.

## 3. Baseline Ownership and Source of Truth

| Record family | Baseline owner | Ownership note |
| ---- | ---- | ---- |
| `Finding` | OpenSearch detection and analytics plane | OpenSearch remains the system of record for detection outputs and finding identifiers. |
| `OpenSearch Alert Signal` | OpenSearch detection and analytics plane | OpenSearch-owned alerting artifacts are upstream analytic signals, not the durable analyst work-tracking record for the platform. |
| `Alert` | Future AegisOps control-plane alert record | Alert lifecycle must not be inferred from OpenSearch alert documents or n8n execution history alone. |
| `Case` | Future AegisOps control-plane case record | Case ownership, analyst status, and evidence linkage must not dissolve into workflow runs or dashboard state. |
| `Evidence` | Future AegisOps control-plane evidence record | Evidence custody, provenance, and record linkage must remain explicit instead of dissolving into case notes, AI output, or workflow metadata. |
| `Observation` | Future AegisOps control-plane observation record | Observations capture analyst-asserted investigative facts and must remain distinct from raw evidence artifacts, AI trace text, and case status fields. |
| `Lead` | Future AegisOps control-plane lead record | Leads preserve candidate hypotheses or follow-up directions without silently promoting them into alerts, cases, or approved action intent. |
| `Recommendation` | Future AegisOps control-plane recommendation record | Recommendations preserve proposed analyst or AI-advised next steps without replacing approval decisions, action requests, or execution outcomes. |
| `Approval Decision` | Future AegisOps control-plane approval record | Approval is a first-class control decision and must not be reconstructed from whether a workflow happened to run. |
| `Action Request` | Future AegisOps control-plane action-request record | Requested intent, target scope, payload binding, and expiry belong to the control layer rather than to workflow definitions or execution logs. |
| `Hunt` | Future AegisOps control-plane hunt record | Hunt lifecycle must remain analyst-directed and reviewable rather than inferred from ad hoc queries or downstream workflow runs. |
| `Hunt Run` | Future AegisOps control-plane hunt-run record | Each hunt run must preserve bounded scope, execution context, and outcome for one hunt iteration without replacing alerts or cases. |
| `AI Trace` | Future AegisOps control-plane AI-trace record | AI trace records must preserve prompt, model, review, and linkage context without mutating evidence custody or analyst-owned dispositions. |
| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state | n8n owns execution-attempt state, step progress, and connector-specific runtime details. |

n8n execution history must not become the implicit system of record for case state, approval state, or action-request intent.

OpenSearch findings and alerts remain upstream analytic signals for reconciliation input, but they do not own downstream case, approval, or execution-policy state.

The minimum control-plane record families for this baseline are Alert, Case, Evidence, Observation, Lead, Recommendation, Approval Decision, Action Request, Hunt, Hunt Run, AI Trace, and the execution-plane Action Execution record that must later reconcile with them.

At the approved baseline level, the source-of-truth expectations are:

- findings remain analytics-plane facts produced and retained by OpenSearch;
- alerts, cases, evidence, observations, leads, recommendations, approvals, action requests, hunts, hunt runs, and AI traces are platform-owned control records whose future authoritative home is an AegisOps control schema or API boundary;
- action execution state remains execution-plane runtime state owned by n8n and backed by PostgreSQL; and
- evidence links across those records must be explicit rather than reconstructed from whichever component happens to log the most detail.

## 4. Approved Future Persistence Boundary

The approved future persistence boundary for those platform-owned control records is an AegisOps-owned PostgreSQL-backed control-plane datastore boundary.

That future PostgreSQL-backed boundary may share a PostgreSQL engine class with n8n, but it must not collapse control-plane ownership into n8n-owned metadata tables or runtime workflow state.

If a future implementation uses one PostgreSQL cluster for both concerns, it must still preserve an explicit ownership split through separate AegisOps-controlled schemas, tables, migration history, and access controls for control-plane records.

OpenSearch must not become the authoritative store for alert lifecycle, case state, evidence custody, approval decisions, action-request intent, hunt lifecycle, hunt-run status, or AI trace review state.

n8n metadata tables and workflow execution history must not become the authoritative store for alert ownership, case ownership, evidence linkage, recommendation review state, approval decisions, or action-request intent.

The approved ownership split for a future PostgreSQL-backed implementation is:

- AegisOps control-plane storage owns authoritative platform records, including alerts, cases, evidence, observations, leads, recommendations, approval decisions, action requests, hunts, hunt runs, AI traces, and reconciliation state that binds those records to analytics and execution outcomes.
- n8n-owned PostgreSQL storage owns runtime workflow metadata, execution attempts, step progress, connector-local execution details, retry artifacts internal to a running workflow, and similar orchestration-engine state.
- OpenSearch owns telemetry, findings, and OpenSearch-native analytic or alerting artifacts that act as upstream signals rather than downstream control-plane truth.

This boundary approves where future authoritative control-plane records belong conceptually, but it does not approve live PostgreSQL provisioning, schema migrations, credentials, or runtime deployment changes in this phase.

## 5. Reconciliation Responsibilities

The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed.

Reconciliation must prefer deterministic correlation keys such as finding identifiers, action-request identifiers, approval identifiers, workflow identifiers, and idempotency keys rather than fuzzy time-window matching.

Stable reconciliation keys must allow operators to compare OpenSearch analytics output, control-plane records, and n8n execution outcomes without assuming those systems share one lifecycle or one authoritative identifier.

OpenSearch is responsible for producing stable analytic identifiers and timestamps for findings and other analytic signals that downstream control-plane logic may reference.

n8n is responsible for exposing enough workflow-run identifiers, timestamps, execution outcomes, and step-level failure detail that a future control-plane layer can correlate approved intent to observed execution behavior.

The minimum stable reconciliation key set for this baseline is:

- `finding_id` for the upstream OpenSearch analytic record;
- `analytic_signal_id` for the specific OpenSearch alerting or correlation artifact, when distinct from the finding;
- `alert_id` and `case_id` for control-plane triage and investigation ownership;
- `evidence_id` plus preserved provenance metadata for linked artifacts or derived material;
- `observation_id`, `lead_id`, and `recommendation_id` for analyst assertions, investigative direction, and proposed next steps that must remain independently reviewable;
- `approval_decision_id` and `action_request_id` for authorized response intent;
- `hunt_id` and `hunt_run_id` for analyst-directed exploration and each bounded execution of that exploration;
- `ai_trace_id` for preserved AI-assisted interpretation or recommendation context; and
- `workflow_id`, `workflow_execution_id`, and an action idempotency key for the n8n execution-plane record.

The future AegisOps control layer is responsible for:

- deciding whether an analytic signal should create or update an alert or case record;
- deciding how evidence, observations, leads, recommendations, hunts, hunt runs, and AI traces are attached to alerts, cases, or independent analyst workflows without collapsing their ownership boundaries;
- deciding whether an action request is pending approval, approved, rejected, expired, canceled, superseded, executing, completed, failed, or unresolved;
- binding approval decisions to exact request context before execution is allowed; and
- marking reconciliation exceptions when upstream findings disappear, duplicate workflow triggers arrive, or n8n reports an outcome that does not satisfy the approved intent record.

Observation records must preserve scoped analyst assertions, timestamps, authorship, and linkage to supporting evidence without turning evidence custody into free-form narrative.

Lead records must preserve investigative hypotheses, triage rationale, and disposition state without being treated as equivalent to alert state, case state, or recommendation text.

Recommendation records must preserve proposed next steps, rationale, and review status without being treated as approval, execution, or immutable evidence.

Hunt records must preserve explicit lifecycle state, ownership, hypothesis linkage, and closure rationale even when no case is opened.

Hunt-run reconciliation must preserve whether a run was planned, started, completed, canceled, superseded, or left unresolved, plus which findings, observations, leads, recommendations, or cases it did or did not influence.

AI trace records must preserve generation, review, acceptance, rejection, supersession, and linkage expectations as explicit control-plane state rather than silent prompt history.

Reconciliation must preserve auditable disagreement. When OpenSearch, n8n, and the future control record disagree, the platform must retain that mismatch as an explicit state that operators can inspect and resolve rather than overwriting one side to make the data look clean.

Disagreement between analytics, control-plane, and execution-plane records must remain auditable rather than silently overwritten.

## 6. Retry, Dead-Letter, and Manual Recovery Responsibilities

Retry policy belongs to the control-plane intent record, while duplicate suppression and step-level retry behavior inside a running workflow belong to n8n.

OpenSearch may re-emit or restate analytic signals according to its own alerting behavior, but deduplication of downstream analyst work belongs to the future AegisOps control layer rather than to OpenSearch.

Dead-letter responsibility begins when the platform can no longer prove whether an approved intent was never executed, is still executing, or executed with an unknown result.

The future control layer must be able to mark a record for manual review when:

- approval expired before a correlated execution started;
- an execution started without a reconcilable approved request;
- multiple executions appear for one approved request without an allowed retry policy;
- execution finished but post-action verification is missing or inconclusive; or
- upstream analytic context changed materially while downstream work remained open.

Manual recovery procedures must support re-drive, cancellation, supersession, and explicit operator annotation without rewriting historical approval or execution evidence.

Manual recovery must also preserve why the operator chose the recovery path, which records were linked or superseded, and whether follow-up verification or rollback work remains open.

## 7. Idempotency and Audit Expectations

Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays.

Idempotency keys must bind to the approved request scope, payload hash, target snapshot, and intended execution path closely enough that a replay can be detected without inferring operator intent from timestamps alone.

Auditability requires separate evidence for:

- the analytic signal that justified work,
- the control-plane record that tracked alert or case ownership,
- the approval decision that authorized or rejected action,
- the action request that defined exact execution intent, and
- the n8n execution record that shows what actually ran and what outcome was observed.

No single component log should be treated as sufficient to reconstruct the entire decision chain when that would blur responsibility boundaries or allow silent loss of approval evidence.

## 8. Baseline Alignment Notes

This model keeps component boundaries explicit without approving a new live datastore in the current phase.

It reinforces the requirements baseline rule that detection and execution remain separate, the domain-model rule that findings, approvals, and execution are distinct records, and the response-action safety rule that approval is not the same as execution.

A future implementation may materialize these control-plane records in a dedicated service or datastore, but this baseline explicitly defers that runtime choice.
