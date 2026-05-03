#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-54-8-manual-fallback-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates"
  printf '%s\n' \
    "# AegisOps" \
    "See [Phase 54.8 manual fallback contract](docs/deployment/shuffle-manual-fallback-contract.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/deployment/shuffle-manual-fallback-contract.md" \
    "${target}/docs/deployment/shuffle-manual-fallback-contract.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
  for template in \
    notify_identity_owner \
    create_tracking_ticket \
    enrichment_only_lookup \
    operator_notification \
    manual_escalation_request; do
    cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates/${template}-import-contract.yaml" \
      "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates/${template}-import-contract.yaml"
  done
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

local_path_case_index=0
assert_rejects_contract_local_path() {
  local path_text="$1"
  local target

  local_path_case_index=$((local_path_case_index + 1))
  target="${workdir}/local-path-${local_path_case_index}"
  create_valid_repo "${target}"
  printf 'Use %s for setup.\n' "${path_text}" \
    >>"${target}/docs/deployment/shuffle-manual-fallback-contract.md"
  assert_fails_with \
    "${target}" \
    "Forbidden Phase 54.8 manual fallback contract: workstation-local absolute path detected"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/shuffle-manual-fallback-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 54.8 manual fallback contract"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "${missing_artifact_repo}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 54.8 manual fallback artifact"

missing_owner_repo="${workdir}/missing-owner"
create_valid_repo "${missing_owner_repo}"
perl -0pi -e 's/  fallback_owner_id: explicit fallback owner required\n//' \
  "${missing_owner_repo}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
assert_fails_with \
  "${missing_owner_repo}" \
  "Mismatched Phase 54.8 manual fallback artifact field required_record.fallback_owner_id: expected [explicit fallback owner required] actual [<missing>]"

missing_owner_field_repo="${workdir}/missing-owner-field"
create_valid_repo "${missing_owner_field_repo}"
perl -0pi -e 's/  - fallback_owner_id\n//' \
  "${missing_owner_field_repo}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
assert_fails_with \
  "${missing_owner_field_repo}" \
  "Missing Phase 54.8 manual fallback artifact required_record_fields item: fallback_owner_id"

approval_bypass_repo="${workdir}/approval-bypass"
create_valid_repo "${approval_bypass_repo}"
perl -0pi -e 's/  approval_bypass_note: reject/  approval_bypass_note: allow/' \
  "${approval_bypass_repo}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
assert_fails_with \
  "${approval_bypass_repo}" \
  "Mismatched Phase 54.8 manual fallback artifact field validation_rules.approval_bypass_note: expected [reject] actual [allow]"

unavailable_success_repo="${workdir}/unavailable-success"
create_valid_repo "${unavailable_success_repo}"
perl -0pi -e 's/  unavailable_reported_success: reject/  unavailable_reported_success: allow/' \
  "${unavailable_success_repo}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
assert_fails_with \
  "${unavailable_success_repo}" \
  "Mismatched Phase 54.8 manual fallback artifact field validation_rules.unavailable_reported_success: expected [reject] actual [allow]"

manual_note_truth_repo="${workdir}/manual-note-truth"
create_valid_repo "${manual_note_truth_repo}"
perl -0pi -e 's/  manual_note_as_reconciliation_truth: reject/  manual_note_as_reconciliation_truth: allow/' \
  "${manual_note_truth_repo}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
assert_fails_with \
  "${manual_note_truth_repo}" \
  "Mismatched Phase 54.8 manual fallback artifact field validation_rules.manual_note_as_reconciliation_truth: expected [reject] actual [allow]"

missing_state_repo="${workdir}/missing-state"
create_valid_repo "${missing_state_repo}"
perl -0pi -e 's/  - stale_receipt\n//' \
  "${missing_state_repo}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
assert_fails_with \
  "${missing_state_repo}" \
  "Missing Phase 54.8 manual fallback artifact fallback_states item: stale_receipt"

missing_template_coverage_repo="${workdir}/missing-template-coverage"
create_valid_repo "${missing_template_coverage_repo}"
perl -0pi -e 's/  - template_id: operator_notification\n    action_type: operator_notification\n    scope: operator-notification-only\n    manual_fallback_required: true\n//' \
  "${missing_template_coverage_repo}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
assert_fails_with \
  "${missing_template_coverage_repo}" \
  "Missing Phase 54.8 manual fallback reviewed_template_coverage entry for operator_notification"

bypass_claim_repo="${workdir}/bypass-claim"
create_valid_repo "${bypass_claim_repo}"
printf '%s\n' "Manual fallback bypasses AegisOps approval." \
  >>"${bypass_claim_repo}/docs/deployment/shuffle-manual-fallback-contract.md"
assert_fails_with \
  "${bypass_claim_repo}" \
  "Forbidden Phase 54.8 manual fallback contract claim: Manual fallback bypasses AegisOps approval"

hidden_required_phrase_repo="${workdir}/hidden-required-phrase"
create_valid_repo "${hidden_required_phrase_repo}"
perl -0pi -e 's/- \*\*Status\*\*: Accepted contract/- **Status**: Draft contract/' \
  "${hidden_required_phrase_repo}/docs/deployment/shuffle-manual-fallback-contract.md"
printf '%s\n' '```' '- **Status**: Accepted contract' '```' \
  >>"${hidden_required_phrase_repo}/docs/deployment/shuffle-manual-fallback-contract.md"
assert_fails_with \
  "${hidden_required_phrase_repo}" \
  "Missing Phase 54.8 manual fallback contract statement: - **Status**: Accepted contract"

hidden_forbidden_listing_repo="${workdir}/hidden-forbidden-listing"
create_valid_repo "${hidden_forbidden_listing_repo}"
perl -0pi -e 's/- Manual fallback note is AegisOps reconciliation truth\./- Manual fallback note remains subordinate operator guidance./' \
  "${hidden_forbidden_listing_repo}/docs/deployment/shuffle-manual-fallback-contract.md"
printf '%s\n' '```' '- Manual fallback note is AegisOps reconciliation truth.' '```' \
  >>"${hidden_forbidden_listing_repo}/docs/deployment/shuffle-manual-fallback-contract.md"
assert_fails_with \
  "${hidden_forbidden_listing_repo}" \
  "Missing Phase 54.8 forbidden claim listing: - Manual fallback note is AegisOps reconciliation truth."

assert_rejects_contract_local_path "$(printf '%s%s/example/AegisOps' '/' "Users")"
assert_rejects_contract_local_path "$(printf '%s%s/example/AegisOps' '/' "home")"
assert_rejects_contract_local_path "$(printf '%sopt%sproduct%sAegisOps' '/' '/' '/')"
assert_rejects_contract_local_path "$(printf '%smnt%sworkspace%sAegisOps' '/' '/' '/')"
assert_rejects_contract_local_path "$(printf '%sVolumes%sworkspace%sAegisOps' '/' '/' '/')"
assert_rejects_contract_local_path "$(printf '%sprivate%stmp%sAegisOps' '/' '/' '/')"
assert_rejects_contract_local_path "$(printf '%sroot%sAegisOps' '/' '/')"
assert_rejects_contract_local_path "$(printf 'D:%bOps%bAegisOps' '\\' '\\')"
assert_rejects_contract_local_path "$(printf 'E:%sOps%sAegisOps' '/' '/')"
assert_rejects_contract_local_path "$(printf '%b%bserver%bshare%bAegisOps' '\\' '\\' '\\' '\\')"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "Missing README Phase 54.8 manual fallback contract link: [Phase 54.8 manual fallback contract](docs/deployment/shuffle-manual-fallback-contract.md)"

echo "Phase 54.8 manual fallback contract verifier tests passed."
