#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/wazuh-certificate-credential-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 53.2 Wazuh Certificate And Credential Handling Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Certificate Handling Contract"
  "## 4. Credential Handling Contract"
  "## 5. Rotation Guidance"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1135, #1136, #1137"
  "This contract defines Wazuh certificate generation-wrapper posture, credential custody expectations, default-credential rejection, rotation guidance, and fail-closed secret validation for the \`smb-single-node\` Wazuh product profile."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/wazuh/certificate-credential-contract.yaml\`."
  "Wazuh is a subordinate detection substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "The Wazuh certificate generation wrapper may generate demo or local rehearsal material only when demo mode is explicit."
  "TLS-ready Wazuh profile validation must require certificate path references for:"
  "Wazuh credentials must be supplied through reviewed file bindings or reviewed OpenBao bindings."
  "Default Wazuh credentials must fail validation."
  "Placeholder credentials must fail validation."
  "Committed live secret-looking values must fail validation."
  "Rotation must replace Wazuh API, indexer admin, dashboard, and ingest shared-secret custody references without committing the old or new secret value."
  "Run \`bash scripts/verify-phase-53-2-wazuh-cert-credential-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-53-2-wazuh-cert-credential-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1137 --config <supervisor-config-path>\`."
)

required_artifact_terms=(
  "profile_id: smb-single-node"
  "product_profile: wazuh"
  "certificate_credential_contract_version: 2026-05-03"
  "tls_ready_profile: true"
  "certificate_generation_wrapper:"
  "demo_mode_required: true"
  "production_truth: false"
  "credential_custody:"
  "wazuh_api_credentials: AEGISOPS_WAZUH_API_CREDENTIALS_FILE or AEGISOPS_WAZUH_API_CREDENTIALS_OPENBAO_PATH"
  "wazuh_indexer_admin_credentials: AEGISOPS_WAZUH_INDEXER_ADMIN_CREDENTIALS_FILE or AEGISOPS_WAZUH_INDEXER_ADMIN_CREDENTIALS_OPENBAO_PATH"
  "wazuh_dashboard_credentials: AEGISOPS_WAZUH_DASHBOARD_CREDENTIALS_FILE or AEGISOPS_WAZUH_DASHBOARD_CREDENTIALS_OPENBAO_PATH"
  "wazuh_ingest_shared_secret: AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE or AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH"
  "default_credential_policy:"
  "placeholder_credential_policy:"
  "committed_secret_policy:"
  "rotation_guidance:"
  "raw_secret_values_allowed: false"
)

required_certificate_paths=(
  "wazuh-manager-api-tls-chain-ref"
  "wazuh-manager-api-tls-private-key-ref"
  "wazuh-indexer-tls-chain-ref"
  "wazuh-indexer-tls-private-key-ref"
  "wazuh-indexer-admin-client-cert-ref"
  "wazuh-dashboard-tls-chain-ref"
  "wazuh-dashboard-tls-private-key-ref"
  "wazuh-dashboard-indexer-client-cert-ref"
)

forbidden_claims=(
  "Wazuh credential state is AegisOps production truth"
  "Wazuh certificate state is AegisOps gate truth"
  "Generated Wazuh certificates are production truth"
  "Default Wazuh credentials are valid credentials"
  "Placeholder Wazuh secrets are valid credentials"
  "Committed Wazuh secret-looking values are acceptable"
  "Raw forwarded headers are trusted identity"
  "Phase 53.2 implements live certificate generation"
  "Phase 53.2 implements secret backend integration"
  "Phase 53.2 implements Wazuh source-health projection"
  "Phase 53.2 implements Wazuh intake binding"
  "Phase 53.2 implements Shuffle product profiles"
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

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 53.2 Wazuh certificate and credential contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 53.2 Wazuh certificate and credential artifact: ${artifact_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.2 Wazuh certificate and credential contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.2 Wazuh certificate and credential contract statement: ${phrase}" >&2
    exit 1
  fi
done

for term in "${required_artifact_terms[@]}"; do
  if ! grep -Fq -- "${term}" "${artifact_path}"; then
    echo "Missing Phase 53.2 Wazuh certificate and credential artifact term: ${term}" >&2
    exit 1
  fi
done

for certificate_path in "${required_certificate_paths[@]}"; do
  if ! grep -Fq -- "- ${certificate_path}" "${artifact_path}"; then
    echo "Missing Phase 53.2 Wazuh certificate path expectation: ${certificate_path}" >&2
    exit 1
  fi
done

if ! awk '
  /^certificate_paths:/ { in_paths = 1; count = 0; next }
  /^[a-z_]+:/ && in_paths { in_paths = 0 }
  in_paths && /^  - [^[:space:]]/ { count++ }
  END { exit(count >= 8 ? 0 : 1) }
' "${artifact_path}"; then
  echo "Missing Phase 53.2 Wazuh certificate path expectation: TLS-ready profile requires certificate path references" >&2
  exit 1
fi

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

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 53.2 Wazuh certificate and credential claim: ${claim}" >&2
    exit 1
  fi
done

if grep -Eiq '(^|[^[:alnum:]_-])(admin:admin|wazuh:wazuh|wazuh:wazuh123|wazuh:SecretPassword)([^[:alnum:]_-]|$)' "${contract_path}" "${artifact_path}"; then
  if grep -Eiq '^[[:space:]]*(default_credentials|wazuh_api_password|wazuh_password|password|credential|secret)[[:space:]]*:[[:space:]]*(admin:admin|wazuh:wazuh|wazuh:wazuh123|wazuh:SecretPassword)' "${artifact_path}"; then
    echo "Forbidden Phase 53.2 Wazuh credential value: default Wazuh credential detected" >&2
    exit 1
  fi
fi

if grep -Eiq '^[[:space:]]*([a-z0-9_-]*_)?(password|secret|credential|token|api_key|placeholder_secret)[[:space:]]*:[[:space:]]*(changeme|change-me|password|Password123|secret|sample|example|fake|dummy|todo)([[:space:]]*$|[^[:alnum:]_-])' "${artifact_path}"; then
  echo "Forbidden Phase 53.2 Wazuh credential value: placeholder secret detected" >&2
  exit 1
fi

if grep -Eq -- '-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----' "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 53.2 Wazuh credential value: committed private key material detected" >&2
  exit 1
fi

if awk '
  BEGIN { found = 0 }
  /^[[:space:]]*([a-z0-9_-]*_)?(password|secret|token|api_key|private_key)[[:space:]]*:/ {
    value = $0
    sub(/^[^:]+:[[:space:]]*/, "", value)
    if (length(value) >= 12 && value !~ /^(AEGISOPS_|<|\$\{)/) {
      found = 1
    }
  }
  END { exit(found ? 0 : 1) }
' "${artifact_path}"; then
  echo "Forbidden Phase 53.2 Wazuh credential value: committed secret-looking value detected" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 53.2 Wazuh certificate and credential contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 53.2 Wazuh certificate and credential contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/wazuh-certificate-credential-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 53.2 Wazuh certificate and credential contract." >&2
  exit 1
fi

echo "Phase 53.2 Wazuh certificate and credential contract is present and rejects default credentials, placeholders, missing TLS certificate paths, committed secret-looking values, private keys, and authority-boundary overclaims."
