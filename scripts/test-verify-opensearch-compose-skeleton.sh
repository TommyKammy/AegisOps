#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-opensearch-compose-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/opensearch"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_compose() {
  local target="$1"
  local content="$2"

  printf '%s\n' "${content}" >"${target}/opensearch/docker-compose.yml"
  git -C "${target}" add opensearch/docker-compose.yml
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
write_compose "${valid_repo}" "name: aegisops-opensearch
services:
  opensearch:
    image: opensearchproject/opensearch:2.19.0
    volumes:
      - /srv/aegisops/opensearch-data-placeholder:/usr/share/opensearch/data
  dashboards:
    image: opensearchproject/opensearch-dashboards:2.19.0
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_passes "${valid_repo}"

missing_file_repo="${workdir}/missing-file"
create_repo "${missing_file_repo}"
git -C "${missing_file_repo}" commit -q --allow-empty -m "fixture"
assert_fails_with "${missing_file_repo}" "Missing OpenSearch compose skeleton"

latest_tag_repo="${workdir}/latest-tag"
create_repo "${latest_tag_repo}"
write_compose "${latest_tag_repo}" "name: aegisops-opensearch
services:
  opensearch:
    image: opensearchproject/opensearch:latest
    volumes:
      - /srv/aegisops/opensearch-data-placeholder:/usr/share/opensearch/data
  dashboards:
    image: opensearchproject/opensearch-dashboards:2.19.0
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${latest_tag_repo}" "must not use the latest tag"

bad_mount_repo="${workdir}/bad-mount"
create_repo "${bad_mount_repo}"
write_compose "${bad_mount_repo}" "name: aegisops-opensearch
services:
  opensearch:
    image: opensearchproject/opensearch:2.19.0
    volumes:
      - /tmp/opensearch:/usr/share/opensearch/data
  dashboards:
    image: opensearchproject/opensearch-dashboards:2.19.0
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${bad_mount_repo}" "persistent mount placeholder"

bad_image_repo="${workdir}/bad-image-repo"
create_repo "${bad_image_repo}"
write_compose "${bad_image_repo}" "name: aegisops-opensearch
services:
  opensearch:
    image: nginx:1.27.0
    volumes:
      - /srv/aegisops/opensearch-data-placeholder:/usr/share/opensearch/data
  dashboards:
    image: opensearchproject/opensearch-dashboards:2.19.0
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${bad_image_repo}" "must pin opensearchproject/opensearch"

missing_dashboards_repo="${workdir}/missing-dashboards"
create_repo "${missing_dashboards_repo}"
write_compose "${missing_dashboards_repo}" "name: aegisops-opensearch
services:
  opensearch:
    image: opensearchproject/opensearch:2.19.0
    volumes:
      - /srv/aegisops/opensearch-data-placeholder:/usr/share/opensearch/data
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${missing_dashboards_repo}" "must define a dashboards service"

dashboards_ports_repo="${workdir}/dashboards-ports"
create_repo "${dashboards_ports_repo}"
write_compose "${dashboards_ports_repo}" "name: aegisops-opensearch
services:
  opensearch:
    image: opensearchproject/opensearch:2.19.0
    volumes:
      - /srv/aegisops/opensearch-data-placeholder:/usr/share/opensearch/data
  dashboards:
    image: opensearchproject/opensearch-dashboards:2.19.0
    ports:
      - 5601:5601
    # skeleton only; not production-ready until approved runtime settings are supplied"
assert_fails_with "${dashboards_ports_repo}" "must not publish Dashboards directly with ports"

echo "verify-opensearch-compose-skeleton tests passed"
