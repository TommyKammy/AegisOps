#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
design_doc="${repo_root}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
validation_doc="${repo_root}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md"
phase18_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
phase18_validation_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-validation.md"
phase17_doc="${repo_root}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
phase16_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
phase15_guidance_doc="${repo_root}/docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md"
architecture_doc="${repo_root}/docs/architecture.md"
test_doc="${repo_root}/control-plane/tests/test_phase19_operator_surface_docs.py"
workflow_test_doc="${repo_root}/control-plane/tests/test_phase19_operator_workflow_validation.py"
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

require_file "${design_doc}" "Missing Phase 19 thin operator surface design doc"
require_file "${validation_doc}" "Missing Phase 19 thin operator surface validation doc"
require_file "${phase18_doc}" "Missing Phase 18 Wazuh lab topology doc"
require_file "${phase18_validation_doc}" "Missing Phase 18 Wazuh lab topology validation doc"
require_file "${phase17_doc}" "Missing Phase 17 runtime config contract doc"
require_file "${phase16_doc}" "Missing Phase 16 first-boot scope doc"
require_file "${phase15_guidance_doc}" "Missing Phase 15 analyst-assistant operating guidance doc"
require_file "${architecture_doc}" "Missing architecture overview doc"
require_file "${test_doc}" "Missing Phase 19 operator surface unittest"
require_file "${workflow_test_doc}" "Missing Phase 19 operator workflow validation unittest"
require_file "${workflow_path}" "Missing CI workflow"

design_required_lines=(
  '# AegisOps Phase 19 Thin Operator Surface and First Daily Analyst Workflow'
  '## 1. Purpose'
  '## 2. Approved Phase 19 Thin Operator Surface'
  '### 2.1 Approved Operator Reads'
  '### 2.2 Approved Bounded Analyst Actions'
  '## 3. First Daily Analyst Workflow'
  '### 3.1 Daily Queue Review'
  '### 3.2 Alert Inspection'
  '### 3.3 Casework Entry'
  '### 3.4 Evidence Review'
  '### 3.5 Cited Advisory Review'
  '## 4. Deferred Beyond Phase 19'
  '## 5. Alignment and Non-Expansion Rules'
  'This document defines the approved Phase 19 thin operator surface and first daily analyst workflow for the first live Wazuh-backed operator slice.'
  'AegisOps remains the primary daily work surface for the approved first live slice.'
  '- daily queue review data from the read-only analyst queue view for the reviewed `analyst_review` queue and `business_hours_triage` selection;'
  '- alert, case, and reconciliation detail linked to the selected queue item;'
  '- read-only evidence access through linked evidence identifiers, evidence records, native rule context, source identity, and reviewed context; and'
  '- cited advisory review through the approved assistant-context path that renders from reviewed control-plane records and linked evidence.'
  '- select a queue item from the reviewed analyst queue;'
  '- inspect alert, case, reconciliation, and evidence detail inside AegisOps;'
  '- promote an alert to a case when review requires tracked casework;'
  '- enter or update AegisOps-owned casework entry as reviewed notes, observations, findings, or recommendation drafts that stay cited to reviewed records and evidence; and'
  '- request a cited advisory review from the approved read-only assistant-context snapshot path.'
  '`daily queue review -> alert inspection -> casework entry -> evidence review -> cited advisory review`'
  'Read-only evidence access must preserve provenance and must not permit destructive evidence editing, silent evidence replacement, or substrate-local overwrite of the reviewed control-plane record set.'
  'Phase 19 cited advisory review must stay citation-first, uncertainty-preserving, and advisory-only as already required by the Phase 15 assistant boundary and operating guidance.'
  'Phase 19 does not approve free-form operator chat, autonomous assistant behavior, or any assistant path that can create approval, execution, or reconciliation authority.'
  '- broader dashboarding or general SOC workspace expansion;'
  '- full interactive assistant behavior or free-form assistant chat surfaces;'
  '- broader automation breadth beyond cited recommendation review;'
  '- medium-risk or high-risk live action wiring;'
)

for line in "${design_required_lines[@]}"; do
  require_fixed_line "${design_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 19 Thin Operator Surface and First Daily Analyst Workflow Validation'
  '- Validation date: 2026-04-11'
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the approved Phase 19 thin operator surface is explicitly limited to a reviewed queue-to-casework path on top of the completed Phase 18 live-path baseline rather than a broad SOC dashboard or substrate-native console workflow.'
  'Confirmed AegisOps as the primary daily work surface for the first live slice by keeping the approved operator reads inside the AegisOps analyst queue, linked alert and case detail, linked reconciliation context, read-only evidence access, and cited advisory review.'
  'Confirmed the approved first daily workflow is queue review through alert inspection, casework entry, evidence review, and cited advisory review.'
  'Confirmed the approved bounded analyst actions are limited to selecting a queue item, inspecting linked records, promoting an alert to a case when review requires tracked casework, entering cited AegisOps-owned casework entries, and requesting cited advisory review from the approved read-only assistant-context path.'
  'Confirmed the design keeps the first live slice anchored to the Wazuh-backed GitHub audit path already approved in Phase 18 and does not reopen live source admission, topology, or first-boot runtime scope.'
  'Confirmed the cited advisory path remains advisory-only, citation-first, uncertainty-preserving, and grounded in reviewed control-plane records and linked evidence instead of turning Phase 19 into full interactive assistant behavior.'
  'Confirmed deferred surfaces and actions remain visibly out of scope, including broader dashboarding, full interactive assistant behavior, broader automation breadth, direct substrate-side mutation, and medium-risk or high-risk live action wiring.'
  'The issue requested review against `Phase 16-21 Epic Roadmap.md`, but that roadmap file was not present in the local worktree and could not be located via repository search during this validation snapshot.'
  '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_line "${validation_doc}" "${line}"
done

required_artifacts=(
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md"
  "docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
  "docs/phase-18-wazuh-lab-topology-validation.md"
  "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  "docs/phase-16-release-state-and-first-boot-scope.md"
  "docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase19_operator_surface_docs.py"
  "control-plane/tests/test_phase19_operator_workflow_validation.py"
  "scripts/verify-phase-19-thin-operator-surface.sh"
  "scripts/test-verify-phase-19-thin-operator-surface.sh"
  "scripts/test-verify-ci-phase-19-workflow-coverage.sh"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 19 artifact"
  require_fixed_line "${validation_doc}" "- \`${artifact}\`"
done

require_fixed_line "${validation_doc}" '- Verification commands: `python3 -m unittest control-plane.tests.test_phase19_operator_surface_docs control-plane.tests.test_phase19_operator_workflow_validation`, `python3 -m unittest discover -s control-plane/tests -p '\''test_*.py'\''`, `bash scripts/verify-phase-19-thin-operator-surface.sh`, `bash scripts/test-verify-phase-19-thin-operator-surface.sh`, `bash scripts/test-verify-ci-phase-19-workflow-coverage.sh`'
require_fixed_line "${test_doc}" 'class Phase19OperatorSurfaceDocsTests(unittest.TestCase):'
require_fixed_line "${test_doc}" '    def test_phase19_design_doc_exists(self) -> None:'
require_fixed_line "${test_doc}" '    def test_phase19_design_doc_defines_operator_surface_workflow_and_deferred_scope(self) -> None:'
require_fixed_line "${test_doc}" '    def test_phase19_validation_doc_exists_and_records_alignment_caveat(self) -> None:'
require_fixed_line "${workflow_test_doc}" 'class Phase19OperatorWorkflowValidationTests(unittest.TestCase):'
require_fixed_line "${workflow_test_doc}" '    def test_reviewed_runtime_path_covers_approved_operator_workflow(self) -> None:'
require_fixed_line "${workflow_path}" '      - name: Run Phase 19 thin operator surface validation'
require_fixed_line "${workflow_path}" '          bash scripts/verify-phase-19-thin-operator-surface.sh'
require_fixed_line "${workflow_path}" '          python3 -m unittest control-plane.tests.test_phase19_operator_surface_docs control-plane.tests.test_phase19_operator_workflow_validation'
require_fixed_line "${workflow_path}" '      - name: Run Phase 19 workflow coverage guard'
require_fixed_line "${workflow_path}" '        run: bash scripts/test-verify-ci-phase-19-workflow-coverage.sh'
require_fixed_line "${workflow_path}" '          bash scripts/test-verify-phase-19-thin-operator-surface.sh'

echo "Phase 19 thin operator surface design and validation artifacts are present and aligned."
