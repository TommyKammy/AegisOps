#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-7-2-canonical-namespace-bridge.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/control-plane" "${target}/docs/adr" "${target}/scripts"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
  cp -R "${repo_root}/control-plane/aegisops" \
    "${target}/control-plane/aegisops"
  mkdir -p "${target}/control-plane/tests"
  cp "${repo_root}/control-plane/tests/test_phase52_7_2_canonical_namespace_bridge.py" \
    "${target}/control-plane/tests/test_phase52_7_2_canonical_namespace_bridge.py"
  cp "${repo_root}/docs/adr/0017-phase-52-7-2-canonical-namespace-bridge.md" \
    "${target}/docs/adr/0017-phase-52-7-2-canonical-namespace-bridge.md"
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

missing_bridge_repo="${workdir}/missing-bridge"
create_valid_repo "${missing_bridge_repo}"
rm -rf "${missing_bridge_repo}/control-plane/aegisops"
assert_fails_with \
  "${missing_bridge_repo}" \
  "Missing Phase 52.7.2 canonical namespace bridge path: control-plane/aegisops/__init__.py"

broken_identity_repo="${workdir}/broken-identity"
create_valid_repo "${broken_identity_repo}"
cat >"${broken_identity_repo}/control-plane/aegisops/control_plane/__init__.py" <<'PY'
class AegisOpsControlPlaneService:
    pass

class AlertRecord:
    pass

class RuntimeConfig:
    pass

def build_runtime_service():
    return None
PY
assert_fails_with \
  "${broken_identity_repo}" \
  "Phase 52.7.2 canonical namespace bridge failed to load: module 'aegisops.control_plane' has no attribute '__all__'"

legacy_deleted_repo="${workdir}/legacy-deleted"
create_valid_repo "${legacy_deleted_repo}"
rm -rf "${legacy_deleted_repo}/control-plane/aegisops_control_plane"
assert_fails_with \
  "${legacy_deleted_repo}" \
  "Missing Phase 52.7.2 canonical namespace bridge path: control-plane/aegisops_control_plane/__init__.py"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/docs/adr/0017-phase-52-7-2-canonical-namespace-bridge.md"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.7.2 canonical namespace bridge: workstation-local absolute path detected"

echo "Phase 52.7.2 canonical namespace bridge verifier negative and valid fixtures passed."
