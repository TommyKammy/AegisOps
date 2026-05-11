#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-59-2-tool-registry-contract.sh"

if [[ ! -x "${verifier}" ]]; then
  echo "Missing executable Phase 59.2 tool registry verifier: ${verifier}" >&2
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
    "See [Phase 59.2 tool registry contract](docs/phase-59-2-tool-registry-contract.md)." \
    >"${target}/README.md"
  cp "${repo_root}/docs/phase-59-2-tool-registry-contract.md" \
    "${target}/docs/phase-59-2-tool-registry-contract.md"
  cp "${repo_root}/docs/automation/ai-tool-registry.json" \
    "${target}/docs/automation/ai-tool-registry.json"
  git -C "${target}" add README.md docs/phase-59-2-tool-registry-contract.md \
    docs/automation/ai-tool-registry.json
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

  python3 - "${target}/docs/automation/ai-tool-registry.json" "${mutation}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
mutation = sys.argv[2]
registry = json.loads(path.read_text(encoding="utf-8"))

if mutation == "missing_tool_name":
    registry["tools"][0].pop("tool_name", None)
elif mutation == "missing_audit_fields":
    registry["tools"][0].pop("audit_fields", None)
elif mutation == "missing_citations":
    registry["tools"][0].pop("required_citations", None)
elif mutation == "missing_record_families":
    registry["tools"][0].pop("allowed_record_families", None)
elif mutation == "missing_disallowed_authority":
    registry["tools"][0].pop("disallowed_authority", None)
elif mutation == "authority_expansion":
    registry["tools"][0]["authority_ceiling"] = "may_execute_actions"
elif mutation == "missing_record_id_citation":
    registry["tools"][0]["required_citations"] = [
        value for value in registry["tools"][0]["required_citations"]
        if "record_id" not in value
    ]
elif mutation == "missing_trace_audit":
    registry["tools"][0]["audit_fields"].remove("trace_id")
elif mutation == "missing_case_closure_refusal":
    registry["tools"][0]["disallowed_authority"].remove("case_closure")
elif mutation == "missing_required_tool":
    registry["tools"] = [
        tool
        for tool in registry["tools"]
        if tool["tool_name"] != "doctor_explanation"
    ]
elif mutation == "unexpected_tool":
    extra_tool = dict(registry["tools"][0])
    extra_tool["tool_name"] = "autonomous_case_closure"
    registry["tools"].append(extra_tool)
elif mutation == "json_escaped_windows_path":
    slash = chr(92)
    registry["tools"][0]["purpose"] += (
        " See C:" + slash + "Users" + slash + "example" + slash + "private.txt."
    )
elif mutation == "json_escaped_unix_path":
    registry["tools"][0]["purpose"] += " See /" + "Users/example/private.txt."
else:
    raise SystemExit(f"unknown mutation: {mutation}")

path.write_text(json.dumps(registry, indent=2, sort_keys=False) + "\n", encoding="utf-8")
PY
}

remove_text_from_doc() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-59-2-tool-registry-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-59-2-tool-registry-contract.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 59.2 tool registry contract doc"

missing_registry_repo="${workdir}/missing-registry"
create_valid_repo "${missing_registry_repo}"
rm "${missing_registry_repo}/docs/automation/ai-tool-registry.json"
assert_fails_with \
  "${missing_registry_repo}" \
  "Missing Phase 59.2 AI tool registry"

missing_contract_field_repo="${workdir}/missing-contract-field"
create_valid_repo "${missing_contract_field_repo}"
remove_text_from_doc "${missing_contract_field_repo}" \
  "Every tool registry row must include tool name, purpose, allowed record families, required citations, audit fields, disallowed authority, and authority ceiling."
assert_fails_with \
  "${missing_contract_field_repo}" \
  "Missing Phase 59.2 tool registry contract statement: Every tool registry row must include tool name"

for mutation in \
  missing_tool_name \
  missing_audit_fields \
  missing_citations \
  missing_record_families \
  missing_disallowed_authority
do
  mutated_repo="${workdir}/${mutation}"
  create_valid_repo "${mutated_repo}"
  mutate_registry "${mutated_repo}" "${mutation}"
  assert_fails_with "${mutated_repo}" "is missing field(s):"
done

authority_expansion_repo="${workdir}/authority-expansion"
create_valid_repo "${authority_expansion_repo}"
mutate_registry "${authority_expansion_repo}" "authority_expansion"
assert_fails_with \
  "${authority_expansion_repo}" \
  "must keep the advisory-only authority ceiling"

missing_record_id_repo="${workdir}/missing-record-id-citation"
create_valid_repo "${missing_record_id_repo}"
mutate_registry "${missing_record_id_repo}" "missing_record_id_citation"
assert_fails_with \
  "${missing_record_id_repo}" \
  "citation requirements must include record_id"

missing_trace_audit_repo="${workdir}/missing-trace-audit"
create_valid_repo "${missing_trace_audit_repo}"
mutate_registry "${missing_trace_audit_repo}" "missing_trace_audit"
assert_fails_with \
  "${missing_trace_audit_repo}" \
  "is missing audit field(s): trace_id"

missing_case_closure_repo="${workdir}/missing-case-closure-refusal"
create_valid_repo "${missing_case_closure_repo}"
mutate_registry "${missing_case_closure_repo}" "missing_case_closure_refusal"
assert_fails_with \
  "${missing_case_closure_repo}" \
  "is missing disallowed authority: case_closure"

missing_required_tool_repo="${workdir}/missing-required-tool"
create_valid_repo "${missing_required_tool_repo}"
mutate_registry "${missing_required_tool_repo}" "missing_required_tool"
assert_fails_with \
  "${missing_required_tool_repo}" \
  "is missing required tool(s): doctor_explanation"

unexpected_tool_repo="${workdir}/unexpected-tool"
create_valid_repo "${unexpected_tool_repo}"
mutate_registry "${unexpected_tool_repo}" "unexpected_tool"
assert_fails_with \
  "${unexpected_tool_repo}" \
  "contains unexpected tool(s) for this slice: autonomous_case_closure"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
printf '/%s/%s/%s\n' "Users" "example" "private.txt" \
  >>"${local_path_repo}/docs/phase-59-2-tool-registry-contract.md"
assert_fails_with \
  "${local_path_repo}" \
  "workstation-local absolute path detected"

json_escaped_windows_path_repo="${workdir}/json-escaped-windows-path"
create_valid_repo "${json_escaped_windows_path_repo}"
mutate_registry "${json_escaped_windows_path_repo}" "json_escaped_windows_path"
assert_fails_with \
  "${json_escaped_windows_path_repo}" \
  "workstation-local absolute path detected"

json_escaped_unix_path_repo="${workdir}/json-escaped-unix-path"
create_valid_repo "${json_escaped_unix_path_repo}"
mutate_registry "${json_escaped_unix_path_repo}" "json_escaped_unix_path"
assert_fails_with \
  "${json_escaped_unix_path_repo}" \
  "workstation-local absolute path detected"

echo "Phase 59.2 tool registry verifier rejects unregistered tools, missing fields, missing citations, missing audit, authority expansion, and local paths."
