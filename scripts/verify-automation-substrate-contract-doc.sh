#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/automation-substrate-contract.md"

required_headings=(
  "# AegisOps Approved Automation Delegation Contract"
  "## 1. Purpose"
  "## 2. Control-Plane Authority Boundary"
  "## 3. Approved Delegation Contract"
  "## 4. Approval-Bound Execution Identity and Reconciliation"
  "## 5. Idempotency, Expiry, and Retry Rules"
  "## 6. Baseline Alignment Notes"
)

required_phrases=(
  "This document defines the reviewed contract for delegating approved AegisOps actions into external automation substrates and controlled executor surfaces."
  "This document defines delegation, binding, provenance, and reconciliation requirements only. It does not introduce adapter code, isolated-executor implementation, or CI expansion in this phase."
  'AegisOps remains the authority for `Action Request`, `Approval Decision`, evidence linkage, `Action Execution` correlation, and `Reconciliation` state even when a reviewed automation substrate or executor surface performs downstream work.'
  "Neither an automation substrate nor an executor surface may mint, overwrite, or become the system of record for approval truth, action-request truth, evidence custody, or reconciliation truth."
  'Delegation is allowed only after AegisOps has a bounded `Action Request` and a still-valid `Approval Decision` whose binding fields exactly match the downstream execution intent.'
  '| `delegation_id` | Immutable AegisOps delegation record identifier for one approved handoff into an automation substrate or executor surface. |'
  '| `action_request_id` | Required AegisOps identifier for the exact request whose approved intent is being delegated. |'
  '| `approval_decision_id` | Required AegisOps identifier for the approval outcome that authorizes the delegated intent. |'
  '| `execution_surface_type` | Required reviewed surface class, constrained to approved automation-substrate or executor categories rather than vendor-local workflow labels. |'
  '| `execution_surface_id` | Required identifier for the specific reviewed automation substrate or executor surface receiving the handoff. |'
  '| `approved_payload` | Required exact payload or payload reference that downstream execution must honor. |'
  '| `payload_hash` | Required integrity value that binds approval, delegation, execution, and reconciliation to the same reviewed payload. |'
  '| `idempotency_key` | Required replay-safe key for the exact approved execution intent. |'
  '| `expires_at` | Required delegation expiry inherited from or tighter than the approved execution window. |'
  '| Provenance set | Required requester, approver, delegation issuer, issuance timestamp, and related evidence references needed to reconstruct who authorized and emitted the handoff. |'
  'The approved payload must remain bound to one `Action Request`, one approval context, one reviewed target scope, and one reviewed execution surface at the time of delegation.'
  "A reused approval decision must not authorize a materially different payload, target set, execution surface, or expiry window."
  'The downstream execution intent must preserve `action_request_id`, `approval_decision_id`, `delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, and `payload_hash` so later `Action Execution` and `Reconciliation` records can prove what was authorized and what actually ran.'
  'Execution-surface receipts, vendor run identifiers, and step logs are downstream evidence inputs. They must not replace the AegisOps-owned `Action Execution` or `Reconciliation` records.'
  'Each later `Action Execution` record must link back to the originating `Action Request`, the governing `Approval Decision`, the emitted `delegation_id`, and the downstream `execution_run_id` observed on the reviewed surface.'
  'Each later `Reconciliation` record must preserve whether the observed downstream execution matched the approved payload, approved target scope, reviewed execution surface, idempotency key, and expiry window.'
  "If the downstream surface reports a run without a matching approved delegation record, AegisOps must treat that result as a reconciliation exception rather than infer approval from execution."
  "If a delegation expires before the reviewed surface starts execution, the run must not be treated as newly approved by virtue of still having a vendor-local queued job."
  "Retries are allowed only when the retry remains inside the same approved payload binding, target scope, execution surface, and expiry window."
  "A new approval path is required before retry when the payload hash, target snapshot, execution surface, or expiry window changes."
  "This contract aligns the approved handoff model to the shipped vendor-neutral execution-surface vocabulary rather than reintroducing substrate-local approval or reconciliation authority."
)

forbidden_phrases=(
  "The automation substrate becomes the authority for approval state once execution starts."
  "Vendor workflow history is the system of record for whether an action was approved."
  "Reconciliation may be inferred from substrate-local success state without a dedicated AegisOps record."
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing automation substrate contract document: ${doc_path}" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fq -- "${heading}" "${doc_path}"; then
    echo "Missing automation substrate contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing automation substrate contract statement: ${phrase}" >&2
    exit 1
  fi
done

for phrase in "${forbidden_phrases[@]}"; do
  if grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Forbidden automation substrate contract statement still present: ${phrase}" >&2
    exit 1
  fi
done

echo "Automation substrate contract document is present and defines approved delegation, approval binding, and reconciliation expectations."
