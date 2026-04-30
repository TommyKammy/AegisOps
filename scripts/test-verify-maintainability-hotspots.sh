#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-maintainability-hotspots.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"
  shift

  mkdir -p "${target}"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"

  mkdir -p "${target}/docs" "${target}/control-plane/aegisops_control_plane"
  printf '%s\n' \
    "# AegisOps Maintainability Decomposition Thresholds and Backlog Triggers" \
    "" \
    "## How To Interpret Verifier Output" \
    "" \
    "Verifier candidates are review prompts for responsibility growth, not automatic refactor instructions." \
    >"${target}/docs/maintainability-decomposition-thresholds.md"

  while (($#)); do
    local path="$1"
    local content="$2"
    shift 2

    mkdir -p "${target}/$(dirname "${path}")"
    printf '%s\n' "${content}" >"${target}/${path}"
  done

  git -C "${target}" add .
  git -C "${target}" commit -q -m "fixture"
}

append_repeated_lines() {
  local target="$1"
  local path="$2"
  local prefix="$3"
  local count="$4"

  for ((index = 1; index <= count; index++)); do
    printf '    %s_%03d = %d\n' "${prefix}" "${index}" "${index}" >>"${target}/${path}"
  done
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

single_responsibility_repo="${workdir}/single-responsibility"
create_repo \
  "${single_responsibility_repo}" \
  "control-plane/aegisops_control_plane/report_projection.py" "class ReportProjection:
    def render_summary(self):
        status = 'ready'
        snapshot = {'status': status}
        return snapshot"
append_repeated_lines "${single_responsibility_repo}" "control-plane/aegisops_control_plane/report_projection.py" "projection_line" 950
git -C "${single_responsibility_repo}" add .
git -C "${single_responsibility_repo}" commit -q -m "large single responsibility"
assert_passes "${single_responsibility_repo}"

baseline_repo="${workdir}/baseline"
create_repo \
  "${baseline_repo}" \
  "docs/maintainability-hotspot-baseline.txt" "control-plane/aegisops_control_plane/service.py max_lines=960 max_effective_lines=960 max_facade_methods=1 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003" \
  "control-plane/aegisops_control_plane/service.py" "class AegisOpsControlPlaneService:
    def describe_runtime(self):
        auth_principal = 'trusted-runtime-boundary'
        queue_status = {'operator': auth_principal}
        case_transition = queue_status
        assistant_recommendation = case_transition
        action_reconciliation = assistant_recommendation
        restore_backup_export = action_reconciliation
        evidence_admission = restore_backup_export
        return evidence_admission"
append_repeated_lines "${baseline_repo}" "control-plane/aegisops_control_plane/service.py" "mixed_line" 950
git -C "${baseline_repo}" add .
git -C "${baseline_repo}" commit -q -m "known hotspot baseline"
assert_passes "${baseline_repo}"
if ! grep -F "Known maintainability hotspot baseline remains present" "${pass_stdout}" >/dev/null; then
  echo "Expected pass output to report the known baseline hotspot." >&2
  cat "${pass_stdout}" >&2
  exit 1
fi
if ! grep -F "AegisOpsControlPlaneService methods=1" "${pass_stdout}" >/dev/null; then
  echo "Expected pass output to report the facade method count." >&2
  cat "${pass_stdout}" >&2
  exit 1
fi

regrowth_repo="${workdir}/regrowth"
create_repo \
  "${regrowth_repo}" \
  "docs/maintainability-hotspot-baseline.txt" "control-plane/aegisops_control_plane/service.py max_lines=959 max_effective_lines=959 max_facade_methods=0 facade_class=RenamedControlPlaneService adr_exception=ADR-0003" \
  "control-plane/aegisops_control_plane/service.py" "class RenamedControlPlaneService:
    def describe_runtime(self):
        auth_principal = 'trusted-runtime-boundary'
        queue_status = {'operator': auth_principal}
        case_transition = queue_status
        assistant_recommendation = case_transition
        action_reconciliation = assistant_recommendation
        restore_backup_export = action_reconciliation
        evidence_admission = restore_backup_export
        return evidence_admission"
append_repeated_lines "${regrowth_repo}" "control-plane/aegisops_control_plane/service.py" "mixed_line" 950
git -C "${regrowth_repo}" add .
git -C "${regrowth_repo}" commit -q -m "hotspot growth past baseline"
assert_fails_with "${regrowth_repo}" "Maintainability hotspot baseline limits were exceeded"
if ! grep -F "lines=960 exceeds max_lines=959" "${fail_stderr}" >/dev/null; then
  echo "Expected failure output to report the line-count limit." >&2
  cat "${fail_stderr}" >&2
  exit 1
fi
if ! grep -F "effective_lines=960 exceeds max_effective_lines=959" "${fail_stderr}" >/dev/null; then
  echo "Expected failure output to report the effective-line limit." >&2
  cat "${fail_stderr}" >&2
  exit 1
fi
if ! grep -F "max_facade_methods=0" "${fail_stderr}" >/dev/null; then
  echo "Expected failure output to report the facade method limit." >&2
  cat "${fail_stderr}" >&2
  exit 1
fi
if ! grep -F "RenamedControlPlaneService methods=1" "${fail_stderr}" >/dev/null; then
  echo "Expected failure output to report the configured successor facade class." >&2
  cat "${fail_stderr}" >&2
  exit 1
fi

phase50_11_regrowth_repo="${workdir}/phase50-11-regrowth"
create_repo \
  "${phase50_11_regrowth_repo}" \
  "docs/maintainability-hotspot-baseline.txt" "control-plane/aegisops_control_plane/service.py max_lines=1773 max_effective_lines=1589 max_facade_methods=125 facade_class=AegisOpsControlPlaneService adr_exception=ADR-0003 phase=50.12.2 issue=#1017" \
  "control-plane/aegisops_control_plane/service.py" "class AegisOpsControlPlaneService:
    def describe_runtime(self):
        auth_principal = 'trusted-runtime-boundary'
        queue_status = {'operator': auth_principal}
        case_transition = queue_status
        assistant_recommendation = case_transition
        action_reconciliation = assistant_recommendation
        restore_backup_export = action_reconciliation
        evidence_admission = restore_backup_export
        return evidence_admission"
append_repeated_lines "${phase50_11_regrowth_repo}" "control-plane/aegisops_control_plane/service.py" "phase50_11_growth_line" 1764
git -C "${phase50_11_regrowth_repo}" add .
git -C "${phase50_11_regrowth_repo}" commit -q -m "phase 50.11 regrowth past accepted closeout"
assert_fails_with "${phase50_11_regrowth_repo}" "Maintainability hotspot baseline limits were exceeded"
if ! grep -F "lines=1774 exceeds max_lines=1773" "${fail_stderr}" >/dev/null; then
  echo "Expected failure output to report the Phase 50.11 line-count limit." >&2
  cat "${fail_stderr}" >&2
  exit 1
fi
if ! grep -F "effective_lines=1774 exceeds max_effective_lines=1589" "${fail_stderr}" >/dev/null; then
  echo "Expected failure output to report the Phase 50.11 effective-line limit." >&2
  cat "${fail_stderr}" >&2
  exit 1
fi

new_hotspot_repo="${workdir}/new-hotspot"
create_repo \
  "${new_hotspot_repo}" \
  "control-plane/aegisops_control_plane/new_facade.py" "class NewFacade:
    def expand(self):
        auth_principal = 'trusted-runtime-boundary'
        operator_detail_snapshot = {'principal': auth_principal}
        case_lifecycle_transition = operator_detail_snapshot
        assistant_advisory_recommendation = case_lifecycle_transition
        action_approval_reconciliation = assistant_advisory_recommendation
        restore_readiness_export = action_approval_reconciliation
        evidence_ingest_admission = restore_readiness_export
        return evidence_ingest_admission"
append_repeated_lines "${new_hotspot_repo}" "control-plane/aegisops_control_plane/new_facade.py" "mixed_line" 950
git -C "${new_hotspot_repo}" add .
git -C "${new_hotspot_repo}" commit -q -m "new hotspot"
assert_fails_with "${new_hotspot_repo}" "docs/maintainability-decomposition-thresholds.md"
if ! grep -F "control-plane/aegisops_control_plane/new_facade.py" "${fail_stderr}" >/dev/null; then
  echo "Expected failure output to name the hotspot candidate." >&2
  cat "${fail_stderr}" >&2
  exit 1
fi

nested_hotspot_repo="${workdir}/nested-hotspot"
create_repo \
  "${nested_hotspot_repo}" \
  "control-plane/aegisops_control_plane/facades/operator_facade.py" "class OperatorFacade:
    def expand(self):
        auth_principal = 'trusted-runtime-boundary'
        operator_detail_snapshot = {'principal': auth_principal}
        case_lifecycle_transition = operator_detail_snapshot
        assistant_advisory_recommendation = case_lifecycle_transition
        action_approval_reconciliation = assistant_advisory_recommendation
        restore_readiness_export = action_approval_reconciliation
        evidence_ingest_admission = restore_readiness_export
        return evidence_ingest_admission"
append_repeated_lines "${nested_hotspot_repo}" "control-plane/aegisops_control_plane/facades/operator_facade.py" "mixed_line" 950
git -C "${nested_hotspot_repo}" add .
git -C "${nested_hotspot_repo}" commit -q -m "nested hotspot"
assert_fails_with "${nested_hotspot_repo}" "control-plane/aegisops_control_plane/facades/operator_facade.py"

missing_doc_repo="${workdir}/missing-doc"
create_repo \
  "${missing_doc_repo}" \
  "control-plane/aegisops_control_plane/small.py" "class Small:
    pass"
rm "${missing_doc_repo}/docs/maintainability-decomposition-thresholds.md"
git -C "${missing_doc_repo}" add -A
git -C "${missing_doc_repo}" commit -q -m "missing doc"
assert_fails_with "${missing_doc_repo}" "Missing maintainability decomposition threshold document"

echo "verify-maintainability-hotspots tests passed"
