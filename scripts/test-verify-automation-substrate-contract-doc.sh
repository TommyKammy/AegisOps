#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-automation-substrate-contract-doc.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

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

  printf '%s\n' "${doc_content}" >"${target}/docs/automation-substrate-contract.md"
  git -C "${target}" add docs/automation-substrate-contract.md
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
write_doc "${valid_repo}" '# AegisOps Approved Automation Delegation Contract

## 1. Purpose

This document defines the reviewed contract for delegating approved AegisOps actions into external automation substrates and controlled executor surfaces.

This document defines delegation, binding, provenance, and reconciliation requirements only. It does not introduce adapter code, isolated-executor implementation, or CI expansion in this phase.

## 2. Control-Plane Authority Boundary

AegisOps remains the authority for `Action Request`, `Approval Decision`, evidence linkage, `Action Execution` correlation, and `Reconciliation` state even when a reviewed automation substrate or executor surface performs downstream work.

Neither an automation substrate nor an executor surface may mint, overwrite, or become the system of record for approval truth, action-request truth, evidence custody, or reconciliation truth.

Delegation is allowed only after AegisOps has a bounded `Action Request` and a still-valid `Approval Decision` whose binding fields exactly match the downstream execution intent.

## 3. Approved Delegation Contract

| Field | Required delegation meaning |
| ---- | ---- |
| `delegation_id` | Immutable AegisOps delegation record identifier for one approved handoff into an automation substrate or executor surface. |
| `action_request_id` | Required AegisOps identifier for the exact request whose approved intent is being delegated. |
| `approval_decision_id` | Required AegisOps identifier for the approval outcome that authorizes the delegated intent. |
| `execution_surface_type` | Required reviewed surface class, constrained to approved automation-substrate or executor categories rather than vendor-local workflow labels. |
| `execution_surface_id` | Required identifier for the specific reviewed automation substrate or executor surface receiving the handoff. |
| `approved_payload` | Required exact payload or payload reference that downstream execution must honor. |
| `payload_hash` | Required integrity value that binds approval, delegation, execution, and reconciliation to the same reviewed payload. |
| `idempotency_key` | Required replay-safe key for the exact approved execution intent. |
| `expires_at` | Required delegation expiry inherited from or tighter than the approved execution window. |
| Provenance set | Required requester, approver, delegation issuer, issuance timestamp, and related evidence references needed to reconstruct who authorized and emitted the handoff. |

The approved payload must remain bound to one `Action Request`, one approval context, one reviewed target scope, and one reviewed execution surface at the time of delegation.

A reused approval decision must not authorize a materially different payload, target set, execution surface, or expiry window.

If target state, target identity, requested payload, or execution-surface destination drifts after approval, the old delegation contract is no longer valid for execution.

## 4. Approval-Bound Execution Identity and Reconciliation

The downstream execution intent must preserve `action_request_id`, `approval_decision_id`, `delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, and `payload_hash` so later `Action Execution` and `Reconciliation` records can prove what was authorized and what actually ran.

Execution-surface receipts, vendor run identifiers, and step logs are downstream evidence inputs. They must not replace the AegisOps-owned `Action Execution` or `Reconciliation` records.

Each later `Action Execution` record must link back to the originating `Action Request`, the governing `Approval Decision`, the emitted `delegation_id`, and the downstream `execution_run_id` observed on the reviewed surface.

Each later `Reconciliation` record must preserve whether the observed downstream execution matched the approved payload, approved target scope, reviewed execution surface, idempotency key, and expiry window.

If the downstream surface reports a run without a matching approved delegation record, AegisOps must treat that result as a reconciliation exception rather than infer approval from execution.

If the downstream surface reports the wrong payload hash, wrong target scope, wrong execution surface, or missing idempotency key, AegisOps must preserve that mismatch as explicit reconciliation state instead of normalizing it away.

If a delegation expires before the reviewed surface starts execution, the run must not be treated as newly approved by virtue of still having a vendor-local queued job.

## 5. Idempotency, Expiry, and Retry Rules

The `idempotency_key` belongs to the approved execution intent, not to a vendor-local retry counter or queue implementation detail.

Duplicate delivery, replay, retried dispatch, or duplicate substrate triggers must remain correlated to the same approved delegation context rather than being interpreted as fresh approvals.

Retries are allowed only when the retry remains inside the same approved payload binding, target scope, execution surface, and expiry window.

A new approval path is required before retry when the payload hash, target snapshot, execution surface, or expiry window changes.

If the execution surface cannot prove whether a received duplicate is the same approved intent or a changed request, AegisOps must keep the result in explicit reconciliation exception state until an operator resolves it.

## 6. Baseline Alignment Notes

This contract aligns the approved handoff model to the shipped vendor-neutral execution-surface vocabulary rather than reintroducing substrate-local approval or reconciliation authority.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing automation substrate contract document:"

missing_binding_repo="${workdir}/missing-binding"
create_repo "${missing_binding_repo}"
write_doc "${missing_binding_repo}" '# AegisOps Approved Automation Delegation Contract

## 1. Purpose

This document defines the reviewed contract for delegating approved AegisOps actions into external automation substrates and controlled executor surfaces.

This document defines delegation, binding, provenance, and reconciliation requirements only. It does not introduce adapter code, isolated-executor implementation, or CI expansion in this phase.

## 2. Control-Plane Authority Boundary

AegisOps remains the authority for `Action Request`, `Approval Decision`, evidence linkage, `Action Execution` correlation, and `Reconciliation` state even when a reviewed automation substrate or executor surface performs downstream work.

Delegation is allowed only after AegisOps has a bounded `Action Request` and a still-valid `Approval Decision` whose binding fields exactly match the downstream execution intent.

## 3. Approved Delegation Contract

| Field | Required delegation meaning |
| ---- | ---- |
| `delegation_id` | Immutable AegisOps delegation record identifier for one approved handoff into an automation substrate or executor surface. |
| `action_request_id` | Required AegisOps identifier for the exact request whose approved intent is being delegated. |
| `approval_decision_id` | Required AegisOps identifier for the approval outcome that authorizes the delegated intent. |
| `execution_surface_type` | Required reviewed surface class, constrained to approved automation-substrate or executor categories rather than vendor-local workflow labels. |
| `execution_surface_id` | Required identifier for the specific reviewed automation substrate or executor surface receiving the handoff. |
| `approved_payload` | Required exact payload or payload reference that downstream execution must honor. |
| `payload_hash` | Required integrity value that binds approval, delegation, execution, and reconciliation to the same reviewed payload. |
| `idempotency_key` | Required replay-safe key for the exact approved execution intent. |
| `expires_at` | Required delegation expiry inherited from or tighter than the approved execution window. |
| Provenance set | Required requester, approver, delegation issuer, issuance timestamp, and related evidence references needed to reconstruct who authorized and emitted the handoff. |

The approved payload must remain bound to one `Action Request`, one approval context, one reviewed target scope, and one reviewed execution surface at the time of delegation.

## 4. Approval-Bound Execution Identity and Reconciliation

The downstream execution intent must preserve `action_request_id`, `approval_decision_id`, `delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, and `payload_hash` so later `Action Execution` and `Reconciliation` records can prove what was authorized and what actually ran.

Execution-surface receipts, vendor run identifiers, and step logs are downstream evidence inputs. They must not replace the AegisOps-owned `Action Execution` or `Reconciliation` records.

Each later `Action Execution` record must link back to the originating `Action Request`, the governing `Approval Decision`, the emitted `delegation_id`, and the downstream `execution_run_id` observed on the reviewed surface.

Each later `Reconciliation` record must preserve whether the observed downstream execution matched the approved payload, approved target scope, reviewed execution surface, idempotency key, and expiry window.

## 5. Idempotency, Expiry, and Retry Rules

Retries are allowed only when the retry remains inside the same approved payload binding, target scope, execution surface, and expiry window.

A new approval path is required before retry when the payload hash, target snapshot, execution_surface, or expiry window changes.

## 6. Baseline Alignment Notes

This contract aligns the approved handoff model to the shipped vendor-neutral execution-surface vocabulary rather than reintroducing substrate-local approval or reconciliation authority.'
commit_fixture "${missing_binding_repo}"
assert_fails_with "${missing_binding_repo}" "Neither an automation substrate nor an executor surface may mint, overwrite, or become the system of record for approval truth, action-request truth, evidence custody, or reconciliation truth."

missing_reconciliation_repo="${workdir}/missing-reconciliation"
create_repo "${missing_reconciliation_repo}"
write_doc "${missing_reconciliation_repo}" '# AegisOps Approved Automation Delegation Contract

## 1. Purpose

This document defines the reviewed contract for delegating approved AegisOps actions into external automation substrates and controlled executor surfaces.

This document defines delegation, binding, provenance, and reconciliation requirements only. It does not introduce adapter code, isolated-executor implementation, or CI expansion in this phase.

## 2. Control-Plane Authority Boundary

AegisOps remains the authority for `Action Request`, `Approval Decision`, evidence linkage, `Action Execution` correlation, and `Reconciliation` state even when a reviewed automation substrate or executor surface performs downstream work.

Neither an automation substrate nor an executor surface may mint, overwrite, or become the system of record for approval truth, action-request truth, evidence custody, or reconciliation truth.

Delegation is allowed only after AegisOps has a bounded `Action Request` and a still-valid `Approval Decision` whose binding fields exactly match the downstream execution intent.

## 3. Approved Delegation Contract

| Field | Required delegation meaning |
| ---- | ---- |
| `delegation_id` | Immutable AegisOps delegation record identifier for one approved handoff into an automation substrate or executor surface. |
| `action_request_id` | Required AegisOps identifier for the exact request whose approved intent is being delegated. |
| `approval_decision_id` | Required AegisOps identifier for the approval outcome that authorizes the delegated intent. |
| `execution_surface_type` | Required reviewed surface class, constrained to approved automation-substrate or executor categories rather than vendor-local workflow labels. |
| `execution_surface_id` | Required identifier for the specific reviewed automation substrate or executor surface receiving the handoff. |
| `approved_payload` | Required exact payload or payload reference that downstream execution must honor. |
| `payload_hash` | Required integrity value that binds approval, delegation, execution, and reconciliation to the same reviewed payload. |
| `idempotency_key` | Required replay-safe key for the exact approved execution intent. |
| `expires_at` | Required delegation expiry inherited from or tighter than the approved execution window. |
| Provenance set | Required requester, approver, delegation issuer, issuance timestamp, and related evidence references needed to reconstruct who authorized and emitted the handoff. |

The approved payload must remain bound to one `Action Request`, one approval context, one reviewed target scope, and one reviewed execution surface at the time of delegation.

A reused approval decision must not authorize a materially different payload, target set, execution surface, or expiry window.

If target state, target identity, requested payload, or execution-surface destination drifts after approval, the old delegation contract is no longer valid for execution.

## 4. Approval-Bound Execution Identity and Reconciliation

Execution-surface receipts, vendor run identifiers, and step logs are downstream evidence inputs. They must not replace the AegisOps-owned `Action Execution` or `Reconciliation` records.

Each later `Action Execution` record must link back to the originating `Action Request`, the governing `Approval Decision`, the emitted `delegation_id`, and the downstream `execution_run_id` observed on the reviewed surface.

If a delegation expires before the reviewed surface starts execution, the run must not be treated as newly approved by virtue of still having a vendor-local queued job.

## 5. Idempotency, Expiry, and Retry Rules

Retries are allowed only when the retry remains inside the same approved payload binding, target scope, execution surface, and expiry window.

A new approval path is required before retry when the payload hash, target snapshot, execution surface, or expiry window changes.

## 6. Baseline Alignment Notes

This contract aligns the approved handoff model to the shipped vendor-neutral execution-surface vocabulary rather than reintroducing substrate-local approval or reconciliation authority.'
commit_fixture "${missing_reconciliation_repo}"
assert_fails_with "${missing_reconciliation_repo}" 'The downstream execution intent must preserve `action_request_id`, `approval_decision_id`, `delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, and `payload_hash` so later `Action Execution` and `Reconciliation` records can prove what was authorized and what actually ran.'

missing_drift_and_duplicate_repo="${workdir}/missing-drift-and-duplicate"
create_repo "${missing_drift_and_duplicate_repo}"
write_doc "${missing_drift_and_duplicate_repo}" '# AegisOps Approved Automation Delegation Contract

## 1. Purpose

This document defines the reviewed contract for delegating approved AegisOps actions into external automation substrates and controlled executor surfaces.

This document defines delegation, binding, provenance, and reconciliation requirements only. It does not introduce adapter code, isolated-executor implementation, or CI expansion in this phase.

## 2. Control-Plane Authority Boundary

AegisOps remains the authority for `Action Request`, `Approval Decision`, evidence linkage, `Action Execution` correlation, and `Reconciliation` state even when a reviewed automation substrate or executor surface performs downstream work.

Neither an automation substrate nor an executor surface may mint, overwrite, or become the system of record for approval truth, action-request truth, evidence custody, or reconciliation truth.

Delegation is allowed only after AegisOps has a bounded `Action Request` and a still-valid `Approval Decision` whose binding fields exactly match the downstream execution intent.

## 3. Approved Delegation Contract

| Field | Required delegation meaning |
| ---- | ---- |
| `delegation_id` | Immutable AegisOps delegation record identifier for one approved handoff into an automation substrate or executor surface. |
| `action_request_id` | Required AegisOps identifier for the exact request whose approved intent is being delegated. |
| `approval_decision_id` | Required AegisOps identifier for the approval outcome that authorizes the delegated intent. |
| `execution_surface_type` | Required reviewed surface class, constrained to approved automation-substrate or executor categories rather than vendor-local workflow labels. |
| `execution_surface_id` | Required identifier for the specific reviewed automation substrate or executor surface receiving the handoff. |
| `approved_payload` | Required exact payload or payload reference that downstream execution must honor. |
| `payload_hash` | Required integrity value that binds approval, delegation, execution, and reconciliation to the same reviewed payload. |
| `idempotency_key` | Required replay-safe key for the exact approved execution intent. |
| `expires_at` | Required delegation expiry inherited from or tighter than the approved execution window. |
| Provenance set | Required requester, approver, delegation issuer, issuance timestamp, and related evidence references needed to reconstruct who authorized and emitted the handoff. |

The approved payload must remain bound to one `Action Request`, one approval context, one reviewed target scope, and one reviewed execution surface at the time of delegation.

A reused approval decision must not authorize a materially different payload, target set, execution surface, or expiry window.

## 4. Approval-Bound Execution Identity and Reconciliation

The downstream execution intent must preserve `action_request_id`, `approval_decision_id`, `delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, and `payload_hash` so later `Action Execution` and `Reconciliation` records can prove what was authorized and what actually ran.

Execution-surface receipts, vendor run identifiers, and step logs are downstream evidence inputs. They must not replace the AegisOps-owned `Action Execution` or `Reconciliation` records.

Each later `Action Execution` record must link back to the originating `Action Request`, the governing `Approval Decision`, the emitted `delegation_id`, and the downstream `execution_run_id` observed on the reviewed surface.

Each later `Reconciliation` record must preserve whether the observed downstream execution matched the approved payload, approved target scope, reviewed execution surface, idempotency key, and expiry window.

If the downstream surface reports a run without a matching approved delegation record, AegisOps must treat that result as a reconciliation exception rather than infer approval from execution.

If a delegation expires before the reviewed surface starts execution, the run must not be treated as newly approved by virtue of still having a vendor-local queued job.

## 5. Idempotency, Expiry, and Retry Rules

Retries are allowed only when the retry remains inside the same approved payload binding, target scope, execution surface, and expiry window.

A new approval path is required before retry when the payload hash, target snapshot, execution surface, or expiry window changes.

## 6. Baseline Alignment Notes

This contract aligns the approved handoff model to the shipped vendor-neutral execution-surface vocabulary rather than reintroducing substrate-local approval or reconciliation authority.'
commit_fixture "${missing_drift_and_duplicate_repo}"
assert_fails_with "${missing_drift_and_duplicate_repo}" "If target state, target identity, requested payload, or execution-surface destination drifts after approval, the old delegation contract is no longer valid for execution."

missing_mismatch_repo="${workdir}/missing-mismatch"
create_repo "${missing_mismatch_repo}"
write_doc "${missing_mismatch_repo}" '# AegisOps Approved Automation Delegation Contract

## 1. Purpose

This document defines the reviewed contract for delegating approved AegisOps actions into external automation substrates and controlled executor surfaces.

This document defines delegation, binding, provenance, and reconciliation requirements only. It does not introduce adapter code, isolated-executor implementation, or CI expansion in this phase.

## 2. Control-Plane Authority Boundary

AegisOps remains the authority for `Action Request`, `Approval Decision`, evidence linkage, `Action Execution` correlation, and `Reconciliation` state even when a reviewed automation substrate or executor surface performs downstream work.

Neither an automation substrate nor an executor surface may mint, overwrite, or become the system of record for approval truth, action-request truth, evidence custody, or reconciliation truth.

Delegation is allowed only after AegisOps has a bounded `Action Request` and a still-valid `Approval Decision` whose binding fields exactly match the downstream execution intent.

## 3. Approved Delegation Contract

| Field | Required delegation meaning |
| ---- | ---- |
| `delegation_id` | Immutable AegisOps delegation record identifier for one approved handoff into an automation substrate or executor surface. |
| `action_request_id` | Required AegisOps identifier for the exact request whose approved intent is being delegated. |
| `approval_decision_id` | Required AegisOps identifier for the approval outcome that authorizes the delegated intent. |
| `execution_surface_type` | Required reviewed surface class, constrained to approved automation-substrate or executor categories rather than vendor-local workflow labels. |
| `execution_surface_id` | Required identifier for the specific reviewed automation substrate or executor surface receiving the handoff. |
| `approved_payload` | Required exact payload or payload reference that downstream execution must honor. |
| `payload_hash` | Required integrity value that binds approval, delegation, execution, and reconciliation to the same reviewed payload. |
| `idempotency_key` | Required replay-safe key for the exact approved execution intent. |
| `expires_at` | Required delegation expiry inherited from or tighter than the approved execution window. |
| Provenance set | Required requester, approver, delegation issuer, issuance timestamp, and related evidence references needed to reconstruct who authorized and emitted the handoff. |

The approved payload must remain bound to one `Action Request`, one approval context, one reviewed target scope, and one reviewed execution surface at the time of delegation.

A reused approval decision must not authorize a materially different payload, target set, execution surface, or expiry window.

If target state, target identity, requested payload, or execution-surface destination drifts after approval, the old delegation contract is no longer valid for execution.

## 4. Approval-Bound Execution Identity and Reconciliation

The downstream execution intent must preserve `action_request_id`, `approval_decision_id`, `delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, and `payload_hash` so later `Action Execution` and `Reconciliation` records can prove what was authorized and what actually ran.

Execution-surface receipts, vendor run identifiers, and step logs are downstream evidence inputs. They must not replace the AegisOps-owned `Action Execution` or `Reconciliation` records.

Each later `Action Execution` record must link back to the originating `Action Request`, the governing `Approval Decision`, the emitted `delegation_id`, and the downstream `execution_run_id` observed on the reviewed surface.

Each later `Reconciliation` record must preserve whether the observed downstream execution matched the approved payload, approved target scope, reviewed execution surface, idempotency key, and expiry window.

If the downstream surface reports a run without a matching approved delegation record, AegisOps must treat that result as a reconciliation exception rather than infer approval from execution.

If a delegation expires before the reviewed surface starts execution, the run must not be treated as newly approved by virtue of still having a vendor-local queued job.

## 5. Idempotency, Expiry, and Retry Rules

The `idempotency_key` belongs to the approved execution intent, not to a vendor-local retry counter or queue implementation detail.

Duplicate delivery, replay, retried dispatch, or duplicate substrate triggers must remain correlated to the same approved delegation context rather than being interpreted as fresh approvals.

Retries are allowed only when the retry remains inside the same approved payload binding, target scope, execution surface, and expiry window.

A new approval path is required before retry when the payload hash, target snapshot, execution surface, or expiry window changes.

If the execution surface cannot prove whether a received duplicate is the same approved intent or a changed request, AegisOps must keep the result in explicit reconciliation exception state until an operator resolves it.

## 6. Baseline Alignment Notes

This contract aligns the approved handoff model to the shipped vendor-neutral execution-surface vocabulary rather than reintroducing substrate-local approval or reconciliation authority.'
commit_fixture "${missing_mismatch_repo}"
assert_fails_with "${missing_mismatch_repo}" "If the downstream surface reports the wrong payload hash, wrong target scope, wrong execution surface, or missing idempotency key, AegisOps must preserve that mismatch as explicit reconciliation state instead of normalizing it away."

echo "verify-automation-substrate-contract-doc tests passed"
