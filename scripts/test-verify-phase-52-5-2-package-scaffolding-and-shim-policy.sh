#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
scaffold_verifier="${repo_root}/scripts/verify-phase-52-5-2-package-scaffolding.sh"
import_verifier="${repo_root}/scripts/verify-phase-52-5-2-import-compatibility.sh"
guardrail_verifier="${repo_root}/scripts/verify-phase-52-5-2-layout-guardrail.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/adr" "${target}/control-plane"
  cp "${repo_root}/docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md" \
    "${target}/docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md"
  cp "${repo_root}/docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md" \
    "${target}/docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" \
    "${target}/control-plane/aegisops_control_plane"
}

assert_passes() {
  local verifier="$1"
  local target="$2"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local verifier="$1"
  local target="$2"
  local expected="$3"

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
assert_passes "${scaffold_verifier}" "${valid_repo}"
assert_passes "${import_verifier}" "${valid_repo}"
assert_passes "${guardrail_verifier}" "${valid_repo}"

missing_scaffold_repo="${workdir}/missing-scaffold"
create_valid_repo "${missing_scaffold_repo}"
rm -rf "${missing_scaffold_repo}/control-plane/aegisops_control_plane/evidence"
assert_fails_with \
  "${scaffold_verifier}" \
  "${missing_scaffold_repo}" \
  "Missing Phase 52.5.2 target package scaffold: control-plane/aegisops_control_plane/evidence"

bypassed_legacy_import_repo="${workdir}/bypassed-legacy-import"
create_valid_repo "${bypassed_legacy_import_repo}"
perl -0pi -e 's/aegisops_control_plane\.service:AegisOpsControlPlaneService/aegisops_control_plane.core.service:AegisOpsControlPlaneService/g' \
  "${bypassed_legacy_import_repo}/docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md"
assert_fails_with \
  "${import_verifier}" \
  "${bypassed_legacy_import_repo}" \
  "Missing Phase 52.5.2 documented legacy import compatibility check: aegisops_control_plane.service:AegisOpsControlPlaneService"

missing_control_plane_root_repo="${workdir}/missing-control-plane-root"
create_valid_repo "${missing_control_plane_root_repo}"
rm -rf "${missing_control_plane_root_repo}/control-plane"
assert_fails_with \
  "${import_verifier}" \
  "${missing_control_plane_root_repo}" \
  "Missing or unreadable Phase 52.5.2 control-plane root for import compatibility verifier:"

unclassified_flat_module_repo="${workdir}/unclassified-flat-module"
create_valid_repo "${unclassified_flat_module_repo}"
printf '%s\n' "\"\"\"Unclassified root-level fixture module.\"\"\"" \
  >"${unclassified_flat_module_repo}/control-plane/aegisops_control_plane/new_flat_module.py"
assert_fails_with \
  "${guardrail_verifier}" \
  "${unclassified_flat_module_repo}" \
  "Phase 52.5.2 layout guardrail found unclassified flat root-level modules: new_flat_module.py"

phase_numbered_production_repo="${workdir}/phase-numbered-production-module"
create_valid_repo "${phase_numbered_production_repo}"
printf '%s\n' "\"\"\"Phase-numbered production fixture module.\"\"\"" \
  >"${phase_numbered_production_repo}/control-plane/aegisops_control_plane/phase52_new_owner.py"
cat >>"${phase_numbered_production_repo}/docs/adr/0012-phase-52-5-1-control-plane-layout-inventory-and-migration-contract.md" <<'EOF'
| `phase52_new_owner.py` | `core` | Owns fixture behavior and should fail the phase-numbered production guardrail. |
EOF
assert_fails_with \
  "${guardrail_verifier}" \
  "${phase_numbered_production_repo}" \
  "Phase 52.5.2 layout guardrail found phase-numbered production modules without compatibility-shim classification: phase52_new_owner.py"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Evidence: /%s/example/AegisOps/package-policy.md\n' "Users" \
  >>"${local_path_repo}/docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md"
assert_fails_with \
  "${scaffold_verifier}" \
  "${local_path_repo}" \
  "Forbidden Phase 52.5.2 package scaffolding policy: workstation-local absolute path detected"

echo "Phase 52.5.2 package scaffolding, import compatibility, and layout guardrail verifier tests passed."
