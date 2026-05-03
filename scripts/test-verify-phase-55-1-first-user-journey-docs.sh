#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-55-1-first-user-journey-docs.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/getting-started"
  printf '%s\n' \
    "# AegisOps" \
    "See [Phase 55.1 first-user journey](docs/getting-started/first-user-journey.md)." \
    "See [Phase 55.1 first 30 minutes](docs/getting-started/first-30-minutes.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/getting-started/first-user-journey.md" \
    "${target}/docs/getting-started/first-user-journey.md"
  cp "${repo_root}/docs/getting-started/first-30-minutes.md" \
    "${target}/docs/getting-started/first-30-minutes.md"
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
  local doc_relative_path="$2"
  local text="$3"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/${doc_relative_path}"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_journey_repo="${workdir}/missing-journey"
create_valid_repo "${missing_journey_repo}"
rm "${missing_journey_repo}/docs/getting-started/first-user-journey.md"
assert_fails_with \
  "${missing_journey_repo}" \
  "Missing Phase 55.1 first-user journey docs"

missing_minutes_repo="${workdir}/missing-minutes"
create_valid_repo "${missing_minutes_repo}"
rm "${missing_minutes_repo}/docs/getting-started/first-30-minutes.md"
assert_fails_with \
  "${missing_minutes_repo}" \
  "Missing Phase 55.1 first-user journey docs"

missing_command_repo="${workdir}/missing-command"
create_valid_repo "${missing_command_repo}"
remove_text_from_doc "${missing_command_repo}" \
  "docs/getting-started/first-user-journey.md" \
  "| 4 | \`aegisops seed-demo --profile smb-single-node --demo-mode explicit\` | Seed a reviewed demo-only queue for the guided journey. | The queue is labeled demo-only and subordinate to AegisOps control-plane truth. |"
assert_fails_with \
  "${missing_command_repo}" \
  "Missing complete Phase 55.1 few-command row: seed-demo"

missing_sequence_repo="${workdir}/missing-sequence"
create_valid_repo "${missing_sequence_repo}"
remove_text_from_doc "${missing_sequence_repo}" \
  "docs/getting-started/first-user-journey.md" \
  "9. **Reconciliation** - Compare the execution receipt against the approved request and record the reconciliation outcome before any closeout language."
assert_fails_with \
  "${missing_sequence_repo}" \
  "Missing or out-of-order Phase 55.1 workflow sequence term: Reconciliation"

production_truth_repo="${workdir}/production-truth"
create_valid_repo "${production_truth_repo}"
printf '%s\n' "Demo records are production truth." \
  >>"${production_truth_repo}/docs/getting-started/first-user-journey.md"
assert_fails_with \
  "${production_truth_repo}" \
  "Forbidden Phase 55.1 first-user journey docs claim: demo (records|data) (are|is) production truth"

phase_overclaim_repo="${workdir}/phase-overclaim"
create_valid_repo "${phase_overclaim_repo}"
printf '%s\n' "Phase 56 is complete." \
  >>"${phase_overclaim_repo}/docs/getting-started/first-30-minutes.md"
assert_fails_with \
  "${phase_overclaim_repo}" \
  "Forbidden Phase 55.1 first-user journey docs claim: Phase 56 (is )?(complete|completed|done)"

commercial_claim_repo="${workdir}/commercial-claim"
create_valid_repo "${commercial_claim_repo}"
printf '%s\n' "AegisOps is commercially ready." \
  >>"${commercial_claim_repo}/docs/getting-started/first-user-journey.md"
assert_fails_with \
  "${commercial_claim_repo}" \
  "Forbidden Phase 55.1 first-user journey docs claim: AegisOps (is )?commercially ready"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 55.1 first-user journey docs."

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/getting-started/first-user-journey.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 55.1 docs: workstation-local absolute path detected"

echo "Phase 55.1 first-user journey docs negative and valid checks passed."
