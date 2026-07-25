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
  [[ -s "${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/wazuh_indexer_ssl_certs/root-ca.pem" ]] \
    || fail "Wazuh substrate is not prepared; run ${LAB_DIR}/prepare-substrates.sh"
fi

compose_scope "${scope}" config --quiet
compose_scope "${scope}" up --detach --build --wait
"${LAB_DIR}/status.sh" "${scope}" --write-evidence
