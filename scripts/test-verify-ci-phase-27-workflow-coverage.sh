#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"

required_verifiers=(
  "bash scripts/verify-phase-27-day-2-hardening-validation.sh"
)

required_tests=(
  "bash scripts/test-verify-phase-27-day-2-hardening-validation.sh"
)

required_runtime_commands=(
  "python3 -m unittest control-plane.tests.test_phase27_day2_hardening_validation control-plane.tests.test_phase27_day2_runtime_contract"
  "python3 -m unittest control-plane.tests.test_service_restore_backup_codec.RestoreBackupCodecTests.test_service_phase21_backup_restore_and_restore_drill_preserve_record_chain control-plane.tests.test_service_restore_drill_transactions.RestoreDrillTransactionTests.test_service_phase21_restore_drill_fails_closed_when_runtime_bindings_missing_after_restore control-plane.tests.test_service_readiness_projection.ReadinessProjectionTests.test_service_phase21_readiness_surfaces_source_and_automation_health control-plane.tests.test_service_restore_validation.RestoreValidationTests.test_service_phase21_restore_fails_closed_on_duplicate_alert_identifiers control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_startup_status_reports_missing_reviewed_identity_provider_binding control-plane.tests.test_phase21_runtime_auth_validation.Phase21RuntimeAuthValidationTests.test_protected_surface_request_rejects_unreviewed_identity_provider_boundary control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_fails_closed_when_openbao_backend_is_unavailable control-plane.tests.test_runtime_secret_boundary.RuntimeSecretBoundaryTests.test_runtime_config_reloads_rotated_openbao_secret_on_fresh_load"
)

self_guard_step_name="Run Phase 27 workflow coverage guard"
self_guard_command="bash scripts/test-verify-ci-phase-27-workflow-coverage.sh"

if [[ ! -f "${workflow_path}" ]]; then
  echo "Missing CI workflow: ${workflow_path}" >&2
  exit 1
fi

collect_active_run_commands() {
  awk '
    {
      if (in_block) {
        if ($0 ~ /^[[:space:]]*$/) {
          next
        }

        current_indent = match($0, /[^ ]/) - 1
        if (current_indent > block_indent) {
          line = $0
          sub(/^[[:space:]]+/, "", line)
          if (line != "" && line !~ /^#/) {
            print line
          }
          next
        }

        in_block = 0
      }

      if ($0 ~ /^[[:space:]]*run:[[:space:]]*\|[-]?[[:space:]]*$/) {
        block_indent = match($0, /[^ ]/) - 1
        in_block = 1
        next
      }

      if ($0 ~ /^[[:space:]]*run:[[:space:]]*[^|>]/) {
        line = $0
        sub(/^[[:space:]]*run:[[:space:]]*/, "", line)
        if (line != "" && line !~ /^#/) {
          print line
        }
      }
    }
  ' "${workflow_path}"
}

extract_self_guard_step_run_command() {
  awk -v step_name="${self_guard_step_name}" '
    function line_indent(line) {
      return match(line, /[^ ]/) - 1
    }

    BEGIN {
      in_step = 0
      step_indent = -1
    }

    {
      if (in_step) {
        if ($0 ~ /^[[:space:]]*-[[:space:]]/ && line_indent($0) <= step_indent) {
          exit 0
        }

        if ($0 ~ /^[[:space:]]*run:[[:space:]]*/ && line_indent($0) > step_indent) {
          line = $0
          sub(/^[[:space:]]*run:[[:space:]]*/, "", line)
          print line
          exit 0
        }
      }

      line = $0
      sub(/^[[:space:]]+/, "", line)
      if (line == "- name: " step_name) {
        in_step = 1
        step_indent = line_indent($0)
      }
    }
  ' "${workflow_path}"
}

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"
active_run_commands="$(collect_active_run_commands)"

for command in "${required_verifiers[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 27 verifier command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_tests[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 27 focused shell test command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_runtime_commands[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 27 focused runtime command in CI workflow: ${command}" >&2
    exit 1
  fi
done

self_guard_step_run_command="$(extract_self_guard_step_run_command)"
if [[ -z "${self_guard_step_run_command}" ]]; then
  echo "Missing dedicated Phase 27 workflow coverage guard step in CI workflow: ${self_guard_step_name}" >&2
  exit 1
fi

if [[ "${self_guard_step_run_command}" != "${self_guard_command}" ]]; then
  echo "Dedicated Phase 27 workflow coverage guard step must run exactly: ${self_guard_command}" >&2
  echo "Found: ${self_guard_step_run_command}" >&2
  exit 1
fi

self_guard_count="$(grep -Fxc -- "${self_guard_command}" <<<"${active_run_commands}" || true)"
if [[ "${self_guard_count}" -lt 2 ]]; then
  echo "Phase 27 workflow coverage checker must run both as a dedicated guard and within focused shell tests." >&2
  exit 1
fi

echo "CI workflow includes the required Phase 27 verifier, focused shell test, and focused runtime command."
