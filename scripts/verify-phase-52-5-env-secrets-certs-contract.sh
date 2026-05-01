#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
doc_path="${repo_root}/docs/deployment/env-secrets-certs-contract.md"
readme_path="${repo_root}/README.md"
gitignore_path="${repo_root}/.gitignore"
env_sample_path="${repo_root}/control-plane/deployment/first-boot/bootstrap.env.sample"

required_headings=(
  "# Phase 52.5 Env, Secrets, and Cert Generation Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Generated Runtime Config"
  "## 4. Secret File Custody"
  "## 5. Certificate Generation"
  "## 6. Ignored Generated Paths"
  "## 7. Validation Rules"
  "## 8. Forbidden Claims"
  "## 9. Validation"
  "## 10. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted"
  "- **Date**: 2026-05-01"
  "- **Related Issues**: #1063, #1065, #1066, #1067, #1068"
  "This contract defines generated runtime env config, secret-reference, and certificate-generation expectations for the executable first-user stack only. It does not implement full secret backend integration, Wazuh product-profile generation, Shuffle product-profile generation, installer UX, release-candidate behavior, general-availability behavior, or runtime behavior."
  "Generated runtime config is a setup prerequisite."
  "Env files, generated secret files, generated demo tokens, generated certificates, certificate paths, OpenBao bindings, and custody checklists are setup/security prerequisites only."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, release, gate, and closeout truth."
  'This contract cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md`.'
  'Later setup commands may generate an untracked runtime env file from `control-plane/deployment/first-boot/bootstrap.env.sample`.'
  "| Binding | Expected form | Production posture | Validation rule |"
  "| Secret class | Accepted reference forms | Demo posture | Rejection rule |"
  "Secret values must be supplied through reviewed file bindings or reviewed OpenBao bindings."
  "Later setup commands may generate demo TLS material only when demo mode is explicit."
  "Demo certificates, self-signed local certificates, generated key pairs, or certificate path existence are not production truth and must not satisfy production ingress TLS custody."
  "Generated runtime config, generated secret files, and generated certificates must be untracked or explicitly ignored before setup commands write them."
  "| Ignored path | Purpose | Tracking rule |"
  "placeholder, TODO, sample, fake, guessed, unsigned, inline, or committed secret-looking value is accepted as valid;"
  "demo token or demo certificate posture is treated as production truth"
  'Run `bash scripts/verify-phase-52-5-env-secrets-certs-contract.sh`.'
  'Run `bash scripts/test-verify-phase-52-5-env-secrets-certs-contract.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1068 --config <supervisor-config-path>`.'
)

bindings=(
  "AEGISOPS_RUNTIME_ENV_FILE"
  "AEGISOPS_GENERATED_CONFIG_DIR"
  "AEGISOPS_SECRETS_DIR"
  "AEGISOPS_CERTS_DIR"
  "AEGISOPS_DEMO_TOKEN_FILE"
  "AEGISOPS_DEMO_TLS_CERT_FILE"
)

secret_classes=(
  "PostgreSQL DSN"
  "Wazuh ingest shared secret"
  "Wazuh reverse-proxy secret"
  "Protected-surface proxy secret"
  "Admin bootstrap token"
  "Break-glass token"
  "OpenBao token"
)

ignored_paths=(
  "control-plane/deployment/first-boot/generated/"
  "control-plane/deployment/first-boot/runtime/"
  "control-plane/deployment/first-boot/secrets/"
  "control-plane/deployment/first-boot/certs/"
)

forbidden_claims=(
  "Placeholder secrets are valid credentials"
  "Committed secret-looking values are acceptable"
  "Demo token is production truth"
  "Demo certificate is production truth"
  "Generated certificate path is production truth"
  "Env config is AegisOps workflow truth"
  "Secret file presence is AegisOps approval truth"
  "Certificate freshness is AegisOps release truth"
  "Raw forwarded headers are trusted identity"
  "Phase 52.5 implements secret backend integration"
  "Phase 52.5 implements production certificate automation"
  "Phase 52.5 implements Wazuh product profiles"
  "Phase 52.5 implements Shuffle product profiles"
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
  echo "Missing Phase 52.5 env secrets certs contract: ${doc_path}" >&2
  exit 1
fi

doc_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${doc_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.5 env secrets certs contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${doc_rendered_markdown}"; then
    echo "Missing Phase 52.5 env secrets certs contract statement: ${phrase}" >&2
    exit 1
  fi
done

for binding in "${bindings[@]}"; do
  if ! grep -Eq "^\| \`${binding}\` \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.5 runtime binding row: ${binding}" >&2
    exit 1
  fi
done

for secret_class in "${secret_classes[@]}"; do
  if ! grep -Eq "^\| ${secret_class} \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.5 secret custody row: ${secret_class}" >&2
    exit 1
  fi
done

for ignored_path in "${ignored_paths[@]}"; do
  if ! grep -Eq "^\| \`${ignored_path//\//\\/}\` \| [^|[:space:]][^|]* \| Must remain ignored\. \|$" <<<"${doc_rendered_markdown}"; then
    echo "Missing complete Phase 52.5 ignored path row: ${ignored_path}" >&2
    exit 1
  fi
done

contains_forbidden_outside_forbidden_section() {
  local claim="$1"

  awk -v claim="${claim}" '
    BEGIN { claim_lower = tolower(claim) }
    /^## 8\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    !in_forbidden_claims && index(tolower($0), claim_lower) { found = 1 }
    END { exit(found ? 0 : 1) }
  ' "${doc_path}"
}

contains_placeholder_secret_valid_claim() {
  awk '
    /^## 8\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(must fail|fail closed|fails validation|invalid|must not|cannot|not satisfy|separate from|rejected|not valid|not production|not product truth)/
      if (!in_forbidden_claims && !negative_context && line ~ /(^|[^[:alnum:]_])placeholder secrets?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|production)([^[:alnum:]_]|$)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${doc_rendered_markdown}"
}

contains_committed_secret_looking_value() {
  grep -Ein \
    '(^|[^A-Z0-9_])[A-Z0-9_-]*(token|secret|password|private[_-]?key|dsn)[A-Z0-9_-]*[[:space:]]*[:=][[:space:]]*["'\'']?[A-Za-z0-9_./+=:@-]{20,}["'\'']?($|[^A-Za-z0-9_./+=:@-])' \
    "${doc_path}" |
    grep -Eiv '(<[^>]+>|placeholder|sample|demo-only|runtime-injected|OPENBAO_PATH|_FILE|`[^`]+`|forbidden claims)' || true
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 52.5 env secrets certs contract claim: ${claim}" >&2
    exit 1
  fi
done

if contains_placeholder_secret_valid_claim; then
  echo "Forbidden Phase 52.5 env secrets certs contract claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

secret_looking_matches="$(contains_committed_secret_looking_value)"
if [[ -n "${secret_looking_matches}" ]]; then
  echo "Forbidden Phase 52.5 env secrets certs contract: committed secret-looking value detected" >&2
  echo "${secret_looking_matches}" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${doc_path}"; then
  echo "Forbidden Phase 52.5 env secrets certs contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${gitignore_path}" ]]; then
  echo "Missing .gitignore for Phase 52.5 generated runtime path checks: ${gitignore_path}" >&2
  exit 1
fi

for ignored_path in "${ignored_paths[@]}"; do
  if ! grep -Fxq -- "${ignored_path}" "${gitignore_path}"; then
    echo "Missing Phase 52.5 generated runtime ignore pattern: ${ignored_path}" >&2
    exit 1
  fi
done

if [[ ! -f "${env_sample_path}" ]]; then
  echo "Missing first-boot bootstrap env sample: ${env_sample_path}" >&2
  exit 1
fi

if ! grep -Fq -- "docs/deployment/env-secrets-certs-contract.md" "${env_sample_path}"; then
  echo "First-boot bootstrap env sample must link the Phase 52.5 env secrets certs contract." >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 52.5 env secrets certs contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/env-secrets-certs-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 52.5 env secrets certs contract." >&2
  exit 1
fi

echo "Phase 52.5 env secrets certs contract is present and preserves ignored generated paths, demo/prod separation, fail-closed secret validation, and authority boundaries."
