#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"

bash "${repo_root}/scripts/verify-phase-62-1-reviewed-automation-catalog-contract.sh" "${repo_root}"
