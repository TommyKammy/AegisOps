#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-52-1-cli-command-contract.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 52.1 CLI Command Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Shared Output Contract"
  "## 4. Command Contract"
  "## 5. Mocked and Skipped States"
  "## 6. Failure and Retry Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1064"
  "This contract defines the first-user CLI command contract only. It does not implement installer behavior, Wazuh profile generation, Shuffle profile generation, first-user UI flows, AI operations, SIEM breadth, SOAR breadth, packaging, release-candidate behavior, or general-availability behavior."
  'The approved command names are `init`, `up`, `doctor`, `seed-demo`, `status`, `open`, `logs`, and `down`.'
  "CLI output is operator guidance and readiness evidence only. CLI output is not alert, case, evidence, approval, execution, reconciliation, gate, release, or production truth."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
  'This command contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  'Every command must emit structured operator-facing output with:'
  '- `command`: the invoked command name.'
  '- `result`: one of `ok`, `skipped`, `mocked`, `degraded`, or `failed`.'
  '- `summary`: a short human-readable operator summary.'
  '- `next_actions`: zero or more safe follow-up commands or prerequisite actions.'
  '- `evidence`: zero or more readiness evidence references, never authoritative workflow truth.'
  "| Command | Purpose | Required inputs | Expected outputs | Failure behavior | Safe retry guidance |"
  'Before reviewed Wazuh and Shuffle product profiles exist, commands must report unavailable substrate work as explicit `skipped` or `mocked` states.'
  '`skipped` and `mocked` states must not be reported as false success.'
  "Wazuh alert status is not AegisOps workflow truth. Shuffle workflow success is not AegisOps workflow truth. Demo data is not production truth. Browser state, UI cache, logs, tickets, downstream receipts, and CLI summaries are not AegisOps workflow truth."
  "All commands fail closed when provenance, profile binding, runtime scope, auth context, snapshot consistency, or authority-boundary signals are missing, malformed, stale, mixed, or only partially trusted."
  "Safe retry means a command can be rerun after the stated prerequisite is repaired without destructive cleanup, duplicate authoritative writes, hidden state promotion, or widened product scope."
  "Failed, rejected, skipped, mocked, and degraded paths must leave durable state clean."
  "- CLI status is workflow truth."
  "- Phase 52 completes Wazuh profiles."
  "- Phase 52 completes Shuffle profiles."
  'Run `bash scripts/verify-phase-52-1-cli-command-contract.sh`.'
  'Run `bash scripts/test-verify-phase-52-1-cli-command-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1064 --config <supervisor-config-path>`.'
)

commands=(init up doctor seed-demo status open logs down)
shared_output_fields=(command result summary next_actions evidence)

forbidden_claims=(
  "CLI status is workflow truth"
  "CLI output is authoritative for AegisOps records"
  "Phase 52 completes Wazuh profiles"
  "Phase 52 completes Shuffle profiles"
  "Wazuh alert status is AegisOps workflow truth"
  "Shuffle workflow success is AegisOps workflow truth"
  "Demo data is production truth"
  "Browser state is workflow truth"
  "Logs are authoritative workflow truth"
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 52.1 CLI command contract: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    !in_fenced_block { print }
  ' "${doc_path}" | perl -0pe 's/<!--.*?-->//gs'
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.1 CLI command contract heading: ${heading}" >&2
    exit 1
  fi
done

for field in "${shared_output_fields[@]}"; do
  if ! grep -Eq -- "^- \`${field}\`: [^[:space:]].+$" <<<"${doc_rendered_markdown}"; then
    echo "Missing or empty Phase 52.1 shared output field: ${field}" >&2
    exit 1
  fi
done

if ! grep -Fxq -- '- `result`: one of `ok`, `skipped`, `mocked`, `degraded`, or `failed`.' <<<"${doc_rendered_markdown}"; then
  echo "Invalid Phase 52.1 shared output result field: expected one of ok, skipped, mocked, degraded, or failed." >&2
  exit 1
fi

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.1 CLI command contract statement: ${phrase}" >&2
    exit 1
  fi
done

for command in "${commands[@]}"; do
  if ! grep -Eq "^\| \`${command}\` \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.1 CLI command row: ${command}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index($0, claim) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${doc_path}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 52.1 CLI command contract claim: ${claim}" >&2
    exit 1
  fi
done

mac_user_home="$(printf '/%s/' 'Users')"
unix_user_home="$(printf '/%s/' 'home')"
windows_user_profile_backslash="$(printf '[A-Za-z]:\\\\%s\\\\' 'Users')"
windows_user_profile_slash="$(printf '[A-Za-z]:/%s/' 'Users')"
path_token_boundary="(^|[[:space:]'\"(<{=])"
local_path_token="(${mac_user_home}|${unix_user_home}|${windows_user_profile_backslash}|${windows_user_profile_slash})[^[:space:]'\" )>}]*"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.1 CLI command contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.1 CLI command contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    !in_fenced_block { print }
  ' "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

readme_rendered_markdown="$(
  perl -0pe 's/<!--.*?-->//gs' <<<"${readme_rendered_markdown}"
)"

if ! grep -Eq '\[[^]]+\]\(docs/phase-52-1-cli-command-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.1 CLI command contract." >&2
  exit 1
fi

echo "Phase 52.1 CLI command contract is present and preserves command coverage, skipped or mocked state handling, and authority boundaries."
