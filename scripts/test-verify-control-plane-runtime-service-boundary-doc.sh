#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-control-plane-runtime-service-boundary-doc.sh"
canonical_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_canonical_doc() {
  local target="$1"

  cp "${canonical_doc}" "${target}/docs/control-plane-runtime-service-boundary.md"
  git -C "${target}" add docs/control-plane-runtime-service-boundary.md
}

remove_text_from_doc() {
  local target="$1"
  local expected_text="$2"
  local doc_path="${target}/docs/control-plane-runtime-service-boundary.md"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${doc_path}"
  git -C "${target}" add docs/control-plane-runtime-service-boundary.md
}

commit_fixture() {
  local target="$1"

  git -C "${target}" commit --allow-empty -q -m "fixture"
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

  if ! grep -F -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_canonical_doc "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing control-plane runtime boundary document:"

missing_runtime_home_repo="${workdir}/missing-runtime-home"
create_repo "${missing_runtime_home_repo}"
write_canonical_doc "${missing_runtime_home_repo}"
remove_text_from_doc "${missing_runtime_home_repo}" 'The approved repository home for live control-plane application code is the top-level `control-plane/` directory.'
commit_fixture "${missing_runtime_home_repo}"
assert_fails_with "${missing_runtime_home_repo}" 'The approved repository home for live control-plane application code is the top-level `control-plane/` directory.'

missing_postgres_split_repo="${workdir}/missing-postgres-split"
create_repo "${missing_postgres_split_repo}"
write_canonical_doc "${missing_postgres_split_repo}"
remove_text_from_doc "${missing_postgres_split_repo}" '`postgres/control-plane/` remains the persistence contract home for reviewed schema and migration assets, but it is not the repository home for live control-plane application code.'
commit_fixture "${missing_postgres_split_repo}"
assert_fails_with "${missing_postgres_split_repo}" '`postgres/control-plane/` remains the persistence contract home for reviewed schema and migration assets, but it is not the repository home for live control-plane application code.'

missing_non_goal_repo="${workdir}/missing-non-goal"
create_repo "${missing_non_goal_repo}"
write_canonical_doc "${missing_non_goal_repo}"
remove_text_from_doc "${missing_non_goal_repo}" '- write-capable response execution or direct replacement of n8n as the execution plane;'
commit_fixture "${missing_non_goal_repo}"
assert_fails_with "${missing_non_goal_repo}" '- write-capable response execution or direct replacement of n8n as the execution plane;'

echo "Control-plane runtime boundary verifier enforces required placement and scope statements."
