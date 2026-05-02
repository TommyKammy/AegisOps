#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-53-1-wazuh-profile-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/wazuh"
  printf '%s\n' "# AegisOps" "See [Phase 53.1 Wazuh profile contract](docs/deployment/wazuh-smb-single-node-profile-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/wazuh-smb-single-node-profile-contract.md" \
    "${target}/docs/deployment/wazuh-smb-single-node-profile-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
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
    "${target}/docs/deployment/wazuh-smb-single-node-profile-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/wazuh-smb-single-node-profile-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 53.1 Wazuh profile contract"

missing_profile_repo="${workdir}/missing-profile"
create_valid_repo "${missing_profile_repo}"
rm "${missing_profile_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${missing_profile_repo}" \
  "Missing Phase 53.1 Wazuh profile artifact"

missing_manager_repo="${workdir}/missing-manager"
create_valid_repo "${missing_manager_repo}"
remove_text_from_contract "${missing_manager_repo}" \
  "| manager | Yes | \`4.12.0\` | \`wazuh/wazuh-manager:4.12.0\` | 2 vCPU, 6 GB RAM, 120 GB durable substrate storage. | \`1514/tcp\` internal agent event intake; \`1514/udp\` internal agent event intake; \`1515/tcp\` internal agent enrollment; \`55000/tcp\` internal manager API. | \`wazuh-manager-data\`; \`wazuh-manager-rules\`; \`wazuh-manager-logs\`. | \`wazuh-manager-api-tls\`; \`wazuh-ingest-shared-secret-ref\`. | Manager status and alert state remain subordinate signal context until admitted and linked by AegisOps. |"
assert_fails_with \
  "${missing_manager_repo}" \
  "Missing complete Phase 53.1 Wazuh component row: manager"

missing_indexer_profile_repo="${workdir}/missing-indexer-profile"
create_valid_repo "${missing_indexer_profile_repo}"
perl -0pi -e 's/\n  indexer:\n    required: true.*?(?=\n  dashboard:)/\n/s' \
  "${missing_indexer_profile_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${missing_indexer_profile_repo}" \
  "Missing complete Phase 53.1 Wazuh profile artifact component: indexer"

missing_dashboard_version_repo="${workdir}/missing-dashboard-version"
create_valid_repo "${missing_dashboard_version_repo}"
remove_text_from_contract "${missing_dashboard_version_repo}" \
  "| dashboard | \`4.12.0\` | exact | Wazuh 3.x; unreviewed Wazuh 5.x; \`latest\`; RC; beta. | Upgrade evidence is deferred to a later Phase 53 child issue. |"
assert_fails_with \
  "${missing_dashboard_version_repo}" \
  "Missing complete Phase 53.1 Wazuh version matrix row: dashboard"

unpinned_version_repo="${workdir}/unpinned-version"
create_valid_repo "${unpinned_version_repo}"
perl -0pi -e 's/version: 4\.12\.0/version: latest/' \
  "${unpinned_version_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${unpinned_version_repo}" \
  "Forbidden Phase 53.1 Wazuh profile artifact: unpinned version or image reference detected"

missing_resources_repo="${workdir}/missing-resources"
create_valid_repo "${missing_resources_repo}"
perl -0pi -e 's/    resource_expectation: 2 vCPU, 6 GB RAM, 120 GB durable substrate storage\n//' \
  "${missing_resources_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${missing_resources_repo}" \
  "Missing complete Phase 53.1 Wazuh profile artifact component: manager"

missing_certificates_repo="${workdir}/missing-certificates"
create_valid_repo "${missing_certificates_repo}"
perl -0pi -e 's/    certificates:\n      - wazuh-dashboard-tls\n      - wazuh-dashboard-indexer-client-cert\n//' \
  "${missing_certificates_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${missing_certificates_repo}" \
  "Missing complete Phase 53.1 Wazuh profile artifact component: dashboard"

wrong_dashboard_image_repo="${workdir}/wrong-dashboard-image"
create_valid_repo "${wrong_dashboard_image_repo}"
perl -0pi -e 's/image: wazuh\/wazuh-dashboard:4\.12\.0/image: wazuh\/wazuh-manager:4.12.0/' \
  "${wrong_dashboard_image_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${wrong_dashboard_image_repo}" \
  "Missing complete Phase 53.1 Wazuh profile artifact component: dashboard"

empty_ports_repo="${workdir}/empty-ports"
create_valid_repo "${empty_ports_repo}"
perl -0pi -e 's/    ports:\n      - 1514\/tcp internal agent event intake\n      - 1514\/udp internal agent event intake\n      - 1515\/tcp internal agent enrollment\n      - 55000\/tcp internal manager API\n/    ports:\n/' \
  "${empty_ports_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${empty_ports_repo}" \
  "Missing complete Phase 53.1 Wazuh profile artifact component: manager"

empty_volumes_repo="${workdir}/empty-volumes"
create_valid_repo "${empty_volumes_repo}"
perl -0pi -e 's/    volumes:\n      - wazuh-indexer-data\n      - wazuh-indexer-backup\n/    volumes:\n/' \
  "${empty_volumes_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${empty_volumes_repo}" \
  "Missing complete Phase 53.1 Wazuh profile artifact component: indexer"

blank_boundary_repo="${workdir}/blank-boundary"
create_valid_repo "${blank_boundary_repo}"
perl -0pi -e 's/    boundary: Dashboard state is operator-facing substrate context only and cannot become AegisOps workflow truth\./    boundary: /' \
  "${blank_boundary_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${blank_boundary_repo}" \
  "Missing complete Phase 53.1 Wazuh profile artifact component: dashboard"

missing_matrix_incompatibility_repo="${workdir}/missing-matrix-incompatibility"
create_valid_repo "${missing_matrix_incompatibility_repo}"
perl -0pi -e 's/incompatible_versions: Wazuh 3\.x, unreviewed Wazuh 5\.x, latest, rc, beta/incompatible_versions: latest, rc, beta/g' \
  "${missing_matrix_incompatibility_repo}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
assert_fails_with \
  "${missing_matrix_incompatibility_repo}" \
  "Missing complete Phase 53.1 Wazuh profile artifact version matrix row: manager"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Wazuh status is AegisOps workflow truth." \
  >>"${workflow_truth_repo}/docs/deployment/wazuh-smb-single-node-profile-contract.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 53.1 Wazuh profile contract claim: Wazuh status is AegisOps workflow truth"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder secrets are valid credentials." \
  >>"${placeholder_secret_repo}/docs/deployment/wazuh-smb-single-node-profile-contract.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 53.1 Wazuh profile contract claim: Placeholder secrets are valid credentials"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/wazuh-smb-single-node-profile-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 53.1 Wazuh profile contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 53.1 Wazuh profile contract."

echo "Phase 53.1 Wazuh profile contract verifier tests passed."
