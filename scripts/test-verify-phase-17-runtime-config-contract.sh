#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-17-runtime-config-contract.sh"
canonical_contract_doc="${repo_root}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
canonical_validation_doc="${repo_root}/docs/phase-17-runtime-config-contract-validation.md"
canonical_phase16_scope_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
canonical_runtime_boundary_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"
canonical_network_doc="${repo_root}/docs/network-exposure-and-access-path-policy.md"
canonical_storage_doc="${repo_root}/docs/storage-layout-and-mount-policy.md"
canonical_readme="${repo_root}/README.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/scripts"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_canonical_artifacts() {
  local target="$1"

  cp "${canonical_contract_doc}" "${target}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  cp "${canonical_validation_doc}" "${target}/docs/phase-17-runtime-config-contract-validation.md"
  cp "${canonical_phase16_scope_doc}" "${target}/docs/phase-16-release-state-and-first-boot-scope.md"
  cp "${canonical_runtime_boundary_doc}" "${target}/docs/control-plane-runtime-service-boundary.md"
  cp "${canonical_network_doc}" "${target}/docs/network-exposure-and-access-path-policy.md"
  cp "${canonical_storage_doc}" "${target}/docs/storage-layout-and-mount-policy.md"
  cp "${canonical_readme}" "${target}/README.md"
  cp "${verifier}" "${target}/scripts/verify-phase-17-runtime-config-contract.sh"
  cp "${repo_root}/scripts/test-verify-phase-17-runtime-config-contract.sh" "${target}/scripts/test-verify-phase-17-runtime-config-contract.sh"
  git -C "${target}" add .
}

remove_text_from_doc() {
  local target="$1"
  local doc_path="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${doc_path}"
  git -C "${target}" add "${doc_path}"
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

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_canonical_artifacts "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_repo "${missing_contract_repo}"
write_canonical_artifacts "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
git -C "${missing_contract_repo}" add -u
commit_fixture "${missing_contract_repo}"
assert_fails_with "${missing_contract_repo}" "Missing Phase 17 runtime config contract doc:"

missing_required_key_repo="${workdir}/missing-required-key"
create_repo "${missing_required_key_repo}"
write_canonical_artifacts "${missing_required_key_repo}"
remove_text_from_doc "${missing_required_key_repo}" "${missing_required_key_repo}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md" '- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`'
commit_fixture "${missing_required_key_repo}"
assert_fails_with "${missing_required_key_repo}" '- `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`'

missing_fail_closed_repo="${workdir}/missing-fail-closed"
create_repo "${missing_fail_closed_repo}"
write_canonical_artifacts "${missing_fail_closed_repo}"
remove_text_from_doc "${missing_fail_closed_repo}" "${missing_fail_closed_repo}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md" 'If any required key is absent, empty, malformed, contradictory, or would violate the approved reverse-proxy-first exposure model, startup must fail closed.'
commit_fixture "${missing_fail_closed_repo}"
assert_fails_with "${missing_fail_closed_repo}" 'If any required key is absent, empty, malformed, contradictory, or would violate the approved reverse-proxy-first exposure model, startup must fail closed.'

missing_boot_sequence_repo="${workdir}/missing-boot-sequence"
create_repo "${missing_boot_sequence_repo}"
write_canonical_artifacts "${missing_boot_sequence_repo}"
remove_text_from_doc "${missing_boot_sequence_repo}" "${missing_boot_sequence_repo}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md" '4. apply the required forward migration bootstrap set'
commit_fixture "${missing_boot_sequence_repo}"
assert_fails_with "${missing_boot_sequence_repo}" '4. apply the required forward migration bootstrap set'

missing_validation_note_repo="${workdir}/missing-validation-note"
create_repo "${missing_validation_note_repo}"
write_canonical_artifacts "${missing_validation_note_repo}"
remove_text_from_doc "${missing_validation_note_repo}" "${missing_validation_note_repo}/docs/phase-17-runtime-config-contract-validation.md" 'Confirmed the reverse proxy remains the only approved user-facing ingress path and that repository-local boot surfaces must not publish the control-plane backend port directly to user networks or the public internet.'
commit_fixture "${missing_validation_note_repo}"
assert_fails_with "${missing_validation_note_repo}" 'Confirmed the reverse proxy remains the only approved user-facing ingress path and that repository-local boot surfaces must not publish the control-plane backend port directly to user networks or the public internet.'

missing_deviation_repo="${workdir}/missing-deviation"
create_repo "${missing_deviation_repo}"
write_canonical_artifacts "${missing_deviation_repo}"
remove_text_from_doc "${missing_deviation_repo}" "${missing_deviation_repo}/docs/phase-17-runtime-config-contract-validation.md" '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
commit_fixture "${missing_deviation_repo}"
assert_fails_with "${missing_deviation_repo}" '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'

echo "Phase 17 runtime config verifier enforces required contract and validation statements."
