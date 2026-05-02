#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-7-5-root-shim-reduction.sh"

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
  cp "${repo_root}/control-plane/tests/test_phase52_7_5_root_shim_reduction.py" \
    "${target}/control-plane/tests/test_phase52_7_5_root_shim_reduction.py"
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

restored_shim_repo="${workdir}/restored-shim"
create_repo_copy "${restored_shim_repo}"
printf '%s\n' '"""Restored simple canonical shim."""' \
  >"${restored_shim_repo}/control-plane/aegisops/control_plane/action_policy.py"
assert_fails_with \
  "${restored_shim_repo}" \
  "Phase 52.7.5 root shim reduction expected retained canonical root files"

missing_alias_repo="${workdir}/missing-alias"
create_repo_copy "${missing_alias_repo}"
alias_file="${missing_alias_repo}/control-plane/aegisops/control_plane/core/legacy_import_aliases.py"
if ! grep -Fq '"aegisops_control_plane.action_policy": _alias(' "${alias_file}"; then
  echo "Fixture setup failed: expected aegisops_control_plane.action_policy alias entry not found in legacy_import_aliases.py before mutation" >&2
  exit 1
fi
perl -0pi -e 's/    "aegisops_control_plane.action_policy": _alias\(\n        "aegisops_control_plane.action_policy",\n        "aegisops_control_plane.actions.action_policy",\n        "actions",\n        "actions\/action_policy.py",\n    \),\n//' \
  "${alias_file}"
if grep -Fq '"aegisops_control_plane.action_policy": _alias(' "${alias_file}"; then
  echo "Fixture setup failed: aegisops_control_plane.action_policy alias entry still present in legacy_import_aliases.py after mutation" >&2
  exit 1
fi
assert_fails_with \
  "${missing_alias_repo}" \
  "Phase 52.7.5 root shim reduction missing canonical alias: aegisops.control_plane.action_policy"

missing_retained_owner_repo="${workdir}/missing-retained-owner"
create_repo_copy "${missing_retained_owner_repo}"
rm -f "${missing_retained_owner_repo}/control-plane/aegisops/control_plane/models.py"
assert_fails_with \
  "${missing_retained_owner_repo}" \
  "Missing Phase 52.7.5 root shim reduction path: control-plane/aegisops/control_plane/models.py"

echo "Phase 52.7.5 root shim reduction verifier negative and valid fixtures passed."
