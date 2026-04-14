#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
design_doc="${repo_root}/docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
validation_doc="${repo_root}/docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary-validation.md"
phase19_doc="${repo_root}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
phase19_validation_doc="${repo_root}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md"
automation_doc="${repo_root}/docs/automation-substrate-contract.md"
response_doc="${repo_root}/docs/response-action-safety-model.md"
state_model_doc="${repo_root}/docs/control-plane-state-model.md"
business_hours_doc="${repo_root}/docs/secops-business-hours-operating-model.md"
architecture_doc="${repo_root}/docs/architecture.md"
docs_test="${repo_root}/control-plane/tests/test_phase20_low_risk_action_docs.py"
runtime_validation_test="${repo_root}/control-plane/tests/test_phase20_low_risk_action_validation.py"
service_test_doc="${repo_root}/control-plane/tests/test_service_persistence_action_reconciliation.py"
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

require_file "${design_doc}" "Missing Phase 20 low-risk action design doc"
require_file "${validation_doc}" "Missing Phase 20 low-risk action validation doc"
require_file "${phase19_doc}" "Missing Phase 19 operator surface design doc"
require_file "${phase19_validation_doc}" "Missing Phase 19 operator surface validation doc"
require_file "${automation_doc}" "Missing automation substrate contract doc"
require_file "${response_doc}" "Missing response action safety model doc"
require_file "${state_model_doc}" "Missing control-plane state model doc"
require_file "${business_hours_doc}" "Missing business-hours operating model doc"
require_file "${architecture_doc}" "Missing architecture overview doc"
require_file "${docs_test}" "Missing Phase 20 doc unittest"
require_file "${runtime_validation_test}" "Missing Phase 20 runtime validation unittest"
require_file "${service_test_doc}" "Missing service persistence test suite"
require_file "${workflow_path}" "Missing CI workflow"

design_required_lines=(
  '# AegisOps Phase 20 First Live Low-Risk Action and Reviewed Delegation Boundary'
  '## 1. Purpose'
  '## 2. Approved First Live Low-Risk Action'
  '## 3. Approved Action Shape'
  '## 4. Operator-to-Approval-to-Delegation Boundary'
  '### 4.1 Human-Owned Steps'
  '### 4.2 Shuffle-Delegated Steps'
  '## 5. Required Binding and Expiry Checks'
  '## 6. Reconciliation Expectations'
  '## 7. Deferred Beyond Phase 20'
  '## 8. Alignment and Non-Expansion Rules'
  'The approved first live low-risk action for Phase 20 is `notify_identity_owner`.'
  'This action is the reviewed single-recipient owner-notification path for one accountable human owner or explicitly designated escalation contact tied to the in-scope alert, case, and evidence set already reviewed inside AegisOps.'
  'The approved first live path is intentionally narrower than a general notification framework. It is limited to a single-recipient owner-notification path rather than ticket creation, chat-room fanout, pager trees, broad stakeholder broadcast, or any action that implicitly changes workflow ownership outside the reviewed case.'
  '`reviewed Phase 19 casework -> explicit action request -> human approval -> reviewed Shuffle delegation -> authoritative reconciliation`'
  'Phase 20 keeps the human approver in the loop even though Phase 13 established a broader low-risk routing capability. Policy-authorized unattended low-risk execution remains deferred until a later reviewed phase narrows that broader authority explicitly.'
  'Shuffle must not become the authority for action intent, recipient selection, approval truth, execution truth, or reconciliation truth.'
  '- `approval_decision_id`;'
  '- `delegation_id`;'
  '- `payload_hash`; and'
  '- the approved expiry window carried by the approval and request records.'
  '- the approved payload no longer matches the action request target scope, recipient binding, or reviewed execution surface;'
  '- the approved expiry window does not match the action request expiry;'
  '- any broader action catalog beyond `notify_identity_owner`;'
  '- policy-authorized unattended low-risk execution;'
  '- any medium-risk or high-risk live action wiring;'
)

for line in "${design_required_lines[@]}"; do
  require_fixed_line "${design_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 20 First Live Low-Risk Action and Reviewed Delegation Boundary Validation'
  '- Validation date: 2026-04-12'
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the approved first live low-risk action is explicitly limited to `notify_identity_owner` as a single-recipient owner-notification path rather than a broad notification or ticketing catalog.'
  'Confirmed the reviewed Phase 20 path stays anchored to the Phase 19 operator surface by requiring reviewed casework, an explicit action request, explicit human approval, reviewed Shuffle delegation, and authoritative reconciliation.'
  'Confirmed the design keeps AegisOps authoritative for request, approval, execution, and reconciliation truth while using Shuffle only as the approved low-risk execution substrate for the already-approved transport step.'
  'Confirmed payload binding, approval expiry, and mismatch handling remain fail closed by requiring the reviewed path to preserve `approval_decision_id`, `delegation_id`, `idempotency_key`, `payload_hash`, execution-surface identity, and the approved expiry window before delegation may proceed.'
  'Confirmed focused repository-local coverage already exercises the current reviewed Shuffle path for `notify_identity_owner`, including approval recheck, payload-binding drift rejection, expiry-window drift rejection, target-scope drift rejection, authoritative reconciliation, and mismatch preservation in `control-plane/tests/test_service_persistence_action_reconciliation.py`.'
  'Confirmed deferred scope remains visible, including broader action catalogs, multi-recipient fanout, unattended low-risk execution, high-risk executor live wiring, and broad workflow orchestration.'
  'The issue requested review against `Phase 16-21 Epic Roadmap.md`, but that roadmap file was not present in the local worktree and could not be located via repository search during this validation snapshot.'
  '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_line "${validation_doc}" "${line}"
done

required_artifacts=(
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary-validation.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md"
  "docs/automation-substrate-contract.md"
  "docs/response-action-safety-model.md"
  "docs/control-plane-state-model.md"
  "docs/secops-business-hours-operating-model.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase20_low_risk_action_docs.py"
  "control-plane/tests/test_phase20_low_risk_action_validation.py"
  "control-plane/tests/test_service_persistence_action_reconciliation.py"
  "scripts/verify-phase-20-low-risk-action-boundary.sh"
  "scripts/test-verify-phase-20-low-risk-action-boundary.sh"
  "scripts/test-verify-ci-phase-20-workflow-coverage.sh"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 20 artifact"
  require_fixed_line "${validation_doc}" "- \`${artifact}\`"
done

require_fixed_line "${validation_doc}" '- Verification commands: `python3 -m unittest control-plane.tests.test_phase20_low_risk_action_docs control-plane.tests.test_phase20_low_risk_action_validation`, `bash scripts/verify-phase-20-low-risk-action-boundary.sh`, `bash scripts/test-verify-phase-20-low-risk-action-boundary.sh`, `bash scripts/test-verify-ci-phase-20-workflow-coverage.sh`'
require_fixed_line "${docs_test}" 'class Phase20LowRiskActionDocsTests(unittest.TestCase):'
require_fixed_line "${docs_test}" '    def test_phase20_design_doc_exists(self) -> None:'
require_fixed_line "${docs_test}" '    def test_phase20_design_doc_defines_one_approved_low_risk_action_and_boundary('
require_fixed_line "${runtime_validation_test}" 'class Phase20LowRiskActionValidationTests(unittest.TestCase):'
require_fixed_line "${runtime_validation_test}" '    def test_reviewed_runtime_path_covers_phase20_low_risk_action_boundary(self) -> None:'
require_fixed_line "${service_test_doc}" '    def test_service_delegates_approved_low_risk_action_through_shuffle_adapter('
require_fixed_line "${service_test_doc}" '    def test_service_rechecks_shuffle_approval_inside_transaction(self) -> None:'
require_fixed_line "${service_test_doc}" '    def test_service_rejects_shuffle_delegation_when_payload_binding_drifts('
require_fixed_line "${service_test_doc}" '    def test_service_rejects_shuffle_delegation_when_expiry_window_drifts_after_approval('
require_fixed_line "${service_test_doc}" '    def test_service_reconciles_shuffle_run_back_into_authoritative_action_execution('
require_fixed_line "${workflow_path}" '      - name: Run Phase 20 low-risk action boundary validation'
require_fixed_line "${workflow_path}" '          bash scripts/verify-phase-20-low-risk-action-boundary.sh'
require_fixed_line "${workflow_path}" '          python3 -m unittest control-plane.tests.test_phase20_low_risk_action_docs control-plane.tests.test_phase20_low_risk_action_validation'
require_fixed_line "${workflow_path}" '      - name: Run Phase 20 workflow coverage guard'
require_fixed_line "${workflow_path}" '        run: bash scripts/test-verify-ci-phase-20-workflow-coverage.sh'
require_fixed_line "${workflow_path}" '          bash scripts/test-verify-phase-20-low-risk-action-boundary.sh'

echo "Phase 20 low-risk action design and validation artifacts are present and aligned."
