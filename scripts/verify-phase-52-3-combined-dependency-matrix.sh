#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/combined-dependency-matrix.md"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 52.3 Combined Dependency Matrix"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Host Footprint"
  "## 4. Dependency Matrix"
  "## 5. Host Preflight Follow-Up Contract"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1065, #1066"
  "This matrix defines dependency documentation and verifier expectations for the executable first-user stack only. It does not implement an installer, compose generation, Wazuh product-profile runtime behavior, Shuffle product-profile runtime behavior, a full host preflight engine, release-candidate behavior, general-availability behavior, or runtime behavior."
  "The matrix covers the first-user executable stack shape: AegisOps, Wazuh, Shuffle, PostgreSQL, proxy, Docker, and Docker Compose."
  "Dependency expectations are setup readiness evidence only. Docker, Docker Compose, Wazuh, Shuffle, PostgreSQL, proxy, port, certificate, volume, host sizing, or version state is not alert, case, evidence, approval, execution, reconciliation, workflow, gate, release, production, or closeout truth."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  'This matrix cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  "| Host tier | CPU | RAM | Disk | Notes |"
  "| Minimum rehearsal | 4 vCPU | 16 GB RAM | 250 GB durable disk plus separate backup capacity | Sufficient for disposable rehearsal and verifier-driven setup review only. |"
  "| Recommended first-user | 8 vCPU | 32 GB RAM | 500 GB durable disk plus separate backup capacity | Recommended for one named customer environment with Wazuh intake, PostgreSQL state, proxy ingress, and bounded Shuffle delegation. |"
  "| Component | Version expectation | Host CPU/RAM/disk expectation | Ports | Volumes | Certificate requirements | Known incompatibilities | Host preflight follow-up fields | Authority boundary |"
  "Known incompatible versions must be explicit and must fail host preflight follow-up until reviewed."
  'A later host preflight issue must consume the `AEGISOPS_PREFLIGHT_*` fields named in this matrix and fail closed when a required field is missing, malformed, placeholder-backed, stale, incompatible, inferred from naming conventions, or only partially trusted.'
  "The existing install preflight remains the current verifier for runtime input, secret custody, storage separation, migration bootstrap, and optional-extension non-blocking behavior."
  "Host preflight output may report readiness evidence, incompatibility findings, missing prerequisites, and safe next actions. It must not promote Docker, Compose, Wazuh, Shuffle, port, certificate, or version state into AegisOps workflow truth."
  "any required component row is missing, including AegisOps, Wazuh, Shuffle, PostgreSQL, proxy, Docker, or Docker Compose;"
  "CPU, RAM, disk, ports, volumes, certificate requirements, known incompatibilities, or preflight follow-up fields are missing;"
  "known incompatible versions are omitted or described as warnings only;"
  "substrate version state, port state, certificate state, Docker state, Compose state, Wazuh state, or Shuffle state is described as workflow truth;"
  "- Substrate version state is AegisOps workflow truth."
  "- Docker status is AegisOps workflow truth."
  "- Docker Compose status is AegisOps workflow truth."
  "- Wazuh alert status is AegisOps case truth."
  "- Shuffle workflow success is AegisOps reconciliation truth."
  "- This matrix implements the host preflight engine."
  'Run `bash scripts/verify-phase-52-3-combined-dependency-matrix.sh`.'
  'Run `bash scripts/test-verify-phase-52-3-combined-dependency-matrix.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1066 --config <supervisor-config-path>`.'
)

components=(
  "AegisOps"
  "Wazuh"
  "Shuffle"
  "PostgreSQL"
  "Proxy"
  "Docker"
  "Docker Compose"
)

forbidden_claims=(
  "Substrate version state is AegisOps workflow truth"
  "Docker status is AegisOps workflow truth"
  "Docker Compose status is AegisOps workflow truth"
  "Wazuh alert status is AegisOps case truth"
  "Shuffle workflow success is AegisOps reconciliation truth"
  "Placeholder secrets are valid credentials"
  "Raw forwarded headers are trusted identity"
  "This matrix implements the host preflight engine"
  "This matrix implements Wazuh product-profile runtime behavior"
  "This matrix implements Shuffle product-profile runtime behavior"
)

required_preflight_fields=(
  "AEGISOPS_PREFLIGHT_AEGISOPS_REVISION"
  "AEGISOPS_PREFLIGHT_WAZUH_VERSION"
  "AEGISOPS_PREFLIGHT_SHUFFLE_VERSION"
  "AEGISOPS_PREFLIGHT_POSTGRES_VERSION"
  "AEGISOPS_PREFLIGHT_PROXY_VERSION"
  "AEGISOPS_PREFLIGHT_DOCKER_ENGINE_VERSION"
  "AEGISOPS_PREFLIGHT_COMPOSE_VERSION"
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
  echo "Missing Phase 52.3 combined dependency matrix: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.3 combined dependency matrix heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.3 combined dependency matrix statement: ${phrase}" >&2
    exit 1
  fi
done

for component in "${components[@]}"; do
  if ! grep -Eq "^\| ${component} \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.3 dependency row: ${component}" >&2
    exit 1
  fi
done

for field in "${required_preflight_fields[@]}"; do
  if ! grep -Fq -- "\`${field}\`" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.3 host preflight follow-up field: ${field}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${doc_path}"
}

contains_placeholder_secret_valid_claim() {
  awk '
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(must fail|fail closed|fails validation|invalid|must not|cannot|not satisfy|incompatible)/
      if (!in_forbidden_claims && !negative_context && line ~ /(^|[^[:alnum:]_])placeholder secrets?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|production)([^[:alnum:]_]|$)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${doc_rendered_markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 52.3 combined dependency matrix claim: ${claim}" >&2
    exit 1
  fi
done

if contains_placeholder_secret_valid_claim; then
  echo "Forbidden Phase 52.3 combined dependency matrix claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
unix_absolute_path="/${path_token_chars}+"
windows_drive_path="[A-Za-z]:[\\\\/]${path_token_chars}*"
local_path_token="(${unix_absolute_path}|${windows_drive_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.3 combined dependency matrix: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.3 combined dependency matrix link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/combined-dependency-matrix\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.3 combined dependency matrix." >&2
  exit 1
fi

echo "Phase 52.3 combined dependency matrix is present and preserves component coverage, host footprint, incompatibility handling, preflight follow-up fields, and authority boundaries."
