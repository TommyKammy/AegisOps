#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-54-2-reviewed-workflow-template-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/shuffle"
  printf '%s\n' "# AegisOps" "See [Phase 54.2 reviewed workflow template contract](docs/deployment/shuffle-reviewed-workflow-template-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/shuffle-reviewed-workflow-template-contract.md" \
    "${target}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/reviewed-workflow-template-contract.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/shuffle/reviewed-workflow-template-contract.yaml"
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
    "${target}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
}

artifact_path_for() {
  printf '%s\n' "$1/docs/deployment/profiles/smb-single-node/shuffle/reviewed-workflow-template-contract.yaml"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 54.2 reviewed workflow template contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "$(artifact_path_for "${missing_artifact_repo}")"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 54.2 reviewed workflow template artifact"

missing_correlation_input_repo="${workdir}/missing-correlation-input"
create_valid_repo "${missing_correlation_input_repo}"
perl -0pi -e 's/  - correlation_id\n//' "$(artifact_path_for "${missing_correlation_input_repo}")"
assert_fails_with \
  "${missing_correlation_input_repo}" \
  "Missing Phase 54.2 reviewed workflow template artifact required_inputs item: correlation_id"

missing_action_request_repo="${workdir}/missing-action-request"
create_valid_repo "${missing_action_request_repo}"
perl -0pi -e 's/  - action_request_id\n//' "$(artifact_path_for "${missing_action_request_repo}")"
assert_fails_with \
  "${missing_action_request_repo}" \
  "Missing Phase 54.2 reviewed workflow template artifact required_inputs item: action_request_id"

missing_approval_decision_repo="${workdir}/missing-approval-decision"
create_valid_repo "${missing_approval_decision_repo}"
perl -0pi -e 's/  - approval_decision_id\n//' "$(artifact_path_for "${missing_approval_decision_repo}")"
assert_fails_with \
  "${missing_approval_decision_repo}" \
  "Missing Phase 54.2 reviewed workflow template artifact required_inputs item: approval_decision_id"

missing_receipt_repo="${workdir}/missing-receipt"
create_valid_repo "${missing_receipt_repo}"
perl -0pi -e 's/  - execution_receipt_id\n//' "$(artifact_path_for "${missing_receipt_repo}")"
assert_fails_with \
  "${missing_receipt_repo}" \
  "Missing Phase 54.2 reviewed workflow template artifact required_outputs item: execution_receipt_id"

missing_normalized_receipt_repo="${workdir}/missing-normalized-receipt"
create_valid_repo "${missing_normalized_receipt_repo}"
perl -0pi -e 's/  - normalized_receipt_ref\n//' "$(artifact_path_for "${missing_normalized_receipt_repo}")"
assert_fails_with \
  "${missing_normalized_receipt_repo}" \
  "Missing Phase 54.2 reviewed workflow template artifact required_outputs item: normalized_receipt_ref"

missing_owner_repo="${workdir}/missing-owner"
create_valid_repo "${missing_owner_repo}"
perl -0pi -e 's/  owner: AegisOps maintainers\n//' "$(artifact_path_for "${missing_owner_repo}")"
assert_fails_with \
  "${missing_owner_repo}" \
  "Missing exact Phase 54.2 reviewed workflow template artifact line:   owner: AegisOps maintainers"

unreviewed_status_repo="${workdir}/unreviewed-status"
create_valid_repo "${unreviewed_status_repo}"
perl -0pi -e 's/  review_status: reviewed/  review_status: unreviewed/' "$(artifact_path_for "${unreviewed_status_repo}")"
assert_fails_with \
  "${unreviewed_status_repo}" \
  "Mismatched Phase 54.2 reviewed workflow template artifact field template_metadata.review_status: expected [reviewed] actual [unreviewed]"

missing_correlation_contract_repo="${workdir}/missing-correlation-contract"
create_valid_repo "${missing_correlation_contract_repo}"
remove_text_from_contract "${missing_correlation_contract_repo}" \
  "| Correlation | \`correlation_id\` in both inputs and outputs | Missing, blank, or one-sided correlation rejects the template. |"
assert_fails_with \
  "${missing_correlation_contract_repo}" \
  "Missing Phase 54.2 reviewed workflow template contract statement: | Correlation | \`correlation_id\` in both inputs and outputs | Missing, blank, or one-sided correlation rejects the template. |"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Shuffle workflow success is AegisOps reconciliation truth." \
  >>"${workflow_truth_repo}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 54.2 reviewed workflow template contract claim: Shuffle workflow success is AegisOps reconciliation truth"

unreviewed_mainline_repo="${workdir}/unreviewed-mainline"
create_valid_repo "${unreviewed_mainline_repo}"
printf '%s\n' "Unreviewed Shuffle templates may enter the product mainline." \
  >>"${unreviewed_mainline_repo}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
assert_fails_with \
  "${unreviewed_mainline_repo}" \
  "Forbidden Phase 54.2 reviewed workflow template contract claim: Unreviewed Shuffle templates may enter the product mainline"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder secrets are valid credentials." \
  >>"${placeholder_secret_repo}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 54.2 reviewed workflow template contract claim: placeholder secrets accepted as valid credentials"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 54.2 reviewed workflow template contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 54.2 reviewed workflow template contract."

echo "Phase 54.2 reviewed workflow template contract verifier tests passed."
