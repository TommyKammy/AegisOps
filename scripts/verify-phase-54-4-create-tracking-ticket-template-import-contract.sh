#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/shuffle-create-tracking-ticket-template-import-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates/create_tracking_ticket-import-contract.yaml"
readme_path="${repo_root}/README.md"
expected_authority_boundary="Ticket pointer, ticket status, ticket comments, ticket assignments, ticket SLA state, Shuffle workflow status, success, failure, callback payloads, execution logs, generated config, and template metadata remain subordinate coordination or automation context; AegisOps control-plane records remain authoritative for approval, action request, execution receipt, reconciliation, release, gate, limitation, and closeout truth."

required_headings=(
  "# Phase 54.4 create_tracking_ticket Shuffle Template Import Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Template Import Metadata"
  "## 4. Required Binding Contract"
  "## 5. Import Entry Rules"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1154, #1156, #1158"
  "This contract defines the repo-owned \`create_tracking_ticket\` Shuffle workflow template import contract for the Phase 54 \`smb-single-node\` product profile."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/shuffle/templates/create_tracking_ticket-import-contract.yaml\`."
  "The contract binds request identity, approval identity, correlation identity, receipt identity, ticket pointer, ticket system identity, ticket pointer custody, ticket coordination scope, and reviewed template version without treating ticket state or Shuffle state as authoritative AegisOps truth."
  "Shuffle is a subordinate routine automation substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "| Field | Required | Expected value or binding | Authority boundary |"
  "| Contract area | Required fields | Failure rule |"
  "| Request | \`action_request_id\` | Missing, blank, mismatched, or inferred request id rejects the template import. |"
  "| Approval | \`approval_decision_id\` | Missing, blank, mismatched, or inferred approval id rejects the template import. |"
  "| Correlation | \`correlation_id\` | Missing, blank, or one-sided correlation rejects the template import. |"
  "| Receipt | \`execution_receipt_id\`, \`normalized_receipt_ref\` | Missing or blank receipt fields reject the template import. |"
  "| Ticket pointer | \`ticket_pointer_id\`, \`ticket_system_id\`, \`ticket_pointer_custody\` | Missing, blank, inferred, or authoritative ticket pointer fields reject the template import. |"
  "| Ticket coordination scope | \`ticket_coordination_scope\` | Missing, blank, broad, authority-mutating, or truth-promoting scope rejects the template import. |"
  "| Version | \`reviewed_template_version\` | Missing or mismatched reviewed template version rejects the template import. |"
  "- The only accepted ticket coordination scope is \`ticket-coordination-context-only\`."
  "- Ticket status as AegisOps case truth is forbidden."
  "- Ticket close as AegisOps reconciliation truth is forbidden."
  "Run \`bash scripts/verify-phase-54-4-create-tracking-ticket-template-import-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-54-4-create-tracking-ticket-template-import-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1158 --config <supervisor-config-path>\`."
)

required_artifact_lines=(
  "contract_id: shuffle-create-tracking-ticket-template-import"
  "product_profile: shuffle"
  "profile_id: smb-single-node"
  "workflow_template_id: create_tracking_ticket"
  "contract_version: 2026-05-03"
  "status: accepted-import-contract"
  "authority_boundary: ${expected_authority_boundary}"
  "  template_id: create_tracking_ticket"
  "  reviewed_template_version: create_tracking_ticket-v1-reviewed-2026-05-03"
  "  owner: AegisOps maintainers"
  "  review_status: reviewed"
  "  import_eligible: true"
  "  action_type: create_tracking_ticket"
  "  action_request_id: explicit AegisOps action request id required"
  "  approval_decision_id: explicit AegisOps approval decision id required"
  "  correlation_id: required in inputs and outputs"
  "  execution_receipt_id: required in outputs"
  "  normalized_receipt_ref: required in outputs"
  "  ticket_pointer_id: explicit non-authoritative ticket pointer required"
  "  ticket_system_id: explicit ticket system identity required"
  "  ticket_pointer_custody: explicit non-authoritative coordination pointer required"
  "  ticket_coordination_scope: ticket-coordination-context-only"
  "  reviewed_template_version: create_tracking_ticket-v1-reviewed-2026-05-03"
  "  missing_request_id: reject"
  "  missing_approval_id: reject"
  "  missing_correlation_id: reject"
  "  missing_receipt_id: reject"
  "  missing_ticket_pointer: reject"
  "  missing_ticket_system: reject"
  "  missing_ticket_pointer_custody: reject"
  "  missing_ticket_coordination_scope: reject"
  "  missing_reviewed_template_version: reject"
  "  inferred_linkage: reject"
  "  placeholder_secret_values: reject"
  "  create_ticket_only: required"
  "  allowed_target_effect: create or update a non-authoritative tracking ticket pointer only"
  "  ticket_status_as_case_truth: forbidden"
  "  ticket_close_as_reconciliation_truth: forbidden"
  "  protected_target_state_mutation: forbidden"
  "  account_disablement: forbidden"
  "  credential_rotation: forbidden"
  "  group_membership_change: forbidden"
  "  ticket_or_case_closure: forbidden"
  "  callback_url: <aegisops-shuffle-callback-url>"
  "  callback_secret_ref: trusted secret reference required"
  "  callback_payload_authority: subordinate evidence only until normalized into an AegisOps execution receipt"
)

required_bindings=(
  action_request_id
  approval_decision_id
  correlation_id
  execution_receipt_id
  normalized_receipt_ref
  ticket_pointer_id
  ticket_system_id
  ticket_pointer_custody
  ticket_coordination_scope
  reviewed_template_version
)

required_inputs=(
  action_request_id
  approval_decision_id
  correlation_id
  ticket_pointer_id
  ticket_system_id
  ticket_pointer_custody
  ticket_coordination_scope
  reviewed_template_version
  requested_by
  callback_url
  callback_secret_ref
)

required_outputs=(
  action_request_id
  approval_decision_id
  correlation_id
  execution_receipt_id
  normalized_receipt_ref
  reviewed_template_version
  execution_status
  ticket_pointer_id
  ticket_system_id
  ticket_pointer_custody
  execution_started_at
  execution_finished_at
)

forbidden_claims=(
  "Shuffle workflow success is AegisOps reconciliation truth"
  "Shuffle callback payload is AegisOps execution receipt truth"
  "Shuffle workflow status closes AegisOps cases"
  "Shuffle execution logs are AegisOps audit truth"
  "Ticket status is AegisOps case truth"
  "Ticket close is AegisOps reconciliation truth"
  "Ticket status is AegisOps workflow truth"
  "Ticket pointer is AegisOps reconciliation truth"
  "create_tracking_ticket mutates ticket or case authority state"
  "create_tracking_ticket disables accounts"
  "create_tracking_ticket rotates credentials"
  "create_tracking_ticket changes group membership"
  "create_tracking_ticket closes cases"
  "Template names imply approval decision binding"
  "Template paths imply action request binding"
  "Ticket pointer can be inferred from a case name, template path, comment, tenant name, issue text, or sibling metadata"
  "Placeholder Shuffle API keys are valid credentials"
  "Raw forwarded headers are trusted callback identity"
  "Phase 54.4 implements broad ticket creation catalog expansion"
  "Phase 54.4 implements write-capable Shuffle actions"
  "Phase 54.4 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement"
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
    echo "Mismatched Phase 54.4 create_tracking_ticket import artifact field ${field}: expected [${expected}] actual [${actual}]" >&2
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
    echo "Mismatched Phase 54.4 create_tracking_ticket import artifact field ${section}.${field}: expected [${expected}] actual [${actual}]" >&2
    exit 1
  fi
}

assert_list_contains() {
  local list_name="$1"
  local item="$2"

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
    echo "Missing Phase 54.4 create_tracking_ticket import artifact ${list_name} item: ${item}" >&2
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

contains_placeholder_secret_valid_claim() {
  awk '
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(must fail|fail closed|fails validation|invalid|must not|cannot|not satisfy|subordinate|deferred|reject)/
      if (!in_forbidden_claims && !negative_context && line ~ /(^|[^[:alnum:]_])placeholder[^.]*secrets?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|production)([^[:alnum:]_]|$)/) {
        found = 1
      }
      if (!in_forbidden_claims && !negative_context && line ~ /(^|[^[:alnum:]_])placeholder[^.]*api keys?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|production)([^[:alnum:]_]|$)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${contract_rendered_markdown}"
}

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 54.4 create_tracking_ticket template import contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 54.4 create_tracking_ticket template import artifact: ${artifact_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 54.4 create_tracking_ticket template import contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 54.4 create_tracking_ticket template import contract statement: ${phrase}" >&2
    exit 1
  fi
done

for line in "${required_artifact_lines[@]}"; do
  if ! grep -Fxq -- "${line}" "${artifact_path}"; then
    echo "Missing exact Phase 54.4 create_tracking_ticket import artifact line: ${line}" >&2
    exit 1
  fi
done

assert_top_field_equals "contract_id" "shuffle-create-tracking-ticket-template-import"
assert_top_field_equals "product_profile" "shuffle"
assert_top_field_equals "profile_id" "smb-single-node"
assert_top_field_equals "workflow_template_id" "create_tracking_ticket"
assert_top_field_equals "contract_version" "2026-05-03"
assert_top_field_equals "status" "accepted-import-contract"
assert_top_field_equals "authority_boundary" "${expected_authority_boundary}"
assert_section_field_equals "template_metadata" "template_id" "create_tracking_ticket"
assert_section_field_equals "template_metadata" "reviewed_template_version" "create_tracking_ticket-v1-reviewed-2026-05-03"
assert_section_field_equals "template_metadata" "owner" "AegisOps maintainers"
assert_section_field_equals "template_metadata" "review_status" "reviewed"
assert_section_field_equals "template_metadata" "import_eligible" "true"
assert_section_field_equals "template_metadata" "action_type" "create_tracking_ticket"
assert_section_field_equals "binding_contract" "ticket_system_id" "explicit ticket system identity required"
assert_section_field_equals "binding_contract" "ticket_pointer_custody" "explicit non-authoritative coordination pointer required"
assert_section_field_equals "binding_contract" "ticket_coordination_scope" "ticket-coordination-context-only"
assert_section_field_equals "binding_contract" "reviewed_template_version" "create_tracking_ticket-v1-reviewed-2026-05-03"
assert_section_field_equals "validation_rules" "review_status" "reviewed"
assert_section_field_equals "validation_rules" "action_type" "create_tracking_ticket"
assert_section_field_equals "validation_rules" "import_eligible" "true"
assert_section_field_equals "validation_rules" "missing_request_id" "reject"
assert_section_field_equals "validation_rules" "missing_approval_id" "reject"
assert_section_field_equals "validation_rules" "missing_correlation_id" "reject"
assert_section_field_equals "validation_rules" "missing_receipt_id" "reject"
assert_section_field_equals "validation_rules" "missing_ticket_pointer" "reject"
assert_section_field_equals "validation_rules" "missing_ticket_system" "reject"
assert_section_field_equals "validation_rules" "missing_ticket_pointer_custody" "reject"
assert_section_field_equals "validation_rules" "missing_ticket_coordination_scope" "reject"
assert_section_field_equals "validation_rules" "missing_reviewed_template_version" "reject"
assert_section_field_equals "validation_rules" "inferred_linkage" "reject"
assert_section_field_equals "validation_rules" "placeholder_secret_values" "reject"
assert_section_field_equals "mutation_boundary" "create_ticket_only" "required"
assert_section_field_equals "mutation_boundary" "allowed_target_effect" "create or update a non-authoritative tracking ticket pointer only"
assert_section_field_equals "mutation_boundary" "ticket_status_as_case_truth" "forbidden"
assert_section_field_equals "mutation_boundary" "ticket_close_as_reconciliation_truth" "forbidden"
assert_section_field_equals "mutation_boundary" "protected_target_state_mutation" "forbidden"
assert_section_field_equals "mutation_boundary" "account_disablement" "forbidden"
assert_section_field_equals "mutation_boundary" "credential_rotation" "forbidden"
assert_section_field_equals "mutation_boundary" "group_membership_change" "forbidden"
assert_section_field_equals "mutation_boundary" "ticket_or_case_closure" "forbidden"
assert_section_field_equals "callback_boundary" "callback_url" "<aegisops-shuffle-callback-url>"
assert_section_field_equals "callback_boundary" "callback_secret_ref" "trusted secret reference required"

for binding_field in "${required_bindings[@]}"; do
  assert_list_contains "required_bindings" "${binding_field}"
done

for input_field in "${required_inputs[@]}"; do
  assert_list_contains "required_inputs" "${input_field}"
done

for output_field in "${required_outputs[@]}"; do
  assert_list_contains "required_outputs" "${output_field}"
done

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 54.4 create_tracking_ticket template import contract claim: ${claim}" >&2
    exit 1
  fi
done

if contains_placeholder_secret_valid_claim; then
  echo "Forbidden Phase 54.4 create_tracking_ticket template import contract claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

if grep -Eq 'review_status:[[:space:]]*(unreviewed|draft|sample|placeholder|TODO|todo|deprecated)' "${artifact_path}"; then
  echo "Forbidden Phase 54.4 create_tracking_ticket import artifact: unreviewed template status enters product mainline" >&2
  exit 1
fi

if grep -Eq 'reviewed_template_version:[[:space:]]*(latest|floating|TODO|todo|sample|placeholder|draft|unreviewed|deprecated)?[[:space:]]*$' "${artifact_path}"; then
  echo "Forbidden Phase 54.4 create_tracking_ticket import artifact: missing reviewed template version pin" >&2
  exit 1
fi

if grep -Eq 'ticket_status_as_case_truth:[[:space:]]*(allowed|true|enabled|yes)|ticket_close_as_reconciliation_truth:[[:space:]]*(allowed|true|enabled|yes)|protected_target_state_mutation:[[:space:]]*(allowed|true|enabled|yes)|account_disablement:[[:space:]]*(allowed|true|enabled|yes)|credential_rotation:[[:space:]]*(allowed|true|enabled|yes)|group_membership_change:[[:space:]]*(allowed|true|enabled|yes)|ticket_or_case_closure:[[:space:]]*(allowed|true|enabled|yes)' "${artifact_path}"; then
  echo "Forbidden Phase 54.4 create_tracking_ticket import artifact: ticket or case authority state mutation is allowed" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 54.4 create_tracking_ticket template import contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 54.4 create_tracking_ticket template import contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/shuffle-create-tracking-ticket-template-import-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 54.4 create_tracking_ticket template import contract." >&2
  exit 1
fi

echo "Phase 54.4 create_tracking_ticket template import contract is present and preserves required request, approval, correlation, receipt, ticket pointer, ticket system, custody, reviewed version, and ticket non-authority boundaries."
