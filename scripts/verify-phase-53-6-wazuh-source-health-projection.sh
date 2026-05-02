#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/wazuh-source-health-projection-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 53.6 Wazuh Source-Health Projection Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Projection Inputs"
  "## 4. Projection States"
  "## 5. Projection Rules"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1135, #1138, #1141"
  "This contract defines the Wazuh source-health projection for the \`smb-single-node\` product profile."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/wazuh/source-health-projection.yaml\`."
  "Wazuh is a subordinate detection substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "Run \`bash scripts/verify-phase-53-6-wazuh-source-health-projection.sh\`."
  "Run \`bash scripts/test-verify-phase-53-6-wazuh-source-health-projection.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1141 --config <supervisor-config-path>\`."
)

required_artifact_terms=(
  "profile_id: smb-single-node"
  "product_profile: wazuh"
  "source_health_projection_contract_version: 2026-05-03"
  "status: accepted-contract"
  "projection_owner: aegisops-control-plane"
  "substrate_owner: wazuh"
  "authority_mutation_allowed: false"
  "raw_secret_values_allowed: false"
  "placeholder_credentials_valid: false"
  "workflow_truth_source: aegisops-record-chain-only"
  "components:"
  "states:"
  "projection_rules:"
  "negative_validation_tests:"
)

required_components=(
  manager
  dashboard
  indexer
  intake
  signal_freshness
  parser
  volume
  credential
)

required_states=(
  available
  degraded
  stale_source
  parser_failure
  volume_anomaly
  credential_degraded
  unavailable
  mismatched
)

required_rules=(
  all-required-components-available
  stale-last-accepted-signal
  parser-failure-visible
  volume-anomaly-visible
  credential-degraded-redacted
  manager-dashboard-indexer-unavailable-visible
  component-mismatch-visible
  no-authority-mutation
)

forbidden_claims=(
  "Wazuh health status is AegisOps workflow truth"
  "Wazuh source health closes AegisOps cases"
  "Wazuh manager health is AegisOps source truth"
  "Wazuh dashboard health is AegisOps workflow truth"
  "Wazuh indexer health is AegisOps evidence truth"
  "Credential-degraded state may expose secret material"
  "Placeholder Wazuh health credentials are valid credentials"
  "Source-health projection is AegisOps closeout truth"
  "Phase 53.6 implements Wazuh Active Response authority"
  "Phase 53.6 implements Shuffle product profiles"
  "Phase 53.6 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness"
)

rendered_markdown_without_code_blocks() {
  local markdown_path="$1"

  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    in_fenced_block { next }
    substr($0, 1, 1) == "\t" { next }
    substr($0, 1, 4) == "    " { next }
    { print }
  ' "${markdown_path}" | perl -0pe 's/<!--.*?-->//gs'
}

has_uncommented_substring() {
  local needle="$1"
  local file_path="$2"

  awk -v needle="${needle}" '
    /^[[:space:]]*#/ { next }
    {
      line = $0
      sub(/[[:space:]]+#.*/, "", line)
      if (index(line, needle)) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' "${file_path}"
}

require_top_level_list_item() {
  local file_path="$1"
  local section="$2"
  local item="$3"
  local label="$4"

  if ! awk -v section="${section}" -v item="${item}" '
    $0 == section ":" {
      in_section = 1
      next
    }
    in_section && /^[^[:space:]][^:]*:/ {
      in_section = 0
    }
    in_section && $0 ~ ("^  - " item "([[:space:]]*(#.*)?)?$") {
      found = 1
    }
    END { exit(found ? 0 : 1) }
  ' "${file_path}"; then
    echo "Missing Phase 53.6 Wazuh source-health ${label}: ${item}" >&2
    exit 1
  fi
}

contains_forbidden_claim_in_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${contract_path}"
}

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${contract_path}"
}

contains_secret_looking_value() {
  local file_path="$1"

  awk '
    /^[[:space:]]*#/ { next }
    {
      line = tolower($0)
      if (line ~ /(secret|token|password|credential|api_key|apikey)[[:space:]]*:[[:space:]]*["'\''"]?[[:alnum:]_\/+=.-]{16,}["'\''"]?/ &&
          line !~ /(allowed:[[:space:]]*false|valid:[[:space:]]*false|redacted|placeholder|<[^>]+>)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' "${file_path}"
}

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 53.6 Wazuh source-health projection contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 53.6 Wazuh source-health projection artifact: ${artifact_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.6 Wazuh source-health projection contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.6 Wazuh source-health projection contract statement: ${phrase}" >&2
    exit 1
  fi
done

for term in "${required_artifact_terms[@]}"; do
  if ! has_uncommented_substring "${term}" "${artifact_path}"; then
    echo "Missing Phase 53.6 Wazuh source-health projection artifact term: ${term}" >&2
    exit 1
  fi
done

for component in "${required_components[@]}"; do
  require_top_level_list_item "${artifact_path}" "components" "${component}" "component"
  if ! grep -Fq -- "| ${component} |" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.6 Wazuh source-health projection contract component row: ${component}" >&2
    exit 1
  fi
done

for state in "${required_states[@]}"; do
  require_top_level_list_item "${artifact_path}" "states" "${state}" "state"
  if ! grep -Fq -- "| ${state} |" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.6 Wazuh source-health projection contract state row: ${state}" >&2
    exit 1
  fi
done

for rule in "${required_rules[@]}"; do
  require_top_level_list_item "${artifact_path}" "projection_rules" "${rule}" "rule"
  if ! grep -Fq -- "| ${rule} |" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.6 Wazuh source-health projection contract rule row: ${rule}" >&2
    exit 1
  fi
done

for claim in "${forbidden_claims[@]}"; do
  if ! contains_forbidden_claim_in_section "${claim}"; then
    echo "Missing Phase 53.6 Wazuh source-health forbidden claim: ${claim}" >&2
    exit 1
  fi

  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 53.6 Wazuh source-health projection claim: ${claim}" >&2
    exit 1
  fi
done

for secret_scan_path in "${contract_path}" "${artifact_path}"; do
  if contains_secret_looking_value "${secret_scan_path}"; then
    echo "Forbidden Phase 53.6 Wazuh source-health artifact: committed secret-looking value detected in ${secret_scan_path}" >&2
    exit 1
  fi
done

mac_user_home_pattern="/""Users/"
posix_user_home_pattern="/""home/[^[:space:]/]+"
windows_user_home_pattern='C:\\''Users\\'
if grep -REq "${mac_user_home_pattern}|${posix_user_home_pattern}|${windows_user_home_pattern}" "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 53.6 Wazuh source-health projection artifact: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 53.6 Wazuh source-health projection link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}"
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/wazuh-source-health-projection-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 53.6 Wazuh source-health projection contract." >&2
  exit 1
fi

echo "Phase 53.6 Wazuh source-health projection contract is present and rejects missing states, authority promotion, secret leakage, and workstation-local paths."
