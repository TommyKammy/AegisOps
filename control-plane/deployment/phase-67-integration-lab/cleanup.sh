#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_configuration
"${LAB_DIR}/down.sh"

echo "Non-destructive cleanup complete."
echo "Use destroy-data.sh only when permanent deletion of lab volumes is intended."
