#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-59-1-agent-registry-contract.md"
registry_path="${repo_root}/docs/automation/ai-agent-registry.json"
readme_path="${repo_root}/README.md"

required_doc_phrases=(
  "# Phase 59.1 Agent Registry Contract"
  "- **Status**: Accepted registry contract slice"
  "- **Related Issues**: #1252, #1253"
  "This contract defines the required registry fields for every AegisOps AI agent before Phase 59 expands tool registry, trace lifecycle, disabled or degraded mode, prompt fixtures, stale or conflicting evidence fixtures, trace queue, or closeout work."
  "Every registry row must include agent name, purpose, allowed tools, disallowed tools, record families, citation requirements, and authority ceiling."
  'The executable registry lives in `docs/automation/ai-agent-registry.json`.'
  "AI remains advisory, registered, audited, cited, and subordinate to reviewed AegisOps records."
  "No agent registry row may grant approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, or authority-widening capability."
  'This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.'
  'Run `bash scripts/verify-phase-59-1-agent-registry-contract.sh`.'
  'Run `bash scripts/test-verify-phase-59-1-agent-registry-contract.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1253 --config <supervisor-config-path>`.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 59.1 agent registry contract doc: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${registry_path}" ]]; then
  echo "Missing Phase 59.1 AI agent registry: ${registry_path}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 59.1 agent registry link check: ${readme_path}" >&2
  exit 1
fi

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 59.1 agent registry contract statement: ${phrase}" >&2
    exit 1
  fi
done

python3 - "${registry_path}" <<'PY'
import json
import re
import sys
from pathlib import Path

registry_path = Path(sys.argv[1])
try:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid Phase 59.1 AI agent registry JSON: {exc}") from exc

if not isinstance(registry, dict):
    raise SystemExit("Phase 59.1 AI agent registry must be a JSON object.")

required_root = {
    "schema_version",
    "phase",
    "registry_status",
    "authority_boundary",
    "agents",
}
missing_root = sorted(required_root - registry.keys())
if missing_root:
    raise SystemExit(
        "Phase 59.1 AI agent registry is missing root field(s): "
        + ", ".join(missing_root)
    )

if registry["phase"] != "59.1":
    raise SystemExit("Phase 59.1 AI agent registry phase must be 59.1.")

if registry["registry_status"] != "accepted_contract_slice":
    raise SystemExit(
        "Phase 59.1 AI agent registry status must be accepted_contract_slice."
    )

agents = registry["agents"]
if not isinstance(agents, list):
    raise SystemExit("Phase 59.1 AI agent registry agents field must be a list.")
if not agents:
    raise SystemExit(
        "Phase 59.1 AI agent registry must contain the required initial agent set."
    )

required_agent_names = {
    "analyst_assistant_context_agent",
    "live_assistant_summary_agent",
    "advisory_action_request_drafting_agent",
    "today_focus_advisory_agent",
    "setup_doctor_explanation_agent",
}
required_agent_fields = {
    "agent_name",
    "purpose",
    "allowed_tools",
    "disallowed_tools",
    "record_families",
    "citation_requirements",
    "authority_ceiling",
}
required_disallowed = {
    "approve_action",
    "execute_action",
    "reconcile_execution",
    "close_case",
    "activate_detector",
    "create_source_truth",
    "bypass_policy",
}


def normalize_tool_name(tool_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", tool_name.lower()).strip("_")


forbidden_authority_terms = (
    "approve",
    "approval",
    "execute",
    "execution",
    "reconcile",
    "reconciliation",
    "close_case",
    "case_closure",
    "activate_detector",
    "detector_activation",
    "source_truth",
    "production_write",
    "bypass_policy",
    "policy-bypass",
    "policy_bypass",
    "policy bypass",
    "authority_widening",
)
forbidden_allowed_tool_fragments = frozenset(
    normalize_tool_name(term) for term in forbidden_authority_terms
)

seen_names: set[str] = set()
for index, agent in enumerate(agents, start=1):
    if not isinstance(agent, dict):
        raise SystemExit(f"Phase 59.1 AI agent row {index} must be an object.")

    missing = sorted(required_agent_fields - agent.keys())
    if missing:
        raise SystemExit(
            f"Phase 59.1 AI agent row {index} is missing field(s): "
            + ", ".join(missing)
        )

    name = agent["agent_name"]
    if not isinstance(name, str) or not name.strip():
        raise SystemExit(f"Phase 59.1 AI agent row {index} has invalid agent_name.")
    if name in seen_names:
        raise SystemExit(f"Duplicate Phase 59.1 AI agent name: {name}")
    seen_names.add(name)

    for field in ("purpose", "authority_ceiling"):
        value = agent[field]
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(
                f"Phase 59.1 AI agent {name} has invalid {field}."
            )

    if agent["authority_ceiling"] != "advisory_only_subordinate_to_aegisops_records":
        raise SystemExit(
            f"Phase 59.1 AI agent {name} must keep the advisory-only authority ceiling."
        )

    for field in (
        "allowed_tools",
        "disallowed_tools",
        "record_families",
        "citation_requirements",
    ):
        values = agent[field]
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
        ):
            raise SystemExit(
                f"Phase 59.1 AI agent {name} must include non-empty string list {field}."
            )

    disallowed = set(agent["disallowed_tools"])
    missing_disallowed = sorted(required_disallowed - disallowed)
    if missing_disallowed:
        raise SystemExit(
            f"Phase 59.1 AI agent {name} is missing disallowed tool(s): "
            + ", ".join(missing_disallowed)
        )

    for allowed_tool in agent["allowed_tools"]:
        normalized = normalize_tool_name(allowed_tool)
        for fragment in forbidden_allowed_tool_fragments:
            if fragment in normalized:
                raise SystemExit(
                    f"Phase 59.1 AI agent {name} has forbidden allowed tool: {allowed_tool}"
                )

    citation_terms = " ".join(agent["citation_requirements"]).lower()
    for required_term in ("record_family", "record_id", "evidence_reference"):
        if required_term not in citation_terms:
            raise SystemExit(
                f"Phase 59.1 AI agent {name} citation requirements must include {required_term}."
            )

missing_required_agents = sorted(required_agent_names - seen_names)
unexpected_agents = sorted(seen_names - required_agent_names)
if missing_required_agents:
    raise SystemExit(
        "Phase 59.1 AI agent registry is missing required agent(s): "
        + ", ".join(missing_required_agents)
    )
if unexpected_agents:
    raise SystemExit(
        "Phase 59.1 AI agent registry contains unexpected agent(s) for this slice: "
        + ", ".join(unexpected_agents)
    )
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 59.1 agent registry artifact: workstation-local absolute path detected" >&2
  exit 1
fi

readme_rendered_markdown="$(
  awk '
    /^[[:space:]]*(```|~~~)/ {
      in_fenced_block = !in_fenced_block
      next
    }
    !in_fenced_block { print }
  ' "${readme_path}" | perl -pe 's/`[^`]*`//g'
)"

if ! grep -Eq '\[[^]]+\]\(docs/phase-59-1-agent-registry-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 59.1 agent registry contract." >&2
  exit 1
fi

echo "Phase 59.1 AI agent registry contract is present with required fields, citations, and advisory-only authority ceilings."
