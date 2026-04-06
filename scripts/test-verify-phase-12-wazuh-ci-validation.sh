#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-12-wazuh-ci-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/wazuh-alert-ingest-contract.md"
  "docs/wazuh-rule-lifecycle-runbook.md"
  "docs/phase-12-wazuh-ci-validation.md"
  "control-plane/tests/test_wazuh_alert_ingest_contract_docs.py"
  "control-plane/tests/test_wazuh_adapter.py"
  "control-plane/tests/test_service_persistence.py"
  "control-plane/tests/test_cli_inspection.py"
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
rm "${missing_validation_repo}/docs/phase-12-wazuh-ci-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-12-wazuh-ci-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 12 Wazuh CI validation record:"

missing_queue_test_repo="${workdir}/missing-queue-test"
create_repo "${missing_queue_test_repo}"
write_required_artifacts "${missing_queue_test_repo}"
remove_text_from_file "${missing_queue_test_repo}" "control-plane/tests/test_service_persistence.py" "def test_service_exposes_wazuh_origin_alerts_in_business_hours_analyst_queue(self) -> None:"
commit_fixture "${missing_queue_test_repo}"
assert_fails_with "${missing_queue_test_repo}" "Missing required Phase 12 test in ${missing_queue_test_repo}/control-plane/tests/test_service_persistence.py: test_service_exposes_wazuh_origin_alerts_in_business_hours_analyst_queue"

stale_contract_repo="${workdir}/stale-contract"
create_repo "${stale_contract_repo}"
write_required_artifacts "${stale_contract_repo}"
replace_text_in_file \
  "${stale_contract_repo}" \
  "docs/wazuh-alert-ingest-contract.md" \
  '| `substrate_detection_record_id` | Set to `wazuh:<id>` unless the input is already namespaced as `wazuh:<id>`. This matches the shipped control-plane rule that substrate detection identifiers are namespaced by substrate key. |' \
  '| `substrate_detection_record_id` | May mirror any upstream identifier shape. |'
commit_fixture "${stale_contract_repo}"
assert_fails_with "${stale_contract_repo}" "Missing required line in ${stale_contract_repo}/docs/wazuh-alert-ingest-contract.md: | \`substrate_detection_record_id\` | Set to \`wazuh:<id>\` unless the input is already namespaced as \`wazuh:<id>\`. This matches the shipped control-plane rule that substrate detection identifiers are namespaced by substrate key. |"

missing_ci_step_repo="${workdir}/missing-ci-step"
create_repo "${missing_ci_step_repo}"
write_required_artifacts "${missing_ci_step_repo}"
remove_text_from_file "${missing_ci_step_repo}" ".github/workflows/ci.yml" "      - name: Run Phase 12 Wazuh validation"
commit_fixture "${missing_ci_step_repo}"
assert_fails_with "${missing_ci_step_repo}" "Missing required line in ${missing_ci_step_repo}/.github/workflows/ci.yml:       - name: Run Phase 12 Wazuh validation"

missing_review_repo="${workdir}/missing-review"
create_repo "${missing_review_repo}"
write_required_artifacts "${missing_review_repo}"
remove_text_from_file \
  "${missing_review_repo}" \
  "docs/phase-12-wazuh-ci-validation.md" \
  "Confirmed analyst queue review keeps Wazuh-specific source precedence when multi-source linkage is present so queue routing does not drift away from the reviewed Phase 12 ingest path."
commit_fixture "${missing_review_repo}"
assert_fails_with "${missing_review_repo}" "Missing required line in ${missing_review_repo}/docs/phase-12-wazuh-ci-validation.md: Confirmed analyst queue review keeps Wazuh-specific source precedence when multi-source linkage is present so queue routing does not drift away from the reviewed Phase 12 ingest path."

echo "Phase 12 Wazuh CI validation verifier fails closed for missing reviewed coverage."
