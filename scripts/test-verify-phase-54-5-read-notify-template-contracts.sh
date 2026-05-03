#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-54-5-read-notify-template-contracts.sh"

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
    "See [Phase 54.5 Read/Notify template contracts](docs/deployment/shuffle-read-notify-template-contracts.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/deployment/shuffle-read-notify-template-contracts.md" \
    "${target}/docs/deployment/shuffle-read-notify-template-contracts.md"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates/enrichment_only_lookup-import-contract.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates/enrichment_only_lookup-import-contract.yaml"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates/operator_notification-import-contract.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates/operator_notification-import-contract.yaml"
  cp "${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates/manual_escalation_request-import-contract.yaml" \
    "${target}/docs/deployment/profiles/smb-single-node/shuffle/templates/manual_escalation_request-import-contract.yaml"
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

artifact_path_for() {
  printf '%s\n' "$1/docs/deployment/profiles/smb-single-node/shuffle/templates/$2-import-contract.yaml"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/shuffle-read-notify-template-contracts.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 54.5 Read/Notify template contract"

missing_enrichment_artifact_repo="${workdir}/missing-enrichment-artifact"
create_valid_repo "${missing_enrichment_artifact_repo}"
rm "$(artifact_path_for "${missing_enrichment_artifact_repo}" enrichment_only_lookup)"
assert_fails_with \
  "${missing_enrichment_artifact_repo}" \
  "Missing Phase 54.5 enrichment_only_lookup template artifact"

enrichment_write_capable_repo="${workdir}/enrichment-write-capable"
create_valid_repo "${enrichment_write_capable_repo}"
perl -0pi -e 's/  enrichment_only: required/  enrichment_only: optional/' "$(artifact_path_for "${enrichment_write_capable_repo}" enrichment_only_lookup)"
assert_fails_with \
  "${enrichment_write_capable_repo}" \
  "Mismatched Phase 54.5 enrichment_only_lookup artifact field mutation_boundary.enrichment_only: expected [required] actual [optional]"

operator_state_mutation_repo="${workdir}/operator-state-mutation"
create_valid_repo "${operator_state_mutation_repo}"
perl -0pi -e 's/  authoritative_workflow_state_change: forbidden/  authoritative_workflow_state_change: allowed/' "$(artifact_path_for "${operator_state_mutation_repo}" operator_notification)"
assert_fails_with \
  "${operator_state_mutation_repo}" \
  "Mismatched Phase 54.5 operator_notification artifact field mutation_boundary.authoritative_workflow_state_change: expected [forbidden] actual [allowed]"

manual_bypass_repo="${workdir}/manual-bypass"
create_valid_repo "${manual_bypass_repo}"
perl -0pi -e 's/  aegisops_approval_bypass: forbidden/  aegisops_approval_bypass: allowed/' "$(artifact_path_for "${manual_bypass_repo}" manual_escalation_request)"
assert_fails_with \
  "${manual_bypass_repo}" \
  "Mismatched Phase 54.5 manual_escalation_request artifact field mutation_boundary.aegisops_approval_bypass: expected [forbidden] actual [allowed]"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Shuffle workflow success is AegisOps reconciliation truth." \
  >>"${workflow_truth_repo}/docs/deployment/shuffle-read-notify-template-contracts.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 54.5 Read/Notify template contract claim: Shuffle workflow success is AegisOps reconciliation truth"

controlled_write_repo="${workdir}/controlled-write"
create_valid_repo "${controlled_write_repo}"
printf '%s\n' "Phase 54.5 enables Controlled Write by default." \
  >>"${controlled_write_repo}/docs/deployment/shuffle-read-notify-template-contracts.md"
assert_fails_with \
  "${controlled_write_repo}" \
  "Forbidden Phase 54.5 Read/Notify template contract claim: Phase 54.5 enables Controlled Write by default"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder secrets are valid credentials." \
  >>"${placeholder_secret_repo}/docs/deployment/shuffle-read-notify-template-contracts.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 54.5 Read/Notify template contract claim: placeholder secrets accepted as valid credentials"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/shuffle-read-notify-template-contracts.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 54.5 Read/Notify template contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "Missing README Phase 54.5 Read/Notify template contracts link: [Phase 54.5 Read/Notify template contracts](docs/deployment/shuffle-read-notify-template-contracts.md)"

echo "Phase 54.5 Read/Notify template contract verifier tests passed."
