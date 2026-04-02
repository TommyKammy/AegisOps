#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-ingest-compose-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/ingest"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_compose() {
  local target="$1"
  local content="$2"

  printf '%s\n' "${content}" >"${target}/ingest/docker-compose.yml"
  git -C "${target}" add ingest/docker-compose.yml
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
write_compose "${valid_repo}" "name: aegisops-ingest
services:
  collector:
    image: alpine:3.22.1
    profiles:
      - placeholder
  parser:
    image: alpine:3.22.1
    profiles:
      - placeholder
    # collection and parsing placeholder services only
    # source integrations, parsing logic, and routing remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_passes "${valid_repo}"

missing_file_repo="${workdir}/missing-file"
create_repo "${missing_file_repo}"
git -C "${missing_file_repo}" commit -q --allow-empty -m "fixture"
assert_fails_with "${missing_file_repo}" "Missing ingest compose skeleton"

latest_tag_repo="${workdir}/latest-tag"
create_repo "${latest_tag_repo}"
write_compose "${latest_tag_repo}" "name: aegisops-ingest
services:
  collector:
    image: alpine:latest
    profiles:
      - placeholder
  parser:
    image: alpine:3.22.1
    profiles:
      - placeholder
    # collection and parsing placeholder services only
    # source integrations, parsing logic, and routing remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${latest_tag_repo}" "must not use the latest tag"

missing_profile_repo="${workdir}/missing-profile"
create_repo "${missing_profile_repo}"
write_compose "${missing_profile_repo}" "name: aegisops-ingest
services:
  collector:
    image: alpine:3.22.1
  parser:
    image: alpine:3.22.1
    profiles:
      - placeholder
    # collection and parsing placeholder services only
    # source integrations, parsing logic, and routing remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${missing_profile_repo}" "must keep collector behind a placeholder-only profile"

ports_repo="${workdir}/ports"
create_repo "${ports_repo}"
write_compose "${ports_repo}" "name: aegisops-ingest
services:
  collector:
    image: alpine:3.22.1
    profiles:
      - placeholder
    ports:
      - 5514:5514
  parser:
    image: alpine:3.22.1
    profiles:
      - placeholder
    # collection and parsing placeholder services only
    # source integrations, parsing logic, and routing remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${ports_repo}" "must not publish ports"

source_specific_repo="${workdir}/source-specific"
create_repo "${source_specific_repo}"
write_compose "${source_specific_repo}" "name: aegisops-ingest
services:
  collector:
    image: alpine:3.22.1
    profiles:
      - placeholder
    command: [\"syslog-listener\"]
  parser:
    image: alpine:3.22.1
    profiles:
      - placeholder
    # collection and parsing placeholder services only
    # source integrations, parsing logic, and routing remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${source_specific_repo}" "must not introduce source-specific transport or parser behavior"

echo "verify-ingest-compose-skeleton tests passed"
