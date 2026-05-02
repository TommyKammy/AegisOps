#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-53-2-wazuh-cert-credential-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/wazuh"
  printf '%s\n' "# AegisOps" "See [Phase 53.2 Wazuh certificate and credential contract](docs/deployment/wazuh-certificate-credential-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/wazuh-certificate-credential-contract.md" \
    "${target}/docs/deployment/wazuh-certificate-credential-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml"
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
    "${target}/docs/deployment/wazuh-certificate-credential-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/wazuh-certificate-credential-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 53.2 Wazuh certificate and credential contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "${missing_artifact_repo}/docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 53.2 Wazuh certificate and credential artifact"

missing_wrapper_repo="${workdir}/missing-wrapper"
create_valid_repo "${missing_wrapper_repo}"
remove_text_from_contract "${missing_wrapper_repo}" \
  "The Wazuh certificate generation wrapper may generate demo or local rehearsal material only when demo mode is explicit."
assert_fails_with \
  "${missing_wrapper_repo}" \
  "Missing Phase 53.2 Wazuh certificate and credential contract statement"

missing_cert_paths_repo="${workdir}/missing-cert-paths"
create_valid_repo "${missing_cert_paths_repo}"
perl -0pi -e 's/\ncertificate_paths:\n(?:  - .+\n)+/\n/' \
  "${missing_cert_paths_repo}/docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml"
assert_fails_with \
  "${missing_cert_paths_repo}" \
  "Missing Phase 53.2 Wazuh certificate path expectation"

default_credentials_repo="${workdir}/default-credentials"
create_valid_repo "${default_credentials_repo}"
printf '%s\n' "default_credentials: admin:admin" \
  >>"${default_credentials_repo}/docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml"
assert_fails_with \
  "${default_credentials_repo}" \
  "Forbidden Phase 53.2 Wazuh credential value: default Wazuh credential detected"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "placeholder_secret: changeme" \
  >>"${placeholder_secret_repo}/docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 53.2 Wazuh credential value: placeholder secret detected"

secret_looking_value_repo="${workdir}/secret-looking-value"
create_valid_repo "${secret_looking_value_repo}"
printf '%s\n' "wazuh_api_password: CorrectHorseBatteryStaple42" \
  >>"${secret_looking_value_repo}/docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml"
assert_fails_with \
  "${secret_looking_value_repo}" \
  "Forbidden Phase 53.2 Wazuh credential value: committed secret-looking value detected"

private_key_repo="${workdir}/private-key"
create_valid_repo "${private_key_repo}"
printf '%s\n' "-----BEGIN PRIVATE KEY-----" \
  >>"${private_key_repo}/docs/deployment/wazuh-certificate-credential-contract.md"
assert_fails_with \
  "${private_key_repo}" \
  "Forbidden Phase 53.2 Wazuh credential value: committed private key material detected"

missing_rotation_repo="${workdir}/missing-rotation"
create_valid_repo "${missing_rotation_repo}"
remove_text_from_contract "${missing_rotation_repo}" \
  "Rotation must replace Wazuh API, indexer admin, dashboard, and ingest shared-secret custody references without committing the old or new secret value."
assert_fails_with \
  "${missing_rotation_repo}" \
  "Missing Phase 53.2 Wazuh certificate and credential contract statement"

authority_truth_repo="${workdir}/authority-truth"
create_valid_repo "${authority_truth_repo}"
printf '%s\n' "Wazuh credential state is AegisOps production truth." \
  >>"${authority_truth_repo}/docs/deployment/wazuh-certificate-credential-contract.md"
assert_fails_with \
  "${authority_truth_repo}" \
  "Forbidden Phase 53.2 Wazuh certificate and credential claim: Wazuh credential state is AegisOps production truth"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/wazuh-certificate-credential-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 53.2 Wazuh certificate and credential contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 53.2 Wazuh certificate and credential contract."

echo "Phase 53.2 Wazuh certificate and credential contract verifier tests passed."
