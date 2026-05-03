#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
contract_path="${repo_root}/docs/deployment/shuffle-smb-single-node-profile-contract.md"
profile_path="${repo_root}/docs/deployment/profiles/smb-single-node/shuffle/profile.yaml"
readme_path="${repo_root}/README.md"

required_headings=(
  "# Phase 54.1 Shuffle SMB Single-Node Profile Contract"
  "## 1. Purpose"
  "## 2. Authority Boundary"
  "## 3. Component Contract"
  "## 4. Version Matrix"
  "## 5. Profile Expectations"
  "## 6. Validation Rules"
  "## 7. Forbidden Claims"
  "## 8. Validation"
  "## 9. Non-Goals"
)

required_phrases=(
  "- **Status**: Accepted contract"
  "- **Date**: 2026-05-03"
  "- **Related Issues**: #1154, #1155"
  "This contract defines the repo-owned Shuffle \`smb-single-node\` product-profile contract and version matrix."
  "The required structured artifact is \`docs/deployment/profiles/smb-single-node/shuffle/profile.yaml\`."
  "Shuffle is a subordinate routine automation substrate."
  "AegisOps control-plane records remain authoritative for alert, case, evidence, approval, action request, execution receipt, reconciliation, audit, limitation, delegation intent, release, gate, and closeout truth."
  "This contract cites the Phase 51.6 authority-boundary negative-test policy in \`docs/phase-51-6-authority-boundary-negative-test-policy.md\`."
  "| Component | Required | Version pin | Image pin | Resource expectation | Ports | Volumes | Credential expectations | Authority boundary |"
  "| Component | Accepted version | Pin type | Known incompatible versions | Upgrade note |"
  "- API URL: the reviewed internal API URL is \`http://shuffle-backend:5001\`; external access must be proxy-mediated and cannot imply direct backend exposure."
  "- Callback URL: the reviewed AegisOps callback URL placeholder is \`<aegisops-shuffle-callback-url>\` and must bind to an AegisOps-owned callback route before runtime use."
  "- Dependency expectations: Shuffle depends on reviewed Docker/Compose posture, proxy custody, trusted secret references, AegisOps approval/action-request records, and later workflow-catalog custody before delegated execution can run."
  "Run \`bash scripts/verify-phase-54-1-shuffle-profile-contract.sh\`."
  "Run \`bash scripts/test-verify-phase-54-1-shuffle-profile-contract.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1155 --config <supervisor-config-path>\`."
)

components=(frontend backend orborus worker opensearch)
required_profile_terms=(
  "profile_id: smb-single-node"
  "product_profile: shuffle"
  "profile_contract_version: 2026-05-03"
  "authority_boundary: Shuffle provides subordinate routine automation substrate context only;"
  "service_topology:"
  "api_boundary:"
  "api_url: http://shuffle-backend:5001"
  "callback_url: <aegisops-shuffle-callback-url>"
  "ports:"
  "volumes:"
  "credentials:"
  "dependencies:"
)

forbidden_claims=(
  "Shuffle workflow success is AegisOps reconciliation truth"
  "Shuffle workflow failure is AegisOps execution truth"
  "Shuffle callback payload is AegisOps execution receipt truth"
  "Shuffle backend state is AegisOps approval truth"
  "Shuffle frontend state is AegisOps workflow truth"
  "Shuffle worker state is AegisOps closeout truth"
  "Shuffle OpenSearch state is AegisOps release truth"
  "Raw forwarded headers are trusted callback identity"
  "Phase 54.1 implements workflow template imports"
  "Phase 54.1 implements delegation binding"
  "Phase 54.1 implements receipt normalization"
  "Phase 54.1 implements Shuffle fallback behavior"
  "Phase 54.1 implements Wazuh product profiles"
  "Phase 54.1 claims Beta, RC, GA, commercial readiness, broad SOAR replacement readiness, Controlled Write default enablement, or Hard Write default enablement"
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

expected_version_for_component() {
  case "$1" in
    opensearch) printf '%s\n' "3.2.0" ;;
    *) printf '%s\n' "2.2.0" ;;
  esac
}

expected_image_for_component() {
  case "$1" in
    frontend) printf '%s\n' "ghcr.io/shuffle/shuffle-frontend:2.2.0" ;;
    backend) printf '%s\n' "ghcr.io/shuffle/shuffle-backend:2.2.0" ;;
    orborus) printf '%s\n' "ghcr.io/shuffle/shuffle-orborus:2.2.0" ;;
    worker) printf '%s\n' "ghcr.io/shuffle/shuffle-worker:2.2.0" ;;
    opensearch) printf '%s\n' "opensearchproject/opensearch:3.2.0" ;;
  esac
}

expected_incompatible_for_component() {
  case "$1" in
    opensearch) printf '%s\n' "OpenSearch 1.x, unreviewed OpenSearch 4.x, latest, rc, beta" ;;
    *) printf '%s\n' "Shuffle 1.x, unreviewed Shuffle 2.3.x, latest, rc, beta" ;;
  esac
}

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 54.1 Shuffle profile contract: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${profile_path}" ]]; then
  echo "Missing Phase 54.1 Shuffle profile artifact: ${profile_path}" >&2
  exit 1
fi

contract_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${contract_path}"
)"

for heading in "${required_headings[@]}"; do
  if ! grep -Fxq -- "${heading}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 54.1 Shuffle profile contract heading: ${heading}" >&2
    exit 1
  fi
done

for phrase in "${required_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" <<<"${contract_rendered_markdown}"; then
    echo "Missing Phase 54.1 Shuffle profile contract statement: ${phrase}" >&2
    exit 1
  fi
done

for term in "${required_profile_terms[@]}"; do
  if ! grep -Fq -- "${term}" "${profile_path}"; then
    echo "Missing Phase 54.1 Shuffle profile artifact term: ${term}" >&2
    exit 1
  fi
done

if grep -Eq '(^|[^[:alnum:]_.-])(latest|stable|current|main|master|HEAD|rc|beta)([^[:alnum:]_.-]|$)' <(grep -E '^[[:space:]]*(version|image):' "${profile_path}"); then
  echo "Forbidden Phase 54.1 Shuffle profile artifact: unpinned version or image reference detected" >&2
  exit 1
fi

for component in "${components[@]}"; do
  expected_version="$(expected_version_for_component "${component}")"
  expected_image="$(expected_image_for_component "${component}")"
  expected_incompatible="$(expected_incompatible_for_component "${component}")"

  if ! grep -Eq "^\| ${component} \| Yes \| \`${expected_version}\` \| \`${expected_image}\` \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${contract_rendered_markdown}"; then
    echo "Missing complete Phase 54.1 Shuffle component row: ${component}" >&2
    exit 1
  fi

  if ! grep -Eq "^\| ${component} \| \`${expected_version}\` \| exact \| [^|[:space:]][^|]* \| [^|[:space:]][^|]* \|$" <<<"${contract_rendered_markdown}"; then
    echo "Missing complete Phase 54.1 Shuffle version matrix row: ${component}" >&2
    exit 1
  fi

  if ! awk -v component="${component}" -v expected_version="${expected_version}" -v expected_image="${expected_image}" '
    function trim(value) {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      return value
    }
    function list_has_items() {
      if (active_list == "ports" && list_items > 0) {
        ports = 1
      } else if (active_list == "volumes" && list_items > 0) {
        volumes = 1
      } else if (active_list == "credentials" && list_items > 0) {
        credentials = 1
      }
      active_list = ""
      list_items = 0
    }
    function value_after_key(line, key) {
      sub("^    " key ":[[:space:]]*", "", line)
      return trim(line)
    }
    $0 == "  " component ":" {
      in_component = 1
      required = version = image = ports = volumes = credentials = resources = boundary = 0
      active_list = ""
      list_items = 0
      next
    }
    in_component && (/^version_matrix:/ || /^  [a-z][a-z0-9_-]*:[[:space:]]*$/) {
      list_has_items()
      in_component = 0
      next
    }
    in_component && /^    [a-z_]+:/ { list_has_items() }
    in_component && $0 == "    required: true" { required = 1 }
    in_component && $0 == "    version: " expected_version { version = 1 }
    in_component && $0 == "    image: " expected_image { image = 1 }
    in_component && $0 == "    ports:" {
      active_list = "ports"
      list_items = 0
      next
    }
    in_component && $0 == "    volumes:" {
      active_list = "volumes"
      list_items = 0
      next
    }
    in_component && $0 == "    credentials:" {
      active_list = "credentials"
      list_items = 0
      next
    }
    in_component && active_list != "" && /^      - [^[:space:]]/ { list_items++ }
    in_component && /^    resource_expectation:/ && value_after_key($0, "resource_expectation") != "" { resources = 1 }
    in_component && /^    boundary:/ && value_after_key($0, "boundary") != "" { boundary = 1 }
    END {
      list_has_items()
      exit(required && version && image && ports && volumes && credentials && resources && boundary ? 0 : 1)
    }
  ' "${profile_path}"; then
    echo "Missing complete Phase 54.1 Shuffle profile artifact component: ${component}" >&2
    exit 1
  fi

  if ! awk -v component="${component}" -v expected_version="${expected_version}" -v expected_incompatible="${expected_incompatible}" '
    /version_matrix:/ { in_matrix = 1; next }
    /^profile_expectations:/ { in_matrix = 0 }
    in_matrix && $0 == "  - component: " component {
      in_component = 1
      version = pin = incompatible = 0
      next
    }
    in_matrix && /^  - component:/ && in_component { in_component = 0 }
    in_component && $0 == "    version: " expected_version { version = 1 }
    in_component && $0 == "    pin_type: exact" { pin = 1 }
    in_component && $0 == "    incompatible_versions: " expected_incompatible { incompatible = 1 }
    END { exit(version && pin && incompatible ? 0 : 1) }
  ' "${profile_path}"; then
    echo "Missing complete Phase 54.1 Shuffle profile artifact version matrix row: ${component}" >&2
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
  ' "${contract_path}"
}

contains_placeholder_secret_valid_claim() {
  awk '
    /^## 7\. Forbidden Claims$/ { in_forbidden_claims = 1; next }
    /^## / && in_forbidden_claims { in_forbidden_claims = 0 }
    {
      line = tolower($0)
      negative_context = line ~ /(must fail|fail closed|fails validation|invalid|must not|cannot|not satisfy|subordinate|deferred)/
      if (!in_forbidden_claims && !negative_context && line ~ /(^|[^[:alnum:]_])placeholder[^.]*secrets?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|production)([^[:alnum:]_]|$)/) {
        found = 1
      }
      if (!in_forbidden_claims && !negative_context && line ~ /(^|[^[:alnum:]_])placeholder[^.]*api keys?[[:space:]]+(are|is|count as|counts as|may be|can be|remain|stays)[[:space:]]+([^.]*[^[:alnum:]_])?(valid|trusted|accepted|production)([^[:alnum:]_]|$)/) {
        found = 1
      }
    }
    END { exit(found ? 0 : 1) }
  ' <<<"${contract_rendered_markdown}"
}

for claim in "${forbidden_claims[@]}"; do
  if contains_forbidden_outside_forbidden_section "${claim}"; then
    echo "Forbidden Phase 54.1 Shuffle profile contract claim: ${claim}" >&2
    exit 1
  fi
done

if contains_placeholder_secret_valid_claim; then
  echo "Forbidden Phase 54.1 Shuffle profile contract claim: placeholder secrets accepted as valid credentials" >&2
  exit 1
fi

path_token_boundary="(^|[[:space:]'\"\`(<{=])"
path_token_chars="[^[:space:]'\"\` )>}|]"
home_absolute_path="/(Users|home)/${path_token_chars}+"
windows_user_path="[A-Za-z]:[\\\\/]Users[\\\\/]${path_token_chars}*"
local_path_token="(${home_absolute_path}|${windows_user_path})"

if grep -Eq "(${path_token_boundary}${local_path_token}|file:///?${local_path_token})" "${contract_path}" "${profile_path}"; then
  echo "Forbidden Phase 54.1 Shuffle profile contract: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 54.1 Shuffle profile contract link check: ${readme_path}" >&2
  exit 1
fi

readme_rendered_markdown="$(
  rendered_markdown_without_code_blocks "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/deployment/shuffle-smb-single-node-profile-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 54.1 Shuffle profile contract." >&2
  exit 1
fi

echo "Phase 54.1 Shuffle profile contract is present and preserves service topology, exact version pins, API/callback boundaries, port/volume/credential expectations, and authority boundaries."
