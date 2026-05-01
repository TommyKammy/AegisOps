#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-8-clean-host-smoke-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/fixtures/clean-host-smoke"
  printf '%s\n' "# AegisOps" "See [Phase 52.8 clean-host smoke skeleton](docs/deployment/clean-host-smoke-skeleton.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/clean-host-smoke-skeleton.md" \
    "${target}/docs/deployment/clean-host-smoke-skeleton.md"
  cp "${repo_root}/docs/deployment/fixtures/clean-host-smoke/"*.json \
    "${target}/docs/deployment/fixtures/clean-host-smoke/"
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
    "${target}/docs/deployment/clean-host-smoke-skeleton.md"
}

set_fixture_json_value() {
  local target="$1"
  local fixture="$2"
  local expression="$3"

  python3 - "${target}/docs/deployment/fixtures/clean-host-smoke/${fixture}" "${expression}" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
expression = sys.argv[2]
payload = json.loads(path.read_text(encoding="utf-8"))
exec(expression, {"payload": payload})
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/clean-host-smoke-skeleton.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 52.8 clean-host smoke skeleton"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 52.8 clean-host smoke skeleton."

missing_sequence_row_repo="${workdir}/missing-sequence-row"
create_valid_repo "${missing_sequence_row_repo}"
remove_text_from_contract "${missing_sequence_row_repo}" \
  "| 4 | \`seed-demo\` | Phase 52.1 CLI command contract and Phase 52.7 demo seed contract. | \`mocked\` or \`skipped\` until demo seed command execution is implemented. | Demo rehearsal fixture evidence only. |"
assert_fails_with \
  "${missing_sequence_row_repo}" \
  "Missing complete Phase 52.8 smoke sequence row: seed-demo"

missing_mocked_state_repo="${workdir}/missing-mocked-state"
create_valid_repo "${missing_mocked_state_repo}"
remove_text_from_contract "${missing_mocked_state_repo}" \
  "| \`mocked\` | The smoke used a reviewed fixture or test double instead of a live clean host. | Replace the mocked step with a real implementation in the later owning phase named by the fixture. |"
assert_fails_with \
  "${missing_mocked_state_repo}" \
  "Missing complete Phase 52.8 state row: mocked"

missing_contract_ref_repo="${workdir}/missing-contract-ref"
create_valid_repo "${missing_contract_ref_repo}"
remove_text_from_contract "${missing_contract_ref_repo}" \
  'Phase 52.6 host preflight contract: `docs/deployment/host-preflight-contract.md`.'
assert_fails_with \
  "${missing_contract_ref_repo}" \
  "Missing Phase 52.8 clean-host smoke skeleton statement: Phase 52.6 host preflight contract"

missing_fixture_repo="${workdir}/missing-fixture"
create_valid_repo "${missing_fixture_repo}"
rm "${missing_fixture_repo}/docs/deployment/fixtures/clean-host-smoke/false-success.json"
assert_fails_with \
  "${missing_fixture_repo}" \
  "Missing Phase 52.8 clean-host smoke fixture: false-success.json"

reordered_fixture_repo="${workdir}/reordered-fixture"
create_valid_repo "${reordered_fixture_repo}"
set_fixture_json_value \
  "${reordered_fixture_repo}" \
  "valid-clean-host-smoke.json" \
  "payload['sequence'][2], payload['sequence'][3] = payload['sequence'][3], payload['sequence'][2]"
assert_fails_with \
  "${reordered_fixture_repo}" \
  "Invalid Phase 52.8 clean-host smoke fixture state for valid-clean-host-smoke.json: expected valid"

misassigned_contract_refs_repo="${workdir}/misassigned-contract-refs"
create_valid_repo "${misassigned_contract_refs_repo}"
set_fixture_json_value \
  "${misassigned_contract_refs_repo}" \
  "valid-clean-host-smoke.json" \
  "payload['sequence'][1]['contract_refs'], payload['sequence'][2]['contract_refs'] = payload['sequence'][2]['contract_refs'], payload['sequence'][1]['contract_refs']"
assert_fails_with \
  "${misassigned_contract_refs_repo}" \
  "Invalid Phase 52.8 clean-host smoke fixture state for valid-clean-host-smoke.json: expected valid"

false_success_not_rejected_repo="${workdir}/false-success-not-rejected"
create_valid_repo "${false_success_not_rejected_repo}"
set_fixture_json_value \
  "${false_success_not_rejected_repo}" \
  "false-success.json" \
  "payload['overall_state'] = 'mocked'; payload['full_stack_success'] = False"
assert_fails_with \
  "${false_success_not_rejected_repo}" \
  "Invalid Phase 52.8 clean-host smoke fixture state for false-success.json: expected rejection"

compose_truth_not_rejected_repo="${workdir}/compose-truth-not-rejected"
create_valid_repo "${compose_truth_not_rejected_repo}"
set_fixture_json_value \
  "${compose_truth_not_rejected_repo}" \
  "compose-truth.json" \
  "payload['authority_boundary'] = 'clean-host smoke output is validation evidence only'; payload['sequence'][1]['evidence_role'] = 'compose fixture evidence only'"
assert_fails_with \
  "${compose_truth_not_rejected_repo}" \
  "Invalid Phase 52.8 clean-host smoke fixture state for compose-truth.json: expected rejection"

phase_required_not_rejected_repo="${workdir}/phase-required-not-rejected"
create_valid_repo "${phase_required_not_rejected_repo}"
set_fixture_json_value \
  "${phase_required_not_rejected_repo}" \
  "phase-53-54-required.json" \
  "payload['requires_phase_53_or_54_completion'] = False"
assert_fails_with \
  "${phase_required_not_rejected_repo}" \
  "Invalid Phase 52.8 clean-host smoke fixture state for phase-53-54-required.json: expected rejection"

workflow_truth_doc_repo="${workdir}/workflow-truth-doc"
create_valid_repo "${workflow_truth_doc_repo}"
printf '%s\n' "Clean-host smoke success is workflow truth." \
  >>"${workflow_truth_doc_repo}/docs/deployment/clean-host-smoke-skeleton.md"
assert_fails_with \
  "${workflow_truth_doc_repo}" \
  "Forbidden Phase 52.8 clean-host smoke skeleton claim: Clean-host smoke success is workflow truth"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/clean-host-smoke-skeleton.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.8 clean-host smoke skeleton: workstation-local absolute path detected"

echo "Phase 52.8 clean-host smoke skeleton negative and valid fixtures passed."
