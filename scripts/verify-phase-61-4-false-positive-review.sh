#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
exec bash "${repo_root}/scripts/verify-phase-61-4-false-positive-review-records.sh" "${repo_root}"
