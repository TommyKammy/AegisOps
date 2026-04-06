#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-10-thesis-consistency.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_docs=(
  "README.md"
  "docs/requirements-baseline.md"
  "docs/architecture.md"
  "docs/secops-domain-model.md"
  "docs/control-plane-state-model.md"
  "docs/repository-structure-baseline.md"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_canonical_docs() {
  local target="$1"
  local doc_path

  for doc_path in "${required_docs[@]}"; do
    mkdir -p "${target}/$(dirname "${doc_path}")"
    cp "${repo_root}/${doc_path}" "${target}/${doc_path}"
    git -C "${target}" add "${doc_path}"
  done
}

remove_text_from_doc() {
  local target="$1"
  local path="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${target}/${path}"
  git -C "${target}" add "${path}"
}

append_text_to_doc() {
  local target="$1"
  local path="$2"
  local text="$3"

  printf '\n%s\n' "${text}" >> "${target}/${path}"
  git -C "${target}" add "${path}"
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
write_canonical_docs "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
write_canonical_docs "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/control-plane-state-model.md"
git -C "${missing_doc_repo}" add -u docs/control-plane-state-model.md
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Phase 10 thesis artifact: docs/control-plane-state-model.md"

missing_marker_repo="${workdir}/missing-marker"
create_repo "${missing_marker_repo}"
write_canonical_docs "${missing_marker_repo}"
remove_text_from_doc "${missing_marker_repo}" "docs/architecture.md" "The AegisOps control plane is the authoritative owner of policy-sensitive records, approval decisions, evidence linkage, action intent, and reconciliation truth across substrate boundaries."
commit_fixture "${missing_marker_repo}"
assert_fails_with "${missing_marker_repo}" "Missing architecture statement: The AegisOps control plane is the authoritative owner of policy-sensitive records, approval decisions, evidence linkage, action intent, and reconciliation truth across substrate boundaries."

contradiction_repo="${workdir}/contradiction"
create_repo "${contradiction_repo}"
write_canonical_docs "${contradiction_repo}"
append_text_to_doc "${contradiction_repo}" "README.md" "**AegisOps** is primarily an OpenSearch-and-n8n product core."
commit_fixture "${contradiction_repo}"
assert_fails_with "${contradiction_repo}" "Forbidden thesis contradiction in README.md: **AegisOps** is primarily an OpenSearch-and-n8n product core."

echo "Phase 10 thesis consistency verifier fails closed for missing artifacts and obvious thesis drift."
