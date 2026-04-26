#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat >&2 <<'EOF'
Usage: scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> [--evidence-dir <evidence-dir>]

Runs the bounded Phase 37 runtime smoke gate against the customer-like rehearsal
environment through the reviewed reverse proxy. The gate captures startup status,
readiness, protected runtime reachability, read-only operator sanity, and the
first low-risk action precondition boundary without creating, approving,
dispatching, or reconciling an action request.

Required smoke-only env values in <runtime-env-file>:
  AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT
  AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY
  AEGISOPS_SMOKE_READONLY_SUBJECT
  AEGISOPS_SMOKE_READONLY_IDENTITY
  AEGISOPS_SMOKE_READONLY_ROLE
  AEGISOPS_SMOKE_REVIEWED_ALERT_ID
  AEGISOPS_SMOKE_REVIEWED_CASE_ID
  AEGISOPS_SMOKE_REVIEWED_ACTION_REQUEST_ID
  AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID
  AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE
  AEGISOPS_SMOKE_APPROVER_OWNER
EOF
}

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_file=""
evidence_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file)
      if [[ $# -lt 2 ]]; then
        usage
        exit 2
      fi
      env_file="$2"
      shift 2
      ;;
    --evidence-dir)
      if [[ $# -lt 2 ]]; then
        usage
        exit 2
      fi
      evidence_dir="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      exit 2
      ;;
  esac
done

if [[ -z "${env_file}" ]]; then
  usage
  exit 2
fi

if [[ ! -f "${env_file}" ]]; then
  echo "Missing smoke env file: ${env_file}" >&2
  exit 1
fi

if [[ -z "${evidence_dir}" ]]; then
  evidence_dir="${repo_root}/.codex-supervisor/smoke-evidence/phase-37-$(date -u +%Y%m%dT%H%M%SZ)"
fi

trim() {
  local value="$1"
  value="${value#"${value%%[![:space:]]*}"}"
  value="${value%"${value##*[![:space:]]}"}"
  printf '%s' "${value}"
}

load_env_value() {
  local key="$1"
  local line value

  line="$(grep -E "^${key}=" "${env_file}" | tail -n 1 || true)"
  if [[ -z "${line}" ]]; then
    printf ''
    return
  fi

  value="${line#*=}"
  value="$(trim "${value}")"
  value="${value%\"}"
  value="${value#\"}"
  value="${value%\'}"
  value="${value#\'}"
  printf '%s' "${value}"
}

is_placeholder_value() {
  local value="$1"
  local lowered

  lowered="$(printf '%s' "${value}" | tr '[:upper:]' '[:lower:]')"
  [[ "${value}" == *"<"*">"* ]] || \
    [[ "${lowered}" == *"todo"* ]] || \
    [[ "${lowered}" == *"sample"* ]] || \
    [[ "${lowered}" == *"fake"* ]] || \
    [[ "${lowered}" == *"placeholder"* ]] || \
    [[ "${lowered}" == *"change-me"* ]] || \
    [[ "${lowered}" == *"guess"* ]] || \
    [[ "${lowered}" == *"unsigned"* ]]
}

require_env_value() {
  local key="$1"
  local value

  value="$(load_env_value "${key}")"
  if [[ -z "${value}" ]]; then
    echo "Missing required smoke input: ${key}" >&2
    exit 1
  fi
  if is_placeholder_value "${value}"; then
    echo "Placeholder smoke input is not allowed: ${key}" >&2
    exit 1
  fi
}

require_tool() {
  local tool="$1"

  if ! command -v "${tool}" >/dev/null 2>&1; then
    echo "Missing required smoke tool: ${tool}" >&2
    exit 1
  fi
}

read_secret_file() {
  local path="$1"
  local value

  if [[ ! -f "${path}" ]]; then
    echo "Missing protected surface proxy secret file: ${path}" >&2
    exit 1
  fi

  value="$(head -n 1 "${path}" | tr -d '\r\n')"
  value="$(trim "${value}")"
  if [[ -z "${value}" ]]; then
    echo "Empty protected surface proxy secret file: ${path}" >&2
    exit 1
  fi
  if is_placeholder_value "${value}"; then
    echo "Placeholder protected surface proxy secret is not allowed" >&2
    exit 1
  fi
  printf '%s' "${value}"
}

run_capture() {
  local step="$1"
  local output_path="$2"
  shift 2

  local error_path="${output_path}.stderr"
  if ! "$@" >"${output_path}" 2>"${error_path}"; then
    echo "Smoke step failed: ${step}" >&2
    cat "${error_path}" >&2
    exit 1
  fi
}

require_env_value AEGISOPS_FIRST_BOOT_PROXY_PORT
require_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT
require_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER
require_env_value AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT
require_env_value AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY
require_env_value AEGISOPS_SMOKE_READONLY_SUBJECT
require_env_value AEGISOPS_SMOKE_READONLY_IDENTITY
require_env_value AEGISOPS_SMOKE_READONLY_ROLE
require_env_value AEGISOPS_SMOKE_REVIEWED_ALERT_ID
require_env_value AEGISOPS_SMOKE_REVIEWED_CASE_ID
require_env_value AEGISOPS_SMOKE_REVIEWED_ACTION_REQUEST_ID
require_env_value AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID
require_env_value AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE
require_env_value AEGISOPS_SMOKE_APPROVER_OWNER

readonly_role="$(load_env_value AEGISOPS_SMOKE_READONLY_ROLE)"
case "${readonly_role}" in
  analyst|approver|platform_admin)
    ;;
  *)
    echo "Invalid smoke read-only role: AEGISOPS_SMOKE_READONLY_ROLE must be analyst, approver, or platform_admin" >&2
    exit 1
    ;;
esac

low_risk_action_type="$(load_env_value AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE)"
if [[ "${low_risk_action_type}" != "notify_identity_owner" ]]; then
  echo "Invalid smoke low-risk action type: AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE must be notify_identity_owner" >&2
  exit 1
fi

proxy_secret_file="$(load_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE)"
if [[ -z "${proxy_secret_file}" ]]; then
  echo "Missing required smoke input: AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE" >&2
  exit 1
fi
if is_placeholder_value "${proxy_secret_file}"; then
  echo "Placeholder smoke input is not allowed: AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE" >&2
  exit 1
fi
proxy_secret="$(read_secret_file "${proxy_secret_file}")"

bash "${repo_root}/scripts/verify-customer-like-rehearsal-environment.sh" --env-file "${env_file}" >/dev/null

require_tool docker
require_tool curl

mkdir -p "${evidence_dir}"

proxy_port="$(load_env_value AEGISOPS_FIRST_BOOT_PROXY_PORT)"
base_url="http://127.0.0.1:${proxy_port}"
service_account="$(load_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT)"
identity_provider="$(load_env_value AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER)"
platform_subject="$(load_env_value AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT)"
platform_identity="$(load_env_value AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY)"
readonly_subject="$(load_env_value AEGISOPS_SMOKE_READONLY_SUBJECT)"
readonly_identity="$(load_env_value AEGISOPS_SMOKE_READONLY_IDENTITY)"
reviewed_alert_id="$(load_env_value AEGISOPS_SMOKE_REVIEWED_ALERT_ID)"
reviewed_case_id="$(load_env_value AEGISOPS_SMOKE_REVIEWED_CASE_ID)"
reviewed_action_request_id="$(load_env_value AEGISOPS_SMOKE_REVIEWED_ACTION_REQUEST_ID)"
reviewed_action_scope_id="$(load_env_value AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID)"
approver_owner="$(load_env_value AEGISOPS_SMOKE_APPROVER_OWNER)"
timestamp="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
revision="$(git -C "${repo_root}" rev-parse --short=12 HEAD 2>/dev/null || printf 'unknown')"

compose_file="${repo_root}/control-plane/deployment/first-boot/docker-compose.yml"

platform_headers=(
  -H "X-Forwarded-Proto: https"
  -H "X-AegisOps-Proxy-Secret: ${proxy_secret}"
  -H "X-AegisOps-Proxy-Service-Account: ${service_account}"
  -H "X-AegisOps-Authenticated-IdP: ${identity_provider}"
  -H "X-AegisOps-Authenticated-Subject: ${platform_subject}"
  -H "X-AegisOps-Authenticated-Identity: ${platform_identity}"
  -H "X-AegisOps-Authenticated-Role: platform_admin"
)

readonly_headers=(
  -H "X-Forwarded-Proto: https"
  -H "X-AegisOps-Proxy-Secret: ${proxy_secret}"
  -H "X-AegisOps-Proxy-Service-Account: ${service_account}"
  -H "X-AegisOps-Authenticated-IdP: ${identity_provider}"
  -H "X-AegisOps-Authenticated-Subject: ${readonly_subject}"
  -H "X-AegisOps-Authenticated-Identity: ${readonly_identity}"
  -H "X-AegisOps-Authenticated-Role: ${readonly_role}"
)

curl_flags=(-fsS --connect-timeout 5 --max-time 20)

run_capture "compose status" "${evidence_dir}/compose-ps.txt" \
  docker compose --env-file "${env_file}" -f "${compose_file}" ps
run_capture "bounded startup logs" "${evidence_dir}/compose-logs-tail-200.txt" \
  docker compose --env-file "${env_file}" -f "${compose_file}" logs --tail=200
run_capture "healthz" "${evidence_dir}/healthz.json" \
  curl "${curl_flags[@]}" "${base_url}/healthz"
run_capture "readyz" "${evidence_dir}/readyz.json" \
  curl "${curl_flags[@]}" "${base_url}/readyz"
run_capture "runtime" "${evidence_dir}/runtime.json" \
  curl "${curl_flags[@]}" "${platform_headers[@]}" "${base_url}/runtime"
run_capture "analyst queue ingress" "${evidence_dir}/inspect-analyst-queue.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-analyst-queue"
run_capture "operator queue ingress" "${evidence_dir}/operator-queue.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/operator/queue"
run_capture "alerts read-only inspection" "${evidence_dir}/inspect-records-alerts.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-records?family=alerts"
run_capture "alert detail inspection" "${evidence_dir}/inspect-alert-detail.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-alert-detail?alert_id=${reviewed_alert_id}"
run_capture "cases read-only inspection" "${evidence_dir}/inspect-records-cases.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-records?family=cases"
run_capture "case detail inspection" "${evidence_dir}/inspect-case-detail.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-case-detail?case_id=${reviewed_case_id}"
run_capture "action request read-only inspection" "${evidence_dir}/inspect-records-action-requests.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-records?family=action_requests"
run_capture "action review detail inspection" "${evidence_dir}/inspect-action-review.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-action-review?action_request_id=${reviewed_action_request_id}"
run_capture "assistant advisory inspection" "${evidence_dir}/inspect-advisory-output-case.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-advisory-output?family=case&record_id=${reviewed_case_id}"
run_capture "reconciliation status inspection" "${evidence_dir}/inspect-reconciliation-status.json" \
  curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-reconciliation-status"

cat > "${evidence_dir}/manifest.md" <<EOF
# Phase 37 Runtime Smoke Gate Evidence

- Result: passed
- Captured at: ${timestamp}
- Repository revision: ${revision}
- Proxy endpoint: http://127.0.0.1:<proxy-port>
- Runtime env file: <runtime-env-file>
- Compose file: control-plane/deployment/first-boot/docker-compose.yml
- Evidence artifact paths are relative to this manifest directory.
- Protected runtime inspection: runtime.json
- Readiness inspection: readyz.json
- Startup status: compose-ps.txt
- Bounded logs: compose-logs-tail-200.txt
- Protected operator-console ingress: inspect-analyst-queue.json, operator-queue.json
- Protected detail ingress: inspect-alert-detail.json, inspect-case-detail.json, inspect-action-review.json, inspect-advisory-output-case.json
- Read-only operator sanity: inspect-records-alerts.json, inspect-records-cases.json, inspect-records-action-requests.json, inspect-reconciliation-status.json
- First low-risk action preconditions: reviewed scope ${reviewed_action_scope_id}, reviewed alert ${reviewed_alert_id}, reviewed case ${reviewed_case_id}, reviewed action request ${reviewed_action_request_id}, low-risk action type ${low_risk_action_type}, approver owner ${approver_owner}; read-only inspection only; no reviewed action request, approval decision, delegation, executor dispatch, or reconciliation write was performed by this gate.
- Optional extension validation: out of scope for this mainline gate.
EOF

echo "Phase 37 runtime smoke gate passed. Evidence: ${evidence_dir}"
