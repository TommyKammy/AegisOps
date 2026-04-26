#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
gate="${repo_root}/scripts/run-phase-37-runtime-smoke-gate.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

write_secret() {
  local path="$1"

  mkdir -p "$(dirname "${path}")"
  printf 'reviewed-proxy-secret\n' > "${path}"
}

write_valid_env() {
  local path="$1"
  local secret_path="$2"

  cat > "${path}" <<EOF
AEGISOPS_CONTROL_PLANE_HOST=0.0.0.0
AEGISOPS_CONTROL_PLANE_PORT=8080
AEGISOPS_CONTROL_PLANE_POSTGRES_DSN_FILE=/run/aegisops-secrets/control-plane-postgres-dsn
AEGISOPS_CONTROL_PLANE_BOOT_MODE=first-boot
AEGISOPS_CONTROL_PLANE_LOG_LEVEL=INFO
AEGISOPS_FIRST_BOOT_PROXY_PORT=18080
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_SHARED_SECRET_FILE=/run/aegisops-secrets/wazuh-shared-secret
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_REVERSE_PROXY_SECRET_FILE=/run/aegisops-secrets/wazuh-reverse-proxy-secret
AEGISOPS_CONTROL_PLANE_WAZUH_INGEST_TRUSTED_PROXY_CIDRS=172.20.0.10/32
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE=${secret_path}
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_TRUSTED_PROXY_CIDRS=172.20.0.10/32
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT=svc-aegisops-proxy-control-plane
AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER=authentik
AEGISOPS_CONTROL_PLANE_ADMIN_BOOTSTRAP_TOKEN_FILE=/run/aegisops-secrets/admin-bootstrap-token
AEGISOPS_CONTROL_PLANE_BREAK_GLASS_TOKEN_FILE=/run/aegisops-secrets/break-glass-token
AEGISOPS_CONTROL_PLANE_OPENSEARCH_URL=
AEGISOPS_CONTROL_PLANE_N8N_BASE_URL=
AEGISOPS_CONTROL_PLANE_SHUFFLE_BASE_URL=
AEGISOPS_CONTROL_PLANE_ISOLATED_EXECUTOR_BASE_URL=
AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT=platform-admin@example.invalid
AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY=platform-admin@example.invalid
AEGISOPS_SMOKE_READONLY_SUBJECT=analyst@example.invalid
AEGISOPS_SMOKE_READONLY_IDENTITY=analyst@example.invalid
AEGISOPS_SMOKE_READONLY_ROLE=analyst
AEGISOPS_SMOKE_REVIEWED_ALERT_ID=alert-rehearsal-001
AEGISOPS_SMOKE_REVIEWED_CASE_ID=case-rehearsal-001
AEGISOPS_SMOKE_REVIEWED_ACTION_REQUEST_ID=action-request-rehearsal-001
AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID=case-rehearsal-001
AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE=notify_identity_owner
AEGISOPS_SMOKE_APPROVER_OWNER=approver@example.invalid
EOF
}

write_fake_bin() {
  local bin_dir="$1"
  local curl_log="$2"

  mkdir -p "${bin_dir}"

  cat > "${bin_dir}/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
if [[ "$*" == *" ps"* ]]; then
  printf 'NAME STATUS\ncontrol-plane running\npostgres running\nreverse-proxy running\n'
  exit 0
fi
if [[ "$*" == *" logs"* ]]; then
  printf 'control-plane ready\nreverse-proxy admitted\n'
  exit 0
fi
printf 'unexpected docker invocation: %s\n' "$*" >&2
exit 1
EOF

  cat > "${bin_dir}/curl" <<EOF
#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' "\$*" >> "${curl_log}"
target="\${@: -1}"
if [[ "\${AEGISOPS_FAKE_CURL_FAIL_RUNTIME:-}" == "1" && "\${target}" == *"/runtime" ]]; then
  printf 'runtime refused\n' >&2
  exit 22
fi
case "\${target}" in
  *"/healthz")
    printf '{"status":"ok"}\n'
    ;;
  *"/readyz")
    printf '{"status":"ready","persistence_mode":"postgres"}\n'
    ;;
  *"/runtime")
    printf '{"service_name":"aegisops-control-plane","boot_mode":"first-boot","deployment_profile":"single-customer"}\n'
    ;;
  *"/inspect-analyst-queue"*)
    printf '{"queue_name":"analyst_review","records":[{"alert_id":"alert-rehearsal-001","case_id":"case-rehearsal-001","review_state":"degraded"}]}\n'
    ;;
  *"/operator/queue"*)
    printf '{"queue_name":"analyst_review","records":[{"alert_id":"alert-rehearsal-001","case_id":"case-rehearsal-001","review_state":"degraded"}]}\n'
    ;;
  *"family=alerts")
    printf '{"family":"alerts","records":[]}\n'
    ;;
  *"/inspect-alert-detail?alert_id=alert-rehearsal-001")
    printf '{"alert_id":"alert-rehearsal-001","case_id":"case-rehearsal-001","review_state":"degraded"}\n'
    ;;
  *"family=cases")
    printf '{"family":"cases","records":[]}\n'
    ;;
  *"/inspect-case-detail?case_id=case-rehearsal-001")
    printf '{"case_id":"case-rehearsal-001","authoritative_state":"open","coordination_mismatch_visible":true}\n'
    ;;
  *"family=action_requests")
    printf '{"family":"action_requests","records":[]}\n'
    ;;
  *"/inspect-action-review?action_request_id=action-request-rehearsal-001")
    printf '{"action_request_id":"action-request-rehearsal-001","case_id":"case-rehearsal-001","review_state":"pending"}\n'
    ;;
  *"/inspect-advisory-output?family=case&record_id=case-rehearsal-001")
    printf '{"family":"case","record_id":"case-rehearsal-001","authority":"subordinate_advisory"}\n'
    ;;
  *"/inspect-reconciliation-status")
    printf '{"status":"readable"}\n'
    ;;
  *)
    printf 'unexpected curl target: %s\n' "\${target}" >&2
    exit 1
    ;;
esac
EOF

  chmod +x "${bin_dir}/docker" "${bin_dir}/curl"
}

assert_passes() {
  local env_path="$1"
  local evidence_dir="$2"
  local bin_dir="$3"

  if ! PATH="${bin_dir}:${PATH}" bash "${gate}" --env-file "${env_path}" --evidence-dir "${evidence_dir}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected smoke gate to pass for ${env_path}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local env_path="$1"
  local evidence_dir="$2"
  local bin_dir="$3"
  local expected="$4"

  if PATH="${bin_dir}:${PATH}" bash "${gate}" --env-file "${env_path}" --evidence-dir "${evidence_dir}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected smoke gate to fail for ${env_path}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

bin_dir="${workdir}/bin"
curl_log="${workdir}/curl.log"
write_fake_bin "${bin_dir}" "${curl_log}"

secret_path="${workdir}/secrets/proxy-secret"
write_secret "${secret_path}"

valid_env="${workdir}/valid.env"
write_valid_env "${valid_env}" "${secret_path}"
valid_evidence="${workdir}/evidence-pass"
assert_passes "${valid_env}" "${valid_evidence}" "${bin_dir}"

if [[ ! -f "${valid_evidence}/manifest.md" ]]; then
  echo "Expected smoke evidence manifest to be written" >&2
  exit 1
fi

if ! grep -F "Phase 37 Runtime Smoke Gate Evidence" "${valid_evidence}/manifest.md" >/dev/null; then
  echo "Expected evidence manifest heading" >&2
  exit 1
fi

if grep -F "evidence/" "${valid_evidence}/manifest.md" >/dev/null; then
  echo "Evidence manifest must list artifact paths relative to the manifest directory" >&2
  exit 1
fi

if ! grep -F -- "- Protected runtime inspection: runtime.json" "${valid_evidence}/manifest.md" >/dev/null; then
  echo "Expected runtime artifact path to be relative to the manifest directory" >&2
  exit 1
fi

if ! grep -F -- "- Protected operator-console ingress: inspect-analyst-queue.json, operator-queue.json" "${valid_evidence}/manifest.md" >/dev/null; then
  echo "Expected operator-console ingress artifacts in the manifest" >&2
  exit 1
fi

if ! grep -F -- "- Protected detail ingress: inspect-alert-detail.json, inspect-case-detail.json, inspect-action-review.json, inspect-advisory-output-case.json" "${valid_evidence}/manifest.md" >/dev/null; then
  echo "Expected protected detail ingress artifacts in the manifest" >&2
  exit 1
fi

actual_curl_count="$(wc -l < "${curl_log}" | tr -d '[:space:]')"
if [[ "${actual_curl_count}" != "13" ]]; then
  echo "Expected 13 curl smoke calls, saw ${actual_curl_count}" >&2
  cat "${curl_log}" >&2
  exit 1
fi

if grep -v -- "-fsS --connect-timeout 5 --max-time 20" "${curl_log}" >/dev/null; then
  echo "Expected every curl smoke call to use bounded timeout flags" >&2
  cat "${curl_log}" >&2
  exit 1
fi

if grep -F "/operator/create-reviewed-action-request" "${curl_log}" >/dev/null; then
  echo "Smoke gate must not create reviewed action requests" >&2
  exit 1
fi

missing_endpoint_env="${workdir}/missing-endpoint.env"
write_valid_env "${missing_endpoint_env}" "${secret_path}"
perl -0pi -e 's/^AEGISOPS_FIRST_BOOT_PROXY_PORT=.*\n//m' "${missing_endpoint_env}"
assert_fails_with "${missing_endpoint_env}" "${workdir}/evidence-missing-endpoint" "${bin_dir}" "Missing required smoke input: AEGISOPS_FIRST_BOOT_PROXY_PORT"

missing_auth_env="${workdir}/missing-auth.env"
write_valid_env "${missing_auth_env}" "${secret_path}"
perl -0pi -e 's/^AEGISOPS_SMOKE_READONLY_IDENTITY=.*\n//m' "${missing_auth_env}"
assert_fails_with "${missing_auth_env}" "${workdir}/evidence-missing-auth" "${bin_dir}" "Missing required smoke input: AEGISOPS_SMOKE_READONLY_IDENTITY"

missing_detail_env="${workdir}/missing-detail.env"
write_valid_env "${missing_detail_env}" "${secret_path}"
perl -0pi -e 's/^AEGISOPS_SMOKE_REVIEWED_ACTION_REQUEST_ID=.*\n//m' "${missing_detail_env}"
assert_fails_with "${missing_detail_env}" "${workdir}/evidence-missing-detail" "${bin_dir}" "Missing required smoke input: AEGISOPS_SMOKE_REVIEWED_ACTION_REQUEST_ID"

invalid_action_type_env="${workdir}/invalid-action-type.env"
write_valid_env "${invalid_action_type_env}" "${secret_path}"
perl -0pi -e 's/^AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE=.*$/AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE=disable_account/m' "${invalid_action_type_env}"
assert_fails_with "${invalid_action_type_env}" "${workdir}/evidence-invalid-action-type" "${bin_dir}" "Invalid smoke low-risk action type: AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE must be notify_identity_owner"

missing_secret_file_env="${workdir}/missing-secret-file.env"
write_valid_env "${missing_secret_file_env}" "${workdir}/secrets/missing-proxy-secret"
assert_fails_with "${missing_secret_file_env}" "${workdir}/evidence-missing-secret-file" "${bin_dir}" "Missing protected surface proxy secret file:"

if AEGISOPS_FAKE_CURL_FAIL_RUNTIME=1 PATH="${bin_dir}:${PATH}" bash "${gate}" --env-file "${valid_env}" --evidence-dir "${workdir}/evidence-runtime-fail" >"${fail_stdout}" 2>"${fail_stderr}"; then
  echo "Expected smoke gate to fail when protected runtime inspection is refused" >&2
  exit 1
fi

if ! grep -F "Smoke step failed: runtime" "${fail_stderr}" >/dev/null; then
  echo "Expected protected runtime refusal to be identified" >&2
  cat "${fail_stderr}" >&2
  exit 1
fi

echo "run-phase-37-runtime-smoke-gate tests passed"
