#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"
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
require_fixed_line "${workflow_path}" "          bash scripts/verify-phase-26-ticket-coordination-validation.sh"
require_fixed_line "${workflow_path}" "          python3 -m unittest control-plane.tests.test_phase26_end_to_end_validation control-plane.tests.test_phase26_coordination_substrate_boundary_docs control-plane.tests.test_phase26_create_tracking_ticket_soft_write_contract_docs"
require_fixed_line "${workflow_path}" "      - name: Run Phase 26 workflow coverage guard"
require_fixed_line "${workflow_path}" "        run: bash scripts/test-verify-ci-phase-26-workflow-coverage.sh"
require_fixed_line "${workflow_path}" "          bash scripts/test-verify-phase-26-ticket-coordination-validation.sh"

echo "Phase 26 ticket coordination validation artifacts and CI wiring are present and aligned."
