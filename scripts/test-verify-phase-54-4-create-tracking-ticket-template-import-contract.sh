#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-54-4-create-tracking-ticket-template-import-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates"
  printf '%s\n' "# AegisOps" "See [Phase 54.4 create_tracking_ticket template import contract](docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md" \
    "${target}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates/create_tracking_ticket-import-contract.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates/create_tracking_ticket-import-contract.yaml"
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
    "${target}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
}

artifact_path_for() {
  printf '%s\n' "$1/docs/deployment/profiles/smb-single-node/shuffle/templates/create_tracking_ticket-import-contract.yaml"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 54.4 create_tracking_ticket template import contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "$(artifact_path_for "${missing_artifact_repo}")"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 54.4 create_tracking_ticket template import artifact"

missing_request_repo="${workdir}/missing-request"
create_valid_repo "${missing_request_repo}"
perl -0pi -e 's/  - action_request_id\n//' "$(artifact_path_for "${missing_request_repo}")"
assert_fails_with \
  "${missing_request_repo}" \
  "Missing Phase 54.4 create_tracking_ticket import artifact required_bindings item: action_request_id"

missing_approval_repo="${workdir}/missing-approval"
create_valid_repo "${missing_approval_repo}"
perl -0pi -e 's/  - approval_decision_id\n//' "$(artifact_path_for "${missing_approval_repo}")"
assert_fails_with \
  "${missing_approval_repo}" \
  "Missing Phase 54.4 create_tracking_ticket import artifact required_bindings item: approval_decision_id"

missing_receipt_repo="${workdir}/missing-receipt"
create_valid_repo "${missing_receipt_repo}"
perl -0pi -e 's/  - execution_receipt_id\n//' "$(artifact_path_for "${missing_receipt_repo}")"
assert_fails_with \
  "${missing_receipt_repo}" \
  "Missing Phase 54.4 create_tracking_ticket import artifact required_bindings item: execution_receipt_id"

missing_ticket_pointer_repo="${workdir}/missing-ticket-pointer"
create_valid_repo "${missing_ticket_pointer_repo}"
perl -0pi -e 's/  - ticket_pointer_id\n//' "$(artifact_path_for "${missing_ticket_pointer_repo}")"
assert_fails_with \
  "${missing_ticket_pointer_repo}" \
  "Missing Phase 54.4 create_tracking_ticket import artifact required_bindings item: ticket_pointer_id"

missing_ticket_system_repo="${workdir}/missing-ticket-system"
create_valid_repo "${missing_ticket_system_repo}"
perl -0pi -e 's/  - ticket_system_id\n//' "$(artifact_path_for "${missing_ticket_system_repo}")"
assert_fails_with \
  "${missing_ticket_system_repo}" \
  "Missing Phase 54.4 create_tracking_ticket import artifact required_bindings item: ticket_system_id"

missing_custody_repo="${workdir}/missing-ticket-custody"
create_valid_repo "${missing_custody_repo}"
perl -0pi -e 's/  ticket_pointer_custody: explicit non-authoritative coordination pointer required\n//' "$(artifact_path_for "${missing_custody_repo}")"
assert_fails_with \
  "${missing_custody_repo}" \
  "Missing exact Phase 54.4 create_tracking_ticket import artifact line:   ticket_pointer_custody: explicit non-authoritative coordination pointer required"

missing_reviewed_version_repo="${workdir}/missing-reviewed-version"
create_valid_repo "${missing_reviewed_version_repo}"
perl -0pi -e 's/  reviewed_template_version: create_tracking_ticket-v1-reviewed-2026-05-03/  reviewed_template_version: latest/' "$(artifact_path_for "${missing_reviewed_version_repo}")"
assert_fails_with \
  "${missing_reviewed_version_repo}" \
  "Mismatched Phase 54.4 create_tracking_ticket import artifact field template_metadata.reviewed_template_version: expected [create_tracking_ticket-v1-reviewed-2026-05-03] actual [latest]"

weakened_authority_boundary_repo="${workdir}/weakened-authority-boundary"
create_valid_repo "${weakened_authority_boundary_repo}"
perl -0pi -e 's/^authority_boundary: .*/authority_boundary: Ticket status is AegisOps case truth./m' "$(artifact_path_for "${weakened_authority_boundary_repo}")"
assert_fails_with \
  "${weakened_authority_boundary_repo}" \
  "Missing exact Phase 54.4 create_tracking_ticket import artifact line: authority_boundary: Ticket pointer, ticket status, ticket comments, ticket assignments, ticket SLA state, Shuffle workflow status, success, failure, callback payloads, execution logs, generated config, and template metadata remain subordinate coordination or automation context; AegisOps control-plane records remain authoritative for approval, action request, execution receipt, reconciliation, release, gate, limitation, and closeout truth."

ticket_truth_repo="${workdir}/ticket-truth"
create_valid_repo "${ticket_truth_repo}"
printf '%s\n' "Ticket status is AegisOps case truth." \
  >>"${ticket_truth_repo}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
assert_fails_with \
  "${ticket_truth_repo}" \
  "Forbidden Phase 54.4 create_tracking_ticket template import contract claim: Ticket status is AegisOps case truth"

ticket_close_truth_repo="${workdir}/ticket-close-truth"
create_valid_repo "${ticket_close_truth_repo}"
printf '%s\n' "Ticket close is AegisOps reconciliation truth." \
  >>"${ticket_close_truth_repo}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
assert_fails_with \
  "${ticket_close_truth_repo}" \
  "Forbidden Phase 54.4 create_tracking_ticket template import contract claim: Ticket close is AegisOps reconciliation truth"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Shuffle workflow success is AegisOps reconciliation truth." \
  >>"${workflow_truth_repo}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 54.4 create_tracking_ticket template import contract claim: Shuffle workflow success is AegisOps reconciliation truth"

missing_binding_contract_repo="${workdir}/missing-binding-contract"
create_valid_repo "${missing_binding_contract_repo}"
remove_text_from_contract "${missing_binding_contract_repo}" \
  "| Ticket pointer | \`ticket_pointer_id\`, \`ticket_system_id\`, \`ticket_pointer_custody\` | Missing, blank, inferred, or authoritative ticket pointer fields reject the template import. |"
assert_fails_with \
  "${missing_binding_contract_repo}" \
  "Missing Phase 54.4 create_tracking_ticket template import contract statement: | Ticket pointer | \`ticket_pointer_id\`, \`ticket_system_id\`, \`ticket_pointer_custody\` | Missing, blank, inferred, or authoritative ticket pointer fields reject the template import. |"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder secrets are valid credentials." \
  >>"${placeholder_secret_repo}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 54.4 create_tracking_ticket template import contract claim: placeholder secrets accepted as valid credentials"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 54.4 create_tracking_ticket template import contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 54.4 create_tracking_ticket template import contract."

echo "Phase 54.4 create_tracking_ticket template import contract verifier tests passed."
