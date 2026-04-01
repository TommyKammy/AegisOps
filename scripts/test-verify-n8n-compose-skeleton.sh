#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-n8n-compose-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/n8n"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_compose() {
  local target="$1"
  local content="$2"

  printf '%s\n' "${content}" >"${target}/n8n/docker-compose.yml"
  git -C "${target}" add n8n/docker-compose.yml
  git -C "${target}" commit -q -m "fixture"
}

assert_passes() {
  local target="$1"

  if ! "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_compose "${valid_repo}" "name: aegisops-n8n
services:
  n8n:
    image: n8nio/n8n:1.89.2
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: \${AEGISOPS_POSTGRES_HOST:-postgres}
      DB_POSTGRESDB_PORT: \${AEGISOPS_POSTGRES_PORT:-5432}
      DB_POSTGRESDB_DATABASE: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
      N8N_ENCRYPTION_KEY: \${AEGISOPS_N8N_ENCRYPTION_KEY:?set-in-runtime-secret-source}
      N8N_HOST: \${AEGISOPS_N8N_HOST:-n8n-placeholder.internal}
      N8N_USER_FOLDER: \${AEGISOPS_N8N_USER_FOLDER:-/data/n8n-placeholder}
      WEBHOOK_URL: \${AEGISOPS_N8N_WEBHOOK_URL:-https://n8n-placeholder.example.invalid/}
    volumes:
      - /srv/aegisops/n8n-data-placeholder:/data/n8n-placeholder
    # approved for n8n orchestration only; queue mode, Redis, and workflow import remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_passes "${valid_repo}"

missing_file_repo="${workdir}/missing-file"
create_repo "${missing_file_repo}"
git -C "${missing_file_repo}" commit -q --allow-empty -m "fixture"
assert_fails_with "${missing_file_repo}" "Missing n8n compose skeleton"

latest_tag_repo="${workdir}/latest-tag"
create_repo "${latest_tag_repo}"
write_compose "${latest_tag_repo}" "name: aegisops-n8n
services:
  n8n:
    image: n8nio/n8n:latest
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: \${AEGISOPS_POSTGRES_HOST:-postgres}
      DB_POSTGRESDB_PORT: \${AEGISOPS_POSTGRES_PORT:-5432}
      DB_POSTGRESDB_DATABASE: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
      N8N_ENCRYPTION_KEY: \${AEGISOPS_N8N_ENCRYPTION_KEY:?set-in-runtime-secret-source}
      N8N_HOST: \${AEGISOPS_N8N_HOST:-n8n-placeholder.internal}
      N8N_USER_FOLDER: \${AEGISOPS_N8N_USER_FOLDER:-/data/n8n-placeholder}
      WEBHOOK_URL: \${AEGISOPS_N8N_WEBHOOK_URL:-https://n8n-placeholder.example.invalid/}
    volumes:
      - /srv/aegisops/n8n-data-placeholder:/data/n8n-placeholder
    # approved for n8n orchestration only; queue mode, Redis, and workflow import remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${latest_tag_repo}" "must not use the latest tag"

bad_mount_repo="${workdir}/bad-mount"
create_repo "${bad_mount_repo}"
write_compose "${bad_mount_repo}" "name: aegisops-n8n
services:
  n8n:
    image: n8nio/n8n:1.89.2
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: \${AEGISOPS_POSTGRES_HOST:-postgres}
      DB_POSTGRESDB_PORT: \${AEGISOPS_POSTGRES_PORT:-5432}
      DB_POSTGRESDB_DATABASE: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
      N8N_ENCRYPTION_KEY: \${AEGISOPS_N8N_ENCRYPTION_KEY:?set-in-runtime-secret-source}
      N8N_HOST: \${AEGISOPS_N8N_HOST:-n8n-placeholder.internal}
      N8N_USER_FOLDER: \${AEGISOPS_N8N_USER_FOLDER:-/data/n8n-placeholder}
      WEBHOOK_URL: \${AEGISOPS_N8N_WEBHOOK_URL:-https://n8n-placeholder.example.invalid/}
    volumes:
      - /tmp/n8n:/data/n8n-placeholder
    # approved for n8n orchestration only; queue mode, Redis, and workflow import remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${bad_mount_repo}" "persistent mount placeholder"

inline_secret_repo="${workdir}/inline-secret"
create_repo "${inline_secret_repo}"
write_compose "${inline_secret_repo}" "name: aegisops-n8n
services:
  n8n:
    image: n8nio/n8n:1.89.2
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: postgres
      DB_POSTGRESDB_PORT: 5432
      DB_POSTGRESDB_DATABASE: aegisops_n8n
      DB_POSTGRESDB_USER: aegisops_n8n
      DB_POSTGRESDB_PASSWORD: supersecret
      N8N_ENCRYPTION_KEY: anothersecret
      N8N_HOST: n8n.internal
      N8N_USER_FOLDER: /data/n8n-placeholder
      WEBHOOK_URL: https://n8n.internal/
    volumes:
      - /srv/aegisops/n8n-data-placeholder:/data/n8n-placeholder
    # approved for n8n orchestration only; queue mode, Redis, and workflow import remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${inline_secret_repo}" "placeholder-safe environment references"

ports_repo="${workdir}/ports"
create_repo "${ports_repo}"
write_compose "${ports_repo}" "name: aegisops-n8n
services:
  n8n:
    image: n8nio/n8n:1.89.2
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: \${AEGISOPS_POSTGRES_HOST:-postgres}
      DB_POSTGRESDB_PORT: \${AEGISOPS_POSTGRES_PORT:-5432}
      DB_POSTGRESDB_DATABASE: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
      N8N_ENCRYPTION_KEY: \${AEGISOPS_N8N_ENCRYPTION_KEY:?set-in-runtime-secret-source}
      N8N_HOST: \${AEGISOPS_N8N_HOST:-n8n-placeholder.internal}
      N8N_USER_FOLDER: \${AEGISOPS_N8N_USER_FOLDER:-/data/n8n-placeholder}
      WEBHOOK_URL: \${AEGISOPS_N8N_WEBHOOK_URL:-https://n8n-placeholder.example.invalid/}
    ports:
      - 5678:5678
    volumes:
      - /srv/aegisops/n8n-data-placeholder:/data/n8n-placeholder
    # approved for n8n orchestration only; queue mode, Redis, and workflow import remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${ports_repo}" "must not publish n8n directly with ports"

redis_repo="${workdir}/redis"
create_repo "${redis_repo}"
write_compose "${redis_repo}" "name: aegisops-n8n
services:
  n8n:
    image: n8nio/n8n:1.89.2
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: \${AEGISOPS_POSTGRES_HOST:-postgres}
      DB_POSTGRESDB_PORT: \${AEGISOPS_POSTGRES_PORT:-5432}
      DB_POSTGRESDB_DATABASE: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
      N8N_ENCRYPTION_KEY: \${AEGISOPS_N8N_ENCRYPTION_KEY:?set-in-runtime-secret-source}
      N8N_HOST: \${AEGISOPS_N8N_HOST:-n8n-placeholder.internal}
      N8N_USER_FOLDER: \${AEGISOPS_N8N_USER_FOLDER:-/data/n8n-placeholder}
      WEBHOOK_URL: \${AEGISOPS_N8N_WEBHOOK_URL:-https://n8n-placeholder.example.invalid/}
      EXECUTIONS_MODE: queue
      QUEUE_BULL_REDIS_HOST: redis
    volumes:
      - /srv/aegisops/n8n-data-placeholder:/data/n8n-placeholder
  redis:
    image: redis:7.4.2
    # approved for n8n orchestration only; queue mode, Redis, and workflow import remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${redis_repo}" "must not enable queue mode or Redis"

workflow_import_repo="${workdir}/workflow-import"
create_repo "${workflow_import_repo}"
write_compose "${workflow_import_repo}" "name: aegisops-n8n
services:
  n8n:
    image: n8nio/n8n:1.89.2
    command: [\"n8n\", \"import:workflow\", \"--input\", \"/workflows/bootstrap.json\"]
    environment:
      DB_TYPE: postgresdb
      DB_POSTGRESDB_HOST: \${AEGISOPS_POSTGRES_HOST:-postgres}
      DB_POSTGRESDB_PORT: \${AEGISOPS_POSTGRES_PORT:-5432}
      DB_POSTGRESDB_DATABASE: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      DB_POSTGRESDB_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
      N8N_ENCRYPTION_KEY: \${AEGISOPS_N8N_ENCRYPTION_KEY:?set-in-runtime-secret-source}
      N8N_HOST: \${AEGISOPS_N8N_HOST:-n8n-placeholder.internal}
      N8N_USER_FOLDER: \${AEGISOPS_N8N_USER_FOLDER:-/data/n8n-placeholder}
      WEBHOOK_URL: \${AEGISOPS_N8N_WEBHOOK_URL:-https://n8n-placeholder.example.invalid/}
    volumes:
      - /srv/aegisops/n8n-data-placeholder:/data/n8n-placeholder
    # approved for n8n orchestration only; queue mode, Redis, and workflow import remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${workflow_import_repo}" "must not introduce workflow import or execution logic"

echo "verify-n8n-compose-skeleton tests passed"
