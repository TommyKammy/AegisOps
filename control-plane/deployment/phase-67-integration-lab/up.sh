#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

scope="${1:-core}"
[[ "$#" -le 1 ]] || fail "usage: $0 [core|wazuh|shuffle|full]"
require_runtime_environment

case "${scope}" in
  core) ;;
  wazuh|shuffle|full) ;;
  *) fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full" ;;
esac

assert_phase67_compose_project_ownership
assert_no_running_excluded_services "${scope}"
"${LAB_DIR}/preflight.sh" --scope "${scope}" --write-evidence

if [[ "${scope}" == "wazuh" || "${scope}" == "full" ]]; then
  require_command git
  require_command openssl
  wazuh_internal_users_relative_path="single-node/config/wazuh_indexer/internal_users.yml"
  wazuh_internal_users="${AEGISOPS_LAB_WAZUH_SOURCE_DIR}/${wazuh_internal_users_relative_path}"
  assert_reviewed_wazuh_checkout \
    "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}" \
    "${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT}" \
    "${wazuh_internal_users_relative_path}"
  assert_reviewed_file_digest \
    "${wazuh_internal_users}" \
    "${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-internal-users.sha256"
  : "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG:?AEGISOPS_LAB_WAZUH_MANAGER_CONFIG is required}"
  assert_reviewed_file_digest \
    "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}" \
    "${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-manager-config.sha256"
  manager_config_relative_path="single-node/config/wazuh_cluster/wazuh_manager.conf"
  manager_config_fragment="${LAB_DIR}/wazuh/ossec-integration.xml"
  expected_manager_config="$(
    mktemp "${AEGISOPS_LAB_RUNTIME_ROOT}/expected-manager-ossec.XXXXXX"
  )"
  cleanup_expected_manager_config() {
    rm -f "${expected_manager_config}"
  }
  trap cleanup_expected_manager_config EXIT
  {
    git -C "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}" \
      show "HEAD:${manager_config_relative_path}"
    printf '\n'
    cat "${manager_config_fragment}"
    printf '\n'
  } >"${expected_manager_config}"
  cmp -s "${expected_manager_config}" "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}" \
    || fail "Wazuh manager config does not match its reviewed source fragment; run ${LAB_DIR}/prepare-substrates.sh"
  rm -f "${expected_manager_config}"
  trap - EXIT
  wazuh_integration_digest="$(
    {
      printf 'manager-entrypoint.sh\0'
      cat "${LAB_DIR}/wazuh/manager-entrypoint.sh"
      printf '\0custom-aegisops\0'
      cat "${LAB_DIR}/wazuh/custom-aegisops"
      printf '\0aegisops_wazuh_integrator.py\0'
      cat "${LAB_DIR}/wazuh/aegisops_wazuh_integrator.py"
      printf '\0ossec-integration.xml\0'
      cat "${manager_config_fragment}"
      printf '\0proxy-ca.crt\0'
      cat "${AEGISOPS_LAB_PROXY_CERT_DIR}/lab.crt"
    } |
      openssl dgst -sha256 -r |
      awk '{print $1}'
  )"
  [[ "${wazuh_integration_digest}" =~ ^[0-9a-f]{64}$ ]] \
    || fail "could not calculate the tracked Wazuh integration digest"
  validate_wazuh_certificate_bundle \
    "${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/wazuh_indexer_ssl_certs" \
    || fail "Wazuh substrate certificate bundle is invalid; run ${LAB_DIR}/prepare-substrates.sh"
  cmp -s \
    "${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/wazuh_indexer_ssl_certs/root-ca.pem" \
    "${AEGISOPS_LAB_PROXY_CERT_DIR}/wazuh-upstream-root-ca.pem" \
    || fail "proxy Wazuh trust certificate is stale; run ${LAB_DIR}/prepare-substrates.sh"
fi

compose_scope "${scope}" config --quiet
proxy_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required"
proxy_config_state="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-config.sha256"
wazuh_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-certificate-recreate-required"
wazuh_integration_state="${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-integration-artifacts.sha256"
require_command openssl
proxy_config_digest="$(
  {
    printf 'nginx.conf\0'
    cat "${LAB_DIR}/config/nginx.conf"
    printf '\0control-plane.conf\0'
    cat "${LAB_DIR}/config/control-plane.conf"
  } |
    openssl dgst -sha256 -r |
    awk '{print $1}'
)"
[[ "${proxy_config_digest}" =~ ^[0-9a-f]{64}$ ]] \
  || fail "could not calculate the tracked proxy configuration digest"
force_recreate=false
if [[ -f "${proxy_recreate_marker}" ]]; then
  force_recreate=true
fi
if [[ ! -s "${proxy_config_state}" ]] ||
  [[ "$(<"${proxy_config_state}")" != "${proxy_config_digest}" ]]; then
  force_recreate=true
fi
if [[ "${scope}" == "wazuh" || "${scope}" == "full" ]]; then
  if [[ -f "${wazuh_recreate_marker}" ]]; then
    force_recreate=true
  fi
  if [[ ! -s "${wazuh_integration_state}" ]] ||
    [[ "$(<"${wazuh_integration_state}")" != "${wazuh_integration_digest}" ]]; then
    force_recreate=true
  fi
fi
if [[ "${force_recreate}" == true ]]; then
  compose_scope "${scope}" up --detach --build --wait --force-recreate
else
  compose_scope "${scope}" up --detach --build --wait
fi
proxy_config_state_staging="$(mktemp "${proxy_config_state}.tmp.XXXXXX")"
printf '%s\n' "${proxy_config_digest}" >"${proxy_config_state_staging}"
chmod 600 "${proxy_config_state_staging}"
mv "${proxy_config_state_staging}" "${proxy_config_state}"
if [[ "${scope}" == "wazuh" || "${scope}" == "full" ]]; then
  wazuh_integration_state_staging="$(
    mktemp "${wazuh_integration_state}.tmp.XXXXXX"
  )"
  printf '%s\n' "${wazuh_integration_digest}" \
    >"${wazuh_integration_state_staging}"
  chmod 600 "${wazuh_integration_state_staging}"
  mv "${wazuh_integration_state_staging}" "${wazuh_integration_state}"
fi
if [[ "${force_recreate}" == true ]]; then
  rm -f "${proxy_recreate_marker}"
  if [[ "${scope}" == "wazuh" || "${scope}" == "full" ]]; then
    rm -f "${wazuh_recreate_marker}"
  fi
fi
"${LAB_DIR}/status.sh" "${scope}" --write-evidence
