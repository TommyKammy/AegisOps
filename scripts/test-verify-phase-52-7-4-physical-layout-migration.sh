#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-7-4-physical-layout-migration.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo_copy() {
  local target="$1"

  mkdir -p "${target}/control-plane" "${target}/scripts"
  cp -R "${repo_root}/control-plane/aegisops" "${target}/control-plane/aegisops"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" "${target}/control-plane/aegisops_control_plane"
  mkdir -p "${target}/control-plane/tests"
  cp "${repo_root}/control-plane/tests/test_phase52_7_4_physical_layout_migration.py" \
    "${target}/control-plane/tests/test_phase52_7_4_physical_layout_migration.py"
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
create_repo_copy "${valid_repo}"
assert_passes "${valid_repo}"

missing_canonical_repo="${workdir}/missing-canonical"
create_repo_copy "${missing_canonical_repo}"
rm -f "${missing_canonical_repo}/control-plane/aegisops/control_plane/service.py"
assert_fails_with \
  "${missing_canonical_repo}" \
  "Missing Phase 52.7.4 physical layout migration path: control-plane/aegisops/control_plane/service.py"

legacy_impl_repo="${workdir}/legacy-implementation"
create_repo_copy "${legacy_impl_repo}"
printf '"""stale legacy implementation."""\n' \
  >"${legacy_impl_repo}/control-plane/aegisops_control_plane/service.py"
assert_fails_with \
  "${legacy_impl_repo}" \
  "Phase 52.7.4 physical layout migration rejected: legacy package contains implementation files"

missing_legacy_bridge_repo="${workdir}/missing-legacy-bridge"
create_repo_copy "${missing_legacy_bridge_repo}"
rm -f "${missing_legacy_bridge_repo}/control-plane/aegisops_control_plane/__init__.py"
assert_fails_with \
  "${missing_legacy_bridge_repo}" \
  "Missing Phase 52.7.4 physical layout migration path: control-plane/aegisops_control_plane/__init__.py"

echo "Phase 52.7.4 physical layout migration verifier negative and valid fixtures passed."
