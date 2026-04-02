#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-proxy-compose-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/proxy/nginx/conf.d-placeholder"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_fixture() {
  local target="$1"
  local path="$2"
  local content="$3"

  printf '%s\n' "${content}" >"${target}/${path}"
  git -C "${target}" add "${path}"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit -q --allow-empty -m "fixture"
}

write_valid_proxy_files() {
  local target="$1"

  write_fixture "${target}" "proxy/docker-compose.yml" "name: aegisops-proxy
services:
  proxy:
    image: nginx:1.27.0
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d-placeholder:/etc/nginx/conf.d:ro
      - /srv/aegisops/proxy-certs-placeholder:/etc/nginx/certs:ro
    # approved ingress layer for user-facing UI access only
    # backend UIs remain internal behind this proxy; no direct backend ports publication here
    # route implementation, live certificates, and public publication remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
  write_fixture "${target}" "proxy/nginx/nginx.conf" "worker_processes auto;

events {
  worker_connections 1024;
}

http {
  include /etc/nginx/mime.types;
  default_type application/octet-stream;

  sendfile on;
  keepalive_timeout 65;

  include /etc/nginx/conf.d/*.conf;
}"
  write_fixture "${target}" "proxy/nginx/conf.d-placeholder/default.conf" "# Placeholder ingress config only.
# Approved upstream routes, TLS server blocks, and public listeners are added later.
server {
  listen 8080 default_server;
  server_name _;

  return 503;
}"
  commit_fixture "${target}"
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
write_valid_proxy_files "${valid_repo}"
assert_passes "${valid_repo}"

missing_file_repo="${workdir}/missing-file"
create_repo "${missing_file_repo}"
commit_fixture "${missing_file_repo}"
assert_fails_with "${missing_file_repo}" "Missing proxy compose skeleton"

latest_tag_repo="${workdir}/latest-tag"
create_repo "${latest_tag_repo}"
write_valid_proxy_files "${latest_tag_repo}"
write_fixture "${latest_tag_repo}" "proxy/docker-compose.yml" "name: aegisops-proxy
services:
  proxy:
    image: nginx:latest
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d-placeholder:/etc/nginx/conf.d:ro
      - /srv/aegisops/proxy-certs-placeholder:/etc/nginx/certs:ro
    # approved ingress layer for user-facing UI access only
    # backend UIs remain internal behind this proxy; no direct backend ports publication here
    # route implementation, live certificates, and public publication remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
commit_fixture "${latest_tag_repo}"
assert_fails_with "${latest_tag_repo}" "must not use the latest tag"

bad_mount_repo="${workdir}/bad-mount"
create_repo "${bad_mount_repo}"
write_valid_proxy_files "${bad_mount_repo}"
write_fixture "${bad_mount_repo}" "proxy/docker-compose.yml" "name: aegisops-proxy
services:
  proxy:
    image: nginx:1.27.0
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d-placeholder:/etc/nginx/conf.d:ro
      - /etc/letsencrypt:/etc/nginx/certs:ro
    # approved ingress layer for user-facing UI access only
    # backend UIs remain internal behind this proxy; no direct backend ports publication here
    # route implementation, live certificates, and public publication remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
commit_fixture "${bad_mount_repo}"
assert_fails_with "${bad_mount_repo}" "placeholder-safe certificate mount"

ports_repo="${workdir}/ports"
create_repo "${ports_repo}"
write_valid_proxy_files "${ports_repo}"
write_fixture "${ports_repo}" "proxy/docker-compose.yml" "name: aegisops-proxy
services:
  proxy:
    image: nginx:1.27.0
    ports:
      - 443:443
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d-placeholder:/etc/nginx/conf.d:ro
      - /srv/aegisops/proxy-certs-placeholder:/etc/nginx/certs:ro
    # approved ingress layer for user-facing UI access only
    # backend UIs remain internal behind this proxy; no direct backend ports publication here
    # route implementation, live certificates, and public publication remain out of scope here
    # skeleton only; not production-ready until approved runtime settings are supplied"
commit_fixture "${ports_repo}"
assert_fails_with "${ports_repo}" "must not publish ports"

live_route_repo="${workdir}/live-route"
create_repo "${live_route_repo}"
write_valid_proxy_files "${live_route_repo}"
write_fixture "${live_route_repo}" "proxy/nginx/conf.d-placeholder/default.conf" "# Placeholder ingress config only.
server {
  listen 8080 default_server;
  server_name _;

  location / {
    proxy_pass http://dashboards:5601;
  }

  return 503;
}"
commit_fixture "${live_route_repo}"
assert_fails_with "${live_route_repo}" "must not define live upstream routes yet"

live_cert_repo="${workdir}/live-cert"
create_repo "${live_cert_repo}"
write_valid_proxy_files "${live_cert_repo}"
write_fixture "${live_cert_repo}" "proxy/nginx/conf.d-placeholder/default.conf" "# Placeholder ingress config only.
server {
  listen 443 ssl default_server;
  server_name _;
  ssl_certificate /etc/letsencrypt/live/aegisops/fullchain.pem;
  ssl_certificate_key /etc/letsencrypt/live/aegisops/privkey.pem;

  return 503;
}"
commit_fixture "${live_cert_repo}"
assert_fails_with "${live_cert_repo}" "must not reference live certificate material"

echo "verify-proxy-compose-skeleton tests passed"
