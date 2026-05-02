#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-53-3-wazuh-intake-binding-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/wazuh"
  printf '%s\n' "# AegisOps" "See [Phase 53.3 Wazuh intake binding contract](docs/deployment/wazuh-manager-intake-binding-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/wazuh-manager-intake-binding-contract.md" \
    "${target}/docs/deployment/wazuh-manager-intake-binding-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
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
    "${target}/docs/deployment/wazuh-manager-intake-binding-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/wazuh-manager-intake-binding-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 53.3 Wazuh intake binding contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "${missing_artifact_repo}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 53.3 Wazuh intake binding artifact"

missing_intake_url_repo="${workdir}/missing-intake-url"
create_valid_repo "${missing_intake_url_repo}"
perl -0pi -e 's/^intake_url: .+$/intake_url: /m' \
  "${missing_intake_url_repo}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
assert_fails_with \
  "${missing_intake_url_repo}" \
  "Missing Phase 53.3 Wazuh intake binding artifact term: intake_url: /intake/wazuh"

missing_proxy_route_repo="${workdir}/missing-proxy-route"
create_valid_repo "${missing_proxy_route_repo}"
perl -0pi -e 's/^proxy_route: .+\n//m' \
  "${missing_proxy_route_repo}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
assert_fails_with \
  "${missing_proxy_route_repo}" \
  "Missing Phase 53.3 Wazuh intake binding artifact term: proxy_route"

missing_secret_repo="${workdir}/missing-secret"
create_valid_repo "${missing_secret_repo}"
perl -0pi -e 's/^shared_secret_custody: .+$/shared_secret_custody: /m' \
  "${missing_secret_repo}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
assert_fails_with \
  "${missing_secret_repo}" \
  "Missing Phase 53.3 Wazuh intake binding artifact term: shared_secret_custody"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
perl -0pi -e 's/^shared_secret_custody: .+$/shared_secret_custody: changeme/m' \
  "${placeholder_secret_repo}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Missing Phase 53.3 Wazuh intake binding artifact term: shared_secret_custody"

secret_looking_value_repo="${workdir}/secret-looking-value"
create_valid_repo "${secret_looking_value_repo}"
printf '%s\n' "wazuh_intake_secret: CorrectHorseBatteryStaple42" \
  >>"${secret_looking_value_repo}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
assert_fails_with \
  "${secret_looking_value_repo}" \
  "Forbidden Phase 53.3 Wazuh intake binding artifact: committed secret-looking value detected"

missing_provenance_repo="${workdir}/missing-provenance"
create_valid_repo "${missing_provenance_repo}"
perl -0pi -e 's/^  - wazuh_rule_id\n//m' \
  "${missing_provenance_repo}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
assert_fails_with \
  "${missing_provenance_repo}" \
  "Missing Phase 53.3 Wazuh provenance field: wazuh_rule_id"

missing_admission_statement_repo="${workdir}/missing-admission-statement"
create_valid_repo "${missing_admission_statement_repo}"
remove_text_from_contract "${missing_admission_statement_repo}" \
  "Wazuh-origin input remains a candidate analytic signal until AegisOps admits it and links it to an AegisOps record."
assert_fails_with \
  "${missing_admission_statement_repo}" \
  "Missing Phase 53.3 Wazuh intake binding contract statement"

pre_admission_truth_repo="${workdir}/pre-admission-truth"
create_valid_repo "${pre_admission_truth_repo}"
printf '%s\n' "Wazuh-origin input is AegisOps case truth before admission." \
  >>"${pre_admission_truth_repo}/docs/deployment/wazuh-manager-intake-binding-contract.md"
assert_fails_with \
  "${pre_admission_truth_repo}" \
  "Forbidden Phase 53.3 Wazuh intake binding claim: Wazuh-origin input is AegisOps case truth before admission"

forwarded_header_repo="${workdir}/forwarded-header"
create_valid_repo "${forwarded_header_repo}"
printf '%s\n' "Raw forwarded headers are trusted identity." \
  >>"${forwarded_header_repo}/docs/deployment/wazuh-manager-intake-binding-contract.md"
assert_fails_with \
  "${forwarded_header_repo}" \
  "Forbidden Phase 53.3 Wazuh intake binding claim: Raw forwarded headers are trusted identity"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/wazuh-manager-intake-binding-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 53.3 Wazuh intake binding contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 53.3 Wazuh intake binding contract."

echo "Phase 53.3 Wazuh intake binding contract verifier tests passed."
