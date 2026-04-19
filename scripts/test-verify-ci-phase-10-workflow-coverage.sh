#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"

required_verifiers=(
  "bash scripts/verify-phase-10-thesis-consistency.sh"
  "bash scripts/verify-positive-smb-value-proposition.sh"
)

required_tests=(
  "bash scripts/test-verify-phase-10-thesis-consistency.sh"
  "bash scripts/test-verify-positive-smb-value-proposition.sh"
)

self_guard_step_name="Run Phase 10 workflow coverage guard"
self_guard_command="bash scripts/test-verify-ci-phase-10-workflow-coverage.sh"

if [[ ! -f "${workflow_path}" ]]; then
  echo "Missing CI workflow: ${workflow_path}" >&2
  exit 1
fi

collect_active_run_commands() {
  awk '
    {
      if (in_block) {
        if ($0 ~ /^[[:space:]]*$/) {
          next
        }

        current_indent = match($0, /[^ ]/) - 1
        if (current_indent > block_indent) {
          line = $0
          sub(/^[[:space:]]+/, "", line)
          if (line != "" && line !~ /^#/) {
            print line
          }
          next
        }

        in_block = 0
      }

      if ($0 ~ /^[[:space:]]*run:[[:space:]]*[|>]-?[[:space:]]*$/) {
        block_indent = match($0, /[^ ]/) - 1
        in_block = 1
        next
      }

      if ($0 ~ /^[[:space:]]*run:[[:space:]]*[^|>]/) {
        line = $0
        sub(/^[[:space:]]*run:[[:space:]]*/, "", line)
        if (line != "" && line !~ /^#/) {
          print line
        }
      }
    }
  ' "${workflow_path}"
}

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"
active_run_commands="$(collect_active_run_commands)"

for command in "${required_verifiers[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 10 verifier command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_tests[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 10 focused shell test command in CI workflow: ${command}" >&2
    exit 1
  fi
done

if ! grep -Eq "^[[:space:]]*- name: ${self_guard_step_name}\$" "${workflow_path}"; then
  echo "Missing dedicated Phase 10 workflow coverage guard step in CI workflow: ${self_guard_step_name}" >&2
  exit 1
fi

self_guard_count="$(grep -Fxc -- "${self_guard_command}" <<<"${active_run_commands}" || true)"
if [[ "${self_guard_count}" -lt 2 ]]; then
  echo "Phase 10 workflow coverage checker must run both as a dedicated guard and within focused shell tests." >&2
  exit 1
fi

echo "CI workflow includes the required Phase 10 verifier and focused shell test commands."
