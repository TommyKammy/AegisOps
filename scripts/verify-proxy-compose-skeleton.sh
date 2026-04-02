#!/usr/bin/env bash

set -euo pipefail

default_repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${default_repo_root}}"
compose_path="${repo_root}/proxy/docker-compose.yml"
nginx_conf_path="${repo_root}/proxy/nginx/nginx.conf"
placeholder_conf_path="${repo_root}/proxy/nginx/conf.d-placeholder/default.conf"

if [[ ! -f "${compose_path}" ]]; then
  echo "Missing proxy compose skeleton: ${compose_path}" >&2
  exit 1
fi

if [[ ! -f "${nginx_conf_path}" ]]; then
  echo "Missing proxy nginx skeleton config: ${nginx_conf_path}" >&2
  exit 1
fi

if [[ ! -f "${placeholder_conf_path}" ]]; then
  echo "Missing proxy placeholder route config: ${placeholder_conf_path}" >&2
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

extract_proxy_block() {
  awk '
    /^  proxy:[[:space:]]*(#.*)?$/ { in_proxy = 1 }
    in_proxy && /^[^[:space:]]/ { exit }
    in_proxy && /^  [a-z0-9_-]+:[[:space:]]*(#.*)?$/ && $0 !~ /^  proxy:[[:space:]]*(#.*)?$/ { exit }
    in_proxy { print }
  ' "${compose_path}"
}

require_proxy_pattern() {
  local pattern="$1"
  local message="$2"

  if ! extract_proxy_block | grep -En "${pattern}" >/dev/null; then
    echo "${message}" >&2
    exit 1
  fi
}

require_fixed_string "${compose_path}" "name: aegisops-proxy"
require_fixed_string "${compose_path}" "services:"
require_fixed_string "${compose_path}" "  proxy:"
require_proxy_pattern '^    image: nginx:[^[:space:]]+$' \
  "Proxy compose skeleton must pin nginx to an explicit version tag."

if grep -En '^    image: .*:latest$' "${compose_path}" >/dev/null; then
  echo "Proxy compose skeleton must not use the latest tag." >&2
  exit 1
fi

if grep -En '^[[:space:]]*container_name:' "${compose_path}" >/dev/null; then
  echo "Proxy compose skeleton must not hard-code container_name." >&2
  exit 1
fi

require_proxy_pattern '^    volumes:$' \
  "Proxy compose skeleton must declare placeholder-safe mount references."
require_proxy_pattern '^      - \./nginx/nginx\.conf:/etc/nginx/nginx\.conf:ro$' \
  "Proxy compose skeleton must mount the tracked nginx base config read-only."
require_proxy_pattern '^      - \./nginx/conf\.d-placeholder:/etc/nginx/conf\.d:ro$' \
  "Proxy compose skeleton must mount the tracked placeholder route config directory read-only."
require_proxy_pattern '^      - /srv/aegisops/proxy-certs-placeholder:/etc/nginx/certs:ro$' \
  "Proxy compose skeleton must use the explicit placeholder-safe certificate mount."
require_pattern "${compose_path}" 'approved ingress layer for user-facing UI access only' \
  "Proxy compose skeleton must limit its role to the approved ingress boundary."
require_pattern "${compose_path}" 'backend UIs remain internal behind this proxy' \
  "Proxy compose skeleton must state that backend UIs remain internal behind the proxy."
require_pattern "${compose_path}" 'route implementation, live certificates, and public publication remain out of scope here' \
  "Proxy compose skeleton must explicitly defer live routes, certificates, and public publication."
require_pattern "${compose_path}" 'skeleton only' \
  "Proxy compose skeleton must state that it is a skeleton only."
require_pattern "${compose_path}" 'not production-ready' \
  "Proxy compose skeleton must state that it is not production-ready."

if extract_proxy_block | awk '
  BEGIN { has_ports = 0 }
  $0 ~ /^    ["'"'"']?ports["'"'"']?:[[:space:]]*(#.*)?$/ { has_ports = 1 }
  END { exit(has_ports ? 0 : 1) }
' ; then
  echo "Proxy compose skeleton must not publish ports before approved runtime exposure is supplied." >&2
  exit 1
fi

require_fixed_string "${nginx_conf_path}" "http {"
require_pattern "${nginx_conf_path}" 'include /etc/nginx/conf\.d/\*\.conf;' \
  "Proxy nginx skeleton config must load the placeholder route directory."

require_pattern "${placeholder_conf_path}" '^# Placeholder ingress config only\.$' \
  "Proxy placeholder route config must declare itself as a placeholder."
require_pattern "${placeholder_conf_path}" '^  return 503;$' \
  "Proxy placeholder route config must fail closed with a 503 placeholder response."

if grep -En 'proxy_pass[[:space:]]+' "${placeholder_conf_path}" >/dev/null; then
  echo "Proxy placeholder route config must not define live upstream routes yet." >&2
  exit 1
fi

if grep -En '(ssl_certificate|ssl_certificate_key|/etc/letsencrypt|acme\.json|fullchain\.pem|privkey\.pem)' "${placeholder_conf_path}" >/dev/null; then
  echo "Proxy placeholder route config must not reference live certificate material." >&2
  exit 1
fi

echo "Proxy compose skeleton matches the approved placeholder-safe ingress contract."
