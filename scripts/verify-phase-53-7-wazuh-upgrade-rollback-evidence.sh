#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/wazuh-upgrade-rollback-evidence-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 53.7 Wazuh Upgrade And Rollback Evidence Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Required Evidence Fields"
  "## 4. Component Coverage"
  "## 5. Validation Rules"
  "## 6. Forbidden Claims"
  "## 7. Validation"
  "## 8. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1135, #1136, #1142"
  "This contract defines release evidence expectations for Wazuh profile version changes in the \`smb-single-node\` product profile."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/wazuh/upgrade-rollback-evidence.yaml\`."
  "without implementing a live Wazuh upgrader"
  "Wazuh is a subordinate detection substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "Run \`bash scripts/verify-phase-53-7-wazuh-upgrade-rollback-evidence.sh\`."
  "Run \`bash scripts/test-verify-phase-53-7-wazuh-upgrade-rollback-evidence.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1142 --config <supervisor-config-path>\`."
)

required_artifact_terms=(
  "profile_id: smb-single-node"
  "product_profile: wazuh"
  "upgrade_rollback_evidence_contract_version: 2026-05-03"
  "status: accepted-contract"
  "evidence_owner: aegisops-release-evidence"
  "substrate_owner: wazuh"
  "authority_mutation_allowed: false"
  "full_upgrader_implemented: false"
  "upgrade_automation_allowed: false"
  "fleet_scale_management_allowed: false"
  "workflow_truth_source: aegisops-record-chain-only"
  "components:"
  "required_evidence_fields:"
  "evidence_references:"
  "known_limitations:"
  "profile_change_handoff:"
  "component_evidence:"
  "negative_validation_tests:"
)

required_components=(
  manager
  indexer
  dashboard
)

required_evidence_fields=(
  version_before
  version_after
  rollback_owner
  rollback_trigger
  evidence_references
  known_limitations
  profile_change_handoff
)

required_evidence_references=(
  aegisops-release-gate-record
  wazuh-profile-diff-record
  source-health-projection-review
  backup-restore-rehearsal-record
  validation-rerun-result
)

required_known_limitations=(
  release-evidence-only
  no-full-wazuh-upgrader
  no-wazuh-upgrade-automation
  no-fleet-scale-wazuh-management
  no-beta-rc-ga-commercial-readiness-claim
)

required_negative_tests=(
  missing-rollback-owner
  missing-version-before
  missing-version-after
  missing-rollback-trigger
  placeholder-rollback-trigger
  missing-evidence-references
  missing-known-limitations
  missing-profile-change-handoff
  missing-component-rollback-target
  full-upgrader-claim
  version-state-as-release-truth
)

forbidden_claims=(
  "Wazuh version state is AegisOps release truth"
  "Wazuh upgrade evidence is AegisOps workflow truth"
  "Wazuh rollback evidence closes AegisOps cases"
  "Wazuh manager version is AegisOps source truth"
  "Wazuh dashboard upgrade status is AegisOps approval truth"
  "Wazuh indexer upgrade status is AegisOps evidence truth"
  "Phase 53.7 implements a full Wazuh upgrader"
  "Phase 53.7 implements Wazuh upgrade automation"
  "Phase 53.7 implements fleet-scale Wazuh management"
  "Phase 53.7 implements Shuffle product profiles"
  "Phase 53.7 claims Beta, RC, GA, commercial readiness, or Wazuh replacement readiness"
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
    echo "Missing Phase 53.7 Wazuh upgrade rollback ${label}: ${item}" >&2
    exit 1
  fi
}

require_top_level_scalar() {
  local file_path="$1"
  local key="$2"
  local expected_value="$3"
  local label="$4"

  if ! awk -v key="${key}" -v expected_value="${expected_value}" '
    $0 == key ": " expected_value {
      found = 1
    }
    END { exit(found ? 0 : 1) }
  ' "${file_path}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback top-level ${label}: ${key}: ${expected_value}" >&2
    exit 1
  fi
}

require_top_level_nonplaceholder_scalar() {
  local file_path="$1"
  local key="$2"
  local label="$3"

  if ! awk -v key="${key}" -v label="${label}" '
    function trim(value) {
      sub(/^[[:space:]]+/, "", value)
      sub(/[[:space:]]+$/, "", value)
      return value
    }
    $0 ~ ("^" key ":") {
      line = $0
      sub(/[[:space:]]+#.*/, "", line)
      sub(("^" key ":"), "", line)
      value = trim(line)
      gsub(/^["'\'']|["'\'']$/, "", value)
      value = trim(value)
      if (value == "") {
        missing = 1
        next
      }
      lower_value = tolower(value)
      if (lower_value ~ /^(tbd|to be determined|to be decided|operator.*later|operator.*decides|operator.*discretion|decide later|discretionary|placeholder)$/ ||
          lower_value ~ /^tbd([[:space:][:punct:]]|$)/) {
        placeholder = value
        next
      }
      found = 1
    }
    END {
      if (found) {
        exit 0
      }
      if (placeholder != "") {
        printf "Forbidden Phase 53.7 Wazuh upgrade rollback placeholder %s: %s: %s\n", label, key, placeholder > "/dev/stderr"
      } else {
        printf "Missing Phase 53.7 Wazuh upgrade rollback top-level %s: %s\n", label, key > "/dev/stderr"
      }
      exit 1
    }
  ' "${file_path}"; then
    exit 1
  fi
}

require_component_evidence_field() {
  local file_path="$1"
  local component="$2"
  local field="$3"

  if ! awk -v component="${component}" -v field="${field}" '
    $0 == "component_evidence:" {
      in_component_evidence = 1
      next
    }
    in_component_evidence && /^[^[:space:]][^:]*:/ {
      in_component_evidence = 0
      in_target_component = 0
    }
    in_component_evidence && $0 ~ ("^  " component ":[[:space:]]*(#.*)?$") {
      in_target_component = 1
      next
    }
    in_component_evidence && in_target_component && /^  [^[:space:]][^:]*:/ {
      in_target_component = 0
    }
    in_component_evidence && in_target_component {
      line = $0
      sub(/[[:space:]]+#.*/, "", line)
      if (line ~ ("^    " field ": .+")) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' "${file_path}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback component evidence ${component} field: ${field}" >&2
    exit 1
  fi
}

contains_forbidden_claim_in_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 6\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${contract_path}"
}

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 6\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
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
  echo "Missing Phase 53.7 Wazuh upgrade rollback evidence contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 53.7 Wazuh upgrade rollback evidence artifact: ${artifact_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

if has_uncommented_substring "full_upgrader_implemented: true" "${artifact_path}"; then
  echo "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: full upgrader implementation claim detected" >&2
  exit 1
fi

if has_uncommented_substring "upgrade_automation_allowed: true" "${artifact_path}"; then
  echo "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: upgrade automation claim detected" >&2
  exit 1
fi

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback contract statement: ${phrase}" >&2
    exit 1
  fi
done

for term in "${required_artifact_terms[@]}"; do
  if ! has_uncommented_substring "${term}" "${artifact_path}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback artifact term: ${term}" >&2
    exit 1
  fi
done

require_top_level_scalar "${artifact_path}" "version_before" "4.12.0" "version before"
require_top_level_scalar "${artifact_path}" "version_after" "<reviewed-target-wazuh-version>" "version after"
require_top_level_scalar "${artifact_path}" "rollback_owner" "aegisops-release-owner" "rollback owner"
require_top_level_nonplaceholder_scalar "${artifact_path}" "rollback_trigger" "rollback trigger"

for component in "${required_components[@]}"; do
  require_top_level_list_item "${artifact_path}" "components" "${component}" "component"
  if ! grep -Fq -- "| ${component} |" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback contract component row: ${component}" >&2
    exit 1
  fi
  if ! has_uncommented_substring "  ${component}:" "${artifact_path}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback component evidence: ${component}" >&2
    exit 1
  fi
  require_component_evidence_field "${artifact_path}" "${component}" "version_before"
  require_component_evidence_field "${artifact_path}" "${component}" "version_after"
  require_component_evidence_field "${artifact_path}" "${component}" "rollback_target"
done

for field in "${required_evidence_fields[@]}"; do
  require_top_level_list_item "${artifact_path}" "required_evidence_fields" "${field}" "required evidence field"
  if ! grep -Fq -- "\`${field}\`" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback contract field row: ${field}" >&2
    exit 1
  fi
done

for reference in "${required_evidence_references[@]}"; do
  require_top_level_list_item "${artifact_path}" "evidence_references" "${reference}" "evidence reference"
done

for limitation in "${required_known_limitations[@]}"; do
  require_top_level_list_item "${artifact_path}" "known_limitations" "${limitation}" "known limitation"
done

for negative_test in "${required_negative_tests[@]}"; do
  require_top_level_list_item "${artifact_path}" "negative_validation_tests" "${negative_test}" "negative test"
done

for claim in "${forbidden_claims[@]}"; do
  if ! contains_forbidden_claim_in_section "${claim}"; then
    echo "Missing Phase 53.7 Wazuh upgrade rollback forbidden claim: ${claim}" >&2
    exit 1
  fi

  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 53.7 Wazuh upgrade rollback claim: ${claim}" >&2
    exit 1
  fi
done

for secret_scan_path in "${contract_path}" "${artifact_path}"; do
  if contains_secret_looking_value "${secret_scan_path}"; then
    echo "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: committed secret-looking value detected in ${secret_scan_path}" >&2
    exit 1
  fi
done

mac_user_home_pattern="/""Users/"
posix_user_home_pattern="/""home/[^[:space:]/]+"
windows_user_home_pattern='C:\\''Users\\'
if grep -REq "${mac_user_home_pattern}|${posix_user_home_pattern}|${windows_user_home_pattern}" "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 53.7 Wazuh upgrade rollback artifact: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 53.7 Wazuh upgrade rollback link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}"
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/wazuh-upgrade-rollback-evidence-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 53.7 Wazuh upgrade rollback evidence contract." >&2
  exit 1
fi

echo "Phase 53.7 Wazuh upgrade rollback evidence contract is present and rejects missing owner, versions, rollback posture, component rollback targets, evidence, limitations, full-upgrader claims, authority promotion, and workstation-local paths."
