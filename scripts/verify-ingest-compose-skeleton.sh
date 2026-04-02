#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
compose_path="${repo_root}/ingest/docker-compose.yml"

if [[ ! -f "${compose_path}" ]]; then
  echo "Missing ingest compose skeleton: ${compose_path}" >&2
  exit 1
fi

require_fixed_string() {
  local expected="$1"

  if ! grep -Fqx "${expected}" "${compose_path}" >/dev/null; then
    echo "Missing required Compose line: ${expected}" >&2
    exit 1
  fi
}

require_pattern() {
  local pattern="$1"
  local message="$2"

  if ! grep -En "${pattern}" "${compose_path}" >/dev/null; then
    echo "${message}" >&2
    exit 1
  fi
}

extract_service_block() {
  local service_name="$1"

  awk -v service_name="${service_name}" '
    $0 == "  " service_name ":" { in_service = 1; next }
    in_service && /^  [a-z0-9-]+:/ { exit }
    in_service && /^[^[:space:]]/ { exit }
    in_service { print }
  ' "${compose_path}"
}

require_service_pattern() {
  local service_name="$1"
  local pattern="$2"
  local message="$3"

  if ! extract_service_block "${service_name}" | grep -En "${pattern}" >/dev/null; then
    echo "${message}" >&2
    exit 1
  fi
}

require_fixed_string "name: aegisops-ingest"
require_fixed_string "services:"
require_fixed_string "  collector:"
require_fixed_string "  parser:"
require_service_pattern "collector" '^    image: alpine:[^[:space:]]+$' \
  "Ingest compose skeleton must pin collector to an explicit placeholder image tag."
require_service_pattern "parser" '^    image: alpine:[^[:space:]]+$' \
  "Ingest compose skeleton must pin parser to an explicit placeholder image tag."
require_service_pattern "collector" '^    profiles:$' \
  "Ingest compose skeleton must keep collector behind a placeholder-only profile."
require_service_pattern "collector" '^      - placeholder$' \
  "Ingest compose skeleton must mark collector as placeholder-only."
require_service_pattern "parser" '^    profiles:$' \
  "Ingest compose skeleton must keep parser behind a placeholder-only profile."
require_service_pattern "parser" '^      - placeholder$' \
  "Ingest compose skeleton must mark parser as placeholder-only."
require_pattern 'collection and parsing placeholder services only' \
  "Ingest compose skeleton must state that it is limited to collection and parsing placeholders only."
require_pattern 'source integrations, parsing logic, and routing remain out of scope here' \
  "Ingest compose skeleton must explicitly defer integrations, parsing logic, and routing behavior."
require_pattern 'skeleton only' \
  "Ingest compose skeleton must state that it is a skeleton only."
require_pattern 'not production-ready' \
  "Ingest compose skeleton must state that it is not production-ready."

if grep -En '^    image: .*:latest$' "${compose_path}" >/dev/null; then
  echo "Ingest compose skeleton must not use the latest tag." >&2
  exit 1
fi

if grep -En '^[[:space:]]*container_name:' "${compose_path}" >/dev/null; then
  echo "Ingest compose skeleton must not hard-code container_name." >&2
  exit 1
fi

if grep -En '^[[:space:]]*ports:' "${compose_path}" >/dev/null; then
  echo "Ingest compose skeleton must not publish ports." >&2
  exit 1
fi

if grep -Ei '(syslog|filebeat|fluent-bit|fluentbit|vector|logstash|kafka|otlp|http input|tcp input|udp input)' "${compose_path}" >/dev/null; then
  echo "Ingest compose skeleton must not introduce source-specific transport or parser behavior." >&2
  exit 1
fi

echo "Ingest compose skeleton matches the approved placeholder-safe contract."
