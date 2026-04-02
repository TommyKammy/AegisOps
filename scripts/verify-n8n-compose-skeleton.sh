#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
compose_path="${repo_root}/n8n/docker-compose.yml"
env_sample_path="${repo_root}/n8n/.env.sample"

if [[ ! -f "${compose_path}" ]]; then
  echo "Missing n8n compose skeleton: ${compose_path}" >&2
  exit 1
fi

if [[ ! -f "${env_sample_path}" ]]; then
  echo "Missing n8n environment sample placeholder: ${env_sample_path}" >&2
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

extract_n8n_block() {
  awk '
    /^  n8n:[[:space:]]*(#.*)?$/ { in_n8n = 1 }
    in_n8n && /^[^[:space:]]/ { exit }
    in_n8n && /^  [a-z0-9_-]+:[[:space:]]*(#.*)?$/ && $0 !~ /^  n8n:[[:space:]]*(#.*)?$/ { exit }
    in_n8n { print }
  ' "${compose_path}"
}

require_n8n_pattern() {
  local pattern="$1"
  local message="$2"

  if ! extract_n8n_block | grep -En "${pattern}" >/dev/null; then
    echo "${message}" >&2
    exit 1
  fi
}

require_fixed_string "${compose_path}" "name: aegisops-n8n"
require_fixed_string "${compose_path}" "services:"
require_fixed_string "${compose_path}" "  n8n:"
require_n8n_pattern '^    image: n8nio/n8n:[^[:space:]]+$' \
  "n8n compose skeleton must pin n8nio/n8n to an explicit version tag."

if grep -En '^    image: .*:latest$' "${compose_path}" >/dev/null; then
  echo "n8n compose skeleton must not use the latest tag." >&2
  exit 1
fi

if grep -En '^[[:space:]]*container_name:' "${compose_path}" >/dev/null; then
  echo "n8n compose skeleton must not hard-code container_name." >&2
  exit 1
fi

require_n8n_pattern '^    environment:$' \
  "n8n compose skeleton must declare environment variables."
require_n8n_pattern '^      DB_TYPE: postgresdb$' \
  "n8n compose skeleton must pin DB_TYPE to postgresdb."
require_n8n_pattern '^      DB_POSTGRESDB_HOST: \${AEGISOPS_POSTGRES_HOST:-postgres}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_HOST."
require_n8n_pattern '^      DB_POSTGRESDB_PORT: \${AEGISOPS_POSTGRES_PORT:-5432}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_PORT."
require_n8n_pattern '^      DB_POSTGRESDB_DATABASE: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_DATABASE."
require_n8n_pattern '^      DB_POSTGRESDB_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_USER."
require_n8n_pattern '^      DB_POSTGRESDB_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:\?set-in-runtime-secret-source}$' \
  "n8n compose skeleton must use placeholder-safe environment references for DB_POSTGRESDB_PASSWORD."
require_n8n_pattern '^      N8N_ENCRYPTION_KEY: \${AEGISOPS_N8N_ENCRYPTION_KEY:\?set-in-runtime-secret-source}$' \
  "n8n compose skeleton must use placeholder-safe environment references for N8N_ENCRYPTION_KEY."
require_n8n_pattern '^      N8N_HOST: \${AEGISOPS_N8N_HOST:-n8n-placeholder\.internal}$' \
  "n8n compose skeleton must use placeholder-safe environment references for N8N_HOST."
require_n8n_pattern '^      N8N_USER_FOLDER: \${AEGISOPS_N8N_USER_FOLDER:-/data/n8n-placeholder}$' \
  "n8n compose skeleton must use placeholder-safe environment references for N8N_USER_FOLDER."
require_n8n_pattern '^      WEBHOOK_URL: \${AEGISOPS_N8N_WEBHOOK_URL:-https://n8n-placeholder\.example\.invalid/}$' \
  "n8n compose skeleton must use placeholder-safe environment references for WEBHOOK_URL."
require_n8n_pattern '^    volumes:$' \
  "n8n compose skeleton must declare volumes."
require_n8n_pattern '^      - /srv/aegisops/n8n-data-placeholder:/data/n8n-placeholder$' \
  "n8n compose skeleton must use the explicit AegisOps n8n persistent mount placeholder."
require_pattern "${compose_path}" 'n8n orchestration only' \
  "n8n compose skeleton must limit its role to the approved n8n orchestration boundary."
require_pattern "${compose_path}" 'queue mode, Redis, and workflow import remain out of scope here' \
  "n8n compose skeleton must explicitly keep queue mode, Redis, and workflow import out of scope."
require_pattern "${compose_path}" 'skeleton only' \
  "n8n compose skeleton must state that it is a skeleton only."
require_pattern "${compose_path}" 'not production-ready' \
  "n8n compose skeleton must state that it is not production-ready."

require_pattern "${env_sample_path}" '^# Sample environment placeholders for the n8n compose skeleton only\.$' \
  "n8n environment sample placeholder must declare itself as sample-only."
require_pattern "${env_sample_path}" '^# Do not use these placeholder values in production\.$' \
  "n8n environment sample placeholder must declare itself non-production."
require_fixed_string "${env_sample_path}" "AEGISOPS_POSTGRES_HOST=postgres"
require_fixed_string "${env_sample_path}" "AEGISOPS_POSTGRES_PORT=5432"
require_fixed_string "${env_sample_path}" "AEGISOPS_POSTGRES_DB=aegisops_n8n_placeholder"
require_fixed_string "${env_sample_path}" "AEGISOPS_POSTGRES_USER=aegisops_n8n_placeholder"
require_fixed_string "${env_sample_path}" "AEGISOPS_POSTGRES_PASSWORD=placeholder-not-a-secret"
require_fixed_string "${env_sample_path}" "AEGISOPS_N8N_ENCRYPTION_KEY=placeholder-not-a-secret"
require_fixed_string "${env_sample_path}" "AEGISOPS_N8N_HOST=n8n-placeholder.internal"
require_fixed_string "${env_sample_path}" "AEGISOPS_N8N_USER_FOLDER=/data/n8n-placeholder"
require_fixed_string "${env_sample_path}" "AEGISOPS_N8N_WEBHOOK_URL=https://n8n-placeholder.example.invalid/"

if grep -Env '^[A-Z0-9_]+=.+$|^#|^$' "${env_sample_path}" >/dev/null; then
  echo "n8n environment sample placeholder must contain only comments, blank lines, and simple KEY=value entries." >&2
  exit 1
fi

if grep -E '^[^#[:space:]=]+=' "${env_sample_path}" | cut -d '=' -f 1 | grep -Ev '^AEGISOPS_' >/dev/null; then
  echo "n8n environment sample placeholder must use only approved AEGISOPS_* variable names." >&2
  exit 1
fi

if extract_n8n_block | awk '
  BEGIN { has_ports = 0 }
  $0 ~ /^    ["'"'"']?ports["'"'"']?:[[:space:]]*(#.*)?$/ { has_ports = 1 }
  END { exit(has_ports ? 0 : 1) }
'; then
  echo "n8n compose skeleton must not publish n8n directly with ports." >&2
  exit 1
fi

if grep -En '(^  ["'"'"']?redis["'"'"']?:[[:space:]]*(#.*)?$|QUEUE_BULL_REDIS_|EXECUTIONS_MODE:[[:space:]]*["'"'"']?queue["'"'"']?[[:space:]]*(#.*)?$)' "${compose_path}" >/dev/null; then
  echo "n8n compose skeleton must not enable queue mode or Redis." >&2
  exit 1
fi

if grep -En '(import:workflow|import workflow|workflow(s)?/|bootstrap\.json)' "${compose_path}" >/dev/null; then
  echo "n8n compose skeleton must not introduce workflow import or execution logic." >&2
  exit 1
fi

echo "n8n compose skeleton matches the approved placeholder-safe contract."
