#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
default_repo_root="$(cd "${script_dir}/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
design_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
validation_doc="${repo_root}/docs/phase-18-wazuh-lab-topology-validation.md"
asset_doc="${repo_root}/docs/phase-18-wazuh-single-node-lab-assets.md"
phase17_doc="${repo_root}/docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
phase16_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
wazuh_contract_doc="${repo_root}/docs/wazuh-alert-ingest-contract.md"
source_contract_doc="${repo_root}/docs/source-onboarding-contract.md"
github_audit_doc="${repo_root}/docs/source-families/github-audit/onboarding-package.md"
architecture_doc="${repo_root}/docs/architecture.md"
asset_dir="${repo_root}/ingest/wazuh/single-node-lab"
asset_readme="${asset_dir}/README.md"
asset_bootstrap="${asset_dir}/bootstrap.env.sample"
asset_compose="${asset_dir}/docker-compose.yml"
asset_integration="${asset_dir}/ossec.integration.sample.xml"

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
require_file "${asset_doc}" "Missing Phase 18 Wazuh lab asset doc"
require_file "${phase17_doc}" "Missing Phase 17 runtime config contract doc"
require_file "${phase16_doc}" "Missing Phase 16 first-boot scope doc"
require_file "${wazuh_contract_doc}" "Missing Wazuh alert ingest contract doc"
require_file "${source_contract_doc}" "Missing source onboarding contract doc"
require_file "${github_audit_doc}" "Missing GitHub audit onboarding package doc"
require_file "${architecture_doc}" "Missing architecture overview doc"
require_file "${asset_readme}" "Missing Phase 18 Wazuh lab README"
require_file "${asset_bootstrap}" "Missing Phase 18 Wazuh lab bootstrap sample"
require_file "${asset_compose}" "Missing Phase 18 Wazuh lab compose asset"
require_file "${asset_integration}" "Missing Phase 18 Wazuh lab integration sample"

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
  'The reviewed repository-local asset bundle for this topology lives under `ingest/wazuh/single-node-lab/` and remains placeholder-safe lab scaffolding rather than production deployment truth.'
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
  '`docs/phase-18-wazuh-single-node-lab-assets.md` and `ingest/wazuh/single-node-lab/` remain the normative reviewed asset references for the first live lab substrate target.'
)

for line in "${design_required_lines[@]}"; do
  require_fixed_string "${design_doc}" "${line}"
done

asset_doc_required_lines=(
  '# Phase 18 Wazuh Single-Node Lab Assets'
  '## 1. Purpose'
  '## 2. Asset Bundle'
  '## 3. Reviewed Bootstrap Inputs'
  '## 4. Operator Expectations'
  '## 5. Deferred Scope'
  '## 6. Reviewable Usage Boundary'
  'The reviewed asset bundle for the single-node Wazuh lab target lives under `ingest/wazuh/single-node-lab/`.'
  '- `docker-compose.yml` for the placeholder-safe single-node Wazuh manager, indexer, and dashboard lab stack with internal-only service exposure and no direct host port publication;'
  '- `bootstrap.env.sample` for reviewed non-secret bootstrap inputs;'
  '- `ossec.integration.sample.xml` for the reviewed custom integration shape that preserves `Wazuh -> AegisOps` as the only approved first live routing path;'
  'The reviewed custom integration shape uses `Authorization: Bearer <shared secret>` at runtime.'
  'The shared secret must remain untracked and must come from an operator-provided runtime secret file or another reviewed untracked secret source.'
  'Operators must keep GitHub audit as the only approved first live source family for this slice.'
  'Operators must keep the Wazuh manager, indexer, and dashboard interfaces internal to the lab compose network or another separately reviewed lab access path rather than publishing host ports from this bundle.'
  '- multi-node or production-scale Wazuh;'
  '- the optional OpenSearch runtime extension;'
)

for line in "${asset_doc_required_lines[@]}"; do
  require_fixed_string "${asset_doc}" "${line}"
done

validation_required_lines=(
  '# Phase 18 Wazuh Lab Topology and Live Ingest Contract Validation'
  '- Validation date: 2026-04-10'
  '- Validation status: PASS'
  '## Required Boundary Artifacts'
  '## Review Outcome'
  '## Cross-Link Review'
  '## Deviations'
  'Confirmed the reviewed repository-local asset bundle under `ingest/wazuh/single-node-lab/` makes the first live substrate target explicit with placeholder-safe compose, bootstrap, and integration artifacts while keeping secrets untracked and production hardening out of scope.'
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
  "docs/phase-18-wazuh-single-node-lab-assets.md"
  "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  "docs/phase-16-release-state-and-first-boot-scope.md"
  "docs/wazuh-alert-ingest-contract.md"
  "docs/source-onboarding-contract.md"
  "docs/source-families/github-audit/onboarding-package.md"
  "docs/architecture.md"
  "ingest/wazuh/single-node-lab/README.md"
  "ingest/wazuh/single-node-lab/bootstrap.env.sample"
  "ingest/wazuh/single-node-lab/docker-compose.yml"
  "ingest/wazuh/single-node-lab/ossec.integration.sample.xml"
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

asset_compose_required_lines=(
  'name: aegisops-wazuh-single-node-lab'
  '  wazuh-manager:'
  '  wazuh-indexer:'
  '  wazuh-dashboard:'
  '    expose:'
  '      - "1514/udp"'
  '      - "1515"'
  '      - "55000"'
  '      - "5601"'
  '      AEGISOPS_WAZUH_AEGISOPS_INGEST_URL: ${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL:?set-in-untracked-runtime-env}'
  '      AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE: ${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE:?set-in-untracked-runtime-env}'
  '    # GitHub audit remains the only approved first live source family.'
  '    # manager interfaces stay internal to the lab compose network until a reviewed lab access path exists'
  '    # dashboard access must stay on an internal-only or separately reviewed lab access path'
  '    # do not add Shuffle, n8n, or a direct control-plane backend publication path here'
)

for line in "${asset_compose_required_lines[@]}"; do
  require_fixed_string "${asset_compose}" "${line}"
done

if grep -En '^[[:space:]]*ports:[[:space:]]*(#.*)?$' "${asset_compose}" >/dev/null; then
  echo "Phase 18 Wazuh lab compose asset must not publish host ports directly." >&2
  exit 1
fi

asset_bootstrap_required_lines=(
  'AEGISOPS_WAZUH_HOSTNAME=wazuh-lab-manager-01'
  'AEGISOPS_WAZUH_INDEXER_HOSTNAME=wazuh-lab-indexer-01'
  'AEGISOPS_WAZUH_DASHBOARD_HOSTNAME=wazuh-lab-dashboard-01'
  'AEGISOPS_WAZUH_AEGISOPS_INGEST_URL=https://aegisops-lab.example.internal/intake/wazuh'
  'AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE=./secrets/aegisops-wazuh-shared-secret.txt'
  'AEGISOPS_WAZUH_GITHUB_AUDIT_ENROLLMENT_STATUS=reviewed-first-live-family-only'
  '# Do not commit live secrets.'
)

for line in "${asset_bootstrap_required_lines[@]}"; do
  require_fixed_string "${asset_bootstrap}" "${line}"
done

asset_integration_required_lines=(
  '  <name>aegisops-github-audit</name>'
  '  <hook_url>${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}</hook_url>'
  '  <api_key>${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET}</api_key>'
  '  <alert_format>json</alert_format>'
)

for line in "${asset_integration_required_lines[@]}"; do
  require_fixed_string "${asset_integration}" "${line}"
done

echo "Phase 18 Wazuh lab topology and live ingest contract remain explicit and reviewable."
