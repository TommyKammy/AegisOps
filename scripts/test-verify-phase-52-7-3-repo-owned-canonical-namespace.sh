#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-7-3-repo-owned-canonical-namespace.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p \
    "${target}/control-plane/aegisops/control_plane" \
    "${target}/control-plane/aegisops_control_plane/core" \
    "${target}/control-plane/tests" \
    "${target}/docs/adr" \
    "${target}/scripts"

  printf '"""Canonical bridge."""\nimport aegisops_control_plane as _legacy_control_plane\n' \
    >"${target}/control-plane/aegisops/control_plane/__init__.py"
  printf '"""Namespace package."""\n' >"${target}/control-plane/aegisops/__init__.py"
  printf '"""Legacy package."""\n' >"${target}/control-plane/aegisops_control_plane/__init__.py"
  printf 'LEGACY_IMPORT_ALIASES = {}\n' \
    >"${target}/control-plane/aegisops_control_plane/core/legacy_import_aliases.py"
  printf 'from aegisops.control_plane.service import build_runtime_service\n' \
    >"${target}/control-plane/main.py"
  printf 'from aegisops.control_plane.models import AlertRecord\n' \
    >"${target}/control-plane/tests/test_runtime.py"
  printf 'Legacy path `aegisops_control_plane.service` remains an approved bridge example.\n' \
    >"${target}/docs/adr/0017-phase-52-7-2-canonical-namespace-bridge.md"
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

legacy_python_repo="${workdir}/legacy-python"
create_valid_repo "${legacy_python_repo}"
printf 'from aegisops_control_plane.service import build_runtime_service\n' \
  >"${legacy_python_repo}/control-plane/tests/test_runtime.py"
assert_fails_with \
  "${legacy_python_repo}" \
  "control-plane/tests/test_runtime.py:1 imports aegisops_control_plane.service; use aegisops.control_plane.service"

legacy_text_repo="${workdir}/legacy-text"
create_valid_repo "${legacy_text_repo}"
printf 'Run `python3 -m aegisops_control_plane.cli`.\n' \
  >"${legacy_text_repo}/README.md"
assert_fails_with \
  "${legacy_text_repo}" \
  "README.md:1 mentions aegisops_control_plane; use aegisops.control_plane or document an approved compatibility exception"

legacy_docs_repo="${workdir}/legacy-docs"
create_valid_repo "${legacy_docs_repo}"
printf 'Run `python3 -m aegisops_control_plane.cli`.\n' \
  >"${legacy_docs_repo}/docs/runbook.md"
assert_fails_with \
  "${legacy_docs_repo}" \
  "docs/runbook.md:1 mentions aegisops_control_plane; use aegisops.control_plane or document an approved compatibility exception"

legacy_script_repo="${workdir}/legacy-script"
create_valid_repo "${legacy_script_repo}"
printf '#!/usr/bin/env bash\npython3 -m aegisops_control_plane.cli\n' \
  >"${legacy_script_repo}/scripts/run-control-plane.sh"
assert_fails_with \
  "${legacy_script_repo}" \
  "scripts/run-control-plane.sh:2 mentions aegisops_control_plane; use aegisops.control_plane or document an approved compatibility exception"

missing_bridge_repo="${workdir}/missing-bridge"
create_valid_repo "${missing_bridge_repo}"
rm -f "${missing_bridge_repo}/control-plane/aegisops/control_plane/__init__.py"
assert_fails_with \
  "${missing_bridge_repo}" \
  "Missing Phase 52.7.3 namespace cleanup prerequisite: control-plane/aegisops/control_plane/__init__.py"

echo "Phase 52.7.3 repo-owned canonical namespace verifier negative and valid fixtures passed."
