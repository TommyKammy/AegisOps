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
require_command ln
require_runtime_environment
[[ "${AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE:-}" == "real_http" ]] \
  || fail "real Shuffle transport is not enabled; run ${LAB_DIR}/bootstrap-shuffle.sh"

# shellcheck source=shuffle/reviewed-app-image.env
source "${LAB_DIR}/shuffle/reviewed-app-image.env"
shuffle_tools_image="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}:${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_TAG}"
shuffle_tools_immutable_ref="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}@${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST}"
shuffle_action_service="shuffle-tools_1-2-0"
shuffle_action_preflight_absent=false
shuffle_action_owned=false
shuffle_action_service_id=""
shuffle_action_service_image=""
shuffle_action_service_port=""
shuffle_action_network_id=""
shuffle_action_cleanup_candidate_id=""
shuffle_action_cleanup_candidate_spec=""
shuffle_worker_service="shuffle-workers"
shuffle_worker_network="shuffle_swarm_executions"
shuffle_worker_immutable_ref=""
shuffle_worker_preflight_absent=false
shuffle_worker_owned=false
shuffle_worker_service_id=""
shuffle_worker_cleanup_candidate_id=""
shuffle_worker_cleanup_candidate_spec=""
captured_shuffle_worker_image_json=""
shuffle_backend_url="$(
  printf 'http://%s-shuffle-backend-1:5001' \
    "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:-aegisops-phase67-lab}"
)"
schema="${LAB_DIR}/e2e/evidence-manifest.schema.json"
validator="${LAB_DIR}/e2e/validate_evidence_manifest.py"
builder="${LAB_DIR}/e2e/build_evidence.py"
swarm_service_labeler="${LAB_DIR}/e2e/update_swarm_service_labels.py"
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

shuffle_action_runtime_matches_reviewed_image() {
  local service_id="$1"
  local service_metadata="$2"
  local replicas
  local task_ids
  local task_metadata
  local task_container_ids
  local container_metadata
  local pinned_image_id

  replicas="$(
    jq -er '
      .[0].Spec.Mode.Replicated.Replicas
      | select(type == "number" and . >= 1 and floor == .)
    ' <<<"${service_metadata}"
  )" || return 1
  task_ids="$(
    docker_lab service ps \
      --filter desired-state=running \
      --quiet \
      "${service_id}" 2>/dev/null
  )" || return 1
  [[ "$(wc -w <<<"${task_ids}")" -eq "${replicas}" ]] || return 1
  # shellcheck disable=SC2086
  task_metadata="$(docker_lab inspect ${task_ids} 2>/dev/null)" || return 1
  jq -e \
    --arg service_id "${service_id}" \
    --argjson replicas "${replicas}" '
      length == $replicas
      and all(.[];
        .ServiceID == $service_id
        and .DesiredState == "running"
        and .Status.State == "running"
        and (
          (.Status.ContainerStatus.ContainerID // "")
          | type == "string" and length > 0
        )
      )
    ' <<<"${task_metadata}" >/dev/null || return 1
  task_container_ids="$(
    jq -er '.[].Status.ContainerStatus.ContainerID' <<<"${task_metadata}"
  )" || return 1
  # shellcheck disable=SC2086
  container_metadata="$(
    docker_lab inspect ${task_container_ids} 2>/dev/null
  )" || return 1
  pinned_image_id="$(
    docker_lab image inspect \
      "${shuffle_tools_immutable_ref}" \
      --format '{{.Id}}' 2>/dev/null
  )" || return 1
  jq -e \
    --arg image_id "${pinned_image_id}" \
    --argjson replicas "${replicas}" '
      length == $replicas and all(.[]; .Image == $image_id)
    ' <<<"${container_metadata}" >/dev/null
}

derive_reviewed_shuffle_action_network_id() {
  local worker_metadata
  local network_ids
  local network_id
  local network_metadata

  [[ -n "${shuffle_worker_service_id}" ]] || return 1
  worker_metadata="$(
    docker_lab service inspect "${shuffle_worker_service_id}" 2>/dev/null
  )" || return 1
  network_ids="$(
    jq -er '
      [.[0].Spec.Networks[]?.Target
        | select(type == "string" and length > 0)]
      | unique
      | if length > 0 then .[]
        else error("worker service has no execution-network candidates")
        end
    ' <<<"${worker_metadata}"
  )" || return 1
  # shellcheck disable=SC2086
  network_metadata="$(docker_lab network inspect ${network_ids} 2>/dev/null)" \
    || return 1
  network_id="$(
    jq -er '
      [
        .[]
        | select(
            .Name == "shuffle_swarm_executions"
            and .Scope == "swarm"
            and .Driver == "overlay"
            and .Ingress == false
            and (.Id | type == "string" and length > 0)
          )
        | .Id
      ]
      | unique
      | if length == 1 then .[0]
        else error("expected one reviewed worker execution network")
        end
    ' <<<"${network_metadata}"
  )" || return 1
  printf '%s\n' "${network_id}"
}

shuffle_action_unowned_service_matches_contract() {
  local service_metadata="$1"
  local network_id="$2"

  jq -e \
    --arg service_name "${shuffle_action_service}" \
    --arg callback_url "${shuffle_backend_url}" \
    --arg network_id "${network_id}" '
      length == 1
      and (.[0].ID | type == "string" and length > 0)
      and .[0].Spec.Name == $service_name
      and ((.[0].Spec.Labels // {}) | type == "object")
      and ((.[0].Spec.Labels // {})
        | has("com.aegisops.lab.phase") | not)
      and ((.[0].Spec.Labels // {})
        | has("com.aegisops.lab.component") | not)
      and ((.[0].Spec.Labels // {})
        | has("com.aegisops.lab.trial-run-id") | not)
      and (
        .[0].Spec.TaskTemplate.ContainerSpec.Image
        | type == "string" and length > 0 and (test("\\s") | not)
      )
      and (
        [.[0].Spec.TaskTemplate.ContainerSpec.Env[]?
          | select(startswith("CALLBACK_URL="))] as $callbacks
        | ($callbacks | length) == 1
          and $callbacks[0] == ("CALLBACK_URL=" + $callback_url)
      )
      and (
        [.[0].Spec.Networks[]?.Target] | unique
      ) == [$network_id]
      and ((.[0].Spec.EndpointSpec.Ports // []) as $ports
        | ($ports | length) == 1
        and $ports[0].Name == "app-port"
        and $ports[0].Protocol == "tcp"
        and $ports[0].PublishMode == "ingress"
        and ($ports[0].PublishedPort
          | type == "number" and . > 0 and floor == .)
        and ($ports[0].TargetPort
          | type == "number" and . > 0 and floor == .))
    ' <<<"${service_metadata}" >/dev/null
}

shuffle_action_service_observation_is_stable() {
  local before_metadata="$1"
  local after_metadata="$2"

  jq -e -s '
    .[0][0] as $before
    | .[1][0] as $after
    | $before.ID == $after.ID
      and $before.Version.Index == $after.Version.Index
      and (($before.Spec | del(.Labels)) == ($after.Spec | del(.Labels)))
  ' \
    <(printf '%s\n' "${before_metadata}") \
    <(printf '%s\n' "${after_metadata}") \
    >/dev/null
}

shuffle_action_service_matches_attempted_claim() {
  local before_metadata="$1"
  local after_metadata="$2"

  jq -e -s \
    --arg service_id "${shuffle_action_service_id}" \
    --arg trial_run_id "${trial_run_id}" '
      .[0][0] as $before
      | .[1][0] as $after
      | $before.ID == $service_id
        and $after.ID == $service_id
        and $after.Version.Index > $before.Version.Index
        and (
          ($after.Spec.Labels // {})
          == (
            ($before.Spec.Labels // {})
            + {
                "com.aegisops.lab.phase": "67.4",
                "com.aegisops.lab.component": "shuffle-action-image",
                "com.aegisops.lab.trial-run-id": $trial_run_id
              }
          )
        )
        and (($after.Spec | del(.Labels)) == ($before.Spec | del(.Labels)))
    ' \
    <(printf '%s\n' "${before_metadata}") \
    <(printf '%s\n' "${after_metadata}") \
    >/dev/null
}

assert_reviewed_shuffle_action_service() {
  local service_metadata
  local named_metadata

  [[ "${shuffle_action_owned}" == true ]] \
    && [[ -n "${shuffle_action_service_id}" ]] \
    && [[ -n "${shuffle_action_service_image}" ]] \
    && [[ -n "${shuffle_action_service_port}" ]] \
    && [[ -n "${shuffle_action_network_id}" ]] \
    || fail "Shuffle action service is not owned by the current trial"
  service_metadata="$(
    docker_lab service inspect "${shuffle_action_service_id}" 2>/dev/null
  )" || fail "owned Shuffle action service disappeared"
  named_metadata="$(
    docker_lab service inspect "${shuffle_action_service}" 2>/dev/null
  )" || fail "Shuffle action service name no longer resolves to the owned service"
  jq -e \
    --arg service_id "${shuffle_action_service_id}" \
    --arg service_name "${shuffle_action_service}" \
    --arg service_image "${shuffle_action_service_image}" \
    --arg trial_run_id "${trial_run_id}" \
    --arg callback_url "${shuffle_backend_url}" \
    --arg network_id "${shuffle_action_network_id}" \
    --argjson port "${shuffle_action_service_port}" '
      length == 1
      and .[0].ID == $service_id
      and .[0].Spec.Name == $service_name
      and .[0].Spec.TaskTemplate.ContainerSpec.Image == $service_image
      and .[0].Spec.Labels["com.aegisops.lab.phase"] == "67.4"
      and .[0].Spec.Labels["com.aegisops.lab.component"]
        == "shuffle-action-image"
      and .[0].Spec.Labels["com.aegisops.lab.trial-run-id"] == $trial_run_id
      and (
        [.[0].Spec.TaskTemplate.ContainerSpec.Env[]?
          | select(startswith("CALLBACK_URL="))] as $callbacks
        | ($callbacks | length) == 1
          and $callbacks[0] == ("CALLBACK_URL=" + $callback_url)
      )
      and ([.[0].Spec.Networks[]?.Target] | unique) == [$network_id]
      and ((.[0].Spec.EndpointSpec.Ports // []) as $ports
        | ($ports | length) == 1
        and $ports[0].Name == "app-port"
        and $ports[0].Protocol == "tcp"
        and $ports[0].PublishMode == "ingress"
        and $ports[0].PublishedPort == $port
        and ($ports[0].TargetPort
          | type == "number" and . > 0 and floor == .))
    ' <<<"${service_metadata}" >/dev/null \
    || fail "Shuffle action service does not match the reviewed lab contract"
  jq -e \
    --arg service_id "${shuffle_action_service_id}" '
      length == 1 and .[0].ID == $service_id
    ' <<<"${named_metadata}" >/dev/null \
    || fail "Shuffle action service name now resolves to a replacement service"
  shuffle_action_runtime_matches_reviewed_image \
    "${shuffle_action_service_id}" "${service_metadata}" \
    || fail "Shuffle action tasks did not retain the reviewed image ID"
}

assert_shuffle_action_service_absent() {
  local service_names

  service_names="$(docker_lab service ls --format '{{.Name}}')" \
    || fail "cannot inspect existing Shuffle action services"
  if grep -Fx -- "${shuffle_action_service}" \
    <<<"${service_names}" >/dev/null; then
    fail "refusing to start while a pre-existing Shuffle action service exists"
  fi
  shuffle_action_preflight_absent=true
}

ensure_reviewed_shuffle_action_service() {
  local attempt
  local candidate_id=""
  local current_metadata=""
  local previous_metadata=""
  local owned_metadata
  local service_version
  local stable=false

  assert_repository_snapshot
  [[ "${shuffle_action_preflight_absent}" == true ]] \
    || fail "Shuffle action service absence was not established before startup"
  for attempt in {1..120}; do
    if shuffle_action_network_id="$(
      derive_reviewed_shuffle_action_network_id
    )"; then
      break
    fi
    sleep 1
  done
  [[ -n "${shuffle_action_network_id}" ]] \
    || fail "Shuffle worker execution network did not stabilize"
  for attempt in {1..120}; do
    if ! current_metadata="$(
      docker_lab service inspect "${shuffle_action_service}" 2>/dev/null
    )"; then
      if [[ -n "${candidate_id}" ]]; then
        fail "Shuffle action service disappeared before ownership was claimed"
      fi
      sleep 1
      continue
    fi
    if ! shuffle_action_unowned_service_matches_contract \
      "${current_metadata}" "${shuffle_action_network_id}"; then
      fail "new Shuffle action service does not match the Orborus contract"
    fi
    shuffle_action_service_id="$(jq -er '.[0].ID' <<<"${current_metadata}")"
    if [[ -z "${candidate_id}" ]]; then
      candidate_id="${shuffle_action_service_id}"
    elif [[ "${shuffle_action_service_id}" != "${candidate_id}" ]]; then
      fail "Shuffle action service was replaced before ownership was claimed"
    fi
    if ! shuffle_action_runtime_matches_reviewed_image \
      "${shuffle_action_service_id}" "${current_metadata}"; then
      sleep 1
      continue
    fi
    if [[ -n "${previous_metadata}" ]] \
      && shuffle_action_service_observation_is_stable \
        "${previous_metadata}" "${current_metadata}"; then
      stable=true
      break
    fi
    previous_metadata="${current_metadata}"
    sleep 1
  done
  [[ "${stable}" == true ]] \
    || fail "Shuffle action service did not reach a stable unowned state"
  shuffle_action_service_image="$(
    jq -er '.[0].Spec.TaskTemplate.ContainerSpec.Image' \
      <<<"${current_metadata}"
  )"
  shuffle_action_service_port="$(
    jq -er '
      [.[0].Spec.EndpointSpec.Ports[]? | select(.Name == "app-port")]
      | if length == 1 then .[0].PublishedPort
        else error("expected one app-port")
        end
    ' <<<"${current_metadata}"
  )"
  service_version="$(jq -er '.[0].Version.Index' <<<"${current_metadata}")"
  if ! python3 "${swarm_service_labeler}" \
    --docker-context "${AEGISOPS_LAB_DOCKER_CONTEXT}" \
    --service-id "${shuffle_action_service_id}" \
    --expected-version "${service_version}" \
    --expected-name "${shuffle_action_service}" \
    --expected-image "${shuffle_action_service_image}" \
    --allow-observed-image-reference-after-runtime-id-verification \
    --label "com.aegisops.lab.phase=67.4" \
    --label "com.aegisops.lab.component=shuffle-action-image" \
    --label "com.aegisops.lab.trial-run-id=${trial_run_id}" \
    >/dev/null; then
    if owned_metadata="$(
      docker_lab service inspect "${shuffle_action_service_id}" 2>/dev/null
    )" && shuffle_action_service_matches_attempted_claim \
      "${current_metadata}" "${owned_metadata}" \
      && shuffle_action_runtime_matches_reviewed_image \
        "${shuffle_action_service_id}" "${owned_metadata}"; then
      shuffle_action_owned=true
      assert_reviewed_shuffle_action_service
      return
    fi
    fail "failed to claim the Orborus-created Shuffle action service"
  fi
  shuffle_action_owned=true
  assert_reviewed_shuffle_action_service
}

wait_for_exact_swarm_service_removal() {
  local service_id="$1"
  local attempt
  local task_container_ids

  for attempt in {1..60}; do
    if docker_lab service inspect "${service_id}" >/dev/null 2>&1; then
      sleep 1
      continue
    fi
    if ! task_container_ids="$(
      docker_lab ps \
        --all \
        --quiet \
        --filter "label=com.docker.swarm.service.id=${service_id}"
    )"; then
      sleep 1
      continue
    fi
    [[ -z "${task_container_ids}" ]] && return
    sleep 1
  done
  echo "BLOCKED: Swarm service ${service_id} tasks did not stop during cleanup" >&2
  return 1
}

capture_reviewed_shuffle_action_cleanup_candidate() {
  local candidate_id
  local current_spec
  local network_id="${shuffle_action_network_id}"
  local service_image
  local service_metadata

  [[ "${shuffle_action_preflight_absent}" == true ]] || return
  if [[ -n "${shuffle_action_service_id}" ]]; then
    candidate_id="${shuffle_action_service_id}"
    service_metadata="$(
      docker_lab service inspect "${candidate_id}" 2>/dev/null
    )" || return
  else
    service_metadata="$(
      docker_lab service inspect "${shuffle_action_service}" 2>/dev/null
    )" || return
    candidate_id="$(jq -er '.[0].ID' <<<"${service_metadata}")" || return 1
  fi
  [[ "${candidate_id}" =~ ^[a-z0-9]{12,64}$ ]] || return 1
  jq -e \
    --arg service_id "${candidate_id}" \
    --arg service_name "${shuffle_action_service}" '
      length == 1
      and .[0].ID == $service_id
      and .[0].Spec.Name == $service_name
    ' <<<"${service_metadata}" >/dev/null || return 1
  if [[ -z "${network_id}" ]]; then
    network_id="$(derive_reviewed_shuffle_action_network_id)" || return 1
  fi
  if [[ "${shuffle_action_owned}" == true ]]; then
    jq -e \
      --arg service_id "${candidate_id}" \
      --arg service_image "${shuffle_action_service_image}" \
      --arg trial_run_id "${trial_run_id}" '
        .[0].ID == $service_id
        and .[0].Spec.TaskTemplate.ContainerSpec.Image == $service_image
        and .[0].Spec.Labels["com.aegisops.lab.phase"] == "67.4"
        and .[0].Spec.Labels["com.aegisops.lab.component"]
          == "shuffle-action-image"
        and .[0].Spec.Labels["com.aegisops.lab.trial-run-id"]
          == $trial_run_id
      ' <<<"${service_metadata}" >/dev/null || return 1
    shuffle_action_runtime_matches_reviewed_image \
      "${candidate_id}" "${service_metadata}" || return 1
  else
    shuffle_action_unowned_service_matches_contract \
      "${service_metadata}" "${network_id}" || return 1
    service_image="$(
      jq -er '.[0].Spec.TaskTemplate.ContainerSpec.Image' \
        <<<"${service_metadata}"
    )" || return 1
    [[ "${service_image}" == "${shuffle_tools_image}" ]] || return 1
  fi
  current_spec="$(jq -cS '.[0].Spec' <<<"${service_metadata}")" || return 1
  shuffle_action_service_id="${candidate_id}"
  shuffle_action_network_id="${network_id}"
  shuffle_action_cleanup_candidate_id="${candidate_id}"
  shuffle_action_cleanup_candidate_spec="${current_spec}"
}

remove_reviewed_shuffle_action_service() {
  local current_spec
  local named_metadata
  local service_metadata

  [[ -n "${shuffle_action_cleanup_candidate_id}" ]] || return
  service_metadata="$(
    docker_lab service inspect \
      "${shuffle_action_cleanup_candidate_id}" 2>/dev/null
  )" || {
    if ! wait_for_exact_swarm_service_removal \
      "${shuffle_action_cleanup_candidate_id}"; then
      return 1
    fi
    if named_metadata="$(
      docker_lab service inspect "${shuffle_action_service}" 2>/dev/null
    )"; then
      echo "BLOCKED: a replacement Shuffle action service appeared during cleanup" >&2
      return 1
    fi
    shuffle_action_cleanup_candidate_id=""
    shuffle_action_cleanup_candidate_spec=""
    return
  }
  current_spec="$(jq -cS '.[0].Spec' <<<"${service_metadata}")" || return 1
  [[ "${current_spec}" == "${shuffle_action_cleanup_candidate_spec}" ]] \
    || {
      echo "BLOCKED: refusing to remove a changed Shuffle action service" >&2
      return 1
    }
  jq -e \
    --arg service_id "${shuffle_action_cleanup_candidate_id}" \
    --arg service_name "${shuffle_action_service}" '
      length == 1
      and .[0].ID == $service_id
      and .[0].Spec.Name == $service_name
    ' <<<"${service_metadata}" >/dev/null || {
      echo "BLOCKED: refusing to remove a replaced Shuffle action service" >&2
      return 1
    }
  docker_lab service rm "${shuffle_action_cleanup_candidate_id}" >/dev/null
  wait_for_exact_swarm_service_removal \
    "${shuffle_action_cleanup_candidate_id}"
  if named_metadata="$(
    docker_lab service inspect "${shuffle_action_service}" 2>/dev/null
  )"; then
    echo "BLOCKED: a replacement Shuffle action service appeared during cleanup" >&2
    return 1
  fi
  shuffle_action_owned=false
  shuffle_action_service_id=""
  shuffle_action_service_image=""
  shuffle_action_service_port=""
  shuffle_action_network_id=""
  shuffle_action_cleanup_candidate_id=""
  shuffle_action_cleanup_candidate_spec=""
}

configured_shuffle_worker_immutable_ref() {
  local orborus_container_ids
  local orborus_metadata

  if [[ -n "${shuffle_worker_immutable_ref}" ]]; then
    printf '%s\n' "${shuffle_worker_immutable_ref}"
    return
  fi
  orborus_container_ids="$(
    compose_scope full ps --quiet shuffle-orborus 2>/dev/null || true
  )"
  [[ "$(wc -w <<<"${orborus_container_ids}")" -eq 1 ]] || return 1
  # shellcheck disable=SC2086
  orborus_metadata="$(docker_lab inspect ${orborus_container_ids})"
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
    | if length == 1
        and (.[0] | test("^[^[:space:]@]+@sha256:[0-9a-f]{64}$"))
      then .[0]
      else error("expected one digest-pinned Shuffle worker image")
      end
  ' <<<"${orborus_metadata}"
}

assert_shuffle_worker_service_absent() {
  local service_names

  service_names="$(docker_lab service ls --format '{{.Name}}')" \
    || fail "cannot inspect existing Shuffle worker services"
  if grep -Fx -- "${shuffle_worker_service}" \
    <<<"${service_names}" >/dev/null; then
    fail "refusing to start while a pre-existing Shuffle worker service exists"
  fi
  shuffle_worker_preflight_absent=true
}

shuffle_worker_service_is_trial_owned() {
  local service_metadata="$1"

  [[ -n "${shuffle_worker_service_id}" ]] \
    && jq -e \
      --arg service_id "${shuffle_worker_service_id}" \
      --arg service_name "${shuffle_worker_service}" \
      --arg service_image "${shuffle_worker_immutable_ref}" \
      --arg trial_run_id "${trial_run_id}" '
        .[0].ID == $service_id
        and .[0].Spec.Name == $service_name
        and .[0].Spec.TaskTemplate.ContainerSpec.Image == $service_image
        and .[0].Spec.Labels["com.aegisops.lab.phase"] == "67.4"
        and .[0].Spec.Labels["com.aegisops.lab.component"]
          == "shuffle-worker-image"
        and .[0].Spec.Labels["com.aegisops.lab.trial-run-id"]
          == $trial_run_id
      ' <<<"${service_metadata}" >/dev/null
}

shuffle_worker_service_matches_attempted_claim() {
  local before_metadata="$1"
  local after_metadata="$2"

  jq -e -s \
    --arg service_id "${shuffle_worker_service_id}" \
    --arg service_name "${shuffle_worker_service}" \
    --arg service_image "${shuffle_worker_immutable_ref}" \
    --arg trial_run_id "${trial_run_id}" '
      .[0][0] as $before
      | .[1][0] as $after
      | $before.ID == $service_id
        and $after.ID == $service_id
        and $after.Version.Index > $before.Version.Index
        and $after.Spec.Name == $service_name
        and $after.Spec.TaskTemplate.ContainerSpec.Image == $service_image
        and (
          ($after.Spec.Labels // {})
          == (
            ($before.Spec.Labels // {})
            + {
                "com.aegisops.lab.phase": "67.4",
                "com.aegisops.lab.component": "shuffle-worker-image",
                "com.aegisops.lab.trial-run-id": $trial_run_id
              }
          )
        )
        and (
          ($after.Spec | del(.Labels))
          == ($before.Spec | del(.Labels))
        )
    ' \
    <(printf '%s\n' "${before_metadata}") \
    <(printf '%s\n' "${after_metadata}") \
    >/dev/null
}

resolve_reviewed_shuffle_worker_network_id() {
  local service_id="$1"
  local attempt
  local network_id
  local network_metadata
  local service_metadata

  for attempt in {1..120}; do
    if ! service_metadata="$(
      docker_lab service inspect "${service_id}" 2>/dev/null
    )"; then
      echo "BLOCKED: Shuffle worker service ID disappeared before network stabilization" >&2
      return 1
    fi
    if ! shuffle_worker_service_is_unowned_candidate \
      "${service_metadata}" "${service_id}"; then
      echo "BLOCKED: Shuffle worker service identity or ownership changed before network stabilization" >&2
      return 1
    fi
    if ! network_id="$(
      jq -er '
        (.[0].Spec.TaskTemplate.Networks // []) as $networks
        | if (($networks | type) != "array") then
            error("worker task networks are not an array")
          elif ($networks | length) == 0 then "pending"
          elif (
            ($networks | length) == 1
            and (($networks[0] | type) == "object")
            and (
              $networks[0].Target
              | type == "string" and test("^[a-z0-9]{12,64}$")
            )
          ) then $networks[0].Target
          else error("expected one worker task network target")
        end
      ' <<<"${service_metadata}" 2>/dev/null
    )"; then
      echo "BLOCKED: Shuffle worker task network specification is invalid" >&2
      return 1
    fi
    if [[ "${network_id}" == "pending" ]]; then
      sleep 1
      continue
    fi
    if ! network_metadata="$(
      docker_lab network inspect "${network_id}" 2>/dev/null
    )" || ! jq -e \
      --arg network_id "${network_id}" \
      --arg network_name "${shuffle_worker_network}" '
        length == 1
        and .[0].Id == $network_id
        and .[0].Name == $network_name
        and .[0].Scope == "swarm"
        and .[0].Driver == "overlay"
      ' <<<"${network_metadata}" >/dev/null; then
      echo "BLOCKED: Shuffle worker task network is not the expected Swarm overlay" >&2
      return 1
    fi
    printf '%s\n' "${network_id}"
    return
  done
  echo "BLOCKED: Shuffle worker overlay network was not created" >&2
  return 1
}

shuffle_worker_service_is_unowned_candidate() {
  local service_metadata="$1"
  local service_id="$2"

  jq -e \
    --arg service_id "${service_id}" \
    --arg service_name "${shuffle_worker_service}" \
    --arg service_image "${shuffle_worker_immutable_ref}" '
      length == 1
      and .[0].ID == $service_id
      and ($service_id | test("^[a-z0-9]{12,64}$"))
      and (
        .[0].Version.Index
        | type == "number" and . >= 1 and floor == .
      )
      and .[0].Spec.Name == $service_name
      and .[0].Spec.TaskTemplate.ContainerSpec.Image == $service_image
      and (
        (.[0].Spec.Labels // {}) as $labels
        | ($labels | type == "object") and ($labels | length) == 0
      )
    ' <<<"${service_metadata}" >/dev/null
}

wait_for_stable_reviewed_shuffle_worker_service() {
  local service_id="$1"
  local expected_network_id="$2"
  local required_nonlabel_spec="${3:-}"
  local attempt
  local current_nonlabel_spec
  local current_version
  local network_metadata
  local network_state
  local previous_nonlabel_spec=""
  local previous_version=""
  local service_metadata

  for attempt in {1..120}; do
    if ! network_metadata="$(
      docker_lab network inspect "${expected_network_id}" 2>/dev/null
    )" || ! jq -e \
      --arg network_id "${expected_network_id}" \
      --arg network_name "${shuffle_worker_network}" '
        length == 1
        and .[0].Id == $network_id
        and .[0].Name == $network_name
        and .[0].Scope == "swarm"
        and .[0].Driver == "overlay"
      ' <<<"${network_metadata}" >/dev/null; then
      echo "BLOCKED: Shuffle worker overlay network identity changed before ownership" >&2
      return 1
    fi
    if ! service_metadata="$(
      docker_lab service inspect "${service_id}" 2>/dev/null
    )"; then
      echo "BLOCKED: Shuffle worker service ID disappeared before ownership" >&2
      return 1
    fi
    if ! shuffle_worker_service_is_unowned_candidate \
      "${service_metadata}" "${service_id}"; then
      echo "BLOCKED: Shuffle worker service identity or ownership changed before claim" >&2
      return 1
    fi
    if ! network_state="$(
      jq -er --arg network_id "${expected_network_id}" '
        (.[0].Spec.TaskTemplate.Networks // []) as $networks
        | if (($networks | type) != "array") then "invalid"
          elif ($networks | length) == 0 then "pending"
          elif (
            ($networks | length) == 1
            and (($networks[0] | type) == "object")
            and $networks[0].Target == $network_id
          ) then "ready"
          else "invalid"
          end
      ' <<<"${service_metadata}" 2>/dev/null
    )"; then
      echo "BLOCKED: cannot inspect Shuffle worker task networks" >&2
      return 1
    fi
    if [[ "${network_state}" == "pending" ]]; then
      previous_version=""
      previous_nonlabel_spec=""
      sleep 1
      continue
    fi
    if [[ "${network_state}" != "ready" ]]; then
      echo "BLOCKED: Shuffle worker task networks do not match the expected overlay" >&2
      return 1
    fi
    current_version="$(jq -er '.[0].Version.Index' <<<"${service_metadata}")"
    current_nonlabel_spec="$(
      jq -cS '.[0].Spec | del(.Labels)' <<<"${service_metadata}"
    )"
    if [[ -n "${required_nonlabel_spec}" ]] \
      && [[ "${current_nonlabel_spec}" != "${required_nonlabel_spec}" ]]; then
      echo "BLOCKED: Shuffle worker non-label specification changed before retry" >&2
      return 1
    fi
    if [[ "${current_version}" == "${previous_version}" ]] \
      && [[ "${current_nonlabel_spec}" == "${previous_nonlabel_spec}" ]]; then
      printf '%s\n' "${service_metadata}"
      return
    fi
    previous_version="${current_version}"
    previous_nonlabel_spec="${current_nonlabel_spec}"
    sleep 1
  done
  echo "BLOCKED: Shuffle worker service did not reach a stable network specification" >&2
  return 1
}

claim_reviewed_shuffle_worker_service() {
  local service_metadata="$1"
  local claim_attempt
  local claim_rc
  local expected_network_id
  local owned_nonlabel_spec
  local retry_version
  local service_id
  local service_image
  local service_version
  local stable_nonlabel_spec
  local owned_metadata

  if [[ "${shuffle_worker_owned}" == true ]]; then
    if ! shuffle_worker_service_is_trial_owned "${service_metadata}"; then
      echo "BLOCKED: Shuffle worker service ownership changed during the trial" >&2
      return 1
    fi
    return 0
  fi
  if [[ "${shuffle_worker_preflight_absent}" != true ]]; then
    echo "BLOCKED: Shuffle worker service absence was not established before startup" >&2
    return 1
  fi
  if ! jq -e '
    (.[0].Spec.Labels["com.aegisops.lab.phase"] // "") == ""
    and (.[0].Spec.Labels["com.aegisops.lab.component"] // "") == ""
    and (.[0].Spec.Labels["com.aegisops.lab.trial-run-id"] // "") == ""
  ' <<<"${service_metadata}" >/dev/null; then
    echo "BLOCKED: new Shuffle worker service already carries ownership labels" >&2
    return 1
  fi
  if ! service_id="$(jq -er '.[0].ID' <<<"${service_metadata}")"; then
    echo "BLOCKED: new Shuffle worker service has no stable service ID" >&2
    return 1
  fi
  if [[ -n "${shuffle_worker_service_id}" ]] \
    && [[ "${shuffle_worker_service_id}" != "${service_id}" ]]; then
    echo "BLOCKED: Shuffle worker service ID was replaced before ownership" >&2
    return 1
  fi
  shuffle_worker_service_id="${service_id}"
  if ! service_image="$(
    jq -er '.[0].Spec.TaskTemplate.ContainerSpec.Image' \
      <<<"${service_metadata}"
  )"; then
    echo "BLOCKED: new Shuffle worker service has no image identity" >&2
    return 1
  fi
  if [[ "${service_image}" != "${shuffle_worker_immutable_ref}" ]]; then
    echo "BLOCKED: Shuffle worker service is not pinned to the reviewed digest" >&2
    return 1
  fi
  if ! service_version="$(
    jq -er '
      .[0].Version.Index
      | select(type == "number" and . >= 1 and floor == .)
    ' <<<"${service_metadata}"
  )"; then
    echo "BLOCKED: new Shuffle worker service has no stable service version" >&2
    return 1
  fi
  if ! expected_network_id="$(
    resolve_reviewed_shuffle_worker_network_id "${service_id}"
  )"; then
    return 1
  fi
  if ! service_metadata="$(
    wait_for_stable_reviewed_shuffle_worker_service \
      "${service_id}" "${expected_network_id}"
  )"; then
    return 1
  fi
  stable_nonlabel_spec="$(
    jq -cS '.[0].Spec | del(.Labels)' <<<"${service_metadata}"
  )"

  for claim_attempt in 1 2; do
    service_version="$(jq -er '.[0].Version.Index' <<<"${service_metadata}")"
    if python3 "${swarm_service_labeler}" \
      --docker-context "${AEGISOPS_LAB_DOCKER_CONTEXT}" \
      --service-id "${service_id}" \
      --expected-version "${service_version}" \
      --expected-name "${shuffle_worker_service}" \
      --expected-image "${shuffle_worker_immutable_ref}" \
      --label "com.aegisops.lab.phase=67.4" \
      --label "com.aegisops.lab.component=shuffle-worker-image" \
      --label "com.aegisops.lab.trial-run-id=${trial_run_id}" \
      >/dev/null 2>&1; then
      claim_rc=0
      break
    else
      claim_rc=$?
    fi
    if owned_metadata="$(
      docker_lab service inspect "${shuffle_worker_service_id}" 2>/dev/null
    )" && shuffle_worker_service_matches_attempted_claim \
      "${service_metadata}" "${owned_metadata}"; then
      shuffle_worker_owned=true
      echo "BLOCKED: Shuffle worker ownership helper failed after applying labels" >&2
      return 1
    fi
    if [[ "${claim_attempt}" -ge 2 ]]; then
      echo "BLOCKED: failed to label the new Shuffle worker service (exit ${claim_rc})" >&2
      return 1
    fi
    if ! service_metadata="$(
      wait_for_stable_reviewed_shuffle_worker_service \
        "${service_id}" \
        "${expected_network_id}" \
        "${stable_nonlabel_spec}"
    )"; then
      echo "BLOCKED: refusing to retry an unstable Shuffle worker ownership claim" >&2
      return 1
    fi
    retry_version="$(jq -er '.[0].Version.Index' <<<"${service_metadata}")"
    if [[ "${retry_version}" -le "${service_version}" ]]; then
      echo "BLOCKED: refusing to retry a Shuffle worker claim without a newer stable version" >&2
      return 1
    fi
  done
  shuffle_worker_owned=true
  if ! owned_metadata="$(
    docker_lab service inspect "${shuffle_worker_service_id}"
  )"; then
    echo "BLOCKED: failed to inspect the claimed Shuffle worker service" >&2
    return 1
  fi
  if ! shuffle_worker_service_is_trial_owned "${owned_metadata}"; then
    echo "BLOCKED: Shuffle worker service did not retain trial ownership labels" >&2
    return 1
  fi
  owned_nonlabel_spec="$(
    jq -cS '.[0].Spec | del(.Labels)' <<<"${owned_metadata}"
  )"
  if [[ "${owned_nonlabel_spec}" != "${stable_nonlabel_spec}" ]]; then
    echo "BLOCKED: Shuffle worker service changed outside ownership labels" >&2
    return 1
  fi
}

capture_reviewed_shuffle_worker_cleanup_candidate() {
  local candidate_id
  local current_spec
  local service_metadata

  [[ "${shuffle_worker_preflight_absent}" == true ]] || return
  if [[ -z "${shuffle_worker_immutable_ref}" ]]; then
    shuffle_worker_immutable_ref="$(
      configured_shuffle_worker_immutable_ref
    )" || return 1
  fi
  if [[ -n "${shuffle_worker_service_id}" ]]; then
    candidate_id="${shuffle_worker_service_id}"
    service_metadata="$(
      docker_lab service inspect "${candidate_id}" 2>/dev/null
    )" || return
  else
    service_metadata="$(
      docker_lab service inspect "${shuffle_worker_service}" 2>/dev/null
    )" || return
    candidate_id="$(jq -er '.[0].ID' <<<"${service_metadata}")" || return 1
  fi
  [[ "${candidate_id}" =~ ^[a-z0-9]{12,64}$ ]] || return 1
  if [[ "${shuffle_worker_owned}" == true ]]; then
    shuffle_worker_service_is_trial_owned "${service_metadata}" || return 1
  else
    shuffle_worker_service_is_unowned_candidate \
      "${service_metadata}" "${candidate_id}" || return 1
  fi
  current_spec="$(jq -cS '.[0].Spec' <<<"${service_metadata}")" || return 1
  shuffle_worker_service_id="${candidate_id}"
  shuffle_worker_cleanup_candidate_id="${candidate_id}"
  shuffle_worker_cleanup_candidate_spec="${current_spec}"
}

capture_reviewed_shuffle_cleanup_candidates() {
  local rc=0

  capture_reviewed_shuffle_worker_cleanup_candidate || rc=1
  capture_reviewed_shuffle_action_cleanup_candidate || rc=1
  return "${rc}"
}

remove_reviewed_shuffle_worker_service() {
  local current_spec
  local named_metadata
  local service_metadata

  [[ -n "${shuffle_worker_cleanup_candidate_id}" ]] || return
  service_metadata="$(
    docker_lab service inspect \
      "${shuffle_worker_cleanup_candidate_id}" 2>/dev/null
  )" || {
    if ! wait_for_exact_swarm_service_removal \
      "${shuffle_worker_cleanup_candidate_id}"; then
      return 1
    fi
    if named_metadata="$(
      docker_lab service inspect "${shuffle_worker_service}" 2>/dev/null
    )"; then
      echo "BLOCKED: a replacement Shuffle worker service appeared during cleanup" >&2
      return 1
    fi
    shuffle_worker_cleanup_candidate_id=""
    shuffle_worker_cleanup_candidate_spec=""
    return
  }
  current_spec="$(jq -cS '.[0].Spec' <<<"${service_metadata}")" || return 1
  [[ "${current_spec}" == "${shuffle_worker_cleanup_candidate_spec}" ]] \
    || {
      echo "BLOCKED: refusing to remove a changed Shuffle worker service" >&2
      return 1
    }
  if [[ "${shuffle_worker_owned}" == true ]]; then
    shuffle_worker_service_is_trial_owned "${service_metadata}" || {
      echo "BLOCKED: refusing to remove a worker without trial ownership" >&2
      return 1
    }
  else
    shuffle_worker_service_is_unowned_candidate \
      "${service_metadata}" "${shuffle_worker_cleanup_candidate_id}" || {
        echo "BLOCKED: refusing to remove an unverified worker candidate" >&2
        return 1
      }
  fi
  docker_lab service rm "${shuffle_worker_cleanup_candidate_id}" >/dev/null
  wait_for_exact_swarm_service_removal \
    "${shuffle_worker_cleanup_candidate_id}"
  if named_metadata="$(
    docker_lab service inspect "${shuffle_worker_service}" 2>/dev/null
  )"; then
    echo "BLOCKED: a replacement Shuffle worker service appeared during cleanup" >&2
    return 1
  fi
  shuffle_worker_owned=false
  shuffle_worker_service_id=""
  shuffle_worker_cleanup_candidate_id=""
  shuffle_worker_cleanup_candidate_spec=""
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
publication_manifest_candidate="${AEGISOPS_LAB_EVIDENCE_DIR}/.${trial_run_id}.manifest-candidate"
cleaned=false
publication_report_published=false
publication_artifacts_published=false
publication_manifest_staged=false
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

  assert_repository_snapshot
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

capture_reviewed_shuffle_worker_image() {
  local execution_id="${1:-}"
  local attempt
  local service_metadata
  local service_image
  local task_ids
  local task_metadata
  local task_container_id
  local container_metadata
  local reviewed_image_id
  local execution_observed=false

  assert_repository_snapshot
  for attempt in {1..120}; do
    if service_metadata="$(
      docker_lab service inspect "${shuffle_worker_service}" 2>/dev/null
    )"; then
      claim_reviewed_shuffle_worker_service "${service_metadata}" \
        || fail "cannot claim the reviewed Shuffle worker service"
      break
    fi
    sleep 1
  done
  [[ -n "${service_metadata:-}" ]] \
    || fail "Shuffle worker service was not created"
  service_image="$(
    jq -er '.[0].Spec.TaskTemplate.ContainerSpec.Image' \
      <<<"${service_metadata}"
  )"
  [[ "${service_image}" == "${shuffle_worker_immutable_ref}" ]] \
    || fail "Shuffle worker service is not pinned to the reviewed digest"
  service_metadata="$(
    docker_lab service inspect "${shuffle_worker_service_id}"
  )"
  shuffle_worker_service_is_trial_owned "${service_metadata}" \
    || fail "Shuffle worker service is not owned by the current trial"
  task_ids=""
  task_metadata=""
  task_container_id=""
  for attempt in {1..120}; do
    if ! task_ids="$(
      docker_lab service ps \
        --filter desired-state=running \
        --quiet \
        "${shuffle_worker_service_id}" 2>/dev/null
    )"; then
      sleep 1
      continue
    fi
    if [[ "$(wc -w <<<"${task_ids}")" -ne 1 ]]; then
      sleep 1
      continue
    fi
    if ! task_metadata="$(docker_lab inspect "${task_ids}" 2>/dev/null)"; then
      sleep 1
      continue
    fi
    if task_container_id="$(
      jq -er \
        --arg task_id "${task_ids}" \
        --arg service_id "${shuffle_worker_service_id}" '
          if (
            length == 1
            and .[0].ID == $task_id
            and .[0].ServiceID == $service_id
            and .[0].DesiredState == "running"
            and .[0].Status.State == "running"
            and (
              (.[0].Status.ContainerStatus.ContainerID // "")
              | type == "string" and length > 0
            )
          ) then .[0].Status.ContainerStatus.ContainerID
          else error("Shuffle worker task is not ready")
          end
        ' <<<"${task_metadata}" 2>/dev/null
    )"; then
      break
    fi
    sleep 1
  done
  [[ -n "${task_container_id}" ]] \
    || fail "Shuffle worker service did not reach exactly one running task with a container ID"
  container_metadata="$(docker_lab inspect "${task_container_id}")"
  reviewed_image_id="$(
    docker_lab image inspect \
      "${shuffle_worker_immutable_ref}" \
      --format '{{.Id}}'
  )"
  jq -e --arg image_id "${reviewed_image_id}" '
    length == 1
    and all(.[]; .Image == $image_id and .State.Running == true)
  ' <<<"${container_metadata}" >/dev/null \
    || fail "Shuffle worker container is not running the reviewed image ID"

  if [[ -n "${execution_id}" ]]; then
    for attempt in {1..30}; do
      if docker_lab logs \
        --tail 10000 \
        "${task_container_id}" 2>&1 \
        | grep -F -- "${execution_id}" >/dev/null; then
        execution_observed=true
        break
      fi
      sleep 1
    done
    [[ "${execution_observed}" == true ]] \
      || fail "Shuffle worker container logs do not contain the reviewed execution ID"
  fi

  captured_shuffle_worker_image_json="$(jq -cn \
    --arg immutable_reference "${service_image}" \
    --arg runtime_image_id "${reviewed_image_id}" '
      {
        service: "shuffle-worker-image",
        immutable_reference: $immutable_reference,
        runtime_image_id: $runtime_image_id
      }
    ')"
  printf '%s\n' "${captured_shuffle_worker_image_json}"
}

cleanup_on_exit() {
  local rc=$?
  local cleanup_failed=false
  rm -f "${compose_render_output}" >/dev/null 2>&1 || true
  if [[ "${cleaned}" != true ]]; then
    capture_reviewed_shuffle_cleanup_candidates >/dev/null 2>&1 \
      || cleanup_failed=true
    "${LAB_DIR}/cleanup.sh" >/dev/null 2>&1 || cleanup_failed=true
    remove_reviewed_shuffle_action_service >/dev/null 2>&1 \
      || cleanup_failed=true
    remove_reviewed_shuffle_worker_service >/dev/null 2>&1 \
      || cleanup_failed=true
  fi
  if [[ "${cleanup_failed}" == true && "${rc}" -eq 0 ]]; then
    rc=1
  fi
  if [[ "${rc}" -ne 0 ]]; then
    if [[ "${publication_manifest_published}" != true ]]; then
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
      if [[ "${publication_manifest_staged}" == true ]] \
        && [[ -f "${publication_manifest_candidate}" ]]; then
        if [[ -d "${staging_dir}" ]] && [[ ! -e "${evidence_output}" ]]; then
          mv "${publication_manifest_candidate}" \
            "${evidence_output}" >/dev/null 2>&1 \
            || rm -f "${publication_manifest_candidate}" \
              >/dev/null 2>&1 \
            || true
        else
          rm -f "${publication_manifest_candidate}" >/dev/null 2>&1 || true
        fi
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

run_reviewed_lab_command assert_shuffle_action_service_absent
run_reviewed_lab_command assert_shuffle_worker_service_absent
run_reviewed_lab_command "${LAB_DIR}/pin-shuffle-app-image.sh"
startup_output="$(run_reviewed_lab_startup "${LAB_DIR}/up.sh" full)"
printf '%s\n' "${startup_output}"
shuffle_worker_immutable_ref="$(
  run_reviewed_lab_command configured_shuffle_worker_immutable_ref
)"
[[ "${shuffle_worker_immutable_ref}" =~ ^[^[:space:]@]+@sha256:[0-9a-f]{64}$ ]] \
  || fail "Shuffle worker image is not digest-pinned"
capture_reviewed_shuffle_worker_image >/dev/null
shuffle_worker_image="${captured_shuffle_worker_image_json}"
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
shuffle_action_image="$(capture_reviewed_shuffle_action_image)"
jq \
  --argjson action_image "${shuffle_action_image}" \
  --argjson worker_image "${shuffle_worker_image}" '
    . + [
      $action_image,
      $worker_image
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
shuffle_execution_id="$(jq -er '.journey.execution_id' "${journey_output}")"
capture_reviewed_shuffle_worker_image "${shuffle_execution_id}" >/dev/null
postdispatch_shuffle_worker_image="${captured_shuffle_worker_image_json}"
[[ "${postdispatch_shuffle_worker_image}" == "${shuffle_worker_image}" ]] \
  || fail "Shuffle worker service changed during reviewed execution"
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

run_reviewed_lab_command capture_reviewed_shuffle_cleanup_candidates
run_reviewed_lab_command "${LAB_DIR}/down.sh"
run_reviewed_lab_command remove_reviewed_shuffle_action_service
run_reviewed_lab_command remove_reviewed_shuffle_worker_service
run_reviewed_lab_command assert_shuffle_action_service_absent
run_reviewed_lab_command assert_shuffle_worker_service_absent
restart_up_output="$(run_reviewed_lab_startup "${LAB_DIR}/up.sh" full)"
printf '%s\n' "${restart_up_output}"
retain_status_evidence "${restart_up_output}" "${restart_status_output}"
capture_reviewed_shuffle_worker_image >/dev/null
restart_shuffle_worker_image="${captured_shuffle_worker_image_json}"
[[ "${restart_shuffle_worker_image}" == "${shuffle_worker_image}" ]] \
  || fail "Shuffle worker service changed during restart verification"
run_reviewed_lab_command ensure_reviewed_shuffle_action_service
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

run_reviewed_lab_command capture_reviewed_shuffle_cleanup_candidates
run_reviewed_lab_command "${LAB_DIR}/cleanup.sh"
run_reviewed_lab_command remove_reviewed_shuffle_action_service
run_reviewed_lab_command remove_reviewed_shuffle_worker_service
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

for destination in \
  "${final_evidence}" \
  "${final_report}" \
  "${final_artifacts}" \
  "${publication_manifest_candidate}"; do
  [[ ! -e "${destination}" && ! -L "${destination}" ]] \
    || fail "publication destination already exists: ${destination}"
done
chmod 700 "${staging_dir}"
find "${staging_dir}" -type f -exec chmod 600 {} +
mv "${evidence_output}" "${publication_manifest_candidate}"
publication_manifest_staged=true
mv "${report_output}" "${final_report}"
publication_report_published=true
mv "${staging_dir}" "${final_artifacts}"
publication_artifacts_published=true
assert_repository_snapshot
python3 "${validator}" \
  --published \
  "${schema}" \
  "${publication_manifest_candidate}" \
  "${final_report}" \
  "${final_artifacts}"
chmod 400 "${publication_manifest_candidate}"
assert_repository_snapshot
[[ ! -e "${final_evidence}" && ! -L "${final_evidence}" ]] \
  || fail "publication destination appeared during validation: ${final_evidence}"
ln "${publication_manifest_candidate}" "${final_evidence}"
publication_manifest_published=true
rm -f "${publication_manifest_candidate}" >/dev/null 2>&1 || true
publication_manifest_staged=false
trap - EXIT

echo "PASS: Phase 67.4 real-service E2E trial completed"
echo "evidence=${final_evidence}"
echo "report=${final_report}"
echo "artifacts=${final_artifacts}"
