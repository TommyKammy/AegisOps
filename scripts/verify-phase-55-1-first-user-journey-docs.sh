#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
journey_path="${repo_root}/docs/getting-started/first-user-journey.md"
minutes_path="${repo_root}/docs/getting-started/first-30-minutes.md"
readme_path="${repo_root}/README.md"

required_docs=(
  "${journey_path}"
  "${minutes_path}"
)

required_headings=(
  "${journey_path}|# Phase 55.1 First-User Journey"
  "${journey_path}|## 1. Few-Command Entry Path"
  "${journey_path}|## 2. Workflow-First Journey"
  "${journey_path}|## 3. Demo Guidance Versus Production Truth"
  "${journey_path}|## 4. Scope Boundaries"
  "${journey_path}|## 5. Validation"
  "${minutes_path}|# Phase 55.1 First 30 Minutes"
  "${minutes_path}|## 1. Minute-by-Minute Path"
  "${minutes_path}|## 2. What To Confirm"
  "${minutes_path}|## 3. Authority Boundary"
  "${minutes_path}|## 4. What This Does Not Prove"
  "${minutes_path}|## 5. Validation"
)

required_phrases=(
  "${journey_path}|This guide is workflow-first operator guidance for a new AegisOps user."
  "${journey_path}|It starts from the Phase 52 few-command stack path and shows the first guided SecOps flow without requiring the full architecture corpus."
  "${journey_path}|First-user docs and first-30-minutes guidance are operator guidance only."
  "${journey_path}|AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  "${journey_path}|Demo records, UI state, browser state, Wazuh state, Shuffle state, AI output, tickets, verifier output, and issue-lint output remain subordinate context."
  "${journey_path}|Run \`bash scripts/verify-phase-55-1-first-user-journey-docs.sh\`."
  "${journey_path}|Run \`bash scripts/test-verify-phase-55-1-first-user-journey-docs.sh\`."
  "${journey_path}|Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "${journey_path}|Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1176 --config <supervisor-config-path>\`."
  "${minutes_path}|This guide keeps the first session focused on workflow orientation, not architecture study."
  "${minutes_path}|Use demo-only records only to rehearse the path; they are not production truth."
  "${minutes_path}|Stop and treat the gap as a follow-up if a required control-plane record, receipt, reconciliation result, or export artifact is missing."
  "${minutes_path}|Run \`bash scripts/verify-phase-55-1-first-user-journey-docs.sh\`."
)

commands=(
  "init"
  "up"
  "doctor"
  "seed-demo"
  "status"
  "open"
)

workflow_sequence=(
  "Stack health"
  "Seeded queue"
  "Sample alert"
  "Case"
  "Evidence"
  "AI summary"
  "Action review"
  "Receipt"
  "Reconciliation"
  "Report export"
)

forbidden_claim_patterns=(
  "demo (records|data) (are|is) production truth"
  "Phase 56 (is )?(complete|completed|done)"
  "Phase 58 (is )?(complete|completed|done)"
  "Phase 62 (is )?(complete|completed|done)"
  "AegisOps (is )?Beta"
  "AegisOps (is )?RC"
  "AegisOps (is )?GA"
  "AegisOps (is )?commercially ready"
  "commercial readiness (is )?(complete|completed|done)"
  "first-login checklist UI (is )?(implemented|complete|completed|done)"
  "demo seed implementation (is )?(implemented|complete|completed|done)"
  "report export implementation (is )?(implemented|complete|completed|done)"
  "daily SOC workbench (is )?(implemented|complete|completed|done)"
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

for doc_path in "${required_docs[@]}"; do
  if [[ ! -f "${doc_path}" ]]; then
    echo "Missing Phase 55.1 first-user journey docs: ${doc_path}" >&2
    exit 1
  fi
done

journey_rendered_markdown="$(rendered_markdown_without_code_blocks "${journey_path}")"
minutes_rendered_markdown="$(rendered_markdown_without_code_blocks "${minutes_path}")"
combined_rendered_markdown="${journey_rendered_markdown}"$'\n'"${minutes_rendered_markdown}"

for entry in "${required_headings[@]}"; do
  doc_path="${entry%%|*}"
  heading="${entry#*|}"
  if ! rendered_markdown_without_code_blocks "${doc_path}" | grep -Fxq -- "${heading}"; then
    echo "Missing Phase 55.1 docs heading in ${doc_path#${repo_root}/}: ${heading}" >&2
    exit 1
  fi
done

for entry in "${required_phrases[@]}"; do
  doc_path="${entry%%|*}"
  phrase="${entry#*|}"
  if ! rendered_markdown_without_code_blocks "${doc_path}" | grep -Fq -- "${phrase}"; then
    echo "Missing Phase 55.1 docs statement in ${doc_path#${repo_root}/}: ${phrase}" >&2
    exit 1
  fi
done

for index in "${!commands[@]}"; do
  step=$((index + 1))
  command="${commands[$index]}"
  if ! grep -Eq "^\\| ${step} \\| \`aegisops ${command}([[:space:]][^\`]+)?\` \\| [^|]+ \\| [^|]+ \\|$" <<<"${journey_rendered_markdown}"; then
    echo "Missing complete Phase 55.1 few-command row: ${command}" >&2
    exit 1
  fi
done

workflow_section="$(
  awk '
    /^## 2\. Workflow-First Journey$/ { in_section = 1; next }
    /^## [0-9]+\./ && in_section { exit }
    in_section { print }
  ' <<<"${journey_rendered_markdown}"
)"

previous_line=0
for token in "${workflow_sequence[@]}"; do
  current_line="$(
    grep -En "^[[:space:]]*[0-9]+\\.[[:space:]]+\\*\\*${token}\\*\\*[[:space:]]*-" <<<"${workflow_section}" |
      awk -F: -v previous="${previous_line}" '$1 > previous { print $1; exit }' ||
      true
  )"
  if [[ -z "${current_line}" ]]; then
    echo "Missing or out-of-order Phase 55.1 workflow sequence term: ${token}" >&2
    exit 1
  fi
  previous_line="${current_line}"
done

contains_forbidden_claim() {
  local pattern="$1"

  awk -v pattern="${pattern}" '
    BEGIN {
      pattern_lower = tolower(pattern)
      bounded_pattern = "(^|[^[:alnum:]_-])(" pattern_lower ")([^[:alnum:]_-]|$)"
    }

    {
      line = tolower($0)
      remainder = line
      base = 0

      while (match(remainder, bounded_pattern)) {
        match_start = base + RSTART
        match_end = match_start + RLENGTH - 1

        prefix_context = substr(line, 1, match_start - 1)
        suffix_context = substr(line, match_end + 1, 96)
        gsub(/^.*[.;!?]/, "", prefix_context)
        gsub(/[.;!?].*$/, "", suffix_context)

        negative_context = \
          prefix_context ~ /(^|[[:space:][:punct:]])((do|does|must)[[:space:]]+not|never|cannot)[[:space:]]+(claim|state|say|treat|promote|present|describe)([[:space:][:punct:]]+[[:alnum:]_-]+){0,4}[[:space:][:punct:]]*$/ || \
          prefix_context ~ /(^|[[:space:][:punct:]])(forbidden|reject|rejected|outside|out[[:space:]]+of[[:space:]]+scope)[[:space:][:punct:]]+(claim|statement|wording|overclaim|docs?)[[:space:][:punct:]]*$/ || \
          prefix_context ~ /(^|[[:space:][:punct:]])(must|should)[[:space:]]+fail[[:space:]]+(when|if)[^.;!?]*$/ || \
          suffix_context ~ /^[[:space:][:punct:]]+(is[[:space:]]+)?(a[[:space:]]+)?(forbidden|invalid|rejected|out[[:space:]]+of[[:space:]]+scope)[[:space:]]+(claim|statement|overclaim)/

        if (!negative_context) {
          found = 1
        }

        next_start = RSTART + RLENGTH
        if (next_start <= RSTART) {
          next_start = RSTART + 1
        }
        base += next_start - 1
        remainder = substr(remainder, next_start)
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${combined_rendered_markdown}"
}

for pattern in "${forbidden_claim_patterns[@]}"; do
  if contains_forbidden_claim "${pattern}"; then
    echo "Forbidden Phase 55.1 first-user journey docs claim: ${pattern}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

for doc_path in "${required_docs[@]}"; do
  if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
    echo "Forbidden Phase 55.1 docs: workstation-local absolute path detected in ${doc_path#${repo_root}/}" >&2
    exit 1
  fi
done

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 55.1 first-user docs link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/getting-started/first-user-journey\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 55.1 first-user journey docs." >&2
  exit 1
fi

if ! grep -Eq '\[[^]]+\]\(docs/getting-started/first-30-minutes\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 55.1 first-30-minutes docs." >&2
  exit 1
fi

echo "Phase 55.1 first-user journey docs preserve the few-command path, workflow sequence, demo boundary, and scope guardrails."
