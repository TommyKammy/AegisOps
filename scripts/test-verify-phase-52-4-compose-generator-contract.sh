#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-4-compose-generator-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/fixtures/compose-generator"
  printf '%s\n' "# AegisOps" "See [Phase 52.4 compose generator contract](docs/deployment/compose-generator-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/compose-generator-contract.md" \
    "${target}/docs/deployment/compose-generator-contract.md"
  cp "${repo_root}/docs/deployment/fixtures/compose-generator/smb-single-node.compose.snapshot.yml" \
    "${target}/docs/deployment/fixtures/compose-generator/smb-single-node.compose.snapshot.yml"
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
    "${target}/docs/deployment/compose-generator-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/compose-generator-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 52.4 compose generator contract"

missing_snapshot_repo="${workdir}/missing-snapshot"
create_valid_repo "${missing_snapshot_repo}"
rm "${missing_snapshot_repo}/docs/deployment/fixtures/compose-generator/smb-single-node.compose.snapshot.yml"
assert_fails_with \
  "${missing_snapshot_repo}" \
  "Missing Phase 52.4 generated compose snapshot fixture"

missing_proxy_repo="${workdir}/missing-proxy"
create_valid_repo "${missing_proxy_repo}"
perl -0pi -e 's/\n  proxy:\n    image: nginx:1\.27\.0.*?(?=\n  wazuh:)/\n/s' \
  "${missing_proxy_repo}/docs/deployment/fixtures/compose-generator/smb-single-node.compose.snapshot.yml"
assert_fails_with \
  "${missing_proxy_repo}" \
  "Missing generated compose snapshot service: proxy"

direct_backend_repo="${workdir}/direct-backend"
create_valid_repo "${direct_backend_repo}"
perl -0pi -e 's/    expose:\n      - "8080"/    ports:\n      - "8080:8080"/' \
  "${direct_backend_repo}/docs/deployment/fixtures/compose-generator/smb-single-node.compose.snapshot.yml"
assert_fails_with \
  "${direct_backend_repo}" \
  "Generated compose snapshot must not publish host ports for service: aegisops"

missing_wazuh_row_repo="${workdir}/missing-wazuh-row"
create_valid_repo "${missing_wazuh_row_repo}"
remove_text_from_contract "${missing_wazuh_row_repo}" \
  "| Wazuh | \`deferred\` | Deferred product-profile placeholder service or external-substrate binding with explicit intake route, source binding, and secret-reference placeholders. | Wazuh status, alerts, timestamps, and rule state remain subordinate signal context, not AegisOps workflow truth. |"
assert_fails_with \
  "${missing_wazuh_row_repo}" \
  "Missing complete Phase 52.4 compose service row: Wazuh"

manual_editing_repo="${workdir}/manual-editing"
create_valid_repo "${manual_editing_repo}"
remove_text_from_contract "${manual_editing_repo}" \
  "Manual editing of generated Compose output is not the product path."
assert_fails_with \
  "${manual_editing_repo}" \
  "Missing Phase 52.4 compose generator contract statement: Manual editing of generated Compose output is not the product path."

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Compose state is AegisOps workflow truth." \
  >>"${workflow_truth_repo}/docs/deployment/compose-generator-contract.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 52.4 compose generator contract claim: Compose state is AegisOps workflow truth"

direct_exposure_claim_repo="${workdir}/direct-exposure-claim"
create_valid_repo "${direct_exposure_claim_repo}"
printf '%s\n' "Direct backend exposure is approved." \
  >>"${direct_exposure_claim_repo}/docs/deployment/compose-generator-contract.md"
assert_fails_with \
  "${direct_exposure_claim_repo}" \
  "Forbidden Phase 52.4 compose generator contract claim: Direct backend exposure is approved"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder secrets are valid credentials." \
  >>"${placeholder_secret_repo}/docs/deployment/compose-generator-contract.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 52.4 compose generator contract claim: Placeholder secrets are valid credentials"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/compose-generator-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.4 compose generator contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 52.4 compose generator contract."

echo "Phase 52.4 compose generator contract verifier tests passed."
