#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/verify-customer-like-rehearsal-environment.sh [<repo-root>] [--env-file <runtime-env-file>]

Validates the customer-like rehearsal environment document and, when an env file
is supplied, fails closed on missing required rehearsal inputs.
EOF
}

repo_root=""
env_file=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      if [[ $# -lt 2 ]]; then
        usage
        exit 2
      fi
      env_file="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -n "${repo_root}" ]]; then
        usage
        exit 2
      fi
      repo_root="$1"
      shift
      ;;
  esac
done

if [[ -z "${repo_root}" ]]; then
  repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
fi

doc_path="${repo_root}/docs/deployment/customer-like-rehearsal-environment.md"
runbook_path="${repo_root}/docs/runbook.md"
profile_path="${repo_root}/docs/deployment/single-customer-profile.md"
smoke_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"
handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"
network_path="${repo_root}/docs/network-exposure-and-access-path-policy.md"
storage_path="${repo_root}/docs/storage-layout-and-mount-policy.md"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

load_env_value() {
  local key="$1"
  local line value

  line="$(grep -E "^${key}=" "${env_file}" | tail -n 1 || true)"
  if [[ -z "${line}" ]]; then
    printf ''
    return
  fi

  value="${line#*=}"
  value="$(trim "${value}")"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "${value}"
}

is_placeholder_value() {
  local value="$1"
  local lowered

  lowered="$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]')"
  [[ "${value}" == *"<"*">"* ]] || \
    [[ "${lowered}" == *"todo"* ]] || \
    [[ "${lowered}" == *"sample"* ]] || \
    [[ "${lowered}" == *"fake"* ]] || \
    [[ "${lowered}" == *"placeholder"* ]] || \
    [[ "${lowered}" == *"change-me"* ]] || \
    [[ "${lowered}" == *"guess"* ]] || \
    [[ "${lowered}" == *"unsigned"* ]]
}

require_env_value() {
  local key="$1"
  local value

  value="$(load_env_value "${key}")"
  if [[ -z "${value}" ]]; then
    echo "Missing required rehearsal input: ${key}" >&2
    exit 1
  fi
  if is_placeholder_value "${value}"; then
    echo "Placeholder rehearsal input is not allowed: ${key}" >&2
    exit 1
  fi
}

require_one_of() {
  local description="$1"
  shift
  local key value has_value=0

  for key in "$@"; do
    value="$(load_env_value "${key}")"
    if [[ -n "${value}" ]]; then
      has_value=1
      if is_placeholder_value "${value}"; then
        echo "Placeholder rehearsal input is not allowed: ${key}" >&2
        exit 1
      fi
    fi
  done

  if [[ "${has_value}" -eq 0 ]]; then
    echo "Missing required rehearsal input binding: ${description}" >&2
    exit 1
  fi
}

uses_openbao_path() {
  local key value

  for key in \
    AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH \
    AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH \
    AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH \
    AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH \
    AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH \
    AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH; do
    value="$(load_env_value "${key}")"
    if [[ -n "${value}" ]]; then
      return 0
    fi
  done

  return 1
}

require_file "${doc_path}" "customer-like rehearsal environment profile"
require_file "${runbook_path}" "runbook document"
require_file "${profile_path}" "single-customer deployment profile"
require_file "${smoke_path}" "runtime smoke bundle"
require_file "${handoff_path}" "operational evidence handoff pack"
require_file "${network_path}" "network exposure policy"
require_file "${storage_path}" "storage layout policy"

required_headings=(
  "# Customer-Like Rehearsal Environment"
  "## 1. Purpose and Boundary"
  "## 2. Disposable Topology"
  "## 3. Services and Ports"
  "## 4. Required Runtime Inputs"
  "## 5. Approved Assumptions"
  "## 6. Rehearsal Flow"
  "## 7. Optional Extensions"
  "## 8. Fail-Closed Validation"
  "## 9. Out of Scope"
)

for heading in "${required_headings[@]}"; do
  require_phrase "${doc_path}" "${heading}" "customer-like rehearsal environment heading"
done

required_phrases=(
  "This document defines the disposable customer-like rehearsal environment for the Phase 37 single-customer live rehearsal gate."
  "The rehearsal exists to replay the reviewed first-boot to single-customer operating path before AegisOps is treated as ready for a single-customer pilot."
  'It is anchored to `docs/runbook.md`, `docs/deployment/single-customer-profile.md`, `docs/deployment/runtime-smoke-bundle.md`, `docs/deployment/operational-evidence-handoff-pack.md`, `docs/network-exposure-and-access-path-policy.md`, `docs/storage-layout-and-mount-policy.md`, and `control-plane/deployment/first-boot/`.'
  "The rehearsal environment must be disposable, customer-like, and free of private customer context."
  "The smallest approved rehearsal topology is:"
  'the repo-owned first-boot compose surface in `control-plane/deployment/first-boot/docker-compose.yml`'
  "PostgreSQL as the authoritative AegisOps control-plane persistence dependency"
  "the approved reverse proxy boundary as the only user-facing ingress path"
  "a reviewed Wazuh-facing intake path admitted through the reverse proxy and control-plane boundary"
  "The first-boot to single-customer delta is operational rather than architectural:"
  "The required rehearsal services are limited to:"
  "Control plane | Authoritative AegisOps record, readiness, runtime, inspection, approval, evidence, execution, and reconciliation surface | Internal only; do not publish the backend port as a front door"
  "PostgreSQL | Authoritative AegisOps-owned state | Internal only; persistent data and backup targets stay separated"
  'Operators must prepare an untracked runtime env file from `control-plane/deployment/first-boot/bootstrap.env.sample`.'
  '`AEGISOPS_FIRST_BOOT_PROXY_PORT`'
  '`AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS`'
  '`AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS`'
  'The PostgreSQL DSN must resolve from either `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN`, `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE`, or `AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH`.'
  "Each required secret must resolve from a reviewed file binding or OpenBao binding:"
  "Missing, empty, placeholder, TODO, sample, fake, guessed, or unsigned values are not approved rehearsal inputs."
  "the reverse proxy is the only reviewed user-facing ingress path"
  "PostgreSQL state uses a dedicated runtime mount"
  "Wazuh remains an upstream detection substrate"
  'Run `scripts/verify-customer-like-rehearsal-environment.sh --env-file <runtime-env-file>` before startup.'
  'Run the Phase 33 runtime smoke bundle in `docs/deployment/runtime-smoke-bundle.md` through the reverse proxy.'
  'Capture the evidence required by `docs/deployment/operational-evidence-handoff-pack.md`.'
  "Assistant, ML shadow, endpoint evidence, optional network evidence, OpenSearch, n8n, Shuffle, and isolated-executor paths remain disabled by default, unavailable, or explicitly non-blocking."
  "Optional extensions must not become startup prerequisites, readiness gates, smoke prerequisites, upgrade success gates, evidence handoff prerequisites, or reasons to widen the control-plane, PostgreSQL, reverse-proxy, or Wazuh-facing boundary."
  'The verifier must fail when the rehearsal document is missing, cross-links are missing, required runtime inputs are absent, secret bindings are absent, placeholder values are still present, `AEGISOPS_CONTROL_PLANE_BOOT_MODE` is not `first-boot`, optional extensions are described as prerequisites, or publishable guidance uses workstation-local absolute paths.'
  "This environment does not authorize external substrates as AegisOps authority."
)

for phrase in "${required_phrases[@]}"; do
  require_phrase "${doc_path}" "${phrase}" "customer-like rehearsal environment statement"
done

require_phrase "${runbook_path}" 'The customer-like rehearsal environment in `docs/deployment/customer-like-rehearsal-environment.md` is the reviewed disposable topology for replaying the first-boot to single-customer path before a pilot readiness decision.' "runbook customer-like rehearsal link"
require_phrase "${profile_path}" 'The customer-like rehearsal environment in `docs/deployment/customer-like-rehearsal-environment.md` defines the disposable topology and preflight validation used to rehearse this profile without private customer context.' "single-customer profile customer-like rehearsal link"
require_phrase "${smoke_path}" 'For Phase 37 rehearsal, run this bundle after `scripts/verify-customer-like-rehearsal-environment.sh --env-file <runtime-env-file>` passes for the disposable customer-like environment.' "runtime smoke customer-like rehearsal link"
require_phrase "${handoff_path}" 'For Phase 37 customer-like rehearsal, include the verifier result from `scripts/verify-customer-like-rehearsal-environment.sh --env-file <runtime-env-file>` with the startup, smoke, backup-custody, and clean-state evidence.' "handoff customer-like rehearsal link"

for forbidden in "requires OpenSearch" "requires n8n" "requires Shuffle" "requires ML shadow" "requires Kubernetes" "requires customer-private credential"; do
  if grep -Fqi -- "${forbidden}" "${doc_path}"; then
    echo "Forbidden customer-like rehearsal environment statement: ${forbidden}" >&2
    exit 1
  fi
done

if grep -Eq '(^|[^[:alnum:]_./-])(~[/\\]|/Users/[^[:space:])>]+|/home/[^[:space:])>]+|[A-Za-z]:\\Users\\[^[:space:])>]+)' "${doc_path}"; then
  echo "Forbidden customer-like rehearsal environment statement: workstation-local absolute path detected" >&2
  exit 1
fi

if [[ -n "${env_file}" ]]; then
  if [[ ! -f "${env_file}" ]]; then
    echo "Missing rehearsal env file: ${env_file}" >&2
    exit 1
  fi

  require_env_value AEGISOPS_CONTROL_PLANE_HOST
  require_env_value AEGISOPS_CONTROL_PLANE_PORT
  require_env_value AEGISOPS_CONTROL_PLANE_BOOT_MODE
  require_env_value AEGISOPS_CONTROL_PLANE_LOG_LEVEL
  require_env_value AEGISOPS_FIRST_BOOT_PROXY_PORT
  require_env_value AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS
  require_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS
  require_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT
  require_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER

  if [[ "$(load_env_value AEGISOPS_CONTROL_PLANE_BOOT_MODE)" != "first-boot" ]]; then
    echo "Invalid rehearsal boot mode: AEGISOPS_CONTROL_PLANE_BOOT_MODE must be first-boot" >&2
    exit 1
  fi

  require_one_of "PostgreSQL DSN" \
    AEGISOPS_CONTROL_PLANE_POSTGRES_DSN \
    AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE \
    AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH
  require_one_of "Wazuh ingest shared secret" \
    AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE \
    AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH
  require_one_of "Wazuh ingest reverse-proxy secret" \
    AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE \
    AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH
  require_one_of "protected-surface reverse-proxy secret" \
    AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE \
    AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH
  require_one_of "admin bootstrap token" \
    AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE \
    AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH
  require_one_of "break-glass token" \
    AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE \
    AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH

  if uses_openbao_path; then
    require_env_value AEGISOPS_OPENBAO_ADDRESS
    require_one_of "OpenBao token" AEGISOPS_OPENBAO_TOKEN_FILE AEGISOPS_OPENBAO_TOKEN
    require_env_value AEGISOPS_OPENBAO_KV_MOUNT
  fi
fi

echo "Customer-like rehearsal environment is present and required rehearsal inputs fail closed when checked."
