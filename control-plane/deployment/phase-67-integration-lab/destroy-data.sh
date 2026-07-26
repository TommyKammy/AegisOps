#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

confirmation="${1:-}"
[[ "${confirmation}" == "--confirm-destroy-phase-67-lab-data" ]] \
  || fail "permanent lab-volume deletion requires: $0 --confirm-destroy-phase-67-lab-data"
[[ "$#" -eq 1 ]] || fail "usage: $0 --confirm-destroy-phase-67-lab-data"

require_runtime_configuration
compose_lab --profile wazuh --profile shuffle down --volumes --remove-orphans

echo "Deleted only Compose volumes owned by project ${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}."
echo "Generated secrets, substrate files, and evidence remain at ${AEGISOPS_LAB_RUNTIME_ROOT}."
