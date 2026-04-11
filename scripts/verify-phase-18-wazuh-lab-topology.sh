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
phase18_live_queue_test="${repo_root}/control-plane/tests/test_phase18_live_wazuh_queue_validation.py"
asset_dir="${repo_root}/ingest/wazuh/single-node-lab"
asset_readme="${asset_dir}/README.md"
asset_bootstrap="${asset_dir}/bootstrap.env.sample"
asset_compose="${asset_dir}/docker-compose.yml"
asset_integration="${asset_dir}/ossec.integration.sample.xml"
asset_render_helper="${asset_dir}/render-ossec-integration.sh"

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
require_file "${phase18_live_queue_test}" "Missing Phase 18 live Wazuh queue validation test"
require_file "${asset_readme}" "Missing Phase 18 Wazuh lab README"
require_file "${asset_bootstrap}" "Missing Phase 18 Wazuh lab bootstrap sample"
require_file "${asset_compose}" "Missing Phase 18 Wazuh lab compose asset"
require_file "${asset_integration}" "Missing Phase 18 Wazuh lab integration sample"
require_file "${asset_render_helper}" "Missing Phase 18 Wazuh lab integration render helper"

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
  'The reviewed reverse proxy must also inject a separate AegisOps-owned boundary credential header before forwarding the request to the control-plane backend.'
  'Direct backend requests that do not cross the reviewed reverse proxy boundary must not be able to mint that backend-only credential.'
  'The payload shape remains the reviewed Wazuh alert contract from `docs/wazuh-alert-ingest-contract.md`.'
  'The live ingest path must fail closed.'
  '- the request is not HTTPS at the approved ingress boundary;'
  '- the request does not use HTTPS POST;'
  '- the `Authorization: Bearer` header is missing, empty, malformed, or does not match the reviewed shared secret;'
  '- the reviewed reverse proxy boundary credential is missing, empty, malformed, or does not match the backend runtime secret injected by the reverse proxy;'
  '- the request attempts to bypass the approved reverse proxy and reach the control-plane backend directly;'
  '- the payload is not valid JSON;'
  '- the payload does not satisfy the reviewed Wazuh required fields including `id`, `timestamp`, `rule.id`, `rule.level`, `rule.description`, accountable source identity, and raw payload preservation expectations; or'
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
  '- `render-ossec-integration.sh` for rendering the reviewed sample into literal Wazuh integration values before operator use with an explicit output path requirement; and'
  'The reviewed custom integration shape uses `Authorization: Bearer <shared secret>` at runtime.'
  'The shared secret must remain untracked and must come from an operator-provided runtime secret file or another reviewed untracked secret source.'
  'Wazuh does not expand the sample `${...}` placeholders inside the integration block. Operators must render literal `<hook_url>` and `<api_key>` values with `render-ossec-integration.sh` before loading the reviewed integration into active Wazuh configuration.'
  'The reviewed render helper must not default to a tracked repository output path. Operators must provide the destination path explicitly so the render step stays intentional when live bearer material is present.'
  'The reviewed safe output example is `${TMPDIR:-/tmp}/aegisops-wazuh/ossec.integration.rendered.xml`.'
  'If an operator intentionally writes a rendered integration file inside a local worktree for short-lived review, the file path must stay under repository ignore coverage for rendered `ossec.integration.rendered.xml` artifacts and must not be staged.'
  'Operators must keep GitHub audit as the only approved first live source family for this slice.'
  'Operators must keep the Wazuh manager, indexer, and dashboard interfaces internal to the lab compose network or another separately reviewed lab access path rather than publishing host ports from this bundle.'
  'Operators must run `render-ossec-integration.sh` in the manager container or another shell where `AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE` resolves to the mounted secret path before copying the reviewed integration block into active Wazuh configuration.'
  'Operators must pass an explicit output path to `render-ossec-integration.sh` rather than relying on an implicit current-directory default.'
  'Operators should prefer `${TMPDIR:-/tmp}/aegisops-wazuh/ossec.integration.rendered.xml` or another reviewed untracked location outside the repository when rendering the live integration block.'
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
  'Confirmed the reviewed lab bundle documents a render step for turning the sample integration into literal Wazuh values instead of implying unsupported environment-variable expansion inside the live Wazuh configuration.'
  'Confirmed the approved topology is limited to one single-node Wazuh lab target feeding one bootable AegisOps control-plane runtime boundary through the reviewed reverse proxy and into PostgreSQL-backed control-plane state.'
  'Confirmed the Phase 18 live path keeps Wazuh -> AegisOps as the mainline live path and does not broaden the first live slice into `Wazuh -> Shuffle`, n8n relay routing, or OpenSearch-first runtime dependence.'
  'Confirmed GitHub audit is the approved first live source family because it preserves the narrowest identity-rich source context already prioritized by the reviewed Phase 14 family order and GitHub audit onboarding package.'
  'Confirmed the reviewed Wazuh custom integration contract requires HTTPS POST to the approved reverse-proxy ingress boundary plus `Authorization: Bearer <shared secret>` authentication sourced from an untracked runtime secret, and a separate reverse-proxy boundary credential injected only on the backend hop.'
  'Confirmed the Phase 18 contract applies the existing Wazuh payload-admission rules rather than redefining them, and limits first live admission to GitHub audit carried inside the reviewed Wazuh alert envelope.'
  'Confirmed the repository-local Phase 18 live-ingest validator now exercises authenticated `ingest_wazuh_alert` runtime admission, repeat live GitHub audit delivery, and analyst-queue appearance so restatement, dedupe, and case-linkage drift fail closed before later operator-surface phases build on the slice.'
  'Confirmed the live ingest path remains fail-closed by rejecting non-HTTPS requests, non-POST requests, missing or invalid bearer credentials, missing or invalid reverse-proxy boundary credentials, direct backend bypass attempts, invalid JSON payloads, Wazuh payloads that violate required field expectations, and payloads outside the approved first live family.'
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
  "control-plane/tests/test_phase18_live_wazuh_queue_validation.py"
  "ingest/wazuh/single-node-lab/README.md"
  "ingest/wazuh/single-node-lab/bootstrap.env.sample"
  "ingest/wazuh/single-node-lab/docker-compose.yml"
  "ingest/wazuh/single-node-lab/ossec.integration.sample.xml"
  "ingest/wazuh/single-node-lab/render-ossec-integration.sh"
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

require_fixed_string "${validation_doc}" '- Verification commands: `python3 -m unittest control-plane.tests.test_phase18_wazuh_lab_topology_docs`, `python3 -m unittest control-plane.tests.test_phase18_wazuh_single_node_lab_assets`, `python3 -m unittest control-plane.tests.test_phase18_live_wazuh_queue_validation`, `bash scripts/verify-phase-18-wazuh-lab-topology.sh`, `bash scripts/test-verify-phase-18-wazuh-lab-topology.sh`'
require_fixed_string "${phase18_live_queue_test}" 'class Phase18LiveWazuhQueueValidationTests(unittest.TestCase):'
require_fixed_string "${phase18_live_queue_test}" '    def test_live_github_audit_ingest_restates_and_deduplicates_into_case_linked_queue_record('
require_fixed_string "${phase18_live_queue_test}" '        self.assertEqual(created.disposition, "created")'
require_fixed_string "${phase18_live_queue_test}" '        self.assertEqual(restated.disposition, "restated")'
require_fixed_string "${phase18_live_queue_test}" '        self.assertEqual(deduplicated.disposition, "deduplicated")'
require_fixed_string "${phase18_live_queue_test}" '        self.assertEqual(queue_view.records[0]["queue_selection"], "business_hours_triage")'
require_fixed_string "${phase18_live_queue_test}" '            "github_audit",'

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
  '      - ./render-ossec-integration.sh:/wazuh-config-placeholder/render-ossec-integration.sh:ro'
  '    # GitHub audit remains the only approved first live source family.'
  '    # render-ossec-integration.sh consumes the mounted secret file before operators copy literal values into active Wazuh config'
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
  'AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE=/run/aegisops-secrets/aegisops-wazuh-shared-secret.txt'
  'AEGISOPS_WAZUH_GITHUB_AUDIT_ENROLLMENT_STATUS=reviewed-first-live-family-only'
  '# Do not commit live secrets.'
)

for line in "${asset_bootstrap_required_lines[@]}"; do
  require_fixed_string "${asset_bootstrap}" "${line}"
done

asset_integration_required_lines=(
  '<!-- Render this sample with render-ossec-integration.sh before use. -->'
  '<!-- render-ossec-integration.sh reads AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE and fills AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET into this reviewed template before operator use. -->'
  '  <name>aegisops-github-audit</name>'
  '  <hook_url>${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}</hook_url>'
  '  <api_key>${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET}</api_key>'
  '  <alert_format>json</alert_format>'
  '  <group>github_audit</group>'
)

for line in "${asset_integration_required_lines[@]}"; do
  require_fixed_string "${asset_integration}" "${line}"
done

render_helper_required_lines=(
  'safe_output_example="${TMPDIR:-/tmp}/aegisops-wazuh/ossec.integration.rendered.xml"'
  'require_explicit_output_path() {'
  '    echo "Explicit output path required. Refusing to write rendered integration content to an implicit worktree path." >&2'
  '    echo "Suggested safe location: ${safe_output_example}" >&2'
  'require_explicit_output_path "$@"'
  'require_env "AEGISOPS_WAZUH_AEGISOPS_INGEST_URL"'
  'require_env "AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET_FILE"'
  'template_path="${script_dir}/ossec.integration.sample.xml"'
  'AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET="${shared_secret}"'
  'escaped_ingest_url="$(xml_escape "${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}")"'
  'escaped_shared_secret="$(xml_escape "${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET}")"'
  '  -e "s|\${AEGISOPS_WAZUH_AEGISOPS_INGEST_URL}|$(escape_sed_replacement "${escaped_ingest_url}")|g" \'
  '  -e "s|\${AEGISOPS_WAZUH_AEGISOPS_SHARED_SECRET}|$(escape_sed_replacement "${escaped_shared_secret}")|g" \'
)

for line in "${render_helper_required_lines[@]}"; do
  require_fixed_string "${asset_render_helper}" "${line}"
done

echo "Phase 18 Wazuh lab topology and live ingest contract remain explicit and reviewable."
