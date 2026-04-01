#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
compose_path="${repo_root}/postgres/docker-compose.yml"

if [[ ! -f "${compose_path}" ]]; then
  echo "Missing PostgreSQL compose skeleton: ${compose_path}" >&2
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

require_fixed_string "name: aegisops-postgres"
require_fixed_string "services:"
require_fixed_string "  postgres:"
require_pattern '^    image: postgres:[^[:space:]]+$' \
  "PostgreSQL compose skeleton must pin postgres to an explicit version tag."

if grep -En '^    image: .*:latest$' "${compose_path}" >/dev/null; then
  echo "PostgreSQL compose skeleton must not use the latest tag." >&2
  exit 1
fi

if grep -En '^[[:space:]]*container_name:' "${compose_path}" >/dev/null; then
  echo "PostgreSQL compose skeleton must not hard-code container_name." >&2
  exit 1
fi

require_pattern '^    environment:$' \
  "PostgreSQL compose skeleton must declare environment variables."
require_pattern '^      POSTGRES_DB: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}$' \
  "PostgreSQL compose skeleton must use placeholder-safe environment references for POSTGRES_DB."
require_pattern '^      POSTGRES_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}$' \
  "PostgreSQL compose skeleton must use placeholder-safe environment references for POSTGRES_USER."
require_pattern '^      POSTGRES_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:\?set-in-runtime-secret-source}$' \
  "PostgreSQL compose skeleton must use placeholder-safe environment references for POSTGRES_PASSWORD."
require_pattern '^    volumes:$' \
  "PostgreSQL compose skeleton must declare volumes."
require_pattern '^      - /srv/aegisops/postgres-data-placeholder:/var/lib/postgresql/data$' \
  "PostgreSQL compose skeleton must use the explicit AegisOps PostgreSQL persistent mount placeholder."
require_pattern 'n8n metadata and execution state only' \
  "PostgreSQL compose skeleton must limit its role to n8n metadata and execution state only."
require_pattern 'skeleton only' \
  "PostgreSQL compose skeleton must state that it is a skeleton only."
require_pattern 'not production-ready' \
  "PostgreSQL compose skeleton must state that it is not production-ready."

if awk '
  BEGIN { in_postgres = 0; has_ports = 0 }
  $0 == "  postgres:" { in_postgres = 1; next }
  in_postgres && /^  [a-z0-9-]+:/ { in_postgres = 0 }
  in_postgres && /^[^[:space:]]/ { in_postgres = 0 }
  in_postgres && $0 == "    ports:" { has_ports = 1 }
  END { exit(has_ports ? 0 : 1) }
' "${compose_path}"; then
  echo "PostgreSQL compose skeleton must not publish PostgreSQL directly with ports." >&2
  exit 1
fi

echo "PostgreSQL compose skeleton matches the approved placeholder-safe contract."
