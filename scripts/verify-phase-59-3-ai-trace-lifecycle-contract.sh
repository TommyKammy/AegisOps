#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-59-3-ai-trace-lifecycle-contract.md"
lifecycle_path="${repo_root}/docs/automation/ai-trace-lifecycle.json"
agent_registry_path="${repo_root}/docs/automation/ai-agent-registry.json"
tool_registry_path="${repo_root}/docs/automation/ai-tool-registry.json"
readme_path="${repo_root}/README.md"

required_doc_phrases=(
  "# Phase 59.3 AI Trace Lifecycle Contract"
  "- **Status**: Accepted lifecycle contract slice"
  "- **Related Issues**: #1252, #1255"
  "This contract defines the AI trace lifecycle states for created, reviewed, accepted, corrected, rejected, and expired traces before Phase 59 expands disabled or degraded mode, prompt fixtures, stale or conflicting evidence fixtures, trace queue UI/API implementation, closeout work, or Phase 60 daily AI operations."
  "Every AI trace lifecycle state must require registered agent linkage, registered tool linkage, citations, reviewed record family and identifier linkage, expiration handling, and advisory-only authority."
  'The executable lifecycle artifact lives in `docs/automation/ai-trace-lifecycle.json`.'
  "AI remains advisory, registered, audited, cited, and subordinate to reviewed AegisOps records."
  "No AI trace lifecycle state or transition may grant approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, or authority-widening capability."
  'This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.'
  'Run `bash scripts/verify-phase-59-3-ai-trace-lifecycle-contract.sh`.'
  'Run `bash scripts/test-verify-phase-59-3-ai-trace-lifecycle-contract.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1255 --config <supervisor-config-path>`.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 59.3 AI trace lifecycle contract doc: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${lifecycle_path}" ]]; then
  echo "Missing Phase 59.3 AI trace lifecycle artifact: ${lifecycle_path}" >&2
  exit 1
fi

if [[ ! -f "${agent_registry_path}" ]]; then
  echo "Missing Phase 59.3 AI agent registry dependency: ${agent_registry_path}" >&2
  exit 1
fi

if [[ ! -f "${tool_registry_path}" ]]; then
  echo "Missing Phase 59.3 AI tool registry dependency: ${tool_registry_path}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 59.3 AI trace lifecycle link check: ${readme_path}" >&2
  exit 1
fi

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 59.3 AI trace lifecycle contract statement: ${phrase}" >&2
    exit 1
  fi
done

python3 - "${lifecycle_path}" "${agent_registry_path}" "${tool_registry_path}" <<'PY'
import json
import re
import sys
from pathlib import Path
from collections import Counter

lifecycle_path = Path(sys.argv[1])
agent_registry_path = Path(sys.argv[2])
tool_registry_path = Path(sys.argv[3])
expected_schema_version = "2026-05-11.phase-59.3"


def require_non_empty_string(value, description: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{description} must be a non-empty string.")
    return value


def require_exact_value(value, expected, description: str) -> None:
    if value != expected:
        raise SystemExit(f"{description} must be {expected}.")


def require_non_empty_string_list(value, description: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise SystemExit(f"{description} must be a non-empty string list.")
    return value


def require_no_duplicate_strings(values: list[str], description: str) -> None:
    duplicates = sorted(item for item, count in Counter(values).items() if count > 1)
    if duplicates:
        raise SystemExit(
            f"{description} must not contain duplicate value(s): " + ", ".join(duplicates)
        )


def require_required_fields(row: dict, required: set[str], description: str) -> None:
    missing = sorted(required - row.keys())
    if missing:
        raise SystemExit(f"{description}: " + ", ".join(missing))


def require_exact_string_set(value, expected: set[str], description: str) -> list[str]:
    values = require_non_empty_string_list(value, description)
    require_no_duplicate_strings(values, description)
    actual = set(values)
    missing = sorted(expected - actual)
    if missing:
        raise SystemExit(f"{description} is missing field(s): " + ", ".join(missing))
    extra = sorted(actual - expected)
    if extra:
        raise SystemExit(f"{description} contains extra field(s): " + ", ".join(extra))
    return values


def require_allowed_from_for_state(
    state_name: str,
    value,
    known_states: set[str],
    expected_by_state: dict[str, list[str]],
) -> None:
    if not isinstance(value, list):
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {state_name} must include list allowed_from."
        )
    for predecessor in value:
        if not isinstance(predecessor, str) or not predecessor.strip():
            raise SystemExit(
                f"Phase 59.3 AI trace lifecycle state {state_name} allowed_from must contain state names."
            )
        if predecessor not in known_states:
            raise SystemExit(
                f"Phase 59.3 AI trace lifecycle state {state_name} references invalid allowed_from state: {predecessor}"
            )
    actual_allowed_from = sorted(value)
    expected_allowed_from = expected_by_state[state_name]
    if actual_allowed_from != expected_allowed_from:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {state_name} allowed_from must match transition graph: "
            + "expected "
            + ", ".join(expected_allowed_from or ["<none>"])
            + "; got "
            + ", ".join(actual_allowed_from or ["<none>"])
        )


def require_transition_boundary(
    index: int,
    from_state: str,
    to_state: str,
    known_states: set[str],
) -> None:
    if not {from_state, to_state}.issubset(known_states):
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle transition {index} references invalid state."
        )
    if from_state == "expired":
        raise SystemExit("Phase 59.3 AI trace lifecycle must not transition from expired traces.")
    to_state_is_review_outcome = to_state in {"accepted", "corrected", "rejected"}
    if to_state_is_review_outcome and from_state != "reviewed":
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle transition {from_state}->{to_state} must go through reviewed."
        )

try:
    lifecycle = json.loads(lifecycle_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid Phase 59.3 AI trace lifecycle JSON: {exc}") from exc

try:
    agent_registry = json.loads(agent_registry_path.read_text(encoding="utf-8"))
    tool_registry = json.loads(tool_registry_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid Phase 59.3 registry dependency JSON: {exc}") from exc

if not isinstance(lifecycle, dict):
    raise SystemExit("Phase 59.3 AI trace lifecycle artifact must be a JSON object.")

required_root = frozenset((
    "schema_version",
    "phase",
    "contract_status",
    "authority_boundary",
    "lifecycle_states",
    "allowed_transitions",
    "trace_review_queue_skeleton",
    "forbidden_authority_states",
))
require_required_fields(
    lifecycle,
    required_root,
    "Phase 59.3 AI trace lifecycle is missing root field(s)",
)

require_exact_value(
    lifecycle["phase"],
    "59.3",
    "Phase 59.3 AI trace lifecycle phase",
)
require_exact_value(
    lifecycle["schema_version"],
    expected_schema_version,
    "Phase 59.3 AI trace lifecycle schema_version",
)
require_exact_value(
    lifecycle["contract_status"],
    "accepted_contract_slice",
    "Phase 59.3 AI trace lifecycle status",
)

authority_boundary = require_non_empty_string(
    lifecycle["authority_boundary"],
    "Phase 59.3 AI trace lifecycle authority_boundary",
)
authority_boundary_lower = authority_boundary.casefold()
if (
    "subordinate" not in authority_boundary_lower
    or "aegisops records remain authoritative" not in authority_boundary_lower
):
    raise SystemExit(
        "Phase 59.3 AI trace lifecycle authority_boundary must preserve subordinate AegisOps authority semantics."
    )

states = lifecycle["lifecycle_states"]
if not isinstance(states, list) or not states:
    raise SystemExit("Phase 59.3 AI trace lifecycle states field must be a list.")

transitions = lifecycle["allowed_transitions"]
if not isinstance(transitions, list) or not transitions:
    raise SystemExit("Phase 59.3 AI trace lifecycle transitions field must be a list.")

registered_agents = {
    agent["agent_name"]
    for agent in agent_registry.get("agents", [])
    if isinstance(agent, dict) and isinstance(agent.get("agent_name"), str)
}
registered_tools = {
    tool["tool_name"]
    for tool in tool_registry.get("tools", [])
    if isinstance(tool, dict) and isinstance(tool.get("tool_name"), str)
}
if not registered_agents:
    raise SystemExit("Phase 59.3 registered agent dependency is empty.")
if not registered_tools:
    raise SystemExit("Phase 59.3 registered tool dependency is empty.")

required_states = {
    "created",
    "reviewed",
    "accepted",
    "corrected",
    "rejected",
    "expired",
}
required_transitions = {
    ("created", "reviewed"),
    ("created", "expired"),
    ("reviewed", "accepted"),
    ("reviewed", "corrected"),
    ("reviewed", "rejected"),
    ("reviewed", "expired"),
    ("accepted", "expired"),
    ("corrected", "expired"),
}
required_allowed_from_by_state = {
    state_name: sorted(
        from_state for from_state, to_state in required_transitions if to_state == state_name
    )
    for state_name in required_states
}
required_state_fields = {
    "state",
    "purpose",
    "allowed_from",
    "terminal",
    "registered_agents",
    "registered_tools",
    "required_linkage",
    "reviewer_action_metadata_required",
    "expiration_handling",
    "authority_effect",
    "disallowed_authority",
}
required_linkage_terms = frozenset((
    "registered_agent_name",
    "registered_tool_names",
    "trace_id",
    "reviewed_record_family",
    "reviewed_record_id",
    "citation_ids",
    "evidence_reference",
    "expires_at",
))
review_outcome_states = {"reviewed", "accepted", "corrected", "rejected"}
required_reviewer_terms = {"reviewer_id", "review_action_id"}
required_state_linkage_terms = {
    "created": {"created_by", "created_at", "expires_at"},
    "reviewed": {"reviewer_id", "review_action_id", "reviewed_at", "expires_at"},
    "accepted": {"reviewer_id", "review_action_id", "accepted_at", "expires_at"},
    "corrected": {
        "reviewer_id",
        "review_action_id",
        "correction_summary",
        "corrected_at",
        "expires_at",
    },
    "rejected": {
        "reviewer_id",
        "review_action_id",
        "rejection_reason",
        "rejected_at",
        "expires_at",
    },
    "expired": {"expires_at", "expired_at", "expiration_reason"},
}
required_forbidden_authority = {
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "production_write",
    "policy_bypass",
    "workflow_truth",
}
forbidden_claim_fragments = (
    "may_approve",
    "can_approve",
    "approve_action",
    "approve_actions",
    "approve_case",
    "approve_case_closure",
    "may_execute",
    "can_execute",
    "execute_action",
    "execute_actions",
    "may_reconcile",
    "can_reconcile",
    "reconcile_receipt",
    "reconcile_outcome",
    "may_close",
    "can_close",
    "close_case",
    "close_cases",
    "may_activate",
    "can_activate",
    "activate_detector",
    "activate_detectors",
    "create_source_truth",
    "source_truth",
    "workflow_truth",
    "authority_widen",
    "production_write",
    "policy_bypass",
    "bypass_policy",
)


def require_no_forbidden_authority_claim(
    value: str,
    description: str,
    allowed_value=None,
) -> None:
    lowered = re.sub(r"[^a-z0-9]+", "_", value.casefold()).strip("_")
    if any(fragment in lowered for fragment in forbidden_claim_fragments):
        if allowed_value is None or value != allowed_value:
            raise SystemExit(f"{description} contains forbidden authority claim.")


require_no_forbidden_authority_claim(
    authority_boundary,
    "Phase 59.3 AI trace lifecycle authority_boundary",
)


seen_states: set[str] = set()
states_by_name: dict[str, dict] = {}
for index, state in enumerate(states, start=1):
    if not isinstance(state, dict):
        raise SystemExit(f"Phase 59.3 AI trace lifecycle row {index} must be an object.")

    missing = sorted(required_state_fields - state.keys())
    if missing:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle row {index} is missing field(s): "
            + ", ".join(missing)
        )

    name = state["state"]
    if not isinstance(name, str) or not name.strip():
        raise SystemExit(f"Phase 59.3 AI trace lifecycle row {index} has invalid state.")
    if name in seen_states:
        raise SystemExit(f"Duplicate Phase 59.3 AI trace lifecycle state: {name}")
    if name not in required_states:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle contains unexpected state for this slice: {name}"
        )
    seen_states.add(name)
    states_by_name[name] = state

    for field in ("purpose", "expiration_handling", "authority_effect"):
        value = require_non_empty_string(
            state[field],
            f"Phase 59.3 AI trace lifecycle state {name} {field}",
        )
        require_no_forbidden_authority_claim(
            value,
            f"Phase 59.3 AI trace lifecycle state {name} {field}",
            allowed_value="advisory_only_no_workflow_mutation",
        )

    if state["authority_effect"] != "advisory_only_no_workflow_mutation":
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {name} must keep advisory-only authority."
        )

    require_allowed_from_for_state(
        name,
        state["allowed_from"],
        required_states,
        required_allowed_from_by_state,
    )
    if not isinstance(state["terminal"], bool):
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {name} terminal must be boolean."
        )
    if not isinstance(state["reviewer_action_metadata_required"], bool):
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {name} reviewer metadata flag must be boolean."
        )

    for field in ("registered_agents", "registered_tools", "required_linkage", "disallowed_authority"):
        values = require_non_empty_string_list(
            state[field],
            f"Phase 59.3 AI trace lifecycle state {name} {field}",
        )
        require_no_duplicate_strings(
            values,
            f"Phase 59.3 AI trace lifecycle state {name} {field}",
        )

    unknown_agents = sorted(set(state["registered_agents"]) - registered_agents)
    if unknown_agents:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {name} references unregistered agent(s): "
            + ", ".join(unknown_agents)
        )

    unknown_tools = sorted(set(state["registered_tools"]) - registered_tools)
    if unknown_tools:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {name} references unregistered tool(s): "
            + ", ".join(unknown_tools)
        )

    linkage_terms = set(state["required_linkage"])
    missing_linkage = sorted(required_linkage_terms - linkage_terms)
    if missing_linkage:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {name} is missing linkage field(s): "
            + ", ".join(missing_linkage)
        )
    missing_state_linkage = sorted(required_state_linkage_terms[name] - linkage_terms)
    if missing_state_linkage:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {name} is missing state-specific linkage field(s): "
            + ", ".join(missing_state_linkage)
        )

    if name in review_outcome_states:
        if not state["reviewer_action_metadata_required"]:
            raise SystemExit(
                f"Phase 59.3 AI trace lifecycle state {name} must require reviewer/action metadata."
            )
        missing_reviewer = sorted(required_reviewer_terms - linkage_terms)
        if missing_reviewer:
            raise SystemExit(
                f"Phase 59.3 AI trace lifecycle state {name} is missing reviewer metadata field(s): "
                + ", ".join(missing_reviewer)
            )

    missing_disallowed = sorted(
        required_forbidden_authority - set(state["disallowed_authority"])
    )
    if missing_disallowed:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {name} is missing disallowed authority: "
            + ", ".join(missing_disallowed)
        )

missing_states = sorted(required_states - seen_states)
unexpected_states = sorted(seen_states - required_states)
if missing_states:
    raise SystemExit(
        "Phase 59.3 AI trace lifecycle is missing required state(s): "
        + ", ".join(missing_states)
    )
if unexpected_states:
    raise SystemExit(
        "Phase 59.3 AI trace lifecycle contains unexpected state(s) for this slice: "
        + ", ".join(unexpected_states)
    )

transition_rows_by_pair: dict[tuple[str, str], int] = {}
required_transition_fields = {
    "from_state",
    "to_state",
    "required_trigger",
    "required_metadata",
    "authority_effect",
}
required_transition_metadata_terms = {
    ("created", "reviewed"): {"reviewer_id", "review_action_id", "reviewed_at"},
    ("created", "expired"): {"expires_at", "expired_at", "expiration_reason"},
    ("reviewed", "accepted"): {"reviewer_id", "review_action_id", "accepted_at"},
    ("reviewed", "corrected"): {
        "reviewer_id",
        "review_action_id",
        "correction_summary",
        "corrected_at",
    },
    ("reviewed", "rejected"): {
        "reviewer_id",
        "review_action_id",
        "rejection_reason",
        "rejected_at",
    },
    ("reviewed", "expired"): {"expires_at", "expired_at", "expiration_reason"},
    ("accepted", "expired"): {"expires_at", "expired_at", "expiration_reason"},
    ("corrected", "expired"): {"expires_at", "expired_at", "expiration_reason"},
}

for index, transition in enumerate(transitions, start=1):
    if not isinstance(transition, dict):
        raise SystemExit(f"Phase 59.3 AI trace lifecycle transition {index} must be an object.")
    require_required_fields(
        transition,
        required_transition_fields,
        f"Phase 59.3 AI trace lifecycle transition {index} is missing field(s)",
    )

    from_state = transition["from_state"]
    to_state = transition["to_state"]
    transition_pair = (from_state, to_state)
    require_transition_boundary(index, from_state, to_state, required_states)
    if transition_pair not in required_transitions:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle contains unexpected transition for this slice: {from_state}->{to_state}"
        )
    if transition_pair in transition_rows_by_pair:
        raise SystemExit(
            f"Duplicate Phase 59.3 AI trace lifecycle transition: {from_state}->{to_state}"
        )

    trigger = require_non_empty_string(
        transition["required_trigger"],
        f"Phase 59.3 AI trace lifecycle transition {from_state}->{to_state} required_trigger",
    )
    require_no_forbidden_authority_claim(
        trigger,
        f"Phase 59.3 AI trace lifecycle transition {from_state}->{to_state} required_trigger",
    )

    if transition["authority_effect"] != "advisory_only_no_workflow_mutation":
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle transition {from_state}->{to_state} must keep advisory-only authority."
        )

    metadata = require_non_empty_string_list(
        transition["required_metadata"],
        f"Phase 59.3 AI trace lifecycle transition {from_state}->{to_state} required_metadata",
    )
    require_no_duplicate_strings(
        metadata,
        f"Phase 59.3 AI trace lifecycle transition {from_state}->{to_state} required_metadata",
    )

    required_metadata_terms = required_transition_metadata_terms[transition_pair]
    missing_transition_metadata = sorted(required_metadata_terms - set(metadata))
    if missing_transition_metadata:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle transition {from_state}->{to_state} is missing transition-specific metadata: "
            + ", ".join(missing_transition_metadata)
        )

    transition_rows_by_pair[transition_pair] = index

seen_transitions = set(transition_rows_by_pair)
missing_transitions = sorted(required_transitions - seen_transitions)
unexpected_transitions = sorted(seen_transitions - required_transitions)
if missing_transitions:
    raise SystemExit(
        "Phase 59.3 AI trace lifecycle is missing required transition(s): "
        + ", ".join(f"{src}->{dst}" for src, dst in missing_transitions)
    )
if unexpected_transitions:
    raise SystemExit(
        "Phase 59.3 AI trace lifecycle contains unexpected transition(s) for this slice: "
        + ", ".join(f"{src}->{dst}" for src, dst in unexpected_transitions)
    )
for state_name in sorted(required_states):
    expected_allowed_from = sorted(
        from_state for from_state, to_state in seen_transitions if to_state == state_name
    )
    actual_allowed_from = sorted(states_by_name[state_name]["allowed_from"])
    if actual_allowed_from != expected_allowed_from:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {state_name} allowed_from must match transition graph: "
            + "expected "
            + ", ".join(expected_allowed_from or ["<none>"])
            + "; got "
            + ", ".join(actual_allowed_from or ["<none>"])
        )

    has_outgoing_transition = any(
        from_state == state_name for from_state, _to_state in seen_transitions
    )
    if has_outgoing_transition and states_by_name[state_name]["terminal"]:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {state_name} terminal flag must be false while outgoing transitions exist."
        )
    if not has_outgoing_transition and not states_by_name[state_name]["terminal"]:
        raise SystemExit(
            f"Phase 59.3 AI trace lifecycle state {state_name} terminal flag must be true when no outgoing transitions exist."
        )

queue = lifecycle["trace_review_queue_skeleton"]
if not isinstance(queue, dict):
    raise SystemExit("Phase 59.3 trace review queue skeleton must be an object.")
if queue.get("phase") != "59.7":
    raise SystemExit("Phase 59.3 trace review queue skeleton must point to Phase 59.7.")
if queue.get("implementation_status") != "deferred_skeleton_only":
    raise SystemExit(
        "Phase 59.3 trace review queue skeleton must remain deferred_skeleton_only."
    )
required_queue_fields = {
    "trace_id",
    "state",
    "reviewed_record_family",
    "reviewed_record_id",
    "registered_agent_name",
    "registered_tool_names",
    "citation_ids",
    "expires_at",
    "review_required",
}
require_exact_string_set(
    queue.get("required_fields"),
    required_queue_fields,
    "Phase 59.3 trace review queue skeleton required_fields",
)

required_non_authoritative_surfaces = {
    "queue_order",
    "badge_text",
    "cache_state",
    "browser_state",
    "trace_state",
}
require_exact_string_set(
    queue.get("non_authoritative_surfaces"),
    required_non_authoritative_surfaces,
    "Phase 59.3 trace review queue skeleton non_authoritative_surfaces",
)

require_exact_string_set(
    lifecycle["forbidden_authority_states"],
    required_forbidden_authority,
    "Phase 59.3 AI trace lifecycle forbidden_authority_states",
)
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 59.3 AI trace lifecycle artifact: workstation-local absolute path detected" >&2
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

if ! grep -Eq '\[[^]]+\]\(docs/phase-59-3-ai-trace-lifecycle-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 59.3 AI trace lifecycle contract." >&2
  exit 1
fi

echo "Phase 59.3 AI trace lifecycle contract is present with required states, registered linkage, citations, review metadata, expiration handling, and advisory-only authority ceilings."
