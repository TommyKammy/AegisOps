#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
compose_path="${repo_root}/opensearch/docker-compose.yml"

if [[ ! -f "${compose_path}" ]]; then
  echo "Missing OpenSearch compose skeleton: ${compose_path}" >&2
  exit 1
fi

require_fixed_string() {
  local expected="$1"

  if ! grep -Fqx "${expected}" "${compose_path}"; then
    echo "Missing required Compose line: ${expected}" >&2
    exit 1
  fi
}

require_pattern() {
  local pattern="$1"
  local message="$2"

  if ! rg -n "${pattern}" "${compose_path}" >/dev/null; then
    echo "${message}" >&2
    exit 1
  fi
}

require_fixed_string "name: aegisops-opensearch"
require_fixed_string "services:"
require_fixed_string "  opensearch:"
require_pattern '^    image: [^[:space:]]+:[^[:space:]]+$' \
  "OpenSearch compose skeleton must pin the image version explicitly."

if rg -n '^    image: .*:latest$' "${compose_path}" >/dev/null; then
  echo "OpenSearch compose skeleton must not use the latest tag." >&2
  exit 1
fi

if rg -n '^\s*container_name:' "${compose_path}" >/dev/null; then
  echo "OpenSearch compose skeleton must not hard-code container_name." >&2
  exit 1
fi

require_pattern '^    volumes:$' \
  "OpenSearch compose skeleton must declare volumes."
require_pattern '^      - /srv/aegisops/opensearch-data-placeholder:/usr/share/opensearch/data$' \
  "OpenSearch compose skeleton must use the explicit AegisOps OpenSearch persistent mount placeholder."
require_pattern 'skeleton only' \
  "OpenSearch compose skeleton must state that it is a skeleton only."
require_pattern 'not production-ready' \
  "OpenSearch compose skeleton must state that it is not production-ready."

echo "OpenSearch compose skeleton matches the approved placeholder-safe contract."
