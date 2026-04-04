#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/response-action-safety-model.md"

required_headings=(
  "# AegisOps Response Action Safety and Approval Binding Model"
  "## 1. Purpose"
  "## 2. Action Safety Classes"
  "## 3. Minimum Action Request Fields"
  "## 4. Approval Binding Requirements"
  "## 5. Execution Safeguards"
  "## 6. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the baseline safety model and approval binding requirements for future AegisOps response actions."
  "This document defines policy and evidence requirements only. It does not introduce live workflows, approval-exempt write paths, or autonomous response behavior."
  '| `Read` |'
  '| `Notify` |'
  '| `Soft Write` |'
  '| `Hard Write` |'
  "Every action request must identify the requester, the intended action class, the target, the justification, and the exact payload or payload reference proposed for execution."
  '| `action_request_id` | Provides the immutable control-plane identifier for the exact request under review and execution binding. |'
  "Execution must not proceed when the action request lacks target specificity, approval requirements, expiry, or the evidence needed to bind approval context to execution context."
  "Approval decisions must remain separate from execution attempts."
  "The approval record must bind the requester identity, approver identity, target snapshot, payload hash, approval timestamp, expiry, and required quorum result to the specific action request."
  'Each approval decision must also carry an immutable `approval_decision_id` so approval outcome does not get inferred from workflow history or overwritten by later review activity.'
  "If dry-run evidence is required for the action class, the approval record must reference the reviewed dry-run result that matches the approved target snapshot and payload hash."
  "Execution must perform post-approval drift checks before acting."
  "An execution attempt must be rejected when requester identity, target snapshot, payload hash, expiry, quorum, or required dry-run evidence no longer matches the approved record."
  'At minimum, the action-request lifecycle must distinguish `draft`, `pending_approval`, `approved`, `rejected`, `expired`, `canceled`, `superseded`, `executing`, `completed`, `failed`, and `unresolved`, while the approval-decision lifecycle must distinguish `pending`, `approved`, `rejected`, `expired`, `canceled`, and `superseded`.'
  "Every execution attempt must carry an idempotency key that is unique for the approved action request and execution intent."
  "Execution records must capture the downstream result, verification evidence, and rollback or containment outcome where applicable."
  "Duplicate execution attempts for the same approved action request must be prevented unless an explicitly recorded retry policy allows another attempt under the same binding context."
  "Post-action verification must confirm the expected target state or clearly record the residual risk and operator follow-up required."
  "This model preserves the baseline separation between detection, approval, and execution and prevents approval from degrading into a generic approve button."
)

prohibited_phrases=(
  "| Request identifier | Distinguishes one requested action from later edits, retries, or related cases. |"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing response action safety model document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq "${heading}" "${doc_path}"; then
    echo "Missing response action safety model heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq "${phrase}" "${doc_path}"; then
    echo "Missing response action safety model statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${prohibited_phrases[@]}"; do
  if grep -Fq "${phrase}" "${doc_path}"; then
    echo "Ambiguous response action safety model statement: ${phrase}" >&2
    exit 1
  fi
done

echo "Response action safety model document is present and defines action classes, approval binding, and execution safeguards."
