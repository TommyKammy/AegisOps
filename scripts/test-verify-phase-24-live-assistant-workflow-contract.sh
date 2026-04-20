#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-24-live-assistant-workflow-contract.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "README.md"
  "docs/Revised Phase23-29 Epic Roadmap.md"
  "docs/control-plane-state-model.md"
  "docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
  "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md"
  "docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract-validation.md"
  "control-plane/tests/test_phase24_live_assistant_workflow_docs.py"
  "control-plane/tests/test_phase24_live_assistant_validation.py"
  "scripts/ci-phase-contract-commands.sh"
  "scripts/ci-workflow-phase-helper.sh"
  "scripts/run-ci-phase-contract.sh"
  "scripts/verify-phase-24-live-assistant-workflow-contract.sh"
  "scripts/test-verify-phase-24-live-assistant-workflow-contract.sh"
  "scripts/test-verify-ci-phase-24-workflow-coverage.sh"
  ".github/workflows/ci.yml"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/control-plane/tests" "${target}/docs" "${target}/scripts" "${target}/.github/workflows"
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

replace_text_in_file() {
  local target="$1"
  local path="$2"
  local original_text="$3"
  local replacement_text="$4"

  ORIGINAL_TEXT="${original_text}" REPLACEMENT_TEXT="${replacement_text}" \
    perl -0pi -e 's/\Q$ENV{ORIGINAL_TEXT}\E/$ENV{REPLACEMENT_TEXT}/g' "${target}/${path}"
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

missing_design_repo="${workdir}/missing-design"
create_repo "${missing_design_repo}"
write_required_artifacts "${missing_design_repo}"
rm "${missing_design_repo}/docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md"
git -C "${missing_design_repo}" add -u docs/phase-24-first-live-assistant-workflow-family-and-trusted-output-contract.md
commit_fixture "${missing_design_repo}"
assert_fails_with "${missing_design_repo}" "Missing Phase 24 workflow contract design document:"

missing_readme_alignment_repo="${workdir}/missing-readme-alignment"
create_repo "${missing_readme_alignment_repo}"
write_required_artifacts "${missing_readme_alignment_repo}"
remove_text_from_file \
  "${missing_readme_alignment_repo}" \
  "README.md" \
  "bounded live assistant workflow family"
commit_fixture "${missing_readme_alignment_repo}"
assert_fails_with "${missing_readme_alignment_repo}" "Missing required text in ${missing_readme_alignment_repo}/README.md: bounded live assistant workflow family"

missing_ci_repo="${workdir}/missing-ci"
create_repo "${missing_ci_repo}"
write_required_artifacts "${missing_ci_repo}"
remove_text_from_file \
  "${missing_ci_repo}" \
  ".github/workflows/ci.yml" \
  "        run: bash scripts/test-verify-ci-phase-24-workflow-coverage.sh"
commit_fixture "${missing_ci_repo}"
assert_fails_with "${missing_ci_repo}" "Missing active command in CI step \"Run Phase 24 workflow coverage guard\": bash scripts/test-verify-ci-phase-24-workflow-coverage.sh"

commented_validation_command_repo="${workdir}/commented-validation-command"
create_repo "${commented_validation_command_repo}"
write_required_artifacts "${commented_validation_command_repo}"
replace_text_in_file \
  "${commented_validation_command_repo}" \
  ".github/workflows/ci.yml" \
  "          bash scripts/verify-phase-24-live-assistant-workflow-contract.sh" \
  "          # bash scripts/verify-phase-24-live-assistant-workflow-contract.sh"
commit_fixture "${commented_validation_command_repo}"
assert_fails_with "${commented_validation_command_repo}" "Missing active command in CI step \"Run Phase 24 live assistant workflow contract validation\": bash scripts/verify-phase-24-live-assistant-workflow-contract.sh"

echo "Phase 24 workflow contract verifier fails closed for missing docs, README alignment, and CI wiring."
