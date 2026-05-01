#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-51-5-competitive-gap-matrix.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' "# AegisOps" "See [Phase 51.5 competitive gap matrix](docs/phase-51-5-competitive-gap-matrix.md)." >"${target}/README.md"
  cp "${repo_root}/docs/phase-51-5-competitive-gap-matrix.md" \
    "${target}/docs/phase-51-5-competitive-gap-matrix.md"
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

remove_text_from_matrix() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-51-5-competitive-gap-matrix.md"
}

replace_text_in_matrix() {
  local target="$1"
  local old_text="$2"
  local new_text="$3"

  OLD_TEXT="${old_text}" NEW_TEXT="${new_text}" perl -0pi -e 's/\Q$ENV{OLD_TEXT}\E/$ENV{NEW_TEXT}/g' \
    "${target}/docs/phase-51-5-competitive-gap-matrix.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

alternate_date_repo="${workdir}/alternate-date"
create_valid_repo "${alternate_date_repo}"
replace_text_in_matrix \
  "${alternate_date_repo}" \
  "- **Date**: 2026-05-01" \
  "- **Date**: 2026-04-30"
assert_passes "${alternate_date_repo}"

invalid_date_repo="${workdir}/invalid-date"
create_valid_repo "${invalid_date_repo}"
replace_text_in_matrix \
  "${invalid_date_repo}" \
  "- **Date**: 2026-05-01" \
  "- **Date**: May 1, 2026"
assert_fails_with \
  "${invalid_date_repo}" \
  "Missing or invalid Phase 51.5 competitive gap matrix date line (- **Date**: YYYY-MM-DD)."

missing_matrix_repo="${workdir}/missing-matrix"
create_valid_repo "${missing_matrix_repo}"
rm "${missing_matrix_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${missing_matrix_repo}" \
  "Missing Phase 51.5 competitive gap matrix"

missing_wazuh_repo="${workdir}/missing-wazuh-comparison"
create_valid_repo "${missing_wazuh_repo}"
remove_text_from_matrix "${missing_wazuh_repo}" "| Standalone Wazuh operations |"
assert_fails_with \
  "${missing_wazuh_repo}" \
  "Missing Phase 51.5 competitive gap matrix statement: | Standalone Wazuh operations |"

missing_shuffle_repo="${workdir}/missing-shuffle-comparison"
create_valid_repo "${missing_shuffle_repo}"
remove_text_from_matrix "${missing_shuffle_repo}" "| Standalone Shuffle operations |"
assert_fails_with \
  "${missing_shuffle_repo}" \
  "Missing Phase 51.5 competitive gap matrix statement: | Standalone Shuffle operations |"

missing_manual_repo="${workdir}/missing-manual-comparison"
create_valid_repo "${missing_manual_repo}"
remove_text_from_matrix "${missing_manual_repo}" "| Manual SOC/ticket workflow |"
assert_fails_with \
  "${missing_manual_repo}" \
  "Missing Phase 51.5 competitive gap matrix statement: | Manual SOC/ticket workflow |"

missing_smb_siem_soar_repo="${workdir}/missing-smb-siem-soar-comparison"
create_valid_repo "${missing_smb_siem_soar_repo}"
remove_text_from_matrix "${missing_smb_siem_soar_repo}" "| Common SMB SIEM/SOAR expectations |"
assert_fails_with \
  "${missing_smb_siem_soar_repo}" \
  "Missing Phase 51.5 competitive gap matrix statement: | Common SMB SIEM/SOAR expectations |"

missing_p0_phase_map_repo="${workdir}/missing-p0-phase-map"
create_valid_repo "${missing_p0_phase_map_repo}"
remove_text_from_matrix \
  "${missing_p0_phase_map_repo}" \
  "| P0 | Wazuh signal admission from replacement profile | Current state does not yet prove the replacement operating experience for Wazuh-backed SMB signal intake across the intended profile. | Phase 54 Wazuh signal intake |"
assert_fails_with \
  "${missing_p0_phase_map_repo}" \
  "Missing Phase 51.5 competitive gap matrix statement: | P0 | Wazuh signal admission from replacement profile |"

enterprise_parity_repo="${workdir}/enterprise-parity"
create_valid_repo "${enterprise_parity_repo}"
printf '%s\n' "AegisOps provides full enterprise SIEM parity." \
  >>"${enterprise_parity_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${enterprise_parity_repo}" \
  "Forbidden Phase 51.5 competitive gap matrix claim: AegisOps provides full enterprise SIEM parity."

enterprise_reworded_repo="${workdir}/enterprise-reworded"
create_valid_repo "${enterprise_reworded_repo}"
printf '%s\n' "AegisOps fully replaces enterprise SOAR." \
  >>"${enterprise_reworded_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${enterprise_reworded_repo}" \
  "Forbidden Phase 51.5 competitive gap matrix claim: AegisOps fully replaces enterprise SOAR."

bullet_wazuh_replacement_repo="${workdir}/bullet-wazuh-replacement"
create_valid_repo "${bullet_wazuh_replacement_repo}"
printf '%s\n' "- AegisOps replaces every Wazuh detector family" \
  >>"${bullet_wazuh_replacement_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${bullet_wazuh_replacement_repo}" \
  "Forbidden Phase 51.5 competitive gap matrix claim matched: (^|[^[:alnum:]_])aegisops[^.]*replaces[[:space:]]+every[[:space:]]+wazuh[[:space:]]+detector"

list_shuffle_replacement_repo="${workdir}/list-shuffle-replacement"
create_valid_repo "${list_shuffle_replacement_repo}"
printf '%s\n' "1. AegisOps replaces every Shuffle integration catalog" \
  >>"${list_shuffle_replacement_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${list_shuffle_replacement_repo}" \
  "Forbidden Phase 51.5 competitive gap matrix claim matched: (^|[^[:alnum:]_])aegisops[^.]*replaces[[:space:]]+every[[:space:]]+shuffle[[:space:]]+integration"

wazuh_authority_repo="${workdir}/wazuh-authority"
create_valid_repo "${wazuh_authority_repo}"
printf '%s\n' "Wazuh is authoritative for AegisOps records." \
  >>"${wazuh_authority_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${wazuh_authority_repo}" \
  "Forbidden Phase 51.5 competitive gap matrix claim: Wazuh is authoritative for AegisOps records."

shuffle_authority_reworded_repo="${workdir}/shuffle-authority-reworded"
create_valid_repo "${shuffle_authority_reworded_repo}"
printf '%s\n' "Shuffle may be authoritative for AegisOps records." \
  >>"${shuffle_authority_reworded_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${shuffle_authority_reworded_repo}" \
  "Forbidden Phase 51.5 competitive gap matrix claim matched: (^|[^[:alnum:]_])shuffle[[:space:]]+(is|are|becomes|become|remains|may[[:space:]]+be|can[[:space:]]+be|serves[[:space:]]+as|acts[[:space:]]+as)[[:space:]]+authoritative[[:space:]]+for[[:space:]]+aegisops"

future_gap_claim_repo="${workdir}/future-gap-claim"
create_valid_repo "${future_gap_claim_repo}"
replace_text_in_matrix \
  "${future_gap_claim_repo}" \
  "AegisOps current state is pre-GA and must not be described as already closing Beta, RC, or GA gaps." \
  "AegisOps current state already closes Beta, RC, and GA gaps."
assert_fails_with \
  "${future_gap_claim_repo}" \
  "Missing Phase 51.5 competitive gap matrix statement: AegisOps current state is pre-GA"

workstation_path_repo="${workdir}/workstation-local-path"
create_valid_repo "${workstation_path_repo}"
workstation_path="$(printf '/%s/%s/gap-matrix.md' "Users" "example")"
printf '%s%s%s\n' "Matrix path:" "file:" "//${workstation_path}" \
  >>"${workstation_path_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 51.5 competitive gap matrix: workstation-local absolute path detected"

web_url_home_repo="${workdir}/web-url-home-path"
create_valid_repo "${web_url_home_repo}"
printf '%s\n' "Reference URL: https://docs.example.invalid/home/aegisops/gap-matrix" \
  >>"${web_url_home_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_passes "${web_url_home_repo}"

standalone_unix_home_repo="${workdir}/standalone-unix-home-path"
create_valid_repo "${standalone_unix_home_repo}"
standalone_unix_home_path="$(printf '/%s/%s/gap-matrix.md' "home" "example")"
printf '%s\n' "Matrix path: ${standalone_unix_home_path}" \
  >>"${standalone_unix_home_repo}/docs/phase-51-5-competitive-gap-matrix.md"
assert_fails_with \
  "${standalone_unix_home_repo}" \
  "Forbidden Phase 51.5 competitive gap matrix: workstation-local absolute path detected"

raw_readme_path_repo="${workdir}/raw-readme-path"
create_valid_repo "${raw_readme_path_repo}"
printf '%s\n' "# AegisOps" "See docs/phase-51-5-competitive-gap-matrix.md." >"${raw_readme_path_repo}/README.md"
assert_fails_with \
  "${raw_readme_path_repo}" \
  "README must link the Phase 51.5 competitive gap matrix."

echo "Phase 51.5 competitive gap matrix verifier tests passed."
