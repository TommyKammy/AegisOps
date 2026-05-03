#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-56-1-today-view-projection-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node"
  printf '%s\n' \
    "# AegisOps" \
    "See [Phase 56.1 Today view backend projection contract](docs/deployment/today-view-backend-projection-contract.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/deployment/today-view-backend-projection-contract.md" \
    "${target}/docs/deployment/today-view-backend-projection-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/today-view-projection.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/today-view-projection.yaml"
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
    "${target}/docs/deployment/today-view-backend-projection-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/today-view-backend-projection-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 56.1 Today projection contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "${missing_artifact_repo}/docs/deployment/profiles/smb-single-node/today-view-projection.yaml"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 56.1 Today projection artifact"

missing_lane_repo="${workdir}/missing-lane"
create_valid_repo "${missing_lane_repo}"
perl -0pi -e 's/^  - evidence_gaps\n//m' \
  "${missing_lane_repo}/docs/deployment/profiles/smb-single-node/today-view-projection.yaml"
assert_fails_with \
  "${missing_lane_repo}" \
  "Missing Phase 56.1 Today projection lane: evidence_gaps"

missing_state_repo="${workdir}/missing-state"
create_valid_repo "${missing_state_repo}"
perl -0pi -e 's/^  - evidence_gap\n//m' \
  "${missing_state_repo}/docs/deployment/profiles/smb-single-node/today-view-projection.yaml"
assert_fails_with \
  "${missing_state_repo}" \
  "Missing Phase 56.1 Today projection state: evidence_gap"

missing_negative_repo="${workdir}/missing-negative"
create_valid_repo "${missing_negative_repo}"
perl -0pi -e 's/^  - ai-focus-as-authority\n//m' \
  "${missing_negative_repo}/docs/deployment/profiles/smb-single-node/today-view-projection.yaml"
assert_fails_with \
  "${missing_negative_repo}" \
  "Missing Phase 56.1 Today projection negative validation test: ai-focus-as-authority"

missing_advisory_repo="${workdir}/missing-advisory"
create_valid_repo "${missing_advisory_repo}"
remove_text_from_contract "${missing_advisory_repo}" "AI-suggested focus is advisory-only"
assert_fails_with \
  "${missing_advisory_repo}" \
  "Missing Phase 56.1 Today projection contract statement: AI-suggested focus is advisory-only"

authority_truth_repo="${workdir}/authority-truth"
create_valid_repo "${authority_truth_repo}"
printf '%s\n' "Today projection is AegisOps approval truth." \
  >>"${authority_truth_repo}/docs/deployment/today-view-backend-projection-contract.md"
assert_fails_with \
  "${authority_truth_repo}" \
  "Forbidden Phase 56.1 Today projection claim: Today projection is AegisOps approval truth"

stale_truth_repo="${workdir}/stale-truth"
create_valid_repo "${stale_truth_repo}"
printf '%s\n' "Stale Today projection output is current AegisOps truth." \
  >>"${stale_truth_repo}/docs/deployment/today-view-backend-projection-contract.md"
assert_fails_with \
  "${stale_truth_repo}" \
  "Forbidden Phase 56.1 Today projection claim: Stale Today projection output is current AegisOps truth"

missing_forbidden_claim_repo="${workdir}/missing-forbidden-claim"
create_valid_repo "${missing_forbidden_claim_repo}"
remove_text_from_contract "${missing_forbidden_claim_repo}" \
  "AI-suggested focus approves actions."
assert_fails_with \
  "${missing_forbidden_claim_repo}" \
  "Missing Phase 56.1 Today projection forbidden claim: AI-suggested focus approves actions"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for projection review.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/today-view-backend-projection-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 56.1 Today projection artifact: workstation-local absolute path detected"

secret_looking_value_repo="${workdir}/secret-looking-value"
create_valid_repo "${secret_looking_value_repo}"
printf '%s\n' "projection_token: CorrectHorseBatteryStaple42" \
  >>"${secret_looking_value_repo}/docs/deployment/profiles/smb-single-node/today-view-projection.yaml"
assert_fails_with \
  "${secret_looking_value_repo}" \
  "Forbidden Phase 56.1 Today projection artifact: committed secret-looking value detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 56.1 Today view backend projection contract."

echo "Phase 56.1 Today view projection verifier tests passed."
