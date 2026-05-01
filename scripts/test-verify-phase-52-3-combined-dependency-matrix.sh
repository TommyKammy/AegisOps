#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-3-combined-dependency-matrix.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/deployment"
  printf '%s\n' "# AegisOps" "See [Phase 52.3 combined dependency matrix](docs/deployment/combined-dependency-matrix.md)." >"${target}/README.md"
  cp "${repo_root}/docs/deployment/combined-dependency-matrix.md" \
    "${target}/docs/deployment/combined-dependency-matrix.md"
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
    "${target}/docs/deployment/combined-dependency-matrix.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_matrix_repo="${workdir}/missing-matrix"
create_valid_repo "${missing_matrix_repo}"
rm "${missing_matrix_repo}/docs/deployment/combined-dependency-matrix.md"
assert_fails_with \
  "${missing_matrix_repo}" \
  "Missing Phase 52.3 combined dependency matrix"

missing_aegisops_repo="${workdir}/missing-aegisops"
create_valid_repo "${missing_aegisops_repo}"
remove_text_from_matrix "${missing_aegisops_repo}" \
  "| AegisOps |"
assert_fails_with \
  "${missing_aegisops_repo}" \
  "Missing complete Phase 52.3 dependency row: AegisOps"

missing_wazuh_repo="${workdir}/missing-wazuh"
create_valid_repo "${missing_wazuh_repo}"
remove_text_from_matrix "${missing_wazuh_repo}" \
  "| Wazuh |"
assert_fails_with \
  "${missing_wazuh_repo}" \
  "Missing complete Phase 52.3 dependency row: Wazuh"

missing_shuffle_repo="${workdir}/missing-shuffle"
create_valid_repo "${missing_shuffle_repo}"
remove_text_from_matrix "${missing_shuffle_repo}" \
  "| Shuffle |"
assert_fails_with \
  "${missing_shuffle_repo}" \
  "Missing complete Phase 52.3 dependency row: Shuffle"

missing_postgresql_repo="${workdir}/missing-postgresql"
create_valid_repo "${missing_postgresql_repo}"
remove_text_from_matrix "${missing_postgresql_repo}" \
  "| PostgreSQL |"
assert_fails_with \
  "${missing_postgresql_repo}" \
  "Missing complete Phase 52.3 dependency row: PostgreSQL"

missing_proxy_repo="${workdir}/missing-proxy"
create_valid_repo "${missing_proxy_repo}"
remove_text_from_matrix "${missing_proxy_repo}" \
  "| Proxy |"
assert_fails_with \
  "${missing_proxy_repo}" \
  "Missing complete Phase 52.3 dependency row: Proxy"

missing_incompat_repo="${workdir}/missing-incompatibility"
create_valid_repo "${missing_incompat_repo}"
remove_text_from_matrix "${missing_incompat_repo}" \
  "Known incompatible versions must be explicit and must fail host preflight follow-up until reviewed."
assert_fails_with \
  "${missing_incompat_repo}" \
  "Missing Phase 52.3 combined dependency matrix statement: Known incompatible versions must be explicit"

workflow_truth_repo="${workdir}/workflow-truth"
create_valid_repo "${workflow_truth_repo}"
printf '%s\n' "Substrate version state is AegisOps workflow truth." \
  >>"${workflow_truth_repo}/docs/deployment/combined-dependency-matrix.md"
assert_fails_with \
  "${workflow_truth_repo}" \
  "Forbidden Phase 52.3 combined dependency matrix claim: Substrate version state is AegisOps workflow truth"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/deployment/combined-dependency-matrix.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.3 combined dependency matrix: workstation-local absolute path detected"

echo "Phase 52.3 combined dependency matrix negative and valid fixtures passed."
