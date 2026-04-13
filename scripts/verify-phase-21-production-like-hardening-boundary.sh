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
phase17_doc="${repo_root}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
architecture_doc="${repo_root}/docs/architecture.md"
docs_test="${repo_root}/control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py"
validation_test="${repo_root}/control-plane/tests/test_phase21_production_like_hardening_boundary_validation.py"
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
require_file "${phase17_doc}" "Missing Phase 17 runtime config contract doc"
require_file "${architecture_doc}" "Missing architecture overview doc"
require_file "${docs_test}" "Missing Phase 21 docs unittest"
require_file "${validation_test}" "Missing Phase 21 validation unittest"
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
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the reviewed Phase 21 boundary is production-like hardening around the completed Phase 20 live path rather than a new breadth phase.'
  'Confirmed the approved hardening scope explicitly covers auth and secrets, service-account ownership, reverse-proxy protections, admin bootstrap, break-glass access, restore, observability, topology-growth conditions, and one reviewed second-source onboarding target.'
  'Confirmed the fixed implementation order is `auth and secrets -> admin bootstrap and break-glass controls -> restore proof -> observability proof -> topology growth gate review -> Entra ID second-source onboarding`.'
  'Confirmed the design preserves the completed Phase 20 operator-to-approval-to-delegation path for `notify_identity_owner` and does not reopen broader action catalogs, unattended execution, or higher-risk live action growth.'
  'Confirmed Entra ID is the first reviewed second live source to onboard after the existing GitHub audit live slice, with the reviewed next identity-rich source order staying `GitHub audit -> Entra ID -> Microsoft 365 audit`.'
  'Confirmed topology growth remains conditional only and cannot proceed unless auth, ingress, restore, observability, and authority-boundary guarantees remain intact.'
  'Confirmed explicit non-expansion rules keep broad multi-source breadth, broad UI expansion, direct vendor-local actioning, and production-scale topology claims out of scope for Phase 21.'
  'The issue requested review against `Phase 16-21 Epic Roadmap.md`, but that roadmap file was not present in the local worktree and could not be located via repository search during this validation snapshot.'
  '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
)

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
  "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py"
  "control-plane/tests/test_phase21_production_like_hardening_boundary_validation.py"
  "scripts/verify-phase-21-production-like-hardening-boundary.sh"
  "scripts/test-verify-phase-21-production-like-hardening-boundary.sh"
  "scripts/test-verify-ci-phase-21-workflow-coverage.sh"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 21 artifact"
  require_fixed_line "${validation_doc}" "- \`${artifact}\`"
done

require_fixed_line "${validation_doc}" '- Verification commands: `python3 -m unittest control-plane.tests.test_phase21_production_like_hardening_boundary_docs control-plane.tests.test_phase21_production_like_hardening_boundary_validation`, `bash scripts/verify-phase-21-production-like-hardening-boundary.sh`, `bash scripts/test-verify-phase-21-production-like-hardening-boundary.sh`, `bash scripts/test-verify-ci-phase-21-workflow-coverage.sh`'
require_fixed_line "${docs_test}" 'class Phase21ProductionLikeHardeningBoundaryDocsTests(unittest.TestCase):'
require_fixed_line "${docs_test}" '    def test_phase21_design_doc_exists(self) -> None:'
require_fixed_line "${docs_test}" '    def test_phase21_design_doc_defines_boundary_sequence_and_non_expansion_rules(self) -> None:'
require_fixed_line "${validation_test}" 'class Phase21ProductionLikeHardeningBoundaryValidationTests(unittest.TestCase):'
require_fixed_line "${validation_test}" '    def test_phase21_validation_artifacts_cross_reference_governing_contracts(self) -> None:'
require_fixed_line "${workflow_path}" '      - name: Run Phase 21 production-like hardening boundary validation'
require_fixed_line "${workflow_path}" '          bash scripts/verify-phase-21-production-like-hardening-boundary.sh'
require_fixed_line "${workflow_path}" '          python3 -m unittest control-plane.tests.test_phase21_production_like_hardening_boundary_docs control-plane.tests.test_phase21_production_like_hardening_boundary_validation'
require_fixed_line "${workflow_path}" '      - name: Run Phase 21 workflow coverage guard'
require_fixed_line "${workflow_path}" '        run: bash scripts/test-verify-ci-phase-21-workflow-coverage.sh'
require_fixed_line "${workflow_path}" '          bash scripts/test-verify-phase-21-production-like-hardening-boundary.sh'

echo "Phase 21 production-like hardening design and validation artifacts are present and aligned."
