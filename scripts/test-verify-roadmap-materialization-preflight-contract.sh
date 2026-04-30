#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-roadmap-materialization-preflight-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_valid_contract() {
  local target="$1"

  mkdir -p "${target}/docs"
  cat >"${target}/docs/roadmap-materialization-preflight-contract.md" <<'EOF'
# Roadmap Materialization Preflight Contract

Required inputs: phase_id, epic_issue_number, child_issue_numbers, Part of:, Depends on:, Parallelizable:, Execution order, issue-lint, execution_ready, missing_required, metadata_errors, phase_completion_state, phase_evaluation_state.

Required classifications: missing, materialized_open, blocked, execution_ready, merge_or_evaluation_needed, done.

Required outputs: pass, fail, phase_classification, invalid_phase_id, invalid_field, suggested_next_safe_action.

Invocation: bash scripts/roadmap-materialization-preflight.sh --graph docs/automation/roadmap-materialization-phase-graph.json --target-phase 49.0 --issue-source github
Smoke test: bash scripts/test-verify-roadmap-materialization-preflight.sh
Graph input: docs/automation/roadmap-materialization-phase-graph.json

Phase 49.0/49 must not start before Phase 48, Phase 48.5, Phase 48.6, and Phase 48.7 gates are materialized, lint-clean, and evaluated or explicitly deferred.
Phase 52+ must not be created, scheduled, or executed until the Phase 51 Epic and child issue set are materialized, lint-clean, and closed or explicitly accepted by the owner.
Phase 51 Epic #1041.
Phase 51 child issues #1042, #1043, #1044, #1045, #1046, #1047, #1048, and #1049.
Child issues need real `Part of:` issue numbers that point to the authoritative Epic.
`Depends on:` must contain true scheduler blockers only.

AegisOps control-plane records remain authoritative workflow truth.
tickets, assistant output, ML output, endpoint evidence, network evidence, browser state, receipts, and optional extension status remain subordinate context.

Examples: Complete phase, Missing Epic issue, Missing child issue, Missing Part of, Missing Depends on, Missing execution order, Placeholder or non-real dependency, Non-lint-clean issue.

Validation command: node <codex-supervisor-root>/dist/index.js issue-lint <issue-number> --config <supervisor-config-path>
EOF
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

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
write_valid_contract "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing roadmap materialization preflight contract: docs/roadmap-materialization-preflight-contract.md"

missing_field_repo="${workdir}/missing-field"
write_valid_contract "${missing_field_repo}"
perl -0pi -e 's/, metadata_errors//' \
  "${missing_field_repo}/docs/roadmap-materialization-preflight-contract.md"
assert_fails_with \
  "${missing_field_repo}" \
  "Missing required contract term in docs/roadmap-materialization-preflight-contract.md: metadata_errors"

missing_gate_repo="${workdir}/missing-gate"
write_valid_contract "${missing_gate_repo}"
perl -0pi -e 's/Phase 49\.0\/49 must not start before Phase 48, Phase 48\.5, Phase 48\.6, and Phase 48\.7 gates are materialized, lint-clean, and evaluated or explicitly deferred\.//' \
  "${missing_gate_repo}/docs/roadmap-materialization-preflight-contract.md"
assert_fails_with \
  "${missing_gate_repo}" \
  "Missing required contract term in docs/roadmap-materialization-preflight-contract.md: Phase 49.0/49 must not start before Phase 48, Phase 48.5, Phase 48.6, and Phase 48.7 gates are materialized, lint-clean, and evaluated or explicitly deferred."

missing_phase51_repo="${workdir}/missing-phase51-gate"
write_valid_contract "${missing_phase51_repo}"
perl -0pi -e 's/Phase 52\+ must not be created, scheduled, or executed until the Phase 51 Epic and child issue set are materialized, lint-clean, and closed or explicitly accepted by the owner\.//' \
  "${missing_phase51_repo}/docs/roadmap-materialization-preflight-contract.md"
assert_fails_with \
  "${missing_phase51_repo}" \
  "Missing required contract term in docs/roadmap-materialization-preflight-contract.md: Phase 52+ must not be created, scheduled, or executed until the Phase 51 Epic and child issue set are materialized, lint-clean, and closed or explicitly accepted by the owner."

echo "verify-roadmap-materialization-preflight-contract tests passed"
