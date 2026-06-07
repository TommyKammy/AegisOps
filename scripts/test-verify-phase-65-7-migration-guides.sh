#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-7-migration-guides.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

copy_repo_path() {
  local target="$1"
  local relative_path="$2"

  mkdir -p "${target}/$(dirname "${relative_path}")"
  cp -p "${repo_root}/${relative_path}" "${target}/${relative_path}"
}

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/migration/phase-65-7-standalone-wazuh-migration-guide.md"
  copy_repo_path "${target}" "docs/migration/phase-65-7-standalone-shuffle-migration-guide.md"
  copy_repo_path "${target}" "docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md"
  copy_repo_path "${target}" "scripts/verify-phase-65-7-migration-guides.sh"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    cat "${fail_stdout}" >&2
    exit 1
  fi

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_wazuh_repo="${workdir}/missing-wazuh"
create_valid_repo "${missing_wazuh_repo}"
rm "${missing_wazuh_repo}/docs/migration/phase-65-7-standalone-wazuh-migration-guide.md"
assert_fails_with "${missing_wazuh_repo}" "Missing Phase 65.7 standalone Wazuh migration guide"

missing_shuffle_repo="${workdir}/missing-shuffle"
create_valid_repo "${missing_shuffle_repo}"
rm "${missing_shuffle_repo}/docs/migration/phase-65-7-standalone-shuffle-migration-guide.md"
assert_fails_with "${missing_shuffle_repo}" "Missing Phase 65.7 standalone Shuffle migration guide"

missing_manual_repo="${workdir}/missing-manual"
create_valid_repo "${missing_manual_repo}"
rm "${missing_manual_repo}/docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md"
assert_fails_with "${missing_manual_repo}" "Missing Phase 65.7 manual SOC and ticket workflow migration guide"

missing_section_repo="${workdir}/missing-section"
create_valid_repo "${missing_section_repo}"
perl -0pi -e 's/^## 4\. Evidence Mapping\n/## 4. Removed\n/m' "${missing_section_repo}/docs/migration/phase-65-7-standalone-wazuh-migration-guide.md"
assert_fails_with "${missing_section_repo}" "Missing Phase 65.7 standalone Wazuh migration guide required section: ## 4. Evidence Mapping"

missing_readme_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 65\.7 standalone Wazuh migration guide\]\(docs\/migration\/phase-65-7-standalone-wazuh-migration-guide\.md\)[^\n]*\n//m' "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README Phase 65.7 migration guide link"

source_truth_repo="${workdir}/source-truth"
create_valid_repo "${source_truth_repo}"
printf '%s\n' "Source-native truth is authoritative for AegisOps records." >>"${source_truth_repo}/docs/migration/phase-65-7-standalone-wazuh-migration-guide.md"
assert_fails_with "${source_truth_repo}" "Forbidden Phase 65.7 migration guide claim: Source-native truth is authoritative for AegisOps records."

wazuh_truth_repo="${workdir}/wazuh-truth"
create_valid_repo "${wazuh_truth_repo}"
printf '%s\n' "Wazuh alerts become AegisOps alert truth." >>"${wazuh_truth_repo}/docs/migration/phase-65-7-standalone-wazuh-migration-guide.md"
assert_fails_with "${wazuh_truth_repo}" "Forbidden Phase 65.7 migration guide claim: Wazuh alerts become AegisOps alert truth."

shuffle_truth_repo="${workdir}/shuffle-truth"
create_valid_repo "${shuffle_truth_repo}"
printf '%s\n' "Shuffle workflow success becomes AegisOps execution truth." >>"${shuffle_truth_repo}/docs/migration/phase-65-7-standalone-shuffle-migration-guide.md"
assert_fails_with "${shuffle_truth_repo}" "Forbidden Phase 65.7 migration guide claim: Shuffle workflow success becomes AegisOps execution truth."

ticket_truth_repo="${workdir}/ticket-truth"
create_valid_repo "${ticket_truth_repo}"
printf '%s\n' "Ticket status is AegisOps case truth." >>"${ticket_truth_repo}/docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md"
assert_fails_with "${ticket_truth_repo}" "Forbidden Phase 65.7 migration guide claim: Ticket status is AegisOps case truth."

arbitrary_import_repo="${workdir}/arbitrary-import"
create_valid_repo "${arbitrary_import_repo}"
printf '%s\n' "AegisOps imports arbitrary production customer data." >>"${arbitrary_import_repo}/docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md"
assert_fails_with "${arbitrary_import_repo}" "Forbidden Phase 65.7 migration guide claim: AegisOps imports arbitrary production customer data."

siem_soar_parity_repo="${workdir}/siem-soar-parity"
create_valid_repo "${siem_soar_parity_repo}"
printf '%s\n' "AegisOps provides broad SIEM/SOAR parity." >>"${siem_soar_parity_repo}/docs/migration/phase-65-7-standalone-shuffle-migration-guide.md"
assert_fails_with "${siem_soar_parity_repo}" "Forbidden Phase 65.7 migration guide claim: AegisOps provides broad SIEM/SOAR parity."

rc_overclaim_repo="${workdir}/rc-overclaim"
create_valid_repo "${rc_overclaim_repo}"
printf '%s\n' "Phase 65.7 proves RC readiness." >>"${rc_overclaim_repo}/docs/migration/phase-65-7-standalone-wazuh-migration-guide.md"
assert_fails_with "${rc_overclaim_repo}" "Forbidden Phase 65.7 migration guide claim: Phase 65.7 proves RC readiness."

ga_overclaim_repo="${workdir}/ga-overclaim"
create_valid_repo "${ga_overclaim_repo}"
printf '%s\n' "Phase 65.7 proves GA readiness." >>"${ga_overclaim_repo}/docs/migration/phase-65-7-standalone-shuffle-migration-guide.md"
assert_fails_with "${ga_overclaim_repo}" "Forbidden Phase 65.7 migration guide claim: Phase 65.7 proves GA readiness."

commercial_overclaim_repo="${workdir}/commercial-overclaim"
create_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "AegisOps is commercially replacement ready." >>"${commercial_overclaim_repo}/docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md"
assert_fails_with "${commercial_overclaim_repo}" "Forbidden Phase 65.7 migration guide claim: AegisOps is commercially replacement ready."

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
printf '%s\n' "api_key = abc123" >>"${secret_repo}/docs/migration/phase-65-7-standalone-shuffle-migration-guide.md"
assert_fails_with "${secret_repo}" "Forbidden Phase 65.7 migration guide production secret material"

customer_private_repo="${workdir}/customer-private"
create_valid_repo "${customer_private_repo}"
printf '%s\n' "The migration guide includes customer-private ticket data." >>"${customer_private_repo}/docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md"
assert_fails_with "${customer_private_repo}" "Forbidden Phase 65.7 migration guide customer-private data"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
workstation_path="/""Users/example/migration-notes.md"
printf '%s\n' "${workstation_path}" >>"${workstation_path_repo}/docs/migration/phase-65-7-standalone-wazuh-migration-guide.md"
assert_fails_with "${workstation_path_repo}" "Forbidden Phase 65.7 migration guide workstation-local absolute path"

echo "Phase 65.7 migration guide verifier self-test passed"
