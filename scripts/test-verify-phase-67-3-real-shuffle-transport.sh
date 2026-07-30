#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-67-3-real-shuffle-transport.sh"
workdir="$(mktemp -d)"
trap 'chmod -R u+w "${workdir}" 2>/dev/null || true; rm -rf "${workdir}"' EXIT

copy_fixture() {
  mkdir -p "$1"
  cp -R "${repo_root}/control-plane" "$1/"
  cp -R "${repo_root}/docs" "$1/"
  cp -R "${repo_root}/postgres" "$1/"
  mkdir -p "$1/scripts"
}

assert_fails_with() {
  if bash "${verifier}" "$1" >"${workdir}/stdout" 2>"${workdir}/stderr"; then
    echo "Expected verifier failure for $1" >&2
    exit 1
  fi
  grep -F -- "$2" "${workdir}/stderr" >/dev/null || {
    cat "${workdir}/stderr" >&2
    exit 1
  }
}

valid="${workdir}/valid"
copy_fixture "${valid}"
bash "${verifier}" "${valid}" >/dev/null

without_tls="${workdir}/without-tls"
copy_fixture "${without_tls}"
sed -i.bak 's/parsed.scheme != "https"/parsed.scheme != "http"/' \
  "${without_tls}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with "${without_tls}" 'parsed.scheme != "https"'

without_replay="${workdir}/without-replay"
copy_fixture "${without_replay}"
sed -i.bak '/reconciliation_id == .replay_reconciliation_id/d' \
  "${without_replay}/control-plane/deployment/phase-67-integration-lab/test-shuffle-execution.sh"
assert_fails_with \
  "${without_replay}" \
  'reconciliation_id == .replay_reconciliation_id'

fixed_proxy_acl="${workdir}/fixed-proxy-acl"
copy_fixture "${fixed_proxy_acl}"
sed -i.bak 's/allow ${AEGISOPS_LAB_CONTROL_PLANE_IPV4};/allow 172.31.67.20;/' \
  "${fixed_proxy_acl}/control-plane/deployment/phase-67-integration-lab/config/control-plane.conf"
assert_fails_with \
  "${fixed_proxy_acl}" \
  'allow ${AEGISOPS_LAB_CONTROL_PLANE_IPV4};'

unredacted_adapter="${workdir}/unredacted-adapter"
copy_fixture "${unredacted_adapter}"
sed -i.bak 's/api_key: str = field(repr=False)/api_key: str/g' \
  "${unredacted_adapter}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${unredacted_adapter}" \
  'api_key: str = field(repr=False)'

without_redirect_guard="${workdir}/without-redirect-guard"
copy_fixture "${without_redirect_guard}"
sed -i.bak 's/class _RejectRedirectHandler/class _FollowRedirectHandler/' \
  "${without_redirect_guard}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_redirect_guard}" \
  'class _RejectRedirectHandler'

without_http_framing_recovery="${workdir}/without-http-framing-recovery"
copy_fixture "${without_http_framing_recovery}"
sed -i.bak 's/except http_client.HTTPException as exc:/except RuntimeError as exc:/' \
  "${without_http_framing_recovery}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_http_framing_recovery}" \
  'except http_client.HTTPException as exc:'

without_tls_response_recovery="${workdir}/without-tls-response-recovery"
copy_fixture "${without_tls_response_recovery}"
sed -i.bak 's/except ssl.SSLEOFError as exc:/except RuntimeError as exc:/' \
  "${without_tls_response_recovery}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_tls_response_recovery}" \
  'except ssl.SSLEOFError as exc:'

without_wrapped_tls_response_recovery="${workdir}/without-wrapped-tls-response-recovery"
copy_fixture "${without_wrapped_tls_response_recovery}"
sed -i.bak \
  's/isinstance(exc.reason, ssl.SSLEOFError)/isinstance(exc.reason, RuntimeError)/' \
  "${without_wrapped_tls_response_recovery}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_wrapped_tls_response_recovery}" \
  'isinstance(exc.reason, ssl.SSLEOFError)'

without_execution_id_normalization="${workdir}/without-execution-id-normalization"
copy_fixture "${without_execution_id_normalization}"
sed -i.bak \
  's/observed_execution_id = _require_real_execution_id(/observed_execution_id = str(/' \
  "${without_execution_id_normalization}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_execution_id_normalization}" \
  'observed_execution_id = _require_real_execution_id('

without_lab_profile_boundary="${workdir}/without-lab-profile-boundary"
copy_fixture "${without_lab_profile_boundary}"
sed -i.bak \
  's/config.deployment_profile != "phase67-integration-lab"/config.deployment_profile != "single-customer"/' \
  "${without_lab_profile_boundary}/control-plane/aegisops/control_plane/service_composition.py"
assert_fails_with \
  "${without_lab_profile_boundary}" \
  'config.deployment_profile != "phase67-integration-lab"'

without_deterministic_recovery="${workdir}/without-deterministic-recovery"
copy_fixture "${without_deterministic_recovery}"
sed -i.bak 's/def recover_interrupted_dispatch(/def removed_recovery(/' \
  "${without_deterministic_recovery}/control-plane/aegisops/control_plane/adapters/executor.py"
assert_fails_with \
  "${without_deterministic_recovery}" \
  'def recover_interrupted_dispatch('

bootstrap_password_argv="${workdir}/bootstrap-password-argv"
copy_fixture "${bootstrap_password_argv}"
sed -i.bak 's/--data-binary @-/--data-binary "${registration_payload}"/' \
  "${bootstrap_password_argv}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh"
assert_fails_with \
  "${bootstrap_password_argv}" \
  '--data-binary @-'

without_external_receipt_binding="${workdir}/without-external-receipt-binding"
copy_fixture "${without_external_receipt_binding}"
sed -i.bak \
  's/observed_external_receipt_id != expected_execution_receipt_id/observed_external_receipt_id == expected_execution_receipt_id/' \
  "${without_external_receipt_binding}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
assert_fails_with \
  "${without_external_receipt_binding}" \
  'observed_external_receipt_id != expected_execution_receipt_id'

without_canceled_receipt_rejection="${workdir}/without-canceled-receipt-rejection"
copy_fixture "${without_canceled_receipt_rejection}"
sed -i.bak \
  's/{"failed", "error", "canceled", "cancelled"}/{"failed", "error"}/' \
  "${without_canceled_receipt_rejection}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
assert_fails_with \
  "${without_canceled_receipt_rejection}" \
  '{"failed", "error", "canceled", "cancelled"}'

without_unknown_status_rejection="${workdir}/without-unknown-status-rejection"
copy_fixture "${without_unknown_status_rejection}"
sed -i.bak \
  's/not in _SHUFFLE_NON_FAILURE_STATUSES/in _SHUFFLE_NON_FAILURE_STATUSES/' \
  "${without_unknown_status_rejection}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
assert_fails_with \
  "${without_unknown_status_rejection}" \
  'not in _SHUFFLE_NON_FAILURE_STATUSES'

future_recovery_timestamp="${workdir}/future-recovery-timestamp"
copy_fixture "${future_recovery_timestamp}"
sed -i.bak \
  's/finalization_transitioned_at = datetime.now(timezone.utc)/finalization_transitioned_at = delegated_at/' \
  "${future_recovery_timestamp}/control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py"
assert_fails_with \
  "${future_recovery_timestamp}" \
  'finalization_transitioned_at = datetime.now(timezone.utc)'

future_initial_dispatch_timestamp="${workdir}/future-initial-dispatch-timestamp"
copy_fixture "${future_initial_dispatch_timestamp}"
sed -i.bak \
  's/claim_transitioned_at = datetime.now(timezone.utc)/claim_transitioned_at = delegated_at/' \
  "${future_initial_dispatch_timestamp}/control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py"
assert_fails_with \
  "${future_initial_dispatch_timestamp}" \
  'claim_transitioned_at = datetime.now(timezone.utc)'

without_receipt_history_identity="${workdir}/without-receipt-history-identity"
copy_fixture "${without_receipt_history_identity}"
sed -i.bak \
  's/normalized_receipt_sha256/normalized_receipt_digest/g' \
  "${without_receipt_history_identity}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
assert_fails_with \
  "${without_receipt_history_identity}" \
  '"normalized_receipt_sha256"'

without_future_dispatch_regression="${workdir}/without-future-dispatch-regression"
copy_fixture "${without_future_dispatch_regression}"
sed -i.bak \
  's/test_service_uses_service_time_for_future_dated_dispatch_transitions/test_service_uses_caller_time_for_future_dated_dispatch_transitions/' \
  "${without_future_dispatch_regression}/control-plane/tests/test_service_persistence_action_reconciliation_delegation.py"
assert_fails_with \
  "${without_future_dispatch_regression}" \
  'def test_service_uses_service_time_for_future_dated_dispatch_transitions('

without_receipt_replay_regression="${workdir}/without-receipt-replay-regression"
copy_fixture "${without_receipt_replay_regression}"
sed -i.bak \
  's/test_phase67_replayed_prior_receipt_does_not_roll_back_latest_status/test_phase67_replayed_prior_receipt_can_roll_back_latest_status/' \
  "${without_receipt_replay_regression}/control-plane/tests/test_service_persistence_action_reconciliation_reconciliation.py"
assert_fails_with \
  "${without_receipt_replay_regression}" \
  'def test_phase67_replayed_prior_receipt_does_not_roll_back_latest_status('

without_registration_recovery="${workdir}/without-registration-recovery"
copy_fixture "${without_registration_recovery}"
sed -i.bak 's|${api_origin}/api/v1/getsettings|${api_origin}/api/v1/generateapikey|' \
  "${without_registration_recovery}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh"
assert_fails_with \
  "${without_registration_recovery}" \
  '${api_origin}/api/v1/getsettings'

workflow_id_mode_coupling="${workdir}/workflow-id-mode-coupling"
copy_fixture "${workflow_id_mode_coupling}"
python3 - \
  "${workflow_id_mode_coupling}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
source = source.replace(
    'if [[ "${AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID:-}" =~',
    'if [[ "${AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE:-}" == "real_http" '
    '&& "${AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID:-}" =~',
    1,
)
path.write_text(source, encoding="utf-8")
PY
assert_fails_with \
  "${workflow_id_mode_coupling}" \
  'if [[ "${AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID:-}" =~'

init_workflow_id_mode_coupling="${workdir}/init-workflow-id-mode-coupling"
copy_fixture "${init_workflow_id_mode_coupling}"
python3 - \
  "${init_workflow_id_mode_coupling}/control-plane/deployment/phase-67-integration-lab/init.sh" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
source = source.replace(
    'if [[ "${existing_shuffle_workflow_id}" =~',
    'if [[ "${existing_shuffle_transport_mode}" == "real_http" '
    '&& "${existing_shuffle_workflow_id}" =~',
    1,
)
path.write_text(source, encoding="utf-8")
PY
assert_fails_with \
  "${init_workflow_id_mode_coupling}" \
  'if [[ "${existing_shuffle_workflow_id}" =~ ^[0-9a-fA-F-]{36}$ ]]; then'

without_secret_remount="${workdir}/without-secret-remount"
copy_fixture "${without_secret_remount}"
sed -i.bak \
  's/up --detach --wait --force-recreate control-plane/up --detach --wait control-plane/' \
  "${without_secret_remount}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh"
assert_fails_with \
  "${without_secret_remount}" \
  'up --detach --wait --force-recreate control-plane'

without_terminal_state="${workdir}/without-terminal-state"
copy_fixture "${without_terminal_state}"
sed -i.bak \
  's/payload.get("execution_lifecycle_state") == "succeeded"/payload.get("execution_lifecycle_state") == "failed"/' \
  "${without_terminal_state}/control-plane/deployment/phase-67-integration-lab/shuffle/validate_evidence_manifest.py"
assert_fails_with \
  "${without_terminal_state}" \
  'payload.get("execution_lifecycle_state") == "succeeded"'

without_complete_schema="${workdir}/without-complete-schema"
copy_fixture "${without_complete_schema}"
sed -i.bak \
  '/_validate_schema(payload, schema/d' \
  "${without_complete_schema}/control-plane/deployment/phase-67-integration-lab/shuffle/validate_evidence_manifest.py"
assert_fails_with \
  "${without_complete_schema}" \
  '_validate_schema(payload, schema, "$")'

without_preserved_workflow_check="${workdir}/without-preserved-workflow-check"
copy_fixture "${without_preserved_workflow_check}"
sed -i.bak \
  's/validate_preserved_workflow.py/skip_preserved_workflow.py/' \
  "${without_preserved_workflow_check}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh"
assert_fails_with \
  "${without_preserved_workflow_check}" \
  'validate_preserved_workflow.py'

without_dispatch_recovery="${workdir}/without-dispatch-recovery"
copy_fixture "${without_dispatch_recovery}"
sed -i.bak \
  's/def recover_interrupted_dispatch(/def skip_interrupted_dispatch_recovery(/' \
  "${without_dispatch_recovery}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_dispatch_recovery}" \
  'def recover_interrupted_dispatch('

without_status_normalization="${workdir}/without-status-normalization"
copy_fixture "${without_status_normalization}"
sed -i.bak \
  's/status.strip().lower()/status.lower()/g' \
  "${without_status_normalization}/control-plane/aegisops/control_plane/actions/execution_coordinator_reconciliation.py"
assert_fails_with \
  "${without_status_normalization}" \
  'status.strip().lower()'

without_strict_scope_binding="${workdir}/without-strict-scope-binding"
copy_fixture "${without_strict_scope_binding}"
sed -i.bak \
  's/if not _json_values_equal(/if (/g' \
  "${without_strict_scope_binding}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_strict_scope_binding}" \
  'if not _json_values_equal('

without_utc_delegation="${workdir}/without-utc-delegation"
copy_fixture "${without_utc_delegation}"
sed -i.bak \
  's/).astimezone(timezone.utc)/)/' \
  "${without_utc_delegation}/control-plane/aegisops/control_plane/actions/execution_coordinator_delegation.py"
assert_fails_with \
  "${without_utc_delegation}" \
  ').astimezone(timezone.utc)'

without_extra_property_rejection="${workdir}/without-extra-property-rejection"
copy_fixture "${without_extra_property_rejection}"
sed -i.bak \
  's/unexpected = sorted(set(observed) - set(expected))/unexpected = []/' \
  "${without_extra_property_rejection}/control-plane/aegisops/control_plane/adapters/shuffle_workflow_contract.py"
assert_fails_with \
  "${without_extra_property_rejection}" \
  'unexpected = sorted(set(observed) - set(expected))'

without_total_deadline="${workdir}/without-total-deadline"
copy_fixture "${without_total_deadline}"
sed -i.bak \
  's/deadline = self.clock() + timeout_seconds/deadline = float("inf")/' \
  "${without_total_deadline}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_total_deadline}" \
  'deadline = self.clock() + timeout_seconds'

without_dispatch_workflow_revalidation="${workdir}/without-dispatch-workflow-revalidation"
copy_fixture "${without_dispatch_workflow_revalidation}"
sed -i.bak \
  's/self\._revalidate_reviewed_workflow()/pass/' \
  "${without_dispatch_workflow_revalidation}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_dispatch_workflow_revalidation}" \
  'self._revalidate_reviewed_workflow()'

without_transient_validation_retry="${workdir}/without-transient-validation-retry"
copy_fixture "${without_transient_validation_retry}"
sed -i.bak \
  's/if not exc.transient or attempt == self.max_attempts:/if True:/' \
  "${without_transient_validation_retry}/control-plane/aegisops/control_plane/adapters/shuffle_real.py"
assert_fails_with \
  "${without_transient_validation_retry}" \
  'if not exc.transient or attempt == self.max_attempts:'

without_workflow_discovery="${workdir}/without-workflow-discovery"
copy_fixture "${without_workflow_discovery}"
sed -i.bak \
  's/find_reviewed_workflow.py/skip_workflow_discovery.py/' \
  "${without_workflow_discovery}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh"
assert_fails_with \
  "${without_workflow_discovery}" \
  'find_reviewed_workflow.py'

delayed_workflow_id_persistence="${workdir}/delayed-workflow-id-persistence"
copy_fixture "${delayed_workflow_id_persistence}"
python3 - \
  "${delayed_workflow_id_persistence}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh" <<'PY'
from pathlib import Path
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding="utf-8")
needle = (
    '    set_runtime_value AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID "${workflow_id}"\n\n'
    '    workflow_with_runtime_id="$('
)
replacement = (
    '    workflow_with_runtime_id="$('
)
if needle not in source:
    raise SystemExit("workflow creation persistence fixture changed")
path.write_text(source.replace(needle, replacement, 1), encoding="utf-8")
PY
assert_fails_with \
  "${delayed_workflow_id_persistence}" \
  'Created Shuffle workflow ID must be persisted before workflow update'

without_app_image_pin="${workdir}/without-app-image-pin"
copy_fixture "${without_app_image_pin}"
sed -i.bak \
  's#"${LAB_DIR}/pin-shuffle-app-image.sh"#"${LAB_DIR}/skip-app-image-pin.sh"#' \
  "${without_app_image_pin}/control-plane/deployment/phase-67-integration-lab/bootstrap-shuffle.sh"
assert_fails_with \
  "${without_app_image_pin}" \
  '"${LAB_DIR}/pin-shuffle-app-image.sh"'

drifted_app_image_digest="${workdir}/drifted-app-image-digest"
copy_fixture "${drifted_app_image_digest}"
sed -i.bak \
  's/fd5391cb0af02e92be194a8c4fe67a4221d5fb26f279eaa3f00676b201bf6cb8/0000000000000000000000000000000000000000000000000000000000000000/' \
  "${drifted_app_image_digest}/control-plane/deployment/phase-67-integration-lab/shuffle/reviewed-app-image.env"
assert_fails_with \
  "${drifted_app_image_digest}" \
  'AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST=sha256:fd5391cb0af02e92be194a8c4fe67a4221d5fb26f279eaa3f00676b201bf6cb8'

without_orborus_identity="${workdir}/without-orborus-identity"
copy_fixture "${without_orborus_identity}"
sed -i.bak '/ORBORUS_CONTAINER_NAME:/d' \
  "${without_orborus_identity}/control-plane/deployment/phase-67-integration-lab/docker-compose.yml"
assert_fails_with \
  "${without_orborus_identity}" \
  'ORBORUS_CONTAINER_NAME: ${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:-aegisops-phase67-lab}-shuffle-orborus-1'

synthetic_allowed="${workdir}/synthetic-allowed"
copy_fixture "${synthetic_allowed}"
python3 - \
  "${synthetic_allowed}/control-plane/deployment/phase-67-integration-lab/shuffle/evidence-manifest.schema.json" <<'PY'
import json
from pathlib import Path
import sys

path = Path(sys.argv[1])
schema = json.loads(path.read_text(encoding="utf-8"))
schema["properties"]["execution_id"].pop("not")
path.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
PY
assert_fails_with "${synthetic_allowed}" '"pattern": "^shuffle-run-"'

inline_secret="${workdir}/inline-secret"
copy_fixture "${inline_secret}"
printf '\n# Authorization: Bearer abcdefghijklmnopqrstuvwxyz123456\n' \
  >>"${inline_secret}/control-plane/deployment/phase-67-integration-lab/shuffle/run_real_trial.py"
assert_fails_with \
  "${inline_secret}" \
  "Committed Phase 67.3 artifact contains an inline API credential"

echo "PASS: Phase 67.3 verifier self-tests passed."
