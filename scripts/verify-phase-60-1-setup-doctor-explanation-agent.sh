#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-60-1-setup-doctor-explanation-agent.md"
module_path="${repo_root}/control-plane/aegisops/control_plane/assistant/setup_doctor_explanation.py"
test_path="${repo_root}/control-plane/tests/test_phase60_1_setup_doctor_explanation_agent.py"
agent_registry_path="${repo_root}/docs/automation/ai-agent-registry.json"

for path in "${doc_path}" "${module_path}" "${test_path}" "${agent_registry_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 60.1 setup doctor explanation artifact: ${path}" >&2
    exit 1
  fi
done

required_doc_phrases=(
  "# Phase 60.1 Setup Doctor Explanation Agent"
  "without automatic repair authority"
  "registered Phase 59 registry artifacts"
  "The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, mutate secrets, restart services, repair the stack, change source posture, or treat support output as workflow, release, gate, restore, limitation, or closeout truth."
  "If AI advisory posture is disabled or degraded, the agent returns bounded fallback output."
  "If doctor evidence is missing or malformed, the agent fails closed with explicit unresolved reasons and bounded fallback guidance rather than inventing setup guidance."
  "Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress uncertainty, repair the stack, rotate secrets, restart services, or change source posture must be blocked."
  'Run `python3 -m unittest control-plane.tests.test_phase60_1_setup_doctor_explanation_agent`.'
  'Run `bash scripts/verify-phase-60-1-setup-doctor-explanation-agent.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1270 --config <supervisor-config-path>`.'
)

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 60.1 setup doctor explanation contract statement: ${phrase}" >&2
    exit 1
  fi
done

required_module_phrases=(
  "_REGISTERED_AGENT_NAME = \"setup_doctor_explanation_agent\""
  "_AGENT_NAME = _REGISTERED_AGENT_NAME"
  "_TOOL_NAME = \"doctor_explanation\""
  "\"authoritative_workflow_truth\": False"
  "\"mutates_authoritative_records\": False"
  "\"automatic_repair_allowed\": False"
  "\"support_output_is_workflow_truth\": False"
  "\"docs/automation/ai-agent-registry.json\""
  "\"docs/automation/ai-tool-registry.json\""
  "\"docs/automation/ai-disabled-degraded-mode-contract.json\""
  "\"decision\": \"blocked\""
  "\"mode\": \"ai_disabled\""
  "\"mode\": \"doctor_evidence_missing\""
  "\"trace_creation_allowed\": False"
)

for phrase in "${required_module_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${module_path}"; then
    echo "Missing Phase 60.1 setup doctor explanation implementation guard: ${phrase}" >&2
    exit 1
  fi
done

required_test_phrases=(
  "test_explains_broken_stack_with_registered_cited_advisory_output"
  "test_disabled_ai_returns_bounded_non_ai_fallback_without_trace_creation"
  "test_prompt_pressure_fails_closed_and_preserves_citations"
  "test_missing_doctor_evidence_fails_closed"
  "test_non_mapping_readiness_payload_fails_closed_before_doctor_snapshot"
  "test_change_source_posture_prompt_fails_closed"
  "repaired the stack"
  "rotated secrets"
  "restarted services"
  "changed source posture"
)

for phrase in "${required_test_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${test_path}"; then
    echo "Missing Phase 60.1 setup doctor explanation focused test guard: ${phrase}" >&2
    exit 1
  fi
done

python3 - "${agent_registry_path}" <<'PY'
import json
import sys
from pathlib import Path

registry = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
agents = {
    agent.get("agent_name"): agent
    for agent in registry.get("agents", ())
    if isinstance(agent, dict)
}
agent = agents.get("setup_doctor_explanation_agent")
if not isinstance(agent, dict):
    raise SystemExit("Missing setup_doctor_explanation_agent registry row.")
if agent.get("authority_ceiling") != "advisory_only_subordinate_to_aegisops_records":
    raise SystemExit("setup_doctor_explanation_agent must keep advisory-only authority ceiling.")
if "doctor_explanation" not in agent.get("allowed_tools", ()):
    raise SystemExit("setup_doctor_explanation_agent must use the registered doctor_explanation tool.")
for disallowed in (
    "approve_action",
    "execute_action",
    "reconcile_execution",
    "close_case",
    "activate_detector",
    "create_source_truth",
    "bypass_policy",
):
    if disallowed not in agent.get("disallowed_tools", ()):
        raise SystemExit(
            "setup_doctor_explanation_agent is missing disallowed tool: "
            + disallowed
        )
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 60.1 setup doctor explanation artifact: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 60.1 setup doctor explanation agent is present with cited advisory output, disabled/degraded fallback, prompt-pressure refusal, and no repair authority."
