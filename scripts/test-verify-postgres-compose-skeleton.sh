#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-postgres-compose-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/postgres"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_compose() {
  local target="$1"
  local content="$2"

  printf '%s\n' "${content}" >"${target}/postgres/docker-compose.yml"
  git -C "${target}" add postgres/docker-compose.yml
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
write_compose "${valid_repo}" "name: aegisops-postgres
services:
  postgres:
    image: postgres:16.4
    environment:
      POSTGRES_DB: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      POSTGRES_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      POSTGRES_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
    volumes:
      - /srv/aegisops/postgres-data-placeholder:/var/lib/postgresql/data
    # internal state store for n8n metadata and execution state only
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_passes "${valid_repo}"

missing_file_repo="${workdir}/missing-file"
create_repo "${missing_file_repo}"
git -C "${missing_file_repo}" commit -q --allow-empty -m "fixture"
assert_fails_with "${missing_file_repo}" "Missing PostgreSQL compose skeleton"

latest_tag_repo="${workdir}/latest-tag"
create_repo "${latest_tag_repo}"
write_compose "${latest_tag_repo}" "name: aegisops-postgres
services:
  postgres:
    image: postgres:latest
    environment:
      POSTGRES_DB: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      POSTGRES_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      POSTGRES_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
    volumes:
      - /srv/aegisops/postgres-data-placeholder:/var/lib/postgresql/data
    # internal state store for n8n metadata and execution state only
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${latest_tag_repo}" "must not use the latest tag"

bad_mount_repo="${workdir}/bad-mount"
create_repo "${bad_mount_repo}"
write_compose "${bad_mount_repo}" "name: aegisops-postgres
services:
  postgres:
    image: postgres:16.4
    environment:
      POSTGRES_DB: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      POSTGRES_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      POSTGRES_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
    volumes:
      - /tmp/postgres:/var/lib/postgresql/data
    # internal state store for n8n metadata and execution state only
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${bad_mount_repo}" "persistent mount placeholder"

inline_secret_repo="${workdir}/inline-secret"
create_repo "${inline_secret_repo}"
write_compose "${inline_secret_repo}" "name: aegisops-postgres
services:
  postgres:
    image: postgres:16.4
    environment:
      POSTGRES_DB: aegisops_n8n
      POSTGRES_USER: aegisops_n8n
      POSTGRES_PASSWORD: supersecret
    volumes:
      - /srv/aegisops/postgres-data-placeholder:/var/lib/postgresql/data
    # internal state store for n8n metadata and execution state only
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${inline_secret_repo}" "placeholder-safe environment references"

ports_repo="${workdir}/ports"
create_repo "${ports_repo}"
write_compose "${ports_repo}" "name: aegisops-postgres
services:
  postgres:
    image: postgres:16.4
    environment:
      POSTGRES_DB: \${AEGISOPS_POSTGRES_DB:-aegisops_n8n_placeholder}
      POSTGRES_USER: \${AEGISOPS_POSTGRES_USER:-aegisops_n8n_placeholder}
      POSTGRES_PASSWORD: \${AEGISOPS_POSTGRES_PASSWORD:?set-in-runtime-secret-source}
    ports:
      - 5432:5432
    volumes:
      - /srv/aegisops/postgres-data-placeholder:/var/lib/postgresql/data
    # internal state store for n8n metadata and execution state only
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${ports_repo}" "must not publish PostgreSQL directly with ports"

echo "verify-postgres-compose-skeleton tests passed"
