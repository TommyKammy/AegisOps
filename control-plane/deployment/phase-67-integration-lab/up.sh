#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

scope="${1:-core}"
[[ "$#" -le 1 ]] || fail "usage: $0 [core|wazuh|shuffle|full]"
require_runtime_environment
"${LAB_DIR}/preflight.sh" --scope "${scope}" --write-evidence

case "${scope}" in
  core) ;;
  wazuh|shuffle|full) ;;
  *) fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full" ;;
esac

if [[ "${scope}" == "wazuh" || "${scope}" == "full" ]]; then
  require_command openssl
  validate_wazuh_certificate_bundle \
    "${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/wazuh_indexer_ssl_certs" \
    || fail "Wazuh substrate certificate bundle is invalid; run ${LAB_DIR}/prepare-substrates.sh"
fi

compose_scope "${scope}" config --quiet
proxy_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required"
wazuh_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-certificate-recreate-required"
force_recreate_arguments=()
if [[ -f "${proxy_recreate_marker}" ]]; then
  force_recreate_arguments+=(--force-recreate)
fi
if [[ "${scope}" == "wazuh" || "${scope}" == "full" ]]; then
  if [[ -f "${wazuh_recreate_marker}" && "${#force_recreate_arguments[@]}" -eq 0 ]]; then
    force_recreate_arguments+=(--force-recreate)
  fi
fi
compose_scope "${scope}" up --detach --build --wait "${force_recreate_arguments[@]}"
if [[ "${#force_recreate_arguments[@]}" -gt 0 ]]; then
  rm -f "${proxy_recreate_marker}"
  if [[ "${scope}" == "wazuh" || "${scope}" == "full" ]]; then
    rm -f "${wazuh_recreate_marker}"
  fi
fi
"${LAB_DIR}/status.sh" "${scope}" --write-evidence
