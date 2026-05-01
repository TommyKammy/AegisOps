#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-9-first-user-stack-docs.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment"
  printf '%s\n' "# AegisOps" "See [Phase 52.9 first-user stack docs](docs/deployment/first-user-stack.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/first-user-stack.md" \
    "${target}/docs/deployment/first-user-stack.md"
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
    "${target}/docs/deployment/first-user-stack.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/deployment/first-user-stack.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 52.9 first-user stack docs"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 52.9 first-user stack docs."

missing_command_repo="${workdir}/missing-command"
create_valid_repo "${missing_command_repo}"
remove_text_from_doc "${missing_command_repo}" \
  "| 4 | \`aegisops seed-demo --profile smb-single-node --demo-mode explicit\` | Seed reviewed demo-only records for workflow rehearsal. | Demo records are labeled as demo-only and not production truth. | [Demo seed separation](demo-seed-contract.md). |"
assert_fails_with \
  "${missing_command_repo}" \
  "Missing complete Phase 52.9 first-user command row: seed-demo"

missing_troubleshooting_repo="${workdir}/missing-troubleshooting"
create_valid_repo "${missing_troubleshooting_repo}"
remove_text_from_doc "${missing_troubleshooting_repo}" \
  "Demo seed separation failures: \`docs/deployment/demo-seed-contract.md\` covers demo-only labels, fixture provenance, reset boundaries, production exclusion, and fake credential rejection."
assert_fails_with \
  "${missing_troubleshooting_repo}" \
  "Missing Phase 52.9 first-user stack docs statement: Demo seed separation failures"

missing_phase51_boundary_repo="${workdir}/missing-phase51-boundary"
create_valid_repo "${missing_phase51_boundary_repo}"
remove_text_from_doc "${missing_phase51_boundary_repo}" \
  "The replacement boundary remains the Phase 51.1 boundary in \`docs/adr/0011-phase-51-1-replacement-boundary.md\`: AegisOps replaces the SMB operating experience and authoritative record chain above Wazuh and Shuffle, not Wazuh internals, Shuffle internals, or every SIEM/SOAR capability."
assert_fails_with \
  "${missing_phase51_boundary_repo}" \
  "Missing Phase 52.9 first-user stack docs statement: The replacement boundary remains the Phase 51.1 boundary"

self_service_claim_repo="${workdir}/self-service-claim"
create_valid_repo "${self_service_claim_repo}"
printf '%s\n' "AegisOps is self-service commercial ready." \
  >>"${self_service_claim_repo}/docs/deployment/first-user-stack.md"
assert_fails_with \
  "${self_service_claim_repo}" \
  "Forbidden Phase 52.9 first-user stack docs claim: AegisOps is self-service commercial ready"

ga_claim_repo="${workdir}/ga-claim"
create_valid_repo "${ga_claim_repo}"
printf '%s\n' "Phase 52 completes GA readiness." \
  >>"${ga_claim_repo}/docs/deployment/first-user-stack.md"
assert_fails_with \
  "${ga_claim_repo}" \
  "Forbidden Phase 52.9 first-user stack docs claim: Phase 52 completes GA readiness"

authority_claim_repo="${workdir}/authority-claim"
create_valid_repo "${authority_claim_repo}"
printf '%s\n' "CLI status is workflow truth." \
  >>"${authority_claim_repo}/docs/deployment/first-user-stack.md"
assert_fails_with \
  "${authority_claim_repo}" \
  "Forbidden Phase 52.9 first-user stack docs claim: CLI status is workflow truth"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/first-user-stack.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.9 first-user stack docs: workstation-local absolute path detected"

echo "Phase 52.9 first-user stack docs negative and valid checks passed."
