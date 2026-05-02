#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-6-2-canonical-domain-imports.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_fixture() {
  local target="$1"

  mkdir -p \
    "${target}/control-plane/aegisops_control_plane/actions" \
    "${target}/control-plane/aegisops_control_plane/api" \
    "${target}/control-plane/aegisops_control_plane/evidence" \
    "${target}/control-plane/aegisops_control_plane/ml_shadow" \
    "${target}/control-plane/tests" \
    "${target}/docs/adr" \
    "${target}/scripts"

  cat >"${target}/control-plane/aegisops_control_plane/action_policy.py" <<'EOF'
from .actions.action_policy import evaluate_action_policy_record
EOF

  cat >"${target}/control-plane/aegisops_control_plane/actions/action_policy.py" <<'EOF'
def evaluate_action_policy_record(record):
    return record
EOF

  cat >"${target}/control-plane/aegisops_control_plane/api/cli.py" <<'EOF'
def build_parser():
    return object()
EOF

  cat >"${target}/control-plane/main.py" <<'EOF'
from aegisops_control_plane.api import cli

def build():
    return cli.build_parser()
EOF

  cat >"${target}/control-plane/tests/test_canonical_imports.py" <<'EOF'
from aegisops_control_plane.actions.action_policy import evaluate_action_policy_record

def test_evaluate_action_policy_record():
    assert evaluate_action_policy_record({"id": "record-1"}) == {"id": "record-1"}
EOF

  cat >"${target}/control-plane/tests/test_phase29_shadow_scoring_validation.py" <<'EOF'
import aegisops_control_plane.phase29_shadow_scoring as legacy_shadow_scoring

def test_legacy_shadow_scoring_import_path_preserves_adapter_surface():
    assert legacy_shadow_scoring is not None
EOF

  cat >"${target}/docs/adr/0013-phase-52-5-2-package-scaffolding-and-compatibility-shim-policy.md" <<'EOF'
Legacy compatibility checks retain `aegisops_control_plane.action_policy`.
EOF
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
  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

passing_repo="${workdir}/passing"
create_fixture "${passing_repo}"
assert_passes "${passing_repo}"
if ! grep -F "approved legacy compatibility usage is limited to" "${pass_stdout}" >/dev/null; then
  echo "Expected passing output to report approved legacy usage." >&2
  cat "${pass_stdout}" >&2
  exit 1
fi

production_root_import_repo="${workdir}/production-root-import"
create_fixture "${production_root_import_repo}"
cat >"${production_root_import_repo}/control-plane/main.py" <<'EOF'
from aegisops_control_plane import cli

def build():
    return cli.build_parser()
EOF
assert_fails_with \
  "${production_root_import_repo}" \
  "control-plane/main.py:1 imports aegisops_control_plane.cli; use aegisops_control_plane.api.cli"

test_root_import_repo="${workdir}/test-root-import"
create_fixture "${test_root_import_repo}"
cat >"${test_root_import_repo}/control-plane/tests/test_canonical_imports.py" <<'EOF'
from aegisops_control_plane.action_policy import evaluate_action_policy_record

def test_evaluate_action_policy_record():
    assert evaluate_action_policy_record({"id": "record-1"}) == {"id": "record-1"}
EOF
assert_fails_with \
  "${test_root_import_repo}" \
  "control-plane/tests/test_canonical_imports.py:1 imports aegisops_control_plane.action_policy; use aegisops_control_plane.actions.action_policy"

doc_root_import_repo="${workdir}/doc-root-import"
create_fixture "${doc_root_import_repo}"
cat >"${doc_root_import_repo}/docs/operator-guide.md" <<'EOF'
Operators should import `aegisops_control_plane.action_policy` directly.
EOF
assert_fails_with \
  "${doc_root_import_repo}" \
  "docs/operator-guide.md:1 mentions a root compatibility import path"

echo "verify-phase-52-6-2-canonical-domain-imports tests passed"
