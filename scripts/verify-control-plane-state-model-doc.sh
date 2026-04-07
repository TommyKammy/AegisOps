#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/control-plane-state-model.md"

required_headings=(
  "# AegisOps Control-Plane State and Reconciliation Model"
  "## 1. Purpose"
  "## 2. Baseline Design Constraints"
  "## 3. Baseline Ownership and Source of Truth"
  "## 4. Approved Persistence Boundary"
  "## 5. Reconciliation Responsibilities"
  "## 6. Minimum Record Identifiers and Lifecycle States"
  "## 7. Retry, Dead-Letter, and Manual Recovery Responsibilities"
  "## 8. Idempotency and Audit Expectations"
  "## 9. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the approved baseline control-plane state model for AegisOps across the live control-plane runtime boundary and the reviewed PostgreSQL control-plane persistence boundary."
  "This document defines ownership, source-of-truth expectations, and recovery responsibilities only. It does not introduce a live datastore, schema migration, API service, or runtime deployment in this phase."
  'The baseline must keep platform-owned control state explicit across the shipped `control-plane/` runtime boundary and the reviewed `postgres/control-plane/` persistence-contract home.'
  'The repository already ships a dedicated control-plane runtime home, so this document is the normative definition of which component owns which state and what must be reconciled across runtime, persistence, analytics, and execution boundaries.'
  'The reviewed local control-plane runtime now reports `persistence_mode="postgresql"` and treats the PostgreSQL-backed control-plane store as the authoritative persistence path for local runtime and inspection flows, while `postgres/control-plane/` remains the reviewed schema and migration home and OpenSearch remains the analytics-plane store for telemetry and detection outputs.'
  '| `Substrate Detection Record` | Approved upstream detection substrate | The detection substrate remains the system of record for substrate-native detection, correlation, and alerting artifacts plus their native identifiers. |'
  '| `Analytic Signal` | AegisOps control-plane intake boundary referencing approved upstream detection substrates | Analytic signals are admitted upstream product inputs that preserve substrate-native linkage without becoming the durable analyst work-tracking record for the platform. |'
  '| `Finding` | Approved detection substrate or analytics plane | Findings remain upstream analytic assertions and must not be reused as downstream control-plane lifecycle state. |'
  '| `Alert` | AegisOps control-plane alert record | Alert lifecycle must not be inferred from OpenSearch alert documents or n8n execution history alone. |'
  '| `Case` | AegisOps control-plane case record | Case ownership, analyst status, and evidence linkage must not dissolve into workflow runs or dashboard state. |'
  '| `Evidence` | AegisOps control-plane evidence record | Evidence custody, provenance, and record linkage must remain explicit instead of dissolving into case notes, AI output, or workflow metadata. |'
  '| `Observation` | AegisOps control-plane observation record | Observations capture analyst-asserted investigative facts and must remain distinct from raw evidence artifacts, AI trace text, and case status fields. |'
  '| `Lead` | AegisOps control-plane lead record | Leads preserve candidate hypotheses or follow-up directions without silently promoting them into alerts, cases, or approved action intent. |'
  '| `Recommendation` | AegisOps control-plane recommendation record | Recommendations preserve proposed analyst or AI-advised next steps without replacing approval decisions, action requests, or execution outcomes. |'
  '| `Approval Decision` | AegisOps control-plane approval record | Approval is a first-class control decision and must not be reconstructed from whether a workflow happened to run. |'
  '| `Hunt` | AegisOps control-plane hunt record | Hunt lifecycle must remain analyst-directed and reviewable rather than inferred from ad hoc queries or downstream workflow runs. |'
  '| `Hunt Run` | AegisOps control-plane hunt-run record | Each hunt run must preserve bounded scope, execution context, and outcome for one hunt iteration without replacing alerts or cases. |'
  '| `AI Trace` | AegisOps control-plane AI-trace record | AI trace records must preserve prompt, model, review, and linkage context without mutating evidence custody or analyst-owned dispositions. |'
  '| `Reconciliation` | AegisOps control-plane reconciliation record | Cross-system linkage, mismatch tracking, and resolution state must not dissolve into alert fields, case notes, or execution-surface metadata. |'
  '| `Action Execution` | AegisOps control-plane action-execution record | `Action Execution` remains the authoritative control-plane record for approved-versus-actual execution, while reviewed automation substrates and executor surfaces contribute correlated run identifiers, receipts, step progress, and other surface-local runtime evidence. |'
  "Execution-surface runtime history must not become the implicit system of record for case state, approval state, or action-request intent."
  "Substrate-native detection records and admitted analytic signals remain upstream reconciliation inputs, but they do not own downstream case, approval, or execution-policy state."
  "The minimum control-plane record families for this baseline are Alert, Case, Evidence, Observation, Lead, Recommendation, Approval Decision, Action Request, Hunt, Hunt Run, AI Trace, Reconciliation, and Action Execution."
  '- analytic signals, alerts, cases, evidence, observations, leads, recommendations, approvals, action requests, hunts, hunt runs, AI traces, action-execution records, and reconciliation records are platform-owned control records whose authoritative home is the AegisOps control-plane runtime boundary with the reviewed PostgreSQL contract rooted under `postgres/control-plane/`;'
  '- reviewed automation substrates and executor surfaces remain the owners of workflow-local runtime state, queued jobs, step progress, receipts, retry artifacts internal to a running surface, and similar execution evidence that the control plane must correlate into authoritative `Action Execution` and `Reconciliation` records; and'
  'The approved persistence boundary for those platform-owned control records is the AegisOps-owned PostgreSQL control-plane boundary reviewed under `postgres/control-plane/`.'
  "That reviewed PostgreSQL-backed boundary may share a PostgreSQL engine class with n8n, but it must not collapse control-plane ownership into n8n-owned metadata tables or runtime workflow state."
  "If a later deployment uses one PostgreSQL cluster for both concerns, it must still preserve an explicit ownership split through separate AegisOps-controlled schemas, tables, migration history, and access controls for control-plane records."
  "OpenSearch must not become the authoritative store for alert lifecycle, case state, evidence custody, approval decisions, action-request intent, hunt lifecycle, hunt-run status, or AI trace review state."
  "n8n metadata tables and workflow execution history must not become the authoritative store for alert ownership, case ownership, evidence linkage, recommendation review state, approval decisions, or action-request intent."
  "The approved ownership split for the reviewed PostgreSQL-backed boundary is:"
  '- AegisOps control-plane storage owns authoritative platform records, including alerts, cases, evidence, observations, leads, recommendations, approval decisions, action requests, hunts, hunt runs, AI traces, action-execution records, and reconciliation state that binds those records to analytics and execution outcomes.'
  "- n8n-owned PostgreSQL storage owns runtime workflow metadata, execution attempts, step progress, connector-local execution details, retry artifacts internal to a running workflow, and similar orchestration-engine state."
  "- OpenSearch owns telemetry, findings, and OpenSearch-native analytic or alerting artifacts that act as upstream signals rather than downstream control-plane truth."
  "This boundary approves where authoritative control-plane records belong for the live runtime boundary, but it does not approve live PostgreSQL provisioning, schema migrations, credentials, or runtime deployment changes in this phase."
  'The repository already materializes a version-controlled schema baseline for that boundary under `postgres/control-plane/`, including reviewed schema manifests and migration files that keep the approved record-family boundary explicit without authorizing live deployment, credentials, or production migration execution in this phase.'
  "The control plane is responsible for reconciling approved action intent against observed execution-surface outcomes and for recording when reconciliation is incomplete, stale, or failed."
  "Reconciliation must prefer deterministic correlation keys such as substrate detection record identifiers, analytic-signal identifiers, action-request identifiers, approval identifiers, workflow identifiers, and idempotency keys rather than fuzzy time-window matching."
  "Stable reconciliation keys must allow operators to compare substrate-native detection output, admitted analytic signals, control-plane records, and execution-surface outcomes without assuming those systems share one lifecycle or one authoritative identifier."
  "The reviewed automation substrate or executor surface is responsible for exposing enough run identifiers, timestamps, execution outcomes, and step-level failure detail that the control-plane runtime can correlate approved intent to observed execution behavior."
  'Substrate-record-to-alert ingestion contract requirements:'
  'The ingestion boundary must treat `substrate_detection_record_id`, `analytic_signal_id`, and `alert_id` as related but non-interchangeable identifiers.'
  'The ingest path must preserve the upstream `substrate_detection_record_id` as the durable substrate-origin reference, preserve `analytic_signal_id` for the admitted vendor-neutral signal created or updated from that substrate record set, and assign a separate control-plane `alert_id` for the analyst-facing record created or updated from that signal.'
  'The control plane must evaluate whether an incoming upstream signal creates a new alert, updates an existing alert, or is recorded only as a duplicate or restatement linked to an existing alert.'
  'Duplicate or restated upstream analytics signals must not mint a fresh `alert_id` when they do not represent materially new analyst work.'
  'The minimum reconciliation fields for that boundary are `substrate_detection_record_id`, `analytic_signal_id`, `alert_id`, the control-plane deduplication or correlation key, first-seen and last-seen timestamps for the linked upstream signal set, and explicit ingest disposition showing whether the signal created, updated, deduplicated against, or restated an existing alert.'
  'Reconciliation records must preserve which substrate detection records and admitted analytic signals were attached to an alert so later implementations can distinguish repeated upstream output from new analyst work.'
  'Reconciliation records must also preserve how alerts, cases, approval decisions, action requests, hunts, hunt runs, AI traces, and execution outcomes were linked or found to disagree so mismatch tracking remains a first-class control-plane concern.'
  "The baseline defines immutable record-family identifiers and explicit lifecycle states for Alert, Case, Evidence, Observation, Lead, Recommendation, Hunt, Hunt Run, AI Trace, Approval Decision, Action Request, Action Execution, and Reconciliation records across the shipped runtime boundary and reviewed persistence contract."
  "These identifiers and states are minimum control-plane expectations. They must not be inferred from substrate-local alert status, substrate document updates, n8n execution status, or ad hoc analyst notes."
  '| `alert_id` | Immutable AegisOps control-plane identifier for one alert record. |'
  '| `substrate_detection_record_id` | Required upstream linkage to the originating substrate-native detection, correlation, or alerting record that justified alert creation or update. |'
  '| `analytic_signal_id` | Required vendor-neutral analytic-signal identifier for the admitted upstream signal that created or updated the alert. |'
  '| `case_id` | Optional linkage that becomes required once the alert is promoted into a tracked case. |'
  '| `new` | The alert record exists and awaits analyst triage. |'
  '| `triaged` | Initial analyst or policy review classified the alert and decided whether deeper work is required. |'
  '| `investigating` | The alert remains an active analyst work item even if a linked case is not yet opened. |'
  '| `escalated_to_case` | The alert remains linked to an active case that now owns the broader investigation. |'
  '| `closed` | Alert handling is complete with an explicit disposition and closure rationale. |'
  '| `reopened` | The alert returned to active review after closure because new evidence, correlation, or review findings changed the decision. |'
  '| `superseded` | The alert is no longer the primary work-tracking record because another alert or case absorbed responsibility through an explicit linkage. |'
  '| `case_id` | Immutable AegisOps control-plane identifier for one investigation record. |'
  '| `alert_id` | Required linkage to the originating alert when the case came from alert promotion. |'
  '| `analytic_signal_id` or `substrate_detection_record_id` | Required when the case is opened directly from upstream analytic intake or needs durable linkage to the driving signal set. |'
  '| `evidence_id` | One or more explicit evidence links rather than implicit attachment through notes or workflow metadata. |'
  '| `open` | The case is created and awaits or has just begun analyst ownership. |'
  '| `investigating` | Investigation, evidence gathering, or coordination work is actively in progress. |'
  '| `pending_action` | The case is waiting for an approved or proposed response step, external dependency, or validation result before closure can proceed. |'
  '| `contained_pending_validation` | Immediate response or containment occurred, but verification or residual-risk review remains open. |'
  '| `closed` | Case handling is complete with recorded disposition, closure rationale, and any follow-up requirements. |'
  '| `reopened` | The case returned to active handling after closure because new facts or failed validation invalidated the prior closure. |'
  '| `superseded` | The case was intentionally replaced or merged into another case or incident while preserving linkage and audit history. |'
  '| `evidence_id` | Immutable AegisOps control-plane identifier for one evidence record. |'
  '| `source_record_id` | Required reference to the originating source artifact, datastore object, upload, or acquisition event. |'
  '| `case_id` or `alert_id` | Required control-plane linkage showing which alert, case, or related work item currently relies on the evidence. |'
  '| Provenance metadata | Required capture context such as collector identity, acquisition timestamp, source system, and derivation relationship when applicable. |'
  '| `collected` | The evidence item was acquired and recorded with initial provenance metadata. |'
  '| `validated` | Provenance, integrity, or acquisition quality checks completed enough for analyst use. |'
  '| `linked` | The evidence is attached to one or more control-plane records as supporting material. |'
  '| `superseded` | A newer or more authoritative evidence record replaced this one without deleting its historical relevance. |'
  '| `withdrawn` | The evidence remains historically visible, but it must no longer be relied on because provenance, integrity, or scope was invalidated. |'
  '| `approval_decision_id` | Immutable AegisOps control-plane identifier for one approval decision record. |'
  '| `action_request_id` | Required linkage to the exact action request under review. |'
  '| Approver identity set | Required accountable identity for each approver or reviewer participating in the decision. |'
  '| Target snapshot, payload hash, and approved expiry window | Required binding inputs that prove which reviewed context and execution window the decision authorized or rejected. |'
  '| `pending` | The approval decision is open and quorum or reviewer action is not yet complete. |'
  '| `approved` | The required approval outcome and quorum, if any, were satisfied before expiry. |'
  '| `rejected` | The reviewed request was explicitly denied. |'
  '| `expired` | The approval window closed before a valid executable approval outcome remained available. |'
  '| `canceled` | The approval decision was intentionally stopped because the underlying request was withdrawn or replaced before completion. |'
  '| `superseded` | A newer approval decision replaced this decision for the same requested intent under revised reviewed context. |'
  '| `action_request_id` | Immutable AegisOps control-plane identifier for one requested response action. |'
  '| `approval_decision_id` | Explicit linkage to the governing approval decision once one exists. |'
  '| `case_id`, `alert_id`, or `analytic_signal_id` | Required upstream context showing which investigative work item or admitted analytic signal justified the request. |'
  '| Idempotency key | Required stable execution correlation key that survives retries and duplicate-delivery checks. |'
  '| `draft` | The request exists but is not yet ready to enter approval or execution handling. |'
  '| `pending_approval` | The request is complete enough for review and is waiting on approval outcome. |'
  '| `approved` | The request has a valid linked approval decision and may proceed to execution readiness checks. |'
  '| `rejected` | The request cannot execute because the approval decision denied it. |'
  '| `expired` | The request cannot execute because its approval or execution window elapsed. |'
  '| `canceled` | The request was intentionally withdrawn before execution completed. |'
  '| `superseded` | The request was replaced by a newer request for revised target scope, payload, or timing. |'
  '| `executing` | At least one correlated execution attempt is in progress under the approved binding context. |'
  '| `completed` | Execution and required post-action verification completed well enough to close the request. |'
  '| `failed` | Execution or required verification concluded unsuccessfully under the current approved request. |'
  '| `unresolved` | Operators cannot yet prove whether the request was executed correctly, failed partially, or needs manual recovery. |'
  "These lifecycle states establish the minimum reviewable transitions for later reconciliation, retry, expiry, duplicate suppression, and manual recovery work."
  "No control-plane record family may silently inherit lifecycle from substrate-local alerts or execution-surface runtime history. Cross-system state must be linked through explicit identifiers and reconciliation records instead."
  "Hunt records must preserve explicit lifecycle state, ownership, hypothesis linkage, and closure rationale even when no case is opened."
  "Observation records must preserve scoped analyst assertions, timestamps, authorship, and linkage to supporting evidence without turning evidence custody into free-form narrative."
  "Lead records must preserve investigative hypotheses, triage rationale, and disposition state without being treated as equivalent to alert state, case state, or recommendation text."
  "Recommendation records must preserve proposed next steps, rationale, and review status without being treated as approval, execution, or immutable evidence."
  "Hunt-run reconciliation must preserve whether a run was planned, started, completed, canceled, superseded, or left unresolved, plus which findings, observations, leads, recommendations, or cases it did or did not influence."
  "AI trace records must preserve generation, review, acceptance, rejection, supersession, and linkage expectations as explicit control-plane state rather than silent prompt history."
  "Disagreement between analytics, control-plane, and execution-plane records must remain auditable rather than silently overwritten."
  "Minimum identifier expectation for an Observation record:"
  '| `observation_id` | Immutable AegisOps control-plane identifier for one observation record. |'
  '| `captured` | The observation is recorded with authorship, scope, and initial supporting context. |'
  "Minimum identifier expectation for a Lead record:"
  '| `lead_id` | Immutable AegisOps control-plane identifier for one lead record. |'
  '| `promoted_to_alert` | The lead remains historically visible while an explicitly linked alert now owns the routed analyst queue lifecycle. |'
  "Minimum identifier expectation for a Recommendation record:"
  '| `recommendation_id` | Immutable AegisOps control-plane identifier for one recommendation record. |'
  '| `materialized` | The recommendation produced an explicit downstream action request, task, or analyst-owned follow-up while remaining reviewable as advisory context. |'
  "Minimum identifier expectation for a Hunt record:"
  '| `hunt_id` | Immutable AegisOps control-plane identifier for one hunt record. |'
  '| `active` | The hunt is approved or assigned for analyst execution and may accumulate multiple bounded runs. |'
  "Minimum identifier expectation for a Hunt Run record:"
  '| `hunt_run_id` | Immutable AegisOps control-plane identifier for one bounded hunt-run record. |'
  '| `running` | Execution of the bounded hunt scope is in progress and intermediate outputs may still arrive. |'
  "Minimum identifier expectation for an AI Trace record:"
  '| `ai_trace_id` | Immutable AegisOps control-plane identifier for one AI-trace record. |'
  '| `accepted_for_reference` | Reviewers allowed the trace to remain linked as advisory context, but it still does not replace evidence, lead state, or case state. |'
  "Minimum identifier expectation for a Reconciliation record:"
  '| `reconciliation_id` | Immutable AegisOps control-plane identifier for one reconciliation record. |'
  '| `mismatched` | The linked records disagree on identifiers, lifecycle, payload binding, timing, or outcome and require explicit review. |'
  "Reconciliation records provide the explicit cross-system home for mismatch tracking and resolution. They do not replace the lifecycle ownership of alerts, cases, approvals, action requests, hunts, hunt runs, AI traces, or execution outcomes."
  "Promotion of a lead into alert or case work must create or update the destination alert or case record while preserving the original lead as a first-class control-plane record with explicit promotion linkage."
  "Observation records, recommendation records, AI trace records, and case notes may contribute context to promotion decisions, but none of them may become the sole system of record for lead state or lead promotion history."
  "Hunt, hunt-run, observation, lead, recommendation, and AI trace records may attach to alerts, cases, or stand-alone hunt workflows, but attachment alone does not transfer lifecycle ownership or collapse one record family into another."
  "- marking reconciliation exceptions when upstream substrate records or findings disappear, duplicate execution triggers arrive, or an execution surface reports an outcome that does not satisfy the approved intent record."
  "Retry policy belongs to the control-plane intent record, while duplicate suppression and step-level retry behavior inside a running automation-substrate or executor run belong to the execution surface."
  "Dead-letter responsibility begins when the platform can no longer prove whether an approved intent was never executed, is still executing, or executed with an unknown result."
  "Manual recovery procedures must support re-drive, cancellation, supersession, and explicit operator annotation without rewriting historical approval or execution evidence."
  "Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays."
  "- the execution-surface record that shows what actually ran and what outcome was observed."
  'This baseline already aligns to the shipped `control-plane/` runtime home and the reviewed `postgres/control-plane/` persistence contract. Later runtime and datastore work must preserve that authority boundary rather than redefine where authoritative control-plane truth lives.'
)

forbidden_phrases=(
  "This document defines the approved baseline control-plane state model for AegisOps before any dedicated control service or datastore is implemented."
  "The baseline must keep platform-owned control state explicit even though no dedicated AegisOps control service exists yet."
  "Until a future implementation materializes a dedicated control schema or API boundary, this document is the normative definition of which component owns which state and what must later be reconciled across component boundaries."
  "The approved future persistence boundary for those platform-owned control records is an AegisOps-owned PostgreSQL-backed control-plane datastore boundary."
  "The approved ownership split for a future PostgreSQL-backed implementation is:"
  "The future AegisOps control layer is responsible for:"
  "Reconciliation must preserve auditable disagreement. When OpenSearch, n8n, and the future control record disagree, the platform must retain that mismatch as an explicit state that operators can inspect and resolve rather than overwriting one side to make the data look clean."
  'No new live datastore rollout is approved in this phase. The current control-plane runtime remains `persistence_mode="in_memory"`, `postgres/control-plane/` remains the reviewed schema and migration home for future PostgreSQL-backed persistence work, and OpenSearch remains the analytics-plane store for telemetry and detection outputs.'
  '| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state | n8n owns execution-attempt state, step progress, and connector-specific runtime details. |'
  "n8n execution history must not become the implicit system of record for case state, approval state, or action-request intent."
  "- action execution state remains execution-plane runtime state owned by n8n and backed by PostgreSQL; and"
  "The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed."
  "Stable reconciliation keys must allow operators to compare substrate-native detection output, admitted analytic signals, control-plane records, and n8n execution outcomes without assuming those systems share one lifecycle or one authoritative identifier."
  "n8n is responsible for exposing enough workflow-run identifiers, timestamps, execution outcomes, and step-level failure detail that the control-plane runtime can correlate approved intent to observed execution behavior."
  "- marking reconciliation exceptions when upstream substrate records or findings disappear, duplicate workflow triggers arrive, or n8n reports an outcome that does not satisfy the approved intent record."
  "No control-plane record family may silently inherit lifecycle from substrate-local alerts or n8n execution history. Cross-system state must be linked through explicit identifiers and reconciliation records instead."
  "Retry policy belongs to the control-plane intent record, while duplicate suppression and step-level retry behavior inside a running workflow belong to n8n."
  "- the n8n execution record that shows what actually ran and what outcome was observed."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing control-plane state model document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing control-plane state model heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing control-plane state model statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${forbidden_phrases[@]}"; do
  if grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Forbidden control-plane state model statement still present: ${phrase}" >&2
    exit 1
  fi
done

echo "Control-plane state model document is present and defines ownership, reconciliation, and recovery boundaries."
