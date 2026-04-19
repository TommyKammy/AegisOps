#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-20-low-risk-action-boundary.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary-validation.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md"
  "docs/automation-substrate-contract.md"
  "docs/response-action-safety-model.md"
  "docs/control-plane-state-model.md"
  "docs/secops-business-hours-operating-model.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase20_low_risk_action_docs.py"
  "control-plane/tests/test_phase20_low_risk_action_validation.py"
  "control-plane/tests/test_service_persistence_action_reconciliation.py"
  "scripts/ci-phase-contract-commands.sh"
  "scripts/ci-workflow-phase-helper.sh"
  "scripts/run-ci-phase-contract.sh"
  "scripts/verify-phase-20-low-risk-action-boundary.sh"
  "scripts/test-verify-phase-20-low-risk-action-boundary.sh"
  "scripts/test-verify-ci-phase-20-workflow-coverage.sh"
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
rm "${missing_validation_repo}/docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 20 low-risk action validation doc:"

missing_action_repo="${workdir}/missing-action"
create_repo "${missing_action_repo}"
write_required_artifacts "${missing_action_repo}"
remove_text_from_file \
  "${missing_action_repo}" \
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md" \
  'The approved first live low-risk action for Phase 20 is `notify_identity_owner`.'
commit_fixture "${missing_action_repo}"
assert_fails_with "${missing_action_repo}" "Missing required line in ${missing_action_repo}/docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md: The approved first live low-risk action for Phase 20 is \`notify_identity_owner\`."

missing_boundary_repo="${workdir}/missing-boundary"
create_repo "${missing_boundary_repo}"
write_required_artifacts "${missing_boundary_repo}"
remove_text_from_file \
  "${missing_boundary_repo}" \
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md" \
  '`reviewed Phase 19 casework -> explicit action request -> human approval -> reviewed Shuffle delegation -> authoritative reconciliation`'
commit_fixture "${missing_boundary_repo}"
assert_fails_with "${missing_boundary_repo}" "Missing required line in ${missing_boundary_repo}/docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md: \`reviewed Phase 19 casework -> explicit action request -> human approval -> reviewed Shuffle delegation -> authoritative reconciliation\`"

missing_deferred_scope_repo="${workdir}/missing-deferred-scope"
create_repo "${missing_deferred_scope_repo}"
write_required_artifacts "${missing_deferred_scope_repo}"
remove_text_from_file \
  "${missing_deferred_scope_repo}" \
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md" \
  '- policy-authorized unattended low-risk execution;'
commit_fixture "${missing_deferred_scope_repo}"
assert_fails_with "${missing_deferred_scope_repo}" "Missing required line in ${missing_deferred_scope_repo}/docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md: - policy-authorized unattended low-risk execution;"

missing_docs_test_repo="${workdir}/missing-docs-test"
create_repo "${missing_docs_test_repo}"
write_required_artifacts "${missing_docs_test_repo}"
remove_text_from_file \
  "${missing_docs_test_repo}" \
  "control-plane/tests/test_phase20_low_risk_action_docs.py" \
  "    def test_phase20_design_doc_defines_one_approved_low_risk_action_and_boundary("
commit_fixture "${missing_docs_test_repo}"
assert_fails_with "${missing_docs_test_repo}" "Missing required line in ${missing_docs_test_repo}/control-plane/tests/test_phase20_low_risk_action_docs.py:     def test_phase20_design_doc_defines_one_approved_low_risk_action_and_boundary("

missing_runtime_validation_test_repo="${workdir}/missing-runtime-validation-test"
create_repo "${missing_runtime_validation_test_repo}"
write_required_artifacts "${missing_runtime_validation_test_repo}"
remove_text_from_file \
  "${missing_runtime_validation_test_repo}" \
  "control-plane/tests/test_phase20_low_risk_action_validation.py" \
  "    def test_reviewed_runtime_path_covers_phase20_low_risk_action_boundary(self) -> None:"
commit_fixture "${missing_runtime_validation_test_repo}"
assert_fails_with "${missing_runtime_validation_test_repo}" "Missing required line in ${missing_runtime_validation_test_repo}/control-plane/tests/test_phase20_low_risk_action_validation.py:     def test_reviewed_runtime_path_covers_phase20_low_risk_action_boundary(self) -> None:"

missing_ci_repo="${workdir}/missing-ci"
create_repo "${missing_ci_repo}"
write_required_artifacts "${missing_ci_repo}"
remove_text_from_file \
  "${missing_ci_repo}" \
  ".github/workflows/ci.yml" \
  "      - name: Run Phase 20 workflow coverage guard"
commit_fixture "${missing_ci_repo}"
assert_fails_with "${missing_ci_repo}" "Missing required line in ${missing_ci_repo}/.github/workflows/ci.yml:       - name: Run Phase 20 workflow coverage guard"

echo "Phase 20 low-risk action verifier fails closed for missing reviewed coverage."
