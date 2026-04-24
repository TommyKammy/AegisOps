#!/usr/bin/env bash

set -euo pipefail

repo_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
gate_path="${repo_root}/scripts/run-phase-37-runtime-smoke-gate.sh"
test_path="${repo_root}/scripts/test-run-phase-37-runtime-smoke-gate.sh"
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
require_file "${smoke_path}" "runtime smoke bundle"
require_file "${runbook_path}" "runbook"
require_file "${rehearsal_path}" "customer-like rehearsal environment"
require_file "${handoff_path}" "operational evidence handoff pack"

required_gate_phrases=(
  'Usage: scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> [--evidence-dir <evidence-dir>]'
  'AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT'
  'AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY'
  'AEGISOPS_SMOKE_READONLY_SUBJECT'
  'AEGISOPS_SMOKE_READONLY_IDENTITY'
  'AEGISOPS_SMOKE_READONLY_ROLE'
  'AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID'
  'AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE'
  'AEGISOPS_SMOKE_APPROVER_OWNER'
  'Invalid smoke low-risk action type: AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE must be notify_identity_owner'
  'bash "${repo_root}/scripts/verify-customer-like-rehearsal-environment.sh" --env-file "${env_file}"'
  'docker compose --env-file "${env_file}" -f "${compose_file}" ps'
  'docker compose --env-file "${env_file}" -f "${compose_file}" logs --tail=200'
  'curl -fsS "${base_url}/healthz"'
  'curl -fsS "${base_url}/readyz"'
  'curl -fsS "${platform_headers[@]}" "${base_url}/runtime"'
  'curl -fsS "${readonly_headers[@]}" "${base_url}/inspect-records?family=alerts"'
  'curl -fsS "${readonly_headers[@]}" "${base_url}/inspect-records?family=cases"'
  'curl -fsS "${readonly_headers[@]}" "${base_url}/inspect-records?family=action_requests"'
  'curl -fsS "${readonly_headers[@]}" "${base_url}/inspect-reconciliation-status"'
  'First low-risk action preconditions: reviewed scope ${reviewed_action_scope_id}, low-risk action type ${low_risk_action_type}, approver owner ${approver_owner}; read-only inspection only; no reviewed action request, approval decision, delegation, executor dispatch, or reconciliation write was performed by this gate.'
)

for phrase in "${required_gate_phrases[@]}"; do
  require_phrase "${gate_path}" "${phrase}" "Phase 37 runtime smoke gate statement"
done

required_doc_phrases=(
  'For Phase 37 rehearsal, run the executable gate with `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` after the customer-like rehearsal preflight passes and the first-boot stack is running.'
  'The gate writes `manifest.md` plus bounded startup, readiness, runtime, protected read-only, and reconciliation evidence files for handoff review.'
  'The smoke-only authentication and precondition inputs are `AEGISOPS_SMOKE_PLATFORM_ADMIN_SUBJECT`, `AEGISOPS_SMOKE_PLATFORM_ADMIN_IDENTITY`, `AEGISOPS_SMOKE_READONLY_SUBJECT`, `AEGISOPS_SMOKE_READONLY_IDENTITY`, `AEGISOPS_SMOKE_READONLY_ROLE`, `AEGISOPS_SMOKE_REVIEWED_ACTION_SCOPE_ID`, `AEGISOPS_SMOKE_LOW_RISK_ACTION_TYPE`, and `AEGISOPS_SMOKE_APPROVER_OWNER` in the untracked runtime env file.'
)

for phrase in "${required_doc_phrases[@]}"; do
  require_phrase "${smoke_path}" "${phrase}" "runtime smoke bundle Phase 37 gate statement"
done

require_phrase "${runbook_path}" 'For Phase 37 customer-like rehearsal, operators run `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` after startup to turn the Phase 33 bundle into an executable release gate with retained smoke evidence.' "runbook Phase 37 executable gate link"
require_phrase "${rehearsal_path}" 'Run `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` through the reverse proxy and retain its `manifest.md`.' "customer-like rehearsal executable gate step"
require_phrase "${handoff_path}" 'For Phase 37 customer-like rehearsal, include the verifier result from `scripts/verify-customer-like-rehearsal-environment.sh --env-file <runtime-env-file>` and the executable smoke gate manifest from `scripts/run-phase-37-runtime-smoke-gate.sh --env-file <runtime-env-file> --evidence-dir <evidence-dir>` with the startup, backup-custody, and clean-state evidence.' "handoff Phase 37 executable gate evidence"

if grep -Fq 'POST /operator/create-reviewed-action-request' "${gate_path}"; then
  echo "Forbidden Phase 37 runtime smoke gate write path: POST /operator/create-reviewed-action-request" >&2
  exit 1
fi

if grep -Eq '(^|[^[:alnum:]_./-])(~[/\\]|/Users/[^[:space:])>]+|/home/[^[:space:])>]+|[A-Za-z]:\\Users\\[^[:space:])>]+)' "${smoke_path}" "${runbook_path}" "${rehearsal_path}" "${handoff_path}"; then
  echo "Forbidden Phase 37 runtime smoke gate guidance: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 37 runtime smoke gate is executable and documented for release handoff."
