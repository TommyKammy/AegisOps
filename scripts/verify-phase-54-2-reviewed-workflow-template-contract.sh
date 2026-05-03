#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/reviewed-workflow-template-contract.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 54.2 Shuffle Reviewed Workflow Template Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Reviewed Template Metadata"
  "## 4. Required Field Contract"
  "## 5. Product Mainline Entry Rules"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1154, #1155, #1156"
  "This contract defines the repo-owned reviewed Shuffle workflow template contract for the Phase 54 \`smb-single-node\` product profile."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/shuffle/reviewed-workflow-template-contract.yaml\`."
  "Shuffle is a subordinate routine automation substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "| Field | Required | Expected value or binding | Authority boundary |"
  "| Contract area | Required fields | Failure rule |"
  "| Inputs | \`correlation_id\`, \`action_request_id\`, \`approval_decision_id\`, \`template_version_id\`, \`delegation_subject_id\`, \`requested_by\`, \`callback_url\`, \`callback_secret_ref\` | Missing or blank input fields reject the template. |"
  "| Outputs | \`correlation_id\`, \`action_request_id\`, \`approval_decision_id\`, \`execution_receipt_id\`, \`template_version_id\`, \`execution_status\`, \`execution_started_at\`, \`execution_finished_at\`, \`normalized_receipt_ref\` | Missing or blank output fields reject the template. |"
  "| Correlation | \`correlation_id\` in both inputs and outputs | Missing, blank, or one-sided correlation rejects the template. |"
  "| Action request | \`action_request_id\` in both inputs and outputs | Missing, blank, or inferred action-request linkage rejects the template. |"
  "| Approval decision | \`approval_decision_id\` in both inputs and outputs | Missing, blank, or inferred approval linkage rejects the template. |"
  "| Execution receipt | \`execution_receipt_id\` and \`normalized_receipt_ref\` in outputs | Missing or blank receipt fields reject the template. |"
  "| Version | \`template_version_id\` in metadata, inputs, and outputs | Missing or mismatched version linkage rejects the template. |"
  "| Review | \`owner\` and \`review_status: reviewed\` in metadata | Missing owner or non-reviewed status rejects the template. |"
  "Run \`bash scripts/verify-phase-54-2-reviewed-workflow-template-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-54-2-reviewed-workflow-template-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1156 --config <supervisor-config-path>\`."
)

required_artifact_lines=(
  "contract_id: shuffle-reviewed-workflow-template"
  "product_profile: shuffle"
  "profile_id: smb-single-node"
  "contract_version: 2026-05-03"
  "status: accepted-contract"
  "  template_id: reviewed-shuffle-template-contract"
  "  template_version_id: reviewed-shuffle-template-v1"
  "  owner: AegisOps maintainers"
  "  review_status: reviewed"
  "  product_mainline_eligible: true"
  "  template_custody: repo-owned reviewed template catalog only"
  "  correlation_id: required in inputs and outputs"
  "  action_request_id: required in inputs and outputs"
  "  approval_decision_id: required in inputs and outputs"
  "  execution_receipt_id: required in outputs"
  "  normalized_receipt_ref: required in outputs"
  "  template_version_id: required in metadata, inputs, and outputs"
  "  review_status: reviewed"
  "  unreviewed_product_mainline: reject"
  "  missing_correlation: reject"
  "  missing_action_request: reject"
  "  missing_approval_decision: reject"
  "  missing_execution_receipt: reject"
  "  missing_owner: reject"
  "  inferred_linkage: reject"
  "  placeholder_secret_values: reject"
  "  callback_url: <aegisops-shuffle-callback-url>"
  "  callback_secret_ref: trusted secret reference required"
  "  callback_payload_authority: subordinate evidence only until normalized into an AegisOps execution receipt"
)

required_inputs=(
  correlation_id
  action_request_id
  approval_decision_id
  template_version_id
  delegation_subject_id
  requested_by
  callback_url
  callback_secret_ref
)

required_outputs=(
  correlation_id
  action_request_id
  approval_decision_id
  execution_receipt_id
  template_version_id
  execution_status
  execution_started_at
  execution_finished_at
  normalized_receipt_ref
)

forbidden_claims=(
  "Shuffle workflow success is AegisOps reconciliation truth"
  "Shuffle callback payload is AegisOps execution receipt truth"
  "Shuffle workflow status closes AegisOps cases"
  "Shuffle execution logs are AegisOps audit truth"
  "Unreviewed Shuffle templates may enter the product mainline"
  "Draft Shuffle templates may enter the product mainline"
  "Raw forwarded headers are trusted callback identity"
  "Template names imply approval decision binding"
  "Template paths imply action request binding"
  "Phase 54.2 implements template imports"
  "Phase 54.2 implements delegation binding"
  "Phase 54.2 implements receipt normalization"
  "Phase 54.2 implements broad SOAR catalog expansion"
  "Phase 54.2 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement"
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
    echo "Mismatched Phase 54.2 reviewed workflow template artifact field ${field}: expected [${expected}] actual [${actual}]" >&2
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
    echo "Mismatched Phase 54.2 reviewed workflow template artifact field ${section}.${field}: expected [${expected}] actual [${actual}]" >&2
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
    echo "Missing Phase 54.2 reviewed workflow template artifact ${list_name} item: ${item}" >&2
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
  echo "Missing Phase 54.2 reviewed workflow template contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 54.2 reviewed workflow template artifact: ${artifact_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 54.2 reviewed workflow template contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 54.2 reviewed workflow template contract statement: ${phrase}" >&2
    exit 1
  fi
done

for line in "${required_artifact_lines[@]}"; do
  if ! grep -Fxq -- "${line}" "${artifact_path}"; then
    echo "Missing exact Phase 54.2 reviewed workflow template artifact line: ${line}" >&2
    exit 1
  fi
done

assert_top_field_equals "contract_id" "shuffle-reviewed-workflow-template"
assert_top_field_equals "product_profile" "shuffle"
assert_top_field_equals "profile_id" "smb-single-node"
assert_top_field_equals "contract_version" "2026-05-03"
assert_top_field_equals "status" "accepted-contract"
assert_section_field_equals "template_metadata" "template_id" "reviewed-shuffle-template-contract"
assert_section_field_equals "template_metadata" "template_version_id" "reviewed-shuffle-template-v1"
assert_section_field_equals "template_metadata" "owner" "AegisOps maintainers"
assert_section_field_equals "template_metadata" "review_status" "reviewed"
assert_section_field_equals "template_metadata" "product_mainline_eligible" "true"
assert_section_field_equals "validation_rules" "review_status" "reviewed"
assert_section_field_equals "validation_rules" "unreviewed_product_mainline" "reject"
assert_section_field_equals "validation_rules" "missing_correlation" "reject"
assert_section_field_equals "validation_rules" "missing_action_request" "reject"
assert_section_field_equals "validation_rules" "missing_approval_decision" "reject"
assert_section_field_equals "validation_rules" "missing_execution_receipt" "reject"
assert_section_field_equals "validation_rules" "missing_owner" "reject"
assert_section_field_equals "validation_rules" "inferred_linkage" "reject"
assert_section_field_equals "validation_rules" "placeholder_secret_values" "reject"
assert_section_field_equals "callback_boundary" "callback_url" "<aegisops-shuffle-callback-url>"
assert_section_field_equals "callback_boundary" "callback_secret_ref" "trusted secret reference required"

for input_field in "${required_inputs[@]}"; do
  assert_list_contains "required_inputs" "${input_field}"
done

for output_field in "${required_outputs[@]}"; do
  assert_list_contains "required_outputs" "${output_field}"
done

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 54.2 reviewed workflow template contract claim: ${claim}" >&2
    exit 1
  fi
done

if contains_placeholder_secret_valid_claim; then
  echo "Forbidden Phase 54.2 reviewed workflow template contract claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

if grep -Eq 'review_status:[[:space:]]*(unreviewed|draft|sample|placeholder|TODO|todo|deprecated)' "${artifact_path}"; then
  echo "Forbidden Phase 54.2 reviewed workflow template artifact: unreviewed template status enters product mainline" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 54.2 reviewed workflow template contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 54.2 reviewed workflow template contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/shuffle-reviewed-workflow-template-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 54.2 reviewed workflow template contract." >&2
  exit 1
fi

echo "Phase 54.2 reviewed workflow template contract is present and preserves required correlation, action request, approval decision, execution receipt, version, owner, review status, and authority boundaries."
