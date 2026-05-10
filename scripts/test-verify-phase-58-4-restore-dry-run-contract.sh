#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-58-4-restore-dry-run-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-58-4-restore-dry-run-contract.md" \
    "${target}/docs/phase-58-4-restore-dry-run-contract.md"
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

remove_text_from_contract() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-58-4-restore-dry-run-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-58-4-restore-dry-run-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 58.4 restore dry-run contract"

missing_boundary_repo="${workdir}/missing-boundary"
create_valid_repo "${missing_boundary_repo}"
remove_text_from_contract "${missing_boundary_repo}" \
  "Restore dry-run output is preflight evidence only."
assert_fails_with \
  "${missing_boundary_repo}" \
  "Missing Phase 58.4 restore dry-run contract statement: Restore dry-run output is preflight evidence only."

missing_failure_state_repo="${workdir}/missing-failure-state"
create_valid_repo "${missing_failure_state_repo}"
remove_text_from_contract "${missing_failure_state_repo}" \
  "| \`stale\` | \`--max-age-hours\` is set and \`created_at\` is older than the requested policy. | Fail closed before any durable write. |"
assert_fails_with \
  "${missing_failure_state_repo}" \
  "Missing Phase 58.4 restore dry-run contract statement: | \`stale\` | \`--max-age-hours\` is set and \`created_at\` is older than the requested policy. | Fail closed before any durable write. |"

authority_overclaim_repo="${workdir}/authority-overclaim"
create_valid_repo "${authority_overclaim_repo}"
printf '%s\n' "Dry-run proves live restore completion." \
  >>"${authority_overclaim_repo}/docs/phase-58-4-restore-dry-run-contract.md"
assert_fails_with \
  "${authority_overclaim_repo}" \
  "Forbidden Phase 58.4 restore dry-run contract claim: dry-run proves live restore completion"

release_gate_overclaim_repo="${workdir}/release-gate-overclaim"
create_valid_repo "${release_gate_overclaim_repo}"
printf '%s\n' "Restore dry-run satisfies release gates." \
  >>"${release_gate_overclaim_repo}/docs/phase-58-4-restore-dry-run-contract.md"
assert_fails_with \
  "${release_gate_overclaim_repo}" \
  "Forbidden Phase 58.4 restore dry-run contract claim: restore dry-run satisfies release gates"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
macos_home_fragment="/""Users/example"
printf '%s\n' "Use ${macos_home_fragment}/aegisops-restore-dry-run.json as the retained evidence path." \
  >>"${workstation_path_repo}/docs/phase-58-4-restore-dry-run-contract.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 58.4 restore dry-run contract claim: workstation-local path"

echo "Phase 58.4 restore dry-run contract verifier rejects missing contract, missing boundary, missing failure states, overclaims, and workstation paths."
