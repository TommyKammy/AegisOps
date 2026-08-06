#!/usr/bin/env bash

set -euo pipefail

repo_root="${AEGISOPS_REPO_ROOT_OVERRIDE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
lab_root="${repo_root}/control-plane/deployment/phase-67-integration-lab"
e2e_root="${lab_root}/e2e"
schema="${e2e_root}/evidence-manifest.schema.json"
sample="${e2e_root}/sample-evidence.json"
validator="${e2e_root}/validate_evidence_manifest.py"
evaluation="${repo_root}/docs/phase-67-prerequisite-evaluation.md"

fail() {
  echo "Phase 67.4 verifier failed: $*" >&2
  exit 1
}

require_file() {
  [[ -f "$1" ]] || fail "missing required file: ${1#"${repo_root}/"}"
}

require_executable() {
  [[ -x "$1" ]] || fail "required script is not executable: ${1#"${repo_root}/"}"
}

require_fixed() {
  local path="$1"
  local text="$2"
  grep -Fq -- "${text}" "${path}" \
    || fail "${path#"${repo_root}/"} is missing required text: ${text}"
}

reject_fixed() {
  local path="$1"
  local text="$2"
  ! grep -Fq -- "${text}" "${path}" \
    || fail "${path#"${repo_root}/"} contains forbidden text: ${text}"
}

for path in \
  "${schema}" \
  "${sample}" \
  "${validator}" \
  "${e2e_root}/build_evidence.py" \
  "${e2e_root}/run_real_journey.py" \
  "${lab_root}/run-e2e-trial.sh" \
  "${evaluation}" \
  "${repo_root}/control-plane/tests/test_phase67_4_real_service_e2e.py"; do
  require_file "${path}"
done

for path in \
  "${validator}" \
  "${e2e_root}/build_evidence.py" \
  "${e2e_root}/run_real_journey.py" \
  "${lab_root}/run-e2e-trial.sh"; do
  require_executable "${path}"
done

require_fixed "${evaluation}" 'Direct verdict: `integration_trial_blocked`'
require_fixed "${evaluation}" 'Evaluation scope: `committed_historical_trial`'
require_fixed "${evaluation}" 'Next complete-trial verdict: `integration_trial_passed_with_owned_limitations`'
require_fixed "${evaluation}" 'GA acceptance: `not_accepted`'
require_fixed "${evaluation}" 'does not attest to the current'
require_fixed "${evaluation}" 'cannot be reused as current-revision evidence'
require_fixed "${evaluation}" 'AegisOps alert, case, action request, approval decision, action execution,'
require_fixed "${evaluation}" 'does not prove production readiness'
require_fixed "${lab_root}/RUNBOOK.md" '## Complete Phase 67.4 E2E Trial'
require_fixed "${lab_root}/RUNBOOK.md" 'run-e2e-trial.sh'
require_fixed "${lab_root}/RUNBOOK.md" 'explicit record-ID allowlist'
require_fixed "${lab_root}/RUNBOOK.md" 'tracked and untracked worktree after cleanup'
require_fixed "${lab_root}/RUNBOOK.md" 'derived from its terminal step'
require_fixed "${repo_root}/README.md" 'Phase 67.4 real-service E2E prerequisite evaluation'
require_fixed "${lab_root}/README.md" 'records in preserved volumes from'
require_fixed "${lab_root}/test-wazuh-intake.sh" 'native_wazuh_agent_id: $agent_id'
require_fixed "${lab_root}/test-wazuh-intake.sh" 'AEGISOPS_LAB_TRIAL_SCOPE:-wazuh'
require_fixed "${e2e_root}/run_real_journey.py" 'REQUESTER_IDENTITY = "phase67-lab-requester"'
require_fixed "${e2e_root}/run_real_journey.py" 'if not rejected or execution_count != 0:'
require_fixed "${e2e_root}/run_real_journey.py" 'lifecycle_state="rejected"'
require_fixed "${e2e_root}/run_real_journey.py" 'service.reconcile_action_execution('
require_fixed "${e2e_root}/run_real_journey.py" 'export_audit_retention_baseline('
require_fixed "${e2e_root}/run_real_journey.py" '_trial_report_record_ids'
require_fixed "${e2e_root}/run_real_journey.py" 'record_ids_by_family='
require_fixed "${e2e_root}/run_real_journey.py" 'wazuh_reconciliation_ids'
require_fixed "${e2e_root}/run_real_journey.py" 'negative receipt probes changed authoritative state'
require_fixed "${e2e_root}/run_real_journey.py" 'delegated_at = datetime.now(timezone.utc)'
reject_fixed "${e2e_root}/run_real_journey.py" 'delegated_at=decided_at + timedelta(seconds=1)'
reject_fixed "${e2e_root}/run_real_journey.py" 'datetime.now(timezone.utc) - timedelta(seconds=5)'
require_fixed "${e2e_root}/run_real_journey.py" '_authoritative_denied_action_state'
require_fixed "${e2e_root}/run_real_journey.py" '_denied_action_evidence'
require_fixed "${e2e_root}/run_real_journey.py" 'authoritative denied action state changed before dispatch'
require_fixed "${e2e_root}/build_evidence.py" 'step observations must be strictly chronological'
require_fixed "${e2e_root}/build_evidence.py" '_validate_trial_report_scope'
require_fixed "${e2e_root}/build_evidence.py" 'contains a record outside this trial'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'step-observations.jsonl'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'snapshot_id is not bound to all snapshot inputs'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'completed step observations must be strictly chronological'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'IDENTIFIER_PRODUCING_STEPS'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'STEP_EVIDENCE_REFS'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'EXPECTED_FULL_PROFILE_IMAGE_SERVICES'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'REVIEWED_IMMUTABLE_IMAGE_REFERENCES'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'complete reviewed full-profile service inventory'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'observed Shuffle action runtime image ID'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'a non-passed evaluation step cannot claim a published evaluation'
require_fixed "${e2e_root}/validate_evidence_manifest.py" '$.snapshot.host_architecture is not supported'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'schema host architecture contract drifted'
require_fixed \
  "${e2e_root}/validate_evidence_manifest.py" \
  'schema current image inventory contract drifted'
require_fixed "${schema}" '"minItems": 13'
require_fixed "${schema}" '"maxItems": 13'
require_fixed "${schema}" '"legacy_blocked_identity"'
require_fixed "${schema}" '"legacy_blocked_image_inventory"'
require_fixed "${schema}" '"current_image_inventory"'
require_fixed "${schema}" '"wazuh_rule_id": {"enum": ["5710", null]}'
require_fixed "${schema}" '"runtime_image_id"'
require_fixed "${schema}" '"enum": ["arm64", "aarch64", "amd64", "x86_64"]'
require_fixed "${e2e_root}/validate_evidence_manifest.py" '"--runtime-images"'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'steps after a failure must be not_run'
require_fixed \
  "${e2e_root}/validate_evidence_manifest.py" \
  'must be null when {producing_step} did not pass'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'NEGATIVE_CASE_PRODUCING_STEPS'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'outside the reviewed detection contract'
require_fixed \
  "${e2e_root}/validate_evidence_manifest.py" \
  'approval confirmation must follow denial proof'
require_fixed \
  "${e2e_root}/validate_evidence_manifest.py" \
  'evaluation time must match the evaluation step observation'
require_fixed "${e2e_root}/build_evidence.py" 'approval confirmation must follow denial proof'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'OWNED_LIMITATION_STATUSES'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'historical approval-blocked limitation contract is incomplete'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'LEGACY_BLOCKED_MANIFEST_SHA256'
require_fixed "${e2e_root}/validate_evidence_manifest.py" '_is_legacy_blocked_manifest'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'wazuh_reconciliation_ids'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'a non-passed denial step cannot claim denial proof'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'an approved dispatch requires requester and approver identities'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'restart proof must contain exactly the reviewed authoritative identifiers'
require_fixed "${e2e_root}/run_real_journey.py" '_verify_restart_records'
require_fixed "${e2e_root}/run_real_journey.py" 'restart lost wazuh_reconciliation_id='
require_fixed "${e2e_root}/run_real_journey.py" '"approval_requirement_override": "human_required"'
require_fixed "${e2e_root}/build_evidence.py" '_validate_status_snapshot'
require_fixed "${e2e_root}/build_evidence.py" 'uses a different control-plane image'
require_fixed "${e2e_root}/build_evidence.py" '_validate_wazuh_reconciliation_scope'
require_fixed "${e2e_root}/build_evidence.py" '_validate_preparation_journey_binding'
require_fixed "${e2e_root}/build_evidence.py" '_load_wazuh_observations'
require_fixed "${e2e_root}/build_evidence.py" '_validate_wazuh_output_contract'
require_fixed \
  "${e2e_root}/build_evidence.py" \
  'f"report {delivery_name} reconciliation is not bound "'
require_fixed \
  "${e2e_root}/build_evidence.py" \
  'journey output embedded report does not match the retained report'
require_fixed "${e2e_root}/build_evidence.py" '_validate_step_observation_sources'
require_fixed "${e2e_root}/build_evidence.py" 'does not use the authoritative'
require_fixed "${e2e_root}/build_evidence.py" '_parse_prerequisite_evaluation'
require_fixed "${e2e_root}/build_evidence.py" 'images.json does not match the snapshotted image inventory'
require_fixed "${e2e_root}/build_evidence.py" 'journey Shuffle workflow version is not reviewed'
require_fixed "${e2e_root}/build_evidence.py" 'ACTION_EXECUTION_REPORT_BINDINGS'
require_fixed "${e2e_root}/build_evidence.py" 'report action execution is not bound to the journey'
require_fixed "${e2e_root}/build_evidence.py" '_validate_snapshot_provenance'
require_fixed \
  "${e2e_root}/build_evidence.py" \
  'captured Compose render does not match the trial digest'
require_fixed \
  "${e2e_root}/build_evidence.py" \
  'Compose digest record does not match the trial digest'
require_fixed "${e2e_root}/build_evidence.py" '_validate_report_record'
require_fixed "${e2e_root}/build_evidence.py" '"approved action request"'
require_fixed "${e2e_root}/build_evidence.py" '"approved decision"'
require_fixed "${e2e_root}/build_evidence.py" '_reject_duplicate_keys'
require_fixed \
  "${e2e_root}/build_evidence.py" \
  'report action reconciliation is not bound to the journey'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'does not match the validator schema'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'load_json_with_sha256'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'action request IDs must remain distinct'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'denied and approved decision IDs must remain distinct'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'Shuffle workflow ID is not bound to the snapshot'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'Shuffle workflow version is not the reviewed version'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'Shuffle execution ID must use canonical UUID form'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'evaluation digest does not match evaluation-record.json artifact'
require_fixed "${e2e_root}/validate_evidence_manifest.py" 'PASSED_VERDICT'
require_fixed \
  "${e2e_root}/validate_evidence_manifest.py" \
  'cleanup must be either unobserved or completed non-destructively'
require_fixed "${e2e_root}/run_real_journey.py" '"idempotency_key": action.idempotency_key'
require_fixed "${e2e_root}/run_real_journey.py" 'NEGATIVE_RECONCILIATION_OUTCOMES'
require_fixed "${e2e_root}/run_real_journey.py" '_verify_restart_report_contents'
reject_fixed "${schema}" 'integration_trial_passed_ga_not_accepted'
require_fixed "${lab_root}/run-e2e-trial.sh" 'verify-restart'
require_fixed "${lab_root}/run-e2e-trial.sh" 'run_reviewed_lab_command()'
require_fixed "${lab_root}/run-e2e-trial.sh" 'run_reviewed_lab_command "${LAB_DIR}/test-wazuh-intake.sh"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'run_reviewed_lab_startup "${LAB_DIR}/up.sh" full'
require_fixed "${lab_root}/run-e2e-trial.sh" 'capture_reviewed_compose_config'
require_fixed "${lab_root}/run-e2e-trial.sh" 'assert_compose_snapshot'
require_fixed "${lab_root}/run-e2e-trial.sh" '--compose-config "${compose_render_output}"'
require_fixed "${lab_root}/run-e2e-trial.sh" '--compose-digest-record "${compose_digest_output}"'
require_fixed \
  "${lab_root}/run-e2e-trial.sh" \
  '--expected-repository-revision "${repository_revision}"'
require_fixed "${lab_root}/run-e2e-trial.sh" '--expected-compose-sha256 "${compose_render_sha256}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'rm -f "${compose_render_output}"'
require_fixed "${e2e_root}/validate_evidence_manifest.py" '"compose-config.sha256"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'record_step 15 "record_prerequisite_evaluation"'
reject_fixed "${lab_root}/run-e2e-trial.sh" 'record_step 15 "publish_prerequisite_evaluation"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'record_step 2 "record_lab_health_after_snapshot"'
reject_fixed "${lab_root}/run-e2e-trial.sh" 'record_step 2 "start_lab_and_record_health"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'startup_status_output='
require_fixed "${lab_root}/run-e2e-trial.sh" 'initial_status_output='
require_fixed "${lab_root}/run-e2e-trial.sh" 'restart_status_output='
require_fixed "${lab_root}/run-e2e-trial.sh" 'workflow_snapshot_output='
require_fixed "${lab_root}/run-e2e-trial.sh" 'workflow_predispatch_output='
require_fixed "${lab_root}/run-e2e-trial.sh" 'capture_reviewed_shuffle_action_image'
require_fixed "${lab_root}/run-e2e-trial.sh" 'ensure_reviewed_shuffle_action_service'
require_fixed "${lab_root}/run-e2e-trial.sh" 'assert_reviewed_shuffle_action_service'
require_fixed "${lab_root}/run-e2e-trial.sh" 'docker_lab service create'
require_fixed "${lab_root}/run-e2e-trial.sh" '.Image == $image_id'
require_fixed "${lab_root}/run-e2e-trial.sh" 'postdispatch_shuffle_action_image'
require_fixed "${lab_root}/run-e2e-trial.sh" 'run_reviewed_journey'
require_fixed "${lab_root}/run-e2e-trial.sh" 'Shuffle action image identity changed after the trial snapshot'
require_fixed "${lab_root}/run-e2e-trial.sh" 'compose_scope full ps -aq'
require_fixed "${lab_root}/run-e2e-trial.sh" 'live Shuffle workflow changed after the trial snapshot'
require_fixed "${lab_root}/run-e2e-trial.sh" '[[ -t 0 && -t 1 ]]'
require_fixed "${lab_root}/run-e2e-trial.sh" '"APPROVE ${approval_challenge}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'display dialog promptText'
require_fixed "${lab_root}/run-e2e-trial.sh" '"shuffle-action-image"'
require_fixed "${lab_root}/run-e2e-trial.sh" '"shuffle-worker-image"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'SHUFFLE_WORKER_IMAGE='
require_fixed "${lab_root}/run-e2e-trial.sh" '--slurpfile report "${report_output}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'report: $report[0]'
require_fixed "${lab_root}/run-e2e-trial.sh" '--wazuh-reconciliation-id'
require_fixed "${lab_root}/run-e2e-trial.sh" 'docker_lab inspect ${container_ids}'
require_fixed "${lab_root}/run-e2e-trial.sh" 'docker_context="${AEGISOPS_LAB_DOCKER_CONTEXT}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'colima_profile="${AEGISOPS_LAB_COLIMA_PROFILE}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'final_artifacts=' 
require_fixed "${lab_root}/run-e2e-trial.sh" 'publication_manifest_published=false'
require_fixed "${lab_root}/run-e2e-trial.sh" 'publication_manifest_moved=false'
require_fixed "${lab_root}/run-e2e-trial.sh" 'mv "${final_artifacts}/evidence.json" "${final_evidence}"'
require_fixed \
  "${lab_root}/run-e2e-trial.sh" \
  'python3 "${validator}" "${schema}" "${final_evidence}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'no passing manifest was published'
require_fixed "${lab_root}/run-e2e-trial.sh" '"${LAB_DIR}/cleanup.sh"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'assert_repository_snapshot'
require_fixed "${lab_root}/run-e2e-trial.sh" 'status --porcelain=v1 --untracked-files=all'

python3 -m json.tool "${schema}" >/dev/null
python3 "${validator}" "${schema}" "${sample}"
bash -n \
  "${lab_root}/run-e2e-trial.sh" \
  "${lab_root}/test-wazuh-intake.sh"
python3 -m compileall -q \
  "${e2e_root}" \
  "${repo_root}/control-plane/tests/test_phase67_4_real_service_e2e.py"
(
  cd "${repo_root}"
  python3 -m unittest control-plane/tests/test_phase67_4_real_service_e2e.py
)

echo "PASS: Phase 67.4 real-service E2E evidence and prerequisite evaluation verified."
