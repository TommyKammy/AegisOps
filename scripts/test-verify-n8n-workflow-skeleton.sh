#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-n8n-workflow-skeleton.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/n8n"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

commit_fixture() {
  local target="$1"

  git -C "${target}" add n8n
  git -C "${target}" commit -q -m "fixture"
}

create_workflow_skeleton() {
  local target="$1"

  mkdir -p \
    "${target}/n8n/workflows/aegisops_alert_ingest" \
    "${target}/n8n/workflows/aegisops_approve" \
    "${target}/n8n/workflows/aegisops_enrich" \
    "${target}/n8n/workflows/aegisops_notify" \
    "${target}/n8n/workflows/aegisops_response"
  : > "${target}/n8n/workflows/aegisops_alert_ingest/.gitkeep"
  : > "${target}/n8n/workflows/aegisops_approve/.gitkeep"
  : > "${target}/n8n/workflows/aegisops_enrich/.gitkeep"
  : > "${target}/n8n/workflows/aegisops_notify/.gitkeep"
  : > "${target}/n8n/workflows/aegisops_response/.gitkeep"
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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
create_workflow_skeleton "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_root_repo="${workdir}/missing-root"
create_repo "${missing_root_repo}"
git -C "${missing_root_repo}" commit -q --allow-empty -m "fixture"
assert_fails_with "${missing_root_repo}" "Missing n8n workflow skeleton directory"

missing_category_repo="${workdir}/missing-category"
create_repo "${missing_category_repo}"
create_workflow_skeleton "${missing_category_repo}"
rm -rf "${missing_category_repo}/n8n/workflows/aegisops_notify"
commit_fixture "${missing_category_repo}"
assert_fails_with "${missing_category_repo}" "aegisops_notify"

logic_file_repo="${workdir}/logic-file"
create_repo "${logic_file_repo}"
create_workflow_skeleton "${logic_file_repo}"
printf '%s\n' '{"name":"aegisops_response_host_isolation"}' > \
  "${logic_file_repo}/n8n/workflows/aegisops_response/bootstrap.json"
commit_fixture "${logic_file_repo}"
assert_fails_with "${logic_file_repo}" "must not introduce workflow logic"

extra_directory_repo="${workdir}/extra-directory"
create_repo "${extra_directory_repo}"
create_workflow_skeleton "${extra_directory_repo}"
mkdir -p "${extra_directory_repo}/n8n/workflows/aegisops_notify/archive"
commit_fixture "${extra_directory_repo}"
assert_fails_with "${extra_directory_repo}" "Unexpected entries:"

echo "verify-n8n-workflow-skeleton tests passed"
