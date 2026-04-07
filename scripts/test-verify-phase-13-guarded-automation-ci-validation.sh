#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-13-guarded-automation-ci-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/automation-substrate-contract.md"
  "docs/architecture.md"
  "docs/phase-13-guarded-automation-ci-validation.md"
  "control-plane/tests/test_service_persistence.py"
  ".github/workflows/ci.yml"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/control-plane/tests" "${target}/.github/workflows"
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
  local old_text="$3"
  local new_text="$4"

  OLD_TEXT="${old_text}" NEW_TEXT="${new_text}" perl -0pi -e 's/\Q$ENV{OLD_TEXT}\E/$ENV{NEW_TEXT}/g' "${target}/${path}"
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
rm "${missing_validation_repo}/docs/phase-13-guarded-automation-ci-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-13-guarded-automation-ci-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 13 guarded-automation CI validation record:"

missing_test_repo="${workdir}/missing-test"
create_repo "${missing_test_repo}"
write_required_artifacts "${missing_test_repo}"
remove_text_from_file "${missing_test_repo}" "control-plane/tests/test_service_persistence.py" "def test_service_delegates_approved_high_risk_action_through_isolated_executor("
commit_fixture "${missing_test_repo}"
assert_fails_with "${missing_test_repo}" "Missing required Phase 13 test in ${missing_test_repo}/control-plane/tests/test_service_persistence.py: test_service_delegates_approved_high_risk_action_through_isolated_executor"

stale_contract_repo="${workdir}/stale-contract"
create_repo "${stale_contract_repo}"
write_required_artifacts "${stale_contract_repo}"
replace_text_in_file \
  "${stale_contract_repo}" \
  "docs/automation-substrate-contract.md" \
  'If the downstream surface reports the wrong payload hash, wrong target scope, wrong execution surface, or missing idempotency key, AegisOps must preserve that mismatch as explicit reconciliation state instead of normalizing it away.' \
  'If the downstream surface reports mismatched execution details, operators may review vendor-local state before deciding whether reconciliation changes are needed.'
commit_fixture "${stale_contract_repo}"
assert_fails_with "${stale_contract_repo}" "Missing required line in ${stale_contract_repo}/docs/automation-substrate-contract.md: If the downstream surface reports the wrong payload hash, wrong target scope, wrong execution surface, or missing idempotency key, AegisOps must preserve that mismatch as explicit reconciliation state instead of normalizing it away."

missing_ci_step_repo="${workdir}/missing-ci-step"
create_repo "${missing_ci_step_repo}"
write_required_artifacts "${missing_ci_step_repo}"
remove_text_from_file "${missing_ci_step_repo}" ".github/workflows/ci.yml" "      - name: Run Phase 13 guarded automation validation"
commit_fixture "${missing_ci_step_repo}"
assert_fails_with "${missing_ci_step_repo}" "Missing required line in ${missing_ci_step_repo}/.github/workflows/ci.yml:       - name: Run Phase 13 guarded automation validation"

echo "Phase 13 guarded-automation verifier fails closed for missing reviewed coverage."
