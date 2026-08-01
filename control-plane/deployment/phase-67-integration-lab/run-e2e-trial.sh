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
require_runtime_environment
[[ "${AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE:-}" == "real_http" ]] \
  || fail "real Shuffle transport is not enabled; run ${LAB_DIR}/bootstrap-shuffle.sh"

# shellcheck source=shuffle/reviewed-app-image.env
source "${LAB_DIR}/shuffle/reviewed-app-image.env"
shuffle_tools_image="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}:${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_TAG}"
shuffle_tools_immutable_ref="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_REPOSITORY}@${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST}"
schema="${LAB_DIR}/e2e/evidence-manifest.schema.json"
validator="${LAB_DIR}/e2e/validate_evidence_manifest.py"
builder="${LAB_DIR}/e2e/build_evidence.py"
evaluation="${REPO_ROOT}/docs/phase-67-prerequisite-evaluation.md"

[[ -f "${evaluation}" ]] \
  || fail "Phase 67 prerequisite evaluation is missing: ${evaluation}"
[[ -z "$(git -C "${REPO_ROOT}" status --porcelain=v1)" ]] \
  || fail "real E2E evidence requires a clean immutable repository revision"

repository_revision="$(git -C "${REPO_ROOT}" rev-parse HEAD)"
captured_prefix="$(date -u '+%Y%m%dT%H%M%SZ')"
trial_run_id="phase67-e2e-${captured_prefix}-$(openssl rand -hex 6)"
staging_dir="$(mktemp -d "${AEGISOPS_LAB_EVIDENCE_DIR}/.phase67-e2e.XXXXXX")"
wazuh_output="${staging_dir}/wazuh-output.txt"
journey_output="${staging_dir}/journey.json"
restart_output="${staging_dir}/restart.json"
report_output="${staging_dir}/report.json"
snapshot_output="${staging_dir}/snapshot.json"
images_output="${staging_dir}/images.json"
evidence_output="${staging_dir}/evidence.json"
cleaned=false

cleanup_on_exit() {
  local rc=$?
  if [[ "${cleaned}" != true ]]; then
    "${LAB_DIR}/cleanup.sh" >/dev/null 2>&1 || true
  fi
  if [[ "${rc}" -ne 0 ]]; then
    echo "BLOCKED: Phase 67.4 real-service E2E trial failed; reviewed captures remain in ${staging_dir}" >&2
  fi
  exit "${rc}"
}
trap cleanup_on_exit EXIT

compose_render_sha256="$(
  compose_scope full config |
    openssl dgst -sha256 -r |
    awk '{print $1}'
)"
schema_sha256="$(openssl dgst -sha256 -r "${schema}" | awk '{print $1}')"
snapshot_id="phase67-snapshot-$(
  printf '%s\0%s\0%s\0%s' \
    "${repository_revision}" \
    "${compose_render_sha256}" \
    "${schema_sha256}" \
    "${trial_run_id}" |
    openssl dgst -sha256 -r |
    awk '{print substr($1, 1, 16)}'
)"

"${LAB_DIR}/pin-shuffle-app-image.sh"
"${LAB_DIR}/up.sh" full

container_ids="$(compose_scope full ps -q)"
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

AEGISOPS_LAB_TRIAL_SCOPE=full \
  "${LAB_DIR}/test-wazuh-intake.sh" | tee "${wazuh_output}"
wazuh_evidence="$(
  sed -n 's/^evidence=//p' "${wazuh_output}" | tail -n 1
)"
[[ -f "${wazuh_evidence}" ]] \
  || fail "real Wazuh trial did not publish its evidence manifest"
aegisops_alert_id="$(jq -er '.aegisops_alert_id' "${wazuh_evidence}")"

compose_scope full exec -T \
  -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE="${shuffle_tools_image}" \
  -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST}" \
  -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_IMMUTABLE_REF="${shuffle_tools_immutable_ref}" \
  control-plane \
  python3 /opt/aegisops/phase67-e2e/run_real_journey.py \
    execute \
    --trial-id "${trial_run_id}" \
    --alert-id "${aegisops_alert_id}" \
    >"${journey_output}"
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

"${LAB_DIR}/down.sh"
"${LAB_DIR}/up.sh" full
jq -c '.journey' "${journey_output}" |
  compose_scope full exec -T \
    -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE="${shuffle_tools_image}" \
    -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST="${AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_DIGEST}" \
    -e AEGISOPS_LAB_SHUFFLE_TOOLS_IMAGE_IMMUTABLE_REF="${shuffle_tools_immutable_ref}" \
    control-plane \
    python3 /opt/aegisops/phase67-e2e/run_real_journey.py verify-restart \
    >"${restart_output}"

[[ "$(git -C "${REPO_ROOT}" rev-parse HEAD)" == "${repository_revision}" ]] \
  || fail "repository revision changed during the E2E trial"
runtime_artifact_sha256="$(jq -er '.runtime_artifact_digest' "${wazuh_evidence}")"
docker_context="${AEGISOPS_LAB_DOCKER_CONTEXT}"
colima_profile="${COLIMA_PROFILE:-default}"
jq -n \
  --arg trial_run_id "${trial_run_id}" \
  --arg snapshot_id "${snapshot_id}" \
  --arg repository_revision "${repository_revision}" \
  --arg compose_sha256 "${compose_render_sha256}" \
  --arg evidence_schema_sha256 "${schema_sha256}" \
  --arg runtime_artifact_sha256 "${runtime_artifact_sha256}" \
  --arg host_architecture "$(uname -m)" \
  --arg docker_context "${docker_context}" \
  --arg colima_profile "${colima_profile}" \
  --slurpfile images "${images_output}" '
    {
      trial_run_id: $trial_run_id,
      snapshot_id: $snapshot_id,
      repository_revision: $repository_revision,
      compose_sha256: $compose_sha256,
      evidence_schema_sha256: $evidence_schema_sha256,
      runtime_artifact_sha256: $runtime_artifact_sha256,
      host_architecture: $host_architecture,
      docker_context: $docker_context,
      colima_profile: $colima_profile,
      selected_profile: "full",
      images: $images[0]
    }
  ' >"${snapshot_output}"

"${LAB_DIR}/cleanup.sh"
cleaned=true
python3 "${builder}" \
  --schema "${schema}" \
  --snapshot "${snapshot_output}" \
  --wazuh "${wazuh_evidence}" \
  --wazuh-output "${wazuh_output}" \
  --journey "${journey_output}" \
  --restart "${restart_output}" \
  --report "${report_output}" \
  --evaluation "${evaluation}" \
  --output "${evidence_output}"
python3 "${validator}" "${schema}" "${evidence_output}"

final_evidence="${AEGISOPS_LAB_EVIDENCE_DIR}/${trial_run_id}.json"
final_report="${AEGISOPS_LAB_EVIDENCE_DIR}/${trial_run_id}-report.json"
mv "${evidence_output}" "${final_evidence}"
mv "${report_output}" "${final_report}"
chmod 600 "${final_evidence}" "${final_report}"
rm -rf "${staging_dir}"
trap - EXIT

echo "PASS: Phase 67.4 real-service E2E trial completed"
echo "evidence=${final_evidence}"
echo "report=${final_report}"
