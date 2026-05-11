#!/usr/bin/env bash

set -euo pipefail

tool_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
repo_root="${1:-${tool_root}}"
doc_path="${repo_root}/docs/phase-59-4-ai-disabled-degraded-mode-contract.md"
contract_path="${repo_root}/docs/automation/ai-disabled-degraded-mode-contract.json"
readme_path="${repo_root}/README.md"

required_doc_phrases=(
  "# Phase 59.4 AI Disabled And Degraded Mode Contract"
  "- **Status**: Accepted disabled and degraded mode contract slice"
  "- **Related Issues**: #1252, #1256"
  "This contract defines the AI disabled and degraded mode behavior before Phase 59 expands prompt fixtures, stale or conflicting evidence fixtures, trace queue UI/API implementation, closeout work, or Phase 60 daily AI operations."
  "Every disabled or degraded mode row must include mode, trigger, operator state, readiness posture, blocked AI generation flags, reason, explanation, safe next steps, authority effect, and disallowed authority."
  'The executable mode artifact lives in `docs/automation/ai-disabled-degraded-mode-contract.json`.'
  "AI remains advisory, registered, audited, cited, and subordinate to reviewed AegisOps records when available, and it produces no recommendations, action drafts, or trace state when disabled or degraded."
  "Disabled and degraded AI posture must not block queue, case, evidence review, action review, reconciliation, doctor/supportability explanation fallback, or admin enablement posture surfaces that use authoritative AegisOps records."
  'This slice cites the Phase 51.6 authority-boundary negative-test policy in `docs/phase-51-6-authority-boundary-negative-test-policy.md` for AI approval, execution, reconciliation, case closure, detector activation, and source-truth refusal.'
  'Run `bash scripts/verify-phase-59-4-ai-disabled-degraded-mode-contract.sh`.'
  'Run `bash scripts/test-verify-phase-59-4-ai-disabled-degraded-mode-contract.sh`.'
  'Run `python3 -m unittest control-plane.tests.test_phase57_7_ai_enablement_admin_toggle`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1256 --config <supervisor-config-path>`.'
)

if [[ ! -f "${doc_path}" ]]; then
  echo "Missing Phase 59.4 AI disabled/degraded mode contract doc: ${doc_path}" >&2
  exit 1
fi

if [[ ! -f "${contract_path}" ]]; then
  echo "Missing Phase 59.4 AI disabled/degraded mode artifact: ${contract_path}" >&2
  exit 1
fi

if [[ ! -f "${readme_path}" ]]; then
  echo "Missing README for Phase 59.4 AI disabled/degraded mode link check: ${readme_path}" >&2
  exit 1
fi

for phrase in "${required_doc_phrases[@]}"; do
  if ! grep -Fq -- "${phrase}" "${doc_path}"; then
    echo "Missing Phase 59.4 AI disabled/degraded mode contract statement: ${phrase}" >&2
    exit 1
  fi
done

python3 - "${contract_path}" <<'PY'
import json
import sys
from pathlib import Path

contract_path = Path(sys.argv[1])
try:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
except json.JSONDecodeError as exc:
    raise SystemExit(f"Invalid Phase 59.4 AI disabled/degraded mode JSON: {exc}") from exc

if not isinstance(contract, dict):
    raise SystemExit("Phase 59.4 AI disabled/degraded mode artifact must be a JSON object.")

required_root = {
    "schema_version",
    "phase",
    "contract_status",
    "authority_boundary",
    "modes",
    "non_ai_workflow_surfaces",
    "blocked_ai_outputs",
    "operator_copy_rules",
}
missing_root = sorted(required_root - contract.keys())
if missing_root:
    raise SystemExit(
        "Phase 59.4 AI disabled/degraded mode artifact is missing root field(s): "
        + ", ".join(missing_root)
    )

if contract["schema_version"] != "2026-05-11.phase-59.4":
    raise SystemExit("Phase 59.4 AI disabled/degraded mode schema_version is incorrect.")
if contract["phase"] != "59.4":
    raise SystemExit("Phase 59.4 AI disabled/degraded mode phase must be 59.4.")
if contract["contract_status"] != "accepted_contract_slice":
    raise SystemExit(
        "Phase 59.4 AI disabled/degraded mode status must be accepted_contract_slice."
    )

boundary = contract["authority_boundary"]
if not isinstance(boundary, str) or not boundary.strip():
    raise SystemExit("Phase 59.4 AI disabled/degraded mode authority_boundary is invalid.")
boundary_lower = boundary.casefold()
if "subordinate" not in boundary_lower or "aegisops records remain authoritative" not in boundary_lower:
    raise SystemExit(
        "Phase 59.4 AI disabled/degraded mode authority boundary must preserve subordinate AegisOps authority semantics."
    )

required_modes = {"disabled", "degraded"}
required_mode_fields = {
    "mode",
    "trigger",
    "operator_state",
    "readiness_posture",
    "reason",
    "explanation",
    "safe_next_steps",
    "ai_generation_allowed",
    "trace_creation_allowed",
    "recommendation_generation_allowed",
    "action_draft_generation_allowed",
    "authority_effect",
    "disallowed_authority",
}
required_disallowed = {
    "approval",
    "execution",
    "reconciliation",
    "case_closure",
    "detector_activation",
    "source_truth_creation",
    "automatic_repair",
    "production_write",
    "policy_bypass",
    "workflow_truth",
}

def require_non_empty_string(value, description: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{description} must be a non-empty string.")
    return value

def require_non_empty_string_list(value, description: str) -> list[str]:
    if (
        not isinstance(value, list)
        or not value
        or any(not isinstance(item, str) or not item.strip() for item in value)
    ):
        raise SystemExit(f"{description} must be a non-empty string list.")
    return value

modes = contract["modes"]
if not isinstance(modes, list):
    raise SystemExit("Phase 59.4 AI disabled/degraded mode modes field must be a list.")

seen_modes: set[str] = set()
for index, mode in enumerate(modes, start=1):
    if not isinstance(mode, dict):
        raise SystemExit(f"Phase 59.4 AI mode row {index} must be an object.")
    missing = sorted(required_mode_fields - mode.keys())
    if missing:
        raise SystemExit(
            f"Phase 59.4 AI mode row {index} is missing field(s): "
            + ", ".join(missing)
        )
    mode_name = require_non_empty_string(mode["mode"], f"Phase 59.4 AI mode row {index} mode")
    if mode_name in seen_modes:
        raise SystemExit(f"Duplicate Phase 59.4 AI mode: {mode_name}")
    seen_modes.add(mode_name)
    for field in ("trigger", "operator_state", "readiness_posture", "reason", "explanation", "authority_effect"):
        require_non_empty_string(mode[field], f"Phase 59.4 AI mode {mode_name} {field}")
    require_non_empty_string_list(mode["safe_next_steps"], f"Phase 59.4 AI mode {mode_name} safe_next_steps")
    for field in (
        "ai_generation_allowed",
        "trace_creation_allowed",
        "recommendation_generation_allowed",
        "action_draft_generation_allowed",
    ):
        if mode[field] is not False:
            raise SystemExit(
                f"Phase 59.4 AI mode {mode_name} must keep {field} false."
            )
    if mode["authority_effect"] != "advisory_unavailable_no_workflow_mutation":
        raise SystemExit(
            f"Phase 59.4 AI mode {mode_name} must not mutate workflow authority."
        )
    disallowed = require_non_empty_string_list(
        mode["disallowed_authority"],
        f"Phase 59.4 AI mode {mode_name} disallowed_authority",
    )
    missing_disallowed = sorted(required_disallowed - set(disallowed))
    if missing_disallowed:
        raise SystemExit(
            f"Phase 59.4 AI mode {mode_name} is missing disallowed authority: "
            + ", ".join(missing_disallowed)
        )
    text = " ".join(
        [
            mode["operator_state"],
            mode["explanation"],
            " ".join(mode["safe_next_steps"]),
        ]
    ).casefold()
    if "authoritative aegisops records" not in text and "aegisops records" not in text:
        raise SystemExit(
            f"Phase 59.4 AI mode {mode_name} must tell operators to use AegisOps records."
        )

missing_modes = sorted(required_modes - seen_modes)
unexpected_modes = sorted(seen_modes - required_modes)
if missing_modes:
    raise SystemExit(
        "Phase 59.4 AI disabled/degraded mode artifact is missing mode(s): "
        + ", ".join(missing_modes)
    )
if unexpected_modes:
    raise SystemExit(
        "Phase 59.4 AI disabled/degraded mode artifact contains unexpected mode(s): "
        + ", ".join(unexpected_modes)
    )

required_surfaces = {
    "queue",
    "case",
    "evidence_review",
    "action_review",
    "reconciliation",
    "doctor_supportability",
    "admin_enablement",
}
required_surface_fields = {
    "surface",
    "authoritative_source",
    "ai_dependency",
    "disabled_mode_behavior",
    "degraded_mode_behavior",
    "required_operator_explanation",
}
surfaces = contract["non_ai_workflow_surfaces"]
if not isinstance(surfaces, list):
    raise SystemExit("Phase 59.4 non-AI workflow surfaces field must be a list.")

seen_surfaces: set[str] = set()
for index, surface in enumerate(surfaces, start=1):
    if not isinstance(surface, dict):
        raise SystemExit(f"Phase 59.4 non-AI workflow surface row {index} must be an object.")
    missing = sorted(required_surface_fields - surface.keys())
    if missing:
        raise SystemExit(
            f"Phase 59.4 non-AI workflow surface row {index} is missing field(s): "
            + ", ".join(missing)
        )
    surface_name = require_non_empty_string(
        surface["surface"],
        f"Phase 59.4 non-AI workflow surface row {index} surface",
    )
    if surface_name in seen_surfaces:
        raise SystemExit(f"Duplicate Phase 59.4 non-AI workflow surface: {surface_name}")
    seen_surfaces.add(surface_name)
    if surface["ai_dependency"] != "non_blocking":
        raise SystemExit(
            f"Phase 59.4 non-AI workflow surface {surface_name} must keep AI non-blocking."
        )
    for field in (
        "authoritative_source",
        "disabled_mode_behavior",
        "degraded_mode_behavior",
        "required_operator_explanation",
    ):
        require_non_empty_string(
            surface[field],
            f"Phase 59.4 non-AI workflow surface {surface_name} {field}",
        )
    explanation = surface["required_operator_explanation"].casefold()
    if "ai advisory unavailable" not in explanation:
        raise SystemExit(
            f"Phase 59.4 non-AI workflow surface {surface_name} must explain AI advisory unavailability."
        )

missing_surfaces = sorted(required_surfaces - seen_surfaces)
unexpected_surfaces = sorted(seen_surfaces - required_surfaces)
if missing_surfaces:
    raise SystemExit(
        "Phase 59.4 non-AI workflow coverage is missing surface(s): "
        + ", ".join(missing_surfaces)
    )
if unexpected_surfaces:
    raise SystemExit(
        "Phase 59.4 non-AI workflow coverage contains unexpected surface(s): "
        + ", ".join(unexpected_surfaces)
    )

blocked_outputs = require_non_empty_string_list(
    contract["blocked_ai_outputs"],
    "Phase 59.4 blocked_ai_outputs",
)
missing_blocked = sorted(required_disallowed - set(blocked_outputs))
if missing_blocked:
    raise SystemExit(
        "Phase 59.4 blocked_ai_outputs is missing blocked output(s): "
        + ", ".join(missing_blocked)
    )
for required_block in (
    "recommendation_generation",
    "action_request_draft_generation",
    "trace_creation",
):
    if required_block not in blocked_outputs:
        raise SystemExit(
            f"Phase 59.4 blocked_ai_outputs must include {required_block}."
        )

copy_rules = contract["operator_copy_rules"]
if not isinstance(copy_rules, dict):
    raise SystemExit("Phase 59.4 operator_copy_rules must be an object.")
required_terms = require_non_empty_string_list(
    copy_rules.get("required_terms"),
    "Phase 59.4 operator_copy_rules required_terms",
)
for term in ("AI advisory unavailable", "authoritative AegisOps records"):
    if term not in required_terms:
        raise SystemExit(
            f"Phase 59.4 operator_copy_rules must require copy term: {term}"
        )
forbidden_fragments = require_non_empty_string_list(
    copy_rules.get("forbidden_fragments"),
    "Phase 59.4 operator_copy_rules forbidden_fragments",
)
for fragment in ("AI approved", "AI executed", "AI reconciled", "AI is workflow truth"):
    if fragment not in forbidden_fragments:
        raise SystemExit(
            f"Phase 59.4 operator_copy_rules must forbid copy fragment: {fragment}"
        )
PY

path_hygiene_stderr="$(mktemp)"
trap 'rm -f "${path_hygiene_stderr}"' EXIT
if ! bash "${tool_root}/scripts/verify-publishable-path-hygiene.sh" "${repo_root}" \
  >/dev/null 2>"${path_hygiene_stderr}"; then
  cat "${path_hygiene_stderr}" >&2
  echo "Forbidden Phase 59.4 AI disabled/degraded mode artifact: workstation-local absolute path detected" >&2
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

if ! grep -Eq '\[[^]]+\]\(docs/phase-59-4-ai-disabled-degraded-mode-contract\.md\)' <<<"${readme_rendered_markdown}"; then
  echo "README must link the Phase 59.4 AI disabled/degraded mode contract." >&2
  exit 1
fi

echo "Phase 59.4 AI disabled/degraded mode contract is present with blocked AI generation, non-blocking workflow surfaces, operator explanations, and advisory-only authority."
