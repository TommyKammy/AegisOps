#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-22-operator-trust-boundary.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md"
  "docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence-validation.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
  "docs/phase-21-production-like-hardening-boundary-and-sequence.md"
  "docs/control-plane-state-model.md"
  "docs/automation-substrate-contract.md"
  "docs/response-action-safety-model.md"
  "docs/secops-business-hours-operating-model.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase22_end_to_end_validation.py"
  "control-plane/tests/test_phase22_operator_trust_boundary_docs.py"
  "control-plane/tests/test_phase22_operator_trust_boundary_validation.py"
  "scripts/verify-phase-22-operator-trust-boundary.sh"
  "scripts/test-verify-phase-22-operator-trust-boundary.sh"
  "scripts/test-verify-ci-phase-22-workflow-coverage.sh"
  ".github/workflows/ci.yml"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/control-plane/tests" "${target}/scripts" "${target}/.github/workflows"
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

missing_validation_repo="${workdir}/missing-validation"
create_repo "${missing_validation_repo}"
write_required_artifacts "${missing_validation_repo}"
rm "${missing_validation_repo}/docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 22 operator trust validation doc:"

missing_semantics_repo="${workdir}/missing-semantics"
create_repo "${missing_semantics_repo}"
write_required_artifacts "${missing_semantics_repo}"
remove_text_from_file \
  "${missing_semantics_repo}" \
  "docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md" \
  'Pending means the action request exists, the reviewed approval decision is not yet resolved, and no delegation or execution may proceed.'
commit_fixture "${missing_semantics_repo}"
assert_fails_with "${missing_semantics_repo}" "Missing required line in ${missing_semantics_repo}/docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md: Pending means the action request exists, the reviewed approval decision is not yet resolved, and no delegation or execution may proceed."

missing_mismatch_repo="${workdir}/missing-mismatch"
create_repo "${missing_mismatch_repo}"
write_required_artifacts "${missing_mismatch_repo}"
remove_text_from_file \
  "${missing_mismatch_repo}" \
  "docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md" \
  'The reviewed mismatch taxonomy is limited to delegation mismatch, execution mismatch, and reconciliation mismatch.'
commit_fixture "${missing_mismatch_repo}"
assert_fails_with "${missing_mismatch_repo}" "Missing required line in ${missing_mismatch_repo}/docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md: The reviewed mismatch taxonomy is limited to delegation mismatch, execution mismatch, and reconciliation mismatch."

missing_handoff_repo="${workdir}/missing-handoff"
create_repo "${missing_handoff_repo}"
write_required_artifacts "${missing_handoff_repo}"
remove_text_from_file \
  "${missing_handoff_repo}" \
  "docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md" \
  'The minimum reviewed record additions in Phase 22 are manual fallback visibility, after-hours handoff visibility, escalation-note visibility, and actor identity display expectations.'
commit_fixture "${missing_handoff_repo}"
assert_fails_with "${missing_handoff_repo}" "Missing required line in ${missing_handoff_repo}/docs/phase-22-operator-trust-and-workflow-ergonomics-boundary-and-sequence.md: The minimum reviewed record additions in Phase 22 are manual fallback visibility, after-hours handoff visibility, escalation-note visibility, and actor identity display expectations."

missing_ci_repo="${workdir}/missing-ci"
create_repo "${missing_ci_repo}"
write_required_artifacts "${missing_ci_repo}"
remove_text_from_file \
  "${missing_ci_repo}" \
  ".github/workflows/ci.yml" \
  "      - name: Run Phase 22 workflow coverage guard"
commit_fixture "${missing_ci_repo}"
assert_fails_with "${missing_ci_repo}" "Missing required line in ${missing_ci_repo}/.github/workflows/ci.yml:       - name: Run Phase 22 workflow coverage guard"

echo "Phase 22 operator trust verifier fails closed for missing reviewed coverage."
