#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-53-5-wazuh-agent-enrollment-helper-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/wazuh"
  printf '%s\n' "# AegisOps" "See [Phase 53.5 Wazuh agent enrollment helper contract](docs/deployment/wazuh-agent-enrollment-helper-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/wazuh-agent-enrollment-helper-contract.md" \
    "${target}/docs/deployment/wazuh-agent-enrollment-helper-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
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
    "${target}/docs/deployment/wazuh-agent-enrollment-helper-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/wazuh-agent-enrollment-helper-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 53.5 Wazuh agent enrollment helper contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "${missing_artifact_repo}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 53.5 Wazuh agent enrollment helper artifact"

missing_prerequisite_repo="${workdir}/missing-prerequisite"
create_valid_repo "${missing_prerequisite_repo}"
perl -0pi -e 's/^  - reviewed-agent-enrollment-secret-custody\n//m' \
  "${missing_prerequisite_repo}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
assert_fails_with \
  "${missing_prerequisite_repo}" \
  "Missing Phase 53.5 Wazuh enrollment prerequisite: reviewed-agent-enrollment-secret-custody"

missing_step_repo="${workdir}/missing-step"
create_valid_repo "${missing_step_repo}"
perl -0pi -e 's/^  - enroll-agent-to-reviewed-manager\n//m' \
  "${missing_step_repo}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
assert_fails_with \
  "${missing_step_repo}" \
  "Missing Phase 53.5 Wazuh enrollment step: enroll-agent-to-reviewed-manager"

missing_rollback_repo="${workdir}/missing-rollback"
create_valid_repo "${missing_rollback_repo}"
perl -0pi -e 's/^  - revoke-or-rotate-enrollment-secret-if-used\n//m' \
  "${missing_rollback_repo}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
assert_fails_with \
  "${missing_rollback_repo}" \
  "Missing Phase 53.5 Wazuh enrollment rollback step: revoke-or-rotate-enrollment-secret-if-used"

missing_warning_repo="${workdir}/missing-warning"
create_valid_repo "${missing_warning_repo}"
perl -0pi -e 's/^  - do-not-enroll-fleet\n//m' \
  "${missing_warning_repo}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
assert_fails_with \
  "${missing_warning_repo}" \
  "Missing Phase 53.5 Wazuh enrollment safety warning: do-not-enroll-fleet"

missing_secret_custody_repo="${workdir}/missing-secret-custody"
create_valid_repo "${missing_secret_custody_repo}"
perl -0pi -e 's/^enrollment_secret_custody: .+$/enrollment_secret_custody: /m' \
  "${missing_secret_custody_repo}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
assert_fails_with \
  "${missing_secret_custody_repo}" \
  "Missing Phase 53.5 Wazuh agent enrollment helper artifact term: enrollment_secret_custody"

secret_looking_value_repo="${workdir}/secret-looking-value"
create_valid_repo "${secret_looking_value_repo}"
printf '%s\n' "agent_enrollment_secret: CorrectHorseBatteryStaple42" \
  >>"${secret_looking_value_repo}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
assert_fails_with \
  "${secret_looking_value_repo}" \
  "Forbidden Phase 53.5 Wazuh enrollment artifact: committed secret-looking value detected"

missing_safety_statement_repo="${workdir}/missing-safety-statement"
create_valid_repo "${missing_safety_statement_repo}"
remove_text_from_contract "${missing_safety_statement_repo}" \
  "The helper must not require committed secrets, inline credentials, customer-specific values, or workstation-local absolute paths."
assert_fails_with \
  "${missing_safety_statement_repo}" \
  "Missing Phase 53.5 Wazuh agent enrollment helper contract statement"

missing_fleet_statement_repo="${workdir}/missing-fleet-statement"
create_valid_repo "${missing_fleet_statement_repo}"
remove_text_from_contract "${missing_fleet_statement_repo}" \
  "Fleet-scale Wazuh agent management remains out of scope."
assert_fails_with \
  "${missing_fleet_statement_repo}" \
  "Missing Phase 53.5 Wazuh agent enrollment helper contract statement"

missing_forbidden_claim_repo="${workdir}/missing-forbidden-claim"
create_valid_repo "${missing_forbidden_claim_repo}"
remove_text_from_contract "${missing_forbidden_claim_repo}" \
  "Phase 53.5 implements fleet-scale Wazuh agent management."
assert_fails_with \
  "${missing_forbidden_claim_repo}" \
  "Missing Phase 53.5 Wazuh forbidden claim: Phase 53.5 implements fleet-scale Wazuh agent management"

agent_truth_repo="${workdir}/agent-truth"
create_valid_repo "${agent_truth_repo}"
printf '%s\n' "Wazuh agent enrollment is AegisOps workflow truth." \
  >>"${agent_truth_repo}/docs/deployment/wazuh-agent-enrollment-helper-contract.md"
assert_fails_with \
  "${agent_truth_repo}" \
  "Forbidden Phase 53.5 Wazuh enrollment helper claim: Wazuh agent enrollment is AegisOps workflow truth"

active_response_repo="${workdir}/active-response"
create_valid_repo "${active_response_repo}"
printf '%s\n' "Wazuh Active Response is an AegisOps authority path." \
  >>"${active_response_repo}/docs/deployment/wazuh-agent-enrollment-helper-contract.md"
assert_fails_with \
  "${active_response_repo}" \
  "Forbidden Phase 53.5 Wazuh enrollment helper claim: Wazuh Active Response is an AegisOps authority path"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/wazuh-agent-enrollment-helper-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 53.5 Wazuh enrollment helper contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 53.5 Wazuh agent enrollment helper contract."

echo "Phase 53.5 Wazuh agent enrollment helper contract verifier tests passed."
