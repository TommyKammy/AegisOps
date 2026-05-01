#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-6-host-preflight-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment/fixtures/host-preflight"
  printf '%s\n' "# AegisOps" "See [Phase 52.6 host preflight contract](docs/deployment/host-preflight-contract.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/host-preflight-contract.md" \
    "${target}/docs/deployment/host-preflight-contract.md"
  cp "${repo_root}/docs/deployment/combined-dependency-matrix.md" \
    "${target}/docs/deployment/combined-dependency-matrix.md"
  cp "${repo_root}/docs/deployment/fixtures/host-preflight/"*.json \
    "${target}/docs/deployment/fixtures/host-preflight/"
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
    "${target}/docs/deployment/host-preflight-contract.md"
}

set_fixture_state() {
  local target="$1"
  local fixture="$2"
  local state="$3"

  python3 - "$target/docs/deployment/fixtures/host-preflight/${fixture}" "${state}" <<'PY'
import json
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
state = sys.argv[2]
payload = json.loads(path.read_text(encoding="utf-8"))
payload["overall_state"] = state
for result in payload["results"]:
    result["state"] = state
path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
PY
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/deployment/host-preflight-contract.md"
assert_fails_with \
  "${missing_contract_repo}" \
  "Missing Phase 52.6 host preflight contract"

missing_docker_coverage_repo="${workdir}/missing-docker-coverage"
create_valid_repo "${missing_docker_coverage_repo}"
remove_text_from_contract "${missing_docker_coverage_repo}" \
  "| Docker engine |"
assert_fails_with \
  "${missing_docker_coverage_repo}" \
  "Missing complete Phase 52.6 checked input row: Docker engine"

missing_compose_coverage_repo="${workdir}/missing-compose-coverage"
create_valid_repo "${missing_compose_coverage_repo}"
remove_text_from_contract "${missing_compose_coverage_repo}" \
  "| Docker Compose |"
assert_fails_with \
  "${missing_compose_coverage_repo}" \
  "Missing complete Phase 52.6 checked input row: Docker Compose"

missing_ports_coverage_repo="${workdir}/missing-ports-coverage"
create_valid_repo "${missing_ports_coverage_repo}"
remove_text_from_contract "${missing_ports_coverage_repo}" \
  "| Ports |"
assert_fails_with \
  "${missing_ports_coverage_repo}" \
  "Missing complete Phase 52.6 checked input row: Ports"

missing_vm_coverage_repo="${workdir}/missing-vm-coverage"
create_valid_repo "${missing_vm_coverage_repo}"
remove_text_from_contract "${missing_vm_coverage_repo}" \
  "| \`vm.max_map_count\` |"
assert_fails_with \
  "${missing_vm_coverage_repo}" \
  "Missing complete Phase 52.6 checked input row: vm.max_map_count"

missing_mocked_state_repo="${workdir}/missing-mocked-state"
create_valid_repo "${missing_mocked_state_repo}"
remove_text_from_contract "${missing_mocked_state_repo}" \
  "| \`mocked\` | The result came from a fixture or test double, not live host state. | Valid only in fixture expectations and tests; it is not setup readiness evidence. |"
assert_fails_with \
  "${missing_mocked_state_repo}" \
  "Missing complete Phase 52.6 output state row: mocked"

missing_docker_fixture_repo="${workdir}/missing-docker-fixture"
create_valid_repo "${missing_docker_fixture_repo}"
rm "${missing_docker_fixture_repo}/docs/deployment/fixtures/host-preflight/missing-docker.json"
assert_fails_with \
  "${missing_docker_fixture_repo}" \
  "Missing Phase 52.6 host preflight fixture: missing-docker.json"

docker_false_success_repo="${workdir}/docker-false-success"
create_valid_repo "${docker_false_success_repo}"
set_fixture_state "${docker_false_success_repo}" "missing-docker.json" "pass"
assert_fails_with \
  "${docker_false_success_repo}" \
  "Invalid Phase 52.6 host preflight fixture state for missing-docker.json: expected fail"

compose_false_success_repo="${workdir}/compose-false-success"
create_valid_repo "${compose_false_success_repo}"
set_fixture_state "${compose_false_success_repo}" "missing-compose.json" "mocked"
assert_fails_with \
  "${compose_false_success_repo}" \
  "Invalid Phase 52.6 host preflight fixture state for missing-compose.json: expected fail"

bad_ports_false_success_repo="${workdir}/bad-ports-false-success"
create_valid_repo "${bad_ports_false_success_repo}"
set_fixture_state "${bad_ports_false_success_repo}" "bad-ports.json" "pass"
assert_fails_with \
  "${bad_ports_false_success_repo}" \
  "Invalid Phase 52.6 host preflight fixture state for bad-ports.json: expected fail"

low_ram_false_success_repo="${workdir}/low-ram-false-success"
create_valid_repo "${low_ram_false_success_repo}"
set_fixture_state "${low_ram_false_success_repo}" "low-ram.json" "skip"
assert_fails_with \
  "${low_ram_false_success_repo}" \
  "Invalid Phase 52.6 host preflight fixture state for low-ram.json: expected fail"

vm_false_success_repo="${workdir}/vm-false-success"
create_valid_repo "${vm_false_success_repo}"
set_fixture_state "${vm_false_success_repo}" "missing-vm-max-map-count.json" "pass"
assert_fails_with \
  "${vm_false_success_repo}" \
  "Invalid Phase 52.6 host preflight fixture state for missing-vm-max-map-count.json: expected fail"

profile_false_success_repo="${workdir}/profile-false-success"
create_valid_repo "${profile_false_success_repo}"
set_fixture_state "${profile_false_success_repo}" "invalid-profile.json" "pass"
assert_fails_with \
  "${profile_false_success_repo}" \
  "Invalid Phase 52.6 host preflight fixture state for invalid-profile.json: expected fail"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Host preflight status is AegisOps workflow truth." \
  >>"${workflow_truth_repo}/docs/deployment/host-preflight-contract.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 52.6 host preflight contract claim: Host preflight status is AegisOps workflow truth"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/host-preflight-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.6 host preflight contract: workstation-local absolute path detected"

missing_matrix_repo="${workdir}/missing-matrix"
create_valid_repo "${missing_matrix_repo}"
rm "${missing_matrix_repo}/docs/deployment/combined-dependency-matrix.md"
assert_fails_with \
  "${missing_matrix_repo}" \
  "Missing Phase 52.3 dependency matrix for Phase 52.6 link check"

missing_readme_link_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_link_repo}"
printf '%s\n' "# AegisOps" >"${missing_readme_link_repo}/README.md"
assert_fails_with \
  "${missing_readme_link_repo}" \
  "README must link the Phase 52.6 host preflight contract."

echo "Phase 52.6 host preflight negative and valid fixtures passed."
