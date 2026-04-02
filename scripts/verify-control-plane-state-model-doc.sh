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
  '| `Approval Decision` | Future AegisOps control-plane approval record | Approval is a first-class control decision and must not be reconstructed from whether a workflow happened to run. |'
  '| `Action Execution` | n8n execution plane with PostgreSQL-backed workflow state | n8n owns execution-attempt state, step progress, and connector-specific runtime details. |'
  "n8n execution history must not become the implicit system of record for case state, approval state, or action-request intent."
  "OpenSearch findings and alerts remain upstream analytic signals for reconciliation input, but they do not own downstream case, approval, or execution-policy state."
  "The control plane is responsible for reconciling approved action intent against observed n8n execution outcomes and for recording when reconciliation is incomplete, stale, or failed."
  "Reconciliation must prefer deterministic correlation keys such as finding identifiers, action-request identifiers, approval identifiers, workflow identifiers, and idempotency keys rather than fuzzy time-window matching."
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
