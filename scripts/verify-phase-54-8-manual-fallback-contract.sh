#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/shuffle-manual-fallback-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/manual-fallback-contract.yaml"
readme_path="${repo_root}/README.md"

reviewed_templates=(
  notify_identity_owner
  create_tracking_ticket
  enrichment_only_lookup
  operator_notification
  manual_escalation_request
)

required_headings=(
  "# Phase 54.8 Shuffle Manual Fallback Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Fallback Record Contract"
  "## 4. Covered Failure States"
  "## 5. Reviewed Template Coverage"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1154, #1160, #1162"
  "This contract defines the manual fallback and operator-note path for unavailable Shuffle, rejected execution, missing receipt, stale receipt, and mismatched receipt states for every reviewed Phase 54 Shuffle template."
  "Manual fallback is subordinate operator guidance and does not create a bypass approval path."
  "AegisOps control-plane records remain authoritative for approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "| Fallback owner | \`fallback_owner_id\` | Missing, blank, placeholder, inferred, or template-derived owner rejects the fallback record. |"
  "| Operator note | \`operator_note\` | Missing, blank, approval-bypass, reconciliation-truth, or Shuffle-success-as-truth note rejects the fallback record. |"
  "| Affected template/action | \`affected_template_id\`, \`affected_action_type\`, \`action_request_id\` | Missing, blank, mismatched, inferred, or unreviewed template/action linkage rejects the fallback record. |"
  "| Expected evidence | \`expected_evidence\` | Missing, blank, broad, or authority-promoting evidence expectations reject the fallback record. |"
  "| Blocked/unavailable reason | \`blocked_reason\`, \`fallback_state\` | Missing, blank, unsupported, success-like, or inferred reason rejects the fallback record. |"
  "| \`notify_identity_owner\` | \`notify_identity_owner\` | \`identity-owner-low-risk-notification-only\` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |"
  "| \`create_tracking_ticket\` | \`create_tracking_ticket\` | \`ticket-coordination-context-only\` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |"
  "| \`enrichment_only_lookup\` | \`enrichment_only_lookup\` | \`read-only-enrichment-lookup\` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |"
  "| \`operator_notification\` | \`operator_notification\` | \`operator-notification-only\` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |"
  "| \`manual_escalation_request\` | \`manual_escalation_request\` | \`manual-escalation-request-only\` | Fallback owner, operator note, expected evidence, and blocked reason are required when Shuffle cannot produce a valid normalized receipt. |"
  "Run \`bash scripts/verify-phase-54-8-manual-fallback-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-54-8-manual-fallback-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1162 --config <supervisor-config-path>\`."
)

forbidden_claims=(
  "Manual fallback bypasses AegisOps approval"
  "Manual fallback note is AegisOps reconciliation truth"
  "Unavailable Shuffle is reported as successful execution"
  "Rejected execution is reported as successful execution"
  "Missing receipt is treated as successful execution"
  "Stale receipt is treated as successful execution"
  "Mismatched receipt is treated as successful execution"
  "Shuffle workflow success is AegisOps reconciliation truth"
  "Shuffle callback payload is AegisOps execution receipt truth"
  "Operator note closes AegisOps cases"
  "Operator note changes AegisOps approval decisions"
  "Fallback owner can be inferred from template name, path, issue text, tenant name, account name, or nearby metadata"
  "Phase 54.8 implements broad SOAR action catalog expansion"
  "Phase 54.8 enables Controlled Write by default"
  "Phase 54.8 enables Hard Write by default"
  "Phase 54.8 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement"
)

fallback_states=(
  shuffle_unavailable
  execution_rejected
  missing_receipt
  stale_receipt
  mismatched_receipt
)

required_record_fields=(
  fallback_owner_id
  operator_note
  affected_template_id
  affected_action_type
  action_request_id
  expected_evidence
  blocked_reason
  fallback_state
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

assert_rendered_contains() {
  local rendered="$1"
  local expected="$2"
  local label="$3"

  if ! grep -Fq -- "${expected}" <<<"${rendered}"; then
    echo "Missing ${label}: ${expected}" >&2
    exit 1
  fi
}

assert_file_contains() {
  local path="$1"
  local expected="$2"
  local label="$3"

  if ! grep -Fq -- "${expected}" "${path}"; then
    echo "Missing ${label}: ${expected}" >&2
    exit 1
  fi
}

assert_yaml_list_contains() {
  local list_name="$1"
  local item="$2"
  local label="$3"

  if ! awk -v list_name="${list_name}" -v item="${item}" '
    $0 == list_name ":" {
      in_list = 1
      next
    }
    in_list && /^[^[:space:]]/ {
      in_list = 0
    }
    in_list && $0 == "  - " item {
      found = 1
    }
    END { exit(found ? 0 : 1) }
  ' "${artifact_path}"; then
    echo "Missing Phase 54.8 manual fallback artifact ${list_name} item: ${item}" >&2
    exit 1
  fi
}

yaml_top_field_value() {
  local field="$1"

  awk -v field="${field}" '
    $0 ~ "^" field ":[[:space:]]*" {
      sub("^" field ":[[:space:]]*", "", $0)
      print
      exit
    }
  ' "${artifact_path}"
}

yaml_section_field_value() {
  local section="$1"
  local field="$2"

  awk -v section="${section}" -v field="${field}" '
    $0 == section ":" {
      in_section = 1
      next
    }
    in_section && /^[^[:space:]]/ {
      in_section = 0
    }
    in_section && $0 ~ "^  " field ":[[:space:]]*" {
      sub("^  " field ":[[:space:]]*", "", $0)
      print
      exit
    }
  ' "${artifact_path}"
}

assert_top_field_equals() {
  local field="$1"
  local expected="$2"
  local actual

  actual="$(yaml_top_field_value "${field}")"
  if [[ "${actual}" != "${expected}" ]]; then
    [[ -n "${actual}" ]] || actual="<missing>"
    echo "Mismatched Phase 54.8 manual fallback artifact field ${field}: expected [${expected}] actual [${actual}]" >&2
    exit 1
  fi
}

assert_section_field_equals() {
  local section="$1"
  local field="$2"
  local expected="$3"
  local actual

  actual="$(yaml_section_field_value "${section}" "${field}")"
  if [[ "${actual}" != "${expected}" ]]; then
    [[ -n "${actual}" ]] || actual="<missing>"
    echo "Mismatched Phase 54.8 manual fallback artifact field ${section}.${field}: expected [${expected}] actual [${actual}]" >&2
    exit 1
  fi
}

assert_template_coverage() {
  local template="$1"
  local action_type="$2"
  local scope="$3"

  if ! awk -v template="${template}" -v action_type="${action_type}" -v scope="${scope}" '
    $0 == "reviewed_template_coverage:" {
      in_coverage = 1
      next
    }
    in_coverage && /^[^[:space:]]/ {
      in_coverage = 0
    }
    in_coverage && $0 == "  - template_id: " template {
      in_template = 1
      found_template = 1
      found_action = 0
      found_scope = 0
      found_required = 0
      next
    }
    in_template && $0 ~ /^  - template_id: / {
      in_template = 0
    }
    in_template && $0 == "    action_type: " action_type {
      found_action = 1
    }
    in_template && $0 == "    scope: " scope {
      found_scope = 1
    }
    in_template && $0 == "    manual_fallback_required: true" {
      found_required = 1
    }
    END { exit(found_template && found_action && found_scope && found_required ? 0 : 1) }
  ' "${artifact_path}"; then
    echo "Missing Phase 54.8 manual fallback reviewed_template_coverage entry for ${template}" >&2
    exit 1
  fi
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

assert_no_workstation_local_paths() {
  local path="$1"
  local label="$2"
  local slash
  local backslash
  local mac_home_root
  local unix_home_root
  local common_unix_root
  local generic_unix_absolute_path
  local windows_drive_root
  local windows_unc_root
  local workstation_path_pattern

  slash="/"
  backslash="\\\\"
  mac_home_root="${slash}Users${slash}"
  unix_home_root="${slash}home${slash}[^[:space:]${slash}]+${slash}"
  common_unix_root="${slash}(mnt|Volumes|private|root)${slash}"
  generic_unix_absolute_path="${slash}[^${slash}[:space:]][^[:space:]]*"
  windows_drive_root="[A-Za-z]:[${backslash}${slash}]+"
  windows_unc_root="${backslash}${backslash}[^${backslash}${slash}[:space:]]+[${backslash}${slash}]+[^${backslash}${slash}[:space:]]+"
  workstation_path_pattern="(^|[^[:alnum:]_.${slash}>-])(${mac_home_root}|${unix_home_root}|${common_unix_root}|${generic_unix_absolute_path}|${windows_drive_root}|${windows_unc_root})"

  if grep -En "${workstation_path_pattern}" "${path}" >/dev/null; then
    echo "Forbidden Phase 54.8 manual fallback contract: workstation-local absolute path detected in ${label}" >&2
    exit 1
  fi
}

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 54.8 manual fallback contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 54.8 manual fallback artifact: ${artifact_path}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README.md" >&2
  exit 1
fi

contract_rendered_markdown="$(rendered_markdown_without_code_blocks "${contract_path}")"

for heading in "${required_headings[@]}"; do
  assert_rendered_contains "${contract_rendered_markdown}" "${heading}" "Phase 54.8 manual fallback contract heading"
done

for phrase in "${required_phrases[@]}"; do
  assert_rendered_contains "${contract_rendered_markdown}" "${phrase}" "Phase 54.8 manual fallback contract statement"
done

for claim in "${forbidden_claims[@]}"; do
  assert_rendered_contains "${contract_rendered_markdown}" "- ${claim}." "Phase 54.8 forbidden claim listing"
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 54.8 manual fallback contract claim: ${claim}" >&2
    exit 1
  fi
done

assert_no_workstation_local_paths "${contract_path}" "${contract_path}"
assert_no_workstation_local_paths "${artifact_path}" "${artifact_path}"

assert_top_field_equals contract_id shuffle-manual-fallback-contract
assert_top_field_equals product_profile shuffle
assert_top_field_equals profile_id smb-single-node
assert_top_field_equals contract_version 2026-05-03
assert_top_field_equals status accepted-contract
assert_top_field_equals manual_fallback_role "subordinate-operator-guidance-only"
assert_top_field_equals approval_bypass "forbidden"
assert_top_field_equals reconciliation_truth "aegisops-control-plane-only"

assert_section_field_equals required_record fallback_owner_id "explicit fallback owner required"
assert_section_field_equals required_record operator_note "explicit operator note required"
assert_section_field_equals required_record affected_template_id "reviewed Phase 54 Shuffle template id required"
assert_section_field_equals required_record affected_action_type "reviewed Phase 54 action type required"
assert_section_field_equals required_record action_request_id "explicit AegisOps action request id required"
assert_section_field_equals required_record expected_evidence "explicit expected evidence required"
assert_section_field_equals required_record blocked_reason "explicit blocked or unavailable reason required"
assert_section_field_equals required_record fallback_state "one of shuffle_unavailable, execution_rejected, missing_receipt, stale_receipt, mismatched_receipt"
assert_section_field_equals validation_rules missing_fallback_owner reject
assert_section_field_equals validation_rules approval_bypass_note reject
assert_section_field_equals validation_rules unavailable_reported_success reject
assert_section_field_equals validation_rules rejected_execution_reported_success reject
assert_section_field_equals validation_rules missing_receipt_reported_success reject
assert_section_field_equals validation_rules stale_receipt_reported_success reject
assert_section_field_equals validation_rules mismatched_receipt_reported_success reject
assert_section_field_equals validation_rules manual_note_as_reconciliation_truth reject
assert_section_field_equals validation_rules inferred_owner_or_template_linkage reject

for state in "${fallback_states[@]}"; do
  assert_yaml_list_contains fallback_states "${state}" "fallback_states"
done

for field in "${required_record_fields[@]}"; do
  assert_yaml_list_contains required_record_fields "${field}" "required_record_fields"
done

assert_template_coverage notify_identity_owner notify_identity_owner identity-owner-low-risk-notification-only
assert_template_coverage create_tracking_ticket create_tracking_ticket ticket-coordination-context-only
assert_template_coverage enrichment_only_lookup enrichment_only_lookup read-only-enrichment-lookup
assert_template_coverage operator_notification operator_notification operator-notification-only
assert_template_coverage manual_escalation_request manual_escalation_request manual-escalation-request-only

for template in "${reviewed_templates[@]}"; do
  template_path="${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates/${template}-import-contract.yaml"
  if [[ ! -f "${template_path}" ]]; then
    echo "Missing reviewed Phase 54 template artifact for manual fallback coverage: ${template_path}" >&2
    exit 1
  fi
done

assert_file_contains \
  "${readme_path}" \
  "[Phase 54.8 manual fallback contract](docs/deployment/shuffle-manual-fallback-contract.md)" \
  "README Phase 54.8 manual fallback contract link"

echo "Phase 54.8 manual fallback contract verified."
