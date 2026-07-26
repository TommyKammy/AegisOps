#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
lab_dir="${repo_root}/control-plane/deployment/phase-67-integration-lab"
relative_lab="control-plane/deployment/phase-67-integration-lab"

fail() {
  echo "$*" >&2
  exit 1
}

require_file() {
  [[ -f "$1" ]] || fail "Missing Phase 67.1 artifact: ${1#${repo_root}/}"
}

require_executable() {
  [[ -x "$1" ]] || fail "Phase 67.1 command must be executable: ${1#${repo_root}/}"
}

require_fixed_string() {
  local path="$1"
  local expected="$2"
  grep -F -- "${expected}" "${path}" >/dev/null \
    || fail "Missing required line in ${path#${repo_root}/}: ${expected}"
}

require_adjacent_lines() {
  local path="$1"
  local first="$2"
  local second="$3"
  local line
  local previous=""

  while IFS= read -r line || [[ -n "${line}" ]]; do
    if [[ "${previous}" == "${first}" && "${line}" == "${second}" ]]; then
      return 0
    fi
    previous="${line}"
  done <"${path}"
  fail "Missing required adjacent lines in ${path#${repo_root}/}: ${first} -> ${second}"
}

require_absent_string() {
  local path="$1"
  local forbidden="$2"
  local message="$3"
  if grep -F -- "${forbidden}" "${path}" >/dev/null; then
    fail "${message}"
  fi
}

files=(
  bootstrap.env.sample
  docker-compose.yml
  config/nginx.conf
  config/control-plane.conf
  control-plane-entrypoint.sh
  lab-common.sh
  preflight.sh
  init.sh
  prepare-substrates.sh
  up.sh
  status.sh
  logs.sh
  down.sh
  cleanup.sh
  destroy-data.sh
  smoke-core.sh
  control-plane-entrypoint.sh
  README.md
  RUNBOOK.md
)
for file in "${files[@]}"; do
  require_file "${lab_dir}/${file}"
done

commands=(
  preflight.sh
  init.sh
  prepare-substrates.sh
  up.sh
  status.sh
  logs.sh
  down.sh
  cleanup.sh
  destroy-data.sh
  smoke-core.sh
)
for command in "${commands[@]}"; do
  require_executable "${lab_dir}/${command}"
done

compose="${lab_dir}/docker-compose.yml"
bootstrap="${lab_dir}/bootstrap.env.sample"
common="${lab_dir}/lab-common.sh"
init="${lab_dir}/init.sh"
preflight="${lab_dir}/preflight.sh"
prepare="${lab_dir}/prepare-substrates.sh"
down="${lab_dir}/down.sh"
cleanup="${lab_dir}/cleanup.sh"
destroy="${lab_dir}/destroy-data.sh"
readme="${lab_dir}/README.md"
runbook="${lab_dir}/RUNBOOK.md"
proxy_config="${lab_dir}/config/control-plane.conf"
dockerignore="${repo_root}/.dockerignore"
control_plane_dockerfile="${repo_root}/control-plane/deployment/first-boot/Dockerfile"
require_file "${control_plane_dockerfile}"

required_compose_lines=(
  'name: ${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:-aegisops-phase67-lab}'
  'image: ${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:-aegisops-phase67-lab}-control-plane:local'
  'profiles:'
  'platform: ${AEGISOPS_LAB_WAZUH_PLATFORM:-linux/arm64}'
  'platform: ${AEGISOPS_LAB_SHUFFLE_PLATFORM:-linux/amd64}'
  '"127.0.0.1:${AEGISOPS_LAB_PROXY_PORT:-18443}:8443"'
  'condition: service_healthy'
  'condition: service_completed_successfully'
  'com.aegisops.lab.component: wazuh-security-bootstrap'
  'DASHBOARD_PASSWORD: ${AEGISOPS_LAB_WAZUH_DASHBOARD_PASSWORD:?run-init-first}'
  '- wazuh.indexer'
  '- wazuh.manager'
  "grep -q 'wazuh-analysisd is running'"
  'com.aegisops.lab.execution-enabled: "false"'
  'file: ${AEGISOPS_LAB_SECRET_DIR:?run-init-first}/postgres-password'
  'file: ${AEGISOPS_LAB_SECRET_DIR:?run-init-first}/control-plane-postgres-dsn'
  'subnet: ${AEGISOPS_LAB_NETWORK_SUBNET:-172.31.67.0/24}'
  'com.aegisops.lab.phase: "67.1"'
  'wazuh/wazuh-manager:4.14.6@sha256:'
  'wazuh/wazuh-indexer:4.14.6@sha256:'
  'wazuh/wazuh-dashboard:4.14.6@sha256:'
  'ghcr.io/shuffle/shuffle-backend:2.2.1@sha256:'
  'ghcr.io/shuffle/shuffle-frontend:2.2.1@sha256:'
  'postgres:16.4@sha256:'
  'nginx:1.27.0@sha256:'
  'opensearchproject/opensearch:3.2.0@sha256:'
)
for line in "${required_compose_lines[@]}"; do
  require_fixed_string "${compose}" "${line}"
done

required_bootstrap_lines=(
  'AEGISOPS_LAB_COLIMA_PROFILE=mac-studio-solo'
  'AEGISOPS_LAB_DOCKER_CONTEXT=colima-mac-studio-solo'
  'AEGISOPS_LAB_COMPOSE_PROJECT_NAME=aegisops-phase67-lab'
  'AEGISOPS_LAB_RUNTIME_ROOT=${HOME}/.local/share/aegisops/phase-67-integration-lab'
  'AEGISOPS_LAB_WAZUH_PLATFORM=linux/arm64'
  'AEGISOPS_LAB_SHUFFLE_PLATFORM=linux/amd64'
  'AEGISOPS_LAB_ALLOW_EMULATION=no'
  'AEGISOPS_LAB_WAZUH_DOCKER_COMMIT=499184cbeb44fc1086791d11ad4b9bdcb77a9bb9'
)
for line in "${required_bootstrap_lines[@]}"; do
  require_fixed_string "${bootstrap}" "${line}"
done

require_fixed_string "${common}" 'docker --context "${AEGISOPS_LAB_DOCKER_CONTEXT}" "$@"'
require_fixed_string "${common}" 'load_bootstrap_environment'
require_fixed_string "${common}" 'RUNTIME_ENV="${AEGISOPS_LAB_RUNTIME_ROOT}/runtime.env"'
require_fixed_string "${common}" 'runtime environment root differs from the reviewed bootstrap root'
require_fixed_string "${common}" 'selected_port_names'
require_fixed_string "${common}" 'service_name_for_published_port'
require_fixed_string "${common}" 'selected_address_names'
require_fixed_string "${common}" 'assert_unique_selected_ports'
require_fixed_string "${common}" 'require_runtime_configuration'
require_fixed_string "${common}" 'assert_reviewed_lab_pins'
require_fixed_string "${common}" 'assert_reviewed_wazuh_checkout'
require_fixed_string "${common}" 'record_reviewed_file_digest'
require_fixed_string "${common}" 'assert_reviewed_file_digest'
require_fixed_string "${common}" 'pathlib.Path(sys.argv[1]).resolve(strict=False)'
require_fixed_string "${common}" 'assert_phase67_compose_project_ownership'
require_fixed_string "${common}" 'excluded_services_for_scope'
require_fixed_string "${common}" 'assert_no_running_excluded_services'
require_fixed_string "${common}" 'assert_no_preserved_phase67_volumes'
require_fixed_string "${common}" 'repository_runtime_state='
require_fixed_string "${common}" 'repository_runtime_artifact_sha256='
require_fixed_string "${common}" 'aegisops-phase67-runtime-artifacts-v1'
require_fixed_string "${common}" 'validate_wazuh_certificate_bundle'
require_fixed_string "${common}" 'openssl x509 -checkend 604800'
require_fixed_string "${common}" 'openssl verify -CAfile'
require_fixed_string "${init}" "printf 'Aa1!%sZz9!"
require_fixed_string "${init}" 'load_bootstrap_environment'
require_fixed_string "${init}" 'openssl x509 -checkend 604800'
require_fixed_string "${init}" 'DNS:wazuh.localhost,DNS:shuffle.localhost'
require_fixed_string "${init}" 'certificate_text="$(openssl x509'
require_fixed_string "${init}" '"DNS:wazuh.localhost"'
require_fixed_string "${init}" '"DNS:shuffle.localhost"'
require_fixed_string "${init}" '"IP Address:127.0.0.1"'
require_fixed_string "${init}" 'wazuh-dashboard-password'
require_fixed_string "${init}" 'AEGISOPS_LAB_WAZUH_DASHBOARD_PASSWORD'
require_fixed_string "${init}" 'write_runtime_env_assignment AEGISOPS_LAB_RUNTIME_ROOT'
require_fixed_string "${init}" 'proxy-certificate-recreate-required'
require_fixed_string "${init}" 'wazuh-upstream-root-ca.pem'
require_fixed_string "${init}" 'desired_proxy_wazuh_trust'
require_fixed_string "${init}" 'initialized runtime is missing credential'
require_fixed_string "${init}" '"${runtime_previously_initialized}" == "true"'
require_fixed_string "${init}" 'assert_no_preserved_phase67_volumes'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'AEGISOPS_CONTROL_PLANE_POSTGRES_DSN="$(cat "${dsn_file}")"'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'unset AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" '/opt/aegisops/bin/first-boot-entrypoint.sh /bin/true'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" '"${migrations_dir}"/0015_*.sql'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'detected migration checksum drift'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'migration_readiness_query'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'prove_migration_state'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'could not prove reviewed schema state for recorded migration'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" "'false_positive_review_id', 'detector_lifecycle_id'"
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" "'lifecycle_transition_records_lifecycle_state_known_values'"
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" "('evidence_records', 'provenance', 'jsonb', 'NO', \$default\$'{}'::jsonb\$default\$)"
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'SELECT table_name, column_name, udt_name, is_nullable, column_default'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'AND column_default IS NULL'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'pg_get_constraintdef(constraint_record.oid, true)'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'AND constraint_record.convalidated'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" "pg_get_indexdef(indexrelid, 1, true) = 'idempotency_key'"
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'CREATE INDEX reconciliation_records_correlation_alert_latest_idx ON aegisops_control.reconciliation_records USING btree (correlation_key, compared_at DESC, reconciliation_id DESC) WHERE (alert_id IS NOT NULL)'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'CREATE INDEX ai_trace_records_latest_idx ON aegisops_control.ai_trace_records USING btree (generated_at DESC, ai_trace_id DESC)'
require_fixed_string "${lab_dir}/control-plane-entrypoint.sh" 'exec "$@"'
require_fixed_string "${preflight}" 'colima status --profile "${AEGISOPS_LAB_COLIMA_PROFILE}" --json'
require_fixed_string "${preflight}" 'Shuffle 2.2.1 is amd64-only'
require_fixed_string "${preflight}" 'test -e /mnt/lima-rosetta/rosetta'
require_fixed_string "${preflight}" 'Shuffle amd64 execution is unavailable in Colima profile'
require_fixed_string "${preflight}" '--activate=false'
require_fixed_string "${preflight}" 'host port ${port}'
require_fixed_string "${preflight}" 'com.docker.compose.service=${expected_service}'
require_fixed_string "${preflight}" 'selected_port_names "${scope}"'
require_fixed_string "${preflight}" 'selected_address_names "${scope}"'
require_fixed_string "${preflight}" 'assert_unique_selected_ports "${scope}"'
require_fixed_string "${preflight}" 'requested.network_address'
require_fixed_string "${preflight}" 'requested.broadcast_address'
require_fixed_string "${preflight}" 'project_network_subnets'
require_fixed_string "${preflight}" 'ARM64 service execution is unavailable'
require_fixed_string "${preflight}" 'record "PASS published_ports=${published_ports}"'
require_fixed_string "${preflight}" 'mktemp "${evidence_dir}/preflight-${scope}-'
require_fixed_string "${prepare}" 'type=volume,source=${cert_volume},target=/certificates'
require_fixed_string "${prepare}" 'validate_wazuh_certificate_bundle'
require_fixed_string "${prepare}" 'wazuh-certificate-recreate-required'
require_adjacent_lines \
  "${prepare}" \
  '  mark_wazuh_recreation_required' \
  '  docker_lab cp "${cert_container}:/certificates/." "${cert_dir}"'
require_adjacent_lines \
  "${prepare}" \
  'mark_wazuh_recreation_required' \
  'python3 - \'
require_fixed_string "${prepare}" 'OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk'
require_fixed_string "${compose}" 'OPENSEARCH_JAVA_HOME: /usr/share/wazuh-indexer/jdk'
require_fixed_string "${common}" 'diff --quiet HEAD --'
require_fixed_string "${prepare}" 'replace_user_hash(document: str, username: str, replacement: str)'
require_fixed_string "${prepare}" '"kibanaserver", dashboard_hash'
require_fixed_string "${prepare}" '("kibanaro", "logstash", "readall", "snapshotrestore")'
require_fixed_string "${prepare}" 'disabled_demo_hash'
require_fixed_string "${prepare}" 'record_reviewed_file_digest'
require_fixed_string "${prepare}" 'wazuh/wazuh-certs-generator:0.0.4@sha256:'
require_fixed_string "${prepare}" 'proxy_wazuh_trust="${AEGISOPS_LAB_PROXY_CERT_DIR}/wazuh-upstream-root-ca.pem"'
require_fixed_string "${proxy_config}" 'server_name wazuh.localhost;'
require_fixed_string "${proxy_config}" 'server_name shuffle.localhost;'
require_fixed_string "${proxy_config}" 'proxy_pass $phase67_wazuh_dashboard;'
require_fixed_string "${proxy_config}" 'proxy_pass $phase67_shuffle_frontend;'
require_fixed_string "${proxy_config}" 'resolver 127.0.0.11 ipv6=off valid=10s;'
require_fixed_string "${proxy_config}" 'proxy_ssl_trusted_certificate /etc/nginx/certs/wazuh-upstream-root-ca.pem;'
require_fixed_string "${proxy_config}" 'proxy_ssl_verify on;'
require_absent_string \
  "${proxy_config}" \
  'proxy_ssl_verify off;' \
  "Wazuh dashboard upstream TLS verification must remain enabled."
require_fixed_string "${lab_dir}/up.sh" 'assert_reviewed_wazuh_checkout'
require_fixed_string "${lab_dir}/up.sh" 'assert_reviewed_file_digest'
require_fixed_string "${lab_dir}/up.sh" 'assert_no_running_excluded_services "${scope}"'
require_fixed_string "${lab_dir}/up.sh" 'proxy Wazuh trust certificate is stale'
require_fixed_string "${lab_dir}/up.sh" 'proxy-certificate-recreate-required'
require_fixed_string "${lab_dir}/up.sh" 'wazuh-certificate-recreate-required'
require_fixed_string "${lab_dir}/up.sh" 'force_recreate=false'
require_fixed_string "${lab_dir}/up.sh" '--force-recreate'
require_fixed_string "${lab_dir}/status.sh" 'scope="full"'
require_fixed_string "${lab_dir}/status.sh" 'while [[ "$#" -gt 0 ]]; do'
require_fixed_string "${lab_dir}/logs.sh" 'for log_argument in "$@"; do'
require_fixed_string "${lab_dir}/logs.sh" 'pass only service names for a bounded snapshot'
require_fixed_string "${down}" 'require_runtime_configuration'
require_fixed_string "${down}" 'assert_phase67_compose_project_ownership'
require_fixed_string "${down}" 'down --remove-orphans'
require_fixed_string "${cleanup}" 'Use destroy-data.sh only when permanent deletion of lab volumes is intended.'
require_fixed_string "${destroy}" '--confirm-destroy-phase-67-lab-data'
require_fixed_string "${destroy}" 'assert_phase67_compose_project_ownership'
require_fixed_string "${destroy}" 'down --volumes --remove-orphans'
require_fixed_string "${readme}" 'Phase 67.1 does not mount the Docker socket or start Orborus'
require_fixed_string "${readme}" 'export AEGISOPS_LAB_BOOTSTRAP_ENV='
require_fixed_string "${readme}" 'next `up.sh` force service recreation'
require_fixed_string "${readme}" 'AEGISOPS_LAB_ALLOW_EMULATION=no'
require_fixed_string "${readme}" 'canonical runtime root must remain below'
require_fixed_string "${runbook}" 'Preflight is read-only with respect to Colima and Docker.'
require_fixed_string "${runbook}" 'validates cached certificate expiry, chains, and key pairs'
require_fixed_string "${runbook}" 'initialized runtime credential missing'
require_fixed_string "${runbook}" 'repository runtime state and artifact SHA-256'
require_fixed_string "${runbook}" 'recheck the checkout, digest, certificate bundle, and proxy trust copy immediately before startup'
require_fixed_string "${runbook}" 'Phase 67.1 resource-label proof'
require_fixed_string "${repo_root}/README.md" '[Phase 67.1 Colima integration lab]'
require_fixed_string "${repo_root}/control-plane/README.md" '`deployment/phase-67-integration-lab/`'
require_fixed_string "${dockerignore}" '!control-plane/**'
require_fixed_string "${dockerignore}" '!postgres/control-plane/migrations/**'
require_fixed_string "${dockerignore}" 'control-plane/deployment/first-boot/secrets/'
require_fixed_string "${dockerignore}" 'control-plane/deployment/first-boot/certs/'
require_fixed_string "${dockerignore}" 'control-plane/deployment/phase-67-integration-lab/secrets/'
require_fixed_string "${dockerignore}" 'control-plane/deployment/phase-67-integration-lab/certs/'
require_fixed_string "${dockerignore}" 'control-plane/deployment/phase-67-integration-lab/substrates/'
require_fixed_string "${repo_root}/.github/workflows/ci.yml" 'bash scripts/verify-phase-67-1-colima-integration-lab.sh'
require_fixed_string "${repo_root}/.github/workflows/ci.yml" 'bash scripts/test-verify-phase-67-1-colima-integration-lab.sh'

if grep -R --include='*.sh' -F -- 'docker context use' "${lab_dir}" >/dev/null; then
  fail "Phase 67.1 lab must not mutate the global Docker context."
fi
if grep -E -- '/var/run/docker\.sock|docker\.sock:/' "${compose}" >/dev/null ||
  grep -R --include='*.sh' -E -- '/var/run/docker\.sock|docker\.sock:/' "${lab_dir}" >/dev/null; then
  fail "Phase 67.1 lab must not mount the Docker socket."
fi
if grep -E -- '(^|[[:space:]])container_name:' "${compose}" >/dev/null; then
  fail "Phase 67.1 lab must preserve Compose project isolation without container_name."
fi
if grep -E -- 'image:.*:latest([@[:space:]]|$)' "${compose}" >/dev/null; then
  fail "Phase 67.1 lab images must not use latest tags."
fi
while IFS= read -r image_reference; do
  if [[ "${image_reference}" == *'-control-plane:local' ]]; then
    continue
  fi
  [[ "${image_reference}" =~ @sha256:[0-9a-f]{64}$ ]] \
    || fail "Phase 67.1 must pin every external Compose image by digest: ${image_reference}"
done < <(sed -n -E 's/^[[:space:]]*image:[[:space:]]*//p' "${compose}")
head -n 1 "${control_plane_dockerfile}" |
  grep -E '^FROM python:3\.12-slim-bookworm@sha256:[0-9a-f]{64}$' >/dev/null \
  || fail "Phase 67.1 control-plane base image must be pinned by digest."
grep -E 'cert_image="wazuh/wazuh-certs-generator:0\.0\.4@sha256:[0-9a-f]{64}"' \
  "${prepare}" >/dev/null \
  || fail "Phase 67.1 Wazuh certificate generator must be pinned by digest."
if grep -F -- '--volumes' "${down}" "${cleanup}" >/dev/null; then
  fail "Ordinary Phase 67.1 stop and cleanup commands must preserve named volumes."
fi
if grep -E -- '^[[:space:]]*-[[:space:]]*"\$\{AEGISOPS_LAB_.*_PORT' "${compose}" >/dev/null; then
  fail "Phase 67.1 published ports must remain bound to 127.0.0.1."
fi
require_absent_string \
  "${compose}" \
  'AEGISOPS_LAB_WAZUH_DASHBOARD_PORT' \
  "Wazuh dashboard must not be published outside the approved proxy."
require_absent_string \
  "${compose}" \
  'AEGISOPS_LAB_SHUFFLE_FRONTEND_PORT' \
  "Shuffle frontend must not be published outside the approved proxy."

echo "Phase 67.1 Colima integration lab contract verified."
