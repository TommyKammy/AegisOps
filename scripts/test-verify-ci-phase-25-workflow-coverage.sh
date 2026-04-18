#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
workflow_path="${repo_root}/.github/workflows/ci.yml"

required_verifiers=(
  "bash scripts/verify-phase-25-multi-source-case-review-runbook.sh"
)

required_tests=(
  "bash scripts/test-verify-phase-25-multi-source-case-review-runbook.sh"
)

required_runtime_commands=(
  "python3 -m unittest control-plane.tests.test_phase25_multi_source_case_admission_docs"
  "python3 -m unittest control-plane.tests.test_phase25_osquery_host_context_validation"
)

self_guard_step_name="Run Phase 25 workflow coverage guard"
self_guard_command="bash scripts/test-verify-ci-phase-25-workflow-coverage.sh"
focused_shell_tests_step_name="Run focused shell tests"

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

extract_step_run_commands() {
  local step_name="${1}"

  awk -v step_name="${step_name}" '
    function line_indent(line) {
      return match(line, /[^ ]/) - 1
    }

    BEGIN {
      in_step = 0
      step_indent = -1
      in_block = 0
      block_indent = -1
    }

    {
      if (in_step) {
        if ($0 ~ /^[[:space:]]*-[[:space:]]name:[[:space:]]+/ && line_indent($0) <= step_indent) {
          exit 0
        }

        if (in_block) {
          if ($0 ~ /^[[:space:]]*$/) {
            next
          }

          current_indent = line_indent($0)
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
          block_indent = line_indent($0)
          in_block = 1
          next
        }

        if ($0 ~ /^[[:space:]]*run:[[:space:]]*/) {
          line = $0
          sub(/^[[:space:]]*run:[[:space:]]*/, "", line)
          if (line != "" && line !~ /^#/) {
            print line
          }
          next
        }
      }

      line = $0
      sub(/^[[:space:]]+/, "", line)
      if (line == "- name: " step_name) {
        in_step = 1
        step_indent = line_indent($0)
      }
    }
  ' "${workflow_path}"
}

active_run_commands="$(collect_active_run_commands)"

for command in "${required_verifiers[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 25 verifier command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_tests[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 25 focused shell test command in CI workflow: ${command}" >&2
    exit 1
  fi
done

for command in "${required_runtime_commands[@]}"; do
  if ! grep -Fqx -- "${command}" <<<"${active_run_commands}" >/dev/null; then
    echo "Missing Phase 25 focused runtime command in CI workflow: ${command}" >&2
    exit 1
  fi
done

self_guard_step_run_commands="$(extract_step_run_commands "${self_guard_step_name}")"
focused_shell_tests_commands="$(extract_step_run_commands "${focused_shell_tests_step_name}")"

if [[ -z "${self_guard_step_run_commands}" ]]; then
  echo "Missing dedicated Phase 25 workflow coverage guard step in CI workflow: ${self_guard_step_name}" >&2
  exit 1
fi

self_guard_step_run_command="$(head -n 1 <<<"${self_guard_step_run_commands}")"
if [[ -z "${self_guard_step_run_command}" ]]; then
  echo "Missing dedicated Phase 25 workflow coverage guard step in CI workflow: ${self_guard_step_name}" >&2
  exit 1
fi

if [[ "${self_guard_step_run_command}" != "${self_guard_command}" ]]; then
  echo "Dedicated Phase 25 workflow coverage guard step must run exactly: ${self_guard_command}" >&2
  echo "Found: ${self_guard_step_run_command}" >&2
  exit 1
fi

self_guard_count="$(grep -Fxc -- "${self_guard_command}" <<<"${active_run_commands}" || true)"
focused_self_guard_count="$(grep -Fxc -- "${self_guard_command}" <<<"${focused_shell_tests_commands}" || true)"
if [[ "${focused_self_guard_count}" -lt 1 || "${self_guard_count}" -lt 2 ]]; then
  echo "Phase 25 workflow coverage checker must run both as a dedicated guard and within focused shell tests." >&2
  exit 1
fi

echo "CI workflow includes the required Phase 25 verifier, focused shell test, and focused runtime commands."
