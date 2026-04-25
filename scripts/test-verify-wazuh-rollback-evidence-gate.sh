#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-wazuh-rollback-evidence-gate.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
}

write_doc() {
  local target="$1"
  local doc_content="$2"

  printf '%s\n' "${doc_content}" >"${target}/docs/wazuh-rule-lifecycle-runbook.md"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected rollback evidence verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected rollback evidence verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_doc "${valid_repo}" '# Wazuh Rule Lifecycle and Validation Runbook

Activation evidence must identify the candidate rule, reviewed fixture set, staging validation result, reviewer, activation window, expected alert volume, and release-gate evidence record.
Disable evidence must identify the disabled rule or candidate, disable owner, disable reason, affected fixture or parser evidence, operator notification path, and follow-up review.
Rollback evidence must identify the last reviewed rule revision, restored fixture set, rollback owner, rollback reason, validation rerun result, and AegisOps release-gate evidence record.
Detector evidence handoff must land in AegisOps-owned records and the retained release-gate evidence package before activation is treated as complete.
the release-gate evidence record that binds activation, disable, and rollback evidence to the current repository revision.
The gate must fail closed when provenance, scope, reviewer, owner, fixture, validation, false-positive, disable, rollback, or release-gate evidence is missing, malformed, placeholder, or inferred.
Operators must not infer activation success, disable completion, rollback completion, case closure, approval state, or reconciliation outcome from Wazuh rule state, alert count, source names, manager labels, or detector status alone.'
assert_passes "${valid_repo}"

missing_rollback_repo="${workdir}/missing-rollback"
create_repo "${missing_rollback_repo}"
write_doc "${missing_rollback_repo}" '# Wazuh Rule Lifecycle and Validation Runbook

Activation evidence must identify the candidate rule, reviewed fixture set, staging validation result, reviewer, activation window, expected alert volume, and release-gate evidence record.
Disable evidence must identify the disabled rule or candidate, disable owner, disable reason, affected fixture or parser evidence, operator notification path, and follow-up review.
Detector evidence handoff must land in AegisOps-owned records and the retained release-gate evidence package before activation is treated as complete.
the release-gate evidence record that binds activation, disable, and rollback evidence to the current repository revision.
The gate must fail closed when provenance, scope, reviewer, owner, fixture, validation, false-positive, disable, rollback, or release-gate evidence is missing, malformed, placeholder, or inferred.
Operators must not infer activation success, disable completion, rollback completion, case closure, approval state, or reconciliation outcome from Wazuh rule state, alert count, source names, manager labels, or detector status alone.'
assert_fails_with "${missing_rollback_repo}" "Missing Wazuh rollback evidence gate text"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Wazuh rule lifecycle runbook:"

echo "verify-wazuh-rollback-evidence-gate tests passed"
