#!/usr/bin/env bash

set -euo pipefail
umask 077

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
load_bootstrap_environment
assert_safe_runtime_root "${AEGISOPS_LAB_RUNTIME_ROOT}"
assert_reviewed_lab_pins
require_command openssl

secret_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/secrets"
cert_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certs"
evidence_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/evidence"
wazuh_source_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/substrates/wazuh-docker"
wazuh_config_dir="${wazuh_source_dir}/single-node/config"
wazuh_manager_config="${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh/manager-ossec.conf"
shuffle_app_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/shuffle/apps"
shuffle_file_dir="${AEGISOPS_LAB_RUNTIME_ROOT}/shuffle/files"
runtime_previously_initialized=false
shuffle_api_workflow_id="67f30000-0000-4000-8000-000000000001"
shuffle_transport_mode="deterministic"
if [[ -f "${RUNTIME_ENV}" ]]; then
  runtime_previously_initialized=true
  for credential in \
    postgres-password \
    wazuh-ingest-shared-secret \
    wazuh-ingest-proxy-secret \
    protected-surface-proxy-secret \
    admin-bootstrap-token \
    break-glass-token \
    wazuh-indexer-password \
    wazuh-api-password \
    shuffle-opensearch-password \
    shuffle-encryption-modifier
  do
    [[ -s "${secret_dir}/${credential}" ]] \
      || fail "initialized runtime is missing credential ${credential}; restore it before reuse, or destroy preserved lab volumes and remove ${RUNTIME_ENV} before reinitializing"
  done
  if grep -Fq 'AEGISOPS_LAB_WAZUH_DASHBOARD_PASSWORD=' "${RUNTIME_ENV}"; then
    [[ -s "${secret_dir}/wazuh-dashboard-password" ]] \
      || fail "initialized runtime is missing credential wazuh-dashboard-password; restore it before reuse, or destroy preserved lab volumes and remove ${RUNTIME_ENV} before reinitializing"
  fi
  if grep -Fq 'AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID=' "${RUNTIME_ENV}"; then
    for credential in shuffle-admin-password shuffle-api-key; do
      [[ -s "${secret_dir}/${credential}" ]] \
        || fail "initialized runtime is missing credential ${credential}; restore it before reuse, or destroy preserved lab volumes and remove ${RUNTIME_ENV} before reinitializing"
    done
    existing_shuffle_workflow_id="$(
      awk -F'"' '
        index($0, "AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID=") == 1 {
          print $2
          exit
        }
      ' "${RUNTIME_ENV}"
    )"
    existing_shuffle_transport_mode="$(
      awk -F'"' '
        index($0, "AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE=") == 1 {
          print $2
          exit
        }
      ' "${RUNTIME_ENV}"
    )"
    if [[ "${existing_shuffle_workflow_id}" =~ ^[0-9a-fA-F-]{36}$ ]]; then
      shuffle_api_workflow_id="${existing_shuffle_workflow_id}"
    fi
    if [[
      "${existing_shuffle_transport_mode}" == "real_http" &&
        "${existing_shuffle_workflow_id}" =~ ^[0-9a-fA-F-]{36}$ &&
        "$(<"${secret_dir}/shuffle-api-key")" != bootstrap-pending-*
    ]]; then
      shuffle_transport_mode="real_http"
    fi
  fi
else
  assert_no_preserved_phase67_volumes
fi

mkdir -p \
  "${secret_dir}" \
  "${cert_dir}" \
  "${evidence_dir}" \
  "$(dirname "${wazuh_manager_config}")" \
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
  if [[ -z "${existing}" ]]; then
    printf 'Aa1!%sZz9!\n' "$(openssl rand -hex 24)" >"${path}"
  elif [[ "${runtime_previously_initialized}" == false && "${existing}" =~ ^[0-9a-f]{48}$ ]]; then
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
write_strong_secret_once "${secret_dir}/wazuh-dashboard-password"
write_strong_secret_once "${secret_dir}/shuffle-opensearch-password"
write_secret_once "${secret_dir}/shuffle-encryption-modifier"
write_strong_secret_once "${secret_dir}/shuffle-admin-password"
if [[ ! -s "${secret_dir}/shuffle-api-key" ]]; then
  printf 'bootstrap-pending-%s\n' "$(openssl rand -hex 24)" \
    >"${secret_dir}/shuffle-api-key"
fi
chmod 600 "${secret_dir}/shuffle-api-key"

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
    -addext "subjectAltName=DNS:localhost,DNS:proxy,DNS:wazuh.localhost,DNS:shuffle.localhost,IP:127.0.0.1" \
    >/dev/null 2>&1; then
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
  certificate_sans="$(
    openssl x509 \
      -in "${cert_dir}/lab.crt" \
      -noout \
      -text 2>/dev/null |
      awk '
        /X509v3 Subject Alternative Name:/ {
          capture_sans = 1
          next
        }
        capture_sans && /^[[:space:]]+X509v3 / {
          exit
        }
        capture_sans && /Signature Algorithm:/ {
          exit
        }
        capture_sans && !/^[[:space:]]+/ {
          exit
        }
        capture_sans {
          sub(/^[[:space:]]+/, "")
          printf "%s", $0
        }
      '
  )"
  certificate_san_entries="$(
    tr ',' '\n' <<<"${certificate_sans}" |
      sed 's/^[[:space:]]*//; s/[[:space:]]*$//'
  )"
  for required_san in \
    "DNS:localhost" \
    "DNS:proxy" \
    "DNS:wazuh.localhost" \
    "DNS:shuffle.localhost" \
    "IP Address:127.0.0.1"
  do
    if ! grep -Fxq "${required_san}" <<<"${certificate_san_entries}"; then
      rotate_proxy_certificate=true
    fi
  done
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
  if [[
    "${proxy_certificate_state_existed}" == "true" ||
      "${runtime_previously_initialized}" == "true"
  ]]; then
    proxy_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required"
    : >"${proxy_recreate_marker}"
    chmod 600 "${proxy_recreate_marker}"
  fi
fi
chmod 600 "${cert_dir}/lab.key" "${cert_dir}/lab.crt"

proxy_runtime_secret="$(<"${secret_dir}/protected-surface-proxy-secret")"
[[ "${proxy_runtime_secret}" =~ ^[0-9a-f]{64}$ ]] \
  || fail "protected-surface proxy secret must be the 64-character hexadecimal value generated by init.sh"
proxy_runtime_auth="${cert_dir}/runtime-auth.conf"
proxy_runtime_auth_staging="$(mktemp "${cert_dir}/.runtime-auth.XXXXXX")"
cat >"${proxy_runtime_auth_staging}" <<EOF
proxy_set_header Host \$host;
proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header X-AegisOps-Proxy-Secret "${proxy_runtime_secret}";
proxy_set_header X-AegisOps-Proxy-Service-Account "svc-aegisops-phase67-proxy";
proxy_set_header X-AegisOps-Authenticated-IdP "phase67-lab";
proxy_set_header X-AegisOps-Authenticated-Subject "phase67-lab-platform-admin";
proxy_set_header X-AegisOps-Authenticated-Identity "phase67-lab-platform-admin";
proxy_set_header X-AegisOps-Authenticated-Role "platform_admin";
EOF
chmod 600 "${proxy_runtime_auth_staging}"
if ! cmp -s "${proxy_runtime_auth_staging}" "${proxy_runtime_auth}"; then
  if [[ -e "${proxy_runtime_auth}" || "${runtime_previously_initialized}" == "true" ]]; then
    proxy_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required"
    : >"${proxy_recreate_marker}"
    chmod 600 "${proxy_recreate_marker}"
  fi
  mv "${proxy_runtime_auth_staging}" "${proxy_runtime_auth}"
else
  rm -f "${proxy_runtime_auth_staging}"
fi
chmod 600 "${proxy_runtime_auth}"

wazuh_ingest_proxy_secret="$(<"${secret_dir}/wazuh-ingest-proxy-secret")"
[[ "${wazuh_ingest_proxy_secret}" =~ ^[0-9a-f]{64}$ ]] \
  || fail "Wazuh intake proxy secret must be the 64-character hexadecimal value generated by init.sh"
proxy_wazuh_intake_auth="${cert_dir}/wazuh-intake-auth.conf"
proxy_wazuh_intake_auth_staging="$(
  mktemp "${cert_dir}/.wazuh-intake-auth.XXXXXX"
)"
cat >"${proxy_wazuh_intake_auth_staging}" <<EOF
proxy_set_header Host \$host;
proxy_set_header X-Forwarded-For \$remote_addr;
proxy_set_header X-Forwarded-Proto https;
proxy_set_header X-AegisOps-Proxy-Secret "${wazuh_ingest_proxy_secret}";
proxy_set_header X-AegisOps-Source-Family "wazuh_detection";
proxy_set_header X-AegisOps-Proxy-Service-Account "";
proxy_set_header X-AegisOps-Authenticated-IdP "";
proxy_set_header X-AegisOps-Authenticated-Subject "";
proxy_set_header X-AegisOps-Authenticated-Identity "";
proxy_set_header X-AegisOps-Authenticated-Role "";
EOF
chmod 600 "${proxy_wazuh_intake_auth_staging}"
if ! cmp -s "${proxy_wazuh_intake_auth_staging}" "${proxy_wazuh_intake_auth}"; then
  if [[ -e "${proxy_wazuh_intake_auth}" || "${runtime_previously_initialized}" == "true" ]]; then
    proxy_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required"
    : >"${proxy_recreate_marker}"
    chmod 600 "${proxy_recreate_marker}"
  fi
  mv "${proxy_wazuh_intake_auth_staging}" "${proxy_wazuh_intake_auth}"
else
  rm -f "${proxy_wazuh_intake_auth_staging}"
fi
chmod 600 "${proxy_wazuh_intake_auth}"

wazuh_root_ca="${wazuh_config_dir}/wazuh_indexer_ssl_certs/root-ca.pem"
proxy_wazuh_trust="${cert_dir}/wazuh-upstream-root-ca.pem"
desired_proxy_wazuh_trust="${cert_dir}/lab.crt"
if [[ -e "${wazuh_root_ca}" ]]; then
  [[ -s "${wazuh_root_ca}" ]] \
    || fail "Wazuh root CA is empty; run prepare-substrates.sh before starting Wazuh"
  openssl x509 -in "${wazuh_root_ca}" -noout >/dev/null 2>&1 \
    || fail "Wazuh root CA is invalid; run prepare-substrates.sh before starting Wazuh"
  openssl x509 -checkend 604800 -noout -in "${wazuh_root_ca}" >/dev/null 2>&1 \
    || fail "Wazuh root CA expires within seven days; run prepare-substrates.sh before starting Wazuh"
  desired_proxy_wazuh_trust="${wazuh_root_ca}"
fi
if ! cmp -s "${desired_proxy_wazuh_trust}" "${proxy_wazuh_trust}"; then
  if [[ -e "${proxy_wazuh_trust}" || "${runtime_previously_initialized}" == "true" ]]; then
    proxy_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required"
    : >"${proxy_recreate_marker}"
    chmod 600 "${proxy_recreate_marker}"
  fi
  proxy_wazuh_trust_staging="$(mktemp "${cert_dir}/.wazuh-upstream-root-ca.XXXXXX")"
  cp "${desired_proxy_wazuh_trust}" "${proxy_wazuh_trust_staging}"
  chmod 600 "${proxy_wazuh_trust_staging}"
  mv "${proxy_wazuh_trust_staging}" "${proxy_wazuh_trust}"
fi
chmod 600 "${proxy_wazuh_trust}"

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
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_MANAGER_CONFIG "${wazuh_manager_config}"
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
  write_runtime_env_assignment AEGISOPS_LAB_MIN_CPUS "${AEGISOPS_LAB_MIN_CPUS}"
  write_runtime_env_assignment AEGISOPS_LAB_MIN_MEMORY_GIB "${AEGISOPS_LAB_MIN_MEMORY_GIB}"
  write_runtime_env_assignment AEGISOPS_LAB_MIN_DISK_GIB "${AEGISOPS_LAB_MIN_DISK_GIB}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_PLATFORM "${AEGISOPS_LAB_WAZUH_PLATFORM}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_PLATFORM "${AEGISOPS_LAB_SHUFFLE_PLATFORM}"
  write_runtime_env_assignment AEGISOPS_LAB_ALLOW_EMULATION "${AEGISOPS_LAB_ALLOW_EMULATION}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_VERSION "${AEGISOPS_LAB_WAZUH_VERSION}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_DOCKER_COMMIT "${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_VERSION "${AEGISOPS_LAB_SHUFFLE_VERSION}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID "${shuffle_api_workflow_id}"
  write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE "${shuffle_transport_mode}"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_INDEXER_PASSWORD "$(<"${secret_dir}/wazuh-indexer-password")"
  write_runtime_env_assignment AEGISOPS_LAB_WAZUH_API_PASSWORD "$(<"${secret_dir}/wazuh-api-password")"
  write_runtime_env_assignment \
    AEGISOPS_LAB_WAZUH_DASHBOARD_PASSWORD \
    "$(<"${secret_dir}/wazuh-dashboard-password")"
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
  echo "Proxy certificate, trust bundle, or runtime identity changed; the next up.sh run will force service recreation."
fi
echo "Next: ${LAB_DIR}/preflight.sh --write-evidence"
