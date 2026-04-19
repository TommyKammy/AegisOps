#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"
phase_validation_step_name="Run Phase 23 authority-closure validation"
phase_coverage_guard_step_name="Run Phase 23 workflow coverage guard"
phase_coverage_guard_command="bash scripts/test-verify-ci-phase-23-workflow-coverage.sh"
e2e_test="${repo_root}/control-plane/tests/test_phase23_end_to_end_validation.py"
approval_test="${repo_root}/control-plane/tests/test_phase23_approval_surface_validation.py"
transition_test="${repo_root}/control-plane/tests/test_phase23_transition_logging_validation.py"
substrate_test="${repo_root}/control-plane/tests/test_phase23_substrate_simplification_validation.py"
workflow_guard="${repo_root}/scripts/test-verify-ci-phase-23-workflow-coverage.sh"
shell_test="${repo_root}/scripts/test-verify-phase-23-authority-closure.sh"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_line() {
  local path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${path}" >/dev/null; then
    echo "Missing required line in ${path}: ${expected}" >&2
    exit 1
  fi
}

require_file "${e2e_test}" "Missing Phase 23 end-to-end validation unittest"
require_file "${approval_test}" "Missing Phase 23 approval surface validation unittest"
require_file "${transition_test}" "Missing Phase 23 transition logging validation unittest"
require_file "${substrate_test}" "Missing Phase 23 substrate simplification validation unittest"
require_file "${workflow_guard}" "Missing Phase 23 workflow coverage guard"
require_file "${shell_test}" "Missing Phase 23 authority-closure shell test"
require_file "${workflow_path}" "Missing CI workflow"

require_fixed_line "${e2e_test}" "class Phase23EndToEndValidationTests(unittest.TestCase):"
require_fixed_line "${e2e_test}" "    def test_phase23_end_to_end_live_grant_keeps_transition_history_and_degraded_visibility_explicit("
require_fixed_line "${e2e_test}" '            ["pending_approval", "approved"],'
require_fixed_line "${e2e_test}" '            "reviewed_delegation_missing_after_approval",'
require_fixed_line "${approval_test}" "class Phase23ApprovalSurfaceValidationTests(unittest.TestCase):"
require_fixed_line "${approval_test}" "    def test_reviewed_runtime_path_records_live_grant_decision(self) -> None:"
require_fixed_line "${approval_test}" "    def test_reviewed_runtime_path_rejects_self_approval(self) -> None:"
require_fixed_line "${transition_test}" "class Phase23TransitionLoggingValidationTests(ServicePersistenceTestBase):"
require_fixed_line "${transition_test}" "    def test_transition_logging_rolls_back_current_state_when_append_only_save_fails("
require_fixed_line "${transition_test}" "    def test_transition_logging_rejects_current_state_drift_from_authoritative_history("
require_fixed_line "${substrate_test}" "class Phase23SubstrateSimplificationValidationTests(unittest.TestCase):"
require_fixed_line "${substrate_test}" "    def test_reviewed_security_mainline_declares_shuffle_as_single_routine_substrate("

require_fixed_line "${workflow_path}" "      - name: Run Phase 23 authority-closure validation"
require_fixed_line "${workflow_path}" "      - name: Run Phase 23 workflow coverage guard"
require_fixed_line "${workflow_path}" "        run: bash scripts/test-verify-ci-phase-23-workflow-coverage.sh"

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"

active_run_commands="$(collect_active_run_commands)"
phase_validation_commands="$(extract_step_run_commands "${phase_validation_step_name}")"

if [[ -z "${phase_validation_commands}" ]]; then
  echo "Missing CI workflow step commands for ${phase_validation_step_name}" >&2
  exit 1
fi

for command in \
  "bash scripts/verify-phase-23-authority-closure.sh" \
  "python3 -m unittest control-plane.tests.test_phase23_end_to_end_validation control-plane.tests.test_phase23_approval_surface_validation control-plane.tests.test_phase23_transition_logging_validation control-plane.tests.test_phase23_substrate_simplification_validation"
do
  if ! grep -Fqx -- "${command}" <<<"${phase_validation_commands}" >/dev/null; then
    echo "Missing required Phase 23 validation command in ${phase_validation_step_name}: ${command}" >&2
    exit 1
  fi
done

if ! grep -Fqx -- "bash scripts/test-verify-phase-23-authority-closure.sh" <<<"${active_run_commands}" >/dev/null; then
  echo "Missing required Phase 23 focused shell test command in CI workflow: bash scripts/test-verify-phase-23-authority-closure.sh" >&2
  exit 1
fi

phase_coverage_guard_commands="$(extract_step_run_commands "${phase_coverage_guard_step_name}")"
if [[ -z "${phase_coverage_guard_commands}" ]]; then
  echo "Missing dedicated Phase 23 workflow coverage guard step in CI workflow: ${phase_coverage_guard_step_name}" >&2
  exit 1
fi

if [[ "$(printf '%s\n' "${phase_coverage_guard_commands}")" != "${phase_coverage_guard_command}" ]]; then
  echo "Dedicated Phase 23 workflow coverage guard step must run exactly: ${phase_coverage_guard_command}" >&2
  echo "Found:" >&2
  printf '%s\n' "${phase_coverage_guard_commands}" >&2
  exit 1
fi

echo "Phase 23 authority-closure validation artifacts and CI wiring are present and aligned."
