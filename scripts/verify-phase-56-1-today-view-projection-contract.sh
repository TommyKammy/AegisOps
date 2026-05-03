#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/today-view-backend-projection-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/today-view-projection.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 56.1 Today View Backend Projection Contract"
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
  "- **Date**: 2026-05-04"
  "- **Related Issues**: #1190, #1191"
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/today-view-projection.yaml\`."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, recommendation, approval, action request, receipt, reconciliation, audit, limitation, gate, release, and closeout truth."
  "Stale or cached Today projection output cannot satisfy authority, approval, execution, or reconciliation truth."
  "AI-suggested focus is advisory-only"
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`"
  "Run \`python3 -m unittest control-plane.tests.test_phase56_1_today_projection_contract\`."
  "Run \`bash scripts/verify-phase-56-1-today-view-projection-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-56-1-today-view-projection-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1190 --config <supervisor-config-path>\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1191 --config <supervisor-config-path>\`."
)

required_artifact_terms=(
  "profile_id: smb-single-node"
  "today_view_projection_contract_version: 2026-05-04"
  "status: accepted-contract"
  "projection_owner: aegisops-control-plane"
  "workflow_truth_source: aegisops-record-chain-only"
  "authority_mutation_allowed: false"
  "cached_projection_authority_allowed: false"
  "ai_focus_authority_allowed: false"
  "subordinate_surfaces_authority_allowed: false"
  "lanes:"
  "states:"
  "projection_rules:"
  "negative_validation_tests:"
)

required_lanes=(
  priority
  stale_work
  pending_approvals
  degraded_sources
  reconciliation_mismatches
  evidence_gaps
  ai_suggested_focus
)

required_states=(
  empty
  normal
  degraded
  stale
  mismatch
  evidence_gap
)

required_rules=(
  all-required-lanes-present
  empty-state-visible
  normal-state-authoritative-anchors
  degraded-subordinate-context-visible
  stale-projection-rejected-as-truth
  mismatch-preserved
  evidence-gap-preserved
  ai-focus-advisory-only
  no-authority-mutation
)

required_negative_tests=(
  missing-required-lane
  missing-empty-state
  missing-normal-state
  missing-degraded-state
  missing-stale-state
  missing-mismatch-state
  missing-evidence-gap-state
  stale-projection-as-current-truth
  ai-focus-as-authority
  wazuh-shuffle-ticket-closeout-shortcut
  today-summary-as-approval-execution-reconciliation-truth
)

forbidden_claims=(
  "Today projection is AegisOps approval truth"
  "Today projection is AegisOps execution truth"
  "Today projection is AegisOps reconciliation truth"
  "Today projection closes AegisOps cases"
  "Stale Today projection output is current AegisOps truth"
  "Cached Today view output satisfies approval truth"
  "AI-suggested focus approves actions"
  "AI-suggested focus executes actions"
  "AI-suggested focus reconciles actions"
  "Wazuh state closes Today work"
  "Shuffle state closes Today work"
  "Ticket state closes Today work"
  "Health summary state is AegisOps workflow truth"
  "Report output is AegisOps closeout truth"
  "Phase 56.1 implements the Today UI"
  "Phase 56.1 claims Beta, RC, GA, or commercial readiness"
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
    echo "Missing Phase 56.1 Today projection ${label}: ${item}" >&2
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
  echo "Missing Phase 56.1 Today projection contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 56.1 Today projection artifact: ${artifact_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(rendered_markdown_without_code_blocks "${contract_path}")"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 56.1 Today projection contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 56.1 Today projection contract statement: ${phrase}" >&2
    exit 1
  fi
done

for term in "${required_artifact_terms[@]}"; do
  if ! has_uncommented_substring "${term}" "${artifact_path}"; then
    echo "Missing Phase 56.1 Today projection artifact term: ${term}" >&2
    exit 1
  fi
done

for lane in "${required_lanes[@]}"; do
  require_top_level_list_item "${artifact_path}" "lanes" "${lane}" "lane"
  if ! grep -Fq -- "| ${lane} |" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 56.1 Today projection contract lane row: ${lane}" >&2
    exit 1
  fi
done

for state in "${required_states[@]}"; do
  require_top_level_list_item "${artifact_path}" "states" "${state}" "state"
  if ! grep -Fq -- "| ${state} |" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 56.1 Today projection contract state row: ${state}" >&2
    exit 1
  fi
done

for rule in "${required_rules[@]}"; do
  require_top_level_list_item "${artifact_path}" "projection_rules" "${rule}" "rule"
  if ! grep -Fq -- "| ${rule} |" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 56.1 Today projection contract rule row: ${rule}" >&2
    exit 1
  fi
done

for negative_test in "${required_negative_tests[@]}"; do
  require_top_level_list_item "${artifact_path}" "negative_validation_tests" "${negative_test}" "negative validation test"
done

for claim in "${forbidden_claims[@]}"; do
  if ! contains_forbidden_claim_in_section "${claim}"; then
    echo "Missing Phase 56.1 Today projection forbidden claim: ${claim}" >&2
    exit 1
  fi

  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 56.1 Today projection claim: ${claim}" >&2
    exit 1
  fi
done

for secret_scan_path in "${contract_path}" "${artifact_path}"; do
  if contains_secret_looking_value "${secret_scan_path}"; then
    echo "Forbidden Phase 56.1 Today projection artifact: committed secret-looking value detected in ${secret_scan_path}" >&2
    exit 1
  fi
done

mac_user_home_pattern="/""Users/"
posix_user_home_pattern="/""home/[^[:space:]/]+"
windows_user_home_pattern='C:\\''Users\\'
if grep -REq "${mac_user_home_pattern}|${posix_user_home_pattern}|${windows_user_home_pattern}" "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 56.1 Today projection artifact: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 56.1 Today projection link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(rendered_markdown_without_code_blocks "${readme_path}")"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/today-view-backend-projection-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 56.1 Today view backend projection contract." >&2
  exit 1
fi

echo "Phase 56.1 Today view backend projection contract is present and rejects missing lanes, stale projection truth, AI authority, subordinate closeout shortcuts, and workstation-local paths."
