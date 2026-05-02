#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/wazuh-agent-enrollment-helper-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 53.5 Wazuh First Agent Enrollment Helper Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Enrollment Helper Contract"
  "## 4. Prerequisites"
  "## 5. First Endpoint Enrollment Steps"
  "## 6. Rollback And Removal"
  "## 7. Safety Warnings"
  "## 8. Validation Rules"
  "## 9. Forbidden Claims"
  "## 10. Validation"
  "## 11. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1135, #1136, #1140"
  "This contract defines the bounded first Wazuh agent enrollment helper posture for one endpoint only."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/wazuh/agent-enrollment-helper.yaml\`."
  "Wazuh is a subordinate detection substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "The enrollment helper covers one reviewed endpoint only."
  "Fleet-scale Wazuh agent management remains out of scope."
  "Enrollment must use a reviewed Wazuh manager address placeholder such as \`<wazuh-manager-host>\` and a reviewed agent enrollment token or password custody reference."
  "The helper must not require committed secrets, inline credentials, customer-specific values, or workstation-local absolute paths."
  "Rollback must remove or disable the enrolled endpoint agent, revoke or rotate the enrollment credential when used, and preserve AegisOps-owned records as the workflow truth."
  "Run \`bash scripts/verify-phase-53-5-wazuh-agent-enrollment-helper-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-53-5-wazuh-agent-enrollment-helper-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1140 --config <supervisor-config-path>\`."
)

required_artifact_terms=(
  "profile_id: smb-single-node"
  "product_profile: wazuh"
  "agent_enrollment_helper_contract_version: 2026-05-03"
  "status: accepted-contract"
  "endpoint_scope: one-reviewed-endpoint"
  "fleet_management_scope: out-of-scope"
  "manager_host_placeholder: <wazuh-manager-host>"
  "agent_name_placeholder: <first-endpoint-agent-name>"
  "enrollment_secret_custody: AEGISOPS_WAZUH_AGENT_ENROLLMENT_SECRET_FILE or AEGISOPS_WAZUH_AGENT_ENROLLMENT_SECRET_OPENBAO_PATH"
  "raw_secret_values_allowed: false"
  "committed_customer_values_allowed: false"
  "workstation_local_paths_allowed: false"
  "wazuh_active_response_authority_allowed: false"
  "aegisops_authority_mutation_allowed: false"
  "prerequisites:"
  "enrollment_steps:"
  "rollback_steps:"
  "safety_warnings:"
  "negative_validation_tests:"
)

required_prerequisites=(
  "reviewed-smb-single-node-wazuh-profile"
  "reviewed-manager-enrollment-port"
  "reviewed-agent-enrollment-secret-custody"
  "one-endpoint-operator-approval"
  "rollback-owner-identified"
)

required_steps=(
  "confirm-reviewed-manager-address"
  "confirm-secret-custody-reference"
  "install-agent-on-one-reviewed-endpoint"
  "enroll-agent-to-reviewed-manager"
  "verify-agent-appears-as-subordinate-signal-source"
)

required_rollback_steps=(
  "disable-or-uninstall-agent-on-first-endpoint"
  "remove-agent-registration-from-wazuh-manager"
  "revoke-or-rotate-enrollment-secret-if-used"
  "record-aegisops-owned-follow-up-if-signal-custody-changed"
)

required_safety_warnings=(
  "do-not-commit-secrets"
  "do-not-use-placeholder-credentials-as-valid"
  "do-not-enroll-fleet"
  "do-not-use-wazuh-status-as-aegisops-truth"
  "do-not-enable-active-response-authority"
  "do-not-use-workstation-local-absolute-paths"
)

forbidden_claims=(
  "Wazuh agent state is AegisOps source truth"
  "Wazuh agent enrollment is AegisOps workflow truth"
  "Wazuh manager agent status is AegisOps evidence truth"
  "Wazuh Active Response is an AegisOps authority path"
  "Placeholder Wazuh enrollment secrets are valid credentials"
  "Committed Wazuh enrollment secrets are acceptable"
  "Phase 53.5 implements fleet-scale Wazuh agent management"
  "Phase 53.5 implements Wazuh upgrade automation"
  "Phase 53.5 implements Shuffle product profiles"
  "Phase 53.5 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness"
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

require_list_item() {
  local file_path="$1"
  local item="$2"
  local label="$3"

  if ! awk -v item="${item}" '
    /^[[:space:]]*#/ { next }
    $0 ~ ("^[[:space:]]*-[[:space:]]+" item "([[:space:]]*(#.*)?)?$") { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${file_path}"; then
    echo "Missing Phase 53.5 Wazuh enrollment ${label}: ${item}" >&2
    exit 1
  fi
}

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 9\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${contract_path}"
}

contains_forbidden_claim_in_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 9\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${contract_path}"
}

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 53.5 Wazuh agent enrollment helper contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 53.5 Wazuh agent enrollment helper artifact: ${artifact_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.5 Wazuh agent enrollment helper contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.5 Wazuh agent enrollment helper contract statement: ${phrase}" >&2
    exit 1
  fi
done

for term in "${required_artifact_terms[@]}"; do
  if ! has_uncommented_substring "${term}" "${artifact_path}"; then
    echo "Missing Phase 53.5 Wazuh agent enrollment helper artifact term: ${term}" >&2
    exit 1
  fi
done

for item in "${required_prerequisites[@]}"; do
  require_list_item "${artifact_path}" "${item}" "prerequisite"
done

for item in "${required_steps[@]}"; do
  require_list_item "${artifact_path}" "${item}" "step"
done

for item in "${required_rollback_steps[@]}"; do
  require_list_item "${artifact_path}" "${item}" "rollback step"
done

for item in "${required_safety_warnings[@]}"; do
  require_list_item "${artifact_path}" "${item}" "safety warning"
done

if grep -Eiq '^[[:space:]]*enrollment_secret_custody:[[:space:]]*($|<|todo|tbd|none|null|changeme|change-me|password|secret|sample|example|fake|dummy)' "${artifact_path}"; then
  echo "Forbidden Phase 53.5 Wazuh enrollment artifact: missing enrollment secret custody reference" >&2
  exit 1
fi

if awk '
  BEGIN { found = 0 }
  /^[[:space:]]*([a-z0-9_-]*_)?(password|secret|token|api_key|enrollment_key)[[:space:]]*:/ {
    value = $0
    sub(/^[^:]+:[[:space:]]*/, "", value)
    if (length(value) >= 12 && value !~ /^(AEGISOPS_|<|\$\{)/) {
      found = 1
    }
  }
  END { exit(found ? 0 : 1) }
' "${artifact_path}"; then
  echo "Forbidden Phase 53.5 Wazuh enrollment artifact: committed secret-looking value detected" >&2
  exit 1
fi

for claim in "${forbidden_claims[@]}"; do
  if ! contains_forbidden_claim_in_section "${claim}"; then
    echo "Missing Phase 53.5 Wazuh forbidden claim: ${claim}" >&2
    exit 1
  fi

  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 53.5 Wazuh enrollment helper claim: ${claim}" >&2
    exit 1
  fi
done

if grep -Eiq 'fleet[-[:space:]]*(scale|wide|management|manager|enrollment|onboarding)|bulk[-[:space:]]*(agent|endpoint|enrollment)|mass[-[:space:]]*(agent|endpoint|enrollment)' "${contract_path}" "${artifact_path}"; then
  if ! grep -Eiq 'fleet-scale Wazuh agent management remains out of scope|Fleet-scale Wazuh agent management remains out of scope|fleet_management_scope: out-of-scope|do-not-enroll-fleet|No fleet-scale Wazuh agent management' "${contract_path}" "${artifact_path}"; then
    echo "Forbidden Phase 53.5 Wazuh enrollment helper claim: fleet management overclaim detected" >&2
    exit 1
  fi
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 53.5 Wazuh enrollment helper contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 53.5 Wazuh enrollment helper contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | tr -d '\140'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/wazuh-agent-enrollment-helper-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 53.5 Wazuh agent enrollment helper contract." >&2
  exit 1
fi

echo "Phase 53.5 Wazuh agent enrollment helper contract is present and rejects missing safety warnings, fleet-management overclaims, committed secrets, authority-boundary overclaims, and workstation-local paths."
