#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/compose-generator-contract.md"
snapshot_path="${repo_root}/docs/deployment/fixtures/compose-generator/smb-single-node.compose.snapshot.yml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 52.4 Compose Generator Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Generated Compose Shape"
  "## 4. Snapshot Expectations"
  "## 5. Validation Rules"
  "## 6. Forbidden Claims"
  "## 7. Validation"
  "## 8. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1065, #1066, #1067"
  "This contract defines generated Docker Compose shape and snapshot-test expectations for the executable first-user stack only. It does not implement the installer, compose generator runtime, Wazuh product profile, Shuffle product profile, production hardening, release-candidate behavior, general-availability behavior, or runtime behavior."
  'The compose generator contract gives later setup issues one stable output shape for the `smb-single-node` first-user stack.'
  "Manual editing of generated Compose output is not the product path."
  "Generated compose state is setup/runtime posture evidence only. Generated compose state is not alert, case, evidence, approval, execution, reconciliation, source, workflow, gate, release, production, or closeout truth."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  'This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  "| Service | Mode label | Generated shape | Boundary requirement |"
  'The required snapshot fixture is `docs/deployment/fixtures/compose-generator/smb-single-node.compose.snapshot.yml`.'
  'the proxy service is the only service with host-published `ports`;'
  "AegisOps, PostgreSQL, Wazuh, Shuffle, and demo source do not publish direct host ports;"
  "the proxy boundary is missing or is not the only approved ingress;"
  "manual Compose editing is described as the product path;"
  'Run `bash scripts/verify-phase-52-4-compose-generator-contract.sh`.'
  'Run `bash scripts/test-verify-phase-52-4-compose-generator-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1067 --config <supervisor-config-path>`.'
)

services=(
  "AegisOps|required"
  "PostgreSQL|required"
  "Proxy|required"
  "Wazuh|deferred"
  "Shuffle|deferred"
  "Demo source|demo-only"
)

snapshot_services=(
  "aegisops"
  "postgres"
  "proxy"
  "wazuh"
  "shuffle"
  "demo-source"
)

forbidden_claims=(
  "Compose state is AegisOps workflow truth"
  "Generated compose state is production truth"
  "Generated compose state is release truth"
  "Generated compose state is closeout truth"
  "Manual Compose editing is the product path"
  "Direct backend exposure is approved"
  "Proxy boundary is optional"
  "Placeholder secrets are valid credentials"
  "Raw forwarded headers are trusted identity"
  "Phase 52.4 implements the compose generator runtime"
  "Phase 52.4 implements Wazuh product profiles"
  "Phase 52.4 implements Shuffle product profiles"
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
  echo "Missing Phase 52.4 compose generator contract: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.4 compose generator contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.4 compose generator contract statement: ${phrase}" >&2
    exit 1
  fi
done

for service_entry in "${services[@]}"; do
  service="${service_entry%%|*}"
  mode="${service_entry##*|}"
  if ! grep -Eq "^\| ${service} \| \`${mode}\` \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.4 compose service row: ${service}" >&2
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

contains_placeholder_secret_valid_claim() {
  awk '
    /^## 6\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(must fail|fail closed|fails validation|invalid|must not|cannot|not satisfy|incompatible|not inline|not the product path)/
      if (!in_forbidden_claims && !negative_context && line ~ /(^|[^[:alnum:]_])placeholder secrets?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|production)([^[:alnum:]_]|$)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${doc_rendered_markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 52.4 compose generator contract claim: ${claim}" >&2
    exit 1
  fi
done

if contains_placeholder_secret_valid_claim; then
  echo "Forbidden Phase 52.4 compose generator contract claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.4 compose generator contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${snapshot_path}" ]]; then
  echo "Missing Phase 52.4 generated compose snapshot fixture: ${snapshot_path}" >&2
  exit 1
fi

for service in "${snapshot_services[@]}"; do
  if ! awk -v service="${service}" '
    /^services:[[:space:]]*$/ { in_services = 1; next }
    /^[A-Za-z0-9_-]+:[[:space:]]*$/ && in_services { in_services = 0 }
    in_services && $0 ~ "^  " service ":[[:space:]]*$" { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${snapshot_path}"; then
    echo "Missing generated compose snapshot service: ${service}" >&2
    exit 1
  fi
done

for required in \
  "name: aegisops-smb-single-node" \
  "x-aegisops-authority-boundary: generated-compose-output-is-setup-runtime-posture-evidence-only" \
  "postgres-data:" \
  "postgres-backup:" \
  "internal: true"; do
  if ! grep -Fq -- "${required}" "${snapshot_path}"; then
    echo "Missing generated compose snapshot statement: ${required}" >&2
    exit 1
  fi
done

non_proxy_ports="$(
  awk '
    /^services:[[:space:]]*$/ { in_services = 1; next }
    /^[A-Za-z0-9_-]+:[[:space:]]*$/ && in_services { in_services = 0 }
    !in_services { next }
    /^  [A-Za-z0-9_-]+:[[:space:]]*$/ {
      service = $1
      sub(/:$/, "", service)
      next
    }
    /^[[:space:]]{4}ports:[[:space:]]*$/ && service != "" && service != "proxy" {
      print service
    }
  ' "${snapshot_path}" | sort -u
)"

if [[ -n "${non_proxy_ports}" ]]; then
  while IFS= read -r service; do
    [[ -z "${service}" ]] && continue
    echo "Generated compose snapshot must not publish host ports for service: ${service}" >&2
  done <<<"${non_proxy_ports}"
  exit 1
fi

if ! awk '
  /^  proxy:[[:space:]]*$/ { in_proxy = 1; next }
  /^  [A-Za-z0-9_-]+:[[:space:]]*$/ && in_proxy { in_proxy = 0 }
  in_proxy && /^[[:space:]]{4}ports:[[:space:]]*$/ { found = 1 }
  END { exit(found ? 0 : 1) }
' "${snapshot_path}"; then
  echo "Generated compose snapshot proxy service must publish the reviewed ingress ports." >&2
  exit 1
fi

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${snapshot_path}"; then
  echo "Forbidden Phase 52.4 generated compose snapshot: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.4 compose generator contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/compose-generator-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.4 compose generator contract." >&2
  exit 1
fi

echo "Phase 52.4 compose generator contract is present and preserves service shape, proxy-only ingress, snapshot expectations, and authority boundaries."
