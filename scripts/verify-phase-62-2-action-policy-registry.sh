#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

required_paths=(
  "${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
  "${repo_root}/control-plane/tests/test_phase62_action_policy_registry.py"
  "${repo_root}/control-plane/tests/test_service_persistence_action_reconciliation_reviewed_requests.py"
)

for path in "${required_paths[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 62.2 action policy registry artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 62.2 action policy registry statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

registry_path="${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
for phrase in \
  '"enrichment_only_lookup"' \
  '"operator_notification"' \
  '"manual_escalation_request"' \
  '"create_tracking_ticket"' \
  'allowed_requester_roles' \
  'allowed_reviewer_roles' \
  'allowed_target_scope' \
  'idempotency_required' \
  'protected_target_posture' \
  'missing_reviewed_policy' \
  'requester_role_not_allowed' \
  'policy_expired' \
  'missing_idempotency_key' \
  'target_scope_not_allowed' \
  'protected_target_misuse'; do
  require_phrase "${registry_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane:${repo_root}/control-plane/tests" python3 -m unittest \
  control-plane.tests.test_phase62_action_policy_registry \
  control-plane.tests.test_service_persistence_action_reconciliation_reviewed_requests.ReviewedActionRequestPersistenceTests.test_service_records_phase62_policy_decision_on_tracking_ticket_request \
  control-plane.tests.test_service_persistence_action_reconciliation_reviewed_requests.ReviewedActionRequestPersistenceTests.test_service_rejects_tracking_ticket_request_from_read_only_role)

path_hygiene_stderr="${repo_root}/.tmp-phase62-2-action-policy-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 62.2 action policy registry absolute path usage detected" >&2
  exit 1
fi

echo "Phase 62.2 action policy registry and focused request-boundary tests pass."
