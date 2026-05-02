#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh"
contract_path="docs/adr/0015-phase-52-6-3-legacy-import-alias-registry.md"
registry_path="control-plane/aegisops/control_plane/core/legacy_import_aliases.py"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/adr" "${target}/control-plane"
  cp "${repo_root}/${contract_path}" "${target}/${contract_path}"
  cp -R "${repo_root}/control-plane/aegisops" \
    "${target}/control-plane/aegisops"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    cat "${fail_stdout}" >&2
    exit 1
  fi

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_owner_repo="${workdir}/missing-owner"
create_valid_repo "${missing_owner_repo}"
perl -0pi -e 's/"reporting\/audit_export\.py"/""/' \
  "${missing_owner_repo}/${registry_path}"
assert_fails_with \
  "${missing_owner_repo}" \
  "Phase 52.6.3 legacy import alias registry failed to load: legacy import alias missing owner"

missing_alias_repo="${workdir}/missing-alias"
create_valid_repo "${missing_alias_repo}"
perl -0pi -e 's/LEGACY_IMPORT_ALIASES: dict\[str, LegacyImportAlias\] = \{.*?\n\}\n/LEGACY_IMPORT_ALIASES: dict[str, LegacyImportAlias] = {}\n/s' \
  "${missing_alias_repo}/${registry_path}"
assert_fails_with \
  "${missing_alias_repo}" \
  "Phase 52.6.3 legacy import alias registry missing approved alias: aegisops_control_plane.audit_export"

restored_physical_shim_repo="${workdir}/restored-physical-shim"
create_valid_repo "${restored_physical_shim_repo}"
printf '%s\n' '"""Unexpected restored audit export shim."""' \
  >"${restored_physical_shim_repo}/control-plane/aegisops_control_plane/audit_export.py"
assert_fails_with \
  "${restored_physical_shim_repo}" \
  "Phase 52.6.3 proof-of-pattern root shim should be removed: control-plane/aegisops_control_plane/audit_export.py"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${local_path_repo}/${contract_path}"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 52.6.3 legacy import alias registry: workstation-local absolute path detected"

behavior_drift_repo="${workdir}/behavior-drift"
create_valid_repo "${behavior_drift_repo}"
python3 - <<'PY' "${behavior_drift_repo}/${registry_path}"
from pathlib import Path
import sys

path = Path(sys.argv[1])
text = path.read_text()
text = text.replace(
    "        target = importlib.import_module(self._target_name)\n",
    "        from types import ModuleType\n"
    "        proxy = ModuleType(self._alias_name)\n"
    "        proxy.export_audit_retention_baseline = object()\n"
    "        target = proxy\n",
)
path.write_text(text)
PY
assert_fails_with \
  "${behavior_drift_repo}" \
  "Phase 52.6.3 legacy import alias changed module identity for aegisops_control_plane.audit_export"

echo "Phase 52.6.3 legacy import alias registry verifier negative and valid fixtures passed."
