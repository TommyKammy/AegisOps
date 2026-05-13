#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-60-4-evidence-gap-detector-agent.md"
module_path="${repo_root}/control-plane/aegisops/control_plane/assistant/evidence_gap_detector.py"
test_path="${repo_root}/control-plane/tests/test_phase60_4_evidence_gap_detector_agent.py"
agent_registry_path="${repo_root}/docs/automation/ai-agent-registry.json"
tool_registry_path="${repo_root}/docs/automation/ai-tool-registry.json"

for path in "${doc_path}" "${module_path}" "${test_path}" "${agent_registry_path}" "${tool_registry_path}"; do
  if [[ ! -f "${path}" ]]; then
    echo "Missing Phase 60.4 evidence gap detector artifact: ${path}" >&2
    exit 1
  fi
done

required_doc_phrases=(
  "# Phase 60.4 Evidence Gap Detector Agent"
  "identifies missing identity owner, stale source health, receipt present but reconciliation missing, evidence conflict, and missing citation gaps"
  "without changing source health, receipt state, reconciliation state, evidence truth, case truth, approval state, execution state, or workflow routing"
  "The runtime entry point is \`aegisops.control_plane.assistant.evidence_gap_detector.build_evidence_gap_detector\`."
  "The agent must not approve actions, execute actions, reconcile outcomes, close cases, activate detectors, create source truth, create evidence truth, select truth between conflicting records, suppress uncertainty, hide citations, or treat detector output as workflow truth."
  "If AI advisory posture is disabled or degraded, the agent returns bounded fallback output."
  "If reviewed evidence payloads are missing, malformed, uncited, mismatched, AI-created truth, unsupported, or contract-mismatched, the agent fails closed with explicit unresolved reasons rather than inventing review posture."
  "Prompt pressure to approve, execute, reconcile, close, activate detectors, create source truth, create evidence truth, bypass policy, hide citations, suppress uncertainty, choose authoritative truth, mark source health current, or mark evidence gaps resolved must be blocked."
  "Run \`python3 -m unittest control-plane.tests.test_phase60_4_evidence_gap_detector_agent\`."
  "Run \`bash scripts/verify-phase-60-4-evidence-gap-detector-agent.sh\`."
  "Run \`bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh\`."
  "Run \`bash scripts/verify-publishable-path-hygiene.sh\`."
  "Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1273 --config <supervisor-config-path>\`."
)

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 60.4 evidence gap detector contract statement: ${phrase}" >&2
    exit 1
  fi
done

required_module_phrases=(
  "_REGISTERED_AGENT_NAME = \"evidence_gap_detector_agent\""
  "_AGENT_NAME = _REGISTERED_AGENT_NAME"
  "_TOOL_NAME = \"evidence_gap_detector\""
  "\"authoritative_workflow_truth\": False"
  "\"mutates_authoritative_records\": False"
  "\"creates_evidence_truth\": False"
  "\"advances_reconciliation\": False"
  "\"trace_creation_allowed\": False"
  "\"authority_boundary\": \"cited_advisory_evidence_gap_detector_only\""
  "\"decision\": \"blocked\""
  "mode=\"ai_disabled\""
  "mode=\"ai_degraded\""
  "mode=\"evidence_gap_review_untrusted\""
  "\"missing_identity_owner\""
  "\"stale_source_health\""
  "\"receipt_without_reconciliation\""
  "\"evidence_conflict\""
  "\"missing_citation\""
  "\"truth_selection_attempt\""
  "\"evidence_gap_resolution_attempt\""
)

for phrase in "${required_module_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${module_path}"; then
    echo "Missing Phase 60.4 evidence gap detector implementation guard: ${phrase}" >&2
    exit 1
  fi
done

required_test_phrases=(
  "test_detector_surfaces_review_needed_gaps_with_citations"
  "test_mismatched_record_family_and_ai_created_truth_fail_closed"
  "test_uncited_review_payload_fails_closed_without_record_citation_leak"
  "test_prompt_pressure_to_resolve_or_hide_evidence_gaps_is_blocked"
  "test_ai_disabled_or_degraded_returns_non_ai_review_fallback"
  "missing_identity_owner"
  "stale_source_health"
  "receipt_without_reconciliation"
  "evidence_conflict"
  "missing_citation"
)

for phrase in "${required_test_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${test_path}"; then
    echo "Missing Phase 60.4 evidence gap detector focused test guard: ${phrase}" >&2
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
agent = agents.get("evidence_gap_detector_agent")
if not isinstance(agent, dict):
    raise SystemExit("Missing evidence_gap_detector_agent registry row.")
if agent.get("authority_ceiling") != "advisory_only_subordinate_to_aegisops_records":
    raise SystemExit("evidence_gap_detector_agent must keep advisory-only authority ceiling.")
allowed_tools = set(agent.get("allowed_tools", ()))
if "evidence_gap_detector" not in allowed_tools:
    raise SystemExit("evidence_gap_detector_agent must use the registered evidence_gap_detector tool.")
unknown_tools = sorted(allowed_tools - set(registered_tools))
if unknown_tools:
    raise SystemExit(
        "evidence_gap_detector_agent references unregistered tool(s): "
        + ", ".join(unknown_tools)
    )
detector_tool = registered_tools.get("evidence_gap_detector")
if not isinstance(detector_tool, dict):
    raise SystemExit("Missing registered evidence_gap_detector tool.")
unexpected_families = sorted(
    set(agent.get("record_families", ()))
    - set(detector_tool.get("allowed_record_families", ()))
)
if unexpected_families:
    raise SystemExit(
        "evidence_gap_detector_agent declares record family outside "
        "evidence_gap_detector allowlist: "
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
            "evidence_gap_detector_agent is missing disallowed tool: "
            + disallowed
        )
for disallowed in (
    "evidence_truth_creation",
    "conflict_resolution",
    "production_write",
):
    if disallowed not in detector_tool.get("disallowed_authority", ()):
        raise SystemExit(
            "evidence_gap_detector tool is missing disallowed authority: "
            + disallowed
        )
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 60.4 evidence gap detector artifact: workstation-local absolute path detected" >&2
  exit 1
fi

echo "Phase 60.4 evidence gap detector agent is present with cited review-needed output, disabled/degraded fallback, prompt-pressure refusal, and no workflow authority."
