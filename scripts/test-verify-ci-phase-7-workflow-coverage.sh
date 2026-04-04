#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"

required_verifiers=(
  "bash scripts/verify-phase-7-ai-hunt-design-validation.sh"
  "bash scripts/verify-asset-identity-privilege-context-baseline.sh"
  "bash scripts/verify-ai-hunt-plane-adr.sh"
)

required_tests=(
  "bash scripts/test-verify-phase-7-ai-hunt-design-validation.sh"
  "bash scripts/test-verify-asset-identity-privilege-context-baseline.sh"
  "bash scripts/test-verify-ci-phase-7-workflow-coverage.sh"
)

if [[ ! -f "${workflow_path}" ]]; then
  echo "Missing CI workflow: ${workflow_path}" >&2
  exit 1
fi

for command in "${required_verifiers[@]}"; do
  if ! grep -Fq "${command}" "${workflow_path}"; then
    echo "Missing Phase 7 verifier command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_tests[@]}"; do
  if ! grep -Fq "${command}" "${workflow_path}"; then
    echo "Missing Phase 7 focused shell test command in CI workflow: ${command}" >&2
    exit 1
  fi
done

echo "CI workflow includes the required Phase 7 verifier and focused shell test commands."
