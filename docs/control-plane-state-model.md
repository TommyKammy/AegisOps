# AegisOps Control-Plane State and Reconciliation Model

## 1. Purpose

This document defines the approved baseline control-plane state model for AegisOps across the live control-plane runtime boundary and the reviewed PostgreSQL control-plane persistence boundary.

It supplements `docs/architecture.md`, `docs/secops-domain-model.md`, and `docs/response-action-safety-model.md` by making state ownership, source-of-truth boundaries, and reconciliation duties explicit enough for future implementation and review work.

This document defines ownership, source-of-truth expectations, and recovery responsibilities only. It does not introduce a live datastore, schema migration, API service, or runtime deployment in this phase.

## 2. Baseline Design Constraints

The baseline must keep platform-owned control state explicit across the shipped `control-plane/` runtime boundary and the reviewed `postgres/control-plane/` persistence-contract home.

The design constraint is to prevent OpenSearch documents, OpenSearch alerting artifacts, n8n execution history, or ad hoc analyst notes from silently becoming the long-term database for case management, approval state, or execution policy.

The repository already ships a dedicated control-plane runtime home, so this document is the normative definition of which component owns which state and what must be reconciled across runtime, persistence, analytics, and execution boundaries.

No new live datastore rollout is approved in this phase. The current control-plane runtime remains `persistence_mode="in_memory"`, `postgres/control-plane/` remains the reviewed schema and migration home for future PostgreSQL-backed persistence work, and OpenSearch remains the analytics-plane store for telemetry and detection outputs.

## 3. Baseline Ownership and Source of Truth

| Record family | Baseline owner | Ownership note |
| ---- | ---- | ---- |
| `Substrate Detection Record` | Approved upstream detection substrate | The detection substrate remains the system of record for substrate-native detection, correlation, and alerting artifacts plus their native identifiers. |
| `Analytic Signal` | AegisOps control-plane intake boundary referencing approved upstream detection substrates | Analytic signals are admitted upstream product inputs that preserve substrate-native linkage without becoming the durable analyst work-tracking record for the platform. |
| `Finding` | Approved detection substrate or analytics plane | Findings remain upstream analytic assertions and must not be reused as downstream control-plane lifecycle state. |
| `Alert` | AegisOps control-plane alert record | Alert lifecycle must not be inferred from OpenSearch alert documents or n8n execution history alone. |
| `Case` | AegisOps control-plane case record | Case ownership, analyst status, and evidence linkage must not dissolve into workflow runs or dashboard state. |
| `Evidence` | AegisOps control-plane evidence record | Evidence custody, provenance, and record linkage must remain explicit instead of dissolving into case notes, AI output, or workflow metadata. |
| `Observation` | AegisOps control-plane observation record | Observations capture analyst-asserted investigative facts and must remain distinct from raw evidence artifacts, AI trace text, and case status fields. |
| `Lead` | AegisOps control-plane lead record | Leads preserve candidate hypotheses or follow-up directions without silently promoting them into alerts, cases, or approved action intent. |
| `Recommendation` | AegisOps control-plane recommendation record | Recommendations preserve proposed analyst or AI-advised next steps without replacing approval decisions, action requests, or execution outcomes. |
| `Approval Decision` | AegisOps control-plane approval record | Approval is a first-class control decision and must not be reconstructed from whether a workflow happened to run. |
| `Action Request` | AegisOps control-plane action-request record | Requested intent, target scope, payload binding, and expiry belong to the control layer rather than to workflow definitions or execution logs. |
| `Hunt` | AegisOps control-plane hunt record | Hunt lifecycle must remain analyst-directed and reviewable rather than inferred from ad hoc queries or downstream workflow runs. |
| `Hunt Run` | AegisOps control-plane hunt-run record | Each hunt run must preserve bounded scope, execution context, and outcome for one hunt iteration without replacing alerts or cases. |
| `AI Trace` | AegisOps control-plane AI-trace record | AI trace records must preserve prompt, model, review, and linkage context without mutating evidence custody or analyst-owned dispositions. |
| `Reconciliation` | AegisOps control-plane reconciliation record | Cross-system linkage, mismatch tracking, and resolution state must not dissolve into alert fields, case notes, or n8n metadata. |
| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state | n8n owns execution-attempt state, step progress, and connector-specific runtime details. |

n8n execution history must not become the implicit system of record for case state, approval state, or action-request intent.

Substrate-native detection records and admitted analytic signals remain upstream reconciliation inputs, but they do not own downstream case, approval, or execution-policy state.

The minimum control-plane record families for this baseline are Alert, Case, Evidence, Observation, Lead, Recommendation, Approval Decision, Action Request, Hunt, Hunt Run, AI Trace, Reconciliation, and the execution-plane Action Execution record that must later reconcile with them.

Analytic signals remain admitted vendor-neutral intake primitives with stable `analytic_signal_id` linkage and first-class control-plane persistence, but they remain distinct from the downstream analyst work-tracking record families listed above.

At the approved baseline level, the source-of-truth expectations are:

- substrate detection records and findings remain upstream substrate or analytics-plane facts, while analytic signals remain the admitted vendor-neutral intake primitive for control-plane routing and are preserved as first-class control-plane records;
- analytic signals, alerts, cases, evidence, observations, leads, recommendations, approvals, action requests, hunts, hunt runs, AI traces, and reconciliation records are platform-owned control records whose authoritative home is the AegisOps control-plane runtime boundary with the reviewed PostgreSQL contract rooted under `postgres/control-plane/`;
- action execution state remains execution-plane runtime state owned by n8n and backed by PostgreSQL; and
- evidence links across those records must be explicit rather than reconstructed from whichever component happens to log the most detail.

## 4. Approved Persistence Boundary

The approved persistence boundary for those platform-owned control records is the AegisOps-owned PostgreSQL control-plane boundary reviewed under `postgres/control-plane/`.

That reviewed PostgreSQL-backed boundary may share a PostgreSQL engine class with n8n, but it must not collapse control-plane ownership into n8n-owned metadata tables or runtime workflow state.

If a later deployment uses one PostgreSQL cluster for both concerns, it must still preserve an explicit ownership split through separate AegisOps-controlled schemas, tables, migration history, and access controls for control-plane records.

OpenSearch must not become the authoritative store for alert lifecycle, case state, evidence custody, approval decisions, action-request intent, hunt lifecycle, hunt-run status, or AI trace review state.

n8n metadata tables and workflow execution history must not become the authoritative store for alert ownership, case ownership, evidence linkage, recommendation review state, approval decisions, or action-request intent.

The approved ownership split for the reviewed PostgreSQL-backed boundary is:

- AegisOps control-plane storage owns authoritative platform records, including alerts, cases, evidence, observations, leads, recommendations, approval decisions, action requests, hunts, hunt runs, AI traces, and reconciliation state that binds those records to analytics and execution outcomes.
- n8n-owned PostgreSQL storage owns runtime workflow metadata, execution attempts, step progress, connector-local execution details, retry artifacts internal to a running workflow, and similar orchestration-engine state.
- OpenSearch owns telemetry, findings, and OpenSearch-native analytic or alerting artifacts that act as upstream signals rather than downstream control-plane truth.

This boundary approves where authoritative control-plane records belong for the live runtime boundary, but it does not approve live PostgreSQL provisioning, schema migrations, credentials, or runtime deployment changes in this phase.

The repository already materializes a version-controlled schema baseline for that boundary under `postgres/control-plane/`, including reviewed schema manifests and migration files that keep the approved record-family boundary explicit without authorizing live deployment, credentials, or production migration execution in this phase.

## 5. Reconciliation Responsibilities

The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed.

Reconciliation must prefer deterministic correlation keys such as substrate detection record identifiers, analytic-signal identifiers, action-request identifiers, approval identifiers, workflow identifiers, and idempotency keys rather than fuzzy time-window matching.

Stable reconciliation keys must allow operators to compare substrate-native detection output, admitted analytic signals, control-plane records, and n8n execution outcomes without assuming those systems share one lifecycle or one authoritative identifier.

Approved detection substrates are responsible for producing stable substrate-native identifiers and timestamps for substrate detection records and related analytic outputs that downstream control-plane logic may reference.

n8n is responsible for exposing enough workflow-run identifiers, timestamps, execution outcomes, and step-level failure detail that the control-plane runtime can correlate approved intent to observed execution behavior.

Substrate-record-to-alert ingestion contract requirements:

The ingestion boundary must treat `substrate_detection_record_id`, `analytic_signal_id`, and `alert_id` as related but non-interchangeable identifiers.

The ingest path must preserve the upstream `substrate_detection_record_id` as the durable substrate-origin reference, preserve `analytic_signal_id` for the admitted vendor-neutral signal created or updated from that substrate record set, and assign a separate control-plane `alert_id` for the analyst-facing record created or updated from that signal.

The control plane must evaluate whether an incoming upstream signal creates a new alert, updates an existing alert, or is recorded only as a duplicate or restatement linked to an existing alert.

Duplicate or restated upstream analytics signals must not mint a fresh `alert_id` when they do not represent materially new analyst work.

The minimum reconciliation fields for that boundary are `substrate_detection_record_id`, `analytic_signal_id`, `alert_id`, the control-plane deduplication or correlation key, first-seen and last-seen timestamps for the linked upstream signal set, and explicit ingest disposition showing whether the signal created, updated, deduplicated against, or restated an existing alert.

Reconciliation records must preserve which substrate detection records and admitted analytic signals were attached to an alert so later implementations can distinguish repeated upstream output from new analyst work.

Reconciliation records must also preserve how alerts, cases, approval decisions, action requests, hunts, hunt runs, AI traces, and execution outcomes were linked or found to disagree so mismatch tracking remains a first-class control-plane concern.

The minimum stable reconciliation key set for this baseline is:

- `substrate_detection_record_id` for the upstream substrate-native detection, correlation, or alerting record;
- `analytic_signal_id` for the admitted vendor-neutral analytic signal derived from one or more substrate detection records;
- `alert_id` and `case_id` for control-plane triage and investigation ownership;
- `evidence_id` plus preserved provenance metadata for linked artifacts or derived material;
- `observation_id`, `lead_id`, and `recommendation_id` for analyst assertions, investigative direction, and proposed next steps that must remain independently reviewable;
- `approval_decision_id` and `action_request_id` for authorized response intent;
- `hunt_id` and `hunt_run_id` for analyst-directed exploration and each bounded execution of that exploration;
- `ai_trace_id` for preserved AI-assisted interpretation or recommendation context; and
- `execution_surface_type`, `execution_surface_id`, `execution_run_id`, and an action idempotency key for the reviewed automation-substrate or executor run being reconciled.

The AegisOps control-plane runtime is responsible for:

- deciding whether an analytic signal should create or update an alert or case record;
- deciding how evidence, observations, leads, recommendations, hunts, hunt runs, and AI traces are attached to alerts, cases, or independent analyst workflows without collapsing their ownership boundaries;
- deciding whether an action request is pending approval, approved, rejected, expired, canceled, superseded, executing, completed, failed, or unresolved;
- binding approval decisions to exact request context before execution is allowed; and
- marking reconciliation exceptions when upstream substrate records or findings disappear, duplicate workflow triggers arrive, or n8n reports an outcome that does not satisfy the approved intent record.

Observation records must preserve scoped analyst assertions, timestamps, authorship, and linkage to supporting evidence without turning evidence custody into free-form narrative.

Lead records must preserve investigative hypotheses, triage rationale, and disposition state without being treated as equivalent to alert state, case state, or recommendation text.

Recommendation records must preserve proposed next steps, rationale, and review status without being treated as approval, execution, or immutable evidence.

Hunt records must preserve explicit lifecycle state, ownership, hypothesis linkage, and closure rationale even when no case is opened.

Hunt-run reconciliation must preserve whether a run was planned, started, completed, canceled, superseded, or left unresolved, plus which findings, observations, leads, recommendations, or cases it did or did not influence.

AI trace records must preserve generation, review, acceptance, rejection, supersession, and linkage expectations as explicit control-plane state rather than silent prompt history.

Reconciliation must preserve auditable disagreement. When OpenSearch, n8n, and the authoritative control-plane record disagree, the platform must retain that mismatch as an explicit state that operators can inspect and resolve rather than overwriting one side to make the data look clean.

Disagreement between analytics, control-plane, and execution-plane records must remain auditable rather than silently overwritten.

## 6. Minimum Record Identifiers and Lifecycle States

The baseline defines immutable record-family identifiers and explicit lifecycle states for Alert, Case, Evidence, Observation, Lead, Recommendation, Hunt, Hunt Run, AI Trace, Approval Decision, Action Request, and Reconciliation records across the shipped runtime boundary and reviewed persistence contract.

These identifiers and states are minimum control-plane expectations. They must not be inferred from substrate-local alert status, substrate document updates, n8n execution status, or ad hoc analyst notes.

### 6.1 Alert

Minimum identifier expectation for an Alert record:

| Field | Minimum expectation |
| ---- | ---- |
| `alert_id` | Immutable AegisOps control-plane identifier for one alert record. |
| `substrate_detection_record_id` | Required upstream linkage to the originating substrate-native detection, correlation, or alerting record that justified alert creation or update. |
| `analytic_signal_id` | Required vendor-neutral analytic-signal identifier for the admitted upstream signal that created or updated the alert. |
| `case_id` | Optional linkage that becomes required once the alert is promoted into a tracked case. |

Minimum lifecycle states for an Alert record:

| State | Meaning |
| ---- | ---- |
| `new` | The alert record exists and awaits analyst triage. |
| `triaged` | Initial analyst or policy review classified the alert and decided whether deeper work is required. |
| `investigating` | The alert remains an active analyst work item even if a linked case is not yet opened. |
| `escalated_to_case` | The alert remains linked to an active case that now owns the broader investigation. |
| `closed` | Alert handling is complete with an explicit disposition and closure rationale. |
| `reopened` | The alert returned to active review after closure because new evidence, correlation, or review findings changed the decision. |
| `superseded` | The alert is no longer the primary work-tracking record because another alert or case absorbed responsibility through an explicit linkage. |

### 6.2 Case

Minimum identifier expectation for a Case record:

| Field | Minimum expectation |
| ---- | ---- |
| `case_id` | Immutable AegisOps control-plane identifier for one investigation record. |
| `alert_id` | Required linkage to the originating alert when the case came from alert promotion. |
| `analytic_signal_id` or `substrate_detection_record_id` | Required when the case is opened directly from upstream analytic intake or needs durable linkage to the driving signal set. |
| `evidence_id` | One or more explicit evidence links rather than implicit attachment through notes or workflow metadata. |

Minimum lifecycle states for a Case record:

| State | Meaning |
| ---- | ---- |
| `open` | The case is created and awaits or has just begun analyst ownership. |
| `investigating` | Investigation, evidence gathering, or coordination work is actively in progress. |
| `pending_action` | The case is waiting for an approved or proposed response step, external dependency, or validation result before closure can proceed. |
| `contained_pending_validation` | Immediate response or containment occurred, but verification or residual-risk review remains open. |
| `closed` | Case handling is complete with recorded disposition, closure rationale, and any follow-up requirements. |
| `reopened` | The case returned to active handling after closure because new facts or failed validation invalidated the prior closure. |
| `superseded` | The case was intentionally replaced or merged into another case or incident while preserving linkage and audit history. |

### 6.3 Evidence

Minimum identifier expectation for an Evidence record:

| Field | Minimum expectation |
| ---- | ---- |
| `evidence_id` | Immutable AegisOps control-plane identifier for one evidence record. |
| `source_record_id` | Required reference to the originating source artifact, datastore object, upload, or acquisition event. |
| `case_id` or `alert_id` | Required control-plane linkage showing which alert, case, or related work item currently relies on the evidence. |
| Provenance metadata | Required capture context such as collector identity, acquisition timestamp, source system, and derivation relationship when applicable. |

Minimum lifecycle states for an Evidence record:

| State | Meaning |
| ---- | ---- |
| `collected` | The evidence item was acquired and recorded with initial provenance metadata. |
| `validated` | Provenance, integrity, or acquisition quality checks completed enough for analyst use. |
| `linked` | The evidence is attached to one or more control-plane records as supporting material. |
| `superseded` | A newer or more authoritative evidence record replaced this one without deleting its historical relevance. |
| `withdrawn` | The evidence remains historically visible, but it must no longer be relied on because provenance, integrity, or scope was invalidated. |

### 6.4 Observation

Minimum identifier expectation for an Observation record:

| Field | Minimum expectation |
| ---- | ---- |
| `observation_id` | Immutable AegisOps control-plane identifier for one observation record. |
| `hunt_id`, `hunt_run_id`, `alert_id`, or `case_id` | Required linkage showing whether the observation belongs to a stand-alone hunt workflow or to tracked alert or case work. |
| Supporting evidence linkage set | Required explicit references to supporting evidence, source artifacts, or analytic records when the observation relies on them. |
| Author and scope metadata | Required authorship, timestamp, and scope statement describing what was observed, where, and under what bounded context. |

Minimum lifecycle states for an Observation record:

| State | Meaning |
| ---- | ---- |
| `captured` | The observation is recorded with authorship, scope, and initial supporting context. |
| `confirmed` | The observation was reviewed and remains a valid investigative fact within the stated scope. |
| `challenged` | Review found ambiguity, contradiction, or insufficient support that must remain visible until resolved. |
| `superseded` | A newer or more precise observation replaced this one while preserving historical linkage. |
| `withdrawn` | The observation remains visible for auditability, but it must no longer be relied on because it was invalidated or recorded against the wrong scope. |

### 6.5 Lead

Minimum identifier expectation for a Lead record:

| Field | Minimum expectation |
| ---- | ---- |
| `lead_id` | Immutable AegisOps control-plane identifier for one lead record. |
| `observation_id`, `analytic_signal_id`, or `hunt_run_id` | Required originating context that explains which observation, admitted analytic signal, or bounded hunt execution produced the lead. |
| `alert_id` or `case_id` | Optional promotion linkage that becomes required once the lead is explicitly promoted into alert or case work. |
| Triage owner and rationale | Required accountable owner, creation timestamp, and preserved statement of why the lead merits or no longer merits follow-up. |

Minimum lifecycle states for a Lead record:

| State | Meaning |
| ---- | ---- |
| `open` | The lead exists as a triage-worthy signal awaiting or undergoing analyst review. |
| `triaged` | An analyst reviewed the lead and recorded whether it should remain under observation, promote, or close. |
| `promoted_to_alert` | The lead remains historically visible while an explicitly linked alert now owns the routed analyst queue lifecycle. |
| `promoted_to_case` | The lead remains historically visible while an explicitly linked case now owns the durable investigation lifecycle. |
| `closed` | The lead no longer requires follow-up, with rationale preserved on the lead record itself. |
| `superseded` | Another lead, alert, or case replaced this lead as the primary investigative signal while preserving promotion linkage. |

### 6.6 Recommendation

Minimum identifier expectation for a Recommendation record:

| Field | Minimum expectation |
| ---- | ---- |
| `recommendation_id` | Immutable AegisOps control-plane identifier for one recommendation record. |
| `lead_id`, `hunt_run_id`, `alert_id`, or `case_id` | Required upstream context showing which investigative work item or hunt activity the recommendation informs. |
| `ai_trace_id` | Required when AI-assisted interpretation materially contributed to the recommendation text or ranking. |
| Review owner and intended outcome | Required accountable reviewer, creation timestamp, and preserved statement of the proposed next step or decision being advised. |

Minimum lifecycle states for a Recommendation record:

| State | Meaning |
| ---- | ---- |
| `proposed` | The recommendation exists as advisory guidance and has not yet been reviewed by the accountable operator. |
| `under_review` | The recommendation is actively being evaluated for acceptance, rejection, or revision. |
| `accepted` | Review accepted the recommendation as valid guidance, but further records are still required for execution or case state. |
| `rejected` | Review determined the recommendation should not guide further action. |
| `materialized` | The recommendation produced an explicit downstream action request, task, or analyst-owned follow-up while remaining reviewable as advisory context. |
| `superseded` | A newer recommendation replaced this one for the same investigative question or operational target. |
| `withdrawn` | The recommendation remains historically visible, but it must no longer be relied on because its basis or scope was invalidated. |

### 6.7 Hunt

Minimum identifier expectation for a Hunt record:

| Field | Minimum expectation |
| ---- | ---- |
| `hunt_id` | Immutable AegisOps control-plane identifier for one hunt record. |
| Hypothesis statement and version | Required preserved hypothesis text plus revision or version metadata so later runs can be evaluated against the same question. |
| Owner and scope boundary | Required accountable owner, intended target scope, and opening timestamp for the analyst-directed hunt. |
| `alert_id` or `case_id` | Optional linkage when the hunt is attached to existing tracked work rather than remaining a stand-alone hunt workflow. |

Minimum lifecycle states for a Hunt record:

| State | Meaning |
| ---- | ---- |
| `draft` | The hunt exists as a hypothesis and planned scope but is not yet active analyst work. |
| `active` | The hunt is approved or assigned for analyst execution and may accumulate multiple bounded runs. |
| `on_hold` | The hunt remains open but is intentionally paused pending more context, access, or competing priority. |
| `concluded` | The hunt question reached a reviewable outcome and no additional runs are currently planned. |
| `closed` | The hunt is complete with preserved rationale, closure summary, and any linked downstream records. |
| `superseded` | A revised or replacement hunt now owns the active hypothesis while this hunt remains historically visible. |

### 6.8 Hunt Run

Minimum identifier expectation for a Hunt Run record:

| Field | Minimum expectation |
| ---- | ---- |
| `hunt_run_id` | Immutable AegisOps control-plane identifier for one bounded hunt-run record. |
| `hunt_id` | Required linkage to the hunt whose hypothesis and ownership context this run evaluates. |
| Scope snapshot and execution plan | Required bounded scope details: time window, dataset or target scope, and query or procedure reference for the specific run. |
| Output linkage set | Required explicit links to any findings, observations, leads, recommendations, alerts, or cases that the run influenced. |

Minimum lifecycle states for a Hunt Run record:

| State | Meaning |
| ---- | ---- |
| `planned` | The run is defined with bounded scope and intent but execution has not started. |
| `running` | Execution of the bounded hunt scope is in progress and intermediate outputs may still arrive. |
| `completed` | The run finished with a reviewable outcome summary and preserved output linkages. |
| `canceled` | The run was intentionally stopped before completing its planned scope. |
| `superseded` | Another run replaced this run for the same hypothesis and scope boundary under revised execution context. |
| `unresolved` | Operators cannot yet prove whether the run completed correctly, produced complete outputs, or requires manual follow-up. |

### 6.9 AI Trace

Minimum identifier expectation for an AI Trace record:

| Field | Minimum expectation |
| ---- | ---- |
| `ai_trace_id` | Immutable AegisOps control-plane identifier for one AI-trace record. |
| Subject linkage set | Required explicit links to the hunt, hunt run, observation, lead, recommendation, alert, or case records the trace informed. |
| Model and prompt provenance | Required model identity, prompt or instruction version, generation timestamp, and material input references. |
| Reviewer and disposition metadata | Required reviewer identity and recorded decision about whether the trace remains usable as advisory context. |

Minimum lifecycle states for an AI Trace record:

| State | Meaning |
| ---- | ---- |
| `generated` | The AI trace was produced and linked to the context it interpreted, but no review outcome exists yet. |
| `under_review` | The trace is being evaluated for whether it may remain linked as advisory context. |
| `accepted_for_reference` | Reviewers allowed the trace to remain linked as advisory context, but it still does not replace evidence, lead state, or case state. |
| `rejected_for_reference` | Review determined the trace must not be relied on for ongoing investigative or response work. |
| `superseded` | A newer or better-reviewed trace replaced this one for the same interpretive context. |
| `withdrawn` | The trace remains historically visible, but it must no longer be used because its inputs, provenance, or review basis were invalidated. |

Promotion of a lead into alert or case work must create or update the destination alert or case record while preserving the original lead as a first-class control-plane record with explicit promotion linkage.

Observation records, recommendation records, AI trace records, and case notes may contribute context to promotion decisions, but none of them may become the sole system of record for lead state or lead promotion history.

Hunt, hunt-run, observation, lead, recommendation, and AI trace records may attach to alerts, cases, or stand-alone hunt workflows, but attachment alone does not transfer lifecycle ownership or collapse one record family into another.

### 6.10 Approval Decision

Minimum identifier expectation for an Approval Decision record:

| Field | Minimum expectation |
| ---- | ---- |
| `approval_decision_id` | Immutable AegisOps control-plane identifier for one approval decision record. |
| `action_request_id` | Required linkage to the exact action request under review. |
| Approver identity set | Required accountable identity for each approver or reviewer participating in the decision. |
| Target snapshot and payload hash | Required binding inputs that prove which reviewed context the decision authorized or rejected. |

Minimum lifecycle states for an Approval Decision record:

| State | Meaning |
| ---- | ---- |
| `pending` | The approval decision is open and quorum or reviewer action is not yet complete. |
| `approved` | The required approval outcome and quorum, if any, were satisfied before expiry. |
| `rejected` | The reviewed request was explicitly denied. |
| `expired` | The approval window closed before a valid executable approval outcome remained available. |
| `canceled` | The approval decision was intentionally stopped because the underlying request was withdrawn or replaced before completion. |
| `superseded` | A newer approval decision replaced this decision for the same requested intent under revised reviewed context. |

### 6.11 Action Request

Minimum identifier expectation for an Action Request record:

| Field | Minimum expectation |
| ---- | ---- |
| `action_request_id` | Immutable AegisOps control-plane identifier for one requested response action. |
| `approval_decision_id` | Explicit linkage to the governing approval decision once one exists. |
| `case_id`, `alert_id`, or `analytic_signal_id` | Required upstream context showing which investigative work item or admitted analytic signal justified the request. |
| Idempotency key | Required stable execution correlation key that survives retries and duplicate-delivery checks. |

Minimum lifecycle states for an Action Request record:

| State | Meaning |
| ---- | ---- |
| `draft` | The request exists but is not yet ready to enter approval or execution handling. |
| `pending_approval` | The request is complete enough for review and is waiting on approval outcome. |
| `approved` | The request has a valid linked approval decision and may proceed to execution readiness checks. |
| `rejected` | The request cannot execute because the approval decision denied it. |
| `expired` | The request cannot execute because its approval or execution window elapsed. |
| `canceled` | The request was intentionally withdrawn before execution completed. |
| `superseded` | The request was replaced by a newer request for revised target scope, payload, or timing. |
| `executing` | At least one correlated execution attempt is in progress under the approved binding context. |
| `completed` | Execution and required post-action verification completed well enough to close the request. |
| `failed` | Execution or required verification concluded unsuccessfully under the current approved request. |
| `unresolved` | Operators cannot yet prove whether the request was executed correctly, failed partially, or needs manual recovery. |

### 6.12 Reconciliation

Minimum identifier expectation for a Reconciliation record:

| Field | Minimum expectation |
| ---- | ---- |
| `reconciliation_id` | Immutable AegisOps control-plane identifier for one reconciliation record. |
| Subject linkage set | Required explicit references to the alert, case, approval decision, action request, hunt, hunt run, AI trace, and execution records or upstream analytic identifiers being compared. |
| `substrate_detection_record_id`, `analytic_signal_id`, or `execution_run_id` | Required external or execution-plane correlation identifiers proving which cross-system records were evaluated. |
| Correlation key and mismatch summary | Required deterministic comparison key, reconciliation scope, and preserved statement of which fields or lifecycle facts aligned or diverged. |

Minimum lifecycle states for a Reconciliation record:

| State | Meaning |
| ---- | ---- |
| `pending` | The linked records were identified, but comparison or correlation has not yet completed. |
| `matched` | The linked analytics, control-plane, and execution-plane records align well enough that no open discrepancy remains. |
| `mismatched` | The linked records disagree on identifiers, lifecycle, payload binding, timing, or outcome and require explicit review. |
| `stale` | The prior comparison no longer reflects the latest upstream or downstream state and must be recomputed or reviewed again. |
| `resolved` | Operators recorded how the mismatch or gap was resolved without deleting the prior disagreement evidence. |
| `superseded` | A newer reconciliation record replaced this one for the same bounded comparison scope. |

Reconciliation records provide the explicit cross-system home for mismatch tracking and resolution. They do not replace the lifecycle ownership of alerts, cases, approvals, action requests, hunts, hunt runs, AI traces, or execution outcomes.

These lifecycle states establish the minimum reviewable transitions for later reconciliation, retry, expiry, duplicate suppression, and manual recovery work.

No control-plane record family may silently inherit lifecycle from substrate-local alerts or n8n execution history. Cross-system state must be linked through explicit identifiers and reconciliation records instead.

## 7. Retry, Dead-Letter, and Manual Recovery Responsibilities

Retry policy belongs to the control-plane intent record, while duplicate suppression and step-level retry behavior inside a running workflow belong to n8n.

OpenSearch may re-emit or restate analytic signals according to its own alerting behavior, but deduplication of downstream analyst work belongs to the AegisOps control-plane runtime rather than to OpenSearch.

Dead-letter responsibility begins when the platform can no longer prove whether an approved intent was never executed, is still executing, or executed with an unknown result.

The control-plane runtime must be able to mark a record for manual review when:

- approval expired before a correlated execution started;
- an execution started without a reconcilable approved request;
- multiple executions appear for one approved request without an allowed retry policy;
- execution finished but post-action verification is missing or inconclusive; or
- upstream analytic context changed materially while downstream work remained open.

Manual recovery procedures must support re-drive, cancellation, supersession, and explicit operator annotation without rewriting historical approval or execution evidence.

Manual recovery must also preserve why the operator chose the recovery path, which records were linked or superseded, and whether follow-up verification or rollback work remains open.

## 8. Idempotency and Audit Expectations

Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays.

Idempotency keys must bind to the approved request scope, payload hash, target snapshot, and intended execution path closely enough that a replay can be detected without inferring operator intent from timestamps alone.

Auditability requires separate evidence for:

- the analytic signal that justified work,
- the control-plane record that tracked alert or case ownership,
- the approval decision that authorized or rejected action,
- the action request that defined exact execution intent, and
- the n8n execution record that shows what actually ran and what outcome was observed.

No single component log should be treated as sufficient to reconstruct the entire decision chain when that would blur responsibility boundaries or allow silent loss of approval evidence.

## 9. Baseline Alignment Notes

This model keeps component boundaries explicit while aligning to the shipped `control-plane/` runtime home and the reviewed `postgres/control-plane/` persistence contract.

It reinforces the requirements baseline rule that detection and execution remain separate, the domain-model rule that findings, approvals, and execution are distinct records, the response-action safety rule that approval is not the same as execution, and the Phase 10 thesis that external detection and automation substrates do not become the authority for platform-owned workflow truth.

This baseline already aligns to the shipped `control-plane/` runtime home and the reviewed `postgres/control-plane/` persistence contract. Later runtime and datastore work must preserve that authority boundary rather than redefine where authoritative control-plane truth lives.
