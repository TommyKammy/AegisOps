#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-59-4-ai-disabled-degraded-mode-contract.sh"

if [[ ! -x "${verifier}" ]]; then
  echo "Missing executable Phase 59.4 AI disabled/degraded mode verifier: ${verifier}" >&2
  exit 1
fi

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/automation" "${target}/scripts"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
  printf '%s\n' \
    "# AegisOps" \
    "See [Phase 59.4 AI disabled/degraded mode contract](docs/phase-59-4-ai-disabled-degraded-mode-contract.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/phase-59-4-ai-disabled-degraded-mode-contract.md" \
    "${target}/docs/phase-59-4-ai-disabled-degraded-mode-contract.md"
  cp "${repo_root}/docs/automation/ai-disabled-degraded-mode-contract.json" \
    "${target}/docs/automation/ai-disabled-degraded-mode-contract.json"
  cp "${repo_root}/scripts/verify-publishable-path-hygiene.sh" \
    "${target}/scripts/verify-publishable-path-hygiene.sh"
  git -C "${target}" add README.md docs/phase-59-4-ai-disabled-degraded-mode-contract.md \
    docs/automation/ai-disabled-degraded-mode-contract.json \
    scripts/verify-publishable-path-hygiene.sh
}

assert_passes() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

mutate_contract() {
  local target="$1"
  local mutation="$2"

  python3 - "${target}/docs/automation/ai-disabled-degraded-mode-contract.json" "${mutation}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
mutation = sys.argv[2]
contract = json.loads(path.read_text(encoding="utf-8"))

disabled = next(mode for mode in contract["modes"] if mode["mode"] == "disabled")
degraded = next(mode for mode in contract["modes"] if mode["mode"] == "degraded")
queue = next(surface for surface in contract["non_ai_workflow_surfaces"] if surface["surface"] == "queue")

if mutation == "missing_disabled_mode":
    contract["modes"] = [mode for mode in contract["modes"] if mode["mode"] != "disabled"]
elif mutation == "allow_recommendation_generation":
    disabled["recommendation_generation_allowed"] = True
elif mutation == "allow_trace_creation":
    degraded["trace_creation_allowed"] = True
elif mutation == "missing_surface":
    contract["non_ai_workflow_surfaces"] = [
        surface
        for surface in contract["non_ai_workflow_surfaces"]
        if surface["surface"] != "reconciliation"
    ]
elif mutation == "ai_blocking_surface":
    queue["ai_dependency"] = "required"
elif mutation == "missing_operator_explanation":
    queue["required_operator_explanation"] = ""
elif mutation == "missing_disallowed_authority":
    disabled["disallowed_authority"].remove("automatic_repair")
elif mutation == "missing_blocked_output":
    contract["blocked_ai_outputs"].remove("trace_creation")
elif mutation == "missing_copy_rule":
    contract["operator_copy_rules"]["forbidden_fragments"].remove("AI is workflow truth")
elif mutation == "missing_extended_copy_rule":
    contract["operator_copy_rules"]["forbidden_fragments"].remove("AI closed")
elif mutation == "authority_boundary_forbidden_claim":
    contract["authority_boundary"] += " AI may execute actions."
elif mutation == "authority_boundary_can_execute_claim":
    contract["authority_boundary"] += " AI can execute actions."
elif mutation == "authority_boundary_allowed_execute_claim":
    contract["authority_boundary"] += " AI is allowed to execute actions."
elif mutation == "mode_generic_posture":
    disabled["operator_state"] = "Normal operations continue."
    disabled["explanation"] = "Continue normal operations from authoritative AegisOps records."
elif mutation == "mode_operator_state_missing_advisory_posture":
    disabled["operator_state"] = "Disabled policy posture is shown."
elif mutation == "mode_explanation_missing_advisory_posture":
    disabled["explanation"] = "Disabled policy posture is shown from authoritative AegisOps records."
elif mutation == "disabled_trigger_degraded":
    disabled["trigger"] = "ai_advisory_degraded_by_admin_or_runtime_health"
elif mutation == "degraded_reason_disabled":
    degraded["reason"] = "ai_advisory_disabled_by_admin"
elif mutation == "degraded_reason_runtime_health":
    degraded["reason"] = "ai_advisory_degraded_by_runtime_health"
elif mutation == "mode_wrong_readiness":
    disabled["readiness_posture"] = "healthy_available"
elif mutation == "degraded_claims_available_readiness":
    degraded["readiness_posture"] = "degraded_healthy_available"
elif mutation == "operator_forbidden_fragment":
    disabled["explanation"] += " AI approved the workflow."
elif mutation == "missing_operator_required_records":
    queue["required_operator_explanation"] = "AI advisory unavailable; queue ordering and case state continue."
elif mutation == "surface_degraded_operator_explanation":
    queue["required_operator_explanation"] = "AI advisory degraded; queue ordering and case state come from authoritative AegisOps records."
elif mutation == "json_escaped_unix_path":
    disabled["explanation"] += " See /" + "Users/example/private.txt."
elif mutation == "json_escaped_windows_path":
    slash = chr(92)
    degraded["explanation"] += " See C:" + slash + "Users" + slash + "example" + slash + "private.txt."
else:
    raise SystemExit(f"unknown mutation: {mutation}")

path.write_text(json.dumps(contract, indent=2, sort_keys=False) + "\n", encoding="utf-8")
PY
}

remove_text_from_doc() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-59-4-ai-disabled-degraded-mode-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

degraded_copy_repo="${workdir}/surface-degraded-operator-explanation"
create_valid_repo "${degraded_copy_repo}"
mutate_contract "${degraded_copy_repo}" "surface_degraded_operator_explanation"
assert_passes "${degraded_copy_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-59-4-ai-disabled-degraded-mode-contract.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 59.4 AI disabled/degraded mode contract doc"

missing_artifact_repo="${workdir}/missing-artifact"
create_valid_repo "${missing_artifact_repo}"
rm "${missing_artifact_repo}/docs/automation/ai-disabled-degraded-mode-contract.json"
assert_fails_with \
  "${missing_artifact_repo}" \
  "Missing Phase 59.4 AI disabled/degraded mode artifact"

missing_contract_field_repo="${workdir}/missing-contract-field"
create_valid_repo "${missing_contract_field_repo}"
remove_text_from_doc "${missing_contract_field_repo}" \
  "Every disabled or degraded mode row must include mode, trigger, operator state, readiness posture, blocked AI generation flags, reason, explanation, safe next steps, authority effect, and disallowed authority."
assert_fails_with \
  "${missing_contract_field_repo}" \
  "Missing Phase 59.4 AI disabled/degraded mode contract statement: Every disabled or degraded mode row"

missing_doctor_validation_repo="${workdir}/missing-doctor-validation"
create_valid_repo "${missing_doctor_validation_repo}"
remove_text_from_doc "${missing_doctor_validation_repo}" \
  'Run `python3 -m unittest control-plane.tests.test_phase58_1_doctor_contract.Phase581DoctorContractTests.test_doctor_contract_reports_degraded_source_and_ai_without_authority`.'
assert_fails_with \
  "${missing_doctor_validation_repo}" \
  "Missing Phase 59.4 AI disabled/degraded mode contract statement: Run \`python3 -m unittest control-plane.tests.test_phase58_1_doctor_contract.Phase581DoctorContractTests.test_doctor_contract_reports_degraded_source_and_ai_without_authority\`."

missing_epic_issue_lint_repo="${workdir}/missing-epic-issue-lint"
create_valid_repo "${missing_epic_issue_lint_repo}"
remove_text_from_doc "${missing_epic_issue_lint_repo}" \
  'Run `node <codex-supervisor-root>/dist/index.js issue-lint 1252 --config <supervisor-config-path>`.'
assert_fails_with \
  "${missing_epic_issue_lint_repo}" \
  "Missing Phase 59.4 AI disabled/degraded mode contract statement: Run \`node <codex-supervisor-root>/dist/index.js issue-lint 1252 --config <supervisor-config-path>\`."

runtime_health_reason_repo="${workdir}/runtime-health-reason"
create_valid_repo "${runtime_health_reason_repo}"
mutate_contract "${runtime_health_reason_repo}" "degraded_reason_runtime_health"
assert_passes "${runtime_health_reason_repo}"

for mutation in \
  missing_disabled_mode \
  allow_recommendation_generation \
  allow_trace_creation \
  missing_surface \
  ai_blocking_surface \
  missing_operator_explanation \
  missing_disallowed_authority \
  missing_blocked_output \
  missing_copy_rule \
  missing_extended_copy_rule \
  authority_boundary_forbidden_claim \
  authority_boundary_can_execute_claim \
  authority_boundary_allowed_execute_claim \
  mode_generic_posture \
  mode_operator_state_missing_advisory_posture \
  mode_explanation_missing_advisory_posture \
  disabled_trigger_degraded \
  degraded_reason_disabled \
  mode_wrong_readiness \
  degraded_claims_available_readiness \
  operator_forbidden_fragment \
  missing_operator_required_records \
  json_escaped_unix_path \
  json_escaped_windows_path
do
  mutated_repo="${workdir}/${mutation}"
  create_valid_repo "${mutated_repo}"
  mutate_contract "${mutated_repo}" "${mutation}"
  case "${mutation}" in
    missing_disabled_mode)
      assert_fails_with "${mutated_repo}" "is missing mode(s): disabled"
      ;;
    allow_recommendation_generation)
      assert_fails_with "${mutated_repo}" "must keep recommendation_generation_allowed false"
      ;;
    allow_trace_creation)
      assert_fails_with "${mutated_repo}" "must keep trace_creation_allowed false"
      ;;
    missing_surface)
      assert_fails_with "${mutated_repo}" "is missing surface(s): reconciliation"
      ;;
    ai_blocking_surface)
      assert_fails_with "${mutated_repo}" "must keep AI non-blocking"
      ;;
    missing_operator_explanation)
      assert_fails_with "${mutated_repo}" "required_operator_explanation must be a non-empty string"
      ;;
    missing_disallowed_authority)
      assert_fails_with "${mutated_repo}" "is missing disallowed authority: automatic_repair"
      ;;
    missing_blocked_output)
      assert_fails_with "${mutated_repo}" "must include trace_creation"
      ;;
    missing_copy_rule)
      assert_fails_with "${mutated_repo}" "must forbid copy fragment: AI is workflow truth"
      ;;
    missing_extended_copy_rule)
      assert_fails_with "${mutated_repo}" "must forbid copy fragment: AI closed"
      ;;
    authority_boundary_forbidden_claim)
      assert_fails_with "${mutated_repo}" "authority_boundary must not include forbidden authority claim: ai may execute"
      ;;
    authority_boundary_can_execute_claim)
      assert_fails_with "${mutated_repo}" "authority_boundary must not include forbidden authority claim: ai can execute"
      ;;
    authority_boundary_allowed_execute_claim)
      assert_fails_with "${mutated_repo}" "authority_boundary contains forbidden authority claim"
      ;;
    mode_generic_posture)
      assert_fails_with "${mutated_repo}" "AI mode disabled operator_state must explain AI advisory disabled posture"
      ;;
    mode_operator_state_missing_advisory_posture)
      assert_fails_with "${mutated_repo}" "AI mode disabled operator_state must explain AI advisory disabled posture"
      ;;
    mode_explanation_missing_advisory_posture)
      assert_fails_with "${mutated_repo}" "AI mode disabled explanation must explain AI advisory disabled posture"
      ;;
    disabled_trigger_degraded)
      assert_fails_with "${mutated_repo}" "AI mode disabled trigger must be platform_admin_policy_disabled"
      ;;
    degraded_reason_disabled)
      assert_fails_with "${mutated_repo}" "AI mode degraded reason must be one of: ai_advisory_degraded_by_admin, ai_advisory_degraded_by_runtime_health"
      ;;
    mode_wrong_readiness)
      assert_fails_with "${mutated_repo}" "AI mode disabled readiness_posture must be not_applicable"
      ;;
    degraded_claims_available_readiness)
      assert_fails_with "${mutated_repo}" "AI mode degraded readiness_posture must be degraded"
      ;;
    operator_forbidden_fragment)
      assert_fails_with "${mutated_repo}" "operator-facing copy must not include forbidden authority claim: AI approved"
      ;;
    missing_operator_required_records)
      assert_fails_with "${mutated_repo}" "operator explanation must direct operators to authoritative AegisOps records"
      ;;
    json_escaped_unix_path|json_escaped_windows_path)
      assert_fails_with "${mutated_repo}" "workstation-local absolute path detected"
      ;;
  esac
done

echo "Phase 59.4 AI disabled/degraded mode verifier rejects missing modes, enabled AI output, blocking workflow surfaces, weak copy rules, missing authority refusals, and local paths."
