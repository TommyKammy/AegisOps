#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-53-6-wazuh-source-health-projection.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/wazuh"
  printf '%s\n' "# AegisOps" "See [Phase 53.6 Wazuh source-health projection contract](docs/deployment/wazuh-source-health-projection-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/wazuh-source-health-projection-contract.md" \
    "${target}/docs/deployment/wazuh-source-health-projection-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
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
    "${target}/docs/deployment/wazuh-source-health-projection-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/wazuh-source-health-projection-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 53.6 Wazuh source-health projection contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "${missing_artifact_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 53.6 Wazuh source-health projection artifact"

missing_component_repo="${workdir}/missing-component"
create_valid_repo "${missing_component_repo}"
perl -0pi -e 's/^  - parser\n//m' \
  "${missing_component_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_component_repo}" \
  "Missing Phase 53.6 Wazuh source-health component: parser"

missing_degraded_repo="${workdir}/missing-degraded"
create_valid_repo "${missing_degraded_repo}"
perl -0pi -e 's/^  - degraded\n//m' \
  "${missing_degraded_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_degraded_repo}" \
  "Missing Phase 53.6 Wazuh source-health state: degraded"

missing_unavailable_repo="${workdir}/missing-unavailable"
create_valid_repo "${missing_unavailable_repo}"
perl -0pi -e 's/^  - unavailable\n//m' \
  "${missing_unavailable_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_unavailable_repo}" \
  "Missing Phase 53.6 Wazuh source-health state: unavailable"

missing_stale_source_repo="${workdir}/missing-stale-source"
create_valid_repo "${missing_stale_source_repo}"
perl -0pi -e 's/^  - stale_source\n//m' \
  "${missing_stale_source_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_stale_source_repo}" \
  "Missing Phase 53.6 Wazuh source-health state: stale_source"

missing_parser_failure_repo="${workdir}/missing-parser-failure"
create_valid_repo "${missing_parser_failure_repo}"
perl -0pi -e 's/^  - parser_failure\n//m' \
  "${missing_parser_failure_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_parser_failure_repo}" \
  "Missing Phase 53.6 Wazuh source-health state: parser_failure"

missing_volume_anomaly_repo="${workdir}/missing-volume-anomaly"
create_valid_repo "${missing_volume_anomaly_repo}"
perl -0pi -e 's/^  - volume_anomaly\n//m' \
  "${missing_volume_anomaly_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_volume_anomaly_repo}" \
  "Missing Phase 53.6 Wazuh source-health state: volume_anomaly"

missing_credential_degraded_repo="${workdir}/missing-credential-degraded"
create_valid_repo "${missing_credential_degraded_repo}"
perl -0pi -e 's/^  - credential_degraded\n//m' \
  "${missing_credential_degraded_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_credential_degraded_repo}" \
  "Missing Phase 53.6 Wazuh source-health state: credential_degraded"

missing_mismatched_repo="${workdir}/missing-mismatched"
create_valid_repo "${missing_mismatched_repo}"
perl -0pi -e 's/^  - mismatched\n//m' \
  "${missing_mismatched_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_mismatched_repo}" \
  "Missing Phase 53.6 Wazuh source-health state: mismatched"

missing_rule_repo="${workdir}/missing-rule"
create_valid_repo "${missing_rule_repo}"
perl -0pi -e 's/^  - credential-degraded-redacted\n//m' \
  "${missing_rule_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${missing_rule_repo}" \
  "Missing Phase 53.6 Wazuh source-health rule: credential-degraded-redacted"

missing_contract_rule_repo="${workdir}/missing-contract-rule"
create_valid_repo "${missing_contract_rule_repo}"
perl -0pi -e 's/^\| no-authority-mutation \|.*\n//m' \
  "${missing_contract_rule_repo}/docs/deployment/wazuh-source-health-projection-contract.md"
assert_fails_with \
  "${missing_contract_rule_repo}" \
  "Missing Phase 53.6 Wazuh source-health projection contract rule row: no-authority-mutation"

secret_looking_value_repo="${workdir}/secret-looking-value"
create_valid_repo "${secret_looking_value_repo}"
printf '%s\n' "health_secret: CorrectHorseBatteryStaple42" \
  >>"${secret_looking_value_repo}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
assert_fails_with \
  "${secret_looking_value_repo}" \
  "Forbidden Phase 53.6 Wazuh source-health artifact: committed secret-looking value detected"

contract_secret_looking_value_repo="${workdir}/contract-secret-looking-value"
create_valid_repo "${contract_secret_looking_value_repo}"
printf '%s\n' "health_secret: CorrectHorseBatteryStaple42" \
  >>"${contract_secret_looking_value_repo}/docs/deployment/wazuh-source-health-projection-contract.md"
assert_fails_with \
  "${contract_secret_looking_value_repo}" \
  "Forbidden Phase 53.6 Wazuh source-health artifact: committed secret-looking value detected"

authority_truth_repo="${workdir}/authority-truth"
create_valid_repo "${authority_truth_repo}"
printf '%s\n' "Wazuh health status is AegisOps workflow truth." \
  >>"${authority_truth_repo}/docs/deployment/wazuh-source-health-projection-contract.md"
assert_fails_with \
  "${authority_truth_repo}" \
  "Forbidden Phase 53.6 Wazuh source-health projection claim: Wazuh health status is AegisOps workflow truth"

credential_leak_repo="${workdir}/credential-leak"
create_valid_repo "${credential_leak_repo}"
printf '%s\n' "Credential-degraded state may expose secret material." \
  >>"${credential_leak_repo}/docs/deployment/wazuh-source-health-projection-contract.md"
assert_fails_with \
  "${credential_leak_repo}" \
  "Forbidden Phase 53.6 Wazuh source-health projection claim: Credential-degraded state may expose secret material"

missing_forbidden_claim_repo="${workdir}/missing-forbidden-claim"
create_valid_repo "${missing_forbidden_claim_repo}"
remove_text_from_contract "${missing_forbidden_claim_repo}" \
  "Wazuh source health closes AegisOps cases."
assert_fails_with \
  "${missing_forbidden_claim_repo}" \
  "Missing Phase 53.6 Wazuh source-health forbidden claim: Wazuh source health closes AegisOps cases"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/wazuh-source-health-projection-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 53.6 Wazuh source-health projection artifact: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 53.6 Wazuh source-health projection contract."

echo "Phase 53.6 Wazuh source-health projection verifier tests passed."
