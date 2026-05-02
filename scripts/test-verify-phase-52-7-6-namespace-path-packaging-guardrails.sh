#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-7-6-namespace-path-packaging-guardrails.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo_copy() {
  local target="$1"

  mkdir -p "${target}/control-plane" "${target}/docs/adr" "${target}/scripts" "${target}/.github/workflows"
  cp -R "${repo_root}/control-plane/aegisops" "${target}/control-plane/aegisops"
  cp -R "${repo_root}/control-plane/aegisops_control_plane" "${target}/control-plane/aegisops_control_plane"
  cp "${repo_root}/control-plane/main.py" "${target}/control-plane/main.py"
  cp -R "${repo_root}/control-plane/tests" "${target}/control-plane/tests"
  cp "${repo_root}/docs/adr/0018-phase-52-7-6-namespace-path-packaging-guardrails.md" \
    "${target}/docs/adr/0018-phase-52-7-6-namespace-path-packaging-guardrails.md"
  cp -R "${repo_root}/docs/adr" "${target}/docs"
  cp "${repo_root}/docs/phase-52-5-closeout-evaluation.md" "${target}/docs/phase-52-5-closeout-evaluation.md"
  cp "${repo_root}/docs/phase-52-6-closeout-evaluation.md" "${target}/docs/phase-52-6-closeout-evaluation.md"
  cp "${repo_root}/scripts/verify-phase-52-5-1-control-plane-layout-inventory-contract.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-5-2-import-compatibility.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-5-2-layout-guardrail.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-5-2-package-scaffolding.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-6-1-root-shim-inventory-contract.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-6-2-canonical-domain-imports.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-6-3-legacy-import-alias-registry.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-6-5-retire-phase29-root-filenames.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-6-6-root-package-guardrails.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-7-1-namespace-layout-inventory-contract.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-7-2-canonical-namespace-bridge.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-7-3-repo-owned-canonical-namespace.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-7-4-physical-layout-migration.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-7-5-root-shim-reduction.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-phase-52-7-6-namespace-path-packaging-guardrails.sh" "${target}/scripts/"
  cp "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${target}/scripts/"
  cp "${repo_root}"/scripts/test-verify-phase-52-{5,6,7}-*.sh "${target}/scripts/" 2>/dev/null || true
  cp "${repo_root}/.github/workflows/ci.yml" "${target}/.github/workflows/ci.yml"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
  git -C "${target}" add .
  git -C "${target}" commit -q -m "fixture"
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
create_repo_copy "${valid_repo}"
assert_passes "${valid_repo}"

legacy_impl_file_repo="${workdir}/legacy-implementation-file"
create_repo_copy "${legacy_impl_file_repo}"
printf '%s\n' '"""Stale legacy implementation file."""' \
  >"${legacy_impl_file_repo}/control-plane/aegisops_control_plane/service.py"
assert_fails_with \
  "${legacy_impl_file_repo}" \
  "Phase 52.7.6 guardrail rejected legacy implementation files: __init__.py, service.py"

canonical_root_growth_repo="${workdir}/canonical-root-growth"
create_repo_copy "${canonical_root_growth_repo}"
printf '%s\n' '"""Unclassified canonical root file."""' \
  >"${canonical_root_growth_repo}/control-plane/aegisops/control_plane/new_root_owner.py"
assert_fails_with \
  "${canonical_root_growth_repo}" \
  "Phase 52.7.6 guardrail expected canonical root files"

legacy_guidance_repo="${workdir}/legacy-guidance"
create_repo_copy "${legacy_guidance_repo}"
printf '%s\n' 'New implementation files belong under `control-plane/aegisops_control_plane/`.' \
  >"${legacy_guidance_repo}/docs/new-guidance.md"
git -C "${legacy_guidance_repo}" add docs/new-guidance.md
git -C "${legacy_guidance_repo}" commit -q -m "add stale guidance"
assert_fails_with \
  "${legacy_guidance_repo}" \
  "docs/new-guidance.md:1 points implementation guidance at control-plane/aegisops_control_plane/"

legacy_import_repo="${workdir}/legacy-import"
create_repo_copy "${legacy_import_repo}"
printf '%s\n' 'from aegisops_control_plane.service import build_runtime_service' \
  >"${legacy_import_repo}/control-plane/tests/test_new_runtime_import.py"
assert_fails_with \
  "${legacy_import_repo}" \
  "control-plane/tests/test_new_runtime_import.py:1 imports aegisops_control_plane.service; use aegisops.control_plane.service"

workstation_path_repo="${workdir}/workstation-path"
create_repo_copy "${workstation_path_repo}"
printf 'Use /%s/example/AegisOps for setup.\n' "Users" \
  >>"${workstation_path_repo}/docs/adr/0018-phase-52-7-6-namespace-path-packaging-guardrails.md"
assert_fails_with \
  "${workstation_path_repo}" \
  "Forbidden Phase 52.7.6 guardrail artifact: workstation-local absolute path detected"

echo "Phase 52.7.6 namespace/path packaging guardrail verifier negative and valid fixtures passed."
