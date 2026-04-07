#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
validation_doc="${repo_root}/docs/phase-13-guarded-automation-ci-validation.md"
automation_contract_doc="${repo_root}/docs/automation-substrate-contract.md"
architecture_doc="${repo_root}/docs/architecture.md"
service_tests="${repo_root}/control-plane/tests/test_service_persistence.py"
workflow_path="${repo_root}/.github/workflows/ci.yml"

bash "${script_dir}/verify-automation-substrate-contract-doc.sh" "${repo_root}"
bash "${script_dir}/verify-architecture-doc.sh" "${repo_root}"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_string() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required line in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_test_name() {
  local file_path="$1"
  local test_name="$2"
  local pattern="^[[:space:]]*def[[:space:]]+${test_name}[[:space:]]*\\("

  if ! grep -Eq -- "${pattern}" "${file_path}" >/dev/null; then
    echo "Missing required Phase 13 test in ${file_path}: ${test_name}" >&2
    exit 1
  fi
}

require_file "${validation_doc}" "Missing Phase 13 guarded-automation CI validation record"
require_file "${automation_contract_doc}" "Missing automation substrate contract document"
require_file "${architecture_doc}" "Missing architecture overview document"
require_file "${service_tests}" "Missing control-plane service persistence tests"
require_file "${workflow_path}" "Missing CI workflow"

validation_required_phrases=(
  "# Phase 13 Guarded Automation and Reconciliation CI Validation"
  "- Validation date: 2026-04-07"
  "- Validation scope: Phase 13 review of guarded-automation policy routing, approval-bound delegation, isolated-executor boundary invariants, authoritative reconciliation behavior, and CI wiring for the reviewed Phase 13 path"
  "- Baseline references: \`docs/automation-substrate-contract.md\`, \`docs/architecture.md\`, \`control-plane/tests/test_service_persistence.py\`, \`.github/workflows/ci.yml\`"
  "- Verification commands: \`bash scripts/verify-automation-substrate-contract-doc.sh\`, \`python3 -m unittest control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_records_execution_correlation_mismatch_states_separately control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_evaluates_action_policy_into_approval_and_isolated_executor control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_evaluates_action_policy_into_shuffle_without_human_approval control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_delegates_approved_low_risk_action_through_shuffle_adapter control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_rejects_shuffle_delegation_for_non_shuffle_execution_policy control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_delegates_approved_high_risk_action_through_isolated_executor control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_shuffle_run_back_into_authoritative_action_execution control-plane.tests.test_service_persistence.ControlPlaneServicePersistenceTests.test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution\`, \`bash scripts/test-verify-ci-phase-13-workflow-coverage.sh\`, \`bash scripts/verify-phase-13-guarded-automation-ci-validation.sh\`"
  "- Validation status: PASS"
  "## Required Boundary Artifacts"
  "## Review Outcome"
  "## Cross-Link Review"
  "## Deviations"
  'Confirmed the reviewed delegation contract and architecture baseline keep AegisOps authoritative for `Action Request`, `Approval Decision`, evidence linkage, `Action Execution` correlation, and `Reconciliation` truth across Shuffle and isolated-executor boundaries.'
  'Confirmed Phase 13 policy evaluation coverage keeps routine actions on the reviewed Shuffle path while routing higher-risk actions to the isolated executor with explicit human approval requirements.'
  'Confirmed Phase 13 delegation coverage binds `approval_decision_id`, `delegation_id`, `execution_surface_type`, `execution_surface_id`, `idempotency_key`, and `payload_hash` through both reviewed execution paths.'
  'Confirmed Phase 13 reconciliation coverage preserves missing, duplicate, mismatch, and stale execution states as explicit control-plane reconciliation outcomes and reconciles reviewed surface status back into authoritative `Action Execution` records.'
  "Confirmed CI now runs a dedicated Phase 13 validation step and a workflow coverage guard so guarded-automation drift fails repository-local review instead of depending on manual spot checks."
  '`docs/automation-substrate-contract.md` must continue to define approval-bound delegation identity, payload binding, replay safety, and fail-closed reconciliation expectations for reviewed downstream execution surfaces.'
  '`docs/architecture.md` must continue to keep the policy-sensitive path explicit and forbid external substrates or executors from becoming the authority for approval or reconciliation truth.'
  '`control-plane/tests/test_service_persistence.py` must continue to guard Phase 13 policy routing, Shuffle delegation boundaries, isolated-executor boundaries, and authoritative reconciliation behavior.'
  '`.github/workflows/ci.yml` must continue to run the dedicated Phase 13 validation step, the focused Phase 13 unittest command, and the workflow coverage guard.'
  "No deviations found."
)

for phrase in "${validation_required_phrases[@]}"; do
  require_fixed_string "${validation_doc}" "${phrase}"
done

required_artifacts=(
  "docs/automation-substrate-contract.md"
  "docs/architecture.md"
  "control-plane/tests/test_service_persistence.py"
  ".github/workflows/ci.yml"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 13 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 13 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

require_fixed_string "${automation_contract_doc}" 'Delegation is allowed only after AegisOps has a bounded `Action Request` and a still-valid `Approval Decision` whose binding fields exactly match the downstream execution intent.'
require_fixed_string "${automation_contract_doc}" 'If the downstream surface reports the wrong payload hash, wrong target scope, wrong execution surface, or missing idempotency key, AegisOps must preserve that mismatch as explicit reconciliation state instead of normalizing it away.'
require_fixed_string "${architecture_doc}" 'The normative mainline policy-sensitive path is:'
require_fixed_string "${architecture_doc}" '`Substrate Detection Record -> Analytic Signal -> Alert or Case -> Action Request -> Approval Decision -> Approved Automation Substrate or Executor -> Reconciliation`'
require_fixed_string "${architecture_doc}" 'Detection substrates may emit substrate detection records and analytic signals, and automation substrates may perform delegated work, but neither may become the authority for alert truth, case truth, approval truth, action intent, evidence custody, or reconciliation truth.'

require_test_name "${service_tests}" "test_service_records_execution_correlation_mismatch_states_separately"
require_test_name "${service_tests}" "test_service_evaluates_action_policy_into_approval_and_isolated_executor"
require_test_name "${service_tests}" "test_service_evaluates_action_policy_into_shuffle_without_human_approval"
require_test_name "${service_tests}" "test_service_delegates_approved_low_risk_action_through_shuffle_adapter"
require_test_name "${service_tests}" "test_service_rejects_shuffle_delegation_for_non_shuffle_execution_policy"
require_test_name "${service_tests}" "test_service_delegates_approved_high_risk_action_through_isolated_executor"
require_test_name "${service_tests}" "test_service_reconciles_shuffle_run_back_into_authoritative_action_execution"
require_test_name "${service_tests}" "test_service_reconciles_isolated_executor_run_back_into_authoritative_action_execution"

require_fixed_string "${workflow_path}" "      - name: Run Phase 13 workflow coverage guard"
require_fixed_string "${workflow_path}" "      - name: Run Phase 13 guarded automation validation"

echo "Phase 13 guarded automation and reconciliation CI validation remains reviewable and fail closed."
