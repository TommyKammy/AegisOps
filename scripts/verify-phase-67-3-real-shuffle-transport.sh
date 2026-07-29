#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
lab="${repo_root}/control-plane/deployment/phase-67-integration-lab"

fail() {
  echo "$*" >&2
  exit 1
}

require_file() {
  [[ -f "$1" ]] || fail "Missing Phase 67.3 artifact: ${1#${repo_root}/}"
}

require_executable() {
  [[ -x "$1" ]] || fail "Phase 67.3 command must be executable: ${1#${repo_root}/}"
}

require_fixed() {
  grep -F -- "$2" "$1" >/dev/null \
    || fail "Missing Phase 67.3 contract in ${1#${repo_root}/}: $2"
}

files=(
  control-plane/aegisops/control_plane/adapters/shuffle_real.py
  control-plane/aegisops/control_plane/config.py
  control-plane/aegisops/control_plane/service_composition.py
  control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py
  control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py
  control-plane/tests/test_phase67_3_real_shuffle_transport.py
  control-plane/deployment/phase-67-integration-lab/docker-compose.yml
  control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh
  control-plane/deployment/phase-67-integration-lab/test-shuffle-execution.sh
  control-plane/deployment/phase-67-integration-lab/shuffle/harmless-local-log-workflow.json
  control-plane/deployment/phase-67-integration-lab/shuffle/run_real_trial.py
  control-plane/deployment/phase-67-integration-lab/shuffle/evidence-manifest.schema.json
  control-plane/deployment/phase-67-integration-lab/shuffle/validate_evidence_manifest.py
  docs/phase-67-3-real-shuffle-transport.md
  postgres/control-plane/migrations/0016_phase_67_action_execution_dispatching_state.sql
)
for file in "${files[@]}"; do
  require_file "${repo_root}/${file}"
done
require_executable "${lab}/bootstrap-shuffle.sh"
require_executable "${lab}/test-shuffle-execution.sh"

adapter="${repo_root}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
reconciliation="${repo_root}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
compose="${lab}/docker-compose.yml"
proxy="${lab}/config/control-plane.conf"
trial="${lab}/test-shuffle-execution.sh"
schema="${lab}/shuffle/evidence-manifest.schema.json"
workflow="${lab}/shuffle/harmless-local-log-workflow.json"

require_fixed "${adapter}" 'parsed.scheme != "https"'
require_fixed "${adapter}" '"Authorization": f"Bearer {api_key}"'
require_fixed "${adapter}" 'max_attempts not in {1, 2}'
require_fixed "${adapter}" 'ShuffleTransportFailure("timeout")'
require_fixed "${adapter}" '"connection_not_established" if retryable'
require_fixed "${adapter}" 'startswith(("shuffle-run-", "shuffle-receipt-"))'
require_fixed "${adapter}" 'Shuffle execution id must be a UUID'
require_fixed "${adapter}" 'api_key: str = field(repr=False)'
require_fixed "${adapter}" 'requires an explicit CA file'
require_fixed \
  "${repo_root}/control-plane/tests/test_phase67_3_real_shuffle_transport.py" \
  'self.assertNotIn("authorization", receipt)'
require_fixed "${reconciliation}" '"normalized_receipt"'
require_fixed "${reconciliation}" '_find_receipt_reconciliation'
require_fixed "${reconciliation}" '"downstream execution failed and requires operator review"'
require_fixed "${reconciliation}" '"requested_scope"'
require_fixed "${reconciliation}" 'not isinstance(value, bool)'
require_fixed "${compose}" 'AEGISOPS_CONTROL_PLANE_SHUFFLE_API_KEY_FILE: /run/secrets/shuffle-api-key'
require_fixed "${compose}" 'NGINX_ENVSUBST_FILTER: ^AEGISOPS_LAB_CONTROL_PLANE_IPV4$'
require_fixed "${compose}" './config/control-plane.conf:/etc/nginx/templates/control-plane.conf.template:ro'
require_fixed "${compose}" 'ghcr.io/shuffle/shuffle-orborus:2.2.1@sha256:'
require_fixed "${compose}" 'ghcr.io/shuffle/shuffle-worker:2.2.1@sha256:'
require_fixed "${compose}" '/var/run/docker.sock:/var/run/docker.sock'
require_fixed "${compose}" 'CLEANUP: "true"'
require_fixed "${compose}" 'ORBORUS_CONTAINER_NAME: ${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:-aegisops-phase67-lab}-shuffle-orborus-1'
require_fixed "${proxy}" 'location /shuffle-api/ {'
require_fixed "${proxy}" 'allow ${AEGISOPS_LAB_CONTROL_PLANE_IPV4};'
require_fixed "${proxy}" 'rewrite ^/shuffle-api/(.*)$ /$1 break;'
require_fixed "${trial}" 'reconciliation_id == .replay_reconciliation_id'
require_fixed \
  "${lab}/shuffle/validate_evidence_manifest.py" \
  'payload.get("execution_lifecycle_state") == "succeeded"'
require_fixed \
  "${lab}/shuffle/validate_evidence_manifest.py" \
  'not isinstance(idempotency_execution_count, bool)'
require_fixed "${schema}" '"source_mode"'
require_fixed "${schema}" '"const": "real_shuffle"'
require_fixed "${schema}" '"idempotency_execution_count"'
require_fixed "${schema}" '"requested_scope"'
require_fixed "${schema}" '"pattern": "^shuffle-run-"'
require_fixed "${schema}" '"pattern": "^shuffle-receipt-"'
require_fixed "${workflow}" '"name": "repeat_back_to_me"'
require_fixed "${workflow}" '"value": "$exec"'

if grep -R -E \
  'fixture-api-key|Authorization: Bearer [A-Za-z0-9_-]{20,}' \
  "${lab}/bootstrap-shuffle.sh" \
  "${lab}/test-shuffle-execution.sh" \
  "${lab}/shuffle" \
  "${repo_root}/docs/phase-67-3-real-shuffle-transport.md" \
  >/dev/null; then
  fail "Committed Phase 67.3 artifact contains an inline API credential"
fi

python3 -m json.tool "${schema}" >/dev/null
python3 -m json.tool "${workflow}" >/dev/null
echo "PASS: Phase 67.3 real Shuffle transport contract verified."
