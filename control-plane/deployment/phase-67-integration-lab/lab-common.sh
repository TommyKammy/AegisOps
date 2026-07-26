#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${LAB_DIR}/../../.." && pwd)"
COMPOSE_FILE="${LAB_DIR}/docker-compose.yml"
BOOTSTRAP_ENV="${AEGISOPS_LAB_BOOTSTRAP_ENV:-${LAB_DIR}/bootstrap.env.sample}"

fail() {
  echo "BLOCKED: $*" >&2
  exit 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || fail "required command is unavailable: $1"
}

load_bootstrap_environment() {
  [[ -f "${BOOTSTRAP_ENV}" ]] || fail "bootstrap environment file not found: ${BOOTSTRAP_ENV}"

  # shellcheck disable=SC1090
  source "${BOOTSTRAP_ENV}"
  : "${AEGISOPS_LAB_RUNTIME_ROOT:?AEGISOPS_LAB_RUNTIME_ROOT is required}"

  AEGISOPS_LAB_RUNTIME_ROOT="${AEGISOPS_LAB_RUNTIME_ROOT/#\~/${HOME}}"
  RUNTIME_ENV="${AEGISOPS_LAB_RUNTIME_ENV:-${AEGISOPS_LAB_RUNTIME_ROOT}/runtime.env}"
  export AEGISOPS_LAB_RUNTIME_ROOT
  export RUNTIME_ENV
}

load_lab_environment() {
  load_bootstrap_environment
  if [[ -f "${RUNTIME_ENV}" ]]; then
    # shellcheck disable=SC1090
    source "${RUNTIME_ENV}"
  fi

  export AEGISOPS_LAB_RUNTIME_ROOT
  export RUNTIME_ENV
}

require_runtime_configuration() {
  load_lab_environment
  [[ -f "${RUNTIME_ENV}" ]] || fail "runtime environment not initialized; run ${LAB_DIR}/init.sh"
}

require_runtime_environment() {
  require_runtime_configuration
  [[ -d "${AEGISOPS_LAB_SECRET_DIR:-}" ]] || fail "runtime secret directory is missing; rerun ${LAB_DIR}/init.sh"
}

assert_reviewed_lab_pins() {
  [[ "${AEGISOPS_LAB_WAZUH_VERSION:-}" == "4.14.6" ]] \
    || fail "AEGISOPS_LAB_WAZUH_VERSION must remain at reviewed version 4.14.6"
  [[ "${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT:-}" == "499184cbeb44fc1086791d11ad4b9bdcb77a9bb9" ]] \
    || fail "AEGISOPS_LAB_WAZUH_DOCKER_COMMIT must remain at the reviewed Wazuh 4.14.6 commit"
  [[ "${AEGISOPS_LAB_SHUFFLE_VERSION:-}" == "2.2.1" ]] \
    || fail "AEGISOPS_LAB_SHUFFLE_VERSION must remain at reviewed version 2.2.1"
  [[ "${AEGISOPS_LAB_WAZUH_PLATFORM:-}" == "linux/arm64" ]] \
    || fail "AEGISOPS_LAB_WAZUH_PLATFORM must remain explicit linux/arm64"
  [[ "${AEGISOPS_LAB_SHUFFLE_PLATFORM:-}" == "linux/amd64" ]] \
    || fail "AEGISOPS_LAB_SHUFFLE_PLATFORM must remain explicit linux/amd64"
}

assert_reviewed_wazuh_checkout() {
  local source_dir="$1"
  local expected_commit="$2"
  local managed_relative_path="$3"
  local actual_commit

  [[ -d "${source_dir}/.git" ]] \
    || fail "Wazuh substrate path is not a Git checkout: ${source_dir}"
  actual_commit="$(git -C "${source_dir}" rev-parse HEAD)"
  [[ "${actual_commit}" == "${expected_commit}" ]] \
    || fail "Wazuh substrate commit is ${actual_commit}; expected ${expected_commit}"
  if ! git -C "${source_dir}" diff --quiet HEAD -- \
    . ":(exclude)${managed_relative_path}"; then
    fail "Wazuh substrate has unreviewed tracked changes outside ${managed_relative_path}"
  fi
}

validate_wazuh_certificate_bundle() {
  local cert_dir="$1"
  local certificate
  local certificate_digest
  local key
  local key_digest
  local required_files=(
    root-ca.pem
    root-ca-manager.pem
    wazuh.indexer-key.pem
    wazuh.indexer.pem
    admin.pem
    admin-key.pem
    wazuh.manager.pem
    wazuh.manager-key.pem
    wazuh.dashboard.pem
    wazuh.dashboard-key.pem
  )

  for certificate in "${required_files[@]}"; do
    [[ -s "${cert_dir}/${certificate}" ]] || return 1
  done
  for certificate in \
    root-ca.pem \
    root-ca-manager.pem \
    wazuh.indexer.pem \
    admin.pem \
    wazuh.manager.pem \
    wazuh.dashboard.pem
  do
    openssl x509 -checkend 604800 -noout -in "${cert_dir}/${certificate}" \
      >/dev/null 2>&1 || return 1
  done
  for key in \
    wazuh.indexer-key.pem \
    admin-key.pem \
    wazuh.manager-key.pem \
    wazuh.dashboard-key.pem
  do
    openssl pkey -in "${cert_dir}/${key}" -noout >/dev/null 2>&1 || return 1
  done

  while IFS='|' read -r certificate key; do
    certificate_digest="$(
      openssl x509 -in "${cert_dir}/${certificate}" -pubkey -noout 2>/dev/null |
        openssl pkey -pubin -outform DER 2>/dev/null |
        openssl sha256
    )" || return 1
    key_digest="$(
      openssl pkey -in "${cert_dir}/${key}" -pubout -outform DER 2>/dev/null |
        openssl sha256
    )" || return 1
    [[ "${certificate_digest}" == "${key_digest}" ]] || return 1
  done <<'EOF'
wazuh.indexer.pem|wazuh.indexer-key.pem
admin.pem|admin-key.pem
wazuh.manager.pem|wazuh.manager-key.pem
wazuh.dashboard.pem|wazuh.dashboard-key.pem
EOF

  openssl verify -CAfile "${cert_dir}/root-ca.pem" "${cert_dir}/root-ca.pem" \
    >/dev/null 2>&1 || return 1
  openssl verify -CAfile "${cert_dir}/root-ca-manager.pem" "${cert_dir}/root-ca-manager.pem" \
    >/dev/null 2>&1 || return 1
  for certificate in wazuh.indexer.pem admin.pem wazuh.dashboard.pem; do
    openssl verify -CAfile "${cert_dir}/root-ca.pem" "${cert_dir}/${certificate}" \
      >/dev/null 2>&1 || return 1
  done
  openssl verify \
    -CAfile "${cert_dir}/root-ca-manager.pem" \
    "${cert_dir}/wazuh.manager.pem" \
    >/dev/null 2>&1 || return 1
}

assert_safe_runtime_root() {
  local candidate="${1:-}"

  [[ -n "${candidate}" ]] || fail "runtime root is empty"
  [[ "${candidate}" == /* ]] || fail "runtime root must be absolute: ${candidate}"
  [[ "${candidate}" != "/" && "${candidate}" != "${HOME}" && "${candidate}" != "${REPO_ROOT}" ]] \
    || fail "refusing unsafe runtime root: ${candidate}"
  case "${candidate}" in
    "${HOME}"/.local/share/aegisops/*) ;;
    *) fail "runtime root must remain below ${HOME}/.local/share/aegisops/" ;;
  esac
}

docker_lab() {
  : "${AEGISOPS_LAB_DOCKER_CONTEXT:?AEGISOPS_LAB_DOCKER_CONTEXT is required}"
  docker --context "${AEGISOPS_LAB_DOCKER_CONTEXT}" "$@"
}

compose_lab() {
  : "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:?AEGISOPS_LAB_COMPOSE_PROJECT_NAME is required}"
  docker_lab compose \
    --project-name "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}" \
    --env-file "${RUNTIME_ENV}" \
    --file "${COMPOSE_FILE}" \
    "$@"
}

compose_scope() {
  local scope="${1:-core}"
  shift

  case "${scope}" in
    core) compose_lab "$@" ;;
    wazuh) compose_lab --profile wazuh "$@" ;;
    shuffle) compose_lab --profile shuffle "$@" ;;
    full) compose_lab --profile wazuh --profile shuffle "$@" ;;
    *) fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full" ;;
  esac
}

selected_port_names() {
  local scope="${1:-core}"

  case "${scope}" in
    core)
      printf '%s\n' PROXY
      ;;
    wazuh)
      printf '%s\n' PROXY WAZUH_DASHBOARD
      ;;
    shuffle)
      printf '%s\n' PROXY SHUFFLE_FRONTEND
      ;;
    full)
      printf '%s\n' PROXY WAZUH_DASHBOARD SHUFFLE_FRONTEND
      ;;
    *)
      fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full"
      ;;
  esac
}

selected_address_names() {
  local scope="${1:-core}"

  printf '%s\n' PROXY CONTROL_PLANE POSTGRES
  case "${scope}" in
    core) ;;
    wazuh)
      printf '%s\n' WAZUH_MANAGER WAZUH_INDEXER WAZUH_DASHBOARD
      ;;
    shuffle)
      printf '%s\n' SHUFFLE_BACKEND SHUFFLE_OPENSEARCH SHUFFLE_FRONTEND
      ;;
    full)
      printf '%s\n' \
        WAZUH_MANAGER \
        WAZUH_INDEXER \
        WAZUH_DASHBOARD \
        SHUFFLE_BACKEND \
        SHUFFLE_OPENSEARCH \
        SHUFFLE_FRONTEND
      ;;
    *) fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full" ;;
  esac
}

assert_unique_selected_ports() {
  local scope="${1:-core}"
  local selected_ports=" "
  local port_name
  local variable
  local port

  while IFS= read -r port_name; do
    variable="AEGISOPS_LAB_${port_name}_PORT"
    port="${!variable}"
    [[ "${port}" =~ ^[0-9]+$ && "${port}" -ge 1 && "${port}" -le 65535 ]] \
      || fail "${variable} must be an integer from 1 through 65535"
    case "${selected_ports}" in
      *" ${port} "*)
        fail "selected scope '${scope}' assigns duplicate host port ${port}"
        ;;
    esac
    selected_ports="${selected_ports}${port} "
  done < <(selected_port_names "${scope}")
}

write_evidence_header() {
  local output="$1"
  {
    printf 'recorded_at_utc=%s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    printf 'repository_commit=%s\n' "$(git -C "${REPO_ROOT}" rev-parse HEAD 2>/dev/null || printf unknown)"
  } >"${output}"
}
