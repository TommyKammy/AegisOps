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
if [[ "${force_recreate}" == true ]]; then
  rm -f "${proxy_recreate_marker}"
  if [[ "${scope}" == "wazuh" || "${scope}" == "full" ]]; then
    rm -f "${wazuh_recreate_marker}"
  fi
fi
"${LAB_DIR}/status.sh" "${scope}" --write-evidence
