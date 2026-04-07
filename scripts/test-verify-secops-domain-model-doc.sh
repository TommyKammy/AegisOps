#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-secops-domain-model-doc.sh"
canonical_doc="${repo_root}/docs/secops-domain-model.md"

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

  cp "${canonical_doc}" "${target}/docs/secops-domain-model.md"
  git -C "${target}" add docs/secops-domain-model.md
}

remove_text_from_doc() {
  local target="$1"
  local expected_text="$2"
  local doc_path="${target}/docs/secops-domain-model.md"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${doc_path}"
  git -C "${target}" add docs/secops-domain-model.md
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

  if ! grep -F "${expected}" "${fail_stderr}" >/dev/null; then
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
assert_fails_with "${missing_doc_repo}" "Missing SecOps domain model document:"

missing_boundary_repo="${workdir}/missing-boundary"
create_repo "${missing_boundary_repo}"
write_canonical_doc "${missing_boundary_repo}"
remove_text_from_doc "${missing_boundary_repo}" "Substrate detection records, analytic signals, workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states."
commit_fixture "${missing_boundary_repo}"
assert_fails_with "${missing_boundary_repo}" "Substrate detection records, analytic signals, workflow runs, and future case state must remain separate records and must not be treated as interchangeable identifiers or lifecycle states."

missing_dedup_repo="${workdir}/missing-dedup"
create_repo "${missing_dedup_repo}"
write_canonical_doc "${missing_dedup_repo}"
remove_text_from_doc "${missing_dedup_repo}" "Deduplication means additional findings are attached to an existing alert or case when they restate the same analytic claim against materially the same operational target within the active review window."
commit_fixture "${missing_dedup_repo}"
assert_fails_with "${missing_dedup_repo}" "Deduplication means additional findings are attached to an existing alert or case when they restate the same analytic claim against materially the same operational target within the active review window."

missing_signal_repo="${workdir}/missing-signal"
create_repo "${missing_signal_repo}"
write_canonical_doc "${missing_signal_repo}"
remove_text_from_doc "${missing_signal_repo}" "An analytic signal is the common upstream product primitive from which alert or case routing decisions begin."
commit_fixture "${missing_signal_repo}"
assert_fails_with "${missing_signal_repo}" "An analytic signal is the common upstream product primitive from which alert or case routing decisions begin."

missing_action_execution_ownership_repo="${workdir}/missing-action-execution-ownership"
create_repo "${missing_action_execution_ownership_repo}"
write_canonical_doc "${missing_action_execution_ownership_repo}"
remove_text_from_doc "${missing_action_execution_ownership_repo}" '| `Action Execution` | AegisOps control-plane action-execution record | `Action Execution` remains the authoritative control-plane record for approved-versus-actual execution, while reviewed automation substrates and executor surfaces contribute correlated run identifiers, receipts, step progress, and other surface-local runtime evidence. |'
commit_fixture "${missing_action_execution_ownership_repo}"
assert_fails_with "${missing_action_execution_ownership_repo}" '| `Action Execution` | AegisOps control-plane action-execution record | `Action Execution` remains the authoritative control-plane record for approved-versus-actual execution, while reviewed automation substrates and executor surfaces contribute correlated run identifiers, receipts, step progress, and other surface-local runtime evidence. |'

echo "verify-secops-domain-model-doc tests passed"
