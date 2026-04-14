#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
design_doc="${repo_root}/docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md"
validation_doc="${repo_root}/docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence-validation.md"
phase19_doc="${repo_root}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
phase20_doc="${repo_root}/docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
phase21_doc="${repo_root}/docs/phase-21-production-like-hardening-boundary-and-sequence.md"
state_model_doc="${repo_root}/docs/control-plane-state-model.md"
automation_doc="${repo_root}/docs/automation-substrate-contract.md"
response_doc="${repo_root}/docs/response-action-safety-model.md"
business_hours_doc="${repo_root}/docs/secops-business-hours-operating-model.md"
architecture_doc="${repo_root}/docs/architecture.md"
docs_test="${repo_root}/control-plane/tests/test_phase22_operator_trust_boundary_docs.py"
validation_test="${repo_root}/control-plane/tests/test_phase22_operator_trust_boundary_validation.py"
workflow_path="${repo_root}/.github/workflows/ci.yml"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_line() {
  local path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${path}" >/dev/null; then
    echo "Missing required line in ${path}: ${expected}" >&2
    exit 1
  fi
}

require_file "${design_doc}" "Missing Phase 22 operator trust design doc"
require_file "${validation_doc}" "Missing Phase 22 operator trust validation doc"
require_file "${phase19_doc}" "Missing Phase 19 operator surface design doc"
require_file "${phase20_doc}" "Missing Phase 20 low-risk action design doc"
require_file "${phase21_doc}" "Missing Phase 21 hardening design doc"
require_file "${state_model_doc}" "Missing control-plane state model doc"
require_file "${automation_doc}" "Missing automation substrate contract doc"
require_file "${response_doc}" "Missing response action safety model doc"
require_file "${business_hours_doc}" "Missing business-hours operating model doc"
require_file "${architecture_doc}" "Missing architecture overview doc"
require_file "${docs_test}" "Missing Phase 22 doc unittest"
require_file "${validation_test}" "Missing Phase 22 validation unittest"
require_file "${workflow_path}" "Missing CI workflow"

design_required_lines=(
  '# AegisOps Phase 22 Operator Trust and Workflow Ergonomics Boundary and Sequence'
  '## 1. Purpose'
  '## 2. Reviewed Phase 22 Boundary'
  '## 3. Operator Visibility Contract'
  '## 4. Reviewed Approval State Semantics'
  '## 5. Mismatch Taxonomy and Inspection Expectations'
  '## 6. Reviewed Record Requirements for Handoff and Fallback'
  '## 7. Fixed Implementation Sequence'
  '## 8. Explicit Out of Scope and Non-Expansion Rules'
  '## 9. Alignment and Governing Contracts'
  'The approved Phase 22 path is:'
  '`Action Request -> Approval Decision -> Delegation -> Action Execution -> Reconciliation`'
  'The approved Phase 22 boundary is a review and ergonomics phase around the already-approved Phase 19 through Phase 21 path rather than a new execution-breadth phase.'
  'Pending means the action request exists, the reviewed approval decision is not yet resolved, and no delegation or execution may proceed.'
  'Expired means the reviewed approval window closed before a valid delegation consumed the approved request.'
  'Rejected means an approver explicitly denied the reviewed action request for the current payload and scope.'
  'Superseded means a later reviewed request or approval record replaced the earlier candidate before execution.'
  'The reviewed mismatch taxonomy is limited to delegation mismatch, execution mismatch, and reconciliation mismatch.'
  'The minimum reviewed record additions in Phase 22 are manual fallback visibility, after-hours handoff visibility, escalation-note visibility, and actor identity display expectations.'
  'Phase 22 does not approve a new live action class, broad browser-first redesign, or AI authority expansion.'
  'Phase 22 must preserve the completed Phase 19 through Phase 21 fail-closed boundaries and the reviewed Phase 20 approval / delegation / reconciliation binding guarantees.'
)

for line in "${design_required_lines[@]}"; do
  require_fixed_line "${design_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 22 Operator Trust and Workflow Ergonomics Boundary and Sequence Validation'
  '- Validation date: 2026-04-14'
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the reviewed Phase 22 boundary improves operator trust and workflow ergonomics around the existing action-review path without approving a new live action class, browser-first redesign, or AI authority expansion.'
  'Confirmed the design explicitly defines reviewed semantics for pending, expired, rejected, and superseded approval states across queue, alert, and case views.'
  'Confirmed the design explicitly defines a mismatch taxonomy for delegation mismatch, execution mismatch, and reconciliation mismatch, along with the minimum operator inspection expectations for each class.'
  'Confirmed the design requires reviewed visibility for manual fallback, after-hours handoff, escalation notes, and actor identity display before implementation may broaden operator-facing review surfaces.'
  'Confirmed the design preserves the completed Phase 19-21 fail-closed boundaries and the reviewed Phase 20 approval / delegation / reconciliation binding guarantees.'
  'The issue requested review against `Phase 16-21 Epic Roadmap.md`, but that roadmap file was not present in the local worktree and could not be located via repository search during this validation snapshot.'
  '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_line "${validation_doc}" "${line}"
done

required_artifacts=(
  "docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md"
  "docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence-validation.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
  "docs/phase-21-production-like-hardening-boundary-and-sequence.md"
  "docs/control-plane-state-model.md"
  "docs/automation-substrate-contract.md"
  "docs/response-action-safety-model.md"
  "docs/secops-business-hours-operating-model.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase22_operator_trust_boundary_docs.py"
  "control-plane/tests/test_phase22_operator_trust_boundary_validation.py"
  "scripts/verify-phase-22-operator-trust-boundary.sh"
  "scripts/test-verify-phase-22-operator-trust-boundary.sh"
  "scripts/test-verify-ci-phase-22-workflow-coverage.sh"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 22 artifact"
  require_fixed_line "${validation_doc}" "- \`${artifact}\`"
done

require_fixed_line "${validation_doc}" '- Verification commands: `python3 -m unittest control-plane.tests.test_phase22_operator_trust_boundary_docs control-plane.tests.test_phase22_operator_trust_boundary_validation`, `bash scripts/verify-phase-22-operator-trust-boundary.sh`, `bash scripts/test-verify-phase-22-operator-trust-boundary.sh`, `bash scripts/test-verify-ci-phase-22-workflow-coverage.sh`'
require_fixed_line "${docs_test}" 'class Phase22OperatorTrustBoundaryDocsTests(unittest.TestCase):'
require_fixed_line "${docs_test}" '    def test_phase22_design_doc_exists(self) -> None:'
require_fixed_line "${docs_test}" '    def test_phase22_design_doc_defines_state_semantics_mismatch_taxonomy_and_boundary('
require_fixed_line "${validation_test}" 'class Phase22OperatorTrustBoundaryValidationTests(unittest.TestCase):'
require_fixed_line "${validation_test}" '    def test_phase22_validation_artifacts_cross_reference_governing_contracts(self) -> None:'
require_fixed_line "${workflow_path}" '      - name: Run Phase 22 operator trust boundary validation'
require_fixed_line "${workflow_path}" '          bash scripts/verify-phase-22-operator-trust-boundary.sh'
require_fixed_line "${workflow_path}" '          python3 -m unittest control-plane.tests.test_phase22_operator_trust_boundary_docs control-plane.tests.test_phase22_operator_trust_boundary_validation'
require_fixed_line "${workflow_path}" '      - name: Run Phase 22 workflow coverage guard'
require_fixed_line "${workflow_path}" '        run: bash scripts/test-verify-ci-phase-22-workflow-coverage.sh'
require_fixed_line "${workflow_path}" '          bash scripts/test-verify-phase-22-operator-trust-boundary.sh'

echo "Phase 22 operator trust design and validation artifacts are present and aligned."
