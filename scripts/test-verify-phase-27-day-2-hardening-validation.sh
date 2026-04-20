#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-27-day-2-hardening-validation.sh"
workflow_guard="${repo_root}/scripts/test-verify-ci-phase-27-workflow-coverage.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"
guard_stdout="${workdir}/guard.out"
guard_stderr="${workdir}/guard.err"

required_artifacts=(
  "docs/phase-27-day-2-hardening-validation.md"
  "control-plane/tests/test_phase27_day2_runtime_contract.py"
  "control-plane/tests/test_service_persistence_restore_readiness.py"
  "control-plane/tests/test_phase21_runtime_auth_validation.py"
  "control-plane/tests/test_runtime_secret_boundary.py"
  "control-plane/tests/test_phase27_day2_hardening_validation.py"
  "scripts/ci-phase-contract-commands.sh"
  "scripts/ci-workflow-phase-helper.sh"
  "scripts/run-ci-phase-contract.sh"
  "scripts/verify-phase-27-day-2-hardening-validation.sh"
  "scripts/test-verify-phase-27-day-2-hardening-validation.sh"
  "scripts/test-verify-ci-phase-27-workflow-coverage.sh"
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

replace_text_in_file() {
  local target="$1"
  local path="$2"
  local expected_text="$3"
  local replacement_text="$4"

  EXPECTED_TEXT="${expected_text}" REPLACEMENT_TEXT="${replacement_text}" perl -0pi -e 's/\Q$ENV{EXPECTED_TEXT}\E/$ENV{REPLACEMENT_TEXT}/g' "${target}/${path}"
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

assert_guard_passes() {
  local target="$1"

  if ! bash "${workflow_guard}" "${target}" >"${guard_stdout}" 2>"${guard_stderr}"; then
    echo "Expected workflow guard to pass for ${target}" >&2
    cat "${guard_stderr}" >&2
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

assert_guard_fails_with() {
  local target="$1"
  local expected="$2"

  if bash "${workflow_guard}" "${target}" >"${guard_stdout}" 2>"${guard_stderr}"; then
    echo "Expected workflow guard to fail for ${target}" >&2
    exit 1
  fi

  if ! grep -F -- "${expected}" "${guard_stderr}" >/dev/null; then
    echo "Expected workflow guard failure output to contain: ${expected}" >&2
    cat "${guard_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_repo "${valid_repo}"
write_required_artifacts "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"
assert_guard_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
write_required_artifacts "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-27-day-2-hardening-validation.md"
git -C "${missing_doc_repo}" add -u docs/phase-27-day-2-hardening-validation.md
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing Phase 27 validation document:"

missing_drill_repo="${workdir}/missing-drill"
create_repo "${missing_drill_repo}"
write_required_artifacts "${missing_drill_repo}"
remove_text_from_file \
  "${missing_drill_repo}" \
  "docs/phase-27-day-2-hardening-validation.md" \
  "| Degraded-mode visibility | \`test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state\` proves readiness keeps source and automation degradation visible instead of implying healthy operation from silence. | \`test_service_phase21_readiness_surfaces_source_and_automation_health\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"
commit_fixture "${missing_drill_repo}"
assert_fails_with "${missing_drill_repo}" "Missing required line in ${missing_drill_repo}/docs/phase-27-day-2-hardening-validation.md: | Degraded-mode visibility | \`test_phase27_readiness_contract_surfaces_degraded_source_and_automation_state\` proves readiness keeps source and automation degradation visible instead of implying healthy operation from silence. | \`test_service_phase21_readiness_surfaces_source_and_automation_health\` | \`python3 -m unittest control-plane.tests.test_phase27_day2_runtime_contract\` |"

missing_ci_repo="${workdir}/missing-ci"
create_repo "${missing_ci_repo}"
write_required_artifacts "${missing_ci_repo}"
remove_text_from_file \
  "${missing_ci_repo}" \
  ".github/workflows/ci.yml" \
  "      - name: Run Phase 27 workflow coverage guard"
commit_fixture "${missing_ci_repo}"
assert_fails_with "${missing_ci_repo}" "Missing required line in ${missing_ci_repo}/.github/workflows/ci.yml:       - name: Run Phase 27 workflow coverage guard"

unnamed_step_repo="${workdir}/unnamed-step-boundary"
create_repo "${unnamed_step_repo}"
write_required_artifacts "${unnamed_step_repo}"
replace_text_in_file \
  "${unnamed_step_repo}" \
  ".github/workflows/ci.yml" \
  $'      - name: Run Phase 27 workflow coverage guard\n        run: bash scripts/test-verify-ci-phase-27-workflow-coverage.sh\n' \
  $'      - name: Run Phase 27 workflow coverage guard\n        if: ${{ always() }}\n\n      - run: bash scripts/test-verify-ci-phase-27-workflow-coverage.sh\n'
commit_fixture "${unnamed_step_repo}"
assert_guard_fails_with "${unnamed_step_repo}" "Missing dedicated Phase 27 workflow coverage guard step in CI workflow: Run Phase 27 workflow coverage guard"

echo "Phase 27 day-2 hardening verifier fails closed for missing drills and CI wiring."
