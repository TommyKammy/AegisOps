#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-23-authority-closure.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "control-plane/tests/test_phase23_end_to_end_validation.py"
  "control-plane/tests/test_phase23_approval_surface_validation.py"
  "control-plane/tests/test_phase23_transition_logging_validation.py"
  "control-plane/tests/test_phase23_substrate_simplification_validation.py"
  "scripts/verify-phase-23-authority-closure.sh"
  "scripts/test-verify-phase-23-authority-closure.sh"
  "scripts/test-verify-ci-phase-23-workflow-coverage.sh"
  ".github/workflows/ci.yml"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/control-plane/tests" "${target}/scripts" "${target}/.github/workflows"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_required_artifacts() {
  local target="$1"
  local artifact=""

  for artifact in "${required_artifacts[@]}"; do
    mkdir -p "${target}/$(dirname "${artifact}")"
    cp "${repo_root}/${artifact}" "${target}/${artifact}"
    git -C "${target}" add "${artifact}"
  done
}

remove_text_from_file() {
  local target="$1"
  local path="$2"
  local expected_text="$3"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${target}/${path}"
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
write_required_artifacts "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_e2e_repo="${workdir}/missing-e2e"
create_repo "${missing_e2e_repo}"
write_required_artifacts "${missing_e2e_repo}"
rm "${missing_e2e_repo}/control-plane/tests/test_phase23_end_to_end_validation.py"
git -C "${missing_e2e_repo}" add -u control-plane/tests/test_phase23_end_to_end_validation.py
commit_fixture "${missing_e2e_repo}"
assert_fails_with "${missing_e2e_repo}" "Missing Phase 23 end-to-end validation unittest:"

missing_degraded_repo="${workdir}/missing-degraded"
create_repo "${missing_degraded_repo}"
write_required_artifacts "${missing_degraded_repo}"
remove_text_from_file \
  "${missing_degraded_repo}" \
  "control-plane/tests/test_phase23_end_to_end_validation.py" \
  '            "reviewed_delegation_missing_after_approval",'
commit_fixture "${missing_degraded_repo}"
assert_fails_with "${missing_degraded_repo}" "Missing required line in ${missing_degraded_repo}/control-plane/tests/test_phase23_end_to_end_validation.py:             \"reviewed_delegation_missing_after_approval\","

missing_self_approval_repo="${workdir}/missing-self-approval"
create_repo "${missing_self_approval_repo}"
write_required_artifacts "${missing_self_approval_repo}"
remove_text_from_file \
  "${missing_self_approval_repo}" \
  "control-plane/tests/test_phase23_approval_surface_validation.py" \
  "    def test_reviewed_runtime_path_rejects_self_approval(self) -> None:"
commit_fixture "${missing_self_approval_repo}"
assert_fails_with "${missing_self_approval_repo}" "Missing required line in ${missing_self_approval_repo}/control-plane/tests/test_phase23_approval_surface_validation.py:     def test_reviewed_runtime_path_rejects_self_approval(self) -> None:"

missing_ci_repo="${workdir}/missing-ci"
create_repo "${missing_ci_repo}"
write_required_artifacts "${missing_ci_repo}"
remove_text_from_file \
  "${missing_ci_repo}" \
  ".github/workflows/ci.yml" \
  "      - name: Run Phase 23 workflow coverage guard"
commit_fixture "${missing_ci_repo}"
assert_fails_with "${missing_ci_repo}" "Missing required line in ${missing_ci_repo}/.github/workflows/ci.yml:       - name: Run Phase 23 workflow coverage guard"

echo "Phase 23 authority-closure verifier fails closed for missing runtime coverage and CI wiring."
