#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
design_doc="${repo_root}/docs/phase-21-production-like-hardening-boundary-and-sequence.md"
validation_doc="${repo_root}/docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md"
phase20_doc="${repo_root}/docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
auth_doc="${repo_root}/docs/auth-baseline.md"
network_doc="${repo_root}/docs/network-exposure-and-access-path-policy.md"
runbook_doc="${repo_root}/docs/runbook.md"
automation_doc="${repo_root}/docs/automation-substrate-contract.md"
response_doc="${repo_root}/docs/response-action-safety-model.md"
source_onboarding_doc="${repo_root}/docs/source-onboarding-contract.md"
phase14_doc="${repo_root}/docs/phase-14-identity-rich-source-family-design.md"
phase18_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
wazuh_ingest_doc="${repo_root}/docs/wazuh-alert-ingest-contract.md"
state_model_doc="${repo_root}/docs/control-plane-state-model.md"
phase19_doc="${repo_root}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
phase17_doc="${repo_root}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
architecture_doc="${repo_root}/docs/architecture.md"
docs_test="${repo_root}/control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py"
validation_test="${repo_root}/control-plane/tests/test_phase21_production_like_hardening_boundary_validation.py"
end_to_end_test="${repo_root}/control-plane/tests/test_phase21_end_to_end_validation.py"
workflow_path="${repo_root}/.github/workflows/ci.yml"
phase_validation_step_name="Run Phase 21 production-like hardening boundary validation"
phase_coverage_guard_step_name="Run Phase 21 workflow coverage guard"
phase_coverage_guard_command="bash scripts/test-verify-ci-phase-21-workflow-coverage.sh"
roadmap_filename="Phase 16-21 Epic Roadmap.md"
roadmap_relative_path="docs/${roadmap_filename}"
roadmap_path="${repo_root}/${roadmap_relative_path}"

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

reject_fixed_line() {
  local path="$1"
  local unexpected="$2"

  if grep -Fqx -- "${unexpected}" "${path}" >/dev/null; then
    echo "Unexpected line in ${path}: ${unexpected}" >&2
    exit 1
  fi
}

require_file "${design_doc}" "Missing Phase 21 production-like hardening design doc"
require_file "${validation_doc}" "Missing Phase 21 production-like hardening validation doc"
require_file "${phase20_doc}" "Missing Phase 20 boundary doc"
require_file "${auth_doc}" "Missing auth baseline doc"
require_file "${network_doc}" "Missing network exposure policy doc"
require_file "${runbook_doc}" "Missing runbook doc"
require_file "${automation_doc}" "Missing automation substrate contract doc"
require_file "${response_doc}" "Missing response action safety model doc"
require_file "${source_onboarding_doc}" "Missing source onboarding contract doc"
require_file "${phase14_doc}" "Missing Phase 14 identity-rich source family design doc"
require_file "${phase18_doc}" "Missing Phase 18 live ingest contract doc"
require_file "${wazuh_ingest_doc}" "Missing Wazuh alert ingest contract doc"
require_file "${state_model_doc}" "Missing control-plane state model doc"
require_file "${phase19_doc}" "Missing Phase 19 operator surface doc"
require_file "${phase17_doc}" "Missing Phase 17 runtime config contract doc"
require_file "${architecture_doc}" "Missing architecture overview doc"
require_file "${docs_test}" "Missing Phase 21 docs unittest"
require_file "${validation_test}" "Missing Phase 21 validation unittest"
require_file "${end_to_end_test}" "Missing Phase 21 end-to-end validation unittest"
require_file "${workflow_path}" "Missing CI workflow"

design_required_lines=(
  '# AegisOps Phase 21 Production-Like Hardening Boundary and Sequence'
  '## 1. Purpose'
  '## 2. Reviewed Phase 21 Hardening Boundary'
  '### 2.1 Auth, Service Accounts, and Secret Scope'
  '### 2.2 Reverse-Proxy, Admin Bootstrap, and Break-Glass Access'
  '### 2.3 Restore and Observability Boundary'
  '### 2.4 Topology Growth Conditions'
  '### 2.5 Reviewed Second-Source Onboarding Target'
  '## 3. Fixed Implementation Sequence'
  '### 3.1 Sequence Rules'
  '## 4. Explicit Out of Scope and Non-Expansion Rules'
  '## 5. Alignment and Governing Contracts'
  '`single-node Wazuh -> reviewed reverse proxy -> AegisOps control plane -> PostgreSQL -> reviewed Shuffle delegation for notify_identity_owner`'
  'The approved first reviewed second live source to onboard after the existing GitHub audit live slice is Entra ID.'
  '`GitHub audit -> Entra ID -> Microsoft 365 audit`'
  '`auth and secrets -> admin bootstrap and break-glass controls -> restore proof -> observability proof -> topology growth gate review -> Entra ID second-source onboarding`'
  'Phase 21 therefore defines the reviewed conditions that must be met before AegisOps grows from the current one-node operating shape toward two-node or broader deployment patterns.'
  'The reviewed topology-growth gate is therefore a one-node-to-multi-node admission review rather than pre-approval for cluster rollout.'
  'The reviewed second-source onboarding boundary must reuse the existing control-plane contracts for payload admission, dedupe, restatement, evidence preservation, case linkage, and thin operator-surface visibility.'
  'Phase 21 does not approve a parallel intake, evidence, case, or operator model for the second source.'
  'Phase 21 does not approve IdP-driven self-service role expansion, mailbox-backed service identities, shared administrator logins, source-side credentials stored in Git, or credentials that silently span monitoring, approval, workflow execution, and platform administration.'
  'The break-glass path is a recovery exception only. It must not become an alternate approval path, a permanent operator shortcut, or a way to bypass the reviewed reverse proxy and control-plane authority model.'
  'Phase 21 does not approve broad SIEM replacement analytics, broad metrics-platform rollout, after-hours autonomous operations, or observability-driven authority shortcuts that move approval or reconciliation truth outside AegisOps.'
  'Phase 21 must not reorder this sequence to onboard Entra ID before auth, secrets, restore, and observability are reviewed.'
  'Phase 21 preserves the completed Phase 20 first live low-risk action exactly as the current approved live path.'
  '- broad multi-source breadth beyond the reviewed GitHub audit live slice plus one reviewed Entra ID follow-on target;'
  '- broad UI expansion, dashboard breadth, or interactive assistant growth beyond the completed thin operator surface;'
  '- broader action catalogs, unattended execution, or any medium-risk or high-risk live action growth;'
  '- any change that weakens the completed Phase 20 operator-to-approval-to-delegation path for `notify_identity_owner`.'
)

for line in "${design_required_lines[@]}"; do
  require_fixed_line "${design_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 21 Production-Like Hardening Boundary and Sequence Validation'
  '- Validation date: 2026-04-13'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the reviewed Phase 21 boundary is production-like hardening around the completed Phase 20 live path rather than a new breadth phase.'
  'Confirmed the approved hardening scope explicitly covers auth and secrets, service-account ownership, reverse-proxy protections, admin bootstrap, break-glass access, restore, observability, topology-growth conditions, and one reviewed second-source onboarding target.'
  'Confirmed the fixed implementation order is `auth and secrets -> admin bootstrap and break-glass controls -> restore proof -> observability proof -> topology growth gate review -> Entra ID second-source onboarding`.'
  'Confirmed the design preserves the completed Phase 20 operator-to-approval-to-delegation path for `notify_identity_owner` and does not reopen broader action catalogs, unattended execution, or higher-risk live action growth.'
  'Confirmed Entra ID is the first reviewed second live source to onboard after the existing GitHub audit live slice, with the reviewed next identity-rich source order staying `GitHub audit -> Entra ID -> Microsoft 365 audit`.'
  'Confirmed topology growth remains conditional only and cannot proceed unless auth, ingress, restore, observability, and authority-boundary guarantees remain intact across the one-node-to-multi-node admission review.'
  'Confirmed the reviewed second-source onboarding boundary reuses the existing payload-admission, dedupe, restatement, evidence-preservation, case-linkage, and thin-operator-surface contracts rather than introducing a parallel second-source model.'
  'Confirmed explicit non-expansion rules keep broad multi-source breadth, broad UI expansion, direct vendor-local actioning, and production-scale topology claims out of scope for Phase 21.'
)

if [[ -f "${roadmap_path}" ]]; then
  validation_required_lines+=(
    '- Validation status: PASS'
    "Confirmed comparison against \`${roadmap_filename}\` completed using \`${roadmap_relative_path}\` as the reviewed roadmap baseline."
  )
  reject_fixed_line "${validation_doc}" '- Validation status: FAIL'
  reject_fixed_line "${validation_doc}" "The issue requested review against \`${roadmap_filename}\`, but that roadmap file was not present in the local worktree and could not be located via repository search during this validation snapshot."
  reject_fixed_line "${validation_doc}" "Validation cannot pass until the requested \`${roadmap_filename}\` comparison is completed from a reviewed local artifact."
  reject_fixed_line "${validation_doc}" "- Requested comparison target \`${roadmap_filename}\` was unavailable in the local worktree during this validation snapshot."
else
  validation_required_lines+=(
    '- Validation status: FAIL'
    "The issue requested review against \`${roadmap_filename}\`, but that roadmap file was not present in the local worktree and could not be located via repository search during this validation snapshot."
    "Validation cannot pass until the requested \`${roadmap_filename}\` comparison is completed from a reviewed local artifact."
    "- Requested comparison target \`${roadmap_filename}\` was unavailable in the local worktree during this validation snapshot."
  )
  reject_fixed_line "${validation_doc}" '- Validation status: PASS'
fi

for line in "${validation_required_lines[@]}"; do
  require_fixed_line "${validation_doc}" "${line}"
done

required_artifacts=(
  "docs/phase-21-production-like-hardening-boundary-and-sequence.md"
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md"
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
  "docs/auth-baseline.md"
  "docs/network-exposure-and-access-path-policy.md"
  "docs/runbook.md"
  "docs/automation-substrate-contract.md"
  "docs/response-action-safety-model.md"
  "docs/source-onboarding-contract.md"
  "docs/phase-14-identity-rich-source-family-design.md"
  "docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
  "docs/wazuh-alert-ingest-contract.md"
  "docs/control-plane-state-model.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py"
  "control-plane/tests/test_phase21_production_like_hardening_boundary_validation.py"
  "control-plane/tests/test_phase21_end_to_end_validation.py"
  "scripts/verify-phase-21-production-like-hardening-boundary.sh"
  "scripts/test-verify-phase-21-production-like-hardening-boundary.sh"
  "scripts/test-verify-ci-phase-21-workflow-coverage.sh"
  ".github/workflows/ci.yml"
)

if [[ -f "${roadmap_path}" ]]; then
  required_artifacts+=("${roadmap_relative_path}")
fi

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 21 artifact"
  require_fixed_line "${validation_doc}" "- \`${artifact}\`"
done

require_fixed_line "${validation_doc}" '- Verification commands: `python3 -m unittest control-plane.tests.test_phase21_end_to_end_validation control-plane.tests.test_phase21_production_like_hardening_boundary_docs control-plane.tests.test_phase21_production_like_hardening_boundary_validation`, `bash scripts/verify-phase-21-production-like-hardening-boundary.sh`, `bash scripts/test-verify-phase-21-production-like-hardening-boundary.sh`, `bash scripts/test-verify-ci-phase-21-workflow-coverage.sh`'
require_fixed_line "${docs_test}" 'class Phase21ProductionLikeHardeningBoundaryDocsTests(unittest.TestCase):'
require_fixed_line "${docs_test}" '    def test_phase21_design_doc_exists(self) -> None:'
require_fixed_line "${docs_test}" '    def test_phase21_design_doc_defines_boundary_sequence_and_non_expansion_rules(self) -> None:'
require_fixed_line "${validation_test}" 'class Phase21ProductionLikeHardeningBoundaryValidationTests(unittest.TestCase):'
require_fixed_line "${validation_test}" '    def test_phase21_validation_artifacts_cross_reference_governing_contracts(self) -> None:'
require_fixed_line "${end_to_end_test}" 'class Phase21EndToEndValidationTests(unittest.TestCase):'
require_fixed_line "${end_to_end_test}" '    def test_phase21_end_to_end_auth_boundaries_fail_closed_and_emit_observability('
require_fixed_line "${end_to_end_test}" '    def test_phase21_end_to_end_restore_and_readiness_preserve_phase20_live_path('
require_fixed_line "${end_to_end_test}" '    def test_phase21_end_to_end_second_source_onboarding_stays_narrow('
require_fixed_line "${workflow_path}" '      - name: Run Phase 21 production-like hardening boundary validation'
require_fixed_line "${workflow_path}" '      - name: Run Phase 21 workflow coverage guard'
require_fixed_line "${workflow_path}" '        run: bash scripts/test-verify-ci-phase-21-workflow-coverage.sh'

. "${repo_root}/scripts/ci-workflow-phase-helper.sh"

active_run_commands="$(collect_active_run_commands)"
phase_validation_commands="$(extract_step_run_commands "${phase_validation_step_name}")"

if [[ -z "${phase_validation_commands}" ]]; then
  echo "Missing CI workflow step commands for ${phase_validation_step_name}" >&2
  exit 1
fi

for command in \
  "bash scripts/verify-phase-21-production-like-hardening-boundary.sh" \
  "python3 -m unittest control-plane.tests.test_phase21_end_to_end_validation control-plane.tests.test_phase21_production_like_hardening_boundary_docs control-plane.tests.test_phase21_production_like_hardening_boundary_validation"
do
  if ! grep -Fqx -- "${command}" <<<"${phase_validation_commands}" >/dev/null; then
    echo "Missing required Phase 21 validation command in ${phase_validation_step_name}: ${command}" >&2
    exit 1
  fi
done

if ! grep -Fqx -- "bash scripts/test-verify-phase-21-production-like-hardening-boundary.sh" <<<"${active_run_commands}" >/dev/null; then
  echo "Missing required Phase 21 focused shell test command in CI workflow: bash scripts/test-verify-phase-21-production-like-hardening-boundary.sh" >&2
  exit 1
fi

phase_coverage_guard_commands="$(extract_step_run_commands "${phase_coverage_guard_step_name}")"
if [[ -z "${phase_coverage_guard_commands}" ]]; then
  echo "Missing dedicated Phase 21 workflow coverage guard step in CI workflow: ${phase_coverage_guard_step_name}" >&2
  exit 1
fi

if [[ "$(printf '%s\n' "${phase_coverage_guard_commands}")" != "${phase_coverage_guard_command}" ]]; then
  echo "Dedicated Phase 21 workflow coverage guard step must run exactly: ${phase_coverage_guard_command}" >&2
  echo "Found:" >&2
  printf '%s\n' "${phase_coverage_guard_commands}" >&2
  exit 1
fi

echo "Phase 21 production-like hardening design and validation artifacts are present and aligned."
