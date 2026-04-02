#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"

required_verifiers=(
  "bash scripts/verify-auth-baseline-doc.sh"
  "bash scripts/verify-canonical-telemetry-schema-doc.sh"
  "bash scripts/verify-control-plane-state-model-doc.sh"
  "bash scripts/verify-phase-5-semantic-contract-validation.sh"
  "bash scripts/verify-response-action-safety-model-doc.sh"
  "bash scripts/verify-retention-baseline-doc.sh"
  "bash scripts/verify-secops-business-hours-operating-model-doc.sh"
  "bash scripts/verify-source-onboarding-contract-doc.sh"
)

required_tests=(
  "bash scripts/test-verify-auth-baseline-doc.sh"
  "bash scripts/test-verify-canonical-telemetry-schema-doc.sh"
  "bash scripts/test-verify-control-plane-state-model-doc.sh"
  "bash scripts/test-verify-phase-5-semantic-contract-validation.sh"
  "bash scripts/test-verify-response-action-safety-model-doc.sh"
  "bash scripts/test-verify-retention-baseline-doc.sh"
  "bash scripts/test-verify-secops-business-hours-operating-model-doc.sh"
  "bash scripts/test-verify-source-onboarding-contract-doc.sh"
)

if [[ ! -f "${workflow_path}" ]]; then
  echo "Missing CI workflow: ${workflow_path}" >&2
  exit 1
fi

for command in "${required_verifiers[@]}"; do
  if ! grep -Fq "${command}" "${workflow_path}"; then
    echo "Missing Phase 5 verifier command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_tests[@]}"; do
  if ! grep -Fq "${command}" "${workflow_path}"; then
    echo "Missing Phase 5 focused shell test command in CI workflow: ${command}" >&2
    exit 1
  fi
done

echo "CI workflow includes the required Phase 5 verifier and focused shell test commands."
