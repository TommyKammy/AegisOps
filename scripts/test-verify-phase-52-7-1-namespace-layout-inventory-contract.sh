#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh"
contract_path="docs/adr/0016-phase-52-7-1-namespace-and-layout-inventory-contract.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/adr" "${target}/control-plane" "${target}/scripts" "${target}/.github/workflows"
  cp "${repo_root}/${contract_path}" "${target}/${contract_path}"
  cp "${repo_root}/docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md" \
    "${target}/docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md"
  cp "${repo_root}/docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md" \
    "${target}/docs/adr/0014-phase-52-6-1-root-shim-inventory-and-deprecation-contract.md"
  cp "${repo_root}/scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh" \
    "${target}/scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh"
  cp "${repo_root}/scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh" \
    "${target}/scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh"
  cp "${repo_root}/scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh" \
    "${target}/scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh"
  cp "${repo_root}/scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh" \
    "${target}/scripts/test-verify-phase-52-7-1-namespace-layout-inventory-contract.sh"
  cp "${repo_root}/.github/workflows/ci.yml" "${target}/.github/workflows/ci.yml"
  cp "${repo_root}/control-plane/main.py" "${target}/control-plane/main.py"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
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

missing_current_package_repo="${workdir}/missing-current-package-row"
create_valid_repo "${missing_current_package_repo}"
perl -0pi -e 's/^\| `current import package` \|.*\n//m' \
  "${missing_current_package_repo}/${contract_path}"
assert_fails_with \
  "${missing_current_package_repo}" \
  "Missing Phase 52.7.1 namespace inventory row: current import package"

missing_proposed_namespace_repo="${workdir}/missing-proposed-namespace-row"
create_valid_repo "${missing_proposed_namespace_repo}"
perl -0pi -e 's/^\| `proposed canonical namespace` \|.*\n//m' \
  "${missing_proposed_namespace_repo}/${contract_path}"
assert_fails_with \
  "${missing_proposed_namespace_repo}" \
  "Missing Phase 52.7.1 namespace inventory row: proposed canonical namespace"

wrong_proposed_namespace_repo="${workdir}/wrong-proposed-namespace"
create_valid_repo "${wrong_proposed_namespace_repo}"
perl -0pi -e 's/aegisops\.control_plane/aegisops.controlplane/g' \
  "${wrong_proposed_namespace_repo}/${contract_path}"
assert_fails_with \
  "${wrong_proposed_namespace_repo}" \
  'Missing Phase 52.7.1 namespace/layout statement: The proposed canonical namespace `aegisops.control_plane` is a future target only.'

package_moved_repo="${workdir}/package-moved"
create_valid_repo "${package_moved_repo}"
mkdir -p "${package_moved_repo}/control-plane/aegisops"
mv "${package_moved_repo}/control-plane/aegisops_control_plane" \
  "${package_moved_repo}/control-plane/aegisops/control_plane"
assert_fails_with \
  "${package_moved_repo}" \
  "Phase 52.7.1 file movement rejected: missing current package path control-plane/aegisops_control_plane/"

entrypoint_moved_repo="${workdir}/entrypoint-moved"
create_valid_repo "${entrypoint_moved_repo}"
mv "${entrypoint_moved_repo}/control-plane/main.py" \
  "${entrypoint_moved_repo}/control-plane/aegisops-main.py"
assert_fails_with \
  "${entrypoint_moved_repo}" \
  "Phase 52.7.1 file movement rejected: missing current path control-plane/main.py"

behavior_change_repo="${workdir}/behavior-change-claim"
create_valid_repo "${behavior_change_repo}"
printf '%s\n' "This contract changes runtime behavior." \
  >>"${behavior_change_repo}/${contract_path}"
assert_fails_with \
  "${behavior_change_repo}" \
  "Forbidden Phase 52.7.1 namespace/layout claim: This contract changes runtime behavior."

importable_namespace_repo="${workdir}/importable-namespace-claim"
create_valid_repo "${importable_namespace_repo}"
printf '%s\n' 'The `aegisops.control_plane` namespace is importable now.' \
  >>"${importable_namespace_repo}/${contract_path}"
assert_fails_with \
  "${importable_namespace_repo}" \
  'Forbidden Phase 52.7.1 namespace/layout claim: The `aegisops.control_plane` namespace is importable now.'

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/${contract_path}"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.7.1 namespace/layout inventory: workstation-local absolute path detected"

echo "Phase 52.7.1 namespace/layout inventory verifier negative and valid fixtures passed."
