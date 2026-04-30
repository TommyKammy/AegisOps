#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-50-13-public-facade-inventory-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_service() {
  local target="$1"

  mkdir -p "${target}/control-plane/aegisops_control_plane"
  cp "${repo_root}/control-plane/aegisops_control_plane/service.py" \
    "${target}/control-plane/aegisops_control_plane/service.py"
}

write_contract() {
  local target="$1"

  mkdir -p "${target}/docs/adr"
  cp "${repo_root}/docs/adr/0010-phase-50-13-public-facade-api-inventory-and-compatibility-policy.md" \
    "${target}/docs/adr/0010-phase-50-13-public-facade-api-inventory-and-compatibility-policy.md"
}

create_valid_repo() {
  local target="$1"

  write_service "${target}"
  write_contract "${target}"
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

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_method_repo="${workdir}/missing-method"
create_valid_repo "${missing_method_repo}"
perl -0pi -e 's/^\| `_require_mapping` \| private guard \| Internal facade and extracted helpers\. \| Keep until receiving collaborator owns input-shape enforcement\. \|\n//m' \
  "${missing_method_repo}/docs/adr/0010-phase-50-13-public-facade-api-inventory-and-compatibility-policy.md"
assert_fails_with \
  "${missing_method_repo}" \
  "Phase 50.13 inventory is missing facade method rows: _require_mapping"

invalid_category_repo="${workdir}/invalid-category"
create_valid_repo "${invalid_category_repo}"
perl -0pi -e 's/\| `describe_runtime` \| HTTP surface dependency \|/\| `describe_runtime` \| guessed surface \|/' \
  "${invalid_category_repo}/docs/adr/0010-phase-50-13-public-facade-api-inventory-and-compatibility-policy.md"
assert_fails_with \
  "${invalid_category_repo}" \
  "Phase 50.13 inventory uses unsupported categories: describe_runtime: guessed surface"

missing_policy_repo="${workdir}/missing-policy"
create_valid_repo "${missing_policy_repo}"
perl -0pi -e 's/^AegisOps control-plane records remain authoritative workflow truth\.\n//m' \
  "${missing_policy_repo}/docs/adr/0010-phase-50-13-public-facade-api-inventory-and-compatibility-policy.md"
assert_fails_with \
  "${missing_policy_repo}" \
  "Missing Phase 50.13 public facade inventory statement: AegisOps control-plane records remain authoritative workflow truth."

echo "Phase 50.13 public facade inventory verifier self-test passed."
