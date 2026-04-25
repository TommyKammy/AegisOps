#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-customer-like-rehearsal-environment.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_valid_env() {
  local path="$1"

  cat > "${path}" <<'EOF'
AEGISOPS_CONTROL_PLANE_HOST=0.0.0.0
AEGISOPS_CONTROL_PLANE_PORT=8080
AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE=/run/aegisops-secrets/control-plane-postgres-dsn
AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot
AEGISOPS_CONTROL_PLANE_LOG_LEVEL=INFO
AEGISOPS_FIRST_BOOT_PROXY_PORT=8080
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE=/run/aegisops-secrets/wazuh-shared-secret
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE=/run/aegisops-secrets/wazuh-reverse-proxy-secret
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS=172.20.0.10/32
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE=/run/aegisops-secrets/protected-surface-reverse-proxy-secret
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS=172.20.0.10/32
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT=svc-aegisops-proxy-control-plane
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER=authentik
AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE=/run/aegisops-secrets/admin-bootstrap-token
AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE=/run/aegisops-secrets/break-glass-token
AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=
AEGISOPS_CONTROL_PLANE_N8N_BASE_URL=
AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL=
AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL=
EOF
}

assert_passes() {
  local env_path="$1"

  if ! bash "${verifier}" --env-file "${env_path}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${env_path}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local env_path="$1"
  local expected="$2"

  if bash "${verifier}" --env-file "${env_path}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${env_path}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

assert_repo_fails_with() {
  local repo_path="$1"
  local expected="$2"

  if bash "${verifier}" "${repo_path}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${repo_path}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_env="${workdir}/valid.env"
write_valid_env "${valid_env}"
assert_passes "${valid_env}"

missing_secret_env="${workdir}/missing-secret.env"
write_valid_env "${missing_secret_env}"
perl -0pi -e 's/^AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE=.*\n//m' "${missing_secret_env}"
assert_fails_with "${missing_secret_env}" "Missing required rehearsal input binding: Wazuh ingest shared secret"

placeholder_env="${workdir}/placeholder.env"
write_valid_env "${placeholder_env}"
perl -0pi -e 's|^AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE=.*$|AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=postgresql://<user>:<password>@postgres:5432/aegisops_control_plane|m' "${placeholder_env}"
assert_fails_with "${placeholder_env}" "Placeholder rehearsal input is not allowed: AEGISOPS_CONTROL_PLANE_POSTGRES_DSN"

guessed_env="${workdir}/guessed.env"
write_valid_env "${guessed_env}"
perl -0pi -e 's|^AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE=.*$|AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=postgresql://guessed-user:reviewed-password@postgres:5432/aegisops_control_plane|m' "${guessed_env}"
assert_fails_with "${guessed_env}" "Placeholder rehearsal input is not allowed: AEGISOPS_CONTROL_PLANE_POSTGRES_DSN"

unsigned_env="${workdir}/unsigned.env"
write_valid_env "${unsigned_env}"
perl -0pi -e 's|^AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE=.*$|AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE=/run/aegisops-secrets/unsigned-wazuh-shared-secret|m' "${unsigned_env}"
assert_fails_with "${unsigned_env}" "Placeholder rehearsal input is not allowed: AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE"

wrong_boot_mode_env="${workdir}/wrong-boot-mode.env"
write_valid_env "${wrong_boot_mode_env}"
perl -0pi -e 's/^AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot$/AEGISOPS_CONTROL_PLANE_BOOT_MODE=single-customer/m' "${wrong_boot_mode_env}"
assert_fails_with "${wrong_boot_mode_env}" "Invalid rehearsal boot mode: AEGISOPS_CONTROL_PLANE_BOOT_MODE must be first-boot"

openbao_env="${workdir}/openbao.env"
write_valid_env "${openbao_env}"
perl -0pi -e 's/^AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE=.*\n/AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH=kv\/aegisops\/break-glass-token\n/m' "${openbao_env}"
assert_fails_with "${openbao_env}" "Missing required rehearsal input: AEGISOPS_OPENBAO_ADDRESS"

path_hygiene_repo="${workdir}/path-hygiene-repo"
mkdir -p "${path_hygiene_repo}"
cp -R "${repo_root}/docs" "${path_hygiene_repo}/docs"
cat >> "${path_hygiene_repo}/docs/deployment/customer-like-rehearsal-environment.md" <<'EOF'

Invalid workstation-local example: /Users/example/AegisOps  # publishable-path-hygiene: allowlist fixture
EOF
assert_repo_fails_with "${path_hygiene_repo}" "Forbidden customer-like rehearsal environment statement: workstation-local absolute path detected"

echo "verify-customer-like-rehearsal-environment tests passed"
