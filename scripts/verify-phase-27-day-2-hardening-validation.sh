#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"
validation_doc="${repo_root}/docs/phase-27-day-2-hardening-validation.md"
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
require_file "${restore_readiness_test}" "Missing restore readiness unittest"
require_file "${runtime_auth_test}" "Missing runtime auth unittest"
require_file "${runtime_secret_test}" "Missing runtime secret unittest"
require_file "${validation_doc_test}" "Missing Phase 27 validation doc unittest"
require_file "${workflow_guard}" "Missing Phase 27 workflow coverage guard"
require_file "${shell_test}" "Missing Phase 27 shell verifier test"
require_file "${workflow_path}" "Missing CI workflow"

require_fixed_line "${validation_doc}" "# Phase 27 Day-2 Hardening Validation"
require_fixed_line "${validation_doc}" "- Validation status: PASS"
require_fixed_line "${validation_doc}" "- Reviewed sources: \`docs/runbook.md\`, \`docs/auth-baseline.md\`, \`docs/smb-footprint-and-deployment-profile-baseline.md\`, \`control-plane/tests/test_service_persistence_restore_readiness.py\`, \`control-plane/tests/test_phase21_runtime_auth_validation.py\`, \`control-plane/tests/test_runtime_secret_boundary.py\`"
require_fixed_line "${validation_doc}" "- \`restore\`: \`test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain\` keeps the approved disaster-recovery path anchored to the authoritative record chain."
require_fixed_line "${validation_doc}" "- \`restore\`: \`test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore\` proves restore verification blocks when the recovered runtime boundary is incomplete."
require_fixed_line "${validation_doc}" "- \`degraded-mode\`: \`test_service_phase21_readiness_surfaces_source_and_automation_health\` keeps source-health and delegation outage visibility explicit during degraded-mode handling."
require_fixed_line "${validation_doc}" "- \`identity-boundary\`: \`test_startup_status_reports_missing_reviewed_identity_provider_binding\` treats IdP outage or missing reviewed provider binding as a fail-closed startup condition."
require_fixed_line "${validation_doc}" "- \`identity-boundary\`: \`test_protected_surface_request_rejects_unreviewed_identity_provider_boundary\` rejects requests that cross the identity boundary through an unreviewed provider path."
require_fixed_line "${validation_doc}" "- \`secret rotation\`: \`test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load\` proves rotation requires a fresh trusted read instead of cached or guessed secret state."
require_fixed_line "${validation_doc}" "- \`secret-backend unavailability\`: \`test_runtime_config_fails_closed_when_openbao_backend_is_unavailable\` keeps the control plane blocked when the reviewed secret backend cannot be read."
require_fixed_line "${validation_doc}" "- \`bash scripts/verify-phase-27-day-2-hardening-validation.sh\`"
require_fixed_line "${validation_doc}" "- \`bash scripts/test-verify-phase-27-day-2-hardening-validation.sh\`"
require_fixed_line "${validation_doc}" "- \`bash scripts/test-verify-ci-phase-27-workflow-coverage.sh\`"

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
require_fixed_line "${workflow_path}" "          bash scripts/verify-phase-27-day-2-hardening-validation.sh"
require_fixed_line "${workflow_path}" "          python3 -m unittest control-plane.tests.test_phase27_day2_hardening_validation control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore control-plane.tests.test_service_persistence_restore_readiness.RestoreReadinessPersistenceTests.test_service_phase21_readiness_surfaces_source_and_automation_health control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_startup_status_reports_missing_reviewed_identity_provider_binding control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_protected_surface_request_rejects_unreviewed_identity_provider_boundary control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_fails_closed_when_openbao_backend_is_unavailable control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load"
require_fixed_line "${workflow_path}" "      - name: Run Phase 27 workflow coverage guard"
require_fixed_line "${workflow_path}" "        run: bash scripts/test-verify-ci-phase-27-workflow-coverage.sh"
require_fixed_line "${workflow_path}" "          bash scripts/test-verify-phase-27-day-2-hardening-validation.sh"

echo "Phase 27 day-2 hardening validation artifacts and CI wiring are present and aligned."
