#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-60-5-runbook-guidance-agent.md"
module_path="${repo_root}/control-plane/aegisops/control_plane/assistant/runbook_guidance.py"
test_path="${repo_root}/control-plane/tests/test_phase60_5_runbook_guidance_agent.py"
agent_registry_path="${repo_root}/docs/automation/ai-agent-registry.json"
tool_registry_path="${repo_root}/docs/automation/ai-tool-registry.json"

for path in "${doc_path}" "${module_path}" "${test_path}" "${agent_registry_path}" "${tool_registry_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 60.5 runbook guidance artifact: ${path}" >&2
    exit 1
  fi
done

required_doc_phrases=(
  "# Phase 60.5 Runbook Guidance Agent"
  "The runtime entry point is \`aegisops.control_plane.assistant.runbook_guidance.build_runbook_guidance\`."
  "operator-visible \`suggested\`, \`skipped\`, \`completed\`, \`blocked\`, and \`needs_review\` posture"
  "completion ownership remains \`operator\` and guidance output never counts as workflow progress"
  "The agent uses the Phase 60.5 \`runbook_guidance\` tool registration in \`docs/automation/ai-tool-registry.json\`."
  "a reviewed \`runbook:docs/runbook.md\` record proving the runbook source was part of the reviewed context"
  "The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, mark runbook steps complete, convert suggestions into workflow progress, suppress uncertainty, hide citations, or treat runbook guidance as workflow truth."
  "If AI advisory posture is disabled or degraded, the agent returns bounded fallback output"
  "Each emitted step must include a display title and linked reviewed-record citations."
  "\`blocked\` posture may only be derived from a linked reviewed \`source_health:<source>\` record whose source health is degraded."
  "If reviewed runbook payloads are missing, empty, malformed, uncited, stale without review posture, mismatched, AI-owned completion truth, unsupported, contract-mismatched, missing the reviewed runbook record, missing linked citations, or blocked by unverified sources, the agent fails closed"
  "Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress uncertainty, mark the runbook complete, complete workflow state, or execute runbook actions must be blocked."
  "Run \`python3 -m unittest control-plane.tests.test_phase60_5_runbook_guidance_agent\`."
  "Run \`bash scripts/verify-phase-60-5-runbook-guidance-agent.sh\`."
  "Run \`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1274 --config <supervisor-config-path>\`."
)

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 60.5 runbook guidance contract statement: ${phrase}" >&2
    exit 1
  fi
done

required_module_phrases=(
  "_REGISTERED_AGENT_NAME = \"runbook_guidance_agent\""
  "_AGENT_NAME = _REGISTERED_AGENT_NAME"
  "_TOOL_NAME = \"runbook_guidance\""
  "\"authoritative_workflow_truth\": False"
  "\"mutates_authoritative_records\": False"
  "\"ai_completion_owner\": False"
  "\"trace_creation_allowed\": False"
  "\"authority_boundary\": \"cited_advisory_runbook_guidance_only\""
  "\"decision\": \"blocked\""
  "mode=\"ai_disabled\""
  "mode=\"ai_degraded\""
  "mode=\"runbook_guidance_untrusted\""
  "\"completion_owner\": \"operator\""
  "\"counts_as_workflow_progress\": False"
  "\"can_mark_complete\": False"
  "\"can_execute\": False"
  "\"stale_runbook_step\""
  "\"blocked_by_degraded_source\""
  "\"missing_reviewed_runbook_steps\""
  "\"missing_runbook_step_title\""
  "\"missing_linked_record_citation\""
  "\"untrusted_linked_record_citation\""
  "\"missing_blocked_by_degraded_source\""
  "\"blocked_by_without_degraded_source\""
  "\"missing_reviewed_runbook_record\""
  "\"ai_owned_completion_truth\""
  "\"runbook_completion_attempt\""
  "\"runbook_execution_attempt\""
)

for phrase in "${required_module_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${module_path}"; then
    echo "Missing Phase 60.5 runbook guidance implementation guard: ${phrase}" >&2
    exit 1
  fi
done

required_test_phrases=(
  "test_suggests_cited_runbook_steps_with_operator_owned_posture"
  "test_ai_owned_completion_truth_fails_closed_without_step_citation_leak"
  "test_uncited_or_stale_runbook_guidance_fails_closed"
  "test_empty_runbook_steps_fail_closed"
  "test_runbook_guidance_requires_reviewed_runbook_record"
  "test_missing_runbook_step_title_fails_closed"
  "test_untrusted_linked_record_citation_fails_closed"
  "test_blocked_posture_requires_verified_degraded_source"
  "test_prompt_pressure_to_complete_execute_or_hide_citations_is_blocked"
  "test_ai_disabled_or_degraded_returns_non_ai_runbook_fallback"
  "docs/runbook.md#2.2"
  "completion_owner"
  "counts_as_workflow_progress"
  "ai_owned_completion_truth"
)

for phrase in "${required_test_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${test_path}"; then
    echo "Missing Phase 60.5 runbook guidance focused test guard: ${phrase}" >&2
    exit 1
  fi
done

python3 - "${agent_registry_path}" "${tool_registry_path}" <<'PY'
import json
import sys
from pathlib import Path

registry = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
tool_registry = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
agents = {
    agent.get("agent_name"): agent
    for agent in registry.get("agents", ())
    if isinstance(agent, dict)
}
registered_tools = {
    tool.get("tool_name"): tool
    for tool in tool_registry.get("tools", ())
    if isinstance(tool, dict)
}
agent = agents.get("runbook_guidance_agent")
if not isinstance(agent, dict):
    raise SystemExit("Missing runbook_guidance_agent registry row.")
if agent.get("authority_ceiling") != "advisory_only_subordinate_to_aegisops_records":
    raise SystemExit("runbook_guidance_agent must keep advisory-only authority ceiling.")
allowed_tools = set(agent.get("allowed_tools", ()))
if "runbook_guidance" not in allowed_tools:
    raise SystemExit("runbook_guidance_agent must use the registered runbook_guidance tool.")
unknown_tools = sorted(allowed_tools - set(registered_tools))
if unknown_tools:
    raise SystemExit(
        "runbook_guidance_agent references unregistered tool(s): "
        + ", ".join(unknown_tools)
    )
guidance_tool = registered_tools.get("runbook_guidance")
if not isinstance(guidance_tool, dict):
    raise SystemExit("Missing registered runbook_guidance tool.")
unexpected_families = sorted(
    set(agent.get("record_families", ()))
    - set(guidance_tool.get("allowed_record_families", ()))
)
if unexpected_families:
    raise SystemExit(
        "runbook_guidance_agent declares record family outside "
        "runbook_guidance allowlist: "
        + ", ".join(unexpected_families)
    )
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
            "runbook_guidance_agent is missing disallowed tool: "
            + disallowed
        )
for disallowed in (
    "runbook_completion",
    "workflow_progress",
    "production_write",
):
    if disallowed not in guidance_tool.get("disallowed_authority", ()):
        raise SystemExit(
            "runbook_guidance tool is missing disallowed authority: "
            + disallowed
        )
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 60.5 runbook guidance artifact: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 60.5 runbook guidance agent is present with cited operator-owned posture, disabled/degraded fallback, prompt-pressure refusal, and no workflow authority."
