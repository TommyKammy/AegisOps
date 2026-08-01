#!/usr/bin/env bash

set -euo pipefail

repo_root="${AEGISOPS_REPO_ROOT_OVERRIDE:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
lab_root="${repo_root}/control-plane/deployment/phase-67-integration-lab"
e2e_root="${lab_root}/e2e"
schema="${e2e_root}/evidence-manifest.schema.json"
sample="${e2e_root}/sample-evidence.json"
validator="${e2e_root}/validate_evidence_manifest.py"
evaluation="${repo_root}/docs/phase-67-prerequisite-evaluation.md"

fail() {
  echo "Phase 67.4 verifier failed: $*" >&2
  exit 1
}

require_file() {
  [[ -f "$1" ]] || fail "missing required file: ${1#"${repo_root}/"}"
}

require_executable() {
  [[ -x "$1" ]] || fail "required script is not executable: ${1#"${repo_root}/"}"
}

require_fixed() {
  local path="$1"
  local text="$2"
  grep -Fq -- "${text}" "${path}" \
    || fail "${path#"${repo_root}/"} is missing required text: ${text}"
}

for path in \
  "${schema}" \
  "${sample}" \
  "${validator}" \
  "${e2e_root}/build_evidence.py" \
  "${e2e_root}/run_real_journey.py" \
  "${lab_root}/run-e2e-trial.sh" \
  "${evaluation}" \
  "${repo_root}/control-plane/tests/test_phase67_4_real_service_e2e.py"; do
  require_file "${path}"
done

for path in \
  "${validator}" \
  "${e2e_root}/build_evidence.py" \
  "${e2e_root}/run_real_journey.py" \
  "${lab_root}/run-e2e-trial.sh"; do
  require_executable "${path}"
done

require_fixed "${evaluation}" '`integration_trial_passed_with_owned_limitations`'
require_fixed "${evaluation}" 'GA acceptance: not accepted.'
require_fixed "${evaluation}" 'AegisOps alert, case, action request, approval decision, action execution,'
require_fixed "${evaluation}" 'does not prove production readiness'
require_fixed "${lab_root}/RUNBOOK.md" '## Complete Phase 67.4 E2E Trial'
require_fixed "${lab_root}/RUNBOOK.md" 'run-e2e-trial.sh'
require_fixed "${repo_root}/README.md" 'Phase 67.4 real-service E2E prerequisite evaluation'
require_fixed "${lab_root}/test-wazuh-intake.sh" 'native_wazuh_agent_id: $agent_id'
require_fixed "${lab_root}/test-wazuh-intake.sh" 'AEGISOPS_LAB_TRIAL_SCOPE:-wazuh'
require_fixed "${e2e_root}/run_real_journey.py" 'REQUESTER_IDENTITY = "phase67-lab-requester"'
require_fixed "${e2e_root}/run_real_journey.py" 'if not rejected or execution_count != 0:'
require_fixed "${e2e_root}/run_real_journey.py" 'lifecycle_state="rejected"'
require_fixed "${e2e_root}/run_real_journey.py" 'service.reconcile_action_execution('
require_fixed "${e2e_root}/run_real_journey.py" 'export_audit_retention_baseline('
require_fixed "${lab_root}/run-e2e-trial.sh" 'verify-restart'
require_fixed "${lab_root}/run-e2e-trial.sh" '[[ -t 0 && -t 1 ]]'
require_fixed "${lab_root}/run-e2e-trial.sh" '"APPROVE ${approval_challenge}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'display dialog promptText'
require_fixed "${lab_root}/run-e2e-trial.sh" '"shuffle-action-image"'
require_fixed "${lab_root}/run-e2e-trial.sh" '.journey | .aegisops_alert_id = .alert_id'
require_fixed "${lab_root}/run-e2e-trial.sh" 'docker_lab inspect ${container_ids}'
require_fixed "${lab_root}/run-e2e-trial.sh" 'docker_context="${AEGISOPS_LAB_DOCKER_CONTEXT}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'colima_profile="${AEGISOPS_LAB_COLIMA_PROFILE}"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'final_artifacts=' 
require_fixed "${lab_root}/run-e2e-trial.sh" '"${LAB_DIR}/cleanup.sh"'
require_fixed "${lab_root}/run-e2e-trial.sh" 'status --porcelain=v1'

python3 -m json.tool "${schema}" >/dev/null
python3 "${validator}" "${schema}" "${sample}"
bash -n \
  "${lab_root}/run-e2e-trial.sh" \
  "${lab_root}/test-wazuh-intake.sh"
python3 -m compileall -q \
  "${e2e_root}" \
  "${repo_root}/control-plane/tests/test_phase67_4_real_service_e2e.py"
(
  cd "${repo_root}"
  python3 -m unittest control-plane/tests/test_phase67_4_real_service_e2e.py
)

echo "PASS: Phase 67.4 real-service E2E evidence and prerequisite evaluation verified."
