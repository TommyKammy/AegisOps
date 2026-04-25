#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
gate_path="${repo_root}/scripts/run-phase-37-runtime-smoke-gate.sh"
test_path="${repo_root}/scripts/test-run-phase-37-runtime-smoke-gate.sh"
record_chain_gate_path="${repo_root}/scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh"
record_chain_test_path="${repo_root}/control-plane/tests/test_phase37_reviewed_record_chain_rehearsal.py"
record_chain_fixture_path="${repo_root}/control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json"
smoke_path="${repo_root}/docs/deployment/runtime-smoke-bundle.md"
runbook_path="${repo_root}/docs/runbook.md"
rehearsal_path="${repo_root}/docs/deployment/customer-like-rehearsal-environment.md"
handoff_path="${repo_root}/docs/deployment/operational-evidence-handoff-pack.md"

require_file() {
  local path="$1"
  local description="$2"

  if [[ ! -f "${path}" ]]; then
    echo "Missing ${description}: ${path}" >&2
    exit 1
  fi
}

require_executable() {
  local path="$1"
  local description="$2"

  require_file "${path}" "${description}"
  if [[ ! -x "${path}" ]]; then
    echo "Missing executable bit for ${description}: ${path}" >&2
    exit 1
  fi
}

require_phrase() {
  local path="$1"
  local phrase="$2"
  local description="$3"

  if ! grep -Fq -- "${phrase}" "${path}"; then
    echo "Missing ${description}: ${phrase}" >&2
    exit 1
  fi
}

require_executable "${gate_path}" "Phase 37 runtime smoke gate"
require_executable "${test_path}" "Phase 37 runtime smoke gate test"
require_executable "${record_chain_gate_path}" "Phase 37 reviewed record-chain rehearsal verifier"
require_file "${record_chain_test_path}" "Phase 37 reviewed record-chain rehearsal test"
require_file "${record_chain_fixture_path}" "Phase 37 reviewed record-chain rehearsal fixture"
require_file "${smoke_path}" "runtime smoke bundle"
require_file "${runbook_path}" "runbook"
require_file "${rehearsal_path}" "customer-like rehearsal environment"
require_file "${handoff_path}" "operational evidence handoff pack"

required_gate_phrases=(
  'Usage: scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> [--evidence-dir <evidence-dir>]'
  'AEGISOPS_FIRST_BOOT_PROXY_PORT'
  'AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_PROXY_SERVICE_ACCOUNT'
  'AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVIEWED_IDENTITY_PROVIDER'
  'AEGISOPS_CONTROL_PLANE_PROTECTED_SURFACE_REVERSE_PROXY_SECRET_FILE'
  'AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT'
  'AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY'
  'AEGISOPS_SMOKE_READONLY_SUBJECT'
  'AEGISOPS_SMOKE_READONLY_IDENTITY'
  'AEGISOPS_SMOKE_READONLY_ROLE'
  'AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID'
  'AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE'
  'AEGISOPS_SMOKE_APPROVER_OWNER'
  'Missing protected surface proxy secret file:'
  'Empty protected surface proxy secret file:'
  'Placeholder protected surface proxy secret is not allowed'
  'Invalid smoke read-only role: AEGISOPS_SMOKE_READONLY_ROLE must be analyst, approver, or platform_admin'
  'Invalid smoke low-risk action type: AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE must be notify_identity_owner'
  'bash "${repo_root}/scripts/verify-customer-like-rehearsal-environment.sh" --env-file "${env_file}"'
  'docker compose --env-file "${env_file}" -f "${compose_file}" ps'
  'docker compose --env-file "${env_file}" -f "${compose_file}" logs --tail=200'
  'curl_flags=(-fsS --connect-timeout 5 --max-time 20)'
  'curl "${curl_flags[@]}" "${base_url}/healthz"'
  'curl "${curl_flags[@]}" "${base_url}/readyz"'
  'curl "${curl_flags[@]}" "${platform_headers[@]}" "${base_url}/runtime"'
  'curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-records?family=alerts"'
  'curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-records?family=cases"'
  'curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-records?family=action_requests"'
  'curl "${curl_flags[@]}" "${readonly_headers[@]}" "${base_url}/inspect-reconciliation-status"'
  '- Evidence artifact paths are relative to this manifest directory.'
  '- Protected runtime inspection: runtime.json'
  '- Readiness inspection: readyz.json'
  '- Startup status: compose-ps.txt'
  '- Bounded logs: compose-logs-tail-200.txt'
  '- Read-only operator sanity: inspect-records-alerts.json, inspect-records-cases.json, inspect-records-action-requests.json, inspect-reconciliation-status.json'
  'First low-risk action preconditions: reviewed scope ${reviewed_action_scope_id}, low-risk action type ${low_risk_action_type}, approver owner ${approver_owner}; read-only inspection only; no reviewed action request, approval decision, delegation, executor dispatch, or reconciliation write was performed by this gate.'
)

for phrase in "${required_gate_phrases[@]}"; do
  require_phrase "${gate_path}" "${phrase}" "Phase 37 runtime smoke gate statement"
done

required_doc_phrases=(
  'For Phase 37 rehearsal, run the executable gate with `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` after the customer-like rehearsal preflight passes and the first-boot stack is running.'
  'Before the runtime smoke gate, run `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh` to replay the seeded fixture in `control-plane/tests/fixtures/phase37/reviewed-record-chain-rehearsal.json` through the authoritative reviewed record chain.'
  'The gate writes `manifest.md` plus bounded startup, readiness, runtime, protected read-only, and reconciliation evidence files for handoff review.'
  'The smoke-only authentication and precondition inputs are `AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT`, `AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY`, `AEGISOPS_SMOKE_READONLY_SUBJECT`, `AEGISOPS_SMOKE_READONLY_IDENTITY`, `AEGISOPS_SMOKE_READONLY_ROLE`, `AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID`, `AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE`, and `AEGISOPS_SMOKE_APPROVER_OWNER` in the untracked runtime env file.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${smoke_path}" "${phrase}" "runtime smoke bundle Phase 37 gate statement"
done

require_phrase "${runbook_path}" 'For Phase 37 customer-like rehearsal, operators run `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` after startup to turn the Phase 33 bundle into an executable release gate with retained smoke evidence.' "runbook Phase 37 executable gate link"
require_phrase "${runbook_path}" 'Before the runtime smoke gate, operators run `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh` to prove the seeded reviewed chain still separates detection evidence, AegisOps-owned alert and case truth, reviewed action request, approval decision, execution receipt, reconciliation, and handoff evidence.' "runbook Phase 37 record-chain rehearsal link"
require_phrase "${rehearsal_path}" 'Run `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh` to replay the seeded reviewed record-chain fixture through detection admission, case ownership, reviewed action request, separate approval, Shuffle execution receipt, reconciliation, and manifest validation.' "customer-like rehearsal record-chain replay step"
require_phrase "${rehearsal_path}" 'Run `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` through the reverse proxy and retain its `manifest.md`.' "customer-like rehearsal executable gate step"
require_phrase "${handoff_path}" 'For Phase 37 customer-like rehearsal, include the verifier result from `scripts/verify-customer-like-rehearsal-environment.sh --env-file <runtime-env-file>`, the reviewed record-chain replay result from `scripts/verify-phase-37-reviewed-record-chain-rehearsal.sh`, and the executable smoke gate manifest from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` with the startup, backup-custody, and clean-state evidence.' "handoff Phase 37 executable gate evidence"

reviewed_action_write_path='/operator/create-reviewed-action-request'
if grep -Eq -- "${reviewed_action_write_path}([/?#[:space:]\"']|$)" "${gate_path}"; then
  echo "Forbidden Phase 37 runtime smoke gate write path: ${reviewed_action_write_path}" >&2
  exit 1
fi

macos_home_pattern='/'"Users"'/[^[:space:])>]+'
linux_home_pattern='/'"home"'/[^[:space:])>]+'
windows_home_pattern='[A-Za-z]:\\'"Users"'\\[^[:space:])>]+'
workstation_local_path_pattern="(^|[^[:alnum:]_./-])(~[/\\\\]|${macos_home_pattern}|${linux_home_pattern}|${windows_home_pattern})"
if grep -Eq "${workstation_local_path_pattern}" "${smoke_path}" "${runbook_path}" "${rehearsal_path}" "${handoff_path}"; then
  echo "Forbidden Phase 37 runtime smoke gate guidance: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 37 runtime smoke gate is executable and documented for release handoff."
