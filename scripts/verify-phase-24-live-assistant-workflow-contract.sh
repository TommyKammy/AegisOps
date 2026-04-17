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

require_file "${design_doc}" "Missing Phase 24 workflow contract design document"
require_file "${validation_doc}" "Missing Phase 24 workflow contract validation note"
require_file "${readme_doc}" "Missing README"
require_file "${roadmap_doc}" "Missing revised roadmap"
require_file "${phase15_doc}" "Missing Phase 15 assistant boundary doc"
require_file "${state_model_doc}" "Missing control-plane state model"
require_file "${phase24_tests}" "Missing Phase 24 workflow contract doc tests"
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

require_contains "${workflow_path}" "      - name: Run Phase 24 live assistant workflow contract validation"
require_contains "${workflow_path}" "          bash scripts/verify-phase-24-live-assistant-workflow-contract.sh"
require_contains "${workflow_path}" "          python3 -m unittest control-plane.tests.test_phase24_live_assistant_workflow_docs"
require_contains "${workflow_path}" "      - name: Run Phase 24 workflow coverage guard"
require_contains "${workflow_path}" "        run: bash scripts/test-verify-ci-phase-24-workflow-coverage.sh"
require_contains "${workflow_path}" "          bash scripts/test-verify-phase-24-live-assistant-workflow-contract.sh"

echo "Phase 24 live assistant workflow family remains bounded, cited, and advisory-only."
