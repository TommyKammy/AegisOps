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

  mkdir -p "${target}/docs"
  printf '%s\n' "# AegisOps" "See docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md." >"${target}/README.md"
  cp "${repo_root}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "${target}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
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

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 51.3 pilot beta RC GA gate contract"

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

missing_phase_66_repo="${workdir}/missing-phase-66-rc"
create_valid_repo "${missing_phase_66_repo}"
remove_text_from_contract "${missing_phase_66_repo}" "Phase 66 is RC. Phase 67 is GA."
assert_fails_with \
  "${missing_phase_66_repo}" \
  "Missing Phase 51.3 gate contract statement: Phase 66 is RC. Phase 67 is GA."

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
printf '%s\n' "Evidence path: ${workstation_path}" \
  >>"${workstation_path_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 51.3 gate contract: workstation-local absolute path detected"

echo "Phase 51.3 pilot beta RC GA gate contract verifier tests passed."
