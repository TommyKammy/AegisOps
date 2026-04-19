#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"
phase_validation_step_name="Run Phase 26 ticket coordination validation"
phase_coverage_guard_step_name="Run Phase 26 workflow coverage guard"
phase_coverage_guard_command="bash scripts/test-verify-ci-phase-26-workflow-coverage.sh"
e2e_test="${repo_root}/control-plane/tests/test_phase26_end_to_end_validation.py"
coordination_doc_test="${repo_root}/control-plane/tests/test_phase26_coordination_substrate_boundary_docs.py"
soft_write_doc_test="${repo_root}/control-plane/tests/test_phase26_create_tracking_ticket_soft_write_contract_docs.py"
workflow_guard="${repo_root}/scripts/test-verify-ci-phase-26-workflow-coverage.sh"
shell_test="${repo_root}/scripts/test-verify-phase-26-ticket-coordination-validation.sh"

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

require_file "${e2e_test}" "Missing Phase 26 end-to-end validation unittest"
require_file "${coordination_doc_test}" "Missing Phase 26 coordination substrate doc unittest"
require_file "${soft_write_doc_test}" "Missing Phase 26 soft-write contract doc unittest"
require_file "${workflow_guard}" "Missing Phase 26 workflow coverage guard"
require_file "${shell_test}" "Missing Phase 26 ticket coordination shell test"
require_file "${workflow_path}" "Missing CI workflow"

require_fixed_line "${e2e_test}" "class Phase26EndToEndValidationTests(unittest.TestCase):"
require_fixed_line "${e2e_test}" "    def test_phase26_end_to_end_surfaces_link_first_ticket_reference_without_authority_drift("
require_fixed_line "${e2e_test}" "    def test_phase26_end_to_end_surfaces_create_tracking_ticket_created_outcome("
require_fixed_line "${e2e_test}" "    def test_phase26_end_to_end_fail_closes_missing_receipt_before_user_facing_success("
require_fixed_line "${e2e_test}" "    def test_phase26_end_to_end_surfaces_duplicate_create_attempt_as_mismatch("
require_fixed_line "${e2e_test}" "    def test_phase26_end_to_end_surfaces_create_tracking_ticket_identifier_mismatch("
require_fixed_line "${e2e_test}" "    def test_phase26_end_to_end_surfaces_create_tracking_ticket_timeout("
require_fixed_line "${e2e_test}" "    def test_phase26_end_to_end_surfaces_create_tracking_ticket_manual_fallback("
require_fixed_line "${coordination_doc_test}" "class Phase26CoordinationSubstrateBoundaryDocsTests(unittest.TestCase):"
require_fixed_line "${soft_write_doc_test}" "class Phase26CreateTrackingTicketSoftWriteContractDocsTests(unittest.TestCase):"

require_fixed_line "${workflow_path}" "      - name: Run Phase 26 ticket coordination validation"
require_fixed_line "${workflow_path}" "      - name: Run Phase 26 workflow coverage guard"
require_fixed_line "${workflow_path}" "        run: bash scripts/test-verify-ci-phase-26-workflow-coverage.sh"

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"

active_run_commands="$(collect_active_run_commands)"
phase_validation_commands="$(extract_step_run_commands "${phase_validation_step_name}")"

if [[ -z "${phase_validation_commands}" ]]; then
  echo "Missing CI workflow step commands for ${phase_validation_step_name}" >&2
  exit 1
fi

for command in \
  "bash scripts/verify-phase-26-ticket-coordination-validation.sh" \
  "python3 -m unittest control-plane.tests.test_phase26_end_to_end_validation control-plane.tests.test_phase26_coordination_substrate_boundary_docs control-plane.tests.test_phase26_create_tracking_ticket_soft_write_contract_docs"
do
  if ! grep -Fqx -- "${command}" <<<"${phase_validation_commands}" >/dev/null; then
    echo "Missing required Phase 26 validation command in ${phase_validation_step_name}: ${command}" >&2
    exit 1
  fi
done

if ! grep -Fqx -- "bash scripts/test-verify-phase-26-ticket-coordination-validation.sh" <<<"${active_run_commands}" >/dev/null; then
  echo "Missing required Phase 26 focused shell test command in CI workflow: bash scripts/test-verify-phase-26-ticket-coordination-validation.sh" >&2
  exit 1
fi

phase_coverage_guard_commands="$(extract_step_run_commands "${phase_coverage_guard_step_name}")"
if [[ -z "${phase_coverage_guard_commands}" ]]; then
  echo "Missing dedicated Phase 26 workflow coverage guard step in CI workflow: ${phase_coverage_guard_step_name}" >&2
  exit 1
fi

if [[ "$(printf '%s\n' "${phase_coverage_guard_commands}")" != "${phase_coverage_guard_command}" ]]; then
  echo "Dedicated Phase 26 workflow coverage guard step must run exactly: ${phase_coverage_guard_command}" >&2
  echo "Found:" >&2
  printf '%s\n' "${phase_coverage_guard_commands}" >&2
  exit 1
fi

echo "Phase 26 ticket coordination validation artifacts and CI wiring are present and aligned."
