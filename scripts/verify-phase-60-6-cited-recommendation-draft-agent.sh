#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-60-6-cited-recommendation-draft-agent.md"
module_path="${repo_root}/control-plane/aegisops/control_plane/assistant/cited_recommendation_draft.py"
test_path="${repo_root}/control-plane/tests/test_phase60_6_cited_recommendation_draft_agent.py"
ui_surface_path="${repo_root}/apps/operator-ui/src/app/operatorConsolePages/advisorySurfaces.tsx"
ui_page_path="${repo_root}/apps/operator-ui/src/app/operatorConsolePages/assistantPages.tsx"
ui_test_path="${repo_root}/apps/operator-ui/src/app/OperatorRoutes.assistant.testSuite.tsx"
agent_registry_path="${repo_root}/docs/automation/ai-agent-registry.json"
tool_registry_path="${repo_root}/docs/automation/ai-tool-registry.json"

for path in \
  "${doc_path}" \
  "${module_path}" \
  "${test_path}" \
  "${ui_surface_path}" \
  "${ui_page_path}" \
  "${ui_test_path}" \
  "${agent_registry_path}" \
  "${tool_registry_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 60.6 cited recommendation draft artifact: ${path}" >&2
    exit 1
  fi
done

required_doc_phrases=(
  "# Phase 60.6 Cited Recommendation Draft Agent"
  "The runtime entry point is \`aegisops.control_plane.assistant.cited_recommendation_draft.build_cited_recommendation_draft\`."
  "operator-visible \`accepted\`, \`rejected\`, \`corrected\`, and \`unresolved\` feedback posture"
  "feedback remains review context only and never becomes workflow truth"
  "The agent uses the Phase 60.6 \`recommendation_draft\` tool registration in \`docs/automation/ai-tool-registry.json\`."
  "The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, convert recommendation feedback into workflow truth, mark workflow complete, suppress uncertainty, hide citations, or force acceptance."
  "If AI advisory posture is disabled or degraded, the agent returns bounded fallback output"
  "Corrected feedback must keep the operator correction visible as review context only."
  "Unresolved, stale, or conflicting evidence posture must remain visible and keeps emitted draft feedback unresolved."
  "If recommendation context payloads are missing, empty, malformed, uncited, unsupported, contract-mismatched, unbound to the review anchor, AI-created recommendation context, unsupported feedback posture, missing correction text, missing required draft citations, or linked to untrusted draft citations, the agent fails closed"
  "Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, bypass policy, hide citations, suppress uncertainty, force acceptance, hide rejected or corrected state, or complete workflow state must be blocked."
  "Run \`python3 -m unittest control-plane.tests.test_phase60_6_cited_recommendation_draft_agent\`."
  "Run \`bash scripts/verify-phase-60-6-cited-recommendation-draft-agent.sh\`."
  "Run \`npm test -- --run src/app/OperatorRoutes.test.tsx\` from \`apps/operator-ui\`."
  "Run \`npm run typecheck --workspace @aegisops/operator-ui\`."
  "Run \`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1275 --config <supervisor-config-path>\`."
)

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 60.6 cited recommendation draft contract statement: ${phrase}" >&2
    exit 1
  fi
done

required_module_phrases=(
  "_AGENT_NAME = \"cited_recommendation_draft_agent\""
  "_TOOL_NAME = \"recommendation_draft\""
  "\"authoritative_workflow_truth\": False"
  "\"mutates_authoritative_records\": False"
  "\"approval_authority\": False"
  "\"execution_authority\": False"
  "\"reconciliation_authority\": False"
  "\"case_closure_authority\": False"
  "\"trace_creation_allowed\": False"
  "\"authority_boundary\": \"cited_advisory_recommendation_draft_only\""
  "\"decision\": \"blocked\""
  "mode=\"ai_disabled\""
  "mode=\"ai_degraded\""
  "mode=\"recommendation_draft_untrusted\""
  "\"counts_as_workflow_truth\": False"
  "\"can_approve_action\": False"
  "\"can_execute_action\": False"
  "\"can_reconcile\": False"
  "\"can_close_case\": False"
  "\"operator_unresolved\""
  "\"stale_evidence\""
  "\"conflicting_evidence\""
  "\"missing_required_draft_citation\""
  "\"untrusted_draft_citation\""
  "\"record_not_bound_to_review_anchor\""
  "\"unsupported_operator_feedback_posture\""
  "\"missing_operator_correction\""
  "\"feedback_coercion_attempt\""
  "\"workflow_completion_attempt\""
)

for phrase in "${required_module_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${module_path}"; then
    echo "Missing Phase 60.6 cited recommendation draft implementation guard: ${phrase}" >&2
    exit 1
  fi
done

required_test_phrases=(
  "test_drafts_cited_reviewable_recommendations_with_feedback_posture"
  "test_missing_citations_fail_closed_without_draft_citation_leak"
  "test_stale_or_conflicting_evidence_keeps_recommendation_unresolved"
  "test_untrusted_feedback_and_cross_anchor_context_fail_closed"
  "test_prompt_pressure_to_approve_execute_or_hide_citations_is_blocked"
  "test_ai_disabled_or_degraded_returns_non_ai_feedback_fallback"
  "operator_feedback_posture"
  "operator_correction"
  "counts_as_workflow_truth"
  "can_approve_action"
)

for phrase in "${required_test_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${test_path}"; then
    echo "Missing Phase 60.6 cited recommendation draft focused test guard: ${phrase}" >&2
    exit 1
  fi
done

required_ui_phrases=(
  "recommendation_drafts"
  "operator_feedback_posture"
  "requested_feedback_posture"
  "Review context only"
  "Correction:"
)

for phrase in "${required_ui_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${ui_surface_path}" "${ui_page_path}" "${ui_test_path}"; then
    echo "Missing Phase 60.6 operator UI feedback guard: ${phrase}" >&2
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
agent = agents.get("cited_recommendation_draft_agent")
if not isinstance(agent, dict):
    raise SystemExit("Missing cited_recommendation_draft_agent registry row.")
if agent.get("authority_ceiling") != "advisory_only_subordinate_to_aegisops_records":
    raise SystemExit("cited_recommendation_draft_agent must keep advisory-only authority ceiling.")
allowed_tools = set(agent.get("allowed_tools", ()))
if "recommendation_draft" not in allowed_tools:
    raise SystemExit("cited_recommendation_draft_agent must use the registered recommendation_draft tool.")
unknown_tools = sorted(allowed_tools - set(registered_tools))
if unknown_tools:
    raise SystemExit(
        "cited_recommendation_draft_agent references unregistered tool(s): "
        + ", ".join(unknown_tools)
    )
draft_tool = registered_tools.get("recommendation_draft")
if not isinstance(draft_tool, dict):
    raise SystemExit("Missing registered recommendation_draft tool.")
unexpected_families = sorted(
    set(agent.get("record_families", ()))
    - set(draft_tool.get("allowed_record_families", ()))
)
if unexpected_families:
    raise SystemExit(
        "cited_recommendation_draft_agent declares record family outside "
        "recommendation_draft allowlist: "
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
            "cited_recommendation_draft_agent is missing disallowed tool: "
            + disallowed
        )
for disallowed in (
    "recommendation_truth",
    "workflow_completion",
    "production_write",
):
    if disallowed not in draft_tool.get("disallowed_authority", ()):
        raise SystemExit(
            "recommendation_draft tool is missing disallowed authority: "
            + disallowed
        )
PY

PYTHONPATH="${repo_root}/control-plane${PYTHONPATH:+:${PYTHONPATH}}" \
  python3 -m unittest control-plane.tests.test_phase60_6_cited_recommendation_draft_agent

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 60.6 cited recommendation draft artifact: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 60.6 cited recommendation draft agent is present with cited reviewable feedback, disabled/degraded fallback, prompt-pressure refusal, UI review context, and no workflow authority."
