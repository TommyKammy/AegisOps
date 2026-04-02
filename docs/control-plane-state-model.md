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
| `Approval Decision` | Future AegisOps control-plane approval record | Approval is a first-class control decision and must not be reconstructed from whether a workflow happened to run. |
| `Action Request` | Future AegisOps control-plane action-request record | Requested intent, target scope, payload binding, and expiry belong to the control layer rather than to workflow definitions or execution logs. |
| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state | n8n owns execution-attempt state, step progress, and connector-specific runtime details. |

n8n execution history must not become the implicit system of record for case state, approval state, or action-request intent.

OpenSearch findings and alerts remain upstream analytic signals for reconciliation input, but they do not own downstream case, approval, or execution-policy state.

At the approved baseline level, the source-of-truth expectations are:

- findings remain analytics-plane facts produced and retained by OpenSearch;
- alerts, cases, approvals, and action requests are platform-owned control records whose future authoritative home is an AegisOps control schema or API boundary;
- action execution state remains execution-plane runtime state owned by n8n and backed by PostgreSQL; and
- evidence links across those records must be explicit rather than reconstructed from whichever component happens to log the most detail.

## 4. Reconciliation Responsibilities

The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed.

Reconciliation must prefer deterministic correlation keys such as finding identifiers, action-request identifiers, approval identifiers, workflow identifiers, and idempotency keys rather than fuzzy time-window matching.

OpenSearch is responsible for producing stable analytic identifiers and timestamps for findings and other analytic signals that downstream control-plane logic may reference.

n8n is responsible for exposing enough workflow-run identifiers, timestamps, execution outcomes, and step-level failure detail that a future control-plane layer can correlate approved intent to observed execution behavior.

The future AegisOps control layer is responsible for:

- deciding whether an analytic signal should create or update an alert or case record;
- deciding whether an action request is pending approval, approved, rejected, expired, canceled, superseded, executing, completed, failed, or unresolved;
- binding approval decisions to exact request context before execution is allowed; and
- marking reconciliation exceptions when upstream findings disappear, duplicate workflow triggers arrive, or n8n reports an outcome that does not satisfy the approved intent record.

Reconciliation must preserve auditable disagreement. When OpenSearch, n8n, and the future control record disagree, the platform must retain that mismatch as an explicit state that operators can inspect and resolve rather than overwriting one side to make the data look clean.

## 5. Retry, Dead-Letter, and Manual Recovery Responsibilities

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

## 6. Idempotency and Audit Expectations

Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays.

Idempotency keys must bind to the approved request scope, payload hash, target snapshot, and intended execution path closely enough that a replay can be detected without inferring operator intent from timestamps alone.

Auditability requires separate evidence for:

- the analytic signal that justified work,
- the control-plane record that tracked alert or case ownership,
- the approval decision that authorized or rejected action,
- the action request that defined exact execution intent, and
- the n8n execution record that shows what actually ran and what outcome was observed.

No single component log should be treated as sufficient to reconstruct the entire decision chain when that would blur responsibility boundaries or allow silent loss of approval evidence.

## 7. Baseline Alignment Notes

This model keeps component boundaries explicit without approving a new live datastore in the current phase.

It reinforces the requirements baseline rule that detection and execution remain separate, the domain-model rule that findings, approvals, and execution are distinct records, and the response-action safety rule that approval is not the same as execution.

A future implementation may materialize these control-plane records in a dedicated service or datastore, but this baseline explicitly defers that runtime choice.
