#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-response-action-safety-model-doc.sh"

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

  printf '%s\n' "${doc_content}" >"${target}/docs/response-action-safety-model.md"
  git -C "${target}" add docs/response-action-safety-model.md
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
write_doc "${valid_repo}" '# AegisOps Response Action Safety and Approval Binding Model

## 1. Purpose

This document defines the baseline safety model and approval binding requirements for future AegisOps response actions.

This document defines policy and evidence requirements only. It does not introduce live workflows, approval-exempt write paths, or autonomous response behavior.

## 2. Action Safety Classes

| Class | Meaning |
| ---- | ---- |
| `Read` | Collect, inspect, or validate state without changing the target system. |
| `Notify` | Send operator-facing or stakeholder-facing communication without changing the protected target. |
| `Soft Write` | Change workflow, coordination, or reversible control state with bounded impact. |
| `Hard Write` | Change production or security-relevant target state with material operational effect. |

## 3. Minimum Action Request Fields

Every action request must identify the requester, the intended action class, the target, the justification, and the exact payload or payload reference proposed for execution.

| Field | Required binding purpose |
| ---- | ---- |
| `action_request_id` | Provides the immutable control-plane identifier for the exact request under review and execution binding. |
| Requester identity | Binds the proposed action to the accountable human or approved service principal that asked for it. |
| Target type and target identifier | Makes the affected host, account, workflow object, recipient set, or other target specific enough to review. |
| Requested payload or payload reference | Prevents approval from floating across materially different commands, parameters, or templates. |
| Payload hash | Gives execution a stable integrity check against the approved payload. |
| Approval requirement and quorum rule | Declares whether the action needs one approver, multiple approvers, or another explicit approval policy outcome. |
| Expiry timestamp | Prevents stale approval from being replayed against later conditions. |

Execution must not proceed when the action request lacks target specificity, approval requirements, expiry, or the evidence needed to bind approval context to execution context.

## 4. Approval Binding Requirements

Approval decisions must remain separate from execution attempts.

The approval record must bind the requester identity, approver identity, target snapshot, payload hash, approval timestamp, expiry, and required quorum result to the specific action request.

Each approval decision must also carry an immutable `approval_decision_id` so approval outcome does not get inferred from workflow history or overwritten by later review activity.

If dry-run evidence is required for the action class, the approval record must reference the reviewed dry-run result that matches the approved target snapshot and payload hash.

Execution must perform post-approval drift checks before acting.

An execution attempt must be rejected when requester identity, target snapshot, payload hash, expiry, quorum, or required dry-run evidence no longer matches the approved record.

At minimum, the action-request lifecycle must distinguish `draft`, `pending_approval`, `approved`, `rejected`, `expired`, `canceled`, `superseded`, `executing`, `completed`, `failed`, and `unresolved`, while the approval-decision lifecycle must distinguish `pending`, `approved`, `rejected`, `expired`, `canceled`, and `superseded`.

## 5. Execution Safeguards

Every execution attempt must carry an idempotency key that is unique for the approved action request and execution intent.

Execution records must capture the downstream result, verification evidence, and rollback or containment outcome where applicable.

Duplicate execution attempts for the same approved action request must be prevented unless an explicitly recorded retry policy allows another attempt under the same binding context.

Post-action verification must confirm the expected target state or clearly record the residual risk and operator follow-up required.

## 6. Baseline Alignment Notes

This model preserves the baseline separation between detection, approval, and execution and prevents approval from degrading into a generic approve button.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing response action safety model document:"

missing_binding_repo="${workdir}/missing-binding"
create_repo "${missing_binding_repo}"
write_doc "${missing_binding_repo}" '# AegisOps Response Action Safety and Approval Binding Model

## 1. Purpose

This document defines the baseline safety model and approval binding requirements for future AegisOps response actions.

This document defines policy and evidence requirements only. It does not introduce live workflows, approval-exempt write paths, or autonomous response behavior.

## 2. Action Safety Classes

| Class | Meaning |
| ---- | ---- |
| `Read` | Collect, inspect, or validate state without changing the target system. |
| `Notify` | Send operator-facing or stakeholder-facing communication without changing the protected target. |
| `Soft Write` | Change workflow, coordination, or reversible control state with bounded impact. |
| `Hard Write` | Change production or security-relevant target state with material operational effect. |

## 3. Minimum Action Request Fields

Every action request must identify the requester, the intended action class, the target, the justification, and the exact payload or payload reference proposed for execution.

| Field | Required binding purpose |
| ---- | ---- |
| `action_request_id` | Provides the immutable control-plane identifier for the exact request under review and execution binding. |

Execution must not proceed when the action request lacks target specificity, approval requirements, expiry, or the evidence needed to bind approval context to execution context.

## 4. Approval Binding Requirements

Approval decisions must remain separate from execution attempts.

Execution must perform post-approval drift checks before acting.

At minimum, the action-request lifecycle must distinguish `draft`, `pending_approval`, `approved`, `rejected`, `expired`, `canceled`, `superseded`, `executing`, `completed`, `failed`, and `unresolved`, while the approval-decision lifecycle must distinguish `pending`, `approved`, `rejected`, `expired`, `canceled`, and `superseded`.

## 5. Execution Safeguards

Every execution attempt must carry an idempotency key that is unique for the approved action request and execution intent.

Execution records must capture the downstream result, verification evidence, and rollback or containment outcome where applicable.

Duplicate execution attempts for the same approved action request must be prevented unless an explicitly recorded retry policy allows another attempt under the same binding context.

Post-action verification must confirm the expected target state or clearly record the residual risk and operator follow-up required.

## 6. Baseline Alignment Notes

This model preserves the baseline separation between detection, approval, and execution and prevents approval from degrading into a generic approve button.'
commit_fixture "${missing_binding_repo}"
assert_fails_with "${missing_binding_repo}" "The approval record must bind the requester identity, approver identity, target snapshot, payload hash, approval timestamp, expiry, and required quorum result to the specific action request."

missing_execution_guard_repo="${workdir}/missing-execution-guard"
create_repo "${missing_execution_guard_repo}"
write_doc "${missing_execution_guard_repo}" '# AegisOps Response Action Safety and Approval Binding Model

## 1. Purpose

This document defines the baseline safety model and approval binding requirements for future AegisOps response actions.

This document defines policy and evidence requirements only. It does not introduce live workflows, approval-exempt write paths, or autonomous response behavior.

## 2. Action Safety Classes

| Class | Meaning |
| ---- | ---- |
| `Read` | Collect, inspect, or validate state without changing the target system. |
| `Notify` | Send operator-facing or stakeholder-facing communication without changing the protected target. |
| `Soft Write` | Change workflow, coordination, or reversible control state with bounded impact. |
| `Hard Write` | Change production or security-relevant target state with material operational effect. |

## 3. Minimum Action Request Fields

Every action request must identify the requester, the intended action class, the target, the justification, and the exact payload or payload reference proposed for execution.

| Field | Required binding purpose |
| ---- | ---- |
| `action_request_id` | Provides the immutable control-plane identifier for the exact request under review and execution binding. |

Execution must not proceed when the action request lacks target specificity, approval requirements, expiry, or the evidence needed to bind approval context to execution context.

## 4. Approval Binding Requirements

Approval decisions must remain separate from execution attempts.

The approval record must bind the requester identity, approver identity, target snapshot, payload hash, approval timestamp, expiry, and required quorum result to the specific action request.

Each approval decision must also carry an immutable `approval_decision_id` so approval outcome does not get inferred from workflow history or overwritten by later review activity.

If dry-run evidence is required for the action class, the approval record must reference the reviewed dry-run result that matches the approved target snapshot and payload hash.

Execution must perform post-approval drift checks before acting.

An execution attempt must be rejected when requester identity, target snapshot, payload hash, expiry, quorum, or required dry-run evidence no longer matches the approved record.

At minimum, the action-request lifecycle must distinguish `draft`, `pending_approval`, `approved`, `rejected`, `expired`, `canceled`, `superseded`, `executing`, `completed`, `failed`, and `unresolved`, while the approval-decision lifecycle must distinguish `pending`, `approved`, `rejected`, `expired`, `canceled`, and `superseded`.

## 5. Execution Safeguards

Execution records must capture the downstream result, verification evidence, and rollback or containment outcome where applicable.

Duplicate execution attempts for the same approved action request must be prevented unless an explicitly recorded retry policy allows another attempt under the same binding context.

Post-action verification must confirm the expected target state or clearly record the residual risk and operator follow-up required.

## 6. Baseline Alignment Notes

This model preserves the baseline separation between detection, approval, and execution and prevents approval from degrading into a generic approve button.'
commit_fixture "${missing_execution_guard_repo}"
assert_fails_with "${missing_execution_guard_repo}" "Every execution attempt must carry an idempotency key that is unique for the approved action request and execution intent."

echo "Response action safety model verifier enforces required policy statements."
