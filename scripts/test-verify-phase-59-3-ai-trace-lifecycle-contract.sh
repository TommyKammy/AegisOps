#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-59-3-ai-trace-lifecycle-contract.sh"

if [[ ! -x "${verifier}" ]]; then
  echo "Missing executable Phase 59.3 AI trace lifecycle verifier: ${verifier}" >&2
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

  mkdir -p "${target}/docs/automation"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
  printf '%s\n' \
    "# AegisOps" \
    "See [Phase 59.3 AI trace lifecycle contract](docs/phase-59-3-ai-trace-lifecycle-contract.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/phase-59-3-ai-trace-lifecycle-contract.md" \
    "${target}/docs/phase-59-3-ai-trace-lifecycle-contract.md"
  cp "${repo_root}/docs/automation/ai-agent-registry.json" \
    "${target}/docs/automation/ai-agent-registry.json"
  cp "${repo_root}/docs/automation/ai-tool-registry.json" \
    "${target}/docs/automation/ai-tool-registry.json"
  cp "${repo_root}/docs/automation/ai-trace-lifecycle.json" \
    "${target}/docs/automation/ai-trace-lifecycle.json"
  git -C "${target}" add README.md docs/phase-59-3-ai-trace-lifecycle-contract.md \
    docs/automation/ai-agent-registry.json docs/automation/ai-tool-registry.json \
    docs/automation/ai-trace-lifecycle.json
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

assert_mutation_fails_with() {
  local mutation="$1"
  local expected="$2"
  local mutated_repo="${workdir}/${mutation}"

  create_valid_repo "${mutated_repo}"
  mutate_lifecycle "${mutated_repo}" "${mutation}"
  assert_fails_with "${mutated_repo}" "${expected}"
}

mutate_lifecycle() {
  local target="$1"
  local mutation="$2"

  python3 - "${target}/docs/automation/ai-trace-lifecycle.json" "${mutation}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
mutation = sys.argv[2]
lifecycle = json.loads(path.read_text(encoding="utf-8"))

states = lifecycle["lifecycle_states"]
created = next(state for state in states if state["state"] == "created")
accepted = next(state for state in states if state["state"] == "accepted")
corrected = next(state for state in states if state["state"] == "corrected")
rejected = next(state for state in states if state["state"] == "rejected")
reviewed = next(state for state in states if state["state"] == "reviewed")

if mutation == "missing_created_state":
    lifecycle["lifecycle_states"] = [
        state for state in states if state["state"] != "created"
    ]
elif mutation == "missing_registered_agent":
    created["registered_agents"] = []
elif mutation == "unregistered_tool":
    created["registered_tools"].append("autonomous_case_closure")
elif mutation == "missing_citation":
    created["required_linkage"] = [
        value for value in created["required_linkage"] if "citation_ids" not in value
    ]
elif mutation == "missing_reviewer_metadata":
    accepted["reviewer_action_metadata_required"] = False
elif mutation == "missing_expiration":
    created["required_linkage"] = [
        value for value in created["required_linkage"] if "expires_at" not in value
    ]
elif mutation == "authority_expansion":
    accepted["authority_effect"] = "may_close_case"
elif mutation == "missing_transition":
    lifecycle["allowed_transitions"] = [
        transition
        for transition in lifecycle["allowed_transitions"]
        if not (
            transition["from_state"] == "reviewed"
            and transition["to_state"] == "corrected"
        )
    ]
elif mutation == "terminal_state_with_outgoing_transition":
    accepted["terminal"] = True
elif mutation == "missing_reviewed_state_linkage":
    reviewed["required_linkage"] = [
        value for value in reviewed["required_linkage"] if value != "reviewed_at"
    ]
elif mutation == "missing_accepted_state_linkage":
    accepted["required_linkage"] = [
        value for value in accepted["required_linkage"] if value != "accepted_at"
    ]
elif mutation == "missing_corrected_state_linkage":
    corrected["required_linkage"] = [
        value for value in corrected["required_linkage"] if value != "corrected_at"
    ]
elif mutation == "missing_rejected_state_linkage":
    rejected["required_linkage"] = [
        value for value in rejected["required_linkage"] if value != "rejected_at"
    ]
elif mutation == "missing_reviewed_transition_metadata":
    transition = next(
        transition
        for transition in lifecycle["allowed_transitions"]
        if transition["from_state"] == "created"
        and transition["to_state"] == "reviewed"
    )
    transition["required_metadata"] = [
        value for value in transition["required_metadata"] if value != "reviewed_at"
    ]
elif mutation == "missing_accepted_transition_metadata":
    transition = next(
        transition
        for transition in lifecycle["allowed_transitions"]
        if transition["from_state"] == "reviewed"
        and transition["to_state"] == "accepted"
    )
    transition["required_metadata"] = [
        value for value in transition["required_metadata"] if value != "accepted_at"
    ]
elif mutation == "missing_corrected_transition_metadata":
    transition = next(
        transition
        for transition in lifecycle["allowed_transitions"]
        if transition["from_state"] == "reviewed"
        and transition["to_state"] == "corrected"
    )
    transition["required_metadata"] = [
        value for value in transition["required_metadata"] if value != "corrected_at"
    ]
elif mutation == "missing_rejected_transition_metadata":
    transition = next(
        transition
        for transition in lifecycle["allowed_transitions"]
        if transition["from_state"] == "reviewed"
        and transition["to_state"] == "rejected"
    )
    transition["required_metadata"] = [
        value for value in transition["required_metadata"] if value != "rejected_at"
    ]
elif mutation == "allowed_from_drift":
    accepted["allowed_from"] = ["created"]
elif mutation == "invalid_allowed_from_state":
    accepted["allowed_from"] = ["unknown_review_state"]
elif mutation == "unexpected_transition_pair":
    lifecycle["allowed_transitions"].append(
        {
            "from_state": "accepted",
            "to_state": "reviewed",
            "required_trigger": "invalid review rewind",
            "required_metadata": ["reviewer_id", "review_action_id", "reviewed_at"],
            "authority_effect": "advisory_only_no_workflow_mutation",
        }
    )
elif mutation == "expiry_can_accept":
    lifecycle["allowed_transitions"].append(
        {
            "from_state": "expired",
            "to_state": "accepted",
            "required_trigger": "late operator acceptance",
            "required_metadata": ["reviewer_id", "review_action_id"],
            "authority_effect": "advisory_only_no_workflow_mutation",
        }
    )
elif mutation == "reviewed_truth_claim":
    reviewed["purpose"] += " This state becomes workflow truth."
elif mutation == "json_escaped_windows_path":
    created["purpose"] += " See C:" + chr(92) + "Users" + chr(92) + "example" + chr(92) + "trace.txt."
elif mutation == "json_escaped_unix_path":
    created["purpose"] += " See /" + "Users/example/trace.txt."
else:
    raise SystemExit(f"unknown mutation: {mutation}")

path.write_text(json.dumps(lifecycle, indent=2, sort_keys=False) + "\n", encoding="utf-8")
PY
}

remove_text_from_doc() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-59-3-ai-trace-lifecycle-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-59-3-ai-trace-lifecycle-contract.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 59.3 AI trace lifecycle contract doc"

missing_lifecycle_repo="${workdir}/missing-lifecycle"
create_valid_repo "${missing_lifecycle_repo}"
rm "${missing_lifecycle_repo}/docs/automation/ai-trace-lifecycle.json"
assert_fails_with \
  "${missing_lifecycle_repo}" \
  "Missing Phase 59.3 AI trace lifecycle artifact"

missing_contract_field_repo="${workdir}/missing-contract-field"
create_valid_repo "${missing_contract_field_repo}"
remove_text_from_doc "${missing_contract_field_repo}" \
  "Every AI trace lifecycle state must require registered agent linkage, registered tool linkage, citations, reviewed record family and identifier linkage, expiration handling, and advisory-only authority."
assert_fails_with \
  "${missing_contract_field_repo}" \
  "Missing Phase 59.3 AI trace lifecycle contract statement: Every AI trace lifecycle state"

for mutation in \
  missing_created_state \
  missing_registered_agent \
  unregistered_tool \
  missing_citation \
  missing_reviewer_metadata \
  missing_expiration \
  authority_expansion \
  missing_transition \
  expiry_can_accept \
  reviewed_truth_claim
do
  mutated_repo="${workdir}/${mutation}"
  create_valid_repo "${mutated_repo}"
  mutate_lifecycle "${mutated_repo}" "${mutation}"
  assert_fails_with "${mutated_repo}" "Phase 59.3"
done

assert_mutation_fails_with \
  terminal_state_with_outgoing_transition \
  "Phase 59.3 AI trace lifecycle state accepted terminal flag must be false while outgoing transitions exist."
assert_mutation_fails_with \
  missing_reviewed_state_linkage \
  "Phase 59.3 AI trace lifecycle state reviewed is missing state-specific linkage field(s): reviewed_at"
assert_mutation_fails_with \
  missing_accepted_state_linkage \
  "Phase 59.3 AI trace lifecycle state accepted is missing state-specific linkage field(s): accepted_at"
assert_mutation_fails_with \
  missing_corrected_state_linkage \
  "Phase 59.3 AI trace lifecycle state corrected is missing state-specific linkage field(s): corrected_at"
assert_mutation_fails_with \
  missing_rejected_state_linkage \
  "Phase 59.3 AI trace lifecycle state rejected is missing state-specific linkage field(s): rejected_at"
assert_mutation_fails_with \
  missing_reviewed_transition_metadata \
  "Phase 59.3 AI trace lifecycle transition created->reviewed is missing transition-specific metadata: reviewed_at"
assert_mutation_fails_with \
  missing_accepted_transition_metadata \
  "Phase 59.3 AI trace lifecycle transition reviewed->accepted is missing transition-specific metadata: accepted_at"
assert_mutation_fails_with \
  missing_corrected_transition_metadata \
  "Phase 59.3 AI trace lifecycle transition reviewed->corrected is missing transition-specific metadata: corrected_at"
assert_mutation_fails_with \
  missing_rejected_transition_metadata \
  "Phase 59.3 AI trace lifecycle transition reviewed->rejected is missing transition-specific metadata: rejected_at"
assert_mutation_fails_with \
  invalid_allowed_from_state \
  "Phase 59.3 AI trace lifecycle state accepted references invalid allowed_from state: unknown_review_state"
assert_mutation_fails_with \
  allowed_from_drift \
  "Phase 59.3 AI trace lifecycle state accepted allowed_from must match transition graph: expected reviewed; got created"
assert_mutation_fails_with \
  unexpected_transition_pair \
  "Phase 59.3 AI trace lifecycle contains unexpected transition for this slice: accepted->reviewed"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf '/%s/%s/%s\n' "Users" "example" "trace.txt" \
  >>"${local_path_repo}/docs/phase-59-3-ai-trace-lifecycle-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "workstation-local absolute path detected"

json_escaped_windows_path_repo="${workdir}/json-escaped-windows-path"
create_valid_repo "${json_escaped_windows_path_repo}"
mutate_lifecycle "${json_escaped_windows_path_repo}" "json_escaped_windows_path"
assert_fails_with \
  "${json_escaped_windows_path_repo}" \
  "workstation-local absolute path detected"

json_escaped_unix_path_repo="${workdir}/json-escaped-unix-path"
create_valid_repo "${json_escaped_unix_path_repo}"
mutate_lifecycle "${json_escaped_unix_path_repo}" "json_escaped_unix_path"
assert_fails_with \
  "${json_escaped_unix_path_repo}" \
  "workstation-local absolute path detected"

echo "Phase 59.3 AI trace lifecycle verifier rejects missing states, unregistered linkage, missing citations, missing review or expiration handling, authority expansion, invalid transitions, truth claims, and local paths."
