#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
design_doc="${repo_root}/docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md"
validation_doc="${repo_root}/docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract-validation.md"
readme_doc="${repo_root}/README.md"
roadmap_doc="${repo_root}/docs/Revised Phase23-20 Epic Roadmap.md"
phase15_doc="${repo_root}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
state_model_doc="${repo_root}/docs/control-plane-state-model.md"
phase24_tests="${repo_root}/control-plane/tests/test_phase24_live_assistant_workflow_docs.py"
phase24_runtime_tests="${repo_root}/control-plane/tests/test_phase24_live_assistant_validation.py"
workflow_path="${repo_root}/.github/workflows/ci.yml"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_contains() {
  local path="$1"
  local expected="$2"

  if ! grep -F -- "${expected}" "${path}" >/dev/null; then
    echo "Missing required text in ${path}: ${expected}" >&2
    exit 1
  fi
}

collect_active_step_run_commands() {
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
            print current_step "\t" line
          }
          next
        }

        in_block = 0
      }

      if ($0 ~ /^[[:space:]]*-[[:space:]]name:[[:space:]]+/) {
        current_step = $0
        sub(/^[[:space:]]*-[[:space:]]name:[[:space:]]+/, "", current_step)
        next
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
          print current_step "\t" line
        }
      }
    }
  ' "${workflow_path}"
}

collect_active_run_commands() {
  collect_active_step_run_commands | cut -f2-
}

collect_active_step_commands() {
  local step_name="$1"

  collect_active_step_run_commands |
    awk -F $'\t' -v step_name="${step_name}" '$1 == step_name { print $2 }'
}

require_active_run_command() {
  local active_commands="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" <<<"${active_commands}" >/dev/null; then
    echo "Missing active CI command in ${workflow_path}: ${expected}" >&2
    exit 1
  fi
}

require_active_step_command() {
  local step_name="$1"
  local expected="$2"
  local step_commands=""

  step_commands="$(extract_step_run_commands "${step_name}")"
  if [[ -z "${step_commands}" ]]; then
    echo "Missing active command in CI step \"${step_name}\": ${expected}" >&2
    exit 1
  fi

  if ! grep -Fqx -- "${expected}" <<<"${step_commands}" >/dev/null; then
    echo "Missing active command in CI step \"${step_name}\": ${expected}" >&2
    exit 1
  fi
}

require_file "${design_doc}" "Missing Phase 24 workflow contract design document"
require_file "${validation_doc}" "Missing Phase 24 workflow contract validation note"
require_file "${readme_doc}" "Missing README"
require_file "${roadmap_doc}" "Missing revised roadmap"
require_file "${phase15_doc}" "Missing Phase 15 assistant boundary doc"
require_file "${state_model_doc}" "Missing control-plane state model"
require_file "${phase24_tests}" "Missing Phase 24 workflow contract doc tests"
require_file "${phase24_runtime_tests}" "Missing Phase 24 live assistant runtime validation tests"
require_file "${workflow_path}" "Missing CI workflow"

require_contains "${design_doc}" "# AegisOps Phase 24 First Live Assistant Workflow Family and Trusted Output Contract"
require_contains "${design_doc}" "The first live assistant workflow family is a bounded reviewed summarization family."
require_contains "${design_doc}" "- \`queue triage summary\`"
require_contains "${design_doc}" "- \`case summary\`"
require_contains "${design_doc}" "This first live assistant workflow family does not include next-step recommendation draft generation"
require_contains "${design_doc}" "The assistant remains advisory-only."
require_contains "${design_doc}" "Allowed fields:"
require_contains "${design_doc}" "| \`workflow_family\` |"
require_contains "${design_doc}" "| \`workflow_task\` |"
require_contains "${design_doc}" "| \`status\` |"
require_contains "${design_doc}" "| \`summary\` |"
require_contains "${design_doc}" "| \`citations\` |"
require_contains "${design_doc}" "| \`unresolved_reasons\` |"
require_contains "${design_doc}" "Required citation fields:"
require_contains "${design_doc}" "If required citations are missing, the workflow must force \`unresolved\`."
require_contains "${design_doc}" "If reviewed records conflict on lifecycle state, ownership, scope, or evidence-backed facts."
require_contains "${design_doc}" "If the operator request asks for approval, delegation, execution, or policy interpretation."
require_contains "${design_doc}" "Approval, delegation, execution, and policy authority outside the assistant boundary must remain on the reviewed human and control-plane path."

require_contains "${validation_doc}" "# Phase 24 First Live Assistant Workflow Family and Trusted Output Contract Validation"
require_contains "${validation_doc}" "Validation status: PASS"
require_contains "${validation_doc}" "docs/Revised Phase23-20 Epic Roadmap.md"
require_contains "${validation_doc}" "README.md"
require_contains "${validation_doc}" "docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
require_contains "${validation_doc}" "authority model"
require_contains "${validation_doc}" "No deviations found."

require_contains "${readme_doc}" "bounded live assistant workflow family"
require_contains "${readme_doc}" "queue triage summary and case summary"
require_contains "${readme_doc}" "The assistant remains advisory-only"

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"

active_run_commands="$(collect_active_run_commands)"

require_active_step_command \
  "Run Phase 24 live assistant workflow contract validation" \
  "bash scripts/verify-phase-24-live-assistant-workflow-contract.sh"
require_active_step_command \
  "Run Phase 24 live assistant workflow contract validation" \
  "python3 -m unittest control-plane.tests.test_phase24_live_assistant_workflow_docs"
require_active_step_command \
  "Run Phase 24 live assistant workflow contract validation" \
  "python3 -m unittest control-plane.tests.test_phase24_live_assistant_validation"
require_active_step_command \
  "Run Phase 24 workflow coverage guard" \
  "bash scripts/test-verify-ci-phase-24-workflow-coverage.sh"
require_active_run_command \
  "${active_run_commands}" \
  "bash scripts/test-verify-phase-24-live-assistant-workflow-contract.sh"

echo "Phase 24 live assistant workflow family remains bounded, cited, and advisory-only."
