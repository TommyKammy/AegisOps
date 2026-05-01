#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-2-smb-single-node-profile-model.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' "# AegisOps" "See [Phase 52.2 SMB single-node profile model](docs/phase-52-2-smb-single-node-profile-model.md)." >"${target}/README.md"
  cp "${repo_root}/docs/phase-52-2-smb-single-node-profile-model.md" \
    "${target}/docs/phase-52-2-smb-single-node-profile-model.md"
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
    "${target}/docs/phase-52-2-smb-single-node-profile-model.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 52.2 SMB single-node profile model"

missing_wazuh_repo="${workdir}/missing-wazuh"
create_valid_repo "${missing_wazuh_repo}"
remove_text_from_contract "${missing_wazuh_repo}" \
  "| Wazuh | \`deferred\` | \`service_name\`, \`manager_url\`, \`ingest_route\`, \`ingest_secret_ref\`, \`alert_contract\`, \`source_binding\` | Wazuh-facing intake placeholders and binding metadata for later reviewed Wazuh product-profile generation. | Missing Wazuh section fails validation; Wazuh status, rule, manager, decoder, alert, or timestamp state must not become AegisOps source, workflow, release, or gate truth without explicit AegisOps admission and linkage. |"
assert_fails_with \
  "${missing_wazuh_repo}" \
  "Missing complete Phase 52.2 profile section row: Wazuh"

missing_shuffle_repo="${workdir}/missing-shuffle"
create_valid_repo "${missing_shuffle_repo}"
remove_text_from_contract "${missing_shuffle_repo}" \
  "| Shuffle | \`deferred\` | \`service_name\`, \`api_url\`, \`credential_ref\`, \`workflow_catalog_ref\`, \`callback_route\`, \`delegation_scope\` | Shuffle delegation placeholders and callback binding metadata for later reviewed Shuffle product-profile generation. | Missing Shuffle section fails validation; Shuffle workflow success, failure, retry, payload, or callback state must not become AegisOps execution, reconciliation, release, gate, or closeout truth without AegisOps approval, action intent, receipt, and reconciliation records. |"
assert_fails_with \
  "${missing_shuffle_repo}" \
  "Missing complete Phase 52.2 profile section row: Shuffle"

missing_mode_repo="${workdir}/missing-mode"
create_valid_repo "${missing_mode_repo}"
perl -0pi -e 's/\| Proxy \| `required` \|/\| Proxy \|  \|/g' \
  "${missing_mode_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${missing_mode_repo}" \
  "Missing complete Phase 52.2 profile section row: Proxy"

wrong_mode_repo="${workdir}/wrong-mode"
create_valid_repo "${wrong_mode_repo}"
perl -0pi -e 's/\| Proxy \| `required` \|/\| Proxy \| `deferred` \|/g' \
  "${wrong_mode_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${wrong_mode_repo}" \
  "Missing complete Phase 52.2 profile section row: Proxy"

missing_field_repo="${workdir}/missing-authority-field"
create_valid_repo "${missing_field_repo}"
remove_text_from_contract "${missing_field_repo}" \
  "- \`authority_boundary\`: the explicit statement that the section remains setup input or subordinate context and cannot become authoritative AegisOps truth."
assert_fails_with \
  "${missing_field_repo}" \
  "Missing Phase 52.2 SMB single-node profile model statement: - \`authority_boundary\`:"

missing_phase51_citation_repo="${workdir}/missing-phase51-citation"
create_valid_repo "${missing_phase51_citation_repo}"
remove_text_from_contract "${missing_phase51_citation_repo}" \
  "This profile model cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
assert_fails_with \
  "${missing_phase51_citation_repo}" \
  "Missing Phase 52.2 SMB single-node profile model statement: This profile model cites the Phase 51.6 authority-boundary negative-test policy"

generated_truth_repo="${workdir}/generated-truth"
create_valid_repo "${generated_truth_repo}"
printf '%s\n' "Generated config is production truth." \
  >>"${generated_truth_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${generated_truth_repo}" \
  "Forbidden Phase 52.2 SMB single-node profile model claim: Generated config is production truth"

generated_truth_variant_repo="${workdir}/generated-truth-variant"
create_valid_repo "${generated_truth_variant_repo}"
printf '%s\n' "- generated config is production truth." \
  >>"${generated_truth_variant_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${generated_truth_variant_repo}" \
  "Forbidden Phase 52.2 SMB single-node profile model claim: Generated config is production truth"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Generated config is workflow truth." \
  >>"${workflow_truth_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 52.2 SMB single-node profile model claim: Generated config is workflow truth"

placeholder_secret_repo="${workdir}/placeholder-secret"
create_valid_repo "${placeholder_secret_repo}"
printf '%s\n' "Placeholder secrets are valid credentials." \
  >>"${placeholder_secret_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${placeholder_secret_repo}" \
  "Forbidden Phase 52.2 SMB single-node profile model claim: Placeholder secrets are valid credentials"

placeholder_secret_variant_repo="${workdir}/placeholder-secret-variant"
create_valid_repo "${placeholder_secret_variant_repo}"
printf '%s\n' "placeholder secret can be trusted production credentials." \
  >>"${placeholder_secret_variant_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${placeholder_secret_variant_repo}" \
  "Forbidden Phase 52.2 SMB single-node profile model claim: placeholder secrets accepted as valid credentials"

placeholder_secret_bullet_repo="${workdir}/placeholder-secret-bullet"
create_valid_repo "${placeholder_secret_bullet_repo}"
printf '%s\n' "- Placeholder secrets may be accepted." \
  >>"${placeholder_secret_bullet_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${placeholder_secret_bullet_repo}" \
  "Forbidden Phase 52.2 SMB single-node profile model claim: placeholder secrets accepted as valid credentials"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.2 SMB single-node profile model: workstation-local absolute path detected"

file_uri_path_repo="${workdir}/file-uri-path"
create_valid_repo "${file_uri_path_repo}"
printf 'Use file:///%s/aegisops for setup.\n' "tmp" \
  >>"${file_uri_path_repo}/docs/phase-52-2-smb-single-node-profile-model.md"
assert_fails_with \
  "${file_uri_path_repo}" \
  "Forbidden Phase 52.2 SMB single-node profile model: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 52.2 SMB single-node profile model."

echo "Phase 52.2 SMB single-node profile model verifier tests passed."
