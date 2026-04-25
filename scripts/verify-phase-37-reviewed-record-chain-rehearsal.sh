#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${repo_root}"

python3 -m unittest control-plane.tests.test_phase37_reviewed_record_chain_rehearsal

echo "Phase 37 reviewed record-chain rehearsal fixture replays through approval, execution receipt, reconciliation, and manifest validation."
