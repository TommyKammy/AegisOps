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
  control-plane/aegisops/control_plane/adapters/executor.py
  control-plane/aegisops/control_plane/adapters/shuffle.py
  control-plane/aegisops/control_plane/adapters/shuffle_real.py
  control-plane/aegisops/control_plane/adapters/shuffle_workflow_contract.py
  control-plane/aegisops/control_plane/config.py
  control-plane/aegisops/control_plane/service_composition.py
  control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py
  control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py
  control-plane/tests/test_phase67_3_real_shuffle_transport.py
  control-plane/deployment/phase-67-integration-lab/docker-compose.yml
  control-plane/deployment/phase-67-integration-lab/init.sh
  control-plane/deployment/phase-67-integration-lab/lab-common.sh
  control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh
  control-plane/deployment/phase-67-integration-lab/pin-shuffle-app-image.sh
  control-plane/deployment/phase-67-integration-lab/test-shuffle-execution.sh
  control-plane/deployment/phase-67-integration-lab/shuffle/find_reviewed_workflow.py
  control-plane/deployment/phase-67-integration-lab/shuffle/harmless-local-log-workflow.json
  control-plane/deployment/phase-67-integration-lab/shuffle/reviewed-app-image.env
  control-plane/deployment/phase-67-integration-lab/shuffle/run_real_trial.py
  control-plane/deployment/phase-67-integration-lab/shuffle/evidence-manifest.schema.json
  control-plane/deployment/phase-67-integration-lab/shuffle/validate_evidence_manifest.py
  control-plane/deployment/phase-67-integration-lab/shuffle/validate_preserved_workflow.py
  docs/phase-67-3-real-shuffle-transport.md
  postgres/control-plane/migrations/0016_phase_67_action_execution_dispatching_state.sql
)
for file in "${files[@]}"; do
  require_file "${repo_root}/${file}"
done
require_executable "${lab}/bootstrap-shuffle.sh"
require_executable "${lab}/pin-shuffle-app-image.sh"
require_executable "${lab}/test-shuffle-execution.sh"

adapter="${repo_root}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
workflow_contract="${repo_root}/control-plane/aegisops/control_plane/adapters/shuffle_workflow_contract.py"
deterministic_shuffle="${repo_root}/control-plane/aegisops/control_plane/adapters/shuffle.py"
isolated_executor="${repo_root}/control-plane/aegisops/control_plane/adapters/executor.py"
service_composition="${repo_root}/control-plane/aegisops/control_plane/service_composition.py"
reconciliation="${repo_root}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
delegation="${repo_root}/control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py"
compose="${lab}/docker-compose.yml"
proxy="${lab}/config/control-plane.conf"
trial="${lab}/test-shuffle-execution.sh"
schema="${lab}/shuffle/evidence-manifest.schema.json"
workflow="${lab}/shuffle/harmless-local-log-workflow.json"
init="${lab}/init.sh"
common="${lab}/lab-common.sh"
bootstrap="${lab}/bootstrap-shuffle.sh"
evidence_validator="${lab}/shuffle/validate_evidence_manifest.py"
workflow_validator="${lab}/shuffle/validate_preserved_workflow.py"
workflow_finder="${lab}/shuffle/find_reviewed_workflow.py"
app_image_pin="${lab}/pin-shuffle-app-image.sh"
app_image_env="${lab}/shuffle/reviewed-app-image.env"

legacy_placeholder_id="67f30000-0000-4000-8000-000000000001"
if grep -F "${legacy_placeholder_id}" "${init}" "${compose}" >/dev/null; then
  fail "Fresh Phase 67.3 runtime must not seed the legacy Shuffle workflow placeholder."
fi

require_fixed "${adapter}" 'parsed.scheme != "https"'
require_fixed "${adapter}" '"Authorization": f"Bearer {api_key}"'
require_fixed "${adapter}" 'max_attempts not in {1, 2}'
require_fixed "${adapter}" 'outcome_unknown=method == "POST"'
require_fixed "${adapter}" 'transient=True'
require_fixed "${adapter}" 'class _RejectRedirectHandler'
require_fixed "${adapter}" 'request.build_opener('
require_fixed "${adapter}" '"redirect_rejected"'
require_fixed "${adapter}" 'except http_client.HTTPException as exc:'
require_fixed "${adapter}" '"invalid_http_response"'
require_fixed "${adapter}" 'except ssl.SSLEOFError as exc:'
require_fixed "${adapter}" '"tls_response_truncated"'
require_fixed "${adapter}" 'except ssl.SSLError as exc:'
require_fixed "${adapter}" '"tls_response_failure"'
require_fixed "${adapter}" 'isinstance(exc.reason, ssl.SSLEOFError)'
require_fixed "${adapter}" 'isinstance(exc.reason, ssl.SSLError)'
require_fixed "${adapter}" 'deadline = self.clock() + timeout_seconds'
require_fixed "${adapter}" 'settimeout(remaining)'
require_fixed "${adapter}" 'chunk = read1('
require_fixed "${adapter}" 'validate_reviewed_workflow('
require_fixed "${adapter}" 'self._revalidate_reviewed_workflow()'
require_fixed \
  "${adapter}" \
  'if not exc.transient or attempt == self.max_attempts:'
require_fixed "${adapter}" '"reviewed_workflow_mismatch"'
require_fixed "${adapter}" '"connection_not_established" if retryable'
require_fixed "${adapter}" 'startswith(("shuffle-run-", "shuffle-receipt-"))'
require_fixed "${adapter}" 'Shuffle execution id must be a UUID'
require_fixed "${adapter}" 'api_key: str = field(repr=False)'
require_fixed "${adapter}" 'requires an explicit CA file'
require_fixed "${adapter}" 'def recover_interrupted_dispatch('
require_fixed "${adapter}" '"interrupted_dispatch_not_observed"'
require_fixed "${adapter}" '"interrupted_dispatch_binding_mismatch"'
require_fixed "${adapter}" 'if not _json_values_equal('
require_fixed "${adapter}" 'replace("+00:00", "Z")'
require_fixed "${adapter}" '"execution_argument_mismatch"'
require_fixed "${adapter}" '"malformed_reviewed_action_result"'
require_fixed "${adapter}" '_REVIEWED_ACTION_NAME = "repeat_back_to_me"'
require_fixed "${adapter}" 'observed_execution_id = _require_real_execution_id('
require_fixed "${deterministic_shuffle}" 'def recover_interrupted_dispatch('
require_fixed "${isolated_executor}" 'def recover_interrupted_dispatch('
require_fixed \
  "${service_composition}" \
  'config.deployment_profile != "phase67-integration-lab"'
require_fixed \
  "${repo_root}/control-plane/tests/test_phase67_3_real_shuffle_transport.py" \
  'self.assertNotIn("authorization", receipt)'
require_fixed "${reconciliation}" '"normalized_receipt"'
require_fixed "${reconciliation}" '"normalized_receipt_sha256"'
require_fixed "${reconciliation}" '_find_receipt_reconciliation'
require_fixed "${reconciliation}" 'allow_unhashed_match'
require_fixed "${reconciliation}" '"downstream execution failed and requires operator review"'
require_fixed "${reconciliation}" '"requested_scope"'
require_fixed "${reconciliation}" 'not isinstance(value, bool)'
require_fixed "${reconciliation}" 'status.strip().lower()'
require_fixed \
  "${reconciliation}" \
  '{"failed", "error", "canceled", "cancelled"}'
require_fixed \
  "${reconciliation}" \
  'not in _SHUFFLE_NON_FAILURE_STATUSES'
require_fixed "${reconciliation}" 'and not _json_values_equal('
require_fixed \
  "${reconciliation}" \
  'observed_external_receipt_id != expected_execution_receipt_id'
require_fixed "${delegation}" '"recover_interrupted_dispatch"'
require_fixed \
  "${common}" \
  'LEGACY_SHUFFLE_PLACEHOLDER_WORKFLOW_ID='
require_fixed "${common}" 'classify_shuffle_workflow_runtime_state()'
require_fixed "${common}" 'active and pending Shuffle workflow ids conflict'
require_fixed "${init}" 'shuffle_api_workflow_id=""'
require_fixed "${init}" 'shuffle_pending_workflow_id=""'
require_fixed \
  "${init}" \
  'classify_shuffle_workflow_runtime_state \'
require_fixed \
  "${init}" \
  'write_runtime_env_assignment AEGISOPS_LAB_SHUFFLE_PENDING_WORKFLOW_ID'
require_fixed "${delegation}" ').astimezone(timezone.utc)'
require_fixed "${delegation}" 'getattr(exc, "outcome_unknown", False)'
require_fixed \
  "${delegation}" \
  'finalization_transitioned_at = datetime.now(timezone.utc)'
require_fixed \
  "${delegation}" \
  'claim_transitioned_at = datetime.now(timezone.utc)'
require_fixed \
  "${repo_root}/control-plane/tests/test_service_persistence_action_reconciliation_delegation.py" \
  'def test_service_uses_service_time_for_future_dated_dispatch_transitions('
require_fixed \
  "${repo_root}/control-plane/tests/test_service_persistence_action_reconciliation_reconciliation.py" \
  'def test_phase67_replayed_prior_receipt_does_not_roll_back_latest_status('
require_fixed "${compose}" 'AEGISOPS_CONTROL_PLANE_SHUFFLE_API_KEY_FILE: /run/secrets/shuffle-api-key'
require_fixed \
  "${compose}" \
  'AEGISOPS_CONTROL_PLANE_SHUFFLE_API_WORKFLOW_ID: "${AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID:-}"'
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
  "${evidence_validator}" \
  'payload.get("execution_lifecycle_state") == "succeeded"'
require_fixed \
  "${evidence_validator}" \
  'not isinstance(idempotency_execution_count, bool)'
require_fixed "${evidence_validator}" '_validate_schema(payload, schema, "$")'
require_fixed "${evidence_validator}" 'schema.get("additionalProperties") is False'
require_fixed "${evidence_validator}" 'REVIEWED_SHUFFLE_APP_IMAGE_DIGEST'
require_fixed "${bootstrap}" 'validate_preserved_workflow.py'
require_fixed "${bootstrap}" 'find_reviewed_workflow.py'
require_fixed "${bootstrap}" '"${LAB_DIR}/pin-shuffle-app-image.sh"'
require_fixed "${bootstrap}" '-H "@${auth_header_path}"'
require_fixed "${bootstrap}" 'unset api_key'
require_fixed "${bootstrap}" '--rawfile password "${admin_password_path}"'
require_fixed "${bootstrap}" '--data-binary @-'
require_fixed "${bootstrap}" '${api_origin}/api/v1/login'
require_fixed "${bootstrap}" '${api_origin}/api/v1/getsettings'
require_fixed "${bootstrap}" '-H "@${login_cookie_header_path}"'
require_fixed \
  "${bootstrap}" \
  'AEGISOPS_LAB_SHUFFLE_PENDING_WORKFLOW_ID'
require_fixed \
  "${bootstrap}" \
  'workflow_runtime_state="$('
require_fixed \
  "${bootstrap}" \
  'set_shuffle_workflow_runtime_state "" "${workflow_id}" deterministic'
require_fixed \
  "${bootstrap}" \
  'set_shuffle_workflow_runtime_state "${workflow_id}" "" real_http'
require_fixed "${bootstrap}" 'workflow_update_required=true'
require_fixed \
  "${bootstrap}" \
  'up --detach --wait --force-recreate control-plane'
require_fixed \
  "${lab}/shuffle/run_real_trial.py" \
  'exc.category != "missing_receipt" and not exc.transient'
require_fixed "${workflow_contract}" 'require_reviewed_definition('
require_fixed "${workflow_contract}" 'len(observed) != len(expected)'
require_fixed \
  "${workflow_contract}" \
  'unexpected = sorted(set(observed) - set(expected))'
require_fixed "${workflow_validator}" 'validate_reviewed_workflow('
require_fixed "${workflow_finder}" 'NOT_FOUND_EXIT_CODE = 3'
require_fixed "${workflow_finder}" 'len(matches) != 1'
require_fixed "${app_image_pin}" '"${LAB_DIR}/preflight.sh" --scope shuffle'
require_fixed "${app_image_pin}" 'docker_lab pull'
require_fixed "${app_image_pin}" '.[0].RepoDigests | index($pinned_reference) != null'
require_fixed "${app_image_pin}" 'docker_lab image tag'
require_fixed \
  "${app_image_env}" \
  'AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST=sha256:fd5391cb0af02e92be194a8c4fe67a4221d5fb26f279eaa3f00676b201bf6cb8'
require_fixed "${schema}" '"source_mode"'
require_fixed "${schema}" '"const": "real_shuffle"'
require_fixed "${schema}" '"idempotency_execution_count"'
require_fixed "${schema}" '"requested_scope"'
require_fixed "${schema}" '"pattern": "^shuffle-run-"'
require_fixed "${schema}" '"pattern": "^shuffle-receipt-"'
require_fixed "${schema}" '"shuffle_app_image_immutable_ref"'
require_fixed "${workflow}" '"name": "repeat_back_to_me"'
require_fixed "${workflow}" '"value": "$exec"'

python3 - "${bootstrap}" <<'PY'
from pathlib import Path
import sys

source = Path(sys.argv[1]).read_text(encoding="utf-8")
create_id = source.index('workflow_id="$(\n        jq -er')
persist_pending_id = source.index(
    'set_shuffle_workflow_runtime_state "" "${workflow_id}" deterministic',
    create_id,
)
update_workflow = source.index('workflow_with_runtime_id="$(', create_id)
persist_authoritative_id = source.index(
    'set_shuffle_workflow_runtime_state "${workflow_id}" "" real_http',
    update_workflow,
)
if not create_id < persist_pending_id < update_workflow < persist_authoritative_id:
    raise SystemExit(
        "Created Shuffle workflow ID must remain pending until workflow update"
    )
PY

classified_state="$(
  bash -c \
    'source "$1"; classify_shuffle_workflow_runtime_state "$2" "" deterministic' \
    phase67-workflow-state-verifier \
    "${common}" \
    "${legacy_placeholder_id}"
)"
[[ "${classified_state}" == "uninitialized" ]] \
  || fail "Legacy Shuffle workflow placeholder must migrate to uninitialized state."

if grep -F -- '--arg password' "${bootstrap}" >/dev/null \
  || grep -F -- '--data-binary "${registration_payload}"' "${bootstrap}" >/dev/null; then
  fail "Shuffle bootstrap credentials must not be expanded into process arguments."
fi

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
