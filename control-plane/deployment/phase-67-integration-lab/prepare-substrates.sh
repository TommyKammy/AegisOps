#!/usr/bin/env bash

set -euo pipefail

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_environment
assert_safe_runtime_root "${AEGISOPS_LAB_RUNTIME_ROOT}"
require_command docker
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

actual_commit="$(git -C "${AEGISOPS_LAB_WAZUH_SOURCE_DIR}" rev-parse HEAD)"
[[ "${actual_commit}" == "${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT}" ]] \
  || fail "Wazuh substrate commit is ${actual_commit}; expected ${AEGISOPS_LAB_WAZUH_DOCKER_COMMIT}"

cert_dir="${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/wazuh_indexer_ssl_certs"
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
for certificate in ${required_certificates}; do
  if [[ ! -s "${cert_dir}/${certificate}" ]]; then
    certificates_complete=false
    break
  fi
done

if [[ "${certificates_complete}" != true ]]; then
  cert_volume="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-cert-staging-$$"
  cert_container="${AEGISOPS_LAB_COMPOSE_PROJECT_NAME}-cert-copy-$$"
  cert_image="wazuh/wazuh-certs-generator:0.0.4"

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
  docker_lab cp "${cert_container}:/certificates/." "${cert_dir}"
  cleanup_cert_staging
  trap - EXIT
fi

for certificate in ${required_certificates}; do
  [[ -s "${cert_dir}/${certificate}" ]] \
    || fail "Wazuh certificate generation is incomplete; missing ${certificate}"
done

indexer_image="wazuh/wazuh-indexer:${AEGISOPS_LAB_WAZUH_VERSION}@sha256:27261711c6479e2e503171918aae9a23b3fc4dcfc2d28d204e75985c1e0fb4c5"
admin_hash="$(
  docker_lab run --rm \
    --platform "${AEGISOPS_LAB_WAZUH_PLATFORM}" \
    --env OPENSEARCH_JAVA_HOME=/usr/share/wazuh-indexer/jdk \
    --entrypoint bash \
    "${indexer_image}" \
    -c '/usr/share/wazuh-indexer/plugins/opensearch-security/tools/hash.sh -p "$1"' \
    phase67 "$( <"${AEGISOPS_LAB_SECRET_DIR}/wazuh-indexer-password" )" |
    grep -E '^\$2[aby]\$' |
    tail -1
)"
[[ -n "${admin_hash}" ]] || fail "Wazuh indexer password hash generation returned no bcrypt hash"

internal_users="${AEGISOPS_LAB_WAZUH_CONFIG_DIR}/wazuh_indexer/internal_users.yml"
python3 - "${internal_users}" "${admin_hash}" <<'PY'
from __future__ import annotations

import pathlib
import sys

path = pathlib.Path(sys.argv[1])
new_hash = sys.argv[2]
lines = path.read_text(encoding="utf-8").splitlines()

section_start = next((index for index, line in enumerate(lines) if line == "admin:"), None)
if section_start is None:
    raise SystemExit("admin section is missing from Wazuh internal_users.yml")

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
    raise SystemExit("admin section must contain exactly one hash entry")

indent = lines[hash_indexes[0]][: len(lines[hash_indexes[0]]) - len(lines[hash_indexes[0]].lstrip())]
lines[hash_indexes[0]] = f'{indent}hash: "{new_hash}"'
path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY
chmod 600 "${internal_users}"

echo "Prepared Wazuh ${AEGISOPS_LAB_WAZUH_VERSION} substrate at ${AEGISOPS_LAB_WAZUH_SOURCE_DIR}"
echo "Shuffle images remain execution-disabled; Docker socket mounting is deferred to Phase 67.3."
