#!/usr/bin/env bash

set -euo pipefail
umask 077

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_command docker
require_command git
require_command jq
require_command openssl
require_command python3
require_command curl
require_runtime_environment
[[ "${AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE:-}" == "real_http" ]] \
  || fail "real Shuffle transport is not enabled; run ${LAB_DIR}/bootstrap-shuffle.sh"

# shellcheck source=shuffle/reviewed-app-image.env
source "${LAB_DIR}/shuffle/reviewed-app-image.env"
shuffle_tools_image="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}:${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_TAG}"
shuffle_tools_immutable_ref="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}@${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST}"
shuffle_action_service="shuffle-tools_1-2-0"
shuffle_action_service_port=33334
shuffle_action_network="shuffle-executions"
shuffle_backend_url="$(
  printf 'http://%s-shuffle-backend-1:5001' \
    "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:-aegisops-phase67-lab}"
)"
shuffle_action_publish_spec="$(
  printf 'name=app-port,published=%s,target=%s,protocol=tcp,mode=ingress' \
    "${shuffle_action_service_port}" \
    "${shuffle_action_service_port}"
)"
schema="${LAB_DIR}/e2e/evidence-manifest.schema.json"
validator="${LAB_DIR}/e2e/validate_evidence_manifest.py"
builder="${LAB_DIR}/e2e/build_evidence.py"
evaluation="${REPO_ROOT}/docs/phase-67-prerequisite-evaluation.md"
reviewed_workflow="${LAB_DIR}/shuffle/harmless-local-log-workflow.json"
workflow_validator="${LAB_DIR}/shuffle/validate_preserved_workflow.py"

assert_repository_snapshot() {
  [[ "$(git -C "${REPO_ROOT}" rev-parse HEAD)" == "${repository_revision}" ]] \
    || fail "repository revision changed during the E2E trial"
  [[ -z "$(git -C "${REPO_ROOT}" status --porcelain=v1 --untracked-files=all)" ]] \
    || fail "real E2E evidence requires the reviewed repository worktree to remain clean"
}

run_reviewed_lab_command() {
  assert_repository_snapshot
  "$@"
}

run_reviewed_journey() {
  assert_repository_snapshot
  compose_scope full exec -T \
    -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE="${shuffle_tools_image}" \
    -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST}" \
    -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_IMMUTABLE_REF="${shuffle_tools_immutable_ref}" \
    control-plane \
    python3 /opt/aegisops/phase67-e2e/run_real_journey.py \
      "$@"
}

capture_reviewed_compose_config() {
  assert_repository_snapshot
  compose_scope full config
}

assert_compose_snapshot() {
  local current_compose_sha256
  current_compose_sha256="$(
    capture_reviewed_compose_config |
      openssl dgst -sha256 -r |
      awk '{print $1}'
  )"
  [[ "${current_compose_sha256}" == "${compose_render_sha256}" ]] \
    || fail "rendered Compose configuration changed during the E2E trial"
}

run_reviewed_lab_startup() {
  assert_repository_snapshot
  assert_compose_snapshot
  "$@"
}

assert_reviewed_shuffle_action_service() {
  local service_metadata
  local service_image
  local task_ids
  local task_metadata
  local task_container_ids
  local container_metadata
  local pinned_image_id

  service_metadata="$(docker_lab service inspect "${shuffle_action_service}")"
  service_image="$(
    jq -er '.[0].Spec.TaskTemplate.ContainerSpec.Image' \
      <<<"${service_metadata}"
  )"
  [[ "${service_image}" == "${shuffle_tools_immutable_ref}" ]] \
    || fail "Shuffle action service is not pinned to the reviewed digest"
  jq -e \
    --arg phase "67.4" \
    --arg component "shuffle-action-image" \
    --argjson port "${shuffle_action_service_port}" '
      .[0] as $service
      | $service.Spec.Labels["com.aegisops.lab.phase"] == $phase
      and $service.Spec.Labels["com.aegisops.lab.component"] == $component
      and $service.Spec.Mode.Replicated.Replicas == 1
      and (
        [
          $service.Endpoint.Spec.Ports[]
          | select(
              .Name == "app-port"
              and .PublishedPort == $port
              and .TargetPort == $port
            )
        ]
        | length == 1
      )
    ' <<<"${service_metadata}" >/dev/null \
    || fail "Shuffle action service does not match the reviewed lab contract"

  task_ids="$(
    docker_lab service ps \
      --filter desired-state=running \
      --quiet \
      "${shuffle_action_service}"
  )"
  [[ "$(wc -w <<<"${task_ids}")" -eq 1 ]] \
    || fail "Shuffle action service does not have exactly one running task"
  # shellcheck disable=SC2086
  task_metadata="$(docker_lab inspect ${task_ids})"
  task_container_ids="$(
    jq -er '
      [.[].Status.ContainerStatus.ContainerID | select(length > 0)]
      | if length == 1 then .[]
        else error("expected one Shuffle action task container")
        end
    ' <<<"${task_metadata}"
  )"
  container_metadata="$(docker_lab inspect "${task_container_ids}")"
  pinned_image_id="$(
    docker_lab image inspect \
      "${shuffle_tools_immutable_ref}" \
      --format '{{.Id}}'
  )"
  jq -e --arg image_id "${pinned_image_id}" '
    length == 1 and all(.[]; .Image == $image_id)
  ' <<<"${container_metadata}" >/dev/null \
    || fail "Shuffle action task did not use the reviewed image ID"
}

ensure_reviewed_shuffle_action_service() {
  local attempt

  assert_repository_snapshot
  for attempt in {1..60}; do
    if docker_lab network inspect "${shuffle_action_network}" >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
  docker_lab network inspect "${shuffle_action_network}" >/dev/null 2>&1 \
    || fail "Shuffle execution network was not initialized"

  if docker_lab service inspect "${shuffle_action_service}" >/dev/null 2>&1; then
    assert_reviewed_shuffle_action_service
    return
  fi

  docker_lab service create \
    --detach=true \
    --name "${shuffle_action_service}" \
    --label com.aegisops.lab.phase=67.4 \
    --label com.aegisops.lab.component=shuffle-action-image \
    --network "${shuffle_action_network}" \
    --publish "${shuffle_action_publish_spec}" \
    --replicas 1 \
    --restart-condition any \
    --log-driver json-file \
    --log-opt max-size=10m \
    --env "SHUFFLE_APP_EXPOSED_PORT=${shuffle_action_service_port}" \
    --env SHUFFLE_SWARM_CONFIG=run \
    --env SHUFFLE_LOGS_DISABLED=true \
    --env "CALLBACK_URL=${shuffle_backend_url}" \
    --env "BASE_URL=${shuffle_backend_url}" \
    --env DOCKER_API_VERSION=1.40 \
    --env SHUFFLE_APP_SDK_TIMEOUT=300 \
    --env TZ=Europe/Amsterdam \
    "${shuffle_tools_immutable_ref}" \
    >/dev/null

  for attempt in {1..120}; do
    if [[ "$(
      docker_lab service ps \
        --filter desired-state=running \
        --format '{{.CurrentState}}' \
        "${shuffle_action_service}" 2>/dev/null \
        | sed -n '/^Running /p' \
        | wc -l \
        | tr -d ' '
    )" -eq 1 ]]; then
      break
    fi
    sleep 1
  done
  assert_reviewed_shuffle_action_service
}

remove_reviewed_shuffle_action_service() {
  local attempt
  local service_metadata

  if ! service_metadata="$(
    docker_lab service inspect "${shuffle_action_service}" 2>/dev/null
  )"; then
    return
  fi
  jq -e '
    .[0].Spec.Labels["com.aegisops.lab.phase"] == "67.4"
    and .[0].Spec.Labels["com.aegisops.lab.component"]
      == "shuffle-action-image"
  ' <<<"${service_metadata}" >/dev/null \
    || fail "refusing to remove an unowned Shuffle action service"
  docker_lab service rm "${shuffle_action_service}" >/dev/null
  for attempt in {1..60}; do
    if [[ -z "$(
      docker_lab ps \
        --all \
        --quiet \
        --filter \
          "label=com.docker.swarm.service.name=${shuffle_action_service}"
    )" ]]; then
      return
    fi
    sleep 1
  done
  fail "Shuffle action service tasks did not stop during cleanup"
}

[[ -f "${evaluation}" ]] \
  || fail "Phase 67 prerequisite evaluation is missing: ${evaluation}"
repository_revision="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
assert_repository_snapshot
captured_prefix="$(date -u '+%Y%m%dT%H%M%SZ')"
trial_run_id="phase67-e2e-${captured_prefix}-$(openssl rand -hex 6)"
staging_dir="$(mktemp -d "${AEGISOPS_LAB_EVIDENCE_DIR}/.phase67-e2e.XXXXXX")"
wazuh_output="${staging_dir}/wazuh-output.txt"
wazuh_manifest_output="${staging_dir}/wazuh-manifest.json"
preparation_output="${staging_dir}/preparation.json"
journey_output="${staging_dir}/journey.json"
restart_output="${staging_dir}/restart.json"
report_output="${staging_dir}/report.json"
snapshot_output="${staging_dir}/snapshot.json"
compose_render_output="$(
  mktemp "${AEGISOPS_LAB_EVIDENCE_DIR}/.phase67-compose-render.XXXXXX"
)"
compose_digest_output="${staging_dir}/compose-config.sha256"
images_output="${staging_dir}/images.json"
evaluation_record_output="${staging_dir}/evaluation-record.json"
observations_output="${staging_dir}/step-observations.jsonl"
startup_status_output="${staging_dir}/startup-status.txt"
initial_status_output="${staging_dir}/initial-status.txt"
restart_status_output="${staging_dir}/restart-status.txt"
workflow_snapshot_output="${staging_dir}/workflow-snapshot.json"
workflow_predispatch_output="${staging_dir}/workflow-pre-dispatch.json"
evidence_output="${staging_dir}/evidence.json"
final_evidence="${AEGISOPS_LAB_EVIDENCE_DIR}/${trial_run_id}.json"
final_report="${AEGISOPS_LAB_EVIDENCE_DIR}/${trial_run_id}-report.json"
final_artifacts="${AEGISOPS_LAB_EVIDENCE_DIR}/${trial_run_id}-artifacts"
cleaned=false
publication_report_published=false
publication_artifacts_published=false
publication_manifest_moved=false
publication_manifest_published=false

observed_now() {
  python3 -c 'from datetime import datetime, timezone; print(datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"))'
}

record_step() {
  local step="$1"
  local name="$2"
  local observed_at="${3:-$(observed_now)}"

  jq -cn \
    --argjson step "${step}" \
    --arg name "${name}" \
    --arg observed_at "${observed_at}" \
    '{step: $step, name: $name, observed_at: $observed_at}' \
    >>"${observations_output}"
}

retain_status_evidence() {
  local command_output="$1"
  local destination="$2"
  local source

  source="$(
    printf '%s\n' "${command_output}" |
      sed -n 's/^evidence=//p' |
      tail -n 1
  )"
  [[ -f "${source}" ]] || fail "lab status evidence was not published"
  cp "${source}" "${destination}"
}

canonical_json_sha256() {
  python3 - "$1" <<'PY'
from pathlib import Path
import hashlib
import json
import sys

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
print(hashlib.sha256(encoded).hexdigest())
PY
}

capture_reviewed_shuffle_workflow() (
  local destination="$1"
  local auth_header_path

  auth_header_path="$(mktemp "${staging_dir}/.shuffle-auth.XXXXXX")"
  trap 'rm -f -- "${auth_header_path}"' EXIT
  printf 'Authorization: Bearer %s\n' \
    "$(<"${AEGISOPS_LAB_SECRET_DIR}/shuffle-api-key")" \
    >"${auth_header_path}"
  chmod 600 "${auth_header_path}"
  curl \
    --silent \
    --show-error \
    --fail-with-body \
    --cacert "${AEGISOPS_LAB_PROXY_CERT_DIR}/lab.crt" \
    --resolve "shuffle.localhost:${AEGISOPS_LAB_PROXY_PORT}:127.0.0.1" \
    --connect-timeout 5 \
    --max-time 30 \
    -H "@${auth_header_path}" \
    "https://shuffle.localhost:${AEGISOPS_LAB_PROXY_PORT}/api/v1/workflows/${shuffle_api_workflow_id}" \
    >"${destination}"
  python3 \
    "${workflow_validator}" \
    "${reviewed_workflow}" \
    "${shuffle_api_workflow_id}" \
    <"${destination}" \
    >/dev/null
)

capture_reviewed_shuffle_action_image() {
  local pinned_metadata
  local runtime_metadata
  local pinned_image_id
  local runtime_image_id
  local runtime_immutable_ref

  assert_reviewed_shuffle_action_service
  pinned_metadata="$(docker_lab image inspect "${shuffle_tools_immutable_ref}")"
  runtime_metadata="$(docker_lab image inspect "${shuffle_tools_image}")"
  pinned_image_id="$(jq -er '.[0].Id' <<<"${pinned_metadata}")"
  runtime_image_id="$(jq -er '.[0].Id' <<<"${runtime_metadata}")"
  runtime_immutable_ref="$(
    jq -er \
      --arg repository "${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}@" '
        [.[0].RepoDigests[] | select(startswith($repository))]
        | unique
        | if length == 1 then .[0]
          else error("expected one repository digest for the Shuffle action image")
          end
      ' <<<"${runtime_metadata}"
  )"
  [[ "${runtime_image_id}" == "${pinned_image_id}" ]] \
    || fail "Shuffle action runtime tag does not resolve to the reviewed image ID"
  [[ "${runtime_immutable_ref}" == "${shuffle_tools_immutable_ref}" ]] \
    || fail "Shuffle action runtime tag does not retain the reviewed digest"

  jq -cn \
    --arg immutable_reference "${runtime_immutable_ref}" \
    --arg runtime_image_id "${runtime_image_id}" '
      {
        service: "shuffle-action-image",
        immutable_reference: $immutable_reference,
        runtime_image_id: $runtime_image_id
      }
    '
}

cleanup_on_exit() {
  local rc=$?
  rm -f "${compose_render_output}" >/dev/null 2>&1 || true
  remove_reviewed_shuffle_action_service >/dev/null 2>&1 || true
  if [[ "${cleaned}" != true ]]; then
    "${LAB_DIR}/cleanup.sh" >/dev/null 2>&1 || true
  fi
  if [[ "${rc}" -ne 0 ]]; then
    if [[ "${publication_manifest_published}" != true ]]; then
      if [[ "${publication_manifest_moved}" == true ]] \
        && [[ -f "${final_evidence}" ]] \
        && [[ -d "${final_artifacts}" ]] \
        && [[ ! -e "${final_artifacts}/evidence.json" ]]; then
        mv "${final_evidence}" \
          "${final_artifacts}/evidence.json" >/dev/null 2>&1 || true
      fi
      if [[ "${publication_artifacts_published}" == true ]] \
        && [[ -d "${final_artifacts}" ]] \
        && [[ ! -e "${staging_dir}" ]]; then
        mv "${final_artifacts}" "${staging_dir}" >/dev/null 2>&1 || true
      fi
      if [[ "${publication_report_published}" == true ]] \
        && [[ -f "${final_report}" ]] \
        && [[ -d "${staging_dir}" ]]; then
        mv "${final_report}" "${report_output}" >/dev/null 2>&1 || true
      fi
    fi
    echo "BLOCKED: Phase 67.4 real-service E2E trial failed; no passing manifest was published" >&2
  fi
  exit "${rc}"
}
trap cleanup_on_exit EXIT

assert_repository_snapshot
capture_reviewed_compose_config >"${compose_render_output}"
compose_render_sha256="$(
  openssl dgst -sha256 -r "${compose_render_output}" | awk '{print $1}'
)"
printf '%s  compose-config.yml\n' \
  "${compose_render_sha256}" >"${compose_digest_output}"
schema_sha256="$(openssl dgst -sha256 -r "${schema}" | awk '{print $1}')"
reviewed_workflow_sha256="$(
  openssl dgst -sha256 -r "${reviewed_workflow}" | awk '{print $1}'
)"
shuffle_api_workflow_id="${AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID}"
[[ "${shuffle_api_workflow_id}" =~ ^[0-9a-fA-F-]{36}$ ]] \
  || fail "real Shuffle workflow ID is not configured"

run_reviewed_lab_command "${LAB_DIR}/pin-shuffle-app-image.sh"
startup_output="$(run_reviewed_lab_startup "${LAB_DIR}/up.sh" full)"
printf '%s\n' "${startup_output}"
retain_status_evidence "${startup_output}" "${startup_status_output}"
run_reviewed_lab_command ensure_reviewed_shuffle_action_service

container_ids="$(compose_scope full ps -aq)"
[[ -n "${container_ids}" ]] || fail "full lab started no containers"
# shellcheck disable=SC2086
docker_lab inspect ${container_ids} |
  jq -S '
    map(
      . as $container
      | ($container.Config.Labels["com.docker.compose.service"] // "unknown") as $service
      | {
          service: $service,
          immutable_reference: (
            if ($container.Config.Image | contains("@sha256:"))
            then $container.Config.Image
            else ($service + "@" + $container.Image)
            end
          )
        }
    )
    | sort_by(.service)
  ' >"${images_output}"
shuffle_worker_immutable_ref="$(
  # shellcheck disable=SC2086
  docker_lab inspect ${container_ids} |
    jq -er '
      [
        .[]
        | select(
            .Config.Labels["com.docker.compose.service"]
            == "shuffle-orborus"
          )
        | .Config.Env[]
        | select(startswith("SHUFFLE_WORKER_IMAGE="))
        | ltrimstr("SHUFFLE_WORKER_IMAGE=")
      ]
      | unique
      | if length == 1 then .[0]
        else error("expected one Shuffle worker image")
        end
    '
)"
[[ "${shuffle_worker_immutable_ref}" == *@sha256:* ]] \
  || fail "Shuffle worker image is not digest-pinned"
shuffle_action_image="$(capture_reviewed_shuffle_action_image)"
jq \
  --argjson action_image "${shuffle_action_image}" \
  --arg worker_reference "${shuffle_worker_immutable_ref}" '
    . + [
      $action_image,
      {
        service: "shuffle-worker-image",
        immutable_reference: $worker_reference
      }
    ]
    | sort_by(.service)
  ' \
  "${images_output}" >"${images_output}.next"
mv "${images_output}.next" "${images_output}"
python3 "${validator}" --runtime-images "${images_output}"
capture_reviewed_shuffle_workflow "${workflow_snapshot_output}"
live_workflow_sha256="$(canonical_json_sha256 "${workflow_snapshot_output}")"
runtime_artifact_sha256="$(
  sed -n 's/^repository_runtime_artifact_sha256=//p' \
    "${startup_status_output}" |
    tail -n 1
)"
[[ "${runtime_artifact_sha256}" =~ ^[0-9a-f]{64}$ ]] \
  || fail "startup status lacks the runtime artifact digest"
docker_context="${AEGISOPS_LAB_DOCKER_CONTEXT}"
colima_profile="${AEGISOPS_LAB_COLIMA_PROFILE}"
host_architecture="$(uname -m)"
snapshot_staging="${snapshot_output}.staging"
jq -n \
  --arg trial_run_id "${trial_run_id}" \
  --arg repository_revision "${repository_revision}" \
  --arg compose_sha256 "${compose_render_sha256}" \
  --arg evidence_schema_sha256 "${schema_sha256}" \
  --arg runtime_artifact_sha256 "${runtime_artifact_sha256}" \
  --arg shuffle_api_workflow_id "${shuffle_api_workflow_id}" \
  --arg shuffle_reviewed_workflow_sha256 "${reviewed_workflow_sha256}" \
  --arg shuffle_live_workflow_sha256 "${live_workflow_sha256}" \
  --arg host_architecture "${host_architecture}" \
  --arg docker_context "${docker_context}" \
  --arg colima_profile "${colima_profile}" \
  --slurpfile images "${images_output}" '
    {
      trial_run_id: $trial_run_id,
      repository_revision: $repository_revision,
      compose_sha256: $compose_sha256,
      evidence_schema_sha256: $evidence_schema_sha256,
      runtime_artifact_sha256: $runtime_artifact_sha256,
      shuffle_api_workflow_id: $shuffle_api_workflow_id,
      shuffle_reviewed_workflow_sha256: $shuffle_reviewed_workflow_sha256,
      shuffle_live_workflow_sha256: $shuffle_live_workflow_sha256,
      host_architecture: $host_architecture,
      docker_context: $docker_context,
      colima_profile: $colima_profile,
      selected_profile: "full",
      images: $images[0]
    }
  ' >"${snapshot_staging}"
snapshot_id="$(
  python3 - "${snapshot_staging}" <<'PY'
from pathlib import Path
import hashlib
import json
import sys

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
print("phase67-snapshot-" + hashlib.sha256(encoded).hexdigest()[:16])
PY
)"
jq --arg snapshot_id "${snapshot_id}" \
  '. + {snapshot_id: $snapshot_id}' \
  "${snapshot_staging}" >"${snapshot_output}"
rm -f "${snapshot_staging}"
record_step 1 "capture_immutable_snapshot"

initial_status_command_output="$(
  run_reviewed_lab_command "${LAB_DIR}/status.sh" full --write-evidence
)"
printf '%s\n' "${initial_status_command_output}"
retain_status_evidence \
  "${initial_status_command_output}" \
  "${initial_status_output}"
record_step 2 "record_lab_health_after_snapshot"

AEGISOPS_LAB_TRIAL_SCOPE=full \
  run_reviewed_lab_command "${LAB_DIR}/test-wazuh-intake.sh" \
  | tee "${wazuh_output}"
wazuh_evidence="$(
  sed -n 's/^evidence=//p' "${wazuh_output}" | tail -n 1
)"
[[ -f "${wazuh_evidence}" ]] \
  || fail "real Wazuh trial did not publish its evidence manifest"
cp "${wazuh_evidence}" "${wazuh_manifest_output}"
aegisops_alert_id="$(jq -er '.aegisops_alert_id' "${wazuh_evidence}")"
wazuh_reconciliation_args=()
while IFS= read -r reconciliation_id; do
  wazuh_reconciliation_args+=(--wazuh-reconciliation-id "${reconciliation_id}")
done < <(
  jq -er '
    [.first_delivery.reconciliation_id, .duplicate_delivery.reconciliation_id]
    | unique[]
  ' "${wazuh_evidence}"
)
[[ "${#wazuh_reconciliation_args[@]}" -gt 0 ]] \
  || fail "Wazuh trial evidence lacks reconciliation identifiers"
record_step 3 \
  "trigger_real_wazuh_detection" \
  "$(sed -n 's/^step_observation\.trigger_real_wazuh_detection=//p' "${wazuh_output}" | tail -n 1)"
record_step 4 \
  "admit_wazuh_alert" \
  "$(sed -n 's/^step_observation\.admit_wazuh_alert=//p' "${wazuh_output}" | tail -n 1)"

run_reviewed_journey \
  prepare \
  --trial-id "${trial_run_id}" \
  --alert-id "${aegisops_alert_id}" \
  "${wazuh_reconciliation_args[@]}" \
  >"${preparation_output}"
record_step 5 \
  "promote_alert_to_case" \
  "$(jq -er '.step_observations.promote_alert_to_case' "${preparation_output}")"
record_step 6 \
  "create_reviewed_action_request" \
  "$(jq -er '.step_observations.create_reviewed_action_request' "${preparation_output}")"
record_step 7 \
  "prove_denied_action_non_dispatch" \
  "$(jq -er '.step_observations.prove_denied_action_non_dispatch' "${preparation_output}")"

approval_challenge="$(jq -er '.approval_challenge' "${preparation_output}")"
action_request_id="$(jq -er '.action_request_id' "${preparation_output}")"
payload_hash="$(jq -er '.payload_hash' "${preparation_output}")"
approver_identity="local-operator:$(id -un)"
if [[ "$(uname -s)" == "Darwin" ]] && command -v osascript >/dev/null 2>&1; then
  approval_method="macos_operator_dialog"
  if ! approval_response="$(
    osascript - \
      "${action_request_id}" \
      "${payload_hash}" \
      "${approval_challenge}" \
      "${approver_identity}" <<'APPLESCRIPT'
on run arguments
  set actionRequestId to item 1 of arguments
  set payloadHash to item 2 of arguments
  set approvalChallenge to item 3 of arguments
  set approverIdentity to item 4 of arguments
  set promptText to "Approve the reviewed harmless local AegisOps action?" & return & return & "action_request_id=" & actionRequestId & return & "payload_hash=" & payloadHash & return & "challenge=" & approvalChallenge & return & "approver_identity=" & approverIdentity
  set response to display dialog promptText with title "AegisOps Phase 67.4 Approval" buttons {"Deny", "Approve"} default button "Approve" cancel button "Deny" with icon caution
  return button returned of response
end run
APPLESCRIPT
  )"; then
    fail "interactive macOS operator approval was denied"
  fi
  [[ "${approval_response}" == "Approve" ]] \
    || fail "interactive macOS operator approval was not granted"
else
  [[ -t 0 && -t 1 ]] \
    || fail "interactive human approval requires a terminal or macOS dialog"
  approval_method="tty_challenge"
  printf '%s\n' \
    "Human approval required for the reviewed harmless local action." \
    "action_request_id=${action_request_id}" \
    "payload_hash=${payload_hash}" \
    "approver_identity=${approver_identity}" \
    "Type exactly: APPROVE ${approval_challenge}"
  IFS= read -r approval_response
  [[ "${approval_response}" == "APPROVE ${approval_challenge}" ]] \
    || fail "interactive approval was not granted"
fi

capture_reviewed_shuffle_workflow "${workflow_predispatch_output}"
[[ "$(canonical_json_sha256 "${workflow_predispatch_output}")" == "${live_workflow_sha256}" ]] \
  || fail "live Shuffle workflow changed after the trial snapshot"
[[ "$(openssl dgst -sha256 -r "${reviewed_workflow}" | awk '{print $1}')" == "${reviewed_workflow_sha256}" ]] \
  || fail "reviewed Shuffle workflow changed after the trial snapshot"
predispatch_shuffle_action_image="$(capture_reviewed_shuffle_action_image)"
[[ "${predispatch_shuffle_action_image}" == "${shuffle_action_image}" ]] \
  || fail "Shuffle action image identity changed after the trial snapshot"
run_reviewed_journey \
  execute \
  --trial-id "${trial_run_id}" \
  --approver-identity "${approver_identity}" \
  --approval-challenge "${approval_challenge}" \
  --approval-method "${approval_method}" \
  <"${preparation_output}" \
  >"${journey_output}"
postdispatch_shuffle_action_image="$(capture_reviewed_shuffle_action_image)"
[[ "${postdispatch_shuffle_action_image}" == "${shuffle_action_image}" ]] \
  || fail "Shuffle action service changed during reviewed execution"
for step_spec in \
  "8:approve_and_dispatch_real_shuffle_action" \
  "9:capture_authenticated_shuffle_receipt" \
  "10:reconcile_from_aegisops_records" \
  "11:export_redacted_aegisops_report" \
  "12:replay_deliveries_for_idempotency" \
  "13:run_negative_cases"; do
  step_number="${step_spec%%:*}"
  step_name="${step_spec#*:}"
  record_step \
    "${step_number}" \
    "${step_name}" \
    "$(jq -er --arg name "${step_name}" '.journey.step_observations[$name]' "${journey_output}")"
done
python3 - "${journey_output}" "${report_output}" <<'PY'
import json
from pathlib import Path
import sys

source = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
Path(sys.argv[2]).write_text(
    json.dumps(source["report"], separators=(",", ":"), sort_keys=True),
    encoding="utf-8",
)
PY

run_reviewed_lab_command remove_reviewed_shuffle_action_service
run_reviewed_lab_command "${LAB_DIR}/down.sh"
restart_up_output="$(run_reviewed_lab_startup "${LAB_DIR}/up.sh" full)"
printf '%s\n' "${restart_up_output}"
retain_status_evidence "${restart_up_output}" "${restart_status_output}"
jq -cn \
  --slurpfile journey "${journey_output}" \
  --slurpfile report "${report_output}" '
    {
      journey: (
        $journey[0].journey
        | .aegisops_alert_id = .alert_id
      ),
      report: $report[0]
    }
  ' |
  run_reviewed_journey verify-restart \
    >"${restart_output}"
record_step 14 \
  "restart_and_verify_persistence" \
  "$(jq -er '.observed_at' "${restart_output}")"

assert_repository_snapshot
evaluated_at="$(observed_now)"
jq -n \
  --arg evaluated_at "${evaluated_at}" \
  --arg trial_run_id "${trial_run_id}" \
  --arg snapshot_id "${snapshot_id}" \
  --arg repository_revision "${repository_revision}" '
    {
      schema_version: "phase67.4-prerequisite-evaluation-v1",
      evaluated_at: $evaluated_at,
      trial_run_id: $trial_run_id,
      snapshot_id: $snapshot_id,
      repository_revision: $repository_revision,
      verdict: "integration_trial_passed_with_owned_limitations",
      ga_accepted: false,
      limitation_ids: [
        "phase67-single-host",
        "phase67-bounded-connectors",
        "phase67-ga-gates-open"
      ]
    }
  ' >"${evaluation_record_output}"
record_step 15 "record_prerequisite_evaluation" "${evaluated_at}"

run_reviewed_lab_command "${LAB_DIR}/cleanup.sh"
cleaned=true
assert_repository_snapshot
assert_compose_snapshot
python3 "${builder}" \
  --schema "${schema}" \
  --snapshot "${snapshot_output}" \
  --compose-config "${compose_render_output}" \
  --compose-digest-record "${compose_digest_output}" \
  --expected-repository-revision "${repository_revision}" \
  --expected-compose-sha256 "${compose_render_sha256}" \
  --images "${images_output}" \
  --preparation "${preparation_output}" \
  --wazuh "${wazuh_manifest_output}" \
  --wazuh-output "${wazuh_output}" \
  --journey "${journey_output}" \
  --restart "${restart_output}" \
  --report "${report_output}" \
  --evaluation "${evaluation}" \
  --evaluation-record "${evaluation_record_output}" \
  --observations "${observations_output}" \
  --startup-status "${startup_status_output}" \
  --initial-status "${initial_status_output}" \
  --restart-status "${restart_status_output}" \
  --workflow-snapshot "${workflow_snapshot_output}" \
  --workflow-pre-dispatch "${workflow_predispatch_output}" \
  --reviewed-workflow "${reviewed_workflow}" \
  --artifacts-directory-name "${trial_run_id}-artifacts" \
  --output "${evidence_output}"
rm -f "${compose_render_output}"
assert_repository_snapshot
python3 "${validator}" "${schema}" "${evidence_output}"
assert_repository_snapshot

for destination in "${final_evidence}" "${final_report}" "${final_artifacts}"; do
  [[ ! -e "${destination}" && ! -L "${destination}" ]] \
    || fail "publication destination already exists: ${destination}"
done
chmod 700 "${staging_dir}"
find "${staging_dir}" -type f -exec chmod 600 {} +
mv "${report_output}" "${final_report}"
publication_report_published=true
mv "${staging_dir}" "${final_artifacts}"
publication_artifacts_published=true
mv "${final_artifacts}/evidence.json" "${final_evidence}"
publication_manifest_moved=true
assert_repository_snapshot
python3 "${validator}" \
  --published \
  "${schema}" \
  "${final_evidence}" \
  "${final_report}" \
  "${final_artifacts}"
chmod 400 "${final_evidence}"
publication_manifest_published=true
trap - EXIT

echo "PASS: Phase 67.4 real-service E2E trial completed"
echo "evidence=${final_evidence}"
echo "report=${final_report}"
echo "artifacts=${final_artifacts}"
