#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-51-4-smb-personas-jtbd.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' "# AegisOps" "See [Phase 51.4 SMB personas](docs/phase-51-4-smb-personas-jobs-to-be-done.md)." >"${target}/README.md"
  cp "${repo_root}/docs/phase-51-4-smb-personas-jobs-to-be-done.md" \
    "${target}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
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

remove_text_from_doc() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
}

replace_text_in_doc() {
  local target="$1"
  local old_text="$2"
  local new_text="$3"

  OLD_TEXT="${old_text}" NEW_TEXT="${new_text}" perl -0pi -e 's/\Q$ENV{OLD_TEXT}\E/$ENV{NEW_TEXT}/g' \
    "${target}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 51.4 SMB personas and jobs-to-be-done document"

missing_support_repo="${workdir}/missing-support-collaborator"
create_valid_repo "${missing_support_repo}"
replace_text_in_doc \
  "${missing_support_repo}" \
  "### 3.5 Bounded External Support Collaborator" \
  "### 3.5 Support Notes"
assert_fails_with \
  "${missing_support_repo}" \
  "Missing Phase 51.4 personas heading: ### 3.5 Bounded External Support Collaborator"

missing_authority_limits_repo="${workdir}/missing-support-authority-limits"
create_valid_repo "${missing_authority_limits_repo}"
remove_text_from_doc \
  "${missing_authority_limits_repo}" \
  "| Bounded External Support Collaborator | Help diagnose platform or product issues without becoming an operator, approver, administrator, or source of truth. | Review redacted support bundles, ask clarifying questions, suggest documented remediation steps, and identify product defects or known limitations for the customer-owned team to accept or reject. | Fear receiving private production data, being expected to provide 24x7 coverage, being blamed for customer decisions, or accidentally becoming an authority path through informal advice. | Needs redacted bundles, explicit customer owner, limitation owner, reproduction steps, environment class, retained evidence references, and a written boundary for what support may not do. | May provide advisory diagnosis from redacted evidence and documented product knowledge only. Must not access customer-private production systems directly, approve actions, execute actions, mutate AegisOps records, operate Wazuh or Shuffle, close cases, or make AI, tickets, or support notes authoritative. | Phase 63 support bundle, Phase 64 known limitations ownership, Phase 66 RC supportability evidence, Phase 67 GA support-readiness evidence. |"
assert_fails_with \
  "${missing_authority_limits_repo}" \
  "Missing Phase 51.4 personas statement: | Bounded External Support Collaborator |"

external_support_authority_repo="${workdir}/external-support-authority"
create_valid_repo "${external_support_authority_repo}"
printf '%s\n' "External support may approve AegisOps actions." \
  >>"${external_support_authority_repo}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
assert_fails_with \
  "${external_support_authority_repo}" \
  "Forbidden Phase 51.4 personas authority or staffing claim: External support may approve AegisOps actions."

ai_authority_repo="${workdir}/ai-authority"
create_valid_repo "${ai_authority_repo}"
printf '%s\n' "AI is authoritative for AegisOps records." \
  >>"${ai_authority_repo}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
assert_fails_with \
  "${ai_authority_repo}" \
  "Forbidden Phase 51.4 personas authority or staffing claim: AI is authoritative for AegisOps records."

staffing_drift_repo="${workdir}/staffing-drift"
create_valid_repo "${staffing_drift_repo}"
printf '%s\n' "24x7 staffed SOC is the default operating model." \
  >>"${staffing_drift_repo}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
assert_fails_with \
  "${staffing_drift_repo}" \
  "Forbidden Phase 51.4 personas authority or staffing claim: 24x7 staffed SOC is the default operating model."

workstation_path_repo="${workdir}/workstation-local-path"
create_valid_repo "${workstation_path_repo}"
workstation_path="$(printf '/%s/%s/support-bundle.md' "Users" "example")"
printf '%s\n' "Support bundle path:file://${workstation_path}" \
  >>"${workstation_path_repo}/docs/phase-51-4-smb-personas-jobs-to-be-done.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 51.4 personas document: workstation-local absolute path detected"

raw_readme_path_repo="${workdir}/raw-readme-path"
create_valid_repo "${raw_readme_path_repo}"
printf '%s\n' "# AegisOps" "See docs/phase-51-4-smb-personas-jobs-to-be-done.md." >"${raw_readme_path_repo}/README.md"
assert_fails_with \
  "${raw_readme_path_repo}" \
  "README must link the Phase 51.4 SMB personas and jobs-to-be-done document."

echo "Phase 51.4 SMB personas and jobs-to-be-done verifier tests passed."
