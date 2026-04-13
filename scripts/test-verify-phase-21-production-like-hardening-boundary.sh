#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-21-production-like-hardening-boundary.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/phase-21-production-like-hardening-boundary-and-sequence.md"
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md"
  "docs/phase-20-first-live-low-risk-action-and-reviewed-delegation-boundary.md"
  "docs/auth-baseline.md"
  "docs/network-exposure-and-access-path-policy.md"
  "docs/runbook.md"
  "docs/automation-substrate-contract.md"
  "docs/response-action-safety-model.md"
  "docs/source-onboarding-contract.md"
  "docs/phase-14-identity-rich-source-family-design.md"
  "docs/phase-18-wazuh-lab-topology-and-live-ingest-contract.md"
  "docs/wazuh-alert-ingest-contract.md"
  "docs/control-plane-state-model.md"
  "docs/phase-19-thin-operator-surface-and-daily-analyst-workflow.md"
  "docs/phase-17-runtime-config-contract-and-boot-command-expectations.md"
  "docs/architecture.md"
  "control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py"
  "control-plane/tests/test_phase21_production_like_hardening_boundary_validation.py"
  "scripts/verify-phase-21-production-like-hardening-boundary.sh"
  "scripts/test-verify-phase-21-production-like-hardening-boundary.sh"
  "scripts/test-verify-ci-phase-21-workflow-coverage.sh"
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
  local source_roadmap="${repo_root}/docs/Phase 16-21 Epic Roadmap.md"

  for artifact in "${required_artifacts[@]}"; do
    mkdir -p "${target}/$(dirname "${artifact}")"
    cp "${repo_root}/${artifact}" "${target}/${artifact}"
    git -C "${target}" add "${artifact}"
  done

  if [[ -f "${source_roadmap}" ]]; then
    cp "${source_roadmap}" "${target}/docs/Phase 16-21 Epic Roadmap.md"
    git -C "${target}" add "docs/Phase 16-21 Epic Roadmap.md"
  fi
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

write_text_file() {
  local target="$1"
  local path="$2"
  local content="$3"

  mkdir -p "${target}/$(dirname "${path}")"
  printf '%s\n' "${content}" >"${target}/${path}"
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

incorrect_pass_status_repo="${workdir}/incorrect-pass-status"
create_repo "${incorrect_pass_status_repo}"
write_required_artifacts "${incorrect_pass_status_repo}"
if [[ -f "${repo_root}/docs/Phase 16-21 Epic Roadmap.md" ]]; then
  replace_text_in_file \
    "${incorrect_pass_status_repo}" \
    "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
    "- Validation status: PASS" \
    "- Validation status: FAIL"
  commit_fixture "${incorrect_pass_status_repo}"
  assert_fails_with "${incorrect_pass_status_repo}" "Unexpected line in ${incorrect_pass_status_repo}/docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md: - Validation status: FAIL"
else
  replace_text_in_file \
    "${incorrect_pass_status_repo}" \
    "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
    "- Validation status: FAIL" \
    "- Validation status: PASS"
  commit_fixture "${incorrect_pass_status_repo}"
  assert_fails_with "${incorrect_pass_status_repo}" "Unexpected line in ${incorrect_pass_status_repo}/docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md: - Validation status: PASS"
fi

roadmap_present_repo="${workdir}/roadmap-present"
create_repo "${roadmap_present_repo}"
write_required_artifacts "${roadmap_present_repo}"
write_text_file \
  "${roadmap_present_repo}" \
  "docs/Phase 16-21 Epic Roadmap.md" \
  "# Phase 16-21 Epic Roadmap"
replace_text_in_file \
  "${roadmap_present_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  "- Validation status: FAIL" \
  "- Validation status: PASS"
replace_text_in_file \
  "${roadmap_present_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  "The issue requested review against \`Phase 16-21 Epic Roadmap.md\`, but that roadmap file was not present in the local worktree and could not be located via repository search during this validation snapshot." \
  "Confirmed comparison against \`Phase 16-21 Epic Roadmap.md\` completed using \`docs/Phase 16-21 Epic Roadmap.md\` as the reviewed roadmap baseline."
remove_text_from_file \
  "${roadmap_present_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  'Validation cannot pass until the requested `Phase 16-21 Epic Roadmap.md` comparison is completed from a reviewed local artifact.'
remove_text_from_file \
  "${roadmap_present_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
replace_text_in_file \
  "${roadmap_present_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  '- `docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md`' \
  $'- `docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md`\n- `docs/Phase 16-21 Epic Roadmap.md`'
commit_fixture "${roadmap_present_repo}"
assert_passes "${roadmap_present_repo}"

roadmap_present_missing_artifact_repo="${workdir}/roadmap-present-missing-artifact"
create_repo "${roadmap_present_missing_artifact_repo}"
write_required_artifacts "${roadmap_present_missing_artifact_repo}"
write_text_file \
  "${roadmap_present_missing_artifact_repo}" \
  "docs/Phase 16-21 Epic Roadmap.md" \
  "# Phase 16-21 Epic Roadmap"
replace_text_in_file \
  "${roadmap_present_missing_artifact_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  "- Validation status: FAIL" \
  "- Validation status: PASS"
replace_text_in_file \
  "${roadmap_present_missing_artifact_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  "The issue requested review against \`Phase 16-21 Epic Roadmap.md\`, but that roadmap file was not present in the local worktree and could not be located via repository search during this validation snapshot." \
  "Confirmed comparison against \`Phase 16-21 Epic Roadmap.md\` completed using \`docs/Phase 16-21 Epic Roadmap.md\` as the reviewed roadmap baseline."
remove_text_from_file \
  "${roadmap_present_missing_artifact_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  'Validation cannot pass until the requested `Phase 16-21 Epic Roadmap.md` comparison is completed from a reviewed local artifact.'
remove_text_from_file \
  "${roadmap_present_missing_artifact_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  '- Requested comparison target `Phase 16-21 Epic Roadmap.md` was unavailable in the local worktree during this validation snapshot.'
remove_text_from_file \
  "${roadmap_present_missing_artifact_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md" \
  '- `docs/Phase 16-21 Epic Roadmap.md`'
commit_fixture "${roadmap_present_missing_artifact_repo}"
assert_fails_with "${roadmap_present_missing_artifact_repo}" "Missing required line in ${roadmap_present_missing_artifact_repo}/docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md: - \`docs/Phase 16-21 Epic Roadmap.md\`"

missing_validation_repo="${workdir}/missing-validation"
create_repo "${missing_validation_repo}"
write_required_artifacts "${missing_validation_repo}"
rm "${missing_validation_repo}/docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-21-production-like-hardening-boundary-and-sequence-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 21 production-like hardening validation doc:"

missing_entra_repo="${workdir}/missing-entra"
create_repo "${missing_entra_repo}"
write_required_artifacts "${missing_entra_repo}"
remove_text_from_file \
  "${missing_entra_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence.md" \
  'The approved first reviewed second live source to onboard after the existing GitHub audit live slice is Entra ID.'
commit_fixture "${missing_entra_repo}"
assert_fails_with "${missing_entra_repo}" "Missing required line in ${missing_entra_repo}/docs/phase-21-production-like-hardening-boundary-and-sequence.md: The approved first reviewed second live source to onboard after the existing GitHub audit live slice is Entra ID."

missing_sequence_repo="${workdir}/missing-sequence"
create_repo "${missing_sequence_repo}"
write_required_artifacts "${missing_sequence_repo}"
remove_text_from_file \
  "${missing_sequence_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence.md" \
  '`auth and secrets -> admin bootstrap and break-glass controls -> restore proof -> observability proof -> topology growth gate review -> Entra ID second-source onboarding`'
commit_fixture "${missing_sequence_repo}"
assert_fails_with "${missing_sequence_repo}" "Missing required line in ${missing_sequence_repo}/docs/phase-21-production-like-hardening-boundary-and-sequence.md: \`auth and secrets -> admin bootstrap and break-glass controls -> restore proof -> observability proof -> topology growth gate review -> Entra ID second-source onboarding\`"

missing_non_expansion_repo="${workdir}/missing-non-expansion"
create_repo "${missing_non_expansion_repo}"
write_required_artifacts "${missing_non_expansion_repo}"
remove_text_from_file \
  "${missing_non_expansion_repo}" \
  "docs/phase-21-production-like-hardening-boundary-and-sequence.md" \
  '- broad multi-source breadth beyond the reviewed GitHub audit live slice plus one reviewed Entra ID follow-on target;'
commit_fixture "${missing_non_expansion_repo}"
assert_fails_with "${missing_non_expansion_repo}" "Missing required line in ${missing_non_expansion_repo}/docs/phase-21-production-like-hardening-boundary-and-sequence.md: - broad multi-source breadth beyond the reviewed GitHub audit live slice plus one reviewed Entra ID follow-on target;"

missing_docs_test_repo="${workdir}/missing-docs-test"
create_repo "${missing_docs_test_repo}"
write_required_artifacts "${missing_docs_test_repo}"
remove_text_from_file \
  "${missing_docs_test_repo}" \
  "control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py" \
  "    def test_phase21_design_doc_defines_boundary_sequence_and_non_expansion_rules(self) -> None:"
commit_fixture "${missing_docs_test_repo}"
assert_fails_with "${missing_docs_test_repo}" "Missing required line in ${missing_docs_test_repo}/control-plane/tests/test_phase21_production_like_hardening_boundary_docs.py:     def test_phase21_design_doc_defines_boundary_sequence_and_non_expansion_rules(self) -> None:"

missing_ci_repo="${workdir}/missing-ci"
create_repo "${missing_ci_repo}"
write_required_artifacts "${missing_ci_repo}"
remove_text_from_file \
  "${missing_ci_repo}" \
  ".github/workflows/ci.yml" \
  "      - name: Run Phase 21 workflow coverage guard"
commit_fixture "${missing_ci_repo}"
assert_fails_with "${missing_ci_repo}" "Missing required line in ${missing_ci_repo}/.github/workflows/ci.yml:       - name: Run Phase 21 workflow coverage guard"

echo "Phase 21 production-like hardening verifier fails closed for missing reviewed coverage."
