#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/verify-single-customer-install-preflight.sh [<repo-root>] --env-file <runtime-env-file>

Validates the Phase 38 single-customer install preflight contract without
provisioning infrastructure, probing customer networks, or printing secret
values.
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

if [[ -z "${env_file}" ]]; then
  usage
  exit 2
fi

manifest_path="${repo_root}/docs/deployment/single-customer-release-bundle-inventory.md"
profile_path="${repo_root}/docs/deployment/single-customer-profile.md"
runbook_path="${repo_root}/docs/runbook.md"
smoke_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"
network_path="${repo_root}/docs/network-exposure-and-access-path-policy.md"
storage_path="${repo_root}/docs/storage-layout-and-mount-policy.md"
compose_path="${repo_root}/control-plane/deployment/first-boot/docker-compose.yml"
env_sample_path="${repo_root}/control-plane/deployment/first-boot/bootstrap.env.sample"
entrypoint_path="${repo_root}/control-plane/deployment/first-boot/control-plane-entrypoint.sh"
migrations_path="${repo_root}/postgres/control-plane/migrations"
smoke_gate_path="${repo_root}/scripts/run-phase-37-runtime-smoke-gate.sh"
rehearsal_verifier_path="${repo_root}/scripts/verify-customer-like-rehearsal-environment.sh"
record_chain_verifier_path="${repo_root}/scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh"
restore_verifier_path="${repo_root}/scripts/verify-phase-37-restore-rollback-upgrade-evidence.sh"

fail() {
  local message="$1"
  printf '%s\n' "${message}" >&2
  exit 1
}

require_file() {
  local path="$1"
  local description="$2"

  [[ -f "${path}" ]] || fail "Missing ${description}"
}

require_dir() {
  local path="$1"
  local description="$2"

  [[ -d "${path}" ]] || fail "Missing ${description}"
}

require_executable() {
  local path="$1"
  local description="$2"

  require_file "${path}" "${description}"
  [[ -x "${path}" ]] || fail "Missing executable bit for ${description}"
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  grep -Fq -- "${phrase}" "${path}" || fail "Missing ${description}"
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

is_placeholder_or_untrusted_value() {
  local value="$1"
  local lowered

  lowered="$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]')"
  [[ "${value}" == *"<"*">"* ]] || \
    [[ "${lowered}" == *"todo"* ]] || \
    [[ "${lowered}" == *"sample"* ]] || \
    [[ "${lowered}" == *"fake"* ]] || \
    [[ "${lowered}" == *"placeholder"* ]] || \
    [[ "${lowered}" == *"change-me"* ]] || \
    [[ "${lowered}" == *"changeme"* ]] || \
    [[ "${lowered}" == *"guess"* ]] || \
    [[ "${lowered}" == *"unsigned"* ]] || \
    [[ "${lowered}" == *"browser-state"* ]] || \
    [[ "${lowered}" == *"x-forwarded-"* ]] || \
    [[ "${lowered}" == "forwarded" ]] || \
    [[ "${lowered}" == *"raw-forwarded"* ]]
}

require_env_value() {
  local key="$1"
  local value

  value="$(load_env_value "${key}")"
  if [[ -z "${value}" ]]; then
    fail "Missing required install preflight input: ${key}"
  fi
  if is_placeholder_or_untrusted_value "${value}"; then
    fail "Invalid install preflight input: ${key}"
  fi
}

reject_env_value() {
  local key="$1"
  local value

  value="$(load_env_value "${key}")"
  if [[ -n "${value}" ]]; then
    fail "Direct secret value is not allowed in install preflight input: ${key}"
  fi
}

require_secret_reference() {
  local description="$1"
  local file_key="$2"
  local openbao_key="$3"
  local file_value openbao_value has_reference=0

  file_value="$(load_env_value "${file_key}")"
  openbao_value="$(load_env_value "${openbao_key}")"

  if [[ -n "${file_value}" ]]; then
    has_reference=1
    if is_placeholder_or_untrusted_value "${file_value}"; then
      fail "Invalid secret reference for ${description}: ${file_key}"
    fi
    case "${file_value}" in
      /run/aegisops-secrets/*|/run/secrets/*) ;;
      *) fail "Unsafe secret reference path for ${description}: ${file_key}" ;;
    esac
  fi

  if [[ -n "${openbao_value}" ]]; then
    has_reference=1
    if is_placeholder_or_untrusted_value "${openbao_value}"; then
      fail "Invalid secret reference for ${description}: ${openbao_key}"
    fi
    case "${openbao_value}" in
      secret/*|aegisops/*|kv/*) ;;
      *) fail "Unsafe OpenBao reference for ${description}: ${openbao_key}" ;;
    esac
  fi

  if [[ "${has_reference}" -eq 0 ]]; then
    fail "Missing required secret reference: ${description}"
  fi
}

require_path_under() {
  local key="$1"
  local required_prefix="$2"
  local value

  value="$(load_env_value "${key}")"
  if [[ -z "${value}" ]]; then
    fail "Missing required install preflight input: ${key}"
  fi
  if is_placeholder_or_untrusted_value "${value}"; then
    fail "Invalid install preflight input: ${key}"
  fi
  case "${value}" in
    "${required_prefix}"/*) ;;
    *) fail "Unsafe storage path contract: ${key}" ;;
  esac
}

require_file "${env_file}" "install preflight env file"
require_file "${manifest_path}" "single-customer release bundle inventory"
require_file "${profile_path}" "single-customer deployment profile"
require_file "${runbook_path}" "runbook"
require_file "${smoke_path}" "runtime smoke bundle"
require_file "${network_path}" "network exposure policy"
require_file "${storage_path}" "storage layout policy"
require_file "${compose_path}" "first-boot compose artefact"
require_file "${env_sample_path}" "first-boot env sample"
require_file "${entrypoint_path}" "first-boot entrypoint"
require_dir "${migrations_path}" "control-plane migration artefacts"
require_executable "${smoke_gate_path}" "Phase 37 runtime smoke gate"
require_executable "${rehearsal_verifier_path}" "customer-like rehearsal verifier"
require_executable "${record_chain_verifier_path}" "Phase 37 reviewed record-chain verifier"
require_executable "${restore_verifier_path}" "Phase 37 restore rollback upgrade evidence verifier"

require_phrase "${manifest_path}" "Missing, empty, placeholder, guessed, unsigned, sample, TODO, browser-state, raw forwarded-header, or customer-private custody values are not valid release evidence" "fail-closed release custody language"
require_phrase "${network_path}" "All user-facing UI access must traverse the approved reverse proxy." "approved reverse-proxy access model"
require_phrase "${storage_path}" "Backup storage must not share the same filesystem mount as primary runtime data." "backup separation policy"
require_phrase "${entrypoint_path}" "REQUIRED_MIGRATIONS=" "reviewed migration bootstrap list"
require_phrase "${smoke_gate_path}" "Usage: scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> [--evidence-dir <evidence-dir>]" "runtime smoke gate contract"

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
  fail "Invalid install boot mode: AEGISOPS_CONTROL_PLANE_BOOT_MODE must be first-boot"
fi

case "$(load_env_value AEGISOPS_CONTROL_PLANE_HOST)" in
  0.0.0.0|127.0.0.1|localhost) ;;
  *) fail "Invalid control-plane host boundary: AEGISOPS_CONTROL_PLANE_HOST" ;;
esac

reject_env_value AEGISOPS_CONTROL_PLANE_POSTGRES_DSN
reject_env_value AEGISOPS_OPENBAO_TOKEN

require_secret_reference "PostgreSQL DSN" \
  AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE \
  AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH
require_secret_reference "Wazuh ingest shared secret" \
  AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE \
  AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH
require_secret_reference "Wazuh ingest reverse-proxy secret" \
  AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE \
  AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH
require_secret_reference "protected-surface reverse-proxy secret" \
  AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE \
  AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH
require_secret_reference "admin bootstrap token" \
  AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE \
  AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH
require_secret_reference "break-glass token" \
  AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE \
  AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH

if [[ -n "$(load_env_value AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH)" || \
      -n "$(load_env_value AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH)" || \
      -n "$(load_env_value AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH)" || \
      -n "$(load_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH)" || \
      -n "$(load_env_value AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH)" || \
      -n "$(load_env_value AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH)" ]]; then
  require_env_value AEGISOPS_OPENBAO_ADDRESS
  require_env_value AEGISOPS_OPENBAO_KV_MOUNT
  require_secret_reference "OpenBao token" AEGISOPS_OPENBAO_TOKEN_FILE AEGISOPS_OPENBAO_TOKEN_OPENBAO_PATH
fi

require_secret_reference "ingress TLS certificate chain" AEGISOPS_INGRESS_TLS_CERT_CHAIN_FILE AEGISOPS_INGRESS_TLS_CERT_CHAIN_OPENBAO_PATH
require_secret_reference "ingress TLS private key" AEGISOPS_INGRESS_TLS_PRIVATE_KEY_FILE AEGISOPS_INGRESS_TLS_PRIVATE_KEY_OPENBAO_PATH
require_env_value AEGISOPS_INGRESS_TLS_CERT_CUSTODY_OWNER
require_env_value AEGISOPS_INGRESS_TLS_PRIVATE_KEY_CUSTODIAN
require_env_value AEGISOPS_INGRESS_TLS_EXPIRY_REVIEW_HORIZON
require_env_value AEGISOPS_INGRESS_TLS_RELOAD_EVIDENCE_REF
require_env_value AEGISOPS_INGRESS_APPROVED_PROXY_ARTIFACT_REVISION
require_env_value AEGISOPS_INGRESS_TRUSTED_HEADER_NORMALIZATION

if [[ "$(load_env_value AEGISOPS_INGRESS_TRUSTED_HEADER_NORMALIZATION)" != "approved-reverse-proxy-only" ]]; then
  fail "Invalid proxy custody marker: AEGISOPS_INGRESS_TRUSTED_HEADER_NORMALIZATION"
fi

require_path_under AEGISOPS_INSTALL_STORAGE_ROOT /srv/aegisops
require_path_under AEGISOPS_INSTALL_BACKUP_ROOT /srv/aegisops-backup
require_path_under AEGISOPS_INSTALL_POSTGRES_DATA_PATH /srv/aegisops
require_path_under AEGISOPS_INSTALL_OPENSEARCH_DATA_PATH /srv/aegisops
require_path_under AEGISOPS_INSTALL_N8N_DATA_PATH /srv/aegisops
require_path_under AEGISOPS_INSTALL_POSTGRES_BACKUP_PATH /srv/aegisops-backup
require_path_under AEGISOPS_INSTALL_OPENSEARCH_BACKUP_PATH /srv/aegisops-backup
require_path_under AEGISOPS_INSTALL_N8N_BACKUP_PATH /srv/aegisops-backup
require_env_value AEGISOPS_INSTALL_RESTORE_TARGET_ENVIRONMENT
require_env_value AEGISOPS_INSTALL_BACKUP_CUSTODY_OWNER
require_env_value AEGISOPS_INSTALL_RESTORE_DRY_RUN_EVIDENCE_REF

storage_root="$(load_env_value AEGISOPS_INSTALL_STORAGE_ROOT)"
backup_root="$(load_env_value AEGISOPS_INSTALL_BACKUP_ROOT)"
if [[ "${storage_root}" == "${backup_root}" || "${backup_root}" == "${storage_root}"/* || "${storage_root}" == "${backup_root}"/* ]]; then
  fail "Unsafe storage contract: primary and backup roots must be separate"
fi

if [[ "$(load_env_value AEGISOPS_INSTALL_RESTORE_TARGET_ENVIRONMENT)" == "live" || \
      "$(load_env_value AEGISOPS_INSTALL_RESTORE_TARGET_ENVIRONMENT)" == "production" ]]; then
  fail "Unsafe restore target contract: AEGISOPS_INSTALL_RESTORE_TARGET_ENVIRONMENT"
fi

require_env_value AEGISOPS_INSTALL_RELEASE_IDENTIFIER
require_env_value AEGISOPS_INSTALL_REPOSITORY_REVISION
require_env_value AEGISOPS_INSTALL_REVIEWED_MIGRATION_REVISION
require_env_value AEGISOPS_INSTALL_REQUIRED_MIGRATION_SET
require_env_value AEGISOPS_INSTALL_MIGRATION_BOOTSTRAP_MODE

case "$(load_env_value AEGISOPS_INSTALL_RELEASE_IDENTIFIER)" in
  aegisops-single-customer-*) ;;
  *) fail "Invalid release identifier contract: AEGISOPS_INSTALL_RELEASE_IDENTIFIER" ;;
esac

if [[ "$(load_env_value AEGISOPS_INSTALL_MIGRATION_BOOTSTRAP_MODE)" != "forward-reviewed-only" ]]; then
  fail "Invalid migration bootstrap contract: AEGISOPS_INSTALL_MIGRATION_BOOTSTRAP_MODE"
fi

require_env_value AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT
require_env_value AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY
require_env_value AEGISOPS_SMOKE_READONLY_SUBJECT
require_env_value AEGISOPS_SMOKE_READONLY_IDENTITY
require_env_value AEGISOPS_SMOKE_READONLY_ROLE
require_env_value AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID
require_env_value AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE
require_env_value AEGISOPS_SMOKE_APPROVER_OWNER
require_env_value AEGISOPS_INSTALL_PHASE37_CUSTOMER_LIKE_PREFLIGHT_REF
require_env_value AEGISOPS_INSTALL_PHASE37_RECORD_CHAIN_REF
require_env_value AEGISOPS_INSTALL_PHASE37_RUNTIME_SMOKE_REF
require_env_value AEGISOPS_INSTALL_RESTORE_ROLLBACK_UPGRADE_REF

if [[ "$(load_env_value AEGISOPS_SMOKE_READONLY_ROLE)" != "analyst" && \
      "$(load_env_value AEGISOPS_SMOKE_READONLY_ROLE)" != "approver" && \
      "$(load_env_value AEGISOPS_SMOKE_READONLY_ROLE)" != "platform_admin" ]]; then
  fail "Invalid smoke read-only role: AEGISOPS_SMOKE_READONLY_ROLE"
fi

if [[ "$(load_env_value AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE)" != "notify_identity_owner" ]]; then
  fail "Invalid smoke low-risk action type: AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE"
fi

for optional_key in \
  AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL \
  AEGISOPS_CONTROL_PLANE_N8N_BASE_URL \
  AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL \
  AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL; do
  if [[ -n "$(load_env_value "${optional_key}")" ]]; then
    fail "Optional extension must remain non-blocking for install preflight: ${optional_key}"
  fi
done

macos_home_pattern='/'"Users"'/[^[:space:])>]+'
linux_home_pattern='/'"home"'/[^[:space:])>]+'
windows_home_pattern='[A-Za-z]:\\'"Users"'\\[^[:space:])>]+'
workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"
if grep -Eq "${workstation_local_path_pattern}" "${env_file}" "${manifest_path}" "${profile_path}" "${runbook_path}" "${smoke_path}"; then
  fail "Forbidden install preflight guidance: workstation-local absolute path detected"
fi

echo "Single-customer install preflight contract passed without printing secret values."
