#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
design_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
validation_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-validation.md"
phase17_doc="${repo_root}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
phase16_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
wazuh_contract_doc="${repo_root}/docs/wazuh-alert-ingest-contract.md"
source_contract_doc="${repo_root}/docs/source-onboarding-contract.md"
github_audit_doc="${repo_root}/docs/source-families/github-audit/onboarding-package.md"
architecture_doc="${repo_root}/docs/architecture.md"

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

require_file "${design_doc}" "Missing Phase 18 Wazuh lab topology doc"
require_file "${validation_doc}" "Missing Phase 18 Wazuh lab topology validation doc"
require_file "${phase17_doc}" "Missing Phase 17 runtime config contract doc"
require_file "${phase16_doc}" "Missing Phase 16 first-boot scope doc"
require_file "${wazuh_contract_doc}" "Missing Wazuh alert ingest contract doc"
require_file "${source_contract_doc}" "Missing source onboarding contract doc"
require_file "${github_audit_doc}" "Missing GitHub audit onboarding package doc"
require_file "${architecture_doc}" "Missing architecture overview doc"

design_required_lines=(
  '# AegisOps Phase 18 Wazuh Lab Topology and Live Ingest Contract'
  '## 1. Purpose'
  '## 2. Approved Phase 18 Lab Topology'
  '## 3. Approved First Live Source Family'
  '## 4. Reviewed Wazuh Custom Integration Live Ingest Contract'
  '### 4.1 Transport and Path'
  '### 4.2 Authentication'
  '### 4.3 Payload Admission Boundary'
  '### 4.4 Fail-Closed Expectations'
  '## 5. Deferred Runtime Surfaces and Non-Goals'
  '## 6. Alignment and Non-Expansion Rules'
  'The approved Phase 18 lab topology is one single-node Wazuh lab target connected to one bootable AegisOps control-plane runtime boundary.'
  '`single-node Wazuh -> reviewed reverse proxy -> bootable AegisOps control-plane runtime boundary -> PostgreSQL`'
  'The control-plane backend port remains internal-only behind the reverse proxy.'
  'The Approved First Live Source Family for the initial Phase 18 slice is GitHub audit.'
  'The reviewed Wazuh custom integration must send one Wazuh alert JSON object at a time to AegisOps using HTTPS POST.'
  'The approved live path is Wazuh -> AegisOps.'
  'Phase 18 must not make `Wazuh -> Shuffle` part of the first live slice.'
  'The reviewed request authentication contract is `Authorization: Bearer <shared secret>`.'
  'The shared secret is an AegisOps-owned runtime secret and must come from an untracked secret source or reviewed operator-provided runtime secret file.'
  'The payload shape remains the reviewed Wazuh alert contract from `docs/wazuh-alert-ingest-contract.md`.'
  'The live ingest path must fail closed.'
  '- the request is not HTTPS at the approved ingress boundary;'
  '- the request does not use HTTPS POST;'
  '- the `Authorization: Bearer` header is missing, empty, malformed, or does not match the reviewed shared secret;'
  '- the request attempts to bypass the approved reverse proxy and reach the control-plane backend directly;'
  '- the payload is not valid JSON;'
  '- the payload represents a family other than the approved GitHub audit first live source family.'
  'The live ingest path must not silently downgrade to HTTP, accept missing authentication, bypass the reviewed Wazuh contract, or treat `Wazuh -> Shuffle` as a fallback route.'
  '- OpenSearch runtime enrichment or OpenSearch-dependent success criteria;'
  '- thin operator UI work;'
  '- guarded automation live wiring;'
)

for line in "${design_required_lines[@]}"; do
  require_fixed_string "${design_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 18 Wazuh Lab Topology and Live Ingest Contract Validation'
  '- Validation date: 2026-04-10'
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the approved topology is limited to one single-node Wazuh lab target feeding one bootable AegisOps control-plane runtime boundary through the reviewed reverse proxy and into PostgreSQL-backed control-plane state.'
  'Confirmed the Phase 18 live path keeps Wazuh -> AegisOps as the mainline live path and does not broaden the first live slice into `Wazuh -> Shuffle`, n8n relay routing, or OpenSearch-first runtime dependence.'
  'Confirmed GitHub audit is the approved first live source family because it preserves the narrowest identity-rich source context already prioritized by the reviewed Phase 14 family order and GitHub audit onboarding package.'
  'Confirmed the reviewed Wazuh custom integration contract requires HTTPS POST to the approved reverse-proxy ingress boundary plus `Authorization: Bearer <shared secret>` authentication sourced from an untracked runtime secret.'
  'Confirmed the Phase 18 contract applies the existing Wazuh payload-admission rules rather than redefining them, and limits first live admission to GitHub audit carried inside the reviewed Wazuh alert envelope.'
  'Confirmed the live ingest path remains fail-closed by rejecting non-HTTPS requests, non-POST requests, missing or invalid bearer credentials, direct backend bypass attempts, invalid JSON payloads, Wazuh payloads that violate required field expectations, and payloads outside the approved first live family.'
  'Confirmed OpenSearch runtime enrichment, thin operator UI, guarded automation live wiring, broader source-family rollout, direct GitHub API actioning, and production-scale Wazuh topologies remain deferred and out of scope for this slice.'
  "The issue requested review against \`Phase 16-21 Epic Roadmap.md\`, but that roadmap file was not present in the local worktree and could not be located via repository search during this turn."
  '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
)

for line in "${validation_required_lines[@]}"; do
  require_fixed_string "${validation_doc}" "${line}"
done

required_artifacts=(
  "docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
  "docs/phase-18-wazuh-lab-topology-validation.md"
  "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  "docs/phase-16-release-state-and-first-boot-scope.md"
  "docs/wazuh-alert-ingest-contract.md"
  "docs/source-onboarding-contract.md"
  "docs/source-families/github-audit/onboarding-package.md"
  "docs/architecture.md"
  "scripts/verify-phase-18-wazuh-lab-topology.sh"
  "scripts/test-verify-phase-18-wazuh-lab-topology.sh"
)

for artifact in "${required_artifacts[@]}"; do
  require_file "${repo_root}/${artifact}" "Missing required Phase 18 artifact"

  if ! grep -Fqx -- "- \`${artifact}\`" "${validation_doc}" >/dev/null; then
    echo "Phase 18 validation record must list required artifact: ${artifact}" >&2
    exit 1
  fi
done

echo "Phase 18 Wazuh lab topology and live ingest contract remain explicit and reviewable."
