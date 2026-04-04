#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/control-plane-state-model.md"

required_headings=(
  "# AegisOps Control-Plane State and Reconciliation Model"
  "## 1. Purpose"
  "## 2. Baseline Design Constraints"
  "## 3. Baseline Ownership and Source of Truth"
  "## 4. Reconciliation Responsibilities"
  "## 5. Retry, Dead-Letter, and Manual Recovery Responsibilities"
  "## 6. Idempotency and Audit Expectations"
  "## 7. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the approved baseline control-plane state model for AegisOps before any dedicated control service or datastore is implemented."
  "This document defines ownership, source-of-truth expectations, and recovery responsibilities only. It does not introduce a live datastore, schema migration, API service, or runtime deployment in this phase."
  '| `Finding` | OpenSearch detection and analytics plane | OpenSearch remains the system of record for detection outputs and finding identifiers. |'
  '| `Alert` | Future AegisOps control-plane alert record | Alert lifecycle must not be inferred from OpenSearch alert documents or n8n execution history alone. |'
  '| `Case` | Future AegisOps control-plane case record | Case ownership, analyst status, and evidence linkage must not dissolve into workflow runs or dashboard state. |'
  '| `Evidence` | Future AegisOps control-plane evidence record | Evidence custody, provenance, and record linkage must remain explicit instead of dissolving into case notes, AI output, or workflow metadata. |'
  '| `Observation` | Future AegisOps control-plane observation record | Observations capture analyst-asserted investigative facts and must remain distinct from raw evidence artifacts, AI trace text, and case status fields. |'
  '| `Lead` | Future AegisOps control-plane lead record | Leads preserve candidate hypotheses or follow-up directions without silently promoting them into alerts, cases, or approved action intent. |'
  '| `Recommendation` | Future AegisOps control-plane recommendation record | Recommendations preserve proposed analyst or AI-advised next steps without replacing approval decisions, action requests, or execution outcomes. |'
  '| `Approval Decision` | Future AegisOps control-plane approval record | Approval is a first-class control decision and must not be reconstructed from whether a workflow happened to run. |'
  '| `Hunt` | Future AegisOps control-plane hunt record | Hunt lifecycle must remain analyst-directed and reviewable rather than inferred from ad hoc queries or downstream workflow runs. |'
  '| `Hunt Run` | Future AegisOps control-plane hunt-run record | Each hunt run must preserve bounded scope, execution context, and outcome for one hunt iteration without replacing alerts or cases. |'
  '| `AI Trace` | Future AegisOps control-plane AI-trace record | AI trace records must preserve prompt, model, review, and linkage context without mutating evidence custody or analyst-owned dispositions. |'
  '| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state | n8n owns execution-attempt state, step progress, and connector-specific runtime details. |'
  "n8n execution history must not become the implicit system of record for case state, approval state, or action-request intent."
  "OpenSearch findings and alerts remain upstream analytic signals for reconciliation input, but they do not own downstream case, approval, or execution-policy state."
  "The minimum control-plane record families for this baseline are Alert, Case, Evidence, Observation, Lead, Recommendation, Approval Decision, Action Request, Hunt, Hunt Run, AI Trace, and the execution-plane Action Execution record that must later reconcile with them."
  "The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed."
  "Reconciliation must prefer deterministic correlation keys such as finding identifiers, action-request identifiers, approval identifiers, workflow identifiers, and idempotency keys rather than fuzzy time-window matching."
  "Stable reconciliation keys must allow operators to compare OpenSearch analytics output, control-plane records, and n8n execution outcomes without assuming those systems share one lifecycle or one authoritative identifier."
  "Hunt records must preserve explicit lifecycle state, ownership, hypothesis linkage, and closure rationale even when no case is opened."
  "Observation records must preserve scoped analyst assertions, timestamps, authorship, and linkage to supporting evidence without turning evidence custody into free-form narrative."
  "Lead records must preserve investigative hypotheses, triage rationale, and disposition state without being treated as equivalent to alert state, case state, or recommendation text."
  "Recommendation records must preserve proposed next steps, rationale, and review status without being treated as approval, execution, or immutable evidence."
  "Hunt-run reconciliation must preserve whether a run was planned, started, completed, canceled, superseded, or left unresolved, plus which findings, observations, leads, recommendations, or cases it did or did not influence."
  "AI trace records must preserve generation, review, acceptance, rejection, supersession, and linkage expectations as explicit control-plane state rather than silent prompt history."
  "Disagreement between analytics, control-plane, and execution-plane records must remain auditable rather than silently overwritten."
  "Retry policy belongs to the control-plane intent record, while duplicate suppression and step-level retry behavior inside a running workflow belong to n8n."
  "Dead-letter responsibility begins when the platform can no longer prove whether an approved intent was never executed, is still executing, or executed with an unknown result."
  "Manual recovery procedures must support re-drive, cancellation, supersession, and explicit operator annotation without rewriting historical approval or execution evidence."
  "Every action request and execution attempt must carry a stable idempotency key that survives retries, duplicate delivery, and reconciliation replays."
  "A future implementation may materialize these control-plane records in a dedicated service or datastore, but this baseline explicitly defers that runtime choice."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing control-plane state model document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing control-plane state model heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing control-plane state model statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Control-plane state model document is present and defines ownership, reconciliation, and recovery boundaries."
