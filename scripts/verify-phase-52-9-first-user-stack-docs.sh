#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/first-user-stack.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 52.9 First-User Stack Overview"
  "## 1. Purpose and Status"
  "## 2. Few-Command Path"
  "## 3. Troubleshooting Index"
  "## 4. Authority Boundary"
  "## 5. Validation Rules"
  "## 6. Forbidden Claims"
  "## 7. Validation"
  "## 8. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1064, #1065, #1068, #1069, #1070, #1071, #1072"
  "This overview is the operator-facing first-user path for the executable Phase 52 stack."
  "AegisOps remains pre-GA."
  "The Phase 52 path is not self-service commercial readiness and is not GA readiness."
  'The replacement boundary remains the Phase 51.1 boundary in `docs/adr/0011-phase-51-1-replacement-boundary.md`'
  "| Step | Command | Operator intent | Expected outcome | Troubleshooting link |"
  'Host preflight failures: `docs/deployment/host-preflight-contract.md`'
  'Env, secrets, and cert failures: `docs/deployment/env-secrets-certs-contract.md`'
  'Compose generation failures: `docs/deployment/compose-generator-contract.md`'
  'Demo seed separation failures: `docs/deployment/demo-seed-contract.md`'
  "First-user docs are operator guidance only."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  'This overview cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  'Run `bash scripts/verify-phase-52-9-first-user-stack-docs.sh`.'
  'Run `bash scripts/test-verify-phase-52-9-first-user-stack-docs.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1072 --config <supervisor-config-path>`.'
)

commands=(
  "init"
  "up"
  "doctor"
  "seed-demo"
  "status"
  "open"
  "logs"
  "down"
)

troubleshooting_targets=(
  "env-secrets-certs-contract.md"
  "compose-generator-contract.md"
  "host-preflight-contract.md"
  "demo-seed-contract.md"
  "clean-host-smoke-skeleton.md"
)

forbidden_claims=(
  "AegisOps is GA ready"
  "AegisOps is self-service commercial ready"
  "Phase 52 completes RC readiness"
  "Phase 52 completes GA readiness"
  "Demo data is workflow truth"
  "Demo data is production truth"
  "CLI status is workflow truth"
  "Docker status is AegisOps workflow truth"
  "Docker Compose status is AegisOps workflow truth"
  "Wazuh state is AegisOps workflow truth"
  "Shuffle state is AegisOps workflow truth"
  "AI output is AegisOps workflow truth"
  "Tickets are AegisOps workflow truth"
  "Logs are authoritative workflow truth"
  "This overview implements Wazuh product profiles"
  "This overview implements Shuffle product profiles"
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

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.9 first-user stack docs: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.9 first-user stack docs heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.9 first-user stack docs statement: ${phrase}" >&2
    exit 1
  fi
done

for index in "${!commands[@]}"; do
  step=$((index + 1))
  command="${commands[$index]}"
  if ! grep -Eq "^\\| ${step} \\| \`aegisops ${command}([[:space:]][^\`]+)?\` \\| [^|]+ \\| [^|]+ \\| \\[[^]]+\\]\\([^)]*\\.md\\)\\. \\|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.9 first-user command row: ${command}" >&2
    exit 1
  fi
done

for target in "${troubleshooting_targets[@]}"; do
  if ! grep -Fq -- "${target}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.9 troubleshooting link: ${target}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 6\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${doc_path}"
}

contains_readiness_overclaim() {
  awk '
    /^## 6\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(not|cannot|must not|fail|fails|invalid|rejected|forbidden|non-goal|no |claim|described as|promoted to)/
      if (!in_forbidden_claims && !negative_context && line ~ /(self-service commercial ready|self-service commercial readiness|ga ready|ga readiness|rc readiness|production readiness)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${doc_rendered_markdown}"
}

contains_authority_promotion() {
  awk '
    /^## 6\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(not|cannot|must not|fail|fails|invalid|rejected|forbidden|non-goal|no |claim|described as|promoted to)/
      if (!in_forbidden_claims && !negative_context && line ~ /(demo data|cli status|docker status|docker compose status|wazuh state|shuffle state|ai output|tickets|logs).*(workflow truth|production truth|authoritative workflow truth|aegisops workflow truth)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${doc_rendered_markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 52.9 first-user stack docs claim: ${claim}" >&2
    exit 1
  fi
done

if contains_readiness_overclaim; then
  echo "Forbidden Phase 52.9 first-user stack docs claim: readiness overclaim" >&2
  exit 1
fi

if contains_authority_promotion; then
  echo "Forbidden Phase 52.9 first-user stack docs claim: subordinate state promoted to workflow truth" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.9 first-user stack docs: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.9 first-user stack docs link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/first-user-stack\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.9 first-user stack docs." >&2
  exit 1
fi

echo "Phase 52.9 first-user stack docs preserve the few-command path, troubleshooting links, pre-GA status, Phase 51 citations, and authority boundaries."
