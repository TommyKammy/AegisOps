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
required_profile_lines=(
  "    role: proxy-mediated operator UI for reviewed Shuffle administration only"
  "    role: internal Shuffle API for reviewed delegated automation"
  "    role: worker orchestration for reviewed routine automation only"
  "    role: pinned worker image for delegated action execution"
  "    role: Shuffle-owned datastore separated from AegisOps PostgreSQL and evidence custody"
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

expected_contract_incompatible_for_component() {
  case "$1" in
    opensearch) printf '%s\n' "OpenSearch 1.x; unreviewed OpenSearch 4.x; \`latest\`; RC; beta." ;;
    *) printf '%s\n' "Shuffle 1.x; unreviewed Shuffle 2.3.x; \`latest\`; RC; beta." ;;
  esac
}

expected_contract_upgrade_note_for_component() {
  case "$1" in
    frontend) printf '%s\n' "UI changes require later guided first-user journey and delegation-surface review." ;;
    backend) printf '%s\n' "API changes require later callback/API boundary and receipt-normalization evidence." ;;
    orborus) printf '%s\n' "Orchestration changes require later delegation-binding and fallback evidence." ;;
    worker) printf '%s\n' "Worker image changes require later workflow-catalog and delegation-binding evidence." ;;
    opensearch) printf '%s\n' "Datastore changes require later backup, restore, and volume-custody evidence." ;;
  esac
}

expected_resource_for_component() {
  case "$1" in
    frontend) printf '%s\n' "1 vCPU, 1 GB RAM, bounded config/log storage" ;;
    backend) printf '%s\n' "2 vCPU, 4 GB RAM, bounded app/file storage" ;;
    orborus) printf '%s\n' "1 vCPU, 2 GB RAM, bounded worker orchestration capacity" ;;
    worker) printf '%s\n' "Ephemeral worker capacity bounded by reviewed concurrency" ;;
    opensearch) printf '%s\n' "2 vCPU, 6 GB RAM, 120 GB durable substrate storage" ;;
  esac
}

expected_contract_ports_for_component() {
  case "$1" in
    frontend) printf '%s\n' "\`80/tcp\` and \`443/tcp\` internal frontend UI through reviewed proxy only." ;;
    backend) printf '%s\n' "\`5001/tcp\` internal API only through reviewed proxy route." ;;
    orborus) printf '%s\n' "No direct host ports; outbound worker orchestration only." ;;
    worker) printf '%s\n' "No direct host ports; callback egress returns through reviewed callback route only." ;;
    opensearch) printf '%s\n' "\`9200/tcp\` internal Shuffle datastore API only." ;;
  esac
}

expected_ports_for_component() {
  case "$1" in
    frontend) printf '%s\n' "80/tcp internal frontend UI|443/tcp internal frontend UI TLS" ;;
    backend) printf '%s\n' "5001/tcp internal backend API" ;;
    orborus) printf '%s\n' "none direct host ports; outbound worker orchestration only" ;;
    worker) printf '%s\n' "none direct host ports; callback egress returns through reviewed callback route only" ;;
    opensearch) printf '%s\n' "9200/tcp internal Shuffle datastore API" ;;
  esac
}

expected_contract_volumes_for_component() {
  case "$1" in
    frontend) printf '%s\n' "\`shuffle-frontend-config\`." ;;
    backend) printf '%s\n' "\`shuffle-apps\`; \`shuffle-files\`; \`shuffle-docker-socket-proxy\`." ;;
    orborus) printf '%s\n' "\`shuffle-docker-socket-proxy\`; \`shuffle-worker-runtime\`." ;;
    worker) printf '%s\n' "\`shuffle-worker-ephemeral\`; \`shuffle-app-execution-cache\`." ;;
    opensearch) printf '%s\n' "\`shuffle-database\`." ;;
  esac
}

expected_volumes_for_component() {
  case "$1" in
    frontend) printf '%s\n' "shuffle-frontend-config" ;;
    backend) printf '%s\n' "shuffle-apps|shuffle-files|shuffle-docker-socket-proxy" ;;
    orborus) printf '%s\n' "shuffle-docker-socket-proxy|shuffle-worker-runtime" ;;
    worker) printf '%s\n' "shuffle-worker-ephemeral|shuffle-app-execution-cache" ;;
    opensearch) printf '%s\n' "shuffle-database" ;;
  esac
}

expected_contract_credentials_for_component() {
  case "$1" in
    frontend) printf '%s\n' "\`shuffle-frontend-session-secret-ref\`." ;;
    backend) printf '%s\n' "\`shuffle-api-credential-ref\`; \`shuffle-callback-secret-ref\`; \`shuffle-encryption-modifier-ref\`." ;;
    orborus) printf '%s\n' "\`shuffle-orborus-auth-ref\`; \`shuffle-worker-registry-ref\`." ;;
    worker) printf '%s\n' "\`shuffle-worker-runtime-secret-ref\`; \`shuffle-app-auth-custody-ref\`." ;;
    opensearch) printf '%s\n' "\`shuffle-opensearch-admin-secret-ref\`." ;;
  esac
}

expected_credentials_for_component() {
  case "$1" in
    frontend) printf '%s\n' "shuffle-frontend-session-secret-ref" ;;
    backend) printf '%s\n' "shuffle-api-credential-ref|shuffle-callback-secret-ref|shuffle-encryption-modifier-ref" ;;
    orborus) printf '%s\n' "shuffle-orborus-auth-ref|shuffle-worker-registry-ref" ;;
    worker) printf '%s\n' "shuffle-worker-runtime-secret-ref|shuffle-app-auth-custody-ref" ;;
    opensearch) printf '%s\n' "shuffle-opensearch-admin-secret-ref" ;;
  esac
}

expected_boundary_for_component() {
  case "$1" in
    frontend) printf '%s\n' "Frontend UI and browser state remain operator context only and cannot become AegisOps workflow truth." ;;
    backend) printf '%s\n' "Backend API and callback payloads remain subordinate delegated-execution context until admitted by AegisOps records." ;;
    orborus) printf '%s\n' "Orborus scheduling and retry state cannot become AegisOps execution or reconciliation truth." ;;
    worker) printf '%s\n' "Worker output is downstream execution context only until normalized into an AegisOps execution receipt." ;;
    opensearch) printf '%s\n' "Shuffle datastore contents are substrate state only and cannot become AegisOps release, gate, or reconciliation truth." ;;
  esac
}

yaml_field_value() {
  local section="$1"
  local field="$2"

  if [[ -z "${section}" ]]; then
    awk -v field="${field}" '
      $0 ~ "^" field ":[[:space:]]*" {
        sub("^" field ":[[:space:]]*", "", $0)
        print
        exit
      }
    ' "${profile_path}"
  else
    awk -v section="${section}" -v field="${field}" '
      $0 == section ":" {
        in_section = 1
        next
      }
      in_section && /^[^[:space:]]/ {
        in_section = 0
      }
      in_section && $0 ~ "^  " field ":[[:space:]]*" {
        sub("^  " field ":[[:space:]]*", "", $0)
        print
        exit
      }
    ' "${profile_path}"
  fi
}

assert_yaml_field_equals() {
  local section="$1"
  local field="$2"
  local expected="$3"
  local actual
  local label

  actual="$(yaml_field_value "${section}" "${field}")"
  label="${field}"
  if [[ -n "${section}" ]]; then
    label="${section}.${field}"
  fi

  if [[ "${actual}" != "${expected}" ]]; then
    if [[ -z "${actual}" ]]; then
      actual="<missing>"
    fi
    echo "Mismatched Phase 54.1 Shuffle profile artifact field ${label}: expected [${expected}] actual [${actual}]" >&2
    exit 1
  fi
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

for line in "${required_profile_lines[@]}"; do
  if ! grep -Fxq -- "${line}" "${profile_path}"; then
    echo "Missing exact Phase 54.1 Shuffle profile artifact line: ${line}" >&2
    exit 1
  fi
done

assert_yaml_field_equals "" "profile_id" "smb-single-node"
assert_yaml_field_equals "" "product_profile" "shuffle"
assert_yaml_field_equals "" "profile_contract_version" "2026-05-03"
assert_yaml_field_equals "" "status" "accepted-contract"
assert_yaml_field_equals "" "authority_boundary" "Shuffle provides subordinate routine automation substrate context only; Shuffle frontend, backend, orborus, worker, OpenSearch, workflow, callback, API, generated config, logs, payload, retry, and version state cannot close, approve, execute, reconcile, release, gate, or mutate authoritative AegisOps records."
assert_yaml_field_equals "api_boundary" "api_url" "http://shuffle-backend:5001"
assert_yaml_field_equals "api_boundary" "callback_url" "<aegisops-shuffle-callback-url>"
assert_yaml_field_equals "api_boundary" "external_access" "proxy-mediated only through reviewed AegisOps route binding"
assert_yaml_field_equals "api_boundary" "callback_identity" "trusted callback secret reference plus AegisOps action request binding required"
assert_yaml_field_equals "profile_expectations" "service_topology" "Frontend, backend, orborus, worker image, and OpenSearch are explicit; optional monitoring, direct Docker socket exposure, and unreviewed workflow packs are not approved by this contract."
assert_yaml_field_equals "profile_expectations" "api_url" "Internal API URL is http://shuffle-backend:5001; external access must be proxy-mediated."
assert_yaml_field_equals "profile_expectations" "callback_url" "Callback URL placeholder <aegisops-shuffle-callback-url> requires later AegisOps route binding before runtime use."
assert_yaml_field_equals "profile_expectations" "ingress" "Shuffle UI, API, worker, and datastore ports are internal or proxy-mediated; direct host exposure is not approved by this contract."
assert_yaml_field_equals "profile_expectations" "volumes" "Shuffle app, file, worker, and datastore volumes are separate from PostgreSQL and AegisOps evidence custody."
assert_yaml_field_equals "profile_expectations" "credentials" "API credentials, callback secrets, encryption modifiers, worker auth, app auth custody, and OpenSearch admin secrets are trusted custody references only; placeholder, sample, fake, TODO, unsigned, inline, or default secret values are invalid."
assert_yaml_field_equals "profile_expectations" "dependencies" "Reviewed Docker/Compose posture, proxy custody, trusted secret references, AegisOps approval/action-request records, and later workflow-catalog custody are required before delegated execution can run."

if grep -Eq '(^|[^[:alnum:]_.-])(latest|stable|current|main|master|HEAD|rc|beta)([^[:alnum:]_.-]|$)' <(grep -E '^[[:space:]]*(version|image):' "${profile_path}"); then
  echo "Forbidden Phase 54.1 Shuffle profile artifact: unpinned version or image reference detected" >&2
  exit 1
fi

for component in "${components[@]}"; do
  expected_version="$(expected_version_for_component "${component}")"
  expected_image="$(expected_image_for_component "${component}")"
  expected_incompatible="$(expected_incompatible_for_component "${component}")"
  expected_contract_incompatible="$(expected_contract_incompatible_for_component "${component}")"
  expected_contract_upgrade_note="$(expected_contract_upgrade_note_for_component "${component}")"
  expected_resource="$(expected_resource_for_component "${component}")"
  expected_contract_ports="$(expected_contract_ports_for_component "${component}")"
  expected_ports="$(expected_ports_for_component "${component}")"
  expected_contract_volumes="$(expected_contract_volumes_for_component "${component}")"
  expected_volumes="$(expected_volumes_for_component "${component}")"
  expected_contract_credentials="$(expected_contract_credentials_for_component "${component}")"
  expected_credentials="$(expected_credentials_for_component "${component}")"
  expected_boundary="$(expected_boundary_for_component "${component}")"
  expected_contract_row="| ${component} | Yes | \`${expected_version}\` | \`${expected_image}\` | ${expected_resource}. | ${expected_contract_ports} | ${expected_contract_volumes} | ${expected_contract_credentials} | ${expected_boundary} |"
  expected_version_row="| ${component} | \`${expected_version}\` | exact | ${expected_contract_incompatible} | ${expected_contract_upgrade_note} |"

  if ! grep -Fxq -- "${expected_contract_row}" <<<"${contract_rendered_markdown}"; then
    echo "Missing complete Phase 54.1 Shuffle component row: ${component}" >&2
    echo "Expected: ${expected_contract_row}" >&2
    exit 1
  fi

  if ! grep -Fxq -- "${expected_version_row}" <<<"${contract_rendered_markdown}"; then
    echo "Missing complete Phase 54.1 Shuffle version matrix row: ${component}" >&2
    echo "Expected: ${expected_version_row}" >&2
    exit 1
  fi

  if ! awk \
    -v component="${component}" \
    -v expected_version="${expected_version}" \
    -v expected_image="${expected_image}" \
    -v expected_ports="${expected_ports}" \
    -v expected_volumes="${expected_volumes}" \
    -v expected_credentials="${expected_credentials}" \
    -v expected_resource="${expected_resource}" \
    -v expected_boundary="${expected_boundary}" '
    function trim(value) {
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      return value
    }
    function finish_list() {
      if (active_list == "ports") {
        ports = list_items
      } else if (active_list == "volumes") {
        volumes = list_items
      } else if (active_list == "credentials") {
        credentials = list_items
      }
      active_list = ""
      list_items = 0
    }
    function append_list_item(line) {
      sub(/^      - /, "", line)
      list_items = list_items == "" ? line : list_items "|" line
    }
    function value_after_key(line, key) {
      sub("^    " key ":[[:space:]]*", "", line)
      return trim(line)
    }
    function mismatch(field, expected, actual) {
      if (actual == "") {
        actual = "<missing>"
      }
      printf "Mismatched Phase 54.1 Shuffle profile artifact component %s field %s: expected [%s] actual [%s]\n", component, field, expected, actual > "/dev/stderr"
      failed = 1
    }
    $0 == "  " component ":" {
      in_component = 1
      required = version = image = ports = volumes = credentials = resource = boundary = ""
      active_list = ""
      list_items = 0
      next
    }
    in_component && (/^version_matrix:/ || /^  [a-z][a-z0-9_-]*:[[:space:]]*$/) {
      finish_list()
      in_component = 0
      next
    }
    in_component && /^    [a-z_]+:/ { finish_list() }
    in_component && /^    required:/ { required = value_after_key($0, "required") }
    in_component && /^    version:/ { version = value_after_key($0, "version") }
    in_component && /^    image:/ { image = value_after_key($0, "image") }
    in_component && $0 == "    ports:" {
      active_list = "ports"
      list_items = ""
      next
    }
    in_component && $0 == "    volumes:" {
      active_list = "volumes"
      list_items = ""
      next
    }
    in_component && $0 == "    credentials:" {
      active_list = "credentials"
      list_items = ""
      next
    }
    in_component && active_list != "" && /^      - [^[:space:]]/ { append_list_item($0) }
    in_component && /^    resource_expectation:/ { resource = value_after_key($0, "resource_expectation") }
    in_component && /^    boundary:/ { boundary = value_after_key($0, "boundary") }
    END {
      finish_list()
      if (required != "true") mismatch("required", "true", required)
      if (version != expected_version) mismatch("version", expected_version, version)
      if (image != expected_image) mismatch("image", expected_image, image)
      if (ports != expected_ports) mismatch("ports", expected_ports, ports)
      if (volumes != expected_volumes) mismatch("volumes", expected_volumes, volumes)
      if (credentials != expected_credentials) mismatch("credentials", expected_credentials, credentials)
      if (resource != expected_resource) mismatch("resource_expectation", expected_resource, resource)
      if (boundary != expected_boundary) mismatch("boundary", expected_boundary, boundary)
      exit(failed ? 1 : 0)
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
