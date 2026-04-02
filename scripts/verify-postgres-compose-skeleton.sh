#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
compose_path="${repo_root}/postgres/docker-compose.yml"
env_sample_path="${repo_root}/postgres/.env.sample"

if [[ ! -f "${compose_path}" ]]; then
  echo "Missing PostgreSQL compose skeleton: ${compose_path}" >&2
  exit 1
fi

if [[ ! -f "${env_sample_path}" ]]; then
  echo "Missing PostgreSQL environment sample placeholder: ${env_sample_path}" >&2
  exit 1
fi

require_fixed_string() {
  local file_path="$1"
  local expected="$2"

  if ! grep -Fqx "${expected}" "${file_path}" >/dev/null; then
    echo "Missing required line in ${file_path}: ${expected}" >&2
    exit 1
  fi
}

require_pattern() {
  local file_path="$1"
  local pattern="$2"
  local message="$3"

  if ! grep -En "${pattern}" "${file_path}" >/dev/null; then
    echo "${message}" >&2
    exit 1
  fi
}

require_fixed_string "${compose_path}" "name: aegisops-postgres"
require_fixed_string "${compose_path}" "services:"
require_fixed_string "${compose_path}" "  postgres:"
require_pattern "${compose_path}" '^    image: postgres:[^[:space:]]+$' \
  "PostgreSQL compose skeleton must pin postgres to an explicit version tag."

if grep -En '^    image: .*:latest$' "${compose_path}" >/dev/null; then
  echo "PostgreSQL compose skeleton must not use the latest tag." >&2
  exit 1
fi

if grep -En '^[[:space:]]*container_name:' "${compose_path}" >/dev/null; then
  echo "PostgreSQL compose skeleton must not hard-code container_name." >&2
  exit 1
fi

require_pattern "${compose_path}" '^    environment:$' \
  "PostgreSQL compose skeleton must declare environment variables."
require_pattern "${compose_path}" '^      POSTGRES_DB: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}$' \
  "PostgreSQL compose skeleton must use placeholder-safe environment references for POSTGRES_DB."
require_pattern "${compose_path}" '^      POSTGRES_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}$' \
  "PostgreSQL compose skeleton must use placeholder-safe environment references for POSTGRES_USER."
require_pattern "${compose_path}" '^      POSTGRES_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:\?set-in-runtime-secret-source}$' \
  "PostgreSQL compose skeleton must use placeholder-safe environment references for POSTGRES_PASSWORD."
require_pattern "${compose_path}" '^    volumes:$' \
  "PostgreSQL compose skeleton must declare volumes."
require_pattern "${compose_path}" '^      - /srv/aegisops/postgres-data-placeholder:/var/lib/postgresql/data$' \
  "PostgreSQL compose skeleton must use the explicit AegisOps PostgreSQL persistent mount placeholder."
require_pattern "${compose_path}" 'n8n metadata and execution state only' \
  "PostgreSQL compose skeleton must limit its role to n8n metadata and execution state only."
require_pattern "${compose_path}" 'skeleton only' \
  "PostgreSQL compose skeleton must state that it is a skeleton only."
require_pattern "${compose_path}" 'not production-ready' \
  "PostgreSQL compose skeleton must state that it is not production-ready."
require_pattern "${env_sample_path}" '^# Sample environment placeholders for the PostgreSQL compose skeleton only\.$' \
  "PostgreSQL environment sample placeholder must declare itself as sample-only."
require_pattern "${env_sample_path}" '^# Do not use these placeholder values in production\.$' \
  "PostgreSQL environment sample placeholder must declare itself non-production."
require_fixed_string "${env_sample_path}" "AEGISOPS_POSTGRES_DB=aegisops_n8n_placeholder"
require_fixed_string "${env_sample_path}" "AEGISOPS_POSTGRES_USER=aegisops_n8n_placeholder"
require_fixed_string "${env_sample_path}" "AEGISOPS_POSTGRES_PASSWORD=placeholder-not-a-secret"

if grep -Env '^[A-Z0-9_]+=.+$|^#|^$' "${env_sample_path}" >/dev/null; then
  echo "PostgreSQL environment sample placeholder must contain only comments, blank lines, and simple KEY=value entries." >&2
  exit 1
fi

if grep -E '^[^#[:space:]=]+=' "${env_sample_path}" | cut -d '=' -f 1 | grep -Ev '^AEGISOPS_' >/dev/null; then
  echo "PostgreSQL environment sample placeholder must use only approved AEGISOPS_* variable names." >&2
  exit 1
fi

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
