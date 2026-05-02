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
  cp -R "${repo_root}/control-plane/aegisops" \
    "${target}/control-plane/aegisops"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
  cp "${repo_root}/scripts/verify-phase-52-7-4-physical-layout-migration.sh" \
    "${target}/scripts/verify-phase-52-7-4-physical-layout-migration.sh"
  cp "${repo_root}/scripts/verify-phase-52-7-5-root-shim-reduction.sh" \
    "${target}/scripts/verify-phase-52-7-5-root-shim-reduction.sh"
  mkdir -p "${target}/control-plane/tests"
  cp "${repo_root}/control-plane/tests/test_phase52_7_4_physical_layout_migration.py" \
    "${target}/control-plane/tests/test_phase52_7_4_physical_layout_migration.py"
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
perl -0pi -e 's{^\| \x60proposed canonical namespace\x60 \| \x60aegisops_control_plane\x60 \| \x60\Kaegisops\.control_plane(?=\x60 \|)}{aegisops.controlplane}m' \
  "${wrong_proposed_namespace_repo}/${contract_path}"
assert_fails_with \
  "${wrong_proposed_namespace_repo}" \
  "Phase 52.7.1 namespace inventory proposed reference mismatch for proposed canonical namespace: expected aegisops.control_plane, got aegisops.controlplane"

missing_legacy_package_repo="${workdir}/missing-legacy-package"
create_valid_repo "${missing_legacy_package_repo}"
rm -rf "${missing_legacy_package_repo}/control-plane/aegisops_control_plane"
assert_fails_with \
  "${missing_legacy_package_repo}" \
  "Phase 52.7.1 compatibility path rejected: missing legacy package marker control-plane/aegisops_control_plane/__init__.py"

missing_canonical_package_repo="${workdir}/missing-canonical-package"
create_valid_repo "${missing_canonical_package_repo}"
rm -rf "${missing_canonical_package_repo}/control-plane/aegisops/control_plane"
assert_fails_with \
  "${missing_canonical_package_repo}" \
  "Phase 52.7.1 follow-on namespace guard rejected: missing canonical package marker control-plane/aegisops/control_plane/__init__.py"

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

non_executable_prerequisite_repo="${workdir}/non-executable-prerequisite"
create_valid_repo "${non_executable_prerequisite_repo}"
chmod -x \
  "${non_executable_prerequisite_repo}/scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh" \
  "${non_executable_prerequisite_repo}/scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh"
assert_passes "${non_executable_prerequisite_repo}"

missing_prerequisite_repo="${workdir}/missing-prerequisite"
create_valid_repo "${missing_prerequisite_repo}"
rm "${missing_prerequisite_repo}/scripts/verify-phase-52-7-4-physical-layout-migration.sh"
assert_fails_with \
  "${missing_prerequisite_repo}" \
  "Missing prerequisite verifier: verify-phase-52-7-4-physical-layout-migration.sh"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/${contract_path}"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.7.1 namespace/layout inventory: workstation-local absolute path detected"

echo "Phase 52.7.1 namespace/layout inventory verifier negative and valid fixtures passed."
