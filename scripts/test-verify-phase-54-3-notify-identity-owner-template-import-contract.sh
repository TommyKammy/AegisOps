#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-54-3-notify-identity-owner-template-import-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates"
  printf '%s\n' "# AegisOps" "See [Phase 54.3 notify_identity_owner template import contract](docs/deployment/shuffle-notify-identity-owner-template-import-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/shuffle-notify-identity-owner-template-import-contract.md" \
    "${target}/docs/deployment/shuffle-notify-identity-owner-template-import-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates/notify_identity_owner-import-contract.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates/notify_identity_owner-import-contract.yaml"
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
    "${target}/docs/deployment/shuffle-notify-identity-owner-template-import-contract.md"
}

artifact_path_for() {
  printf '%s\n' "$1/docs/deployment/profiles/smb-single-node/shuffle/templates/notify_identity_owner-import-contract.yaml"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/shuffle-notify-identity-owner-template-import-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 54.3 notify_identity_owner template import contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "$(artifact_path_for "${missing_artifact_repo}")"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 54.3 notify_identity_owner template import artifact"

missing_request_repo="${workdir}/missing-request"
create_valid_repo "${missing_request_repo}"
perl -0pi -e 's/  - action_request_id\n//' "$(artifact_path_for "${missing_request_repo}")"
assert_fails_with \
  "${missing_request_repo}" \
  "Missing Phase 54.3 notify_identity_owner import artifact required_bindings item: action_request_id"

missing_approval_repo="${workdir}/missing-approval"
create_valid_repo "${missing_approval_repo}"
perl -0pi -e 's/  - approval_decision_id\n//' "$(artifact_path_for "${missing_approval_repo}")"
assert_fails_with \
  "${missing_approval_repo}" \
  "Missing Phase 54.3 notify_identity_owner import artifact required_bindings item: approval_decision_id"

missing_receipt_repo="${workdir}/missing-receipt"
create_valid_repo "${missing_receipt_repo}"
perl -0pi -e 's/  - execution_receipt_id\n//' "$(artifact_path_for "${missing_receipt_repo}")"
assert_fails_with \
  "${missing_receipt_repo}" \
  "Missing Phase 54.3 notify_identity_owner import artifact required_bindings item: execution_receipt_id"

missing_recipient_owner_repo="${workdir}/missing-recipient-owner"
create_valid_repo "${missing_recipient_owner_repo}"
perl -0pi -e 's/  - recipient_identity_owner_id\n//' "$(artifact_path_for "${missing_recipient_owner_repo}")"
assert_fails_with \
  "${missing_recipient_owner_repo}" \
  "Missing Phase 54.3 notify_identity_owner import artifact required_bindings item: recipient_identity_owner_id"

missing_message_scope_repo="${workdir}/missing-message-scope"
create_valid_repo "${missing_message_scope_repo}"
perl -0pi -e 's/  message_scope: identity-owner-low-risk-notification-only\n//' "$(artifact_path_for "${missing_message_scope_repo}")"
assert_fails_with \
  "${missing_message_scope_repo}" \
  "Missing exact Phase 54.3 notify_identity_owner import artifact line:   message_scope: identity-owner-low-risk-notification-only"

wrong_message_scope_repo="${workdir}/wrong-message-scope"
create_valid_repo "${wrong_message_scope_repo}"
perl -0pi -e 's/  message_scope: identity-owner-low-risk-notification-only/  message_scope: broad-notification-catalog/' "$(artifact_path_for "${wrong_message_scope_repo}")"
assert_fails_with \
  "${wrong_message_scope_repo}" \
  "Missing exact Phase 54.3 notify_identity_owner import artifact line:   message_scope: identity-owner-low-risk-notification-only"

missing_reviewed_version_repo="${workdir}/missing-reviewed-version"
create_valid_repo "${missing_reviewed_version_repo}"
perl -0pi -e 's/  reviewed_template_version: notify_identity_owner-v1-reviewed-2026-05-03/  reviewed_template_version: latest/' "$(artifact_path_for "${missing_reviewed_version_repo}")"
assert_fails_with \
  "${missing_reviewed_version_repo}" \
  "Mismatched Phase 54.3 notify_identity_owner import artifact field template_metadata.reviewed_template_version: expected [notify_identity_owner-v1-reviewed-2026-05-03] actual [latest]"

unreviewed_status_repo="${workdir}/unreviewed-status"
create_valid_repo "${unreviewed_status_repo}"
perl -0pi -e 's/  review_status: reviewed/  review_status: unreviewed/' "$(artifact_path_for "${unreviewed_status_repo}")"
assert_fails_with \
  "${unreviewed_status_repo}" \
  "Mismatched Phase 54.3 notify_identity_owner import artifact field template_metadata.review_status: expected [reviewed] actual [unreviewed]"

mutating_template_repo="${workdir}/mutating-template"
create_valid_repo "${mutating_template_repo}"
perl -0pi -e 's/  protected_target_state_mutation: forbidden/  protected_target_state_mutation: allowed/' "$(artifact_path_for "${mutating_template_repo}")"
assert_fails_with \
  "${mutating_template_repo}" \
  "Missing exact Phase 54.3 notify_identity_owner import artifact line:   protected_target_state_mutation: forbidden"

account_disablement_repo="${workdir}/account-disablement"
create_valid_repo "${account_disablement_repo}"
perl -0pi -e 's/  account_disablement: forbidden/  account_disablement: enabled/' "$(artifact_path_for "${account_disablement_repo}")"
assert_fails_with \
  "${account_disablement_repo}" \
  "Missing exact Phase 54.3 notify_identity_owner import artifact line:   account_disablement: forbidden"

missing_binding_contract_repo="${workdir}/missing-binding-contract"
create_valid_repo "${missing_binding_contract_repo}"
remove_text_from_contract "${missing_binding_contract_repo}" \
  "| Request | \`action_request_id\` | Missing, blank, mismatched, or inferred request id rejects the template import. |"
assert_fails_with \
  "${missing_binding_contract_repo}" \
  "Missing Phase 54.3 notify_identity_owner template import contract statement: | Request | \`action_request_id\` | Missing, blank, mismatched, or inferred request id rejects the template import. |"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Shuffle workflow success is AegisOps reconciliation truth." \
  >>"${workflow_truth_repo}/docs/deployment/shuffle-notify-identity-owner-template-import-contract.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 54.3 notify_identity_owner template import contract claim: Shuffle workflow success is AegisOps reconciliation truth"

write_capable_repo="${workdir}/write-capable"
create_valid_repo "${write_capable_repo}"
printf '%s\n' "Phase 54.3 implements write-capable Shuffle actions." \
  >>"${write_capable_repo}/docs/deployment/shuffle-notify-identity-owner-template-import-contract.md"
assert_fails_with \
  "${write_capable_repo}" \
  "Forbidden Phase 54.3 notify_identity_owner template import contract claim: Phase 54.3 implements write-capable Shuffle actions"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder secrets are valid credentials." \
  >>"${placeholder_secret_repo}/docs/deployment/shuffle-notify-identity-owner-template-import-contract.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 54.3 notify_identity_owner template import contract claim: placeholder secrets accepted as valid credentials"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/shuffle-notify-identity-owner-template-import-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 54.3 notify_identity_owner template import contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 54.3 notify_identity_owner template import contract."

echo "Phase 54.3 notify_identity_owner template import contract verifier tests passed."
