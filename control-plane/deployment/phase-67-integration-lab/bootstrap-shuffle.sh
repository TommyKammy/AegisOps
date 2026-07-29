#!/usr/bin/env bash

set -euo pipefail
umask 077
trap 'rc=$?; echo "BLOCKED: Shuffle bootstrap failed at line ${LINENO} (exit ${rc})" >&2' ERR
trap '[[ -z "${auth_header_path:-}" ]] || rm -f -- "${auth_header_path}"' EXIT

LAB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lab-common.sh
source "${LAB_DIR}/lab-common.sh"

[[ "$#" -eq 0 ]] || fail "usage: $0"
require_runtime_environment
require_command curl
require_command jq
require_command openssl
require_command python3

"${LAB_DIR}/up.sh" shuffle

api_key_path="${AEGISOPS_LAB_SECRET_DIR}/shuffle-api-key"
admin_password_path="${AEGISOPS_LAB_SECRET_DIR}/shuffle-admin-password"
workflow_path="${LAB_DIR}/shuffle/harmless-local-log-workflow.json"
api_origin="https://shuffle.localhost:${AEGISOPS_LAB_PROXY_PORT}"
curl_common=(
  --fail-with-body
  --silent
  --show-error
  --cacert "${AEGISOPS_LAB_PROXY_CERT_DIR}/lab.crt"
  --resolve "shuffle.localhost:${AEGISOPS_LAB_PROXY_PORT}:127.0.0.1"
  --connect-timeout 5
  --max-time 30
)

api_key="$(<"${api_key_path}")"
if [[ "${api_key}" == bootstrap-pending-* ]]; then
  registration_payload="$(
    jq -cn \
      --arg username "phase67-admin@example.invalid" \
      --arg password "$(<"${admin_password_path}")" \
      '{username:$username,password:$password}'
  )"
  registration_response="$(
    curl "${curl_common[@]}" \
      -H 'Content-Type: application/json' \
      --data-binary "${registration_payload}" \
      "${api_origin}/api/v1/users/register"
  )"
  api_key="$(jq -er '.apikey | select(type == "string" and length > 20)' <<<"${registration_response}")"
  api_key_staging="$(mktemp "${api_key_path}.tmp.XXXXXX")"
  printf '%s\n' "${api_key}" >"${api_key_staging}"
  chmod 600 "${api_key_staging}"
  mv "${api_key_staging}" "${api_key_path}"
fi

auth_header_path="$(mktemp "${api_key_path}.header.XXXXXX")"
printf 'Authorization: Bearer %s\n' "${api_key}" >"${auth_header_path}"
chmod 600 "${auth_header_path}"
unset api_key
if [[
  "${AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE:-}" == "real_http" &&
    "${AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID:-}" =~ ^[0-9a-fA-F-]{36}$
]]; then
  workflow_id="${AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID}"
else
  workflow_create_response="$(
    curl "${curl_common[@]}" \
      -H "@${auth_header_path}" \
      -H 'Content-Type: application/json' \
      --data-binary "@${workflow_path}" \
      "${api_origin}/api/v1/workflows"
  )"
  workflow_id="$(
    jq -er '
      (.id // .workflow.id // .workflow_id)
      | select(type == "string")
      | select(test("^[0-9a-fA-F-]{36}$"))
    ' <<<"${workflow_create_response}"
  )"

  workflow_with_runtime_id="$(
    jq --arg workflow_id "${workflow_id}" '.id = $workflow_id' "${workflow_path}"
  )"
  curl "${curl_common[@]}" \
    -X PUT \
    -H "@${auth_header_path}" \
    -H 'Content-Type: application/json' \
    --data-binary "${workflow_with_runtime_id}" \
    "${api_origin}/api/v1/workflows/${workflow_id}" \
    >/dev/null
fi

preserved_workflow="$(
  curl "${curl_common[@]}" \
    -H "@${auth_header_path}" \
    "${api_origin}/api/v1/workflows/${workflow_id}"
)"
python3 \
  "${LAB_DIR}/shuffle/validate_preserved_workflow.py" \
  "${workflow_path}" \
  "${workflow_id}" \
  <<<"${preserved_workflow}"

set_runtime_value() {
  local name="$1"
  local value="$2"
  local staging

  staging="$(mktemp "${RUNTIME_ENV}.tmp.XXXXXX")"
  awk -v key="${name}" -v replacement="${name}=\"${value}\"" '
    BEGIN { replaced = 0 }
    index($0, key "=") == 1 {
      print replacement
      replaced = 1
      next
    }
    { print }
    END {
      if (!replaced) {
        print replacement
      }
    }
  ' "${RUNTIME_ENV}" >"${staging}"
  chmod 600 "${staging}"
  mv "${staging}" "${RUNTIME_ENV}"
}

set_runtime_value AEGISOPS_LAB_SHUFFLE_API_WORKFLOW_ID "${workflow_id}"
set_runtime_value AEGISOPS_LAB_SHUFFLE_TRANSPORT_MODE real_http

workflow_digest="$(
  openssl dgst -sha256 -r "${workflow_path}" | awk '{print $1}'
)"
bootstrap_evidence="${AEGISOPS_LAB_EVIDENCE_DIR}/phase67-3-shuffle-bootstrap.json"
jq -n \
  --arg captured_at "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --arg workflow_id "${workflow_id}" \
  --arg workflow_digest "${workflow_digest}" \
  '{
    schema_version:"phase67.3-shuffle-bootstrap-v1",
    captured_at:$captured_at,
    substrate:"shuffle-2.2.1",
    api_authentication:"file_backed_bearer",
    workflow_api_id:$workflow_id,
    reviewed_template_id:"notify_identity_owner",
    reviewed_template_version:"notify_identity_owner-v1-reviewed-2026-05-03",
    workflow_export_sha256:$workflow_digest,
    action_scope:"harmless_local_echo_only",
    authority_posture:"subordinate_shuffle_execution_surface"
  }' >"${bootstrap_evidence}"
chmod 600 "${bootstrap_evidence}"

"${LAB_DIR}/up.sh" shuffle
echo "Shuffle workflow imported and real_http transport enabled."
echo "workflow_api_id=${workflow_id}"
echo "Next: ${LAB_DIR}/test-shuffle-execution.sh"
