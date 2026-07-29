#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_environment
assert_safe_runtime_root "${AEGISOPS_LAB_RUNTIME_ROOT}"
assert_reviewed_lab_pins
require_command git
require_command python3

: "${AEGISOPS_LAB_WAZUH_SOURCE_DIR:?AEGISOPS_LAB_WAZUH_SOURCE_DIR is required}"
: "${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT:?AEGISOPS_LAB_WAZUH_DOCKER_COMMIT is required}"
: "${AEGISOPS_LAB_WAZUH_VERSION:?AEGISOPS_LAB_WAZUH_VERSION is required}"

if [[ -e "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}" && ! -d "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}/.git" ]]; then
  fail "Wazuh substrate path exists but is not a Git checkout: ${AEGISOPS_LAB_WAZUH_SOURCE_DIR}"
fi

if [[ ! -d "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}/.git" ]]; then
  mkdir -p "$(dirname "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}")"
  git clone \
    --depth 1 \
    --branch "v${AEGISOPS_LAB_WAZUH_VERSION}" \
    https://github.com/wazuh/wazuh-docker.git \
    "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}"
fi

wazuh_internal_users_relative_path="single-node/config/wazuh_indexer/internal_users.yml"
assert_reviewed_wazuh_checkout \
  "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}" \
  "${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT}" \
  "${wazuh_internal_users_relative_path}"
require_command docker
require_command openssl

# Preparation launches platform-selected helper images before up.sh. Reuse the
# Wazuh preflight so architecture, explicit emulation acceptance, and enabled
# binfmt handler checks complete before any Docker mutation or container run.
"${LAB_DIR}/preflight.sh" --scope wazuh

cert_dir="${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/wazuh_indexer_ssl_certs"
wazuh_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-certificate-recreate-required"
mark_wazuh_recreation_required() {
  : >"${wazuh_recreate_marker}"
  chmod 600 "${wazuh_recreate_marker}"
}

required_certificates="
root-ca.pem
root-ca-manager.pem
wazuh.indexer-key.pem
wazuh.indexer.pem
admin.pem
admin-key.pem
wazuh.manager.pem
wazuh.manager-key.pem
wazuh.dashboard.pem
wazuh.dashboard-key.pem
"
certificates_complete=true
validate_wazuh_certificate_bundle "${cert_dir}" || certificates_complete=false

if [[ "${certificates_complete}" != true ]]; then
  cert_volume="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-cert-staging-$$"
  cert_container="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-cert-copy-$$"
  cert_image="wazuh/wazuh-certs-generator:0.0.4@sha256:369b4d58509aab074b188596870c81584f7120e653d9ef83c591f0f785dcf325"

  cleanup_cert_staging() {
    docker_lab rm --force "${cert_container}" >/dev/null 2>&1 || true
    docker_lab volume rm "${cert_volume}" >/dev/null 2>&1 || true
  }
  trap cleanup_cert_staging EXIT

  docker_lab volume create \
    --label com.aegisops.lab.phase=67.1 \
    --label "com.docker.compose.project=${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}" \
    "${cert_volume}" >/dev/null
  docker_lab run --rm \
    --env CERT_TOOL_VERSION=4.14 \
    --mount "type=volume,source=${cert_volume},target=/certificates" \
    --mount "type=bind,source=${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/certs.yml,target=/config/certs.yml,readonly" \
    "${cert_image}"

  mkdir -p "${cert_dir}"
  chmod 700 "${cert_dir}"
  docker_lab create \
    --name "${cert_container}" \
    --mount "type=volume,source=${cert_volume},target=/certificates" \
    --entrypoint /bin/true \
    "${cert_image}" >/dev/null
  mark_wazuh_recreation_required
  docker_lab cp "${cert_container}:/certificates/." "${cert_dir}"
  cleanup_cert_staging
  trap - EXIT
  validate_wazuh_certificate_bundle "${cert_dir}" \
    || fail "regenerated Wazuh certificate bundle failed validity, chain, or key-pair validation"
fi

validate_wazuh_certificate_bundle "${cert_dir}" \
  || fail "Wazuh certificate bundle failed validity, identity, chain, or key-pair validation"

proxy_wazuh_trust="${AEGISOPS_LAB_PROXY_CERT_DIR}/wazuh-upstream-root-ca.pem"
if ! cmp -s "${cert_dir}/root-ca.pem" "${proxy_wazuh_trust}"; then
  proxy_recreate_marker="${AEGISOPS_LAB_RUNTIME_ROOT}/proxy-certificate-recreate-required"
  : >"${proxy_recreate_marker}"
  chmod 600 "${proxy_recreate_marker}"
  proxy_wazuh_trust_staging="$(mktemp "${AEGISOPS_LAB_PROXY_CERT_DIR}/.wazuh-upstream-root-ca.XXXXXX")"
  cleanup_proxy_wazuh_trust_staging() {
    rm -f "${proxy_wazuh_trust_staging}"
  }
  trap cleanup_proxy_wazuh_trust_staging EXIT
  cp "${cert_dir}/root-ca.pem" "${proxy_wazuh_trust_staging}"
  chmod 600 "${proxy_wazuh_trust_staging}"
  mv "${proxy_wazuh_trust_staging}" "${proxy_wazuh_trust}"
  proxy_wazuh_trust_staging=""
  trap - EXIT
fi

indexer_image="wazuh/wazuh-indexer:${AEGISOPS_LAB_WAZUH_VERSION}@sha256:27261711c6479e2e503171918aae9a23b3fc4dcfc2d28d204e75985c1e0fb4c5"
generate_indexer_password_hash() {
  local password="$1"

  docker_lab run --rm \
    --platform "${AEGISOPS_LAB_WAZUH_PLATFORM}" \
    --env OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk \
    --entrypoint bash \
    "${indexer_image}" \
    -c '/usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh -p "$1"' \
    phase67 "${password}" |
    grep -E '^\$2[aby]\$' |
    tail -1
}

admin_hash="$(
  generate_indexer_password_hash \
    "$(<"${AEGISOPS_LAB_SECRET_DIR}/wazuh-indexer-password")"
)"
[[ -n "${admin_hash}" ]] || fail "Wazuh indexer password hash generation returned no bcrypt hash"
dashboard_hash="$(
  generate_indexer_password_hash \
    "$(<"${AEGISOPS_LAB_SECRET_DIR}/wazuh-dashboard-password")"
)"
[[ -n "${dashboard_hash}" ]] || fail "Wazuh dashboard password hash generation returned no bcrypt hash"
disabled_demo_hash="$(generate_indexer_password_hash "$(openssl rand -hex 32)")"
[[ -n "${disabled_demo_hash}" ]] \
  || fail "Wazuh unused demo-user hash generation returned no bcrypt hash"

internal_users="${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/wazuh_indexer/internal_users.yml"
mark_wazuh_recreation_required
python3 - \
  "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}" \
  "${wazuh_internal_users_relative_path}" \
  "${internal_users}" \
  "${admin_hash}" \
  "${dashboard_hash}" \
  "${disabled_demo_hash}" <<'PY'
from __future__ import annotations

import os
import pathlib
import subprocess
import sys

repository = pathlib.Path(sys.argv[1])
relative_path = sys.argv[2]
path = pathlib.Path(sys.argv[3])
admin_hash = sys.argv[4]
dashboard_hash = sys.argv[5]
disabled_demo_hash = sys.argv[6]

canonical = subprocess.run(
    ["git", "-C", str(repository), "show", f"HEAD:{relative_path}"],
    check=True,
    capture_output=True,
    text=True,
).stdout
current = path.read_text(encoding="utf-8")

def replace_user_hash(document: str, username: str, replacement: str) -> str:
    lines = document.splitlines()
    section_start = next(
        (index for index, line in enumerate(lines) if line == f"{username}:"),
        None,
    )
    if section_start is None:
        raise SystemExit(
            f"{username} section is missing from Wazuh internal_users.yml"
        )

    section_end = next(
        (
            index
            for index in range(section_start + 1, len(lines))
            if lines[index] and not lines[index][0].isspace() and lines[index].endswith(":")
        ),
        len(lines),
    )
    hash_indexes = [
        index
        for index in range(section_start + 1, section_end)
        if lines[index].lstrip().startswith("hash:")
    ]
    if len(hash_indexes) != 1:
        raise SystemExit(f"{username} section must contain exactly one hash entry")

    hash_index = hash_indexes[0]
    indent = lines[hash_index][: len(lines[hash_index]) - len(lines[hash_index].lstrip())]
    lines[hash_index] = f'{indent}hash: "{replacement}"'
    return "\n".join(lines) + "\n"


def normalize_managed_hashes(document: str) -> str:
    normalized = replace_user_hash(
        document,
        "admin",
        "__AEGISOPS_REVIEWED_ADMIN_HASH__",
    )
    normalized = replace_user_hash(
        normalized,
        "kibanaserver",
        "__AEGISOPS_REVIEWED_DASHBOARD_HASH__",
    )
    for username in ("kibanaro", "logstash", "readall", "snapshotrestore"):
        normalized = replace_user_hash(
            normalized,
            username,
            f"__AEGISOPS_DISABLED_{username.upper()}_HASH__",
        )
    return normalized


if normalize_managed_hashes(current) != normalize_managed_hashes(canonical):
    raise SystemExit(
        "Wazuh internal_users.yml has unreviewed changes outside managed hashes"
    )

expected = replace_user_hash(canonical, "admin", admin_hash)
expected = replace_user_hash(expected, "kibanaserver", dashboard_hash)
for username in ("kibanaro", "logstash", "readall", "snapshotrestore"):
    expected = replace_user_hash(expected, username, disabled_demo_hash)
temporary_path = path.with_name(f".{path.name}.aegisops-{os.getpid()}")
try:
    temporary_path.write_text(expected, encoding="utf-8")
    temporary_path.chmod(0o600)
    os.replace(temporary_path, path)
finally:
    temporary_path.unlink(missing_ok=True)
PY
chmod 600 "${internal_users}"
record_reviewed_file_digest \
  "${internal_users}" \
  "${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-internal-users.sha256"

manager_config_relative_path="single-node/config/wazuh_cluster/wazuh_manager.conf"
manager_config_fragment="${LAB_DIR}/wazuh/ossec-integration.xml"
: "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG:?AEGISOPS_LAB_WAZUH_MANAGER_CONFIG is required}"
[[ -s "${manager_config_fragment}" ]] \
  || fail "Phase 67.2 Wazuh integration fragment is missing"
manager_config_staging="$(
  mktemp "$(dirname "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}")/.manager-ossec.XXXXXX"
)"
cleanup_manager_config_staging() {
  [[ -z "${manager_config_staging:-}" ]] || rm -f "${manager_config_staging}"
}
trap cleanup_manager_config_staging EXIT
{
  git -C "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}" \
    show "HEAD:${manager_config_relative_path}"
  printf '\n'
  cat "${manager_config_fragment}"
  printf '\n'
} >"${manager_config_staging}"
chmod 600 "${manager_config_staging}"
if ! cmp -s "${manager_config_staging}" "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"; then
  mv "${manager_config_staging}" "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"
  manager_config_staging=""
  mark_wazuh_recreation_required
else
  rm -f "${manager_config_staging}"
  manager_config_staging=""
fi
trap - EXIT
chmod 600 "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}"
record_reviewed_file_digest \
  "${AEGISOPS_LAB_WAZUH_MANAGER_CONFIG}" \
  "${AEGISOPS_LAB_RUNTIME_ROOT}/wazuh-manager-config.sha256"

echo "Prepared Wazuh ${AEGISOPS_LAB_WAZUH_VERSION} substrate at ${AEGISOPS_LAB_WAZUH_SOURCE_DIR}"
echo "The next wazuh/full up.sh run will force service recreation."
echo "Shuffle execution setup is handled separately by bootstrap-shuffle.sh."
