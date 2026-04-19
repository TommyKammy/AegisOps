#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"

required_verifiers=(
  "bash scripts/verify-phase-13-guarded-automation-ci-validation.sh"
)

required_tests=(
  "bash scripts/test-verify-phase-13-guarded-automation-ci-validation.sh"
)

required_runtime_commands=(
  "python3 -m unittest control-plane.tests.test_service_persistence_action_reconciliation.ActionReconciliationPersistenceTests.test_service_records_execution_correlation_mismatch_states_separately control-plane.tests.test_service_persistence_action_reconciliation.ActionReconciliationPersistenceTests.test_service_evaluates_action_policy_into_approval_and_isolated_executor control-plane.tests.test_service_persistence_action_reconciliation.ActionReconciliationPersistenceTests.test_service_evaluates_action_policy_into_shuffle_without_human_approval control-plane.tests.test_service_persistence_action_reconciliation.ActionReconciliationPersistenceTests.test_service_delegates_approved_low_risk_action_through_shuffle_adapter control-plane.tests.test_service_persistence_action_reconciliation.ActionReconciliationPersistenceTests.test_service_rejects_shuffle_delegation_for_non_shuffle_execution_policy control-plane.tests.test_service_persistence_action_reconciliation.ActionReconciliationPersistenceTests.test_service_delegates_approved_high_risk_action_through_isolated_executor control-plane.tests.test_service_persistence_action_reconciliation.ActionReconciliationPersistenceTests.test_service_reconciles_shuffle_run_back_into_authoritative_action_execution control-plane.tests.test_service_persistence_action_reconciliation.ActionReconciliationPersistenceTests.test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution"
)

self_guard_step_name="Run Phase 13 workflow coverage guard"
self_guard_command="bash scripts/test-verify-ci-phase-13-workflow-coverage.sh"

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

      if ($0 ~ /^[[:space:]]*run:[[:space:]]*[|>]-?[[:space:]]*$/) {
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

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"
active_run_commands="$(collect_active_run_commands)"

for command in "${required_verifiers[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 13 verifier command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_tests[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 13 focused shell test command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_runtime_commands[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 13 focused guarded-automation runtime command in CI workflow: ${command}" >&2
    exit 1
  fi
done

if ! grep -Eq "^[[:space:]]*- name: ${self_guard_step_name}\$" "${workflow_path}"; then
  echo "Missing dedicated Phase 13 workflow coverage guard step in CI workflow: ${self_guard_step_name}" >&2
  exit 1
fi

self_guard_count="$(grep -Fxc -- "${self_guard_command}" <<<"${active_run_commands}" || true)"
if [[ "${self_guard_count}" -lt 2 ]]; then
  echo "Phase 13 workflow coverage checker must run both as a dedicated guard and within focused shell tests." >&2
  exit 1
fi

echo "CI workflow includes the required Phase 13 verifier, focused shell test, and focused guarded-automation runtime command."
