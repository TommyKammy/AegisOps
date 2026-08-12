#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/adr"
  printf '%s\n' "# AegisOps" "See [Phase 51.3 gate contract](docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "${target}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  cp "${repo_root}/docs/adr/0020-phase-67-ga-prerequisite-boundary.md" \
    "${target}/docs/adr/0020-phase-67-ga-prerequisite-boundary.md"
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

  perl -0pi -e "s#\\Q${text}\\E##" \
    "${target}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
}

replace_text_in_contract() {
  local target="$1"
  local old_text="$2"
  local new_text="$3"

  perl -0pi -e "s#\\Q${old_text}\\E#${new_text}#" \
    "${target}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
}

remove_text_from_adr() {
  local target="$1"
  local text="$2"

  perl -0pi -e "s#\\Q${text}\\E##" \
    "${target}/docs/adr/0020-phase-67-ga-prerequisite-boundary.md"
}

replace_text_in_adr() {
  local target="$1"
  local old_text="$2"
  local new_text="$3"

  perl -0pi -e "s#\\Q${old_text}\\E#${new_text}#" \
    "${target}/docs/adr/0020-phase-67-ga-prerequisite-boundary.md"
}

insert_after_heading() {
  local target="$1"
  local heading="$2"
  local text="$3"
  local source="${target}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  local updated="${target}/contract.updated"

  awk -v heading="${heading}" -v text="${text}" '{
    print
    if ($0 == heading) {
      print ""
      print text
    }
  }' "${source}" >"${updated}"
  mv "${updated}" "${source}"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_adr_repo="${workdir}/missing-adr"
create_valid_repo "${missing_adr_repo}"
rm "${missing_adr_repo}/docs/adr/0020-phase-67-ga-prerequisite-boundary.md"
assert_fails_with \
  "${missing_adr_repo}" \
  "Missing proposed Phase 67 GA-prerequisite ADR"

accepted_adr_repo="${workdir}/accepted-adr-without-approval"
create_valid_repo "${accepted_adr_repo}"
replace_text_in_adr \
  "${accepted_adr_repo}" \
  "- **Status**: Proposed" \
  "- **Status**: Accepted"
assert_fails_with \
  "${accepted_adr_repo}" \
  "Missing proposed ADR 0020 line: - **Status**: Proposed"

duplicate_adr_status_repo="${workdir}/duplicate-adr-status"
create_valid_repo "${duplicate_adr_status_repo}"
printf '%s\n' '- **Status**: Accepted' \
  >>"${duplicate_adr_status_repo}/docs/adr/0020-phase-67-ga-prerequisite-boundary.md"
assert_fails_with \
  "${duplicate_adr_status_repo}" \
  "Expected exactly one proposed ADR 0020 Status field; found 2"

duplicate_adr_approval_repo="${workdir}/duplicate-adr-approval"
create_valid_repo "${duplicate_adr_approval_repo}"
printf '%s\n' '- **Approved By**: Example Maintainer' \
  >>"${duplicate_adr_approval_repo}/docs/adr/0020-phase-67-ga-prerequisite-boundary.md"
assert_fails_with \
  "${duplicate_adr_approval_repo}" \
  "Expected exactly one proposed ADR 0020 Approved By field; found 2"

drifted_adr_decision_repo="${workdir}/drifted-adr-decision"
create_valid_repo "${drifted_adr_decision_repo}"
replace_text_in_adr \
  "${drifted_adr_decision_repo}" \
  "Phase 67 performs bounded GA-prerequisite validation." \
  "Phase 67 remains GA."
assert_fails_with \
  "${drifted_adr_decision_repo}" \
  "Missing proposed ADR 0020 decision: Phase 67 performs bounded GA-prerequisite validation."

for approval_line in \
  "- **Proposed By**: Codex for PR #1424" \
  "- **Reviewed By**: Pending" \
  "- **Approved By**: Pending" \
  "- **Approval Date**: Pending"; do
  approval_slug="$(printf '%s' "${approval_line}" | tr '[:upper:] ' '[:lower:]-' | tr -cd '[:alnum:]-')"
  missing_approval_repo="${workdir}/missing-${approval_slug}"
  create_valid_repo "${missing_approval_repo}"
  remove_text_from_adr "${missing_approval_repo}" "${approval_line}"
  assert_fails_with \
    "${missing_approval_repo}" \
    "Missing proposed ADR 0020 line: ${approval_line}"
done

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 51.3 pilot beta RC GA gate contract"

modified_heading_repo="${workdir}/modified-heading"
create_valid_repo "${modified_heading_repo}"
replace_text_in_contract \
  "${modified_heading_repo}" \
  "# Phase 51.3 Pilot, Beta, RC, and GA Gate Contract" \
  "# Phase 51.3 Pilot, Beta, RC, and GA Gate Contract (Draft)"
assert_fails_with \
  "${modified_heading_repo}" \
  "Missing Phase 51.3 gate contract heading: # Phase 51.3 Pilot, Beta, RC, and GA Gate Contract"

modified_required_statement_repo="${workdir}/modified-required-statement"
create_valid_repo "${modified_required_statement_repo}"
replace_text_in_contract \
  "${modified_required_statement_repo}" \
  "Phase 66 is RC. Phase 67 performs bounded GA-prerequisite validation and does not accept GA." \
  "Phase 66 is RC. Phase 67 prerequisite validation is still under review."
assert_fails_with \
  "${modified_required_statement_repo}" \
  "Missing Phase 51.3 gate contract statement: Phase 66 is RC. Phase 67 performs bounded GA-prerequisite validation and does not accept GA."

missing_rc_ga_repo="${workdir}/missing-rc-ga-distinction"
create_valid_repo "${missing_rc_ga_repo}"
remove_text_from_contract "${missing_rc_ga_repo}" \
  "RC is not GA. RC allows a release-candidate replacement claim only for the explicitly reviewed SMB operating scope and only while the remaining GA evidence is tracked as a named prerequisite."
assert_fails_with \
  "${missing_rc_ga_repo}" \
  "Missing Phase 51.3 gate contract statement: RC is not GA."

missing_design_partner_repo="${workdir}/missing-design-partner-evidence"
create_valid_repo "${missing_design_partner_repo}"
remove_text_from_contract "${missing_design_partner_repo}" \
  "GA must reject broad GA overclaim before real-user or design-partner evidence exists."
assert_fails_with \
  "${missing_design_partner_repo}" \
  "Missing Phase 51.3 gate contract statement: GA must reject broad GA overclaim before real-user or design-partner evidence exists."

missing_independent_approval_repo="${workdir}/missing-independent-approval"
create_valid_repo "${missing_independent_approval_repo}"
remove_text_from_contract "${missing_independent_approval_repo}" \
  "GA acceptance requires a separately scoped gate decision backed by current-revision launch-scope evidence and independent human approval after Phase 67 prerequisite evidence is complete."
assert_fails_with \
  "${missing_independent_approval_repo}" \
  "Missing Phase 51.3 gate contract statement: GA acceptance requires a separately scoped gate decision backed by current-revision launch-scope evidence and independent human approval"

missing_phase_66_repo="${workdir}/missing-phase-66-rc"
create_valid_repo "${missing_phase_66_repo}"
remove_text_from_contract "${missing_phase_66_repo}" "Phase 66 is RC. Phase 67 performs bounded GA-prerequisite validation and does not accept GA."
assert_fails_with \
  "${missing_phase_66_repo}" \
  "Missing Phase 51.3 gate contract statement: Phase 66 is RC. Phase 67 performs bounded GA-prerequisite validation and does not accept GA."

direct_phase67_ga_claims=(
  "Phase 67 is GA"
  "Phase 67 is GA."
  "Phase 67 remains GA."
  "Phase 67 becomes GA"
  "Phase 67 stays GA!"
  "Phase 67 equals GA"
  "Phase 67 stays the GA gate"
  "Phase-67 equals the GA"
  "Phase 67: becomes the GA gate."
  "Phase 67 is GA-gate."
  "Phase 67 accepts GA."
  "Phase 67 materializes the GA gate."
  "| Direct mapping | Phase 67 is GA |"
  "| Phase 67 | becomes | the GA gate |"
  "This does not claim GA, but Phase 67 is GA."
  "This release is not a drill: Phase 67 remains GA."
)

direct_claim_index=0
for direct_claim in "${direct_phase67_ga_claims[@]}"; do
  direct_claim_index=$((direct_claim_index + 1))
  direct_claim_repo="${workdir}/phase67-direct-ga-claim-${direct_claim_index}"
  create_valid_repo "${direct_claim_repo}"
  insert_after_heading "${direct_claim_repo}" "## 7. GA Gate" "${direct_claim}"
  assert_fails_with \
    "${direct_claim_repo}" \
    "Forbidden Phase 51.3 gate contract direct GA claim: ${direct_claim}"
done

negated_phase67_ga_claim_repo="${workdir}/negated-phase67-ga-claims"
create_valid_repo "${negated_phase67_ga_claim_repo}"
printf '%s\n' \
  'Phase 67 is not GA.' \
  'Phase 67 does not become GA.' \
  'Phase 67 is GA-prerequisite validation only.' \
  'Phase 67 remains GA-prerequisite validation only.' \
  'Phase 67 is GA prerequisite validation only.' \
  'Phase 67 becomes the GA readiness boundary.' \
  'Phase 67 remains GA evidence only.' \
  'The verifier rejects the claim "Phase 67 is GA".' \
  '"Phase 67 is GA" is forbidden.' \
  'Forbidden wording: Phase 67 is GA.' \
  'These are not claims: Phase 67 remains GA.' \
  >>"${negated_phase67_ga_claim_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_passes "${negated_phase67_ga_claim_repo}"

phase67_completion_overclaim_repo="${workdir}/phase67-completion-overclaim"
create_valid_repo "${phase67_completion_overclaim_repo}"
insert_after_heading "${phase67_completion_overclaim_repo}" "## 7. GA Gate" "Completing Phase 67 accepts GA."
assert_fails_with \
  "${phase67_completion_overclaim_repo}" \
  "Forbidden Phase 51.3 gate contract direct GA claim: Completing Phase 67 accepts GA."

authority_drift_repo="${workdir}/authority-drift"
create_valid_repo "${authority_drift_repo}"
printf '%s\n' "Wazuh is authoritative for gate acceptance." \
  >>"${authority_drift_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with \
  "${authority_drift_repo}" \
  "Forbidden Phase 51.3 gate contract claim: Wazuh is authoritative for gate acceptance"

ga_overclaim_repo="${workdir}/ga-overclaim"
create_valid_repo "${ga_overclaim_repo}"
insert_after_heading "${ga_overclaim_repo}" "## 6. RC Gate" "- Phase 66 is GA."
assert_fails_with \
  "${ga_overclaim_repo}" \
  "Forbidden Phase 51.3 gate contract claim: Phase 66 is GA"

workstation_path_repo="${workdir}/workstation-local-path"
create_valid_repo "${workstation_path_repo}"
workstation_path="$(printf '/%s/%s/evidence.md' "Users" "example")"
printf '%s\n' "Evidence path:file://${workstation_path}" \
  >>"${workstation_path_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 51.3 gate contract: workstation-local absolute path detected"

windows_slash_path_repo="${workdir}/windows-slash-path"
create_valid_repo "${windows_slash_path_repo}"
windows_slash_path="$(printf 'C:/%s/%s/evidence.md' "Users" "example")"
printf '%s\n' "Evidence path:file://${windows_slash_path}" \
  >>"${windows_slash_path_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with \
  "${windows_slash_path_repo}" \
  "Forbidden Phase 51.3 gate contract: workstation-local absolute path detected"

raw_readme_path_repo="${workdir}/raw-readme-path"
create_valid_repo "${raw_readme_path_repo}"
printf '%s\n' "# AegisOps" "See docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md." >"${raw_readme_path_repo}/README.md"
assert_fails_with \
  "${raw_readme_path_repo}" \
  "README must link the Phase 51.3 pilot beta RC GA gate contract."

inline_code_readme_link_repo="${workdir}/inline-code-readme-link"
create_valid_repo "${inline_code_readme_link_repo}"
printf '%s\n' \
  "# AegisOps" \
  'Mentioned only as code: `[Phase 51.3 gate contract](docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md)`.' \
  >"${inline_code_readme_link_repo}/README.md"
assert_fails_with \
  "${inline_code_readme_link_repo}" \
  "README must link the Phase 51.3 pilot beta RC GA gate contract."

fenced_code_readme_link_repo="${workdir}/fenced-code-readme-link"
create_valid_repo "${fenced_code_readme_link_repo}"
printf '%s\n' \
  "# AegisOps" \
  '```markdown' \
  '[Phase 51.3 gate contract](docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md)' \
  '```' \
  >"${fenced_code_readme_link_repo}/README.md"
assert_fails_with \
  "${fenced_code_readme_link_repo}" \
  "README must link the Phase 51.3 pilot beta RC GA gate contract."

tilde_fenced_code_readme_link_repo="${workdir}/tilde-fenced-code-readme-link"
create_valid_repo "${tilde_fenced_code_readme_link_repo}"
printf '%s\n' \
  "# AegisOps" \
  '~~~markdown' \
  '[Phase 51.3 gate contract](docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md)' \
  '~~~' \
  >"${tilde_fenced_code_readme_link_repo}/README.md"
assert_fails_with \
  "${tilde_fenced_code_readme_link_repo}" \
  "README must link the Phase 51.3 pilot beta RC GA gate contract."

echo "Phase 51.3 pilot beta RC GA gate contract verifier tests passed."
