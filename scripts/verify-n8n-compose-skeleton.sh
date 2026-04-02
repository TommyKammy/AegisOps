#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
compose_path="${repo_root}/n8n/docker-compose.yml"

if [[ ! -f "${compose_path}" ]]; then
  echo "Missing n8n compose skeleton: ${compose_path}" >&2
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

require_fixed_string "name: aegisops-n8n"
require_fixed_string "services:"
require_fixed_string "  n8n:"
require_pattern '^    image: n8nio/n8n:[^[:space:]]+$' \
  "n8n compose skeleton must pin n8nio/n8n to an explicit version tag."

if grep -En '^    image: .*:latest$' "${compose_path}" >/dev/null; then
  echo "n8n compose skeleton must not use the latest tag." >&2
  exit 1
fi

if grep -En '^[[:space:]]*container_name:' "${compose_path}" >/dev/null; then
  echo "n8n compose skeleton must not hard-code container_name." >&2
  exit 1
fi

require_pattern '^    environment:$' \
  "n8n compose skeleton must declare environment variables."
require_pattern '^      DB_TYPE: postgresdb$' \
  "n8n compose skeleton must pin DB_TYPE to postgresdb."
require_pattern '^      DB_POSTGRESDB_HOST: \${AEGISOPS_POSTGRES_HOST:-postgres}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_HOST."
require_pattern '^      DB_POSTGRESDB_PORT: \${AEGISOPS_POSTGRES_PORT:-5432}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_PORT."
require_pattern '^      DB_POSTGRESDB_DATABASE: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_DATABASE."
require_pattern '^      DB_POSTGRESDB_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_USER."
require_pattern '^      DB_POSTGRESDB_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:\?set-in-runtime-secret-source}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_PASSWORD."
require_pattern '^      N8N_ENCRYPTION_KEY: \${AEGISOPS_N8N_ENCRYPTION_KEY:\?set-in-runtime-secret-source}$' \
  "n8n compose skeleton must use placeholder-safe environment references for N8N_ENCRYPTION_KEY."
require_pattern '^      N8N_HOST: \${AEGISOPS_N8N_HOST:-n8n-placeholder\.internal}$' \
  "n8n compose skeleton must use placeholder-safe environment references for N8N_HOST."
require_pattern '^      N8N_USER_FOLDER: \${AEGISOPS_N8N_USER_FOLDER:-/data/n8n-placeholder}$' \
  "n8n compose skeleton must use placeholder-safe environment references for N8N_USER_FOLDER."
require_pattern '^      WEBHOOK_URL: \${AEGISOPS_N8N_WEBHOOK_URL:-https://n8n-placeholder\.example\.invalid/}$' \
  "n8n compose skeleton must use placeholder-safe environment references for WEBHOOK_URL."
require_pattern '^    volumes:$' \
  "n8n compose skeleton must declare volumes."
require_pattern '^      - /srv/aegisops/n8n-data-placeholder:/data/n8n-placeholder$' \
  "n8n compose skeleton must use the explicit AegisOps n8n persistent mount placeholder."
require_pattern 'n8n orchestration only' \
  "n8n compose skeleton must limit its role to the approved n8n orchestration boundary."
require_pattern 'queue mode, Redis, and workflow import remain out of scope here' \
  "n8n compose skeleton must explicitly keep queue mode, Redis, and workflow import out of scope."
require_pattern 'skeleton only' \
  "n8n compose skeleton must state that it is a skeleton only."
require_pattern 'not production-ready' \
  "n8n compose skeleton must state that it is not production-ready."

if awk '
  BEGIN { in_n8n = 0; has_ports = 0 }
  $0 == "  n8n:" { in_n8n = 1; next }
  in_n8n && /^  [a-z0-9-]+:/ { in_n8n = 0 }
  in_n8n && /^[^[:space:]]/ { in_n8n = 0 }
  in_n8n && $0 ~ /^    ["'"'"']?ports["'"'"']?:[[:space:]]*$/ { has_ports = 1 }
  END { exit(has_ports ? 0 : 1) }
' "${compose_path}"; then
  echo "n8n compose skeleton must not publish n8n directly with ports." >&2
  exit 1
fi

if grep -En '(^  ["'"'"']?redis["'"'"']?:$|QUEUE_BULL_REDIS_|EXECUTIONS_MODE:[[:space:]]*["'"'"']?queue["'"'"']?[[:space:]]*$)' "${compose_path}" >/dev/null; then
  echo "n8n compose skeleton must not enable queue mode or Redis." >&2
  exit 1
fi

if grep -En '(import:workflow|import workflow|workflow(s)?/|bootstrap\.json)' "${compose_path}" >/dev/null; then
  echo "n8n compose skeleton must not introduce workflow import or execution logic." >&2
  exit 1
fi

echo "n8n compose skeleton matches the approved placeholder-safe contract."
