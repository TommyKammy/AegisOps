#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"
phase_validation_step_name="Run Phase 27 day-2 hardening validation"
phase_coverage_guard_step_name="Run Phase 27 workflow coverage guard"
phase_coverage_guard_command="bash scripts/test-verify-ci-phase-27-workflow-coverage.sh"
validation_doc="${repo_root}/docs/phase-27-day-2-hardening-validation.md"
phase_runtime_contract_test="${repo_root}/control-plane/tests/test_phase27_day2_runtime_contract.py"
restore_readiness_test="${repo_root}/control-plane/tests/test_service_persistence_restore_readiness.py"
runtime_auth_test="${repo_root}/control-plane/tests/test_phase21_runtime_auth_validation.py"
runtime_secret_test="${repo_root}/control-plane/tests/test_runtime_secret_boundary.py"
validation_doc_test="${repo_root}/control-plane/tests/test_phase27_day2_hardening_validation.py"
workflow_guard="${repo_root}/scripts/test-verify-ci-phase-27-workflow-coverage.sh"
shell_test="${repo_root}/scripts/test-verify-phase-27-day-2-hardening-validation.sh"

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

require_file "${validation_doc}" "Missing Phase 27 validation document"
require_file "${phase_runtime_contract_test}" "Missing Phase 27 runtime contract unittest"
require_file "${restore_readiness_test}" "Missing restore readiness unittest"
require_file "${runtime_auth_test}" "Missing runtime auth unittest"
require_file "${runtime_secret_test}" "Missing runtime secret unittest"
require_file "${validation_doc_test}" "Missing Phase 27 validation doc unittest"
require_file "${workflow_guard}" "Missing Phase 27 workflow coverage guard"
require_file "${shell_test}" "Missing Phase 27 shell verifier test"
require_file "${workflow_path}" "Missing CI workflow"

require_fixed_line "${validation_doc}" "# Phase 27 Day-2 Hardening Validation"
require_fixed_line "${validation_doc}" "- Validation status: PASS"
require_fixed_line "${validation_doc}" "- Reviewed sources: \`docs/runbook.md\`, \`docs/auth-baseline.md\`, \`docs/smb-footprint-and-deployment-profile-baseline.md\`, \`control-plane/tests/test_phase27_day2_runtime_contract.py\`, \`control-plane/tests/test_service_persistence_restore_readiness.py\`, \`control-plane/tests/test_phase21_runtime_auth_validation.py\`, \`control-plane/tests/test_runtime_secret_boundary.py\`"
require_fixed_line "${validation_doc}" "## Evidence Matrix"
require_fixed_line "${validation_doc}" "| Restore runtime guard | \`test_phase27_restore_runtime_contract_fails_closed_without_post_restore_bindings\` proves a restored control plane does not report success when required runtime bindings are still missing. | \`test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain\`; \`test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"
require_fixed_line "${validation_doc}" "| Restore reconciliation truth integrity | \`test_phase27_restore_reconciliation_truth_integrity_keeps_mismatch_reviewable\` proves restored subordinate receipts and external-ticket evidence cannot auto-close cases or auto-advance action execution state when the authoritative reconciliation record remains mismatched. | \`test_service_fail_closes_when_create_tracking_ticket_reconciliation_receipt_drifts\`; \`test_service_phase21_restore_rejects_reconciliation_run_binding_mismatch\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"
require_fixed_line "${validation_doc}" "| Degraded-mode visibility | \`test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state\` proves readiness keeps source and automation degradation visible instead of implying healthy operation from silence. | \`test_service_phase21_readiness_surfaces_source_and_automation_health\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"
require_fixed_line "${validation_doc}" "| Identity hardening | \`test_phase27_identity_contract_fails_closed_for_missing_or_unreviewed_provider_boundary\` proves startup and protected-surface access fail closed when the reviewed IdP binding is absent or crossed through an unreviewed provider. | \`test_startup_status_reports_missing_reviewed_identity_provider_binding\`; \`test_protected_surface_request_rejects_unreviewed_identity_provider_boundary\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"
require_fixed_line "${validation_doc}" "| IdP outage fail-closed workflow authority | \`test_phase27_idp_outage_blocks_operator_authority_and_workflow_progression\` proves unavailable IdP context blocks protected operator writes before action requests, approval decisions, executions, reconciliations, or case lifecycle transitions can advance. | \`test_protected_surface_request_rejects_missing_reviewed_identity_provider_header\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"
require_fixed_line "${validation_doc}" "| Secret delivery and rotation | \`test_phase27_secret_contract_requires_fresh_read_and_blocks_backend_outage\` proves OpenBao-backed config reloads rotated secrets only through a fresh read and blocks when the backend is unavailable; \`test_phase27_secret_backend_outage_rejects_plaintext_fallback_and_blocks_workflow_progression\` proves protected-surface secret outage rejects plaintext and file fallback before workflow authority can progress. | \`test_runtime_config_fails_closed_when_openbao_backend_is_unavailable\`; \`test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"
require_fixed_line "${validation_doc}" "| Upgrade/rollback authority freeze | \`test_phase27_upgrade_rollback_uncertainty_freezes_authority_sensitive_progression\` proves rollback-in-progress control-plane state blocks approval, execution, reconciliation, and case lifecycle progression while readiness remains failing closed and operator-visible. | \`docs/runbook.md\`; \`docs/smb-footprint-and-deployment-profile-baseline.md\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"
require_fixed_line "${validation_doc}" "### Phase 27-specific contract coverage"
require_fixed_line "${validation_doc}" "### Foundational coverage reused by Phase 27"
require_fixed_line "${validation_doc}" "- \`bash scripts/verify-phase-27-day-2-hardening-validation.sh\`"
require_fixed_line "${validation_doc}" "- \`bash scripts/test-verify-phase-27-day-2-hardening-validation.sh\`"
require_fixed_line "${validation_doc}" "- \`bash scripts/test-verify-ci-phase-27-workflow-coverage.sh\`"
require_fixed_line "${validation_doc}" "- \`python3 -m unittest control-plane.tests.test_phase27_day2_hardening_validation control-plane.tests.test_phase27_day2_runtime_contract\`"

require_fixed_line "${phase_runtime_contract_test}" "class Phase27Day2RuntimeContractTests(ServicePersistenceTestBase):"
require_fixed_line "${phase_runtime_contract_test}" "    def test_phase27_restore_runtime_contract_fails_closed_without_post_restore_bindings("
require_fixed_line "${phase_runtime_contract_test}" "    def test_phase27_restore_reconciliation_truth_integrity_keeps_mismatch_reviewable("
require_fixed_line "${phase_runtime_contract_test}" "    def test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state("
require_fixed_line "${phase_runtime_contract_test}" "    def test_phase27_identity_contract_fails_closed_for_missing_or_unreviewed_provider_boundary("
require_fixed_line "${phase_runtime_contract_test}" "    def test_phase27_idp_outage_blocks_operator_authority_and_workflow_progression("
require_fixed_line "${phase_runtime_contract_test}" "    def test_phase27_upgrade_rollback_uncertainty_freezes_authority_sensitive_progression("
require_fixed_line "${phase_runtime_contract_test}" "    def test_phase27_secret_contract_requires_fresh_read_and_blocks_backend_outage("
require_fixed_line "${phase_runtime_contract_test}" "    def test_phase27_secret_backend_outage_rejects_plaintext_fallback_and_blocks_workflow_progression("
require_fixed_line "${restore_readiness_test}" "class RestoreReadinessPersistenceTests(ServicePersistenceTestBase):"
require_fixed_line "${restore_readiness_test}" "    def test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain("
require_fixed_line "${restore_readiness_test}" "    def test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore("
require_fixed_line "${restore_readiness_test}" "    def test_service_phase21_readiness_surfaces_source_and_automation_health("
require_fixed_line "${runtime_auth_test}" "class Phase21RuntimeAuthValidationTests(unittest.TestCase):"
require_fixed_line "${runtime_auth_test}" "    def test_startup_status_reports_missing_reviewed_identity_provider_binding(self) -> None:"
require_fixed_line "${runtime_auth_test}" "    def test_protected_surface_request_rejects_unreviewed_identity_provider_boundary("
require_fixed_line "${runtime_secret_test}" "class RuntimeSecretBoundaryTests(unittest.TestCase):"
require_fixed_line "${runtime_secret_test}" "    def test_runtime_config_fails_closed_when_openbao_backend_is_unavailable(self) -> None:"
require_fixed_line "${runtime_secret_test}" "    def test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load(self) -> None:"
require_fixed_line "${validation_doc_test}" "class Phase27Day2HardeningValidationTests(unittest.TestCase):"

require_fixed_line "${workflow_path}" "      - name: Run Phase 27 day-2 hardening validation"
require_fixed_line "${workflow_path}" "      - name: Run Phase 27 workflow coverage guard"
require_fixed_line "${workflow_path}" "        run: bash scripts/test-verify-ci-phase-27-workflow-coverage.sh"

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"

active_run_commands="$(collect_active_run_commands)"
phase_validation_commands="$(extract_step_run_commands "${phase_validation_step_name}")"

if [[ -z "${phase_validation_commands}" ]]; then
  echo "Missing CI workflow step commands for ${phase_validation_step_name}" >&2
  exit 1
fi

for command in \
  "bash scripts/verify-phase-27-day-2-hardening-validation.sh" \
  "python3 -m unittest control-plane.tests.test_phase27_day2_hardening_validation control-plane.tests.test_phase27_day2_runtime_contract" \
  "python3 -m unittest control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_readiness_surfaces_source_and_automation_health control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_startup_status_reports_missing_reviewed_identity_provider_binding control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_protected_surface_request_rejects_unreviewed_identity_provider_boundary control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_fails_closed_when_openbao_backend_is_unavailable control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load"
do
  if ! grep -Fqx -- "${command}" <<<"${phase_validation_commands}" >/dev/null; then
    echo "Missing required Phase 27 validation command in ${phase_validation_step_name}: ${command}" >&2
    exit 1
  fi
done

if ! grep -Fqx -- "bash scripts/test-verify-phase-27-day-2-hardening-validation.sh" <<<"${active_run_commands}" >/dev/null; then
  echo "Missing required Phase 27 focused shell test command in CI workflow: bash scripts/test-verify-phase-27-day-2-hardening-validation.sh" >&2
  exit 1
fi

phase_coverage_guard_commands="$(extract_step_run_commands "${phase_coverage_guard_step_name}")"
if [[ -z "${phase_coverage_guard_commands}" ]]; then
  echo "Missing dedicated Phase 27 workflow coverage guard step in CI workflow: ${phase_coverage_guard_step_name}" >&2
  exit 1
fi

if [[ "$(printf '%s\n' "${phase_coverage_guard_commands}")" != "${phase_coverage_guard_command}" ]]; then
  echo "Dedicated Phase 27 workflow coverage guard step must run exactly: ${phase_coverage_guard_command}" >&2
  echo "Found:" >&2
  printf '%s\n' "${phase_coverage_guard_commands}" >&2
  exit 1
fi

echo "Phase 27 day-2 hardening validation artifacts and CI wiring are present and aligned."
