#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
repo_root="$(cd "${repo_root}" && pwd -P)"

readme_path="${repo_root}/README.md"

guides=(
  "docs/migration/phase-65-7-standalone-wazuh-migration-guide.md|standalone Wazuh migration guide|Standalone Wazuh|Wazuh remains the detection substrate.|No Wazuh manager, indexer, dashboard, alert, rule, decoder, source-health projection, or agent state becomes authoritative AegisOps truth."
  "docs/migration/phase-65-7-standalone-shuffle-migration-guide.md|standalone Shuffle migration guide|Standalone Shuffle|Standalone Shuffle remains the routine automation substrate.|No Shuffle frontend, backend, workflow, callback, API, generated config, execution log, retry state, or ticket pointer becomes authoritative AegisOps truth."
  "docs/migration/phase-65-7-manual-soc-ticket-workflow-migration-guide.md|manual SOC and ticket workflow migration guide|Manual SOC And Ticket Workflow|Manual SOC and ticket surfaces remain coordination context.|No ticket status, ticket assignment, ticket SLA state, chat decision, spreadsheet row, report export, support note, or downstream receipt becomes authoritative AegisOps truth."
)

required_headings=(
  "## 1. Prerequisites"
  "## 2. Non-Goals"
  "## 3. Authority Boundary"
  "## 4. Evidence Mapping"
  "## 5. Limitation Notes"
  "## 6. Validation Expectations"
  "## 7. Non-Claims"
)

required_common_phrases=(
  "- **Status**: Accepted as Phase 65 beta/design-partner migration guidance only."
  "- **Related Issues**: #1378, #1379, #1381"
  "The guide is documentation and planning evidence only."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, workflow, and closeout truth."
  "bash scripts/verify-phase-65-7-migration-guides.sh"
  "bash scripts/test-verify-phase-65-7-migration-guides.sh"
  "bash scripts/verify-phase-51-5-competitive-gap-matrix.sh"
  "bash scripts/verify-publishable-path-hygiene.sh"
  "node <codex-supervisor-root>/dist/index.js issue-lint 1381 --config <supervisor-config-path>"
  "This migration guide does not claim automated migration, production customer-data import"
  "RC readiness"
  "GA readiness"
  "commercial replacement readiness"
  "substitute evidence for the Phase 51.3 gate contract"
)

forbidden_lines=(
  "Source-native truth is authoritative for AegisOps records."
  "Source-native state is AegisOps truth."
  "Wazuh alerts become AegisOps alert truth."
  "Wazuh manager state is AegisOps workflow truth."
  "Shuffle workflow success becomes AegisOps execution truth."
  "Shuffle callback payload is AegisOps execution receipt truth."
  "Ticket status is AegisOps case truth."
  "Tickets are authoritative for AegisOps records."
  "AegisOps imports arbitrary production customer data."
  "AegisOps imports arbitrary source-native records."
  "AegisOps provides broad SIEM/SOAR parity."
  "AegisOps provides full enterprise SIEM parity."
  "AegisOps provides full enterprise SOAR parity."
  "Phase 65.7 proves RC readiness."
  "Phase 65.7 proves GA readiness."
  "Phase 65.7 satisfies the RC gate."
  "Phase 65.7 satisfies the GA gate."
  "AegisOps is commercially replacement ready."
  "Migration verifier output is readiness truth."
  "issue-lint output is readiness truth."
)

forbidden_patterns=(
  'phase[[:space:]]+65\.7[[:space:]]+(proves|proven|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(rc|release[- ]candidate|ga|general[- ]availability)[[:space:]]+(readiness|gate|acceptance)'
  'phase[[:space:]]+65\.7[[:space:]]+(satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(rc|release[- ]candidate|ga|general[- ]availability)[^.[:cntrl:]]*gate'
  'aegisops[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(rc|release[- ]candidate|ga|general[- ]availability|commercially[[:space:]]+replacement)[[:space:]]+ready'
  'migration[[:space:]]+guide[[:space:]]+(proves|satisfies|passes|accepts|grants|confirms)[^.[:cntrl:]]*(rc|release[- ]candidate|ga|general[- ]availability)[[:space:]]+(readiness|gate|acceptance)'
  'verifier[[:space:]]+output[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(readiness|release|gate)[[:space:]]+truth'
  'issue-lint[[:space:]]+output[[:space:]]+(is|becomes|serves[[:space:]]+as)[^.[:cntrl:]]*(readiness|release|gate)[[:space:]]+truth'
)

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -s "${path}" ]]; then
    echo "Missing Phase 65.7 ${description}: ${path#"${repo_root}/"}" >&2
    exit 1
  fi
}

visible_text() {
  perl -0pe 's/<!--.*?-->//gs' "$@"
}

require_phrase() {
  local file="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" < <(visible_text "${file}"); then
    echo "Missing Phase 65.7 ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_heading() {
  local file="$1"
  local heading="$2"
  local description="$3"

  if ! grep -Fxq -- "${heading}" < <(visible_text "${file}"); then
    echo "Missing Phase 65.7 ${description}: ${heading}" >&2
    exit 1
  fi
}

reject_forbidden_lines() {
  local file="$1"
  local forbidden

  for forbidden in "${forbidden_lines[@]}"; do
    if grep -Fiq -- "${forbidden}" < <(visible_text "${file}"); then
      echo "Forbidden Phase 65.7 migration guide claim: ${forbidden}" >&2
      exit 1
    fi
  done
}

reject_forbidden_patterns() {
  local file="$1"
  local pattern

  for pattern in "${forbidden_patterns[@]}"; do
    if grep -Eiq -- "${pattern}" < <(visible_text "${file}"); then
      echo "Forbidden Phase 65.7 migration guide claim matched: ${pattern}" >&2
      exit 1
    fi
  done
}

reject_publishable_hazards() {
  local file="$1"

  if grep -Eiq '(password|passwd|secret|token|api[_ -]?key)[[:space:]]*[:=][[:space:]]*[^[:space:]`<>]+' < <(visible_text "${file}"); then
    echo "Forbidden Phase 65.7 migration guide production secret material: ${file#"${repo_root}/"}" >&2
    exit 1
  fi
  if grep -Eiq '(includes|contains|embeds|carries)[[:space:]]+customer[-_ ]private|customer[-_ ]private[[:space:]]+(example|ticket|alert|log|chat|payload|export)|unredacted[[:space:]]+(customer|ticket|alert|log|chat|payload)[[:space:]]+(data|content|example)' < <(visible_text "${file}"); then
    echo "Forbidden Phase 65.7 migration guide customer-private data: ${file#"${repo_root}/"}" >&2
    exit 1
  fi

  local mac_user_home unix_user_home windows_user_profile_backslash windows_user_profile_slash path_token_boundary local_path_token
  mac_user_home="$(printf '/%s/' 'Users')"
  unix_user_home="$(printf '/%s/' 'home')"
  windows_user_profile_backslash="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
  windows_user_profile_slash="$(printf '[A-Za-z]:/%s/' 'Users')"
  path_token_boundary="(^|[[:space:]'\"(<{=])"
  local_path_token="(${mac_user_home}|${unix_user_home}|${windows_user_profile_backslash}|${windows_user_profile_slash})[^[:space:]'\" )>}]*"

  if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" < <(visible_text "${file}"); then
    echo "Forbidden Phase 65.7 migration guide workstation-local absolute path: ${file#"${repo_root}/"}" >&2
    exit 1
  fi
}

require_readme_link() {
  local path="$1"
  local rendered

  require_file "${readme_path}" "README"
  rendered="$(
    awk '
      /^[[:space:]]*(```|~~~)/ {
        in_fenced_block = !in_fenced_block
        next
      }
      !in_fenced_block { print }
    ' "${readme_path}" | perl -pe 's/`[^`]*`//g'
  )"

  if ! grep -Eq "\\[[^]]+\\]\\(${path}\\)" <<<"${rendered}"; then
    echo "Missing README Phase 65.7 migration guide link: ${path}" >&2
    exit 1
  fi
}

validate_guide() {
  local relative_path="$1"
  local description="$2"
  local title_fragment="$3"
  local boundary_phrase="$4"
  local non_goal_phrase="$5"
  local absolute_path="${repo_root}/${relative_path}"
  local heading phrase

  require_file "${absolute_path}" "${description}"
  require_phrase "${absolute_path}" "# Phase 65.7 ${title_fragment} Migration Guide" "${description} title"
  require_phrase "${absolute_path}" "${boundary_phrase}" "${description} authority boundary"
  require_phrase "${absolute_path}" "${non_goal_phrase}" "${description} non-goal authority exclusion"

  for heading in "${required_headings[@]}"; do
    require_heading "${absolute_path}" "${heading}" "${description} required section"
  done

  for phrase in "${required_common_phrases[@]}"; do
    require_phrase "${absolute_path}" "${phrase}" "${description} required statement"
  done

  if ! grep -Eq '^- \*\*Date\*\*: [0-9]{4}-[0-9]{2}-[0-9]{2}$' "${absolute_path}"; then
    echo "Missing or invalid Phase 65.7 ${description} date line (- **Date**: YYYY-MM-DD)." >&2
    exit 1
  fi

  reject_forbidden_lines "${absolute_path}"
  reject_forbidden_patterns "${absolute_path}"
  reject_publishable_hazards "${absolute_path}"
  require_readme_link "${relative_path}"
}

for guide_spec in "${guides[@]}"; do
  IFS="|" read -r relative_path description title_fragment boundary_phrase non_goal_phrase <<<"${guide_spec}"
  validate_guide "${relative_path}" "${description}" "${title_fragment}" "${boundary_phrase}" "${non_goal_phrase}"
done

echo "Phase 65.7 migration guides are present and preserve migration, evidence, and authority boundaries."
