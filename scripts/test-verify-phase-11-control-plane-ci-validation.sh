#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-11-control-plane-ci-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/control-plane-state-model.md"
  "docs/phase-11-control-plane-ci-validation.md"
  "control-plane/README.md"
  "control-plane/tests/test_service_persistence.py"
  "control-plane/tests/test_postgres_store.py"
  "control-plane/tests/test_cli_inspection.py"
  ".github/workflows/ci.yml"
)

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs" "${target}/control-plane/tests" "${target}/.github/workflows" "${target}/control-plane"
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
rm "${missing_validation_repo}/docs/phase-11-control-plane-ci-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-11-control-plane-ci-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 11 control-plane CI validation record:"

missing_test_repo="${workdir}/missing-test"
create_repo "${missing_test_repo}"
write_required_artifacts "${missing_test_repo}"
remove_text_from_file "${missing_test_repo}" "control-plane/tests/test_service_persistence.py" "def test_service_reconcile_action_execution_supports_generic_execution_surfaces("
commit_fixture "${missing_test_repo}"
assert_fails_with "${missing_test_repo}" "Missing required Phase 11 test in ${missing_test_repo}/control-plane/tests/test_service_persistence.py: test_service_reconcile_action_execution_supports_generic_execution_surfaces"

stale_state_model_repo="${workdir}/stale-state-model"
create_repo "${stale_state_model_repo}"
write_required_artifacts "${stale_state_model_repo}"
replace_text_in_file \
  "${stale_state_model_repo}" \
  "docs/control-plane-state-model.md" \
  'The reviewed local control-plane runtime now reports `persistence_mode="postgresql"` and treats the PostgreSQL-backed control-plane store as the authoritative persistence path for local runtime and inspection flows, while `postgres/control-plane/` remains the reviewed schema and migration home and OpenSearch remains the analytics-plane store for telemetry and detection outputs.' \
  'No new live datastore rollout is approved in this phase. The current control-plane runtime remains `persistence_mode="in_memory"`, `postgres/control-plane/` remains the reviewed schema and migration home for future PostgreSQL-backed persistence work, and OpenSearch remains the analytics-plane store for telemetry and detection outputs.'
commit_fixture "${stale_state_model_repo}"
assert_fails_with "${stale_state_model_repo}" "Missing control-plane state model statement: The reviewed local control-plane runtime now reports \`persistence_mode=\"postgresql\"\` and treats the PostgreSQL-backed control-plane store as the authoritative persistence path for local runtime and inspection flows, while \`postgres/control-plane/\` remains the reviewed schema and migration home and OpenSearch remains the analytics-plane store for telemetry and detection outputs."

missing_ci_step_repo="${workdir}/missing-ci-step"
create_repo "${missing_ci_step_repo}"
write_required_artifacts "${missing_ci_step_repo}"
remove_text_from_file "${missing_ci_step_repo}" ".github/workflows/ci.yml" "      - name: Run Phase 11 control-plane validation"
commit_fixture "${missing_ci_step_repo}"
assert_fails_with "${missing_ci_step_repo}" "Missing required line in ${missing_ci_step_repo}/.github/workflows/ci.yml:       - name: Run Phase 11 control-plane validation"

echo "Phase 11 control-plane CI validation verifier fails closed for missing reviewed coverage."
