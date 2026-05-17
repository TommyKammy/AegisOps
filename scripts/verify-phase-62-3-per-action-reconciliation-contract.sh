#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

required_paths=(
  "${repo_root}/docs/phase-62-3-per-action-reconciliation-contract.md"
  "${repo_root}/docs/phase-62-3-per-action-reconciliation-validation.md"
  "${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
  "${repo_root}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
  "${repo_root}/control-plane/tests/test_phase62_action_policy_registry.py"
  "${repo_root}/control-plane/tests/test_service_persistence_action_reconciliation_reviewed_requests.py"
)

for path in "${required_paths[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 62.3 per-action reconciliation artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 62.3 reconciliation statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

registry_path="${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
for phrase in \
  'expected_receipt_fields' \
  'correlation_fields' \
  'reconciliation_outcomes' \
  '"success"' \
  '"failure"' \
  '"missing"' \
  '"stale"' \
  '"mismatched"' \
  '"duplicated"' \
  '"wrong_correlation"' \
  '"manual_review"' \
  '"expected_execution_receipt_id"' \
  '"coordination_reference_id"'; do
  require_phrase "${registry_path}" "${phrase}"
done

contract_path="${repo_root}/docs/phase-62-3-per-action-reconciliation-contract.md"
for phrase in \
  '# AegisOps Phase 62.3 Per-Action Reconciliation Contract' \
  'Every reviewed Phase 62 action must carry expected receipt fields' \
  'Shuffle receipts are subordinate evidence.' \
  'A Shuffle `success` status can only update AegisOps action execution state when the observed receipt is bound' \
  'Run `bash scripts/verify-phase-62-3-per-action-reconciliation-contract.sh`.'; do
  require_phrase "${contract_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane:${repo_root}/control-plane/tests" python3 -m unittest \
  control-plane.tests.test_phase62_action_policy_registry \
  control-plane.tests.test_service_persistence_action_reconciliation_reviewed_requests.ReviewedActionRequestPersistenceTests.test_service_rejects_phase62_notification_success_without_bound_receipt \
  control-plane.tests.test_service_persistence_action_reconciliation_reviewed_requests.ReviewedActionRequestPersistenceTests.test_service_executes_phase20_first_live_action_end_to_end_from_reviewed_recommendation \
  control-plane.tests.test_service_persistence_action_reconciliation_create_tracking_ticket.CreateTrackingTicketActionReconciliationPersistenceTests.test_service_reconciles_create_tracking_ticket_receipt_into_authoritative_records \
  control-plane.tests.test_service_persistence_action_reconciliation_create_tracking_ticket.CreateTrackingTicketActionReconciliationPersistenceTests.test_service_fail_closes_when_create_tracking_ticket_reconciliation_receipt_drifts \
  control-plane.tests.test_action_receipt_validation)

path_hygiene_stderr="${repo_root}/.tmp-phase62-3-reconciliation-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 62.3 reconciliation contract absolute path usage detected" >&2
  exit 1
fi

echo "Phase 62.3 per-action reconciliation contract and focused tests pass."
