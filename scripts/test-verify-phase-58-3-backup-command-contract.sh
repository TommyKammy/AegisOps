#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-58-3-backup-command-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-58-3-backup-command-contract.md" \
    "${target}/docs/phase-58-3-backup-command-contract.md"
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
    "${target}/docs/phase-58-3-backup-command-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-58-3-backup-command-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 58.3 backup command contract"

missing_boundary_repo="${workdir}/missing-boundary"
create_valid_repo "${missing_boundary_repo}"
remove_text_from_contract "${missing_boundary_repo}" \
  "The backup manifest is subordinate evidence only."
assert_fails_with \
  "${missing_boundary_repo}" \
  "Missing Phase 58.3 backup command contract statement: The backup manifest is subordinate evidence only."

missing_redaction_repo="${workdir}/missing-redaction"
create_valid_repo "${missing_redaction_repo}"
remove_text_from_contract "${missing_redaction_repo}" \
  "The manifest must not contain plaintext secrets, DSNs, private keys,"
assert_fails_with \
  "${missing_redaction_repo}" \
  "Missing Phase 58.3 backup command contract statement: The manifest must not contain plaintext secrets, DSNs, private keys,"

authority_overclaim_repo="${workdir}/authority-overclaim"
create_valid_repo "${authority_overclaim_repo}"
printf '%s\n' "Backup manifest proves restore success." \
  >>"${authority_overclaim_repo}/docs/phase-58-3-backup-command-contract.md"
assert_fails_with \
  "${authority_overclaim_repo}" \
  "Forbidden Phase 58.3 backup command contract claim: backup manifest proves restore success"

enterprise_overclaim_repo="${workdir}/enterprise-overclaim"
create_valid_repo "${enterprise_overclaim_repo}"
printf '%s\n' "Enterprise backup scheduling platform is included." \
  >>"${enterprise_overclaim_repo}/docs/phase-58-3-backup-command-contract.md"
assert_fails_with \
  "${enterprise_overclaim_repo}" \
  "Forbidden Phase 58.3 backup command contract claim: enterprise backup scheduling platform"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
macos_home_fragment="/""Users/example"
printf '%s\n' "Use ${macos_home_fragment}/aegisops-backups as the target." \
  >>"${workstation_path_repo}/docs/phase-58-3-backup-command-contract.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 58.3 backup command contract claim: workstation-local path"

echo "Phase 58.3 backup command contract verifier rejects missing custody, redaction, authority, enterprise-overclaim, and workstation-path cases."
