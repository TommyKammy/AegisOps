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
  'Run `python3 -m unittest control-plane.tests.test_phase58_1_doctor_contract.Phase581DoctorContractTests.test_doctor_contract_reports_degraded_source_and_ai_without_authority`.'
  'Run `bash scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh`.'
  'Run `bash scripts/verify-publishable-path-hygiene.sh`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1256 --config <supervisor-config-path>`.'
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1252 --config <supervisor-config-path>`.'
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
import re
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
required_forbidden_fragments = {
    "AI approved",
    "AI executed",
    "AI reconciled",
    "AI closed",
    "AI activated",
    "AI repaired",
    "AI is workflow truth",
    "automatic repair complete",
}
contradictory_authority_claims = {
    "ai can approve",
    "ai can execute",
    "ai can reconcile",
    "ai can close",
    "ai can activate",
    "ai can create source truth",
    "ai can repair",
    "ai can bypass policy",
    "ai may approve",
    "ai may execute",
    "ai may reconcile",
    "ai may close",
    "ai may activate",
    "ai may create source truth",
    "ai may repair",
    "ai may bypass policy",
    "ai approves",
    "ai executes",
    "ai reconciles",
    "ai closes",
    "ai activates",
    "ai creates source truth",
    "ai repairs",
    "ai bypasses policy",
    "ai approved",
    "ai executed",
    "ai reconciled",
    "ai closed",
    "ai activated",
    "ai repaired",
    "ai is workflow truth",
    "automatic repair complete",
}
forbidden_authority_fragments = {
    "ai_may_approve",
    "ai_can_approve",
    "ai_is_allowed_to_approve",
    "ai_is_authorized_to_approve",
    "ai_has_approval_authority",
    "ai_may_execute",
    "ai_can_execute",
    "ai_is_allowed_to_execute",
    "ai_is_authorized_to_execute",
    "ai_has_execution_authority",
    "ai_may_reconcile",
    "ai_can_reconcile",
    "ai_is_allowed_to_reconcile",
    "ai_is_authorized_to_reconcile",
    "ai_has_reconciliation_authority",
    "ai_may_close",
    "ai_can_close",
    "ai_is_allowed_to_close",
    "ai_is_authorized_to_close",
    "ai_has_case_closure_authority",
    "ai_may_activate",
    "ai_can_activate",
    "ai_is_allowed_to_activate",
    "ai_is_authorized_to_activate",
    "ai_has_detector_activation_authority",
    "ai_may_create_source_truth",
    "ai_can_create_source_truth",
    "ai_is_allowed_to_create_source_truth",
    "ai_is_authorized_to_create_source_truth",
    "ai_may_repair",
    "ai_can_repair",
    "ai_is_allowed_to_repair",
    "ai_is_authorized_to_repair",
    "ai_may_bypass_policy",
    "ai_can_bypass_policy",
    "ai_is_allowed_to_bypass_policy",
    "ai_is_authorized_to_bypass_policy",
    "ai_is_workflow_truth",
    "automatic_repair_complete",
}
expected_mode_values = {
    "disabled": {
        "trigger": "platform_admin_policy_disabled",
        "readiness_posture": "not_applicable",
        "reasons": ("ai_advisory_disabled_by_admin",),
        "operator_posture_terms": (
            "ai advisory unavailable",
            "ai advisory is unavailable",
            "ai advisory disabled",
            "ai advisory is disabled",
        ),
    },
    "degraded": {
        "trigger": "ai_advisory_degraded_by_admin_or_runtime_health",
        "readiness_posture": "degraded",
        "reasons": (
            "ai_advisory_degraded_by_admin",
            "ai_advisory_degraded_by_runtime_health",
        ),
        "operator_posture_terms": (
            "ai advisory degraded",
            "ai advisory is degraded",
        ),
    },
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

def require_no_forbidden_fragments(text: str, description: str, fragments: list[str]) -> None:
    text_lower = text.casefold()
    for fragment in fragments:
        if fragment.casefold() in text_lower:
            raise SystemExit(
                f"{description} must not include forbidden authority claim: {fragment}"
            )

def require_no_forbidden_authority_claim(text: str, description: str) -> None:
    normalized = re.sub(r"[^a-z0-9]+", "_", text.casefold()).strip("_")
    if any(fragment in normalized for fragment in forbidden_authority_fragments):
        raise SystemExit(f"{description} contains forbidden authority claim.")

if not isinstance(boundary, str) or not boundary.strip():
    raise SystemExit("Phase 59.4 AI disabled/degraded mode authority_boundary is invalid.")
boundary_lower = boundary.casefold()
if "subordinate" not in boundary_lower or "aegisops records remain authoritative" not in boundary_lower:
    raise SystemExit(
        "Phase 59.4 AI disabled/degraded mode authority boundary must preserve subordinate AegisOps authority semantics."
    )
require_no_forbidden_fragments(
    boundary,
    "Phase 59.4 AI disabled/degraded mode authority_boundary",
    sorted(contradictory_authority_claims),
)
require_no_forbidden_authority_claim(
    boundary,
    "Phase 59.4 AI disabled/degraded mode authority_boundary",
)

def require_ai_advisory_posture(text: str, description: str) -> None:
    text_lower = text.casefold()
    allowed_posture_terms = (
        "ai advisory unavailable",
        "ai advisory is unavailable",
        "ai advisory disabled",
        "ai advisory is disabled",
        "ai advisory degraded",
        "ai advisory is degraded",
        "ai advisory unavailable or degraded",
    )
    if not any(term in text_lower for term in allowed_posture_terms):
        raise SystemExit(
            f"{description} must explain AI advisory unavailable or degraded posture."
        )

def require_mode_operator_posture(mode_name: str, text: str, description: str) -> None:
    text_lower = text.casefold()
    posture_terms = expected_mode_values[mode_name]["operator_posture_terms"]
    if not any(term in text_lower for term in posture_terms):
        raise SystemExit(f"{description} must explain AI advisory {mode_name} posture.")

def require_authoritative_records(text: str, description: str) -> None:
    if "authoritative aegisops records" not in text.casefold():
        raise SystemExit(
            f"{description} must direct operators to authoritative AegisOps records."
        )

def require_operator_required_terms(
    text: str, description: str, required_terms: list[str]
) -> None:
    text_lower = text.casefold()
    for term in required_terms:
        term_lower = term.casefold()
        if term == "AI advisory unavailable or degraded":
            require_ai_advisory_posture(text, description)
        elif term == "authoritative AegisOps records":
            require_authoritative_records(text, description)
        elif term_lower not in text_lower:
            raise SystemExit(f"{description} must include required copy term: {term}")

def require_no_healthy_or_available_posture(text: str, description: str) -> None:
    normalized = re.sub(r"[^a-z0-9]+", " ", text.casefold())
    terms = set(normalized.split())
    for forbidden in ("healthy", "available"):
        if forbidden in terms:
            raise SystemExit(
                f"{description} must not claim healthy or available AI posture."
            )

def require_mode_reason_semantics(mode_name: str, value: object) -> list[str]:
    expected = expected_mode_values.get(mode_name)
    description = f"Phase 59.4 AI mode {mode_name} reason"
    if expected is None:
        return [require_non_empty_string(value, description)]
    if isinstance(value, str):
        reasons = [require_non_empty_string(value, description)]
    elif isinstance(value, list):
        reasons = require_non_empty_string_list(value, description)
    else:
        raise SystemExit(f"{description} must be a non-empty string or string list.")
    allowed_reasons = set(expected["reasons"])
    unexpected_reasons = sorted(set(reasons) - allowed_reasons)
    if unexpected_reasons:
        raise SystemExit(
            f"{description} must be one of: {', '.join(expected['reasons'])}."
        )
    return reasons

def require_mode_specific_semantics(mode_name: str, mode: dict) -> None:
    expected = expected_mode_values.get(mode_name)
    if expected is None:
        return
    for field in ("trigger", "readiness_posture"):
        if mode[field] != expected[field]:
            raise SystemExit(
                f"Phase 59.4 AI mode {mode_name} {field} must be {expected[field]}."
            )
    reasons = require_mode_reason_semantics(mode_name, mode["reason"])
    for field in ("operator_state", "explanation"):
        require_mode_operator_posture(
            mode_name,
            mode[field],
            f"Phase 59.4 AI mode {mode_name} {field}",
        )
    posture_values = [
        mode["trigger"],
        mode["readiness_posture"],
        *reasons,
        mode["operator_state"],
        mode["explanation"],
    ]
    for value in posture_values:
        require_no_healthy_or_available_posture(
            value,
            f"Phase 59.4 AI mode {mode_name} posture field",
        )

def require_mode_operator_copy_contract(
    mode_name: str,
    mode: dict,
    safe_next_steps: list[str],
    forbidden_fragments: list[str],
) -> None:
    text = " ".join(
        [
            mode["operator_state"],
            mode["explanation"],
            " ".join(safe_next_steps),
        ]
    )
    for field in ("operator_state", "explanation"):
        require_ai_advisory_posture(
            mode[field],
            f"Phase 59.4 AI mode {mode_name} {field}",
        )
        if mode_name in expected_mode_values:
            require_mode_operator_posture(
                mode_name,
                mode[field],
                f"Phase 59.4 AI mode {mode_name} {field}",
            )
    require_authoritative_records(
        text,
        f"Phase 59.4 AI mode {mode_name} operator-facing copy",
    )
    require_operator_required_terms(
        text,
        f"Phase 59.4 AI mode {mode_name} operator-facing copy",
        required_terms,
    )
    require_no_forbidden_fragments(
        text,
        f"Phase 59.4 AI mode {mode_name} operator-facing copy",
        forbidden_fragments,
    )
    require_no_forbidden_authority_claim(
        text,
        f"Phase 59.4 AI mode {mode_name} operator-facing copy",
    )

copy_rules = contract["operator_copy_rules"]
if not isinstance(copy_rules, dict):
    raise SystemExit("Phase 59.4 operator_copy_rules must be an object.")
required_terms = require_non_empty_string_list(
    copy_rules.get("required_terms"),
    "Phase 59.4 operator_copy_rules required_terms",
)
for term in ("AI advisory unavailable or degraded", "authoritative AegisOps records"):
    if term not in required_terms:
        raise SystemExit(
            f"Phase 59.4 operator_copy_rules must require copy term: {term}"
        )
forbidden_fragments = require_non_empty_string_list(
    copy_rules.get("forbidden_fragments"),
    "Phase 59.4 operator_copy_rules forbidden_fragments",
)
for fragment in sorted(required_forbidden_fragments):
    if fragment not in forbidden_fragments:
        raise SystemExit(
            f"Phase 59.4 operator_copy_rules must forbid copy fragment: {fragment}"
        )
require_no_forbidden_fragments(
    boundary,
    "Phase 59.4 AI disabled/degraded mode authority_boundary",
    sorted(contradictory_authority_claims | {fragment.casefold() for fragment in forbidden_fragments}),
)
require_no_forbidden_authority_claim(
    boundary,
    "Phase 59.4 AI disabled/degraded mode authority_boundary",
)

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
    for field in ("trigger", "operator_state", "readiness_posture", "explanation", "authority_effect"):
        require_non_empty_string(mode[field], f"Phase 59.4 AI mode {mode_name} {field}")
    safe_next_steps = require_non_empty_string_list(
        mode["safe_next_steps"],
        f"Phase 59.4 AI mode {mode_name} safe_next_steps",
    )
    require_mode_specific_semantics(mode_name, mode)
    require_mode_operator_copy_contract(
        mode_name,
        mode,
        safe_next_steps,
        forbidden_fragments,
    )
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
    operator_text = " ".join(
        [
            surface["disabled_mode_behavior"],
            surface["degraded_mode_behavior"],
            surface["required_operator_explanation"],
        ]
    )
    require_ai_advisory_posture(
        surface["required_operator_explanation"],
        f"Phase 59.4 non-AI workflow surface {surface_name} operator explanation",
    )
    require_authoritative_records(
        surface["required_operator_explanation"],
        f"Phase 59.4 non-AI workflow surface {surface_name} operator explanation",
    )
    require_operator_required_terms(
        operator_text,
        f"Phase 59.4 non-AI workflow surface {surface_name} operator-facing copy",
        required_terms,
    )
    require_no_forbidden_fragments(
        operator_text,
        f"Phase 59.4 non-AI workflow surface {surface_name} operator-facing copy",
        forbidden_fragments,
    )
    require_no_forbidden_authority_claim(
        operator_text,
        f"Phase 59.4 non-AI workflow surface {surface_name} operator-facing copy",
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
