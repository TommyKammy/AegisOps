#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

scope="full"
scope_selected=false
write_evidence=false
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    core|wazuh|shuffle|full)
      [[ "${scope_selected}" == false ]] \
        || fail "usage: $0 [core|wazuh|shuffle|full] [--write-evidence]"
      scope="$1"
      scope_selected=true
      ;;
    --write-evidence)
      [[ "${write_evidence}" == false ]] \
        || fail "usage: $0 [core|wazuh|shuffle|full] [--write-evidence]"
      write_evidence=true
      ;;
    *)
      fail "usage: $0 [core|wazuh|shuffle|full] [--write-evidence]"
      ;;
  esac
  shift
done
require_runtime_environment

case "${scope}" in
  core) ;;
  wazuh|shuffle|full) ;;
  *) fail "unknown lab scope '${scope}'; expected core, wazuh, shuffle, or full" ;;
esac

status_output="$(compose_scope "${scope}" ps --all)"
printf '%s\n' "${status_output}"

if [[ "${write_evidence}" == true ]]; then
  control_plane_container_id="$(
    compose_scope "${scope}" ps --all --quiet control-plane
  )"
  control_plane_container_image_id=unavailable
  if [[ -n "${control_plane_container_id}" ]]; then
    control_plane_container_image_id="$(
      docker_lab inspect \
        --format '{{.Image}}' \
        "${control_plane_container_id}"
    )"
    [[ "${control_plane_container_image_id}" =~ ^sha256:[0-9a-f]{64}$ ]] \
      || fail "control-plane container image ID is invalid"
  fi
  evidence_file="$(
    mktemp "${AEGISOPS_LAB_EVIDENCE_DIR}/status-${scope}-$(date -u '+%Y%m%dT%H%M%SZ').XXXXXX"
  )"
  write_evidence_header "${evidence_file}"
  printf 'control_plane_container_image_id=%s\n' \
    "${control_plane_container_image_id}" >>"${evidence_file}"
  printf '%s\n' "${status_output}" >>"${evidence_file}"
  chmod 600 "${evidence_file}"
  printf 'evidence=%s\n' "${evidence_file}"
fi
