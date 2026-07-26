#!/usr/bin/env bash

set -euo pipefail
umask 077

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
load_bootstrap_environment
assert_safe_runtime_root "${AEGISOPS_LAB_RUNTIME_ROOT}"
require_command openssl

secret_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/secrets"
cert_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certs"
evidence_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/evidence"
wazuh_source_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/substrates/wazuh-docker"
wazuh_config_dir="${wazuh_source_dir}/single-node/config"
shuffle_app_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/shuffle/apps"
shuffle_file_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/shuffle/files"

mkdir -p \
  "${secret_dir}" \
  "${cert_dir}" \
  "${evidence_dir}" \
  "${shuffle_app_dir}" \
  "${shuffle_file_dir}"

write_secret_once() {
  local path="$1"
  local bytes="${2:-32}"

  if [[ ! -s "${path}" ]]; then
    openssl rand -hex "${bytes}" >"${path}"
  fi
  chmod 600 "${path}"
}

write_strong_secret_once() {
  local path="$1"
  local existing=""

  if [[ -s "${path}" ]]; then
    existing="$(<"${path}")"
  fi
  if [[ -z "${existing}" || "${existing}" =~ ^[0-9a-f]{48}$ ]]; then
    printf 'Aa1!%sZz9!\n' "$(openssl rand -hex 24)" >"${path}"
  fi
  chmod 600 "${path}"
}

write_secret_once "${secret_dir}/postgres-password" 24
write_secret_once "${secret_dir}/wazuh-ingest-shared-secret"
write_secret_once "${secret_dir}/wazuh-ingest-proxy-secret"
write_secret_once "${secret_dir}/protected-surface-proxy-secret"
write_secret_once "${secret_dir}/admin-bootstrap-token"
write_secret_once "${secret_dir}/break-glass-token"
write_secret_once "${secret_dir}/wazuh-indexer-password" 24
write_secret_once "${secret_dir}/wazuh-api-password" 24
write_strong_secret_once "${secret_dir}/shuffle-opensearch-password"
write_secret_once "${secret_dir}/shuffle-encryption-modifier"

postgres_password="$(<"${secret_dir}/postgres-password")"
printf 'postgresql://aegisops_control_plane:%s@postgres:5432/aegisops_control_plane\n' \
  "${postgres_password}" >"${secret_dir}/control-plane-postgres-dsn"
chmod 600 "${secret_dir}/control-plane-postgres-dsn"

generate_proxy_certificate() {
  local staging_dir

  staging_dir="$(mktemp -d "${cert_dir}/.proxy-certificate.XXXXXX")"
  if ! openssl req -x509 -newkey rsa:3072 -sha256 -nodes \
    -keyout "${staging_dir}/lab.key" \
    -out "${staging_dir}/lab.crt" \
    -days 30 \
    -subj "/CN=localhost" \
    -addext "subjectAltName=DNS:localhost,IP:127.0.0.1" >/dev/null 2>&1; then
    rm -rf "${staging_dir}"
    fail "failed to generate the proxy TLS certificate"
  fi
  chmod 600 "${staging_dir}/lab.key" "${staging_dir}/lab.crt"
  mv "${staging_dir}/lab.key" "${cert_dir}/lab.key"
  mv "${staging_dir}/lab.crt" "${cert_dir}/lab.crt"
  rmdir "${staging_dir}"
}

rotate_proxy_certificate=false
proxy_certificate_state_existed=false
if [[ -e "${cert_dir}/lab.key" || -e "${cert_dir}/lab.crt" ]]; then
  proxy_certificate_state_existed=true
  [[ -s "${cert_dir}/lab.key" && -s "${cert_dir}/lab.crt" ]] \
    || fail "proxy TLS state is partial; restore or remove both lab.key and lab.crt before rerunning init"
  openssl pkey -in "${cert_dir}/lab.key" -noout >/dev/null 2>&1 \
    || fail "proxy TLS private key is invalid; restore or remove the certificate pair before rerunning init"
  openssl x509 -in "${cert_dir}/lab.crt" -noout >/dev/null 2>&1 \
    || fail "proxy TLS certificate is invalid; restore or remove the certificate pair before rerunning init"
  key_public_digest="$(
    openssl pkey -in "${cert_dir}/lab.key" -pubout -outform DER 2>/dev/null |
      openssl sha256
  )"
  certificate_public_digest="$(
    openssl x509 -in "${cert_dir}/lab.crt" -pubkey -noout 2>/dev/null |
      openssl pkey -pubin -outform DER 2>/dev/null |
      openssl sha256
  )"
  [[ "${key_public_digest}" == "${certificate_public_digest}" ]] \
    || fail "proxy TLS key and certificate do not match; restore or remove the pair before rerunning init"
  if ! openssl x509 -checkend 604800 -noout -in "${cert_dir}/lab.crt" >/dev/null 2>&1; then
    rotate_proxy_certificate=true
  fi
else
  rotate_proxy_certificate=true
fi
if [[ "${rotate_proxy_certificate}" == "true" ]]; then
  generate_proxy_certificate
  if [[ "${proxy_certificate_state_existed}" == "true" ]]; then
    proxy_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required"
    : >"${proxy_recreate_marker}"
    chmod 600 "${proxy_recreate_marker}"
  fi
fi
chmod 600 "${cert_dir}/lab.key" "${cert_dir}/lab.crt"

write_runtime_env_assignment() {
  local name="$1"
  local value="$2"

  [[ "${name}" =~ ^[A-Z0-9_]+$ ]] || fail "invalid runtime environment variable name: ${name}"
  [[ "${value}" != *$'\n'* && "${value}" != *'$'* && "${value}" != *'`'* ]] \
    || fail "${name} contains a value that cannot be safely serialized"
  value="${value//\\/\\\\}"
  value="${value//\"/\\\"}"
  printf '%s="%s"\n' "${name}" "${value}"
}

runtime_env_staging="$(mktemp "${RUNTIME_ENV}.tmp.XXXXXX")"
cleanup_runtime_env_staging() {
  [[ -z "${runtime_env_staging:-}" ]] || rm -f "${runtime_env_staging}"
}
trap cleanup_runtime_env_staging EXIT
{
  echo "# Generated by Phase 67.1 init.sh. Keep this file untracked."
  write_runtime_env_assignment AEGISOPS_LAB_COLIMA_PROFILE "${AEGISOPS_LAB_COLIMA_PROFILE}"
  write_runtime_env_assignment AEGISOPS_LAB_DOCKER_CONTEXT "${AEGISOPS_LAB_DOCKER_CONTEXT}"
  write_runtime_env_assignment AEGISOPS_LAB_COMPOSE_PROJECT_NAME "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}"
  write_runtime_env_assignment AEGISOPS_LAB_RUNTIME_ROOT "${AEGISOPS_LAB_RUNTIME_ROOT}"
  write_runtime_env_assignment AEGISOPS_LAB_SECRET_DIR "${secret_dir}"
  write_runtime_env_assignment AEGISOPS_LAB_PROXY_CERT_DIR "${cert_dir}"
  write_runtime_env_assignment AEGISOPS_LAB_EVIDENCE_DIR "${evidence_dir}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_SOURCE_DIR "${wazuh_source_dir}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_CONFIG_DIR "${wazuh_config_dir}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_APP_DIR "${shuffle_app_dir}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_FILE_DIR "${shuffle_file_dir}"
  write_runtime_env_assignment AEGISOPS_LAB_NETWORK_SUBNET "${AEGISOPS_LAB_NETWORK_SUBNET}"
  write_runtime_env_assignment AEGISOPS_LAB_PROXY_IPV4 "${AEGISOPS_LAB_PROXY_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_CONTROL_PLANE_IPV4 "${AEGISOPS_LAB_CONTROL_PLANE_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_POSTGRES_IPV4 "${AEGISOPS_LAB_POSTGRES_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_MANAGER_IPV4 "${AEGISOPS_LAB_WAZUH_MANAGER_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_INDEXER_IPV4 "${AEGISOPS_LAB_WAZUH_INDEXER_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_DASHBOARD_IPV4 "${AEGISOPS_LAB_WAZUH_DASHBOARD_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_BACKEND_IPV4 "${AEGISOPS_LAB_SHUFFLE_BACKEND_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_OPENSEARCH_IPV4 "${AEGISOPS_LAB_SHUFFLE_OPENSEARCH_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_FRONTEND_IPV4 "${AEGISOPS_LAB_SHUFFLE_FRONTEND_IPV4}"
  write_runtime_env_assignment AEGISOPS_LAB_PROXY_PORT "${AEGISOPS_LAB_PROXY_PORT}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_DASHBOARD_PORT "${AEGISOPS_LAB_WAZUH_DASHBOARD_PORT}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_FRONTEND_PORT "${AEGISOPS_LAB_SHUFFLE_FRONTEND_PORT}"
  write_runtime_env_assignment AEGISOPS_LAB_MIN_CPUS "${AEGISOPS_LAB_MIN_CPUS}"
  write_runtime_env_assignment AEGISOPS_LAB_MIN_MEMORY_GIB "${AEGISOPS_LAB_MIN_MEMORY_GIB}"
  write_runtime_env_assignment AEGISOPS_LAB_MIN_DISK_GIB "${AEGISOPS_LAB_MIN_DISK_GIB}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_PLATFORM "${AEGISOPS_LAB_WAZUH_PLATFORM}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_PLATFORM "${AEGISOPS_LAB_SHUFFLE_PLATFORM}"
  write_runtime_env_assignment AEGISOPS_LAB_ALLOW_EMULATION "${AEGISOPS_LAB_ALLOW_EMULATION}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_VERSION "${AEGISOPS_LAB_WAZUH_VERSION}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_DOCKER_COMMIT "${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_VERSION "${AEGISOPS_LAB_SHUFFLE_VERSION}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_INDEXER_PASSWORD "$(<"${secret_dir}/wazuh-indexer-password")"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_API_PASSWORD "$(<"${secret_dir}/wazuh-api-password")"
  write_runtime_env_assignment \
    AEGISOPS_LAB_SHUFFLE_OPENSEARCH_PASSWORD \
    "$(<"${secret_dir}/shuffle-opensearch-password")"
  write_runtime_env_assignment \
    AEGISOPS_LAB_SHUFFLE_ENCRYPTION_MODIFIER \
    "$(<"${secret_dir}/shuffle-encryption-modifier")"
} >"${runtime_env_staging}"
chmod 600 "${runtime_env_staging}"
mv "${runtime_env_staging}" "${RUNTIME_ENV}"
runtime_env_staging=""
trap - EXIT

echo "Initialized Phase 67.1 runtime at ${AEGISOPS_LAB_RUNTIME_ROOT}"
if [[ -f "${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required" ]]; then
  echo "Proxy certificate rotated; the next up.sh run will force service recreation."
fi
echo "Next: ${LAB_DIR}/preflight.sh --write-evidence"
