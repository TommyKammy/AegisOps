#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_environment
require_command curl

for endpoint in healthz readyz runtime; do
  curl \
    --fail \
    --silent \
    --show-error \
    --cacert "${AEGISOPS_LAB_PROXY_CERT_DIR}/lab.crt" \
    "https://localhost:${AEGISOPS_LAB_PROXY_PORT}/${endpoint}" >/dev/null
  echo "PASS https://localhost:${AEGISOPS_LAB_PROXY_PORT}/${endpoint}"
done

echo "Core Phase 67.1 health boundary passed."
