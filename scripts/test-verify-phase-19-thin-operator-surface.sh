#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-19-thin-operator-surface.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md"
  "docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
  "docs/phase-18-wazuh-lab-topology-validation.md"
  "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  "docs/phase-16-release-state-and-first-boot-scope.md"
  "docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase19_operator_surface_docs.py"
  "scripts/verify-phase-19-thin-operator-surface.sh"
  "scripts/test-verify-phase-19-thin-operator-surface.sh"
  "scripts/test-verify-ci-phase-19-workflow-coverage.sh"
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
rm "${missing_validation_repo}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-19-thin-operator-surface-and-daily-analyst-workflow-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 19 thin operator surface validation doc:"

missing_surface_statement_repo="${workdir}/missing-surface-statement"
create_repo "${missing_surface_statement_repo}"
write_required_artifacts "${missing_surface_statement_repo}"
remove_text_from_file \
  "${missing_surface_statement_repo}" \
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md" \
  "AegisOps remains the primary daily work surface for the approved first live slice."
commit_fixture "${missing_surface_statement_repo}"
assert_fails_with "${missing_surface_statement_repo}" "Missing required line in ${missing_surface_statement_repo}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md: AegisOps remains the primary daily work surface for the approved first live slice."

missing_workflow_repo="${workdir}/missing-workflow"
create_repo "${missing_workflow_repo}"
write_required_artifacts "${missing_workflow_repo}"
remove_text_from_file \
  "${missing_workflow_repo}" \
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md" \
  '`daily queue review -> alert inspection -> casework entry -> evidence review -> cited advisory review`'
commit_fixture "${missing_workflow_repo}"
assert_fails_with "${missing_workflow_repo}" "Missing required line in ${missing_workflow_repo}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md: \`daily queue review -> alert inspection -> casework entry -> evidence review -> cited advisory review\`"

missing_deferred_boundary_repo="${workdir}/missing-deferred-boundary"
create_repo "${missing_deferred_boundary_repo}"
write_required_artifacts "${missing_deferred_boundary_repo}"
remove_text_from_file \
  "${missing_deferred_boundary_repo}" \
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md" \
  "- medium-risk or high-risk live action wiring;"
commit_fixture "${missing_deferred_boundary_repo}"
assert_fails_with "${missing_deferred_boundary_repo}" "Missing required line in ${missing_deferred_boundary_repo}/docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md: - medium-risk or high-risk live action wiring;"

missing_test_repo="${workdir}/missing-test"
create_repo "${missing_test_repo}"
write_required_artifacts "${missing_test_repo}"
remove_text_from_file \
  "${missing_test_repo}" \
  "control-plane/tests/test_phase19_operator_surface_docs.py" \
  "    def test_phase19_design_doc_defines_operator_surface_workflow_and_deferred_scope(self) -> None:"
commit_fixture "${missing_test_repo}"
assert_fails_with "${missing_test_repo}" "Missing required line in ${missing_test_repo}/control-plane/tests/test_phase19_operator_surface_docs.py:     def test_phase19_design_doc_defines_operator_surface_workflow_and_deferred_scope(self) -> None:"

missing_ci_repo="${workdir}/missing-ci"
create_repo "${missing_ci_repo}"
write_required_artifacts "${missing_ci_repo}"
remove_text_from_file \
  "${missing_ci_repo}" \
  ".github/workflows/ci.yml" \
  "      - name: Run Phase 19 workflow coverage guard"
commit_fixture "${missing_ci_repo}"
assert_fails_with "${missing_ci_repo}" "Missing required line in ${missing_ci_repo}/.github/workflows/ci.yml:       - name: Run Phase 19 workflow coverage guard"

echo "Phase 19 thin operator surface verifier fails closed for missing reviewed coverage."
