#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"

operator_ui_step_name="Run operator UI merge-gate checks"
operator_ui_commands=(
  "npm ci"
  "npm run typecheck --workspace @aegisops/operator-ui"
  "npm run test --workspace @aegisops/operator-ui"
  "npm run build --workspace @aegisops/operator-ui"
)

self_guard_step_name="Run operator UI workflow coverage guard"
self_guard_command="bash scripts/test-verify-ci-operator-ui-workflow-coverage.sh"

if [[ ! -f "${workflow_path}" ]]; then
  echo "Missing CI workflow: ${workflow_path}" >&2
  exit 1
fi

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"

active_run_commands="$(collect_active_run_commands)"
operator_ui_step_commands="$(extract_step_run_commands "${operator_ui_step_name}")"

if [[ -z "${operator_ui_step_commands}" ]]; then
  echo "Missing dedicated operator UI merge-gate step in CI workflow: ${operator_ui_step_name}" >&2
  exit 1
fi

for command in "${operator_ui_commands[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${operator_ui_step_commands}" >/dev/null; then
    echo "Missing operator UI merge-gate command in dedicated CI step: ${command}" >&2
    exit 1
  fi
done

self_guard_step_commands="$(extract_step_run_commands "${self_guard_step_name}")"
if [[ -z "${self_guard_step_commands}" ]]; then
  echo "Missing dedicated operator UI workflow coverage guard step in CI workflow: ${self_guard_step_name}" >&2
  exit 1
fi

if ! grep -Fqx -- "${self_guard_command}" <<<"${self_guard_step_commands}" >/dev/null; then
  echo "Dedicated operator UI workflow coverage guard step must run exactly: ${self_guard_command}" >&2
  printf 'Found commands:\n%s\n' "${self_guard_step_commands}" >&2
  exit 1
fi

if ! grep -Fqx -- "${self_guard_command}" <<<"${active_run_commands}" >/dev/null; then
  echo "Missing operator UI workflow coverage guard command in CI workflow: ${self_guard_command}" >&2
  exit 1
fi

echo "CI workflow includes the required operator UI install, typecheck, test, build, and workflow guard commands."
