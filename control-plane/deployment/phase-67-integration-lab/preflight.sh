#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

write_evidence=false
scope=core
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --write-evidence)
      write_evidence=true
      shift
      ;;
    --scope)
      [[ "$#" -ge 2 ]] || fail "usage: $0 [--scope core|wazuh|shuffle|full] [--write-evidence]"
      scope="$2"
      shift 2
      ;;
    *)
      fail "usage: $0 [--scope core|wazuh|shuffle|full] [--write-evidence]"
      ;;
  esac
done
case "${scope}" in
  core|wazuh|shuffle|full) ;;
  *) fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full" ;;
esac

load_lab_environment
require_command colima
require_command docker
require_command jq
require_command lsof
require_command python3

: "${AEGISOPS_LAB_COLIMA_PROFILE:?AEGISOPS_LAB_COLIMA_PROFILE is required}"
: "${AEGISOPS_LAB_DOCKER_CONTEXT:?AEGISOPS_LAB_DOCKER_CONTEXT is required}"
: "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME:?AEGISOPS_LAB_COMPOSE_PROJECT_NAME is required}"
: "${AEGISOPS_LAB_NETWORK_SUBNET:?AEGISOPS_LAB_NETWORK_SUBNET is required}"

report="$(mktemp)"
trap 'rm -f "${report}"' EXIT

record() {
  printf '%s\n' "$*" | tee -a "${report}"
}

check_minimum() {
  local label="$1"
  local actual="$2"
  local minimum="$3"

  (( actual >= minimum )) \
    || fail "${label} is ${actual}; Phase 67.1 requires at least ${minimum}"
}

port_is_listening() {
  lsof -nP -iTCP:"$1" -sTCP:LISTEN 2>/dev/null | tail -n +2 | grep -q .
}

status_json="$(colima status --profile "${AEGISOPS_LAB_COLIMA_PROFILE}" --json 2>/dev/null)" \
  || fail "Colima profile '${AEGISOPS_LAB_COLIMA_PROFILE}' is not running; start it explicitly with: colima start --profile ${AEGISOPS_LAB_COLIMA_PROFILE}"

runtime="$(jq -r '.runtime // empty' <<<"${status_json}")"
arch="$(jq -r '.arch // empty' <<<"${status_json}")"
cpus="$(jq -r '.cpu // 0' <<<"${status_json}")"
memory_bytes="$(jq -r '.memory // 0' <<<"${status_json}")"
disk_bytes="$(jq -r '.disk // 0' <<<"${status_json}")"
docker_socket="$(jq -r '.docker_socket // empty' <<<"${status_json}")"
memory_gib="$((memory_bytes / 1024 / 1024 / 1024))"
disk_gib="$((disk_bytes / 1024 / 1024 / 1024))"

[[ "${runtime}" == "docker" ]] || fail "Colima profile runtime is '${runtime}', expected docker"
check_minimum "Colima CPU allocation" "${cpus}" "${AEGISOPS_LAB_MIN_CPUS:-8}"
check_minimum "Colima memory allocation (GiB)" "${memory_gib}" "${AEGISOPS_LAB_MIN_MEMORY_GIB:-16}"
check_minimum "Colima disk allocation (GiB)" "${disk_gib}" "${AEGISOPS_LAB_MIN_DISK_GIB:-100}"

context_socket="$(docker context inspect "${AEGISOPS_LAB_DOCKER_CONTEXT}" --format '{{(index .Endpoints "docker").Host}}' 2>/dev/null)" \
  || fail "Docker context '${AEGISOPS_LAB_DOCKER_CONTEXT}' does not exist"
[[ "${context_socket}" == "${docker_socket}" ]] \
  || fail "Docker context '${AEGISOPS_LAB_DOCKER_CONTEXT}' points to '${context_socket}', not selected Colima socket '${docker_socket}'"

server_arch="$(docker_lab info --format '{{.Architecture}}' 2>/dev/null)" \
  || fail "Docker context '${AEGISOPS_LAB_DOCKER_CONTEXT}' cannot reach its engine"
docker_lab compose version >/dev/null 2>&1 \
  || fail "Docker Compose plugin is unavailable for context '${AEGISOPS_LAB_DOCKER_CONTEXT}'"

[[ "${server_arch}" == "${arch}" ]] \
  || fail "Docker server architecture '${server_arch}' differs from Colima architecture '${arch}'"
[[ "${AEGISOPS_LAB_WAZUH_PLATFORM:-}" == "linux/arm64" ]] \
  || fail "Wazuh platform must remain explicit linux/arm64 for this host"
if [[ "${scope}" == "shuffle" || "${scope}" == "full" ]]; then
  [[ "${AEGISOPS_LAB_SHUFFLE_PLATFORM:-}" == "linux/amd64" ]] \
    || fail "Shuffle 2.2.1 platform must remain explicit linux/amd64"
  [[ "${AEGISOPS_LAB_ALLOW_EMULATION:-no}" == "yes" ]] \
    || fail "Shuffle 2.2.1 is amd64-only; set AEGISOPS_LAB_ALLOW_EMULATION=yes only after accepting emulation"
  if ! colima ssh --profile "${AEGISOPS_LAB_COLIMA_PROFILE}" -- sh -c \
    'test -e /mnt/lima-rosetta/rosetta || test -e /proc/sys/fs/binfmt_misc/qemu-x86_64' \
    >/dev/null 2>&1; then
    fail "Shuffle amd64 execution is unavailable in Colima profile '${AEGISOPS_LAB_COLIMA_PROFILE}'. Preserve the profile settings, then run: colima stop --profile ${AEGISOPS_LAB_COLIMA_PROFILE} && colima start --profile ${AEGISOPS_LAB_COLIMA_PROFILE} --vm-type vz --vz-rosetta --arch aarch64 --cpus ${cpus} --memory ${memory_gib} --disk ${disk_gib} --runtime docker --kubernetes --activate=false"
  fi
fi

while IFS= read -r port_name; do
  variable="AEGISOPS_LAB_${port_name}_PORT"
  port="${!variable}"
  if port_is_listening "${port}"; then
    lab_binding="$(docker_lab ps --filter "label=com.docker.compose.project=${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}" --format '{{.Ports}}' | grep -F "127.0.0.1:${port}->" || true)"
    [[ -n "${lab_binding}" ]] || fail "host port ${port} (${port_name}) is already in use outside project '${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}'"
  fi
done < <(selected_port_names "${scope}")

network_name="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-network"
if docker_lab network inspect "${network_name}" >/dev/null 2>&1; then
  phase_label="$(docker_lab network inspect "${network_name}" --format '{{index .Labels "com.aegisops.lab.phase"}}')"
  project_label="$(docker_lab network inspect "${network_name}" --format '{{index .Labels "com.docker.compose.project"}}')"
  [[ "${phase_label}" == "67.1" ]] || fail "network '${network_name}' exists without the Phase 67.1 ownership label"
  [[ "${project_label}" == "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}" ]] \
    || fail "network '${network_name}' is not owned by Compose project '${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}'"
fi

volume_suffixes="
postgres-data
wazuh-api-configuration
wazuh-etc
wazuh-logs
wazuh-queue
wazuh-integrations
wazuh-indexer-data
wazuh-dashboard-config
wazuh-dashboard-custom
shuffle-database
"
for suffix in ${volume_suffixes}; do
  volume_name="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-${suffix}"
  if docker_lab volume inspect "${volume_name}" >/dev/null 2>&1; then
    phase_label="$(docker_lab volume inspect "${volume_name}" --format '{{index .Labels "com.aegisops.lab.phase"}}')"
    project_label="$(docker_lab volume inspect "${volume_name}" --format '{{index .Labels "com.docker.compose.project"}}')"
    [[ "${phase_label}" == "67.1" && "${project_label}" == "${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}" ]] \
      || fail "volume '${volume_name}' exists without Phase 67.1 Compose ownership"
  fi
done

network_subnets="$(
  docker_lab network ls --format '{{.Name}}' |
    while IFS= read -r network; do
      [[ "${network}" == "${network_name}" ]] && continue
      docker_lab network inspect "${network}" \
        --format '{{range .IPAM.Config}}{{println .Subnet}}{{end}}' 2>/dev/null |
        awk -v network="${network}" 'NF { print network "|" $0 }'
    done
)"

service_addresses="$(
  printf '%s\n' \
    "${AEGISOPS_LAB_PROXY_IPV4}" \
    "${AEGISOPS_LAB_CONTROL_PLANE_IPV4}" \
    "${AEGISOPS_LAB_POSTGRES_IPV4}" \
    "${AEGISOPS_LAB_WAZUH_MANAGER_IPV4}" \
    "${AEGISOPS_LAB_WAZUH_INDEXER_IPV4}" \
    "${AEGISOPS_LAB_WAZUH_DASHBOARD_IPV4}" \
    "${AEGISOPS_LAB_SHUFFLE_BACKEND_IPV4}" \
    "${AEGISOPS_LAB_SHUFFLE_OPENSEARCH_IPV4}" \
    "${AEGISOPS_LAB_SHUFFLE_FRONTEND_IPV4}"
)"

overlap="$(
  NETWORK_SUBNETS="${network_subnets}" SERVICE_ADDRESSES="${service_addresses}" \
    python3 - "${AEGISOPS_LAB_NETWORK_SUBNET}" <<'PY'
from __future__ import annotations

import ipaddress
import os
import sys

requested = ipaddress.ip_network(sys.argv[1], strict=True)
addresses = [
    ipaddress.ip_address(value)
    for value in os.environ["SERVICE_ADDRESSES"].splitlines()
    if value
]
if len(addresses) != len(set(addresses)):
    raise SystemExit("service IPv4 values must be unique")
outside = [str(address) for address in addresses if address not in requested]
if outside:
    raise SystemExit(
        f"service IPv4 values outside requested subnet {requested}: {','.join(outside)}"
    )

for line in os.environ.get("NETWORK_SUBNETS", "").splitlines():
    name, separator, subnet_text = line.partition("|")
    if not separator or not subnet_text:
        continue
    try:
        existing = ipaddress.ip_network(subnet_text, strict=False)
    except ValueError:
        continue
    if requested.version == existing.version and requested.overlaps(existing):
        print(f"{name}:{existing}")
PY
)" || fail "invalid network or service IPv4 configuration"
[[ -z "${overlap}" ]] || fail "requested subnet ${AEGISOPS_LAB_NETWORK_SUBNET} is already used by ${overlap}; choose a non-overlapping subnet and matching service IPv4 values"

record "PASS profile=${AEGISOPS_LAB_COLIMA_PROFILE}"
record "PASS scope=${scope}"
record "PASS docker_context=${AEGISOPS_LAB_DOCKER_CONTEXT}"
record "PASS architecture=${server_arch}"
record "PASS resources=cpu:${cpus},memory_gib:${memory_gib},disk_gib:${disk_gib}"
record "PASS compose_project=${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}"
record "PASS network_subnet=${AEGISOPS_LAB_NETWORK_SUBNET}"
record "PASS published_ports=127.0.0.1:${AEGISOPS_LAB_PROXY_PORT},127.0.0.1:${AEGISOPS_LAB_WAZUH_DASHBOARD_PORT},127.0.0.1:${AEGISOPS_LAB_SHUFFLE_FRONTEND_PORT}"
if [[ "${scope}" == "shuffle" || "${scope}" == "full" ]]; then
  record "PASS shuffle_emulation=available-and-explicitly-accepted"
else
  record "PASS shuffle_emulation=not-required-for-${scope}"
fi

if [[ "${write_evidence}" == true ]]; then
  assert_safe_runtime_root "${AEGISOPS_LAB_RUNTIME_ROOT}"
  evidence_dir="${AEGISOPS_LAB_EVIDENCE_DIR:-${AEGISOPS_LAB_RUNTIME_ROOT}/evidence}"
  mkdir -p "${evidence_dir}"
  evidence_file="${evidence_dir}/preflight-$(date -u '+%Y%m%dT%H%M%SZ').txt"
  write_evidence_header "${evidence_file}"
  cat "${report}" >>"${evidence_file}"
  chmod 600 "${evidence_file}"
  printf 'evidence=%s\n' "${evidence_file}"
fi
