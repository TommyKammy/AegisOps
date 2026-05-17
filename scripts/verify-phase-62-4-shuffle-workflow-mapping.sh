#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

required_files=(
  "${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
  "${repo_root}/control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py"
  "${repo_root}/control-plane/aegisops/control_plane/adapters/shuffle.py"
  "${repo_root}/control-plane/tests/test_phase62_action_policy_registry.py"
)

for path in "${required_files[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 62.4 Shuffle workflow mapping artifact: ${path}" >&2
    exit 1
  fi
done

(cd "${repo_root}" && python3 -m unittest \
  control-plane.tests.test_phase62_action_policy_registry \
  control-plane.tests.test_service_persistence_action_reconciliation_delegation \
  control-plane.tests.test_service_persistence_action_reconciliation_reviewed_requests \
  control-plane.tests.test_service_persistence_action_reconciliation_create_tracking_ticket)

path_hygiene_stderr="${repo_root}/.tmp-phase62-4-shuffle-mapping-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 62.4 Shuffle workflow mapping absolute path usage detected" >&2
  exit 1
fi

echo "Phase 62.4 Shuffle workflow mapping verifier passes."
