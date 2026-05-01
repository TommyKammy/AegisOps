#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-52-5-9-service-facade-freeze.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_fixture() {
  local target="$1"

  mkdir -p \
    "${target}/control-plane/aegisops_control_plane/actions/review" \
    "${target}/control-plane/aegisops_control_plane/actions" \
    "${target}/docs"

  cat >"${target}/docs/maintainability-hotspot-baseline.txt" <<'EOF'
control-plane/aegisops_control_plane/service.py max_lines=1393 max_effective_lines=1241 max_facade_methods=95 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.13.5 issue=#1035
EOF

  cat >"${target}/docs/control-plane-service-internal-boundaries.md" <<'EOF'
## 11. Phase 52.5 Facade Freeze And Package Import Rule

No new implementation-heavy behavior belongs in `service.py` after Phase 52.5.
Internal control-plane modules must import moved implementation owners from their domain packages.
Compatibility shims are for public or legacy callers, not for package-internal dependency direction.
Run `bash scripts/verify-phase-52-5-9-service-facade-freeze.sh`.
EOF

  cat >"${target}/control-plane/aegisops_control_plane/service.py" <<'EOF'
class AegisOpsControlPlaneService:
    def describe_runtime(self):
        return "ok"
EOF

  cat >"${target}/control-plane/aegisops_control_plane/actions/action_policy.py" <<'EOF'
def evaluate_action_policy_record(record):
    return record
EOF

  cat >"${target}/control-plane/aegisops_control_plane/action_policy.py" <<'EOF'
from .actions.action_policy import evaluate_action_policy_record

__all__ = ["evaluate_action_policy_record"]
EOF

  cat >"${target}/control-plane/aegisops_control_plane/actions/review/action_review_write_surface.py" <<'EOF'
from ..action_policy import evaluate_action_policy_record

def evaluate(record):
    return evaluate_action_policy_record(record)
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
if ! grep -F "domain package internals avoid legacy compatibility shims" "${pass_stdout}" >/dev/null; then
  echo "Expected passing output to report internal import cleanup." >&2
  cat "${pass_stdout}" >&2
  exit 1
fi

legacy_import_repo="${workdir}/legacy-import"
create_fixture "${legacy_import_repo}"
perl -0pi -e 's/from \.\.action_policy import evaluate_action_policy_record/from ...action_policy import evaluate_action_policy_record/' \
  "${legacy_import_repo}/control-plane/aegisops_control_plane/actions/review/action_review_write_surface.py"
assert_fails_with "${legacy_import_repo}" "imports aegisops_control_plane.action_policy; use aegisops_control_plane.actions.action_policy"

service_growth_repo="${workdir}/service-growth"
create_fixture "${service_growth_repo}"
for index in $(seq 1 1393); do
  printf 'growth_line_%04d = %d\n' "${index}" "${index}" \
    >>"${service_growth_repo}/control-plane/aegisops_control_plane/service.py"
done
assert_fails_with "${service_growth_repo}" "rejects service.py growth beyond the accepted Phase 50.13.5 ceiling"

missing_doc_repo="${workdir}/missing-doc"
create_fixture "${missing_doc_repo}"
perl -0pi -e 's/Compatibility shims are for public or legacy callers, not for package-internal dependency direction\.\n//' \
  "${missing_doc_repo}/docs/control-plane-service-internal-boundaries.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 52.5.9 service facade freeze guidance"

echo "verify-phase-52-5-9-service-facade-freeze tests passed"
