#!/usr/bin/env bash

set -euo pipefail
umask 077
trap 'rc=$?; echo "BLOCKED: real Shuffle trial failed at line ${LINENO} (exit ${rc})" >&2' ERR

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_environment
[[ "${AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE:-}" == "real_http" ]] \
  || fail "real Shuffle transport is not enabled; run ${LAB_DIR}/bootstrap-shuffle.sh"

"${LAB_DIR}/up.sh" shuffle
evidence_path="${AEGISOPS_LAB_EVIDENCE_DIR}/phase67-3-real-shuffle-trial.json"
evidence_staging="$(mktemp "${evidence_path}.tmp.XXXXXX")"
compose_scope shuffle exec -T control-plane \
  python3 /opt/aegisops/phase67-shuffle/run_real_trial.py \
  >"${evidence_staging}"
jq -e '
  .schema_version == "phase67.3-real-shuffle-trial-v1"
  and .source_mode == "real_shuffle"
  and (.execution_id | startswith("shuffle-run-") | not)
  and (.expected_execution_receipt_id | startswith("shuffle-receipt-") | not)
  and .reconciliation_id == .replay_reconciliation_id
  and .reconciliation_disposition == "matched"
  and .authority_posture == "aegisops_reconciliation_remains_authoritative"
' "${evidence_staging}" >/dev/null
python3 "${LAB_DIR}/shuffle/validate_evidence_manifest.py" \
  "${evidence_staging}" >/dev/null
chmod 600 "${evidence_staging}"
mv "${evidence_staging}" "${evidence_path}"
echo "PASS: real Shuffle execution and idempotent receipt reconciliation verified"
jq 'del(.payload_hash)' "${evidence_path}"
