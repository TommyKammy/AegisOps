#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_configuration
compose_lab --profile wazuh --profile shuffle down --remove-orphans

echo "Stopped Phase 67.1 containers."
echo "Named volumes, generated secrets, substrates, and evidence were preserved."
