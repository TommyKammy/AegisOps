#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-60-2-today-queue-digest-agent.md"
module_path="${repo_root}/control-plane/aegisops/control_plane/assistant/today_queue_digest.py"
test_path="${repo_root}/control-plane/tests/test_phase60_2_today_queue_digest_agent.py"
agent_registry_path="${repo_root}/docs/automation/ai-agent-registry.json"
tool_registry_path="${repo_root}/docs/automation/ai-tool-registry.json"

for path in "${doc_path}" "${module_path}" "${test_path}" "${agent_registry_path}" "${tool_registry_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 60.2 Today queue digest artifact: ${path}" >&2
    exit 1
  fi
done

required_doc_phrases=(
  "# Phase 60.2 Today Queue Digest Agent"
  "summarizes reviewed Today analyst queue records with citations"
  "without changing queue priority, task state, case state, approval state, execution state, reconciliation state, or workflow routing"
  "The runtime entry point is \`aegisops.control_plane.assistant.today_queue_digest.build_today_queue_digest\`."
  "The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, change queue priority, mark tasks complete, suppress stale or degraded work, hide missing evidence, or treat digest output as workflow truth."
  "If AI advisory posture is disabled or degraded, the agent returns bounded fallback output."
  "If queue evidence is missing, malformed, unreviewed, or uncited, the agent fails closed with explicit unresolved reasons rather than inventing a digest."
  "Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress stale/degraded work, suppress uncertainty, change queue priority, or mark tasks complete must be blocked."
  "Run \`python3 -m unittest control-plane.tests.test_phase60_2_today_queue_digest_agent\`."
  "Run \`bash scripts/verify-phase-60-2-today-queue-digest-agent.sh\`."
  "Run \`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1271 --config <supervisor-config-path>\`."
)

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 60.2 Today queue digest contract statement: ${phrase}" >&2
    exit 1
  fi
done

required_module_phrases=(
  "_REGISTERED_AGENT_NAME = \"today_queue_digest_agent\""
  "_AGENT_NAME = _REGISTERED_AGENT_NAME"
  "_TOOL_NAME = \"today_queue_digest\""
  "\"authoritative_workflow_truth\": False"
  "\"mutates_authoritative_records\": False"
  "\"trace_creation_allowed\": False"
  "\"queue:analyst_review\""
  "\"decision\": \"blocked\""
  "mode=\"ai_disabled\""
  "mode=\"ai_degraded\""
  "mode=\"queue_evidence_missing\""
  "\"queue_priority_mutation_attempt\""
  "\"uncertainty_suppression_attempt\""
)

for phrase in "${required_module_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${module_path}"; then
    echo "Missing Phase 60.2 Today queue digest implementation guard: ${phrase}" >&2
    exit 1
  fi
done

required_test_phrases=(
  "test_digest_summarizes_reviewed_queue_with_citations_and_gaps"
  "test_uncited_or_unreviewed_queue_record_fails_closed"
  "test_prompt_pressure_to_mutate_or_hide_queue_truth_is_blocked"
  "test_ai_disabled_or_degraded_returns_non_ai_today_fallback"
  "changed queue priority"
  "marked tasks complete"
  "missing_evidence"
  "source_health:wazuh"
)

for phrase in "${required_test_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${test_path}"; then
    echo "Missing Phase 60.2 Today queue digest focused test guard: ${phrase}" >&2
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
agent = agents.get("today_queue_digest_agent")
if not isinstance(agent, dict):
    raise SystemExit("Missing today_queue_digest_agent registry row.")
if agent.get("authority_ceiling") != "advisory_only_subordinate_to_aegisops_records":
    raise SystemExit("today_queue_digest_agent must keep advisory-only authority ceiling.")
allowed_tools = set(agent.get("allowed_tools", ()))
if "today_queue_digest" not in allowed_tools:
    raise SystemExit("today_queue_digest_agent must use the registered today_queue_digest tool.")
unknown_tools = sorted(allowed_tools - set(registered_tools))
if unknown_tools:
    raise SystemExit(
        "today_queue_digest_agent references unregistered tool(s): "
        + ", ".join(unknown_tools)
    )
digest_tool = registered_tools.get("today_queue_digest")
if not isinstance(digest_tool, dict):
    raise SystemExit("Missing registered today_queue_digest tool.")
unexpected_families = sorted(
    set(agent.get("record_families", ()))
    - set(digest_tool.get("allowed_record_families", ()))
)
if unexpected_families:
    raise SystemExit(
        "today_queue_digest_agent declares record family outside "
        "today_queue_digest allowlist: "
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
            "today_queue_digest_agent is missing disallowed tool: "
            + disallowed
        )
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 60.2 Today queue digest artifact: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 60.2 Today queue digest agent is present with cited advisory output, disabled/degraded fallback, prompt-pressure refusal, and no workflow authority."
