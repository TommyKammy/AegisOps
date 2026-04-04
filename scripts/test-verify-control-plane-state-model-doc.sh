#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-control-plane-state-model-doc.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

valid_doc_content='
# AegisOps Control-Plane State and Reconciliation Model

## 1. Purpose

This document defines the approved baseline control-plane state model for AegisOps before any dedicated control service or datastore is implemented.

This document defines ownership, source-of-truth expectations, and recovery responsibilities only. It does not introduce a live datastore, schema migration, API service, or runtime deployment in this phase.

## 2. Baseline Design Constraints

The control-plane boundary must remain explicit even though the baseline does not yet deploy a dedicated control-plane service.

## 3. Baseline Ownership and Source of Truth

| Record family | Baseline owner | Ownership note |
| ---- | ---- | ---- |
| `Finding` | OpenSearch detection and analytics plane | OpenSearch remains the system of record for detection outputs and finding identifiers. |
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

Observation records must preserve scoped analyst assertions, timestamps, authorship, and linkage to supporting evidence without turning evidence custody into free-form narrative.

Lead records must preserve investigative hypotheses, triage rationale, and disposition state without being treated as equivalent to alert state, case state, or recommendation text.

Recommendation records must preserve proposed next steps, rationale, and review status without being treated as approval, execution, or immutable evidence.

Hunt records must preserve explicit lifecycle state, ownership, hypothesis linkage, and closure rationale even when no case is opened.

Hunt-run reconciliation must preserve whether a run was planned, started, completed, canceled, superseded, or left unresolved, plus which findings, observations, leads, recommendations, or cases it did or did not influence.

AI trace records must preserve generation, review, acceptance, rejection, supersession, and linkage expectations as explicit control-plane state rather than silent prompt history.

Disagreement between analytics, control-plane, and execution-plane records must remain auditable rather than silently overwritten.

## 6. Minimum Record Identifiers and Lifecycle States

The baseline must define immutable record-family identifiers and explicit lifecycle states for Alert, Case, Evidence, Approval Decision, and Action Request records before any live control-plane implementation exists.

These identifiers and states are minimum control-plane expectations. They must not be inferred from OpenSearch alert status, OpenSearch document updates, n8n execution status, or ad hoc analyst notes.

### 6.1 Alert

| Field | Minimum expectation |
| ---- | ---- |
| `alert_id` | Immutable AegisOps control-plane identifier for one alert record. |
| `finding_id` | Required upstream analytic linkage to the originating finding that justified alert creation or update. |
| `analytic_signal_id` | Required when the routed OpenSearch alerting or correlation artifact is distinct from the underlying finding. |
| `case_id` | Optional linkage that becomes required once the alert is promoted into a tracked case. |

| State | Meaning |
| ---- | ---- |
| `new` | The alert record exists and awaits analyst triage. |
| `triaged` | Initial analyst or policy review classified the alert and decided whether deeper work is required. |
| `investigating` | Investigation, evidence gathering, or coordination work is actively in progress. |
| `escalated_to_case` | The alert remains linked to an active case that now owns the broader investigation. |
| `closed` | Alert handling is complete with an explicit disposition and closure rationale. |
| `reopened` | The alert returned to active review after closure because new evidence, correlation, or review findings changed the decision. |
| `superseded` | The alert is no longer the primary work-tracking record because another alert or case absorbed responsibility through an explicit linkage. |

### 6.2 Case

| Field | Minimum expectation |
| ---- | ---- |
| `case_id` | Immutable AegisOps control-plane identifier for one investigation record. |
| `alert_id` | Required linkage to the originating alert when the case came from alert promotion. |
| `finding_id` | Required when the case is opened directly from analytic output or needs durable linkage to the driving finding set. |
| `evidence_id` | One or more explicit evidence links rather than implicit attachment through notes or workflow metadata. |

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

| Field | Minimum expectation |
| ---- | ---- |
| `evidence_id` | Immutable AegisOps control-plane identifier for one evidence record. |
| `source_record_id` | Required reference to the originating source artifact, datastore object, upload, or acquisition event. |
| `case_id` or `alert_id` | Required control-plane linkage showing which alert, case, or related work item currently relies on the evidence. |
| Provenance metadata | Required capture context such as collector identity, acquisition timestamp, source system, and derivation relationship when applicable. |

| State | Meaning |
| ---- | ---- |
| `collected` | The evidence item was acquired and recorded with initial provenance metadata. |
| `validated` | Provenance, integrity, or acquisition quality checks completed enough for analyst use. |
| `linked` | The evidence is attached to one or more control-plane records as supporting material. |
| `superseded` | A newer or more authoritative evidence record replaced this one without deleting its historical relevance. |
| `withdrawn` | The evidence remains historically visible, but it must no longer be relied on because provenance, integrity, or scope was invalidated. |

### 6.4 Approval Decision

| Field | Minimum expectation |
| ---- | ---- |
| `approval_decision_id` | Immutable AegisOps control-plane identifier for one approval decision record. |
| `action_request_id` | Required linkage to the exact action request under review. |
| Approver identity set | Required accountable identity for each approver or reviewer participating in the decision. |
| Target snapshot and payload hash | Required binding inputs that prove which reviewed context the decision authorized or rejected. |

| State | Meaning |
| ---- | ---- |
| `pending` | The approval decision is open and quorum or reviewer action is not yet complete. |
| `approved` | The required approval outcome and quorum, if any, were satisfied before expiry. |
| `rejected` | The reviewed request was explicitly denied. |
| `expired` | The approval window closed before a valid executable approval outcome remained available. |
| `canceled` | The approval decision was intentionally stopped because the underlying request was withdrawn or replaced before completion. |
| `superseded` | A newer approval decision replaced this decision for the same requested intent under revised reviewed context. |

### 6.5 Action Request

| Field | Minimum expectation |
| ---- | ---- |
| `action_request_id` | Immutable AegisOps control-plane identifier for one requested response action. |
| `approval_decision_id` | Explicit linkage to the governing approval decision once one exists. |
| `case_id`, `alert_id`, or `finding_id` | Required upstream context showing which investigative work item justified the request. |
| Idempotency key | Required stable execution correlation key that survives retries and duplicate-delivery checks. |

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

These lifecycle states establish the minimum reviewable transitions for later reconciliation, retry, expiry, duplicate suppression, and manual recovery work.

No control-plane record family may silently inherit lifecycle from OpenSearch alerts or n8n execution history. Cross-system state must be linked through explicit identifiers and reconciliation records instead.

## 7. Retry, Dead-Letter, and Manual Recovery Responsibilities

Retry policy belongs to the control-plane intent record, while duplicate suppression and step-level retry behavior inside a running workflow belong to n8n.

Dead-letter responsibility begins when the platform can no longer prove whether an approved intent was never executed, is still executing, or executed with an unknown result.

Manual recovery procedures must support re-drive, cancellation, supersession, and explicit operator annotation without rewriting historical approval or execution evidence.

## 8. Idempotency and Audit Expectations

Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays.

## 9. Baseline Alignment Notes

A future implementation may materialize these control-plane records in a dedicated service or datastore, but this baseline explicitly defers that runtime choice.
'

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/control-plane-state-model.md"
  git -C "${target}" add docs/control-plane-state-model.md
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_doc "${valid_repo}" "${valid_doc_content}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing control-plane state model document:"

missing_reconciliation_repo="${workdir}/missing-reconciliation"
create_repo "${missing_reconciliation_repo}"
write_doc "${missing_reconciliation_repo}" "${valid_doc_content/The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed./}"
commit_fixture "${missing_reconciliation_repo}"
assert_fails_with "${missing_reconciliation_repo}" "The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed."

missing_idempotency_repo="${workdir}/missing-idempotency"
create_repo "${missing_idempotency_repo}"
write_doc "${missing_idempotency_repo}" "${valid_doc_content/Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays./}"
commit_fixture "${missing_idempotency_repo}"
assert_fails_with "${missing_idempotency_repo}" "Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays."

missing_ownership_split_repo="${workdir}/missing-ownership-split"
create_repo "${missing_ownership_split_repo}"
write_doc "${missing_ownership_split_repo}" "${valid_doc_content/The approved ownership split for a future PostgreSQL-backed implementation is:/}"
commit_fixture "${missing_ownership_split_repo}"
assert_fails_with "${missing_ownership_split_repo}" "The approved ownership split for a future PostgreSQL-backed implementation is:"
