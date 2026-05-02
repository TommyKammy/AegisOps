#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/wazuh-manager-intake-binding-contract.md"
artifact_path="${repo_root}/docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 53.3 Wazuh Manager Intake Binding Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Intake Binding Contract"
  "## 4. Required Provenance Fields"
  "## 5. Analytic-Signal Admission"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1135, #1136, #1137, #1138"
  "This contract defines the Wazuh manager-to-AegisOps intake URL binding, shared-secret custody reference, reviewed proxy binding, required provenance fields, and analytic-signal admission posture for the \`smb-single-node\` Wazuh product profile."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/wazuh/intake-binding.yaml\`."
  "Wazuh is a subordinate detection substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, source admission, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "The reviewed AegisOps intake URL is \`/intake/wazuh\`."
  "The reviewed proxy route binding is \`aegisops-proxy:/intake/wazuh -> aegisops-control-plane:/intake/wazuh\`."
  "The Wazuh manager must send alerts to AegisOps through the reviewed proxy route only."
  "The shared-secret custody reference must be \`AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE\` or \`AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH\`."
  "Raw shared-secret values, placeholder secrets, sample secrets, fake values, TODO values, unsigned tokens, raw forwarded headers, or inferred source linkage must fail validation."
  "Wazuh-origin input remains a candidate analytic signal until AegisOps admits it and links it to an AegisOps record."
  "A Wazuh alert, manager status, dashboard status, rule state, timestamp, or webhook acknowledgement must not be treated as case, alert, reconciliation, release, gate, closeout, or source truth before AegisOps admission and linkage."
  "Run \`bash scripts/verify-phase-53-3-wazuh-intake-binding-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-53-3-wazuh-intake-binding-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1138 --config <supervisor-config-path>\`."
)

required_artifact_terms=(
  "profile_id: smb-single-node"
  "product_profile: wazuh"
  "intake_binding_contract_version: 2026-05-03"
  "status: accepted-contract"
  "intake_url: /intake/wazuh"
  "proxy_route: aegisops-proxy:/intake/wazuh -> aegisops-control-plane:/intake/wazuh"
  "manager_delivery: reviewed-proxy-only"
  "shared_secret_custody: AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE or AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH"
  "raw_secret_values_allowed: false"
  "forwarded_headers_trusted: false"
  "source_linkage_inference_allowed: false"
  "admission_posture: candidate-analytic-signal-until-aegisops-admission-and-linkage"
  "pre_admission_authority: false"
  "direct_wazuh_to_shuffle_shortcut_allowed: false"
  "provenance_fields:"
  "negative_admission_tests:"
)

required_provenance_fields=(
  "source_family"
  "source_system"
  "source_component"
  "source_id"
  "event_id"
  "event_timestamp"
  "wazuh_manager_id"
  "wazuh_rule_id"
  "wazuh_rule_level"
  "ingest_channel"
  "admission_channel"
  "secret_custody_reference"
  "proxy_route"
  "reviewed_by"
)

forbidden_claims=(
  "Wazuh-origin input is AegisOps case truth before admission"
  "Wazuh alert status is AegisOps case truth"
  "Wazuh manager state is AegisOps source truth"
  "Wazuh dashboard state is AegisOps workflow truth"
  "Webhook acknowledgement is AegisOps reconciliation truth"
  "Wazuh timestamp is AegisOps release truth"
  "Placeholder Wazuh intake secrets are valid credentials"
  "Raw forwarded headers are trusted identity"
  "Inferred Wazuh source linkage is valid admission"
  "Phase 53.3 implements Wazuh source-health projection"
  "Phase 53.3 implements Wazuh upgrade automation"
  "Phase 53.3 implements Shuffle product profiles"
)

rendered_markdown_without_code_blocks() {
  local markdown_path="$1"

  awk '
    /^[[:space:]]*(\`\`\`|~~~)/ {
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
  echo "Missing Phase 53.3 Wazuh intake binding contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${artifact_path}" ]]; then
  echo "Missing Phase 53.3 Wazuh intake binding artifact: ${artifact_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.3 Wazuh intake binding contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 53.3 Wazuh intake binding contract statement: ${phrase}" >&2
    exit 1
  fi
done

for term in "${required_artifact_terms[@]}"; do
  if ! grep -Fq -- "${term}" "${artifact_path}"; then
    echo "Missing Phase 53.3 Wazuh intake binding artifact term: ${term}" >&2
    exit 1
  fi
done

for field in "${required_provenance_fields[@]}"; do
  if ! grep -Fq -- "- ${field}" "${artifact_path}"; then
    echo "Missing Phase 53.3 Wazuh provenance field: ${field}" >&2
    exit 1
  fi
done

if ! awk '
  /^provenance_fields:/ { in_fields = 1; count = 0; next }
  /^[a-z_]+:/ && in_fields { in_fields = 0 }
  in_fields && /^  - [^[:space:]]/ { count++ }
  END { exit(count >= 14 ? 0 : 1) }
' "${artifact_path}"; then
  echo "Missing Phase 53.3 Wazuh provenance field coverage: expected at least 14 required fields" >&2
  exit 1
fi

if grep -Eiq '^[[:space:]]*intake_url:[[:space:]]*($|<|todo|tbd|none|null)' "${artifact_path}"; then
  echo "Forbidden Phase 53.3 Wazuh intake binding artifact: missing intake URL" >&2
  exit 1
fi

if grep -Eiq '^[[:space:]]*shared_secret_custody:[[:space:]]*($|<|todo|tbd|none|null|changeme|change-me|password|secret|sample|example|fake|dummy)' "${artifact_path}"; then
  echo "Forbidden Phase 53.3 Wazuh intake binding artifact: missing secret custody reference" >&2
  exit 1
fi

if awk '
  BEGIN { found = 0 }
  /^[[:space:]]*([a-z0-9_-]*_)?(password|secret|token|api_key)[[:space:]]*:/ {
    value = $0
    sub(/^[^:]+:[[:space:]]*/, "", value)
    if (length(value) >= 12 && value !~ /^(AEGISOPS_|<|\$\{)/) {
      found = 1
    }
  }
  END { exit(found ? 0 : 1) }
' "${artifact_path}"; then
  echo "Forbidden Phase 53.3 Wazuh intake binding artifact: committed secret-looking value detected" >&2
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
    echo "Forbidden Phase 53.3 Wazuh intake binding claim: ${claim}" >&2
    exit 1
  fi
done

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${contract_path}" "${artifact_path}"; then
  echo "Forbidden Phase 53.3 Wazuh intake binding contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 53.3 Wazuh intake binding contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | tr -d '\140'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/wazuh-manager-intake-binding-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 53.3 Wazuh intake binding contract." >&2
  exit 1
fi

echo "Phase 53.3 Wazuh intake binding contract is present and rejects missing intake URL, missing secret custody, missing provenance, pre-admission authority, committed secrets, trusted forwarded headers, inferred source linkage, and workstation-local paths."
