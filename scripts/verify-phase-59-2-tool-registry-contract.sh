#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-59-2-tool-registry-contract.md"
registry_path="${repo_root}/docs/automation/ai-tool-registry.json"
readme_path="${repo_root}/README.md"

required_doc_phrases=(
  "# Phase 59.2 Tool Registry Contract"
  "- **Status**: Accepted registry contract slice"
  "- **Related Issues**: #1252, #1254"
  "This contract defines the required registry fields for every AegisOps AI tool before Phase 59 expands trace lifecycle, disabled or degraded mode, prompt fixtures, stale or conflicting evidence fixtures, trace queue, closeout work, or Phase 60 daily AI operations."
  "Every tool registry row must include tool name, purpose, allowed record families, required citations, audit fields, disallowed authority, and authority ceiling."
  'The executable registry lives in `docs/automation/ai-tool-registry.json`.'
  "AI remains advisory, registered, audited, cited, and subordinate to reviewed AegisOps records."
  "No tool registry row may grant approval, execution, reconciliation, case-closure, detector-activation, source-truth, production write, policy-bypass, or authority-widening capability."
  'This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.'
  'Run `bash scripts/verify-phase-59-2-tool-registry-contract.sh`.'
  'Run `bash scripts/test-verify-phase-59-2-tool-registry-contract.sh`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1254 --config <supervisor-config-path>`.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 59.2 tool registry contract doc: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${registry_path}" ]]; then
  echo "Missing Phase 59.2 AI tool registry: ${registry_path}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 59.2 tool registry link check: ${readme_path}" >&2
  exit 1
fi

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 59.2 tool registry contract statement: ${phrase}" >&2
    exit 1
  fi
done

python3 - "${registry_path}" <<'PY'
import json
import sys
from pathlib import Path

registry_path = Path(sys.argv[1])
try:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid Phase 59.2 AI tool registry JSON: {exc}") from exc

if not isinstance(registry, dict):
    raise SystemExit("Phase 59.2 AI tool registry must be a JSON object.")

required_root = {
    "schema_version",
    "phase",
    "registry_status",
    "authority_boundary",
    "tools",
}
missing_root = sorted(required_root - registry.keys())
if missing_root:
    raise SystemExit(
        "Phase 59.2 AI tool registry is missing root field(s): "
        + ", ".join(missing_root)
    )

if registry["phase"] != "59.2":
    raise SystemExit("Phase 59.2 AI tool registry phase must be 59.2.")

if registry["registry_status"] != "accepted_contract_slice":
    raise SystemExit(
        "Phase 59.2 AI tool registry status must be accepted_contract_slice."
    )

tools = registry["tools"]
if not isinstance(tools, list):
    raise SystemExit("Phase 59.2 AI tool registry tools field must be a list.")
if not tools:
    raise SystemExit(
        "Phase 59.2 AI tool registry must contain the required initial tool set."
    )

required_tool_names = {
    "safe_query",
    "evidence_lookup",
    "source_health_lookup",
    "runbook_lookup",
    "recommendation_draft",
    "action_request_draft",
    "doctor_explanation",
}
required_tool_fields = {
    "tool_name",
    "purpose",
    "allowed_record_families",
    "required_citations",
    "audit_fields",
    "disallowed_authority",
    "authority_ceiling",
}
required_audit_fields = {
    "tool_name",
    "agent_name",
    "trace_id",
    "requested_by",
    "record_family",
    "record_id",
    "citation_ids",
    "decision",
    "timestamp",
}
required_disallowed_authority = {
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "production_write",
    "policy_bypass",
}

seen_names: set[str] = set()
for index, tool in enumerate(tools, start=1):
    if not isinstance(tool, dict):
        raise SystemExit(f"Phase 59.2 AI tool row {index} must be an object.")

    missing = sorted(required_tool_fields - tool.keys())
    if missing:
        raise SystemExit(
            f"Phase 59.2 AI tool row {index} is missing field(s): "
            + ", ".join(missing)
        )

    name = tool["tool_name"]
    if not isinstance(name, str) or not name.strip():
        raise SystemExit(f"Phase 59.2 AI tool row {index} has invalid tool_name.")
    if name in seen_names:
        raise SystemExit(f"Duplicate Phase 59.2 AI tool name: {name}")
    seen_names.add(name)

    for field in ("purpose", "authority_ceiling"):
        value = tool[field]
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"Phase 59.2 AI tool {name} has invalid {field}.")

    if tool["authority_ceiling"] != "advisory_only_subordinate_to_aegisops_records":
        raise SystemExit(
            f"Phase 59.2 AI tool {name} must keep the advisory-only authority ceiling."
        )

    for field in (
        "allowed_record_families",
        "required_citations",
        "audit_fields",
        "disallowed_authority",
    ):
        values = tool[field]
        if (
            not isinstance(values, list)
            or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
        ):
            raise SystemExit(
                f"Phase 59.2 AI tool {name} must include non-empty string list {field}."
            )

    missing_audit = sorted(required_audit_fields - set(tool["audit_fields"]))
    if missing_audit:
        raise SystemExit(
            f"Phase 59.2 AI tool {name} is missing audit field(s): "
            + ", ".join(missing_audit)
        )

    missing_disallowed = sorted(
        required_disallowed_authority - set(tool["disallowed_authority"])
    )
    if missing_disallowed:
        raise SystemExit(
            f"Phase 59.2 AI tool {name} is missing disallowed authority: "
            + ", ".join(missing_disallowed)
        )

    citation_terms = " ".join(tool["required_citations"]).lower()
    for required_term in ("record_family", "record_id", "evidence_reference"):
        if required_term not in citation_terms:
            raise SystemExit(
                f"Phase 59.2 AI tool {name} citation requirements must include {required_term}."
            )

missing_required_tools = sorted(required_tool_names - seen_names)
unexpected_tools = sorted(seen_names - required_tool_names)
if missing_required_tools:
    raise SystemExit(
        "Phase 59.2 AI tool registry is missing required tool(s): "
        + ", ".join(missing_required_tools)
    )
if unexpected_tools:
    raise SystemExit(
        "Phase 59.2 AI tool registry contains unexpected tool(s) for this slice: "
        + ", ".join(unexpected_tools)
    )
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 59.2 tool registry artifact: workstation-local absolute path detected" >&2
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

if ! grep -Eq '\[[^]]+\]\(docs/phase-59-2-tool-registry-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 59.2 tool registry contract." >&2
  exit 1
fi

echo "Phase 59.2 AI tool registry contract is present with required fields, citations, audit fields, and advisory-only authority ceilings."
