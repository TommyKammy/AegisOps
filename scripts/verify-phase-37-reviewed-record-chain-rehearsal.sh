#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${repo_root}"

python3 -m unittest discover -s control-plane/tests -p 'test_phase37_reviewed_record_chain_rehearsal.py'

echo "Phase 37 reviewed record-chain rehearsal fixture replays approval, denial, manual fallback, escalation, execution receipt, reconciliation, and manifest validation."
