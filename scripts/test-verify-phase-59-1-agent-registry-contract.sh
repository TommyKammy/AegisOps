#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-59-1-agent-registry-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs/automation"
  printf '%s\n' \
    "# AegisOps" \
    "See [Phase 59.1 agent registry contract](docs/phase-59-1-agent-registry-contract.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/phase-59-1-agent-registry-contract.md" \
    "${target}/docs/phase-59-1-agent-registry-contract.md"
  cp "${repo_root}/docs/automation/ai-agent-registry.json" \
    "${target}/docs/automation/ai-agent-registry.json"
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

mutate_registry() {
  local target="$1"
  local mutation="$2"

  python3 - "${target}/docs/automation/ai-agent-registry.json" "${mutation}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
mutation = sys.argv[2]
registry = json.loads(path.read_text(encoding="utf-8"))

if mutation == "missing_authority_ceiling":
    registry["agents"][0].pop("authority_ceiling", None)
elif mutation == "missing_citation_requirements":
    registry["agents"][0].pop("citation_requirements", None)
elif mutation == "authority_expansion":
    registry["agents"][0]["authority_ceiling"] = "may_approve_actions"
elif mutation == "allowed_execution_tool":
    registry["agents"][0]["allowed_tools"].append("execute_action")
elif mutation == "missing_disallowed_execution":
    registry["agents"][0]["disallowed_tools"].remove("execute_action")
elif mutation == "missing_record_id_citation":
    registry["agents"][0]["citation_requirements"] = [
        value for value in registry["agents"][0]["citation_requirements"]
        if "record_id" not in value
    ]
else:
    raise SystemExit(f"unknown mutation: {mutation}")

path.write_text(json.dumps(registry, indent=2, sort_keys=False) + "\n", encoding="utf-8")
PY
}

remove_text_from_doc() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-59-1-agent-registry-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-59-1-agent-registry-contract.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 59.1 agent registry contract doc"

missing_registry_repo="${workdir}/missing-registry"
create_valid_repo "${missing_registry_repo}"
rm "${missing_registry_repo}/docs/automation/ai-agent-registry.json"
assert_fails_with \
  "${missing_registry_repo}" \
  "Missing Phase 59.1 AI agent registry"

missing_contract_field_repo="${workdir}/missing-contract-field"
create_valid_repo "${missing_contract_field_repo}"
remove_text_from_doc "${missing_contract_field_repo}" \
  "Every registry row must include agent name, purpose, allowed tools, disallowed tools, record families, citation requirements, and authority ceiling."
assert_fails_with \
  "${missing_contract_field_repo}" \
  "Missing Phase 59.1 agent registry contract statement: Every registry row must include agent name"

missing_authority_repo="${workdir}/missing-authority"
create_valid_repo "${missing_authority_repo}"
mutate_registry "${missing_authority_repo}" "missing_authority_ceiling"
assert_fails_with \
  "${missing_authority_repo}" \
  "is missing field(s): authority_ceiling"

missing_citations_repo="${workdir}/missing-citations"
create_valid_repo "${missing_citations_repo}"
mutate_registry "${missing_citations_repo}" "missing_citation_requirements"
assert_fails_with \
  "${missing_citations_repo}" \
  "is missing field(s): citation_requirements"

authority_expansion_repo="${workdir}/authority-expansion"
create_valid_repo "${authority_expansion_repo}"
mutate_registry "${authority_expansion_repo}" "authority_expansion"
assert_fails_with \
  "${authority_expansion_repo}" \
  "must keep the advisory-only authority ceiling"

allowed_execution_repo="${workdir}/allowed-execution"
create_valid_repo "${allowed_execution_repo}"
mutate_registry "${allowed_execution_repo}" "allowed_execution_tool"
assert_fails_with \
  "${allowed_execution_repo}" \
  "has forbidden allowed tool: execute_action"

missing_disallowed_repo="${workdir}/missing-disallowed-execution"
create_valid_repo "${missing_disallowed_repo}"
mutate_registry "${missing_disallowed_repo}" "missing_disallowed_execution"
assert_fails_with \
  "${missing_disallowed_repo}" \
  "is missing disallowed tool(s): execute_action"

missing_record_id_repo="${workdir}/missing-record-id-citation"
create_valid_repo "${missing_record_id_repo}"
mutate_registry "${missing_record_id_repo}" "missing_record_id_citation"
assert_fails_with \
  "${missing_record_id_repo}" \
  "citation requirements must include record_id"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf '/%s/%s/%s\n' "Users" "example" "private.txt" \
  >>"${local_path_repo}/docs/phase-59-1-agent-registry-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "workstation-local absolute path detected"

echo "Phase 59.1 agent registry verifier rejects missing fields, authority expansion, missing citations, unsafe tools, and local paths."
