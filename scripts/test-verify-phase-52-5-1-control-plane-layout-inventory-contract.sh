#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh"
contract_path="docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/adr" "${target}/control-plane"
  cp "${repo_root}/${contract_path}" "${target}/${contract_path}"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
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
    "${target}/${contract_path}"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

unclassified_repo="${workdir}/unclassified-module"
create_valid_repo "${unclassified_repo}"
printf '%s\n' "\"\"\"Fixture module intentionally missing from the layout inventory.\"\"\"" \
  >"${unclassified_repo}/control-plane/aegisops_control_plane/new_unclassified_module.py"
assert_fails_with \
  "${unclassified_repo}" \
  "Phase 52.5.1 layout inventory is missing module rows: new_unclassified_module.py"

behavior_change_repo="${workdir}/behavior-change-claim"
create_valid_repo "${behavior_change_repo}"
printf '%s\n' "This contract changes runtime behavior." \
  >>"${behavior_change_repo}/${contract_path}"
assert_fails_with \
  "${behavior_change_repo}" \
  "Forbidden Phase 52.5.1 layout contract claim: This contract changes runtime behavior."

fenced_behavior_change_repo="${workdir}/fenced-behavior-change-claim"
create_valid_repo "${fenced_behavior_change_repo}"
{
  printf '%s\n' '```'
  printf '%s\n' "This contract changes runtime behavior."
  printf '%s\n' '```'
} >>"${fenced_behavior_change_repo}/${contract_path}"
assert_fails_with \
  "${fenced_behavior_change_repo}" \
  "Forbidden Phase 52.5.1 layout contract claim: This contract changes runtime behavior."

commented_behavior_change_repo="${workdir}/commented-behavior-change-claim"
create_valid_repo "${commented_behavior_change_repo}"
printf '%s\n' "<!-- This contract changes runtime behavior. -->" \
  >>"${commented_behavior_change_repo}/${contract_path}"
assert_fails_with \
  "${commented_behavior_change_repo}" \
  "Forbidden Phase 52.5.1 layout contract claim: This contract changes runtime behavior."

wazuh_profile_repo="${workdir}/wazuh-profile-claim"
create_valid_repo "${wazuh_profile_repo}"
printf '%s\n' "This contract implements Wazuh product profiles." \
  >>"${wazuh_profile_repo}/${contract_path}"
assert_fails_with \
  "${wazuh_profile_repo}" \
  "Forbidden Phase 52.5.1 layout contract claim: This contract implements Wazuh product profiles."

shuffle_profile_repo="${workdir}/shuffle-profile-claim"
create_valid_repo "${shuffle_profile_repo}"
printf '%s\n' "This contract implements Shuffle product profiles." \
  >>"${shuffle_profile_repo}/${contract_path}"
assert_fails_with \
  "${shuffle_profile_repo}" \
  "Forbidden Phase 52.5.1 layout contract claim: This contract implements Shuffle product profiles."

legacy_import_removal_repo="${workdir}/legacy-import-removal"
create_valid_repo "${legacy_import_removal_repo}"
printf '%s\n' "Legacy imports may be removed immediately." \
  >>"${legacy_import_removal_repo}/${contract_path}"
assert_fails_with \
  "${legacy_import_removal_repo}" \
  "Forbidden Phase 52.5.1 layout contract claim: Legacy imports may be removed immediately."

missing_transition_policy_repo="${workdir}/missing-transition-policy"
create_valid_repo "${missing_transition_policy_repo}"
remove_text_from_contract "${missing_transition_policy_repo}" \
  "Removing a legacy import path requires a later transition policy that lists the affected import path, replacement import path, caller evidence, deprecation window, focused regression test, and rollback path."
assert_fails_with \
  "${missing_transition_policy_repo}" \
  "Missing Phase 52.5.1 layout contract statement: Removing a legacy import path requires a later transition policy"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/${contract_path}"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.5.1 layout contract: workstation-local absolute path detected"

echo "Phase 52.5.1 control-plane layout inventory verifier negative and valid fixtures passed."
