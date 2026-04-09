#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
scope_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
validation_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-validation.md"
runtime_boundary_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"
architecture_doc="${repo_root}/docs/architecture.md"
network_doc="${repo_root}/docs/network-exposure-and-access-path-policy.md"
storage_doc="${repo_root}/docs/storage-layout-and-mount-policy.md"
readme_doc="${repo_root}/README.md"

require_file() {
  local path="$1"
  local message="$2"

  if [[ ! -f "${path}" ]]; then
    echo "${message}: ${path}" >&2
    exit 1
  fi
}

require_fixed_string() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fqx -- "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required line in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_file "${scope_doc}" "Missing Phase 16 release-state scope document"
require_file "${validation_doc}" "Missing Phase 16 validation record"
require_file "${runtime_boundary_doc}" "Missing control-plane runtime boundary doc"
require_file "${architecture_doc}" "Missing architecture overview doc"
require_file "${network_doc}" "Missing network exposure policy doc"
require_file "${storage_doc}" "Missing storage layout policy doc"
require_file "${readme_doc}" "Missing repository README"

scope_required_lines=(
  '# AegisOps Phase 16 Release-State and First-Boot Scope'
  '## 1. Purpose'
  '## 2. Approved Phase 16 Release-State'
  '## 3. First-Boot In-Scope Runtime Components'
  '## 4. First-Boot Explicitly Out of Scope'
  '## 5. Phase 16 Definition of Done'
  '## 6. Boundary and Alignment Notes'
  'This document defines the approved Phase 16 release-state and first-boot scope for bootable AegisOps.'
  'This document defines release-state and review scope only. It does not approve concrete containerization, live Wazuh integration wiring, analyst UI implementation, or broad runtime expansion beyond the first-boot boundary described here.'
  'The approved Phase 16 release-state is a repository baseline that is ready to enter Phase 17 runtime bring-up with one narrow bootability target.'
  '- the AegisOps control-plane service as the authoritative runtime boundary;'
  '- PostgreSQL as the AegisOps-owned persistence dependency for control-plane state;'
  '- the approved reverse proxy access boundary for controlled ingress; and'
  '- reviewed Wazuh-facing runtime expectations for upstream analytic-signal intake.'
  'Phase 16 release-state means those components are the required bootability floor.'
  'It does not mean every adjacent substrate tracked in the repository must boot on day one, and it does not redefine optional repository assets as mandatory first-boot dependencies.'
  'The first bootable AegisOps runtime includes the following in-scope components:'
  '- a live AegisOps control-plane service rooted under `control-plane/`;'
  '- the reviewed PostgreSQL boundary for AegisOps-owned control-plane records;'
  '- the approved reverse proxy path for controlled user-facing ingress and administrative exposure control; and'
  '- reviewed runtime expectations that the control-plane service can accept Wazuh-originated analytic-signal inputs without requiring Wazuh to become the authority for downstream alert, case, approval, or reconciliation truth.'
  'The first-boot scope is intentionally narrow.'
  'The following items are explicitly out of scope for the Phase 16 first-boot release-state:'
  '- optional OpenSearch extension runtime or OpenSearch-dependent first-boot success criteria;'
  '- n8n as a required first-boot dependency or orchestration prerequisite;'
  '- the full interactive analyst-assistant surface;'
  '- the high-risk executor path or write-capable response execution; and'
  '- broad source coverage beyond the narrow Wazuh-facing runtime expectation required for first boot.'
  'Phase 16 is done when the repository baseline unambiguously states that:'
  '- first boot requires the AegisOps control-plane service, PostgreSQL, and the approved reverse proxy boundary;'
  '- Wazuh-facing runtime expectations are limited to reviewed upstream analytic-signal intake expectations rather than live end-to-end substrate wiring;'
  '- OpenSearch, n8n, the full analyst-assistant surface, the high-risk executor, and broad source expansion remain optional, deferred, or non-blocking for first boot; and'
  '- later phases can use this document as the bootability target for Phase 17 runtime bring-up without reopening what counts as the minimum first-boot runtime.'
)

for line in "${scope_required_lines[@]}"; do
  require_fixed_string "${scope_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 16 Release-State and First-Boot Scope Validation'
  '- Validation date: 2026-04-09'
  '- Validation scope: Phase 16 review of the approved first-boot runtime boundary, required first-boot components, explicit non-blocking optional components, Wazuh-facing runtime expectations, and the definition of done that gates Phase 17 runtime bring-up'
  "- Baseline references: \`docs/phase-16-release-state-and-first-boot-scope.md\`, \`docs/control-plane-runtime-service-boundary.md\`, \`docs/architecture.md\`, \`docs/network-exposure-and-access-path-policy.md\`, \`docs/storage-layout-and-mount-policy.md\`, \`README.md\`"
  "- Verification commands: \`bash scripts/verify-phase-16-release-state-and-first-boot-scope.sh\`, \`bash scripts/test-verify-phase-16-release-state-and-first-boot-scope.sh\`"
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed Phase 16 now defines one approved bootability target for the first live AegisOps runtime instead of treating every tracked substrate as a first-boot dependency.'
  'Confirmed the required first-boot runtime is limited to the AegisOps control-plane service, PostgreSQL, the approved reverse proxy boundary, and reviewed Wazuh-facing analytic-signal intake expectations.'
  'Confirmed OpenSearch remains an optional extension rather than a mandatory first-boot dependency.'
  'Confirmed n8n remains optional or deferred and does not block the first bootable runtime target.'
  'Confirmed the full interactive analyst-assistant surface, the high-risk executor path, and broad source coverage remain outside the first-boot definition.'
  'Confirmed the Phase 16 definition of done gives Phase 17 a clear bootability target without approving concrete containerization or live substrate wiring in this phase.'
  "The issue requested review against \`Phase 16-21 Epic Roadmap.md\`, but that roadmap file was not present in the local worktree and could not be located via repository search during this turn."
  "- Requested comparison target \`Phase 16-21 Epic Roadmap.md\` was unavailable in the local worktree during this validation snapshot."
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_string "${validation_doc}" "${line}"
done

required_artifacts=(
  "docs/phase-16-release-state-and-first-boot-scope.md"
  "docs/phase-16-release-state-and-first-boot-validation.md"
  "docs/control-plane-runtime-service-boundary.md"
  "docs/architecture.md"
  "docs/network-exposure-and-access-path-policy.md"
  "docs/storage-layout-and-mount-policy.md"
  "README.md"
  "scripts/verify-phase-16-release-state-and-first-boot-scope.sh"
  "scripts/test-verify-phase-16-release-state-and-first-boot-scope.sh"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 16 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 16 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Phase 16 release-state and first-boot scope remain explicit and reviewable."
