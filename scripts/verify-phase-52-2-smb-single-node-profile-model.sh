#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/phase-52-2-smb-single-node-profile-model.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 52.2 SMB Single-Node Profile Model"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Mode Labels"
  "## 4. Required Profile Sections"
  "## 5. Shared Required Fields"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1064, #1065"
  'This contract defines the repo-owned `smb-single-node` profile model only. It does not implement full profile generation, compose generation, Wazuh product profiles, Shuffle product profiles, installer UX, release-candidate behavior, general-availability behavior, or runtime behavior.'
  'The approved profile identifier is `smb-single-node`.'
  "Profile config is setup input only. Profile config is not alert, case, evidence, approval, execution, reconciliation, source, workflow, gate, release, production, or closeout truth."
  "Generated config is operator setup output and readiness evidence only. Generated config is not production truth and must not become AegisOps workflow truth."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
  'This profile model cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  "| Mode label | Purpose | Production meaning |"
  '| `required` | The section is required for a valid `smb-single-node` profile contract. | Missing required sections fail validation. |'
  '| `deferred` | The section is named and bounded now, but full product-profile generation is owned by a later issue. | Deferred sections remain explicit `skipped` or `mocked` setup surfaces until reviewed implementation exists. |'
  '| `demo-only` | The section may seed reviewed demonstration fixtures for first-user evaluation. | Demo-only data is not production truth and must not satisfy production credential, source, approval, execution, or reconciliation requirements. |'
  "| Section | Mode label | Required fields | Generated config expectations | Validation rules |"
  '- `section_id`: stable section key from the required profile sections table.'
  '- `mode_label`: one of `required`, `deferred`, or `demo-only`.'
  '- `required_fields`: the section-specific input fields that must be present.'
  '- `generated_config_expectations`: the config files, placeholders, routes, or evidence references later generators may create.'
  '- `validation_rules`: fail-closed validation requirements for missing, malformed, placeholder-backed, ambiguous, inferred, or untrusted fields.'
  '- `authority_boundary`: the explicit statement that the section remains setup input or subordinate context and cannot become authoritative AegisOps truth.'
  'the profile identifier is missing or is not `smb-single-node`;'
  "any required profile section is missing, including Wazuh or Shuffle;"
  "generated config is described as production truth or workflow truth;"
  "placeholder secrets, fake secrets, sample credentials, TODO values, or inline credentials are treated as valid values;"
  'Run `bash scripts/verify-phase-52-2-smb-single-node-profile-model.sh`.'
  'Run `bash scripts/test-verify-phase-52-2-smb-single-node-profile-model.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1065 --config <supervisor-config-path>`.'
)

sections=("AegisOps" "PostgreSQL" "Proxy" "Wazuh" "Shuffle" "Demo source")
shared_fields=(
  "section_id"
  "mode_label"
  "required_fields"
  "generated_config_expectations"
  "validation_rules"
  "authority_boundary"
)

forbidden_claims=(
  "Generated config is production truth"
  "Generated config is workflow truth"
  "Profile config is authoritative for AegisOps records"
  "Wazuh profile status is AegisOps source truth"
  "Shuffle workflow success is AegisOps reconciliation truth"
  "Demo data is production truth"
  "Placeholder secrets are valid credentials"
  "Raw forwarded headers are trusted identity"
  "Phase 52.2 implements Wazuh product profiles"
  "Phase 52.2 implements Shuffle product profiles"
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
  echo "Missing Phase 52.2 SMB single-node profile model: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.2 SMB single-node profile model heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.2 SMB single-node profile model statement: ${phrase}" >&2
    exit 1
  fi
done

for field in "${shared_fields[@]}"; do
  if ! grep -Eq -- "^- \`${field}\`: [^[:space:]].+$" <<<"${doc_rendered_markdown}"; then
    echo "Missing or empty Phase 52.2 shared profile field: ${field}" >&2
    exit 1
  fi
done

for section in "${sections[@]}"; do
  if ! grep -Eq "^\| ${section} \| \`(required|deferred|demo-only)\` \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.2 profile section row: ${section}" >&2
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
    echo "Forbidden Phase 52.2 SMB single-node profile model claim: ${claim}" >&2
    exit 1
  fi
done

if grep -Eiq "^placeholder secrets? (are|is|count as|counts as|may be|can be|remain|stays) (valid|trusted|accepted|production)" <<<"${doc_rendered_markdown}"; then
  echo "Forbidden Phase 52.2 SMB single-node profile model claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
unix_absolute_path="/${path_token_chars}+"
windows_drive_path="[A-Za-z]:[\\\\/]${path_token_chars}*"
local_path_token="(${unix_absolute_path}|${windows_drive_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.2 SMB single-node profile model: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.2 SMB single-node profile model link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/phase-52-2-smb-single-node-profile-model\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.2 SMB single-node profile model." >&2
  exit 1
fi

echo "Phase 52.2 SMB single-node profile model is present and preserves required section coverage, mode labels, validation rules, and authority boundaries."
