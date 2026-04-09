#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-16-release-state-and-first-boot-scope.sh"
canonical_scope_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-scope.md"
canonical_validation_doc="${repo_root}/docs/phase-16-release-state-and-first-boot-validation.md"
canonical_runtime_boundary_doc="${repo_root}/docs/control-plane-runtime-service-boundary.md"
canonical_architecture_doc="${repo_root}/docs/architecture.md"
canonical_network_doc="${repo_root}/docs/network-exposure-and-access-path-policy.md"
canonical_storage_doc="${repo_root}/docs/storage-layout-and-mount-policy.md"
canonical_readme="${repo_root}/README.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/scripts"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_canonical_artifacts() {
  local target="$1"

  cp "${canonical_scope_doc}" "${target}/docs/phase-16-release-state-and-first-boot-scope.md"
  cp "${canonical_validation_doc}" "${target}/docs/phase-16-release-state-and-first-boot-validation.md"
  cp "${canonical_runtime_boundary_doc}" "${target}/docs/control-plane-runtime-service-boundary.md"
  cp "${canonical_architecture_doc}" "${target}/docs/architecture.md"
  cp "${canonical_network_doc}" "${target}/docs/network-exposure-and-access-path-policy.md"
  cp "${canonical_storage_doc}" "${target}/docs/storage-layout-and-mount-policy.md"
  cp "${canonical_readme}" "${target}/README.md"
  cp "${verifier}" "${target}/scripts/verify-phase-16-release-state-and-first-boot-scope.sh"
  cp "${repo_root}/scripts/test-verify-phase-16-release-state-and-first-boot-scope.sh" "${target}/scripts/test-verify-phase-16-release-state-and-first-boot-scope.sh"
  git -C "${target}" add .
}

remove_text_from_doc() {
  local target="$1"
  local doc_path="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${doc_path}"
  git -C "${target}" add "${doc_path}"
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
write_canonical_artifacts "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_scope_repo="${workdir}/missing-scope"
create_repo "${missing_scope_repo}"
write_canonical_artifacts "${missing_scope_repo}"
rm "${missing_scope_repo}/docs/phase-16-release-state-and-first-boot-scope.md"
git -C "${missing_scope_repo}" add -u
commit_fixture "${missing_scope_repo}"
assert_fails_with "${missing_scope_repo}" "Missing Phase 16 release-state scope document:"

missing_required_component_repo="${workdir}/missing-required-component"
create_repo "${missing_required_component_repo}"
write_canonical_artifacts "${missing_required_component_repo}"
remove_text_from_doc "${missing_required_component_repo}" "${missing_required_component_repo}/docs/phase-16-release-state-and-first-boot-scope.md" "- PostgreSQL as the AegisOps-owned persistence dependency for control-plane state;"
commit_fixture "${missing_required_component_repo}"
assert_fails_with "${missing_required_component_repo}" "- PostgreSQL as the AegisOps-owned persistence dependency for control-plane state;"

missing_optional_boundary_repo="${workdir}/missing-optional-boundary"
create_repo "${missing_optional_boundary_repo}"
write_canonical_artifacts "${missing_optional_boundary_repo}"
remove_text_from_doc "${missing_optional_boundary_repo}" "${missing_optional_boundary_repo}/docs/phase-16-release-state-and-first-boot-scope.md" "- n8n as a required first-boot dependency or orchestration prerequisite;"
commit_fixture "${missing_optional_boundary_repo}"
assert_fails_with "${missing_optional_boundary_repo}" "- n8n as a required first-boot dependency or orchestration prerequisite;"

missing_validation_note_repo="${workdir}/missing-validation-note"
create_repo "${missing_validation_note_repo}"
write_canonical_artifacts "${missing_validation_note_repo}"
remove_text_from_doc "${missing_validation_note_repo}" "${missing_validation_note_repo}/docs/phase-16-release-state-and-first-boot-validation.md" "Confirmed the Phase 16 definition of done gives Phase 17 a clear bootability target without approving concrete containerization or live substrate wiring in this phase."
commit_fixture "${missing_validation_note_repo}"
assert_fails_with "${missing_validation_note_repo}" "Confirmed the Phase 16 definition of done gives Phase 17 a clear bootability target without approving concrete containerization or live substrate wiring in this phase."

echo "Phase 16 release-state verifier enforces required first-boot scope and validation statements."
