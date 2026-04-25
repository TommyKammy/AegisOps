#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
preflight="${repo_root}/scripts/verify-single-customer-install-preflight.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"
macos_home_fragment='/'"Users"'/'
linux_home_fragment='/'"home"'/'
output_leak_pattern="postgresql://|reviewed-proxy-secret|admin-bootstrap|break-glass-token|ingress-tls-key|${macos_home_fragment}|${linux_home_fragment}"
failure_leak_pattern="postgresql://|super-secret|private-key-material|${macos_home_fragment}|${linux_home_fragment}"

write_valid_env() {
  local path="$1"

  cat > "${path}" <<'EOF'
AEGISOPS_CONTROL_PLANE_HOST=0.0.0.0
AEGISOPS_CONTROL_PLANE_PORT=8080
AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=
AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE=/run/aegisops-secrets/control-plane-postgres-dsn
AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot
AEGISOPS_CONTROL_PLANE_LOG_LEVEL=INFO
AEGISOPS_FIRST_BOOT_PROXY_PORT=8443
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE=/run/aegisops-secrets/wazuh-shared-secret
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE=/run/aegisops-secrets/wazuh-reverse-proxy-secret
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS=172.20.0.10/32
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE=/run/aegisops-secrets/protected-surface-reverse-proxy-secret
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS=172.20.0.10/32
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT=svc-aegisops-proxy-control-plane
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER=authentik
AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE=/run/aegisops-secrets/admin-bootstrap-token
AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_OPENBAO_PATH=
AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE=/run/aegisops-secrets/break-glass-token
AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_OPENBAO_PATH=
AEGISOPS_OPENBAO_ADDRESS=
AEGISOPS_OPENBAO_TOKEN=
AEGISOPS_OPENBAO_TOKEN_FILE=
AEGISOPS_OPENBAO_TOKEN_OPENBAO_PATH=
AEGISOPS_OPENBAO_KV_MOUNT=secret
AEGISOPS_INGRESS_TLS_CERT_CHAIN_FILE=/run/aegisops-secrets/ingress-tls-chain.pem
AEGISOPS_INGRESS_TLS_CERT_CHAIN_OPENBAO_PATH=
AEGISOPS_INGRESS_TLS_PRIVATE_KEY_FILE=/run/aegisops-secrets/ingress-tls-key.pem
AEGISOPS_INGRESS_TLS_PRIVATE_KEY_OPENBAO_PATH=
AEGISOPS_INGRESS_TLS_CERT_CUSTODY_OWNER=it-operations
AEGISOPS_INGRESS_TLS_PRIVATE_KEY_CUSTODIAN=security-operations
AEGISOPS_INGRESS_TLS_EXPIRY_REVIEW_HORIZON=30d
AEGISOPS_INGRESS_TLS_RELOAD_EVIDENCE_REF=evidence/proxy-tls-reload.md
AEGISOPS_INGRESS_APPROVED_PROXY_ARTIFACT_REVISION=repository-revision
AEGISOPS_INGRESS_TRUSTED_HEADER_NORMALIZATION=approved-reverse-proxy-only
AEGISOPS_INSTALL_STORAGE_ROOT=/srv/aegisops/runtime
AEGISOPS_INSTALL_BACKUP_ROOT=/srv/aegisops-backup/runtime
AEGISOPS_INSTALL_POSTGRES_DATA_PATH=/srv/aegisops/postgres-data
AEGISOPS_INSTALL_OPENSEARCH_DATA_PATH=/srv/aegisops/opensearch-data
AEGISOPS_INSTALL_N8N_DATA_PATH=/srv/aegisops/n8n-data
AEGISOPS_INSTALL_POSTGRES_BACKUP_PATH=/srv/aegisops-backup/postgres-backups
AEGISOPS_INSTALL_OPENSEARCH_BACKUP_PATH=/srv/aegisops-backup/opensearch-snapshots
AEGISOPS_INSTALL_N8N_BACKUP_PATH=/srv/aegisops-backup/n8n-backups
AEGISOPS_INSTALL_RESTORE_TARGET_ENVIRONMENT=restore-rehearsal
AEGISOPS_INSTALL_BACKUP_CUSTODY_OWNER=it-operations
AEGISOPS_INSTALL_RESTORE_DRY_RUN_EVIDENCE_REF=evidence/restore-dry-run.md
AEGISOPS_INSTALL_RELEASE_IDENTIFIER=aegisops-single-customer-repository-revision
AEGISOPS_INSTALL_REPOSITORY_REVISION=repository-revision
AEGISOPS_INSTALL_REVIEWED_MIGRATION_REVISION=repository-revision
AEGISOPS_INSTALL_REQUIRED_MIGRATION_SET=0001_control_plane_schema_skeleton.sql
AEGISOPS_INSTALL_MIGRATION_BOOTSTRAP_MODE=forward-reviewed-only
AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT=platform-admin@example.invalid
AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY=platform-admin@example.invalid
AEGISOPS_SMOKE_READONLY_SUBJECT=analyst@example.invalid
AEGISOPS_SMOKE_READONLY_IDENTITY=analyst@example.invalid
AEGISOPS_SMOKE_READONLY_ROLE=analyst
AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID=case-rehearsal-001
AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE=notify_identity_owner
AEGISOPS_SMOKE_APPROVER_OWNER=approver@example.invalid
AEGISOPS_INSTALL_PHASE37_CUSTOMER_LIKE_PREFLIGHT_REF=evidence/customer-like-preflight.md
AEGISOPS_INSTALL_PHASE37_RECORD_CHAIN_REF=evidence/record-chain.md
AEGISOPS_INSTALL_PHASE37_RUNTIME_SMOKE_REF=evidence/runtime-smoke/manifest.md
AEGISOPS_INSTALL_RESTORE_ROLLBACK_UPGRADE_REF=evidence/restore-rollback-upgrade.md
AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=
AEGISOPS_CONTROL_PLANE_N8N_BASE_URL=
AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL=
AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL=
EOF
}

assert_passes() {
  local env_path="$1"

  if ! bash "${preflight}" --env-file "${env_path}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected install preflight to pass for ${env_path}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi

  if grep -Eq "${output_leak_pattern}" "${pass_stdout}" "${pass_stderr}"; then
    echo "Install preflight output must not leak secret material or workstation-local paths" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local env_path="$1"
  local expected="$2"

  if bash "${preflight}" --env-file "${env_path}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected install preflight to fail for ${env_path}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi

  if grep -Eq "${failure_leak_pattern}" "${fail_stdout}" "${fail_stderr}"; then
    echo "Failure output must stay redacted and path-hygienic" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

copy_env() {
  local source="$1"
  local target="$2"
  cp "${source}" "${target}"
}

valid_env="${workdir}/valid.env"
write_valid_env "${valid_env}"
assert_passes "${valid_env}"

missing_env="${workdir}/missing-env.env"
copy_env "${valid_env}" "${missing_env}"
perl -0pi -e 's/^AEGISOPS_CONTROL_PLANE_BOOT_MODE=.*\n//m' "${missing_env}"
assert_fails_with "${missing_env}" "Missing required install preflight input: AEGISOPS_CONTROL_PLANE_BOOT_MODE"

placeholder_env="${workdir}/placeholder-env.env"
copy_env "${valid_env}" "${placeholder_env}"
perl -0pi -e 's/^AEGISOPS_INSTALL_REPOSITORY_REVISION=.*$/AEGISOPS_INSTALL_REPOSITORY_REVISION=<repository-revision>/m' "${placeholder_env}"
assert_fails_with "${placeholder_env}" "Invalid install preflight input: AEGISOPS_INSTALL_REPOSITORY_REVISION"

direct_secret_env="${workdir}/direct-secret.env"
copy_env "${valid_env}" "${direct_secret_env}"
perl -0pi -e 's|^AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=.*$|AEGISOPS_CONTROL_PLANE_POSTGRES_DSN=postgresql://super-secret@postgres:5432/aegisops|m' "${direct_secret_env}"
assert_fails_with "${direct_secret_env}" "Direct secret value is not allowed in install preflight input: AEGISOPS_CONTROL_PLANE_POSTGRES_DSN"

missing_secret_ref_env="${workdir}/missing-secret-ref.env"
copy_env "${valid_env}" "${missing_secret_ref_env}"
perl -0pi -e 's/^AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE=.*\n//m' "${missing_secret_ref_env}"
assert_fails_with "${missing_secret_ref_env}" "Missing required secret reference: Wazuh ingest shared secret"

missing_cert_env="${workdir}/missing-cert.env"
copy_env "${valid_env}" "${missing_cert_env}"
perl -0pi -e 's/^AEGISOPS_INGRESS_TLS_CERT_CHAIN_FILE=.*\n//m' "${missing_cert_env}"
assert_fails_with "${missing_cert_env}" "Missing required secret reference: ingress TLS certificate chain"

proxy_drift_env="${workdir}/proxy-drift.env"
copy_env "${valid_env}" "${proxy_drift_env}"
perl -0pi -e 's/^AEGISOPS_INGRESS_TRUSTED_HEADER_NORMALIZATION=.*$/AEGISOPS_INGRESS_TRUSTED_HEADER_NORMALIZATION=raw-x-forwarded-for/m' "${proxy_drift_env}"
assert_fails_with "${proxy_drift_env}" "Invalid install preflight input: AEGISOPS_INGRESS_TRUSTED_HEADER_NORMALIZATION"

storage_drift_env="${workdir}/storage-drift.env"
copy_env "${valid_env}" "${storage_drift_env}"
perl -0pi -e 's|^AEGISOPS_INSTALL_BACKUP_ROOT=.*$|AEGISOPS_INSTALL_BACKUP_ROOT=/srv/aegisops/runtime/backups|m' "${storage_drift_env}"
assert_fails_with "${storage_drift_env}" "Unsafe storage path contract: AEGISOPS_INSTALL_BACKUP_ROOT"

restore_target_env="${workdir}/restore-target.env"
copy_env "${valid_env}" "${restore_target_env}"
perl -0pi -e 's/^AEGISOPS_INSTALL_RESTORE_TARGET_ENVIRONMENT=.*$/AEGISOPS_INSTALL_RESTORE_TARGET_ENVIRONMENT=live/m' "${restore_target_env}"
assert_fails_with "${restore_target_env}" "Unsafe restore target contract: AEGISOPS_INSTALL_RESTORE_TARGET_ENVIRONMENT"

migration_drift_env="${workdir}/migration-drift.env"
copy_env "${valid_env}" "${migration_drift_env}"
perl -0pi -e 's/^AEGISOPS_INSTALL_MIGRATION_BOOTSTRAP_MODE=.*$/AEGISOPS_INSTALL_MIGRATION_BOOTSTRAP_MODE=recreate-schema/m' "${migration_drift_env}"
assert_fails_with "${migration_drift_env}" "Invalid migration bootstrap contract: AEGISOPS_INSTALL_MIGRATION_BOOTSTRAP_MODE"

invalid_release_env="${workdir}/invalid-release.env"
copy_env "${valid_env}" "${invalid_release_env}"
perl -0pi -e 's/^AEGISOPS_INSTALL_RELEASE_IDENTIFIER=.*$/AEGISOPS_INSTALL_RELEASE_IDENTIFIER=customer-release/m' "${invalid_release_env}"
assert_fails_with "${invalid_release_env}" "Invalid release identifier contract: AEGISOPS_INSTALL_RELEASE_IDENTIFIER"

invalid_smoke_readonly_env="${workdir}/invalid-smoke-readonly.env"
copy_env "${valid_env}" "${invalid_smoke_readonly_env}"
perl -0pi -e 's/^AEGISOPS_SMOKE_READONLY_ROLE=.*$/AEGISOPS_SMOKE_READONLY_ROLE=owner/m' "${invalid_smoke_readonly_env}"
assert_fails_with "${invalid_smoke_readonly_env}" "Invalid smoke read-only role: AEGISOPS_SMOKE_READONLY_ROLE"

smoke_drift_env="${workdir}/smoke-drift.env"
copy_env "${valid_env}" "${smoke_drift_env}"
perl -0pi -e 's/^AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE=.*$/AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE=disable_account/m' "${smoke_drift_env}"
assert_fails_with "${smoke_drift_env}" "Invalid smoke low-risk action type: AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE"

optional_extension_env="${workdir}/optional-extension.env"
copy_env "${valid_env}" "${optional_extension_env}"
perl -0pi -e 's|^AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=.*$|AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=http://opensearch:9200|m' "${optional_extension_env}"
assert_fails_with "${optional_extension_env}" "Optional extension must remain non-blocking for install preflight: AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL"

echo "Single-customer install preflight negative and valid fixtures passed."
