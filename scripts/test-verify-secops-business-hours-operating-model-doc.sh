#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-secops-business-hours-operating-model-doc.sh"

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

  printf '%s\n' "${doc_content}" >"${target}/docs/secops-business-hours-operating-model.md"
  git -C "${target}" add docs/secops-business-hours-operating-model.md
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
write_doc "${valid_repo}" '# AegisOps Business-Hours SecOps Daily Operating Model

## 1. Purpose

This document defines the business-hours SecOps daily operating model for the AegisOps baseline.

## 2. Operating Assumptions

This model assumes business-hours analyst coverage rather than 24x7 staffed monitoring.

Finding or alert intake enters the analyst review queue for the next business-hours review cycle unless an explicitly defined escalation path applies.

## 3. Daily Analyst Workflow

The analyst begins by validating whether the incoming finding or alert is in scope, duplicated, or obviously explained by known benign context.

A case is created when the work requires durable ownership, evidence capture, approval tracking, cross-shift visibility, or coordinated follow-up beyond the alert record itself.

The analyst records the recommended action, target scope, justification, and required approver before any approval-bound response is requested.

## 4. Approval, Timeout, and Manual Fallback Expectations

Approval timeout must leave the action request in a non-executed state and force explicit analyst re-review during business hours before any later execution attempt.

Manual fallback may be used when the approved workflow path is unavailable, but the same approval decision, execution record, and post-action evidence requirements still apply.

## 5. After-Hours and Handoff Model

After hours, AegisOps does not imply an always-on analyst at the console.

After-hours handling must distinguish between work that can wait for the next business-hours review window and work that requires explicit escalation to an on-call or separately designated human owner.

Business-hours handoff must preserve queue state, open cases, pending approvals, expired approvals, and follow-up tasks so the next analyst can continue without reconstructing context from raw system logs.

## 6. Required Records and Decision Points

| Record | Expectation |
| ---- | ---- |
| `Alert or Finding Record` | Intake and triage state stay reviewable. |
| `Case Record` | Durable investigation ownership is explicit. |
| `Approval Decision Record` | Authorization outcome is attributable. |
| `Action Execution Record` | Execution attempt state is separate from approval. |
| `Closure or Disposition Record` | Closure rationale remains reviewable. |

## 7. Baseline Alignment Notes

No part of this operating model creates a 24x7 staffing promise, an automatic destructive-action path, or a dependency on unsupported live-response coverage.'
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing business-hours operating model document:"

missing_phrase_repo="${workdir}/missing-phrase"
create_repo "${missing_phrase_repo}"
write_doc "${missing_phrase_repo}" '# AegisOps Business-Hours SecOps Daily Operating Model

## 1. Purpose

This document defines the business-hours SecOps daily operating model for the AegisOps baseline.

## 2. Operating Assumptions

This model assumes business-hours analyst coverage rather than 24x7 staffed monitoring.

Finding or alert intake enters the analyst review queue for the next business-hours review cycle unless an explicitly defined escalation path applies.

## 3. Daily Analyst Workflow

The analyst begins by validating whether the incoming finding or alert is in scope, duplicated, or obviously explained by known benign context.

A case is created when the work requires durable ownership, evidence capture, approval tracking, cross-shift visibility, or coordinated follow-up beyond the alert record itself.

## 4. Approval, Timeout, and Manual Fallback Expectations

Approval timeout must leave the action request in a non-executed state and force explicit analyst re-review during business hours before any later execution attempt.

Manual fallback may be used when the approved workflow path is unavailable, but the same approval decision, execution record, and post-action evidence requirements still apply.

## 5. After-Hours and Handoff Model

After hours, AegisOps does not imply an always-on analyst at the console.

After-hours handling must distinguish between work that can wait for the next business-hours review window and work that requires explicit escalation to an on-call or separately designated human owner.

Business-hours handoff must preserve queue state, open cases, pending approvals, expired approvals, and follow-up tasks so the next analyst can continue without reconstructing context from raw system logs.

## 6. Required Records and Decision Points

| Record | Expectation |
| ---- | ---- |
| `Alert or Finding Record` | Intake and triage state stay reviewable. |
| `Case Record` | Durable investigation ownership is explicit. |
| `Approval Decision Record` | Authorization outcome is attributable. |
| `Action Execution Record` | Execution attempt state is separate from approval. |
| `Closure or Disposition Record` | Closure rationale remains reviewable. |

## 7. Baseline Alignment Notes

No part of this operating model creates a 24x7 staffing promise, an automatic destructive-action path, or a dependency on unsupported live-response coverage.'
commit_fixture "${missing_phrase_repo}"
assert_fails_with "${missing_phrase_repo}" "Missing business-hours operating model statement: The analyst records the recommended action, target scope, justification, and required approver before any approval-bound response is requested."

echo "Business-hours SecOps operating model verifier tests passed."
