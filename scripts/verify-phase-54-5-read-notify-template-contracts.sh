#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/shuffle-read-notify-template-contracts.md"
template_dir="${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/templates"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 54.5 Read/Notify Shuffle Template Contracts"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Template Contract Metadata"
  "## 4. Required Binding Contract"
  "## 5. Entry Rules"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1154, #1156, #1159"
  "This contract defines repo-owned \`enrichment_only_lookup\`, \`operator_notification\`, and \`manual_escalation_request\` Shuffle template contracts for the Phase 54 \`smb-single-node\` product profile."
  "Shuffle is a subordinate routine automation substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "| \`enrichment_only_lookup\` | \`enrichment_only_lookup\` | \`read-only-enrichment-lookup\` | Read subordinate context and return lookup evidence only. | No protected target state mutation, account change, credential rotation, group membership change, ticket closure, case closure, or workflow state change. |"
  "| \`operator_notification\` | \`operator_notification\` | \`operator-notification-only\` | Notify a reviewed operator recipient only. | No authoritative workflow state mutation, case closure, ticket closure, approval decision, reconciliation decision, or protected target state mutation. |"
  "| \`manual_escalation_request\` | \`manual_escalation_request\` | \`manual-escalation-request-only\` | Request human escalation through an AegisOps-approved path only. | No AegisOps approval bypass, automatic escalation approval, case closure, ticket closure, or protected target state mutation. |"
  "| Request | \`action_request_id\` | Missing, blank, mismatched, or inferred request id rejects the template contract. |"
  "| Approval | \`approval_decision_id\` | Missing, blank, mismatched, or inferred approval id rejects the template contract. |"
  "| Receipt | \`execution_receipt_id\`, \`normalized_receipt_ref\` | Missing or blank receipt fields reject the template contract. |"
  "- \`enrichment_only_lookup\` is enrichment-only and read-only. It may return subordinate lookup evidence but cannot mutate protected target state."
  "- \`operator_notification\` is notification-only. It cannot change authoritative workflow state, close cases, close tickets, approve actions, reconcile actions, or mutate protected target state."
  "- \`manual_escalation_request\` is a request-only path. It cannot bypass AegisOps approval, create automatic escalation approval, close cases, close tickets, or mutate protected target state."
  "Run \`bash scripts/verify-phase-54-5-read-notify-template-contracts.sh\`."
  "Run \`bash scripts/test-verify-phase-54-5-read-notify-template-contracts.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1159 --config <supervisor-config-path>\`."
)

forbidden_claims=(
  "Shuffle workflow success is AegisOps reconciliation truth"
  "Shuffle callback payload is AegisOps execution receipt truth"
  "Shuffle workflow status closes AegisOps cases"
  "Shuffle execution logs are AegisOps audit truth"
  "enrichment_only_lookup mutates protected target state"
  "enrichment_only_lookup disables accounts"
  "enrichment_only_lookup rotates credentials"
  "enrichment_only_lookup changes group membership"
  "operator_notification changes authoritative workflow state"
  "operator_notification closes cases"
  "operator_notification closes tickets"
  "manual_escalation_request bypasses AegisOps approval"
  "manual_escalation_request creates automatic approval"
  "manual_escalation_request closes cases"
  "Phase 54.5 implements broad enrichment marketplace expansion"
  "Phase 54.5 implements write-capable Shuffle actions"
  "Phase 54.5 enables Controlled Write by default"
  "Phase 54.5 enables Hard Write by default"
  "Phase 54.5 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement"
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

assert_file_contains() {
  local path="$1"
  local expected="$2"
  local label="$3"

  if ! grep -Fq -- "${expected}" "${path}"; then
    echo "Missing ${label}: ${expected}" >&2
    exit 1
  fi
}

assert_exact_line() {
  local path="$1"
  local expected="$2"
  local label="$3"

  if ! grep -Fxq -- "${expected}" "${path}"; then
    echo "Missing exact ${label} line: ${expected}" >&2
    exit 1
  fi
}

assert_yaml_list_contains() {
  local artifact_path="$1"
  local list_name="$2"
  local item="$3"
  local label="$4"

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
    echo "Missing Phase 54.5 ${label} artifact ${list_name} item: ${item}" >&2
    exit 1
  fi
}

yaml_top_field_value() {
  local artifact_path="$1"
  local field="$2"

  awk -v field="${field}" '
    $0 ~ "^" field ":[[:space:]]*" {
      sub("^" field ":[[:space:]]*", "", $0)
      print
      exit
    }
  ' "${artifact_path}"
}

yaml_section_field_value() {
  local artifact_path="$1"
  local section="$2"
  local field="$3"

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
  local artifact_path="$1"
  local field="$2"
  local expected="$3"
  local label="$4"
  local actual

  actual="$(yaml_top_field_value "${artifact_path}" "${field}")"
  if [[ "${actual}" != "${expected}" ]]; then
    [[ -n "${actual}" ]] || actual="<missing>"
    echo "Mismatched Phase 54.5 ${label} artifact field ${field}: expected [${expected}] actual [${actual}]" >&2
    exit 1
  fi
}

assert_section_field_equals() {
  local artifact_path="$1"
  local section="$2"
  local field="$3"
  local expected="$4"
  local label="$5"
  local actual

  actual="$(yaml_section_field_value "${artifact_path}" "${section}" "${field}")"
  if [[ "${actual}" != "${expected}" ]]; then
    [[ -n "${actual}" ]] || actual="<missing>"
    echo "Mismatched Phase 54.5 ${label} artifact field ${section}.${field}: expected [${expected}] actual [${actual}]" >&2
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

assert_no_workstation_local_paths() {
  local path="$1"
  local label="$2"

  if grep -En '(^|[^[:alnum:]_])(/Users/|/home/[^[:space:]/]+/|C:\\Users\\)' "${path}" >/dev/null; then
    echo "Forbidden Phase 54.5 Read/Notify template contract: workstation-local absolute path detected in ${label}" >&2
    exit 1
  fi
}

verify_artifact_common() {
  local template="$1"
  local artifact_path="$2"
  local expected_contract_id="$3"
  local expected_scope_field="$4"
  local expected_scope_value="$5"

  assert_top_field_equals "${artifact_path}" contract_id "${expected_contract_id}" "${template}"
  assert_top_field_equals "${artifact_path}" product_profile shuffle "${template}"
  assert_top_field_equals "${artifact_path}" profile_id smb-single-node "${template}"
  assert_top_field_equals "${artifact_path}" workflow_template_id "${template}" "${template}"
  assert_top_field_equals "${artifact_path}" contract_version 2026-05-03 "${template}"
  assert_top_field_equals "${artifact_path}" status accepted-import-contract "${template}"
  assert_section_field_equals "${artifact_path}" template_metadata template_id "${template}" "${template}"
  assert_section_field_equals "${artifact_path}" template_metadata reviewed_template_version "${template}-v1-reviewed-2026-05-03" "${template}"
  assert_section_field_equals "${artifact_path}" template_metadata review_status reviewed "${template}"
  assert_section_field_equals "${artifact_path}" template_metadata import_eligible true "${template}"
  assert_section_field_equals "${artifact_path}" template_metadata action_type "${template}" "${template}"
  assert_section_field_equals "${artifact_path}" binding_contract action_request_id "explicit AegisOps action request id required" "${template}"
  assert_section_field_equals "${artifact_path}" binding_contract approval_decision_id "explicit AegisOps approval decision id required" "${template}"
  assert_section_field_equals "${artifact_path}" binding_contract correlation_id "required in inputs and outputs" "${template}"
  assert_section_field_equals "${artifact_path}" binding_contract execution_receipt_id "required in outputs" "${template}"
  assert_section_field_equals "${artifact_path}" binding_contract normalized_receipt_ref "required in outputs" "${template}"
  assert_section_field_equals "${artifact_path}" binding_contract "${expected_scope_field}" "${expected_scope_value}" "${template}"
  assert_section_field_equals "${artifact_path}" validation_rules review_status reviewed "${template}"
  assert_section_field_equals "${artifact_path}" validation_rules action_type "${template}" "${template}"
  assert_section_field_equals "${artifact_path}" validation_rules import_eligible true "${template}"
  assert_section_field_equals "${artifact_path}" validation_rules inferred_linkage reject "${template}"
  assert_section_field_equals "${artifact_path}" validation_rules placeholder_secret_values reject "${template}"
  assert_section_field_equals "${artifact_path}" callback_boundary callback_url "<aegisops-shuffle-callback-url>" "${template}"
  assert_section_field_equals "${artifact_path}" callback_boundary callback_secret_ref "trusted secret reference required" "${template}"
  assert_section_field_equals "${artifact_path}" callback_boundary callback_payload_authority "subordinate evidence only until normalized into an AegisOps execution receipt" "${template}"

  for item in action_request_id approval_decision_id correlation_id execution_receipt_id normalized_receipt_ref reviewed_template_version; do
    assert_yaml_list_contains "${artifact_path}" required_bindings "${item}" "${template}"
  done

  for item in action_request_id approval_decision_id correlation_id reviewed_template_version requested_by callback_url callback_secret_ref; do
    assert_yaml_list_contains "${artifact_path}" required_inputs "${item}" "${template}"
  done

  for item in action_request_id approval_decision_id correlation_id execution_receipt_id normalized_receipt_ref reviewed_template_version execution_status execution_started_at execution_finished_at; do
    assert_yaml_list_contains "${artifact_path}" required_outputs "${item}" "${template}"
  done
}

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 54.5 Read/Notify template contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README.md" >&2
  exit 1
fi

contract_rendered_markdown="$(rendered_markdown_without_code_blocks "${contract_path}")"

for heading in "${required_headings[@]}"; do
  assert_file_contains "${contract_path}" "${heading}" "Phase 54.5 Read/Notify template contract heading"
done

for phrase in "${required_phrases[@]}"; do
  assert_file_contains "${contract_path}" "${phrase}" "Phase 54.5 Read/Notify template contract statement"
done

for claim in "${forbidden_claims[@]}"; do
  assert_file_contains "${contract_path}" "- ${claim}." "Phase 54.5 forbidden claim listing"
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 54.5 Read/Notify template contract claim: ${claim}" >&2
    exit 1
  fi
done

if contains_placeholder_secret_valid_claim; then
  echo "Forbidden Phase 54.5 Read/Notify template contract claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

assert_no_workstation_local_paths "${contract_path}" "${contract_path}"

enrichment_artifact="${template_dir}/enrichment_only_lookup-import-contract.yaml"
operator_artifact="${template_dir}/operator_notification-import-contract.yaml"
manual_artifact="${template_dir}/manual_escalation_request-import-contract.yaml"

if [[ ! -f "${enrichment_artifact}" ]]; then
  echo "Missing Phase 54.5 enrichment_only_lookup template artifact: ${enrichment_artifact}" >&2
  exit 1
fi
if [[ ! -f "${operator_artifact}" ]]; then
  echo "Missing Phase 54.5 operator_notification template artifact: ${operator_artifact}" >&2
  exit 1
fi
if [[ ! -f "${manual_artifact}" ]]; then
  echo "Missing Phase 54.5 manual_escalation_request template artifact: ${manual_artifact}" >&2
  exit 1
fi

verify_artifact_common \
  enrichment_only_lookup \
  "${enrichment_artifact}" \
  shuffle-enrichment-only-lookup-template-import \
  enrichment_scope \
  read-only-enrichment-lookup
assert_yaml_list_contains "${enrichment_artifact}" required_bindings lookup_subject_id enrichment_only_lookup
assert_yaml_list_contains "${enrichment_artifact}" required_bindings enrichment_scope enrichment_only_lookup
assert_yaml_list_contains "${enrichment_artifact}" required_inputs lookup_subject_id enrichment_only_lookup
assert_yaml_list_contains "${enrichment_artifact}" required_inputs enrichment_scope enrichment_only_lookup
assert_yaml_list_contains "${enrichment_artifact}" required_outputs lookup_result_ref enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" binding_contract lookup_subject_id "explicit lookup subject required" enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" mutation_boundary enrichment_only required enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" mutation_boundary read_only_lookup required enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" mutation_boundary protected_target_state_mutation forbidden enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" mutation_boundary authoritative_workflow_state_change forbidden enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" mutation_boundary account_disablement forbidden enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" mutation_boundary credential_rotation forbidden enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" mutation_boundary group_membership_change forbidden enrichment_only_lookup
assert_section_field_equals "${enrichment_artifact}" mutation_boundary ticket_or_case_closure forbidden enrichment_only_lookup
assert_exact_line "${enrichment_artifact}" "  enrichment_only: required" "Phase 54.5 enrichment_only_lookup artifact"

verify_artifact_common \
  operator_notification \
  "${operator_artifact}" \
  shuffle-operator-notification-template-import \
  notification_scope \
  operator-notification-only
assert_yaml_list_contains "${operator_artifact}" required_bindings operator_recipient_id operator_notification
assert_yaml_list_contains "${operator_artifact}" required_bindings notification_scope operator_notification
assert_yaml_list_contains "${operator_artifact}" required_inputs operator_recipient_id operator_notification
assert_yaml_list_contains "${operator_artifact}" required_inputs notification_scope operator_notification
assert_yaml_list_contains "${operator_artifact}" required_outputs notification_delivery_ref operator_notification
assert_section_field_equals "${operator_artifact}" binding_contract operator_recipient_id "explicit reviewed operator recipient required" operator_notification
assert_section_field_equals "${operator_artifact}" mutation_boundary notification_only required operator_notification
assert_section_field_equals "${operator_artifact}" mutation_boundary authoritative_workflow_state_change forbidden operator_notification
assert_section_field_equals "${operator_artifact}" mutation_boundary protected_target_state_mutation forbidden operator_notification
assert_section_field_equals "${operator_artifact}" mutation_boundary approval_decision_change forbidden operator_notification
assert_section_field_equals "${operator_artifact}" mutation_boundary reconciliation_decision_change forbidden operator_notification
assert_section_field_equals "${operator_artifact}" mutation_boundary ticket_or_case_closure forbidden operator_notification
assert_exact_line "${operator_artifact}" "  authoritative_workflow_state_change: forbidden" "Phase 54.5 operator_notification artifact"

verify_artifact_common \
  manual_escalation_request \
  "${manual_artifact}" \
  shuffle-manual-escalation-request-template-import \
  escalation_scope \
  manual-escalation-request-only
assert_yaml_list_contains "${manual_artifact}" required_bindings escalation_subject_id manual_escalation_request
assert_yaml_list_contains "${manual_artifact}" required_bindings escalation_owner_id manual_escalation_request
assert_yaml_list_contains "${manual_artifact}" required_bindings escalation_scope manual_escalation_request
assert_yaml_list_contains "${manual_artifact}" required_inputs escalation_subject_id manual_escalation_request
assert_yaml_list_contains "${manual_artifact}" required_inputs escalation_owner_id manual_escalation_request
assert_yaml_list_contains "${manual_artifact}" required_inputs escalation_scope manual_escalation_request
assert_yaml_list_contains "${manual_artifact}" required_outputs manual_escalation_request_ref manual_escalation_request
assert_section_field_equals "${manual_artifact}" binding_contract escalation_subject_id "explicit escalation subject required" manual_escalation_request
assert_section_field_equals "${manual_artifact}" binding_contract escalation_owner_id "explicit human escalation owner required" manual_escalation_request
assert_section_field_equals "${manual_artifact}" mutation_boundary manual_request_only required manual_escalation_request
assert_section_field_equals "${manual_artifact}" mutation_boundary aegisops_approval_bypass forbidden manual_escalation_request
assert_section_field_equals "${manual_artifact}" mutation_boundary automatic_escalation_approval forbidden manual_escalation_request
assert_section_field_equals "${manual_artifact}" mutation_boundary authoritative_workflow_state_change forbidden manual_escalation_request
assert_section_field_equals "${manual_artifact}" mutation_boundary protected_target_state_mutation forbidden manual_escalation_request
assert_section_field_equals "${manual_artifact}" mutation_boundary ticket_or_case_closure forbidden manual_escalation_request
assert_exact_line "${manual_artifact}" "  aegisops_approval_bypass: forbidden" "Phase 54.5 manual_escalation_request artifact"

assert_file_contains \
  "${readme_path}" \
  "[Phase 54.5 Read/Notify template contracts](docs/deployment/shuffle-read-notify-template-contracts.md)" \
  "README Phase 54.5 Read/Notify template contracts link"

echo "Phase 54.5 Read/Notify template contracts verified."
