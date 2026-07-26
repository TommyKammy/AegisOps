#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

require_runtime_environment
for log_argument in "$@"; do
  [[ "${log_argument}" != -* ]] \
    || fail "log options are intentionally unavailable; pass only service names for a bounded snapshot"
done

if [[ "$#" -eq 0 ]]; then
  compose_lab --profile wazuh --profile shuffle logs \
    --no-color \
    --timestamps \
    --tail "${AEGISOPS_LAB_LOG_TAIL:-200}"
else
  compose_lab --profile wazuh --profile shuffle logs \
    --no-color \
    --timestamps \
    --tail "${AEGISOPS_LAB_LOG_TAIL:-200}" \
    "$@"
fi
