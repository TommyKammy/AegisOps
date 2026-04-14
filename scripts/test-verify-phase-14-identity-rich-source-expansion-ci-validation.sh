#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-14-identity-rich-source-expansion-ci-validation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/phase-14-identity-rich-source-family-design.md"
  "docs/phase-14-identity-rich-source-expansion-ci-validation.md"
  "docs/source-families/github-audit/onboarding-package.md"
  "docs/source-families/github-audit/analyst-triage-runbook.md"
  "docs/source-families/microsoft-365-audit/onboarding-package.md"
  "docs/source-families/microsoft-365-audit/analyst-triage-runbook.md"
  "docs/source-families/entra-id/onboarding-package.md"
  "docs/source-families/entra-id/analyst-triage-runbook.md"
  "control-plane/tests/test_phase14_identity_rich_source_profile_docs.py"
  "control-plane/tests/test_wazuh_adapter.py"
  "control-plane/tests/test_service_persistence_ingest_case_lifecycle.py"
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

  if ! grep -Fqx -- "${expected}" "${fail_stderr}" >/dev/null; then
    echo "Expected failure output to equal: ${expected}" >&2
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
rm "${missing_validation_repo}/docs/phase-14-identity-rich-source-expansion-ci-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-14-identity-rich-source-expansion-ci-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 14 identity-rich source expansion CI validation record: ${missing_validation_repo}/docs/phase-14-identity-rich-source-expansion-ci-validation.md"

missing_parser_ownership_repo="${workdir}/missing-parser-ownership"
create_repo "${missing_parser_ownership_repo}"
write_required_artifacts "${missing_parser_ownership_repo}"
remove_text_from_file \
  "${missing_parser_ownership_repo}" \
  "docs/source-families/github-audit/onboarding-package.md" \
  "Parser ownership remains with IT Operations, Information Systems Department."
commit_fixture "${missing_parser_ownership_repo}"
assert_fails_with "${missing_parser_ownership_repo}" "Missing required line in ${missing_parser_ownership_repo}/docs/source-families/github-audit/onboarding-package.md: Parser ownership remains with IT Operations, Information Systems Department."

missing_false_positive_repo="${workdir}/missing-false-positive"
create_repo "${missing_false_positive_repo}"
write_required_artifacts "${missing_false_positive_repo}"
remove_text_from_file \
  "${missing_false_positive_repo}" \
  "docs/source-families/microsoft-365-audit/analyst-triage-runbook.md" \
  "The runbook keeps Microsoft 365 audit handling inside the control-plane-first analyst workflow and makes the family-specific false-positive expectations, evidence requirements, and business-hours handling explicit."
commit_fixture "${missing_false_positive_repo}"
assert_fails_with "${missing_false_positive_repo}" "Missing required line in ${missing_false_positive_repo}/docs/source-families/microsoft-365-audit/analyst-triage-runbook.md: The runbook keeps Microsoft 365 audit handling inside the control-plane-first analyst workflow and makes the family-specific false-positive expectations, evidence requirements, and business-hours handling explicit."

missing_entra_service_test_repo="${workdir}/missing-entra-service-test"
create_repo "${missing_entra_service_test_repo}"
write_required_artifacts "${missing_entra_service_test_repo}"
replace_text_in_file \
  "${missing_entra_service_test_repo}" \
  "control-plane/tests/test_service_persistence_ingest_case_lifecycle.py" \
  "    def test_service_admits_entra_id_fixture_through_wazuh_source_profile(" \
  "    def _missing_service_admits_entra_id_fixture_through_wazuh_source_profile("
commit_fixture "${missing_entra_service_test_repo}"
assert_fails_with "${missing_entra_service_test_repo}" "Missing required Phase 14 unittest-discoverable test in ${missing_entra_service_test_repo}/control-plane/tests/test_service_persistence_ingest_case_lifecycle.py: test_service_admits_entra_id_fixture_through_wazuh_source_profile"

missing_prerequisite_test_repo="${workdir}/missing-prerequisite-test"
create_repo "${missing_prerequisite_test_repo}"
write_required_artifacts "${missing_prerequisite_test_repo}"
replace_text_in_file \
  "${missing_prerequisite_test_repo}" \
  "control-plane/tests/test_phase14_identity_rich_source_profile_docs.py" \
  "    def test_phase14_onboarding_packages_define_reviewed_ownership_and_prerequisites(" \
  "    def _missing_test_phase14_onboarding_packages_define_reviewed_ownership_and_prerequisites("
commit_fixture "${missing_prerequisite_test_repo}"
assert_fails_with "${missing_prerequisite_test_repo}" "Missing required Phase 14 unittest-discoverable test in ${missing_prerequisite_test_repo}/control-plane/tests/test_phase14_identity_rich_source_profile_docs.py: test_phase14_onboarding_packages_define_reviewed_ownership_and_prerequisites"

missing_ci_step_repo="${workdir}/missing-ci-step"
create_repo "${missing_ci_step_repo}"
write_required_artifacts "${missing_ci_step_repo}"
remove_text_from_file "${missing_ci_step_repo}" ".github/workflows/ci.yml" "      - name: Run Phase 14 identity-rich source expansion validation"
commit_fixture "${missing_ci_step_repo}"
assert_fails_with "${missing_ci_step_repo}" "Missing required line in ${missing_ci_step_repo}/.github/workflows/ci.yml:       - name: Run Phase 14 identity-rich source expansion validation"

missing_workflow_guard_repo="${workdir}/missing-workflow-guard"
create_repo "${missing_workflow_guard_repo}"
write_required_artifacts "${missing_workflow_guard_repo}"
remove_text_from_file "${missing_workflow_guard_repo}" ".github/workflows/ci.yml" "      - name: Run Phase 14 workflow coverage guard"
commit_fixture "${missing_workflow_guard_repo}"
assert_fails_with "${missing_workflow_guard_repo}" "Missing required line in ${missing_workflow_guard_repo}/.github/workflows/ci.yml:       - name: Run Phase 14 workflow coverage guard"

echo "Phase 14 identity-rich source expansion CI validation verifier tests passed."
