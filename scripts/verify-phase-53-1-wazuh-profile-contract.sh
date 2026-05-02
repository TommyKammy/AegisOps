#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/wazuh-smb-single-node-profile-contract.md"
profile_path="${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/profile.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 53.1 Wazuh SMB Single-Node Profile Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Component Contract"
  "## 4. Version Matrix"
  "## 5. Profile Expectations"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1135, #1136"
  "This contract defines the repo-owned Wazuh \`smb-single-node\` product-profile contract and version matrix."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/wazuh/profile.yaml\`."
  "Wazuh is a subordinate detection substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "| Component | Required | Version pin | Image pin | Resource expectation | Ports | Volumes | Certificate expectations | Authority boundary |"
  "| Component | Accepted version | Pin type | Known incompatible versions | Upgrade note |"
  "Run \`bash scripts/verify-phase-53-1-wazuh-profile-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-53-1-wazuh-profile-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1136 --config <supervisor-config-path>\`."
)

components=(manager indexer dashboard)
required_profile_terms=(
  "profile_id: smb-single-node"
  "product_profile: wazuh"
  "profile_contract_version: 2026-05-03"
  "authority_boundary: Wazuh provides subordinate detection substrate signals only;"
  "resource_floor:"
  "ingress:"
  "volumes:"
  "certificates:"
  "source_health:"
)

forbidden_claims=(
  "Wazuh status is AegisOps workflow truth"
  "Wazuh alert status is AegisOps case truth"
  "Wazuh manager state is AegisOps source truth"
  "Wazuh dashboard state is AegisOps approval truth"
  "Wazuh indexer state is AegisOps evidence truth"
  "Wazuh version state is AegisOps release truth"
  "Source-health projection is AegisOps closeout truth"
  "Raw forwarded headers are trusted identity"
  "Phase 53.1 implements Wazuh intake binding"
  "Phase 53.1 implements Wazuh certificate generation"
  "Phase 53.1 implements Wazuh source-health projection"
  "Phase 53.1 implements Wazuh upgrade automation"
  "Phase 53.1 implements Shuffle product profiles"
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

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 53.1 Wazuh profile contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${profile_path}" ]]; then
  echo "Missing Phase 53.1 Wazuh profile artifact: ${profile_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.1 Wazuh profile contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.1 Wazuh profile contract statement: ${phrase}" >&2
    exit 1
  fi
done

for term in "${required_profile_terms[@]}"; do
  if ! grep -Fq -- "${term}" "${profile_path}"; then
    echo "Missing Phase 53.1 Wazuh profile artifact term: ${term}" >&2
    exit 1
  fi
done

if grep -Eq '(^|[^[:alnum:]_.-])(latest|stable|current|main|master|HEAD|rc|beta)([^[:alnum:]_.-]|$)' <(grep -E '^[[:space:]]*(version|image):' "${profile_path}"); then
  echo "Forbidden Phase 53.1 Wazuh profile artifact: unpinned version or image reference detected" >&2
  exit 1
fi

for component in "${components[@]}"; do
  if ! grep -Eq "^\| ${component} \| Yes \| \`4\.12\.0\` \| \`wazuh/wazuh-${component}:4\.12\.0\` \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${contract_rendered_markdown}"; then
    echo "Missing complete Phase 53.1 Wazuh component row: ${component}" >&2
    exit 1
  fi

  if ! grep -Eq "^\| ${component} \| \`4\.12\.0\` \| exact \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${contract_rendered_markdown}"; then
    echo "Missing complete Phase 53.1 Wazuh version matrix row: ${component}" >&2
    exit 1
  fi

  expected_image="wazuh/wazuh-${component}:4.12.0"
  if ! awk -v component="${component}" -v expected_image="${expected_image}" '
    function trim(value) {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      return value
    }
    function list_has_items() {
      if (active_list == "ports" && list_items > 0) {
        ports = 1
      } else if (active_list == "volumes" && list_items > 0) {
        volumes = 1
      } else if (active_list == "certificates" && list_items > 0) {
        certificates = 1
      }
      active_list = ""
      list_items = 0
    }
    function value_after_key(line, key) {
      sub("^    " key ":[[:space:]]*", "", line)
      return trim(line)
    }
    $0 == "  " component ":" {
      in_component = 1
      required = version = image = ports = volumes = certificates = resources = boundary = 0
      active_list = ""
      list_items = 0
      next
    }
    in_component && (/^version_matrix:/ || /^  [a-z][a-z0-9_-]*:[[:space:]]*$/) {
      list_has_items()
      in_component = 0
      next
    }
    in_component && /^    [a-z_]+:/ { list_has_items() }
    in_component && $0 == "    required: true" { required = 1 }
    in_component && $0 == "    version: 4.12.0" { version = 1 }
    in_component && $0 == "    image: " expected_image { image = 1 }
    in_component && $0 == "    ports:" {
      active_list = "ports"
      list_items = 0
      next
    }
    in_component && $0 == "    volumes:" {
      active_list = "volumes"
      list_items = 0
      next
    }
    in_component && $0 == "    certificates:" {
      active_list = "certificates"
      list_items = 0
      next
    }
    in_component && active_list != "" && /^      - [^[:space:]]/ { list_items++ }
    in_component && /^    resource_expectation:/ && value_after_key($0, "resource_expectation") != "" { resources = 1 }
    in_component && /^    boundary:/ && value_after_key($0, "boundary") != "" { boundary = 1 }
    END {
      list_has_items()
      exit(required && version && image && ports && volumes && certificates && resources && boundary ? 0 : 1)
    }
  ' "${profile_path}"; then
    echo "Missing complete Phase 53.1 Wazuh profile artifact component: ${component}" >&2
    exit 1
  fi

  if ! awk -v component="${component}" -v expected_incompatible="Wazuh 3.x, unreviewed Wazuh 5.x, latest, rc, beta" '
    /version_matrix:/ { in_matrix = 1; next }
    /^profile_expectations:/ { in_matrix = 0 }
    in_matrix && $0 == "  - component: " component {
      in_component = 1
      version = pin = incompatible = 0
      next
    }
    in_matrix && /^  - component:/ && in_component { in_component = 0 }
    in_component && $0 == "    version: 4.12.0" { version = 1 }
    in_component && $0 == "    pin_type: exact" { pin = 1 }
    in_component && $0 == "    incompatible_versions: " expected_incompatible { incompatible = 1 }
    END { exit(version && pin && incompatible ? 0 : 1) }
  ' "${profile_path}"; then
    echo "Missing complete Phase 53.1 Wazuh profile artifact version matrix row: ${component}" >&2
    exit 1
  fi
done

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

contains_placeholder_secret_valid_claim() {
  awk '
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(must fail|fail closed|fails validation|invalid|must not|cannot|not satisfy|subordinate|deferred)/
      if (!in_forbidden_claims && !negative_context && line ~ /(^|[^[:alnum:]_])placeholder secrets?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|production)([^[:alnum:]_]|$)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${contract_rendered_markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 53.1 Wazuh profile contract claim: ${claim}" >&2
    exit 1
  fi
done

if contains_placeholder_secret_valid_claim; then
  echo "Forbidden Phase 53.1 Wazuh profile contract claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${contract_path}" "${profile_path}"; then
  echo "Forbidden Phase 53.1 Wazuh profile contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 53.1 Wazuh profile contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/wazuh-smb-single-node-profile-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 53.1 Wazuh profile contract." >&2
  exit 1
fi

echo "Phase 53.1 Wazuh profile contract is present and preserves component coverage, exact version pins, resource/port/volume/certificate expectations, and authority boundaries."
