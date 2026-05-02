#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-control-plane-runtime-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_runtime_repo() {
  local target="$1"
  mkdir -p "${target}/control-plane/aegisops_control_plane"
  mkdir -p "${target}/control-plane/aegisops/control_plane/adapters"
  mkdir -p "${target}/control-plane/tests"
  mkdir -p "${target}/control-plane/config"

  cat <<'EOF' > "${target}/control-plane/README.md"
# Fixture
EOF
  cat <<'EOF' > "${target}/control-plane/main.py"
from aegisops.control_plane.service import build_runtime_service
EOF
  cat <<'EOF' > "${target}/control-plane/aegisops_control_plane/__init__.py"
"""Fixture package."""
EOF
  cat <<'EOF' > "${target}/control-plane/aegisops/control_plane/config.py"
class RuntimeConfig:
    pass
EOF
  cat <<'EOF' > "${target}/control-plane/aegisops/control_plane/service.py"
class AegisOpsControlPlaneService:
    pass
EOF
  cat <<'EOF' > "${target}/control-plane/aegisops/control_plane/adapters/__init__.py"
"""Fixture adapters."""
EOF
  : > "${target}/control-plane/aegisops/control_plane/adapters/opensearch.py"
  : > "${target}/control-plane/aegisops/control_plane/adapters/postgres.py"
  : > "${target}/control-plane/aegisops/control_plane/adapters/n8n.py"
  : > "${target}/control-plane/tests/test_runtime_skeleton.py"
  cat <<'EOF' > "${target}/control-plane/config/local.env.sample"
AEGISOPS_CONTROL_PLANE_HOST=127.0.0.1
AEGISOPS_CONTROL_PLANE_PORT=8080
AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=<set-me>
AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE=
AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=<set-me>
AEGISOPS_CONTROL_PLANE_N8N_BASE_URL=<set-me>
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET=
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE=
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET=
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE=
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS=
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET=
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE=
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS=
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT=
AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN=
AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE=
AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN=
AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE=
AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH=
AEGISOPS_OPENBAO_ADDRESS=
AEGISOPS_OPENBAO_TOKEN=
AEGISOPS_OPENBAO_TOKEN_FILE=
AEGISOPS_OPENBAO_KV_MOUNT=secret
EOF
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

passing_repo="${workdir}/passing"
mkdir -p "${passing_repo}"
create_runtime_repo "${passing_repo}"
assert_passes "${passing_repo}"

failing_repo="${workdir}/failing"
mkdir -p "${failing_repo}"
create_runtime_repo "${failing_repo}"
rm "${failing_repo}/control-plane/aegisops/control_plane/adapters/n8n.py"
assert_fails_with "${failing_repo}" "Missing control-plane runtime skeleton file: control-plane/aegisops/control_plane/adapters/n8n.py"

unexpected_env_repo="${workdir}/unexpected-env"
mkdir -p "${unexpected_env_repo}"
create_runtime_repo "${unexpected_env_repo}"
cat <<'EOF' >> "${unexpected_env_repo}/control-plane/config/local.env.sample"
AEGISOPS_CONTROL_PLANE_SECRET_TOKEN=real-secret
EOF
assert_fails_with "${unexpected_env_repo}" "Unexpected control-plane local sample setting: AEGISOPS_CONTROL_PLANE_SECRET_TOKEN=real-secret"

duplicate_env_repo="${workdir}/duplicate-env"
mkdir -p "${duplicate_env_repo}"
create_runtime_repo "${duplicate_env_repo}"
cat <<'EOF' >> "${duplicate_env_repo}/control-plane/config/local.env.sample"
AEGISOPS_CONTROL_PLANE_PORT=8080
EOF
assert_fails_with "${duplicate_env_repo}" "Control-plane local env sample must define exactly 29 non-comment settings."

echo "verify-control-plane-runtime-skeleton tests passed"
