#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-54-1-shuffle-profile-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/shuffle"
  printf '%s\n' "# AegisOps" "See [Phase 54.1 Shuffle profile contract](docs/deployment/shuffle-smb-single-node-profile-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/shuffle-smb-single-node-profile-contract.md" \
    "${target}/docs/deployment/shuffle-smb-single-node-profile-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
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
    "${target}/docs/deployment/shuffle-smb-single-node-profile-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/shuffle-smb-single-node-profile-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 54.1 Shuffle profile contract"

missing_profile_repo="${workdir}/missing-profile"
create_valid_repo "${missing_profile_repo}"
rm "${missing_profile_repo}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
assert_fails_with \
  "${missing_profile_repo}" \
  "Missing Phase 54.1 Shuffle profile artifact"

missing_backend_contract_repo="${workdir}/missing-backend-contract"
create_valid_repo "${missing_backend_contract_repo}"
remove_text_from_contract "${missing_backend_contract_repo}" \
  "| backend | Yes | \`2.2.0\` | \`ghcr.io/shuffle/shuffle-backend:2.2.0\` | 2 vCPU, 4 GB RAM, bounded app/file storage. | \`5001/tcp\` internal API only through reviewed proxy route. | \`shuffle-apps\`; \`shuffle-files\`; \`shuffle-docker-socket-proxy\`. | \`shuffle-api-credential-ref\`; \`shuffle-callback-secret-ref\`; \`shuffle-encryption-modifier-ref\`. | Backend API and callback payloads remain subordinate delegated-execution context until admitted by AegisOps records. |"
assert_fails_with \
  "${missing_backend_contract_repo}" \
  "Missing complete Phase 54.1 Shuffle component row: backend"

missing_orborus_profile_repo="${workdir}/missing-orborus-profile"
create_valid_repo "${missing_orborus_profile_repo}"
perl -0pi -e 's/\n  orborus:\n    required: true.*?(?=\n  worker:)/\n/s' \
  "${missing_orborus_profile_repo}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
perl -0pi -e 's/\n  orborus:\n    required: true\n    version: 2\.2\.0.*?(?=\n  worker:)/\n/s' \
  "${missing_orborus_profile_repo}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
assert_fails_with \
  "${missing_orborus_profile_repo}" \
  "Missing complete Phase 54.1 Shuffle profile artifact component: orborus"

missing_worker_version_repo="${workdir}/missing-worker-version"
create_valid_repo "${missing_worker_version_repo}"
remove_text_from_contract "${missing_worker_version_repo}" \
  "| worker | \`2.2.0\` | exact | Shuffle 1.x; unreviewed Shuffle 2.3.x; \`latest\`; RC; beta. | Worker image changes require later workflow-catalog and delegation-binding evidence. |"
assert_fails_with \
  "${missing_worker_version_repo}" \
  "Missing complete Phase 54.1 Shuffle version matrix row: worker"

unpinned_version_repo="${workdir}/unpinned-version"
create_valid_repo "${unpinned_version_repo}"
perl -0pi -e 's/version: 2\.2\.0/version: latest/' \
  "${unpinned_version_repo}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
assert_fails_with \
  "${unpinned_version_repo}" \
  "Forbidden Phase 54.1 Shuffle profile artifact: unpinned version or image reference detected"

missing_ports_repo="${workdir}/missing-ports"
create_valid_repo "${missing_ports_repo}"
perl -0pi -e 's/    ports:\n      - 5001\/tcp internal backend API\n/    ports:\n/' \
  "${missing_ports_repo}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
assert_fails_with \
  "${missing_ports_repo}" \
  "Missing complete Phase 54.1 Shuffle profile artifact component: backend"

missing_volumes_repo="${workdir}/missing-volumes"
create_valid_repo "${missing_volumes_repo}"
perl -0pi -e 's/    volumes:\n      - shuffle-apps\n      - shuffle-files\n      - shuffle-docker-socket-proxy\n/    volumes:\n/' \
  "${missing_volumes_repo}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
assert_fails_with \
  "${missing_volumes_repo}" \
  "Missing complete Phase 54.1 Shuffle profile artifact component: backend"

missing_credentials_repo="${workdir}/missing-credentials"
create_valid_repo "${missing_credentials_repo}"
perl -0pi -e 's/    credentials:\n      - shuffle-api-credential-ref\n      - shuffle-callback-secret-ref\n      - shuffle-encryption-modifier-ref\n/    credentials:\n/' \
  "${missing_credentials_repo}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
assert_fails_with \
  "${missing_credentials_repo}" \
  "Missing complete Phase 54.1 Shuffle profile artifact component: backend"

missing_api_callback_repo="${workdir}/missing-api-callback"
create_valid_repo "${missing_api_callback_repo}"
perl -0pi -e 's/  api_url: http:\/\/shuffle-backend:5001\n//' \
  "${missing_api_callback_repo}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
assert_fails_with \
  "${missing_api_callback_repo}" \
  "Missing Phase 54.1 Shuffle profile artifact term: api_url: http://shuffle-backend:5001"

missing_api_contract_repo="${workdir}/missing-api-contract"
create_valid_repo "${missing_api_contract_repo}"
remove_text_from_contract "${missing_api_contract_repo}" \
  "- API URL: the reviewed internal API URL is \`http://shuffle-backend:5001\`; external access must be proxy-mediated and cannot imply direct backend exposure."
assert_fails_with \
  "${missing_api_contract_repo}" \
  "Missing Phase 54.1 Shuffle profile contract statement: - API URL: the reviewed internal API URL is \`http://shuffle-backend:5001\`; external access must be proxy-mediated and cannot imply direct backend exposure."

missing_callback_contract_repo="${workdir}/missing-callback-contract"
create_valid_repo "${missing_callback_contract_repo}"
remove_text_from_contract "${missing_callback_contract_repo}" \
  "- Callback URL: the reviewed AegisOps callback URL placeholder is \`<aegisops-shuffle-callback-url>\` and must bind to an AegisOps-owned callback route before runtime use."
assert_fails_with \
  "${missing_callback_contract_repo}" \
  "Missing Phase 54.1 Shuffle profile contract statement: - Callback URL: the reviewed AegisOps callback URL placeholder is \`<aegisops-shuffle-callback-url>\` and must bind to an AegisOps-owned callback route before runtime use."

missing_dependencies_contract_repo="${workdir}/missing-dependencies-contract"
create_valid_repo "${missing_dependencies_contract_repo}"
remove_text_from_contract "${missing_dependencies_contract_repo}" \
  "- Dependency expectations: Shuffle depends on reviewed Docker/Compose posture, proxy custody, trusted secret references, AegisOps approval/action-request records, and later workflow-catalog custody before delegated execution can run."
assert_fails_with \
  "${missing_dependencies_contract_repo}" \
  "Missing Phase 54.1 Shuffle profile contract statement: - Dependency expectations: Shuffle depends on reviewed Docker/Compose posture, proxy custody, trusted secret references, AegisOps approval/action-request records, and later workflow-catalog custody before delegated execution can run."

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder Shuffle API keys are valid credentials." \
  >>"${placeholder_secret_repo}/docs/deployment/shuffle-smb-single-node-profile-contract.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 54.1 Shuffle profile contract claim: placeholder secrets accepted as valid credentials"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Shuffle workflow success is AegisOps reconciliation truth." \
  >>"${workflow_truth_repo}/docs/deployment/shuffle-smb-single-node-profile-contract.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 54.1 Shuffle profile contract claim: Shuffle workflow success is AegisOps reconciliation truth"

readiness_overclaim_repo="${workdir}/readiness-overclaim"
create_valid_repo "${readiness_overclaim_repo}"
printf '%s\n' "Phase 54.1 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement." \
  >>"${readiness_overclaim_repo}/docs/deployment/shuffle-smb-single-node-profile-contract.md"
assert_fails_with \
  "${readiness_overclaim_repo}" \
  "Forbidden Phase 54.1 Shuffle profile contract claim: Phase 54.1 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/shuffle-smb-single-node-profile-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 54.1 Shuffle profile contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 54.1 Shuffle profile contract."

echo "Phase 54.1 Shuffle profile contract verifier tests passed."
