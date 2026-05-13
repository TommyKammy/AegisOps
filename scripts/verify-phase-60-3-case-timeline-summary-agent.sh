#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-60-3-case-timeline-summary-agent.md"
module_path="${repo_root}/control-plane/aegisops/control_plane/assistant/case_timeline_summary.py"
test_path="${repo_root}/control-plane/tests/test_phase60_3_case_timeline_summary_agent.py"
agent_registry_path="${repo_root}/docs/automation/ai-agent-registry.json"
tool_registry_path="${repo_root}/docs/automation/ai-tool-registry.json"

for path in "${doc_path}" "${module_path}" "${test_path}" "${agent_registry_path}" "${tool_registry_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 60.3 case timeline summary artifact: ${path}" >&2
    exit 1
  fi
done

required_doc_phrases=(
  "# Phase 60.3 Case Timeline Summary Agent"
  "summarizes reviewed case timeline chains with citations, authority labels, and uncertainty flags"
  "without changing case state, segment state, approval state, execution state, reconciliation state, subordinate evidence posture, or workflow routing"
  "The runtime entry point is \`aegisops.control_plane.assistant.case_timeline_summary.build_case_timeline_summary\`."
  "The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, complete timeline segments, suppress uncertainty, hide citations, resolve conflicts, or treat summary output as workflow truth."
  "If AI advisory posture is disabled or degraded, the agent returns bounded fallback output."
  "If timeline evidence is missing, malformed, uncited, cache-sourced, unsupported, or contract-mismatched, the agent fails closed with explicit unresolved reasons rather than inventing a summary."
  "Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress uncertainty, complete timeline segments, or resolve conflicts must be blocked."
  "Run \`python3 -m unittest control-plane.tests.test_phase60_3_case_timeline_summary_agent\`."
  "Run \`npm --prefix apps/operator-ui test -- OperatorRoutes.test.tsx\`."
  "Run \`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1272 --config <supervisor-config-path>\`."
)

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 60.3 case timeline summary contract statement: ${phrase}" >&2
    exit 1
  fi
done

required_module_phrases=(
  "_REGISTERED_AGENT_NAME = \"case_timeline_summary_agent\""
  "_AGENT_NAME = _REGISTERED_AGENT_NAME"
  "_TOOL_NAME = \"case_timeline_summary\""
  "\"authoritative_workflow_truth\": False"
  "\"mutates_authoritative_records\": False"
  "\"trace_creation_allowed\": False"
  "\"authority_boundary\": \"cited_advisory_case_timeline_summary_only\""
  "\"decision\": \"blocked\""
  "mode=\"ai_disabled\""
  "mode=\"ai_degraded\""
  "mode=\"timeline_evidence_missing\""
  "\"timeline_completion_attempt\""
  "\"uncertainty_suppression_attempt\""
  "\"timeline_gap:"
)

for phrase in "${required_module_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${module_path}"; then
    echo "Missing Phase 60.3 case timeline summary implementation guard: ${phrase}" >&2
    exit 1
  fi
done

required_test_phrases=(
  "test_summary_cites_reviewed_timeline_segments_with_authority_and_uncertainty"
  "test_uncited_reviewed_segment_fails_closed"
  "test_malformed_timeline_projection_fails_closed"
  "test_prompt_pressure_to_mutate_or_hide_case_truth_is_blocked"
  "test_ai_disabled_or_degraded_returns_non_ai_case_fallback"
  "missing_timeline_segment"
  "stale_timeline_segment"
  "conflicting_timeline_segment"
  "timeline_completion_attempt"
)

for phrase in "${required_test_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${test_path}"; then
    echo "Missing Phase 60.3 case timeline summary focused test guard: ${phrase}" >&2
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
agent = agents.get("case_timeline_summary_agent")
if not isinstance(agent, dict):
    raise SystemExit("Missing case_timeline_summary_agent registry row.")
if agent.get("authority_ceiling") != "advisory_only_subordinate_to_aegisops_records":
    raise SystemExit("case_timeline_summary_agent must keep advisory-only authority ceiling.")
allowed_tools = set(agent.get("allowed_tools", ()))
if "case_timeline_summary" not in allowed_tools:
    raise SystemExit("case_timeline_summary_agent must use the registered case_timeline_summary tool.")
unknown_tools = sorted(allowed_tools - set(registered_tools))
if unknown_tools:
    raise SystemExit(
        "case_timeline_summary_agent references unregistered tool(s): "
        + ", ".join(unknown_tools)
    )
summary_tool = registered_tools.get("case_timeline_summary")
if not isinstance(summary_tool, dict):
    raise SystemExit("Missing registered case_timeline_summary tool.")
unexpected_families = sorted(
    set(agent.get("record_families", ()))
    - set(summary_tool.get("allowed_record_families", ()))
)
if unexpected_families:
    raise SystemExit(
        "case_timeline_summary_agent declares record family outside "
        "case_timeline_summary allowlist: "
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
            "case_timeline_summary_agent is missing disallowed tool: "
            + disallowed
        )
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 60.3 case timeline summary artifact: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 60.3 case timeline summary agent is present with cited advisory output, disabled/degraded fallback, prompt-pressure refusal, and no workflow authority."
