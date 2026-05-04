#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-57-r-supportability-pre-refactor-boundary.sh"
contract_path="docs/adr/0019-phase-57-r-supportability-pre-refactor-boundary.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p \
    "${target}/docs/adr" \
    "${target}/docs/deployment" \
    "${target}/apps/operator-ui/src/app/operatorConsolePages" \
    "${target}/apps/operator-ui/src/auth" \
    "${target}/control-plane/aegisops/control_plane/runtime" \
    "${target}/control-plane/aegisops/control_plane/api" \
    "${target}/control-plane/tests" \
    "${target}/scripts"

  cp "${repo_root}/${contract_path}" "${target}/${contract_path}"

  for required_file in \
    "docs/phase-57-closeout-evaluation.md" \
    "docs/maintainability-decomposition-thresholds.md" \
    "docs/maintainability-hotspot-baseline.txt" \
    "docs/phase-50-maintainability-closeout.md" \
    "docs/deployment/restore-rollback-upgrade-evidence-rehearsal.md" \
    "docs/deployment/support-playbook-break-glass-rehearsal.md" \
    "docs/phase-51-4-smb-personas-jobs-to-be-done.md" \
    "apps/operator-ui/src/app/OperatorRoutes.tsx" \
    "apps/operator-ui/src/app/OperatorShell.tsx" \
    "apps/operator-ui/src/app/operatorConsolePages/adminPages.tsx" \
    "apps/operator-ui/src/auth/roleMatrix.ts" \
    "apps/operator-ui/src/auth/session.ts" \
    "apps/operator-ui/src/auth/navigation.ts" \
    "control-plane/aegisops/control_plane/runtime/restore_readiness.py" \
    "control-plane/aegisops/control_plane/runtime/restore_readiness_backup_restore.py" \
    "control-plane/aegisops/control_plane/runtime/restore_readiness_projection.py" \
    "control-plane/aegisops/control_plane/runtime/runtime_restore_readiness_diagnostics.py" \
    "control-plane/aegisops/control_plane/runtime/readiness_operability.py" \
    "control-plane/aegisops/control_plane/runtime/readiness_contracts.py" \
    "control-plane/aegisops/control_plane/runtime/runtime_boundary.py" \
    "control-plane/aegisops/control_plane/api/http_runtime_surface.py" \
    "control-plane/aegisops/control_plane/api/entrypoint_support.py" \
    "control-plane/aegisops/control_plane/service.py" \
    "control-plane/aegisops/control_plane/service_composition.py" \
    "control-plane/tests/test_service_persistence_restore_readiness.py" \
    "control-plane/tests/test_phase37_reviewed_record_chain_rehearsal.py" \
    "control-plane/tests/test_phase57_7_ai_enablement_admin_toggle.py" \
    "control-plane/tests/test_service_boundary_refactor_regression_validation.py" \
    "control-plane/tests/test_support_package.py" \
    "scripts/verify-maintainability-hotspots.sh" \
    "scripts/test-verify-maintainability-hotspots.sh"; do
    mkdir -p "${target}/$(dirname "${required_file}")"
    if [[ -f "${repo_root}/${required_file}" ]]; then
      cp "${repo_root}/${required_file}" "${target}/${required_file}"
    else
      : >"${target}/${required_file}"
    fi
  done
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

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/${contract_path}"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 57.R supportability pre-refactor boundary ADR: ${contract_path}"

missing_inventory_repo="${workdir}/missing-inventory"
create_valid_repo "${missing_inventory_repo}"
perl -0pi -e 's/^\| Restore\/readiness runtime \|.*\n//m' \
  "${missing_inventory_repo}/${contract_path}"
assert_fails_with \
  "${missing_inventory_repo}" \
  'Missing Phase 57.R ADR statement: `control-plane/aegisops/control_plane/runtime/restore_readiness.py`'

missing_order_repo="${workdir}/missing-order"
create_valid_repo "${missing_order_repo}"
perl -0pi -e 's/^\| 57\.R\.3 \|.*\n//m' \
  "${missing_order_repo}/${contract_path}"
assert_fails_with \
  "${missing_order_repo}" \
  "Missing Phase 57.R ADR statement: | 57.R.3 | #1227 Extract backup / restore payload codec and validation boundaries | Runtime extraction only. | #1225 |"

missing_rollback_repo="${workdir}/missing-rollback"
create_valid_repo "${missing_rollback_repo}"
perl -0pi -e 's/Revert the extracted codec and validation modules to the current restore\/readiness runtime files without changing public facade or persisted records\.//g' \
  "${missing_rollback_repo}/${contract_path}"
assert_fails_with \
  "${missing_rollback_repo}" \
  "Missing Phase 57.R ADR statement: Revert the extracted codec and validation modules to the current restore/readiness runtime files without changing public facade or persisted records."

overclaim_repo="${workdir}/phase58-overclaim"
create_valid_repo "${overclaim_repo}"
printf '%s\n' "Phase 58 supportability is complete" >>"${overclaim_repo}/${contract_path}"
assert_fails_with \
  "${overclaim_repo}" \
  "Forbidden Phase 57.R ADR claim: Phase 58 supportability is complete"

restore_weakening_repo="${workdir}/restore-weakening"
create_valid_repo "${restore_weakening_repo}"
printf '%s\n' "This refactor weakens restore validation" >>"${restore_weakening_repo}/${contract_path}"
assert_fails_with \
  "${restore_weakening_repo}" \
  "Forbidden Phase 57.R ADR claim: This refactor weakens restore validation"

admin_crud_repo="${workdir}/admin-crud"
create_valid_repo "${admin_crud_repo}"
printf '%s\n' "This refactor approves admin CRUD expansion" >>"${admin_crud_repo}/${contract_path}"
assert_fails_with \
  "${admin_crud_repo}" \
  "Forbidden Phase 57.R ADR claim: This refactor approves admin CRUD expansion"

projection_authority_repo="${workdir}/projection-authority"
create_valid_repo "${projection_authority_repo}"
printf '%s\n' "Supportability projections are authoritative restore truth" >>"${projection_authority_repo}/${contract_path}"
assert_fails_with \
  "${projection_authority_repo}" \
  "Forbidden Phase 57.R ADR claim: Supportability projections are authoritative restore truth"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" >>"${local_path_repo}/${contract_path}"
assert_fails_with \
  "${local_path_repo}" \
  "Forbidden Phase 57.R ADR: workstation-local absolute path detected"

missing_referenced_file_repo="${workdir}/missing-referenced-file"
create_valid_repo "${missing_referenced_file_repo}"
rm "${missing_referenced_file_repo}/control-plane/aegisops/control_plane/runtime/restore_readiness.py"
assert_fails_with \
  "${missing_referenced_file_repo}" \
  "Phase 57.R ADR inventory references missing file: control-plane/aegisops/control_plane/runtime/restore_readiness.py"

echo "Phase 57.R supportability pre-refactor boundary verifier negative and valid fixtures passed."
