#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-58-5-upgrade-rollback-plan-contract.md" \
    "${target}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
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
    "${target}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

external_url_repo="${workdir}/external-url"
create_valid_repo "${external_url_repo}"
printf '%s\n' \
  "Use https://example.com/home/docs/upgrade-plan.md as reviewed external reference context." \
  >>"${external_url_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_passes "${external_url_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 58.5 upgrade rollback plan contract"

missing_required_field_repo="${workdir}/missing-required-field"
create_valid_repo "${missing_required_field_repo}"
remove_text_from_contract "${missing_required_field_repo}" \
  "| \`backup_reference\` | Reviewed Phase 58.3 backup manifest or restore rehearsal reference used before the plan is considered reviewable. | Missing, placeholder, Wazuh-only, ticket-only, or inferred backup evidence fails. |"
assert_fails_with \
  "${missing_required_field_repo}" \
  "Missing Phase 58.5 upgrade rollback plan contract statement: | \`backup_reference\` | Reviewed Phase 58.3 backup manifest or restore rehearsal reference used before the plan is considered reviewable. | Missing, placeholder, Wazuh-only, ticket-only, or inferred backup evidence fails. |"

missing_failure_state_repo="${workdir}/missing-failure-state"
create_valid_repo "${missing_failure_state_repo}"
remove_text_from_contract "${missing_failure_state_repo}" \
  "| \`missing_rollback_owner\` | Rollback owner is absent, TODO-only, sample-only, inferred from a team name, or broad operator discretion. | Reject the plan before any maintenance window is accepted. |"
assert_fails_with \
  "${missing_failure_state_repo}" \
  "Missing Phase 58.5 upgrade rollback plan contract statement: | \`missing_rollback_owner\` | Rollback owner is absent, TODO-only, sample-only, inferred from a team name, or broad operator discretion. | Reject the plan before any maintenance window is accepted. |"

missing_trigger_repo="${workdir}/missing-trigger"
create_valid_repo "${missing_trigger_repo}"
remove_text_from_contract "${missing_trigger_repo}" \
  "| \`rollback_trigger\` | Reviewed condition that requires rollback review or rejects continued upgrade progress. | Missing, placeholder, broad operator discretion, TODO, or post-facto trigger definition fails. |"
assert_fails_with \
  "${missing_trigger_repo}" \
  "Missing Phase 58.5 upgrade rollback plan contract statement: | \`rollback_trigger\` | Reviewed condition that requires rollback review or rejects continued upgrade progress. | Missing, placeholder, broad operator discretion, TODO, or post-facto trigger definition fails. |"

incompatible_version_repo="${workdir}/incompatible-version"
create_valid_repo "${incompatible_version_repo}"
remove_text_from_contract "${incompatible_version_repo}" \
  "| \`incompatible_version\` | \`version_before\` or \`version_after\` is unsupported, floating, unreviewed, beta, RC, \`latest\`, or inconsistent with the target profile. | Reject the plan before upgrade scheduling or maintenance-window acceptance. |"
assert_fails_with \
  "${incompatible_version_repo}" \
  "Missing Phase 58.5 upgrade rollback plan contract statement: | \`incompatible_version\` | \`version_before\` or \`version_after\` is unsupported, floating, unreviewed, beta, RC, \`latest\`, or inconsistent with the target profile. | Reject the plan before upgrade scheduling or maintenance-window acceptance. |"

silent_upgrade_repo="${workdir}/silent-upgrade"
create_valid_repo "${silent_upgrade_repo}"
printf '%s\n' "Silent upgrade is allowed after plan validation." \
  >>"${silent_upgrade_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_fails_with \
  "${silent_upgrade_repo}" \
  "Forbidden Phase 58.5 upgrade rollback plan contract claim: silent upgrade is allowed"

plan_as_release_truth_repo="${workdir}/plan-as-release-truth"
create_valid_repo "${plan_as_release_truth_repo}"
printf '%s\n' "Upgrade plan is release truth." \
  >>"${plan_as_release_truth_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_fails_with \
  "${plan_as_release_truth_repo}" \
  "Forbidden Phase 58.5 upgrade rollback plan contract claim: upgrade plan is release truth"

substrate_mutation_repo="${workdir}/substrate-mutation"
create_valid_repo "${substrate_mutation_repo}"
printf '%s\n' "Plan validation mutates substrate state." \
  >>"${substrate_mutation_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_fails_with \
  "${substrate_mutation_repo}" \
  "Forbidden Phase 58.5 upgrade rollback plan contract claim: plan validation mutates substrate state"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
macos_home_fragment="/""Users/example"
printf '%s\n' "Use ${macos_home_fragment}/upgrade-plan.md as the retained evidence path." \
  >>"${workstation_path_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 58.5 upgrade rollback plan contract claim: workstation-local path"

linux_workstation_path_repo="${workdir}/linux-workstation-path"
create_valid_repo "${linux_workstation_path_repo}"
linux_home_fragment="/""home/example"
printf '%s\n' "Use ${linux_home_fragment}/upgrade-plan.md as the retained evidence path." \
  >>"${linux_workstation_path_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_fails_with \
  "${linux_workstation_path_repo}" \
  "Forbidden Phase 58.5 upgrade rollback plan contract claim: workstation-local path"

windows_workstation_path_repo="${workdir}/windows-workstation-path"
create_valid_repo "${windows_workstation_path_repo}"
windows_home_fragment="D:""\\Users\\example"
printf '%s\n' "Use ${windows_home_fragment}\\upgrade-plan.md as the retained evidence path." \
  >>"${windows_workstation_path_repo}/docs/phase-58-5-upgrade-rollback-plan-contract.md"
assert_fails_with \
  "${windows_workstation_path_repo}" \
  "Forbidden Phase 58.5 upgrade rollback plan contract claim: workstation-local path"

echo "Phase 58.5 upgrade rollback plan contract verifier rejects missing contract, missing fields, unsafe claims, and workstation paths."
