#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"
runner_path="${repo_root}/scripts/run-ci-phase-contract.sh"
manifest_path="${repo_root}/scripts/ci-phase-contract-commands.sh"

if [[ ! -f "${workflow_path}" ]]; then
  echo "Missing CI workflow: ${workflow_path}" >&2
  exit 1
fi

if [[ ! -f "${runner_path}" ]]; then
  echo "Missing phase-contract runner: ${runner_path}" >&2
  exit 1
fi

if [[ ! -f "${manifest_path}" ]]; then
  echo "Missing phase-contract manifest: ${manifest_path}" >&2
  exit 1
fi

required_workflow_commands=(
  "bash scripts/run-ci-phase-contract.sh all-verifiers"
  "bash scripts/run-ci-phase-contract.sh all-shell-tests"
)

for command in "${required_workflow_commands[@]}"; do
  if ! grep -Fq -- "${command}" "${workflow_path}" >/dev/null; then
    echo "Missing shared phase-contract runner invocation in CI workflow: ${command}" >&2
    exit 1
  fi
done

required_manifest_commands=(
  "bash scripts/verify-phase-5-semantic-contract-validation.sh"
  "bash scripts/verify-phase-25-multi-source-case-review-runbook.sh"
  "bash scripts/test-verify-phase-15-identity-grounded-analyst-assistant-boundary.sh"
  "bash scripts/test-verify-ci-phase-28-workflow-coverage.sh"
)

for command in "${required_manifest_commands[@]}"; do
  if ! "${runner_path}" --print all-verifiers | grep -Fqx -- "${command}" >/dev/null && \
     ! "${runner_path}" --print all-shell-tests | grep -Fqx -- "${command}" >/dev/null; then
    echo "Missing required phase-contract command from shared runner output: ${command}" >&2
    exit 1
  fi
done

echo "CI workflow delegates phase-contract verifier and shell-test command sets through the shared runner."
