#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-1-cli-command-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  printf '%s\n' "# AegisOps" "See [Phase 52.1 CLI command contract](docs/phase-52-1-cli-command-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/phase-52-1-cli-command-contract.md" \
    "${target}/docs/phase-52-1-cli-command-contract.md"
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
    "${target}/docs/phase-52-1-cli-command-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 52.1 CLI command contract"

missing_command_repo="${workdir}/missing-seed-demo"
create_valid_repo "${missing_command_repo}"
remove_text_from_contract "${missing_command_repo}" \
  '| `seed-demo` | Seed reviewed demo-only records and fixtures for first-user evaluation without production claims. | Initialized workspace; explicit demo mode flag; selected `<profile-name>`; demo fixture bundle. | `result=ok` only for demo fixture admission; demo record identifiers; warning that demo data is not production truth; next action `aegisops status`. | Fail closed if demo mode is not explicit, fixture provenance is missing, fake credentials are treated as real, or seed data would overwrite production-bound records. | Safe to retry after cleaning partial demo state or supplying a reviewed fixture bundle. Retry must not duplicate authoritative records silently. |'
assert_fails_with \
  "${missing_command_repo}" \
  "Missing complete Phase 52.1 CLI command row: seed-demo"

missing_retry_repo="${workdir}/missing-retry"
create_valid_repo "${missing_retry_repo}"
remove_text_from_contract "${missing_retry_repo}" \
  "Safe retry means a command can be rerun after the stated prerequisite is repaired without destructive cleanup, duplicate authoritative writes, hidden state promotion, or widened product scope."
assert_fails_with \
  "${missing_retry_repo}" \
  "Missing Phase 52.1 CLI command contract statement: Safe retry means"

missing_mocked_repo="${workdir}/missing-mocked"
create_valid_repo "${missing_mocked_repo}"
remove_text_from_contract "${missing_mocked_repo}" \
  '`skipped` and `mocked` states must not be reported as false success.'
assert_fails_with \
  "${missing_mocked_repo}" \
  "Missing Phase 52.1 CLI command contract statement: \`skipped\` and \`mocked\` states must not be reported as false success."

missing_phase51_citation_repo="${workdir}/missing-phase51-citation"
create_valid_repo "${missing_phase51_citation_repo}"
remove_text_from_contract "${missing_phase51_citation_repo}" \
  'This command contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
assert_fails_with \
  "${missing_phase51_citation_repo}" \
  "Missing Phase 52.1 CLI command contract statement: This command contract cites the Phase 51.6 authority-boundary negative-test policy"

commented_heading_repo="${workdir}/commented-heading"
create_valid_repo "${commented_heading_repo}"
remove_text_from_contract "${commented_heading_repo}" \
  '# Phase 52.1 CLI Command Contract'
printf '%s\n' '<!-- # Phase 52.1 CLI Command Contract -->' \
  >>"${commented_heading_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${commented_heading_repo}" \
  "Missing Phase 52.1 CLI command contract heading: # Phase 52.1 CLI Command Contract"

missing_command_field_repo="${workdir}/missing-command-field"
create_valid_repo "${missing_command_field_repo}"
remove_text_from_contract "${missing_command_field_repo}" \
  '- `command`: the invoked command name.'
assert_fails_with \
  "${missing_command_field_repo}" \
  "Missing or empty Phase 52.1 shared output field: command"

missing_summary_field_repo="${workdir}/missing-summary-field"
create_valid_repo "${missing_summary_field_repo}"
remove_text_from_contract "${missing_summary_field_repo}" \
  '- `summary`: a short human-readable operator summary.'
assert_fails_with \
  "${missing_summary_field_repo}" \
  "Missing or empty Phase 52.1 shared output field: summary"

missing_next_actions_field_repo="${workdir}/missing-next-actions-field"
create_valid_repo "${missing_next_actions_field_repo}"
remove_text_from_contract "${missing_next_actions_field_repo}" \
  '- `next_actions`: zero or more safe follow-up commands or prerequisite actions.'
assert_fails_with \
  "${missing_next_actions_field_repo}" \
  "Missing or empty Phase 52.1 shared output field: next_actions"

missing_evidence_field_repo="${workdir}/missing-evidence-field"
create_valid_repo "${missing_evidence_field_repo}"
remove_text_from_contract "${missing_evidence_field_repo}" \
  '- `evidence`: zero or more readiness evidence references, never authoritative workflow truth.'
assert_fails_with \
  "${missing_evidence_field_repo}" \
  "Missing or empty Phase 52.1 shared output field: evidence"

missing_result_field_repo="${workdir}/missing-result-field"
create_valid_repo "${missing_result_field_repo}"
remove_text_from_contract "${missing_result_field_repo}" \
  '- `result`: one of `ok`, `skipped`, `mocked`, `degraded`, or `failed`.'
assert_fails_with \
  "${missing_result_field_repo}" \
  "Missing or empty Phase 52.1 shared output field: result"

fenced_result_field_repo="${workdir}/fenced-result-field"
create_valid_repo "${fenced_result_field_repo}"
remove_text_from_contract "${fenced_result_field_repo}" \
  '- `result`: one of `ok`, `skipped`, `mocked`, `degraded`, or `failed`.'
printf '%s\n' \
  '```markdown' \
  '- `result`: one of `ok`, `skipped`, `mocked`, `degraded`, or `failed`.' \
  '```' \
  >>"${fenced_result_field_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${fenced_result_field_repo}" \
  "Missing or empty Phase 52.1 shared output field: result"

invalid_result_field_repo="${workdir}/invalid-result-field"
create_valid_repo "${invalid_result_field_repo}"
perl -0pi -e 's/- `result`: one of `ok`, `skipped`, `mocked`, `degraded`, or `failed`\./- `result`: one of `ok` or `failed`./g' \
  "${invalid_result_field_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${invalid_result_field_repo}" \
  "Invalid Phase 52.1 shared output result field"

cli_truth_repo="${workdir}/cli-truth"
create_valid_repo "${cli_truth_repo}"
printf '%s\n' "CLI status is workflow truth." \
  >>"${cli_truth_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${cli_truth_repo}" \
  "Forbidden Phase 52.1 CLI command contract claim: CLI status is workflow truth"

wazuh_complete_repo="${workdir}/wazuh-complete"
create_valid_repo "${wazuh_complete_repo}"
printf '%s\n' "Phase 52 completes Wazuh profiles." \
  >>"${wazuh_complete_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${wazuh_complete_repo}" \
  "Forbidden Phase 52.1 CLI command contract claim: Phase 52 completes Wazuh profiles"

shuffle_complete_repo="${workdir}/shuffle-complete"
create_valid_repo "${shuffle_complete_repo}"
printf '%s\n' "Phase 52 completes Shuffle profiles." \
  >>"${shuffle_complete_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${shuffle_complete_repo}" \
  "Forbidden Phase 52.1 CLI command contract claim: Phase 52 completes Shuffle profiles"

fenced_command_row_repo="${workdir}/fenced-command-row"
create_valid_repo "${fenced_command_row_repo}"
remove_text_from_contract "${fenced_command_row_repo}" \
  '| `logs` | Show bounded logs for selected first-user stack components. | Initialized workspace; `<log-selector>` or default selector; optional time window. | Bounded log stream or retained log path; redaction and truncation notice; evidence references only. | Fail closed if the selector is ambiguous, logs cannot be bounded, redaction cannot run, or log text is used as authoritative workflow truth. | Safe to retry with a narrower selector or time window. Retry must not require destructive cleanup. |'
printf '%s\n' \
  '```markdown' \
  '| `logs` | Show bounded logs for selected first-user stack components. | Initialized workspace; `<log-selector>` or default selector; optional time window. | Bounded log stream or retained log path; redaction and truncation notice; evidence references only. | Fail closed if the selector is ambiguous, logs cannot be bounded, redaction cannot run, or log text is used as authoritative workflow truth. | Safe to retry with a narrower selector or time window. Retry must not require destructive cleanup. |' \
  '```' \
  >>"${fenced_command_row_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${fenced_command_row_repo}" \
  "Missing complete Phase 52.1 CLI command row: logs"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/phase-52-1-cli-command-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.1 CLI command contract: workstation-local absolute path detected"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" "Phase 52.1 CLI command contract exists." >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 52.1 CLI command contract."

commented_readme_link_repo="${workdir}/commented-readme-link"
create_valid_repo "${commented_readme_link_repo}"
printf '%s\n' \
  "# AegisOps" \
  "<!-- [Phase 52.1 CLI command contract](docs/phase-52-1-cli-command-contract.md) -->" \
  >"${commented_readme_link_repo}/README.md"
assert_fails_with \
  "${commented_readme_link_repo}" \
  "README must link the Phase 52.1 CLI command contract."

echo "Phase 52.1 CLI command contract verifier tests passed."
