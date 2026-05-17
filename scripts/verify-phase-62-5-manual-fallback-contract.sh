#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

required_paths=(
  "${repo_root}/docs/phase-62-5-manual-fallback-contract.md"
  "${repo_root}/docs/phase-62-5-manual-fallback-validation.md"
  "${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
  "${repo_root}/control-plane/tests/test_phase62_action_policy_registry.py"
)

for path in "${required_paths[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 62.5 manual fallback artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 62.5 manual fallback statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

contract_path="${repo_root}/docs/phase-62-5-manual-fallback-contract.md"
for phrase in \
  '# AegisOps Phase 62.5 Manual Fallback Contract' \
  'Every reviewed Phase 62 action must have a manual fallback requirement' \
  'Manual fallback is subordinate operator guidance.' \
  'Run `bash scripts/verify-phase-62-5-manual-fallback-contract.sh`.' \
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1319 --config <supervisor-config-path>`.'; do
  require_phrase "${contract_path}" "${phrase}"
done

registry_path="${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
for phrase in \
  'ManualFallbackRequirement' \
  'PHASE62_MANUAL_FALLBACK_REQUIREMENTS' \
  'validate_phase62_manual_fallback_record' \
  '"shuffle_unavailable"' \
  '"execution_rejected"' \
  '"missing_receipt"' \
  '"stale_receipt"' \
  '"mismatched_receipt"' \
  '"fallback_owner_id"' \
  '"operator_note"' \
  '"affected_action"' \
  '"fallback_state"' \
  '"blocked_reason"' \
  '"expected_evidence"' \
  '"follow_up_state"' \
  '"execution_receipt_required"' \
  '"aegisops_reconciliation_required"'; do
  require_phrase "${registry_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane:${repo_root}/control-plane/tests" python3 -m unittest \
  control-plane.tests.test_phase62_action_policy_registry)

bash "${repo_root}/scripts/verify-phase-54-8-manual-fallback-contract.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-phase-54-9-shuffle-authority-boundary-negative-tests.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh" "${repo_root}"

path_hygiene_stderr="${repo_root}/.tmp-phase62-5-manual-fallback-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 62.5 manual fallback absolute path usage detected" >&2
  exit 1
fi

echo "Phase 62.5 manual fallback contract and focused tests pass."
