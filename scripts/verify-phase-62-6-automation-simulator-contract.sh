#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

required_paths=(
  "${repo_root}/docs/phase-62-6-automation-simulator-contract.md"
  "${repo_root}/docs/phase-62-6-automation-simulator-validation.md"
  "${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
  "${repo_root}/control-plane/tests/test_phase62_action_policy_registry.py"
)

for path in "${required_paths[@]}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 62.6 automation simulator artifact: ${path}" >&2
    exit 1
  fi
done

require_phrase() {
  local file_path="$1"
  local expected="$2"
  if ! grep -Fq -- "${expected}" "${file_path}"; then
    echo "Missing Phase 62.6 automation simulator statement in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

contract_path="${repo_root}/docs/phase-62-6-automation-simulator-contract.md"
for phrase in \
  '# AegisOps Phase 62.6 Automation Simulator Contract' \
  'Every simulator output must be tied to one reviewed catalog action' \
  'Simulator output is demo/test evidence only.' \
  'excluded from production execution receipt and reconciliation truth' \
  'Run `bash scripts/verify-phase-62-6-automation-simulator-contract.sh`.' \
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1320 --config <supervisor-config-path>`.'; do
  require_phrase "${contract_path}" "${phrase}"
done

registry_path="${repo_root}/control-plane/aegisops/control_plane/actions/action_policy_registry.py"
for phrase in \
  'SimulatorContract' \
  'PHASE62_SIMULATOR_CONTRACTS' \
  'validate_phase62_simulator_output' \
  '"demo"' \
  '"test"' \
  '"demo_test_label"' \
  '"production_exclusion"' \
  '"authority_posture"' \
  '"non_authoritative_demo_test_evidence"' \
  '"live_secret_ref"' \
  '"customer_data_classification"' \
  '"synthetic_only"' \
  '"sanitized_demo_only"'; do
  require_phrase "${registry_path}" "${phrase}"
done

(cd "${repo_root}" && PYTHONPATH="${repo_root}/control-plane:${repo_root}/control-plane/tests" python3 -m unittest \
  control-plane.tests.test_phase62_action_policy_registry \
  control-plane.tests.test_action_receipt_validation)

bash "${repo_root}/scripts/verify-phase-54-9-shuffle-authority-boundary-negative-tests.sh" "${repo_root}"
bash "${repo_root}/scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh" "${repo_root}"

path_hygiene_stderr="${repo_root}/.tmp-phase62-6-automation-simulator-path-hygiene.err"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${repo_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 62.6 automation simulator absolute path usage detected" >&2
  exit 1
fi

echo "Phase 62.6 automation simulator contract and focused tests pass."
