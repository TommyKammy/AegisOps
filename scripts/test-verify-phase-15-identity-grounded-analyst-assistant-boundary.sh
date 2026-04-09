#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-15-identity-grounded-analyst-assistant-boundary.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

required_artifacts=(
  "docs/phase-15-identity-grounded-analyst-assistant-boundary.md"
  "docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md"
  "docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md"
  "docs/safe-query-gateway-and-tool-policy.md"
  "docs/phase-7-ai-hunt-design-validation.md"
  "docs/control-plane-state-model.md"
  "docs/control-plane-runtime-service-boundary.md"
  "docs/asset-identity-privilege-context-baseline.md"
  "docs/phase-14-identity-rich-source-family-design.md"
  "docs/phase-13-guarded-automation-ci-validation.md"
  "docs/response-action-safety-model.md"
  "docs/adr/0002-wazuh-shuffle-control-plane-thesis.md"
  "control-plane/tests/test_phase15_identity_grounded_analyst_assistant_boundary_docs.py"
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
rm "${missing_validation_repo}/docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md"
git -C "${missing_validation_repo}" add -u docs/phase-15-identity-grounded-analyst-assistant-boundary-validation.md
commit_fixture "${missing_validation_repo}"
assert_fails_with "${missing_validation_repo}" "Missing Phase 15 analyst-assistant boundary validation record:"

missing_design_repo="${workdir}/missing-design"
create_repo "${missing_design_repo}"
write_required_artifacts "${missing_design_repo}"
remove_text_from_file "${missing_design_repo}" "docs/phase-15-identity-grounded-analyst-assistant-boundary.md" "This document defines the approved advisory-only analyst-assistant boundary for Phase 15."
commit_fixture "${missing_design_repo}"
assert_fails_with "${missing_design_repo}" "Missing required line in ${missing_design_repo}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md: This document defines the approved advisory-only analyst-assistant boundary for Phase 15."

missing_guidance_repo="${workdir}/missing-guidance"
create_repo "${missing_guidance_repo}"
write_required_artifacts "${missing_guidance_repo}"
rm "${missing_guidance_repo}/docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md"
git -C "${missing_guidance_repo}" add -u docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md
commit_fixture "${missing_guidance_repo}"
assert_fails_with "${missing_guidance_repo}" "Missing Phase 15 analyst-assistant operating guidance document:"

missing_guidance_statement_repo="${workdir}/missing-guidance-statement"
create_repo "${missing_guidance_statement_repo}"
write_required_artifacts "${missing_guidance_statement_repo}"
remove_text_from_file \
  "${missing_guidance_statement_repo}" \
  "docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md" \
  "Operators must preserve uncertainty whenever the assistant only has alias-style metadata, heuristic name matches, or other non-stable source labels."
commit_fixture "${missing_guidance_statement_repo}"
assert_fails_with "${missing_guidance_statement_repo}" "Missing required line in ${missing_guidance_statement_repo}/docs/phase-15-identity-grounded-analyst-assistant-operating-guidance.md: Operators must preserve uncertainty whenever the assistant only has alias-style metadata, heuristic name matches, or other non-stable source labels."

missing_safe_query_repo="${workdir}/missing-safe-query"
create_repo "${missing_safe_query_repo}"
write_required_artifacts "${missing_safe_query_repo}"
remove_text_from_file \
  "${missing_safe_query_repo}" \
  "docs/phase-15-identity-grounded-analyst-assistant-boundary.md" \
  "The assistant must use the Safe Query Gateway policy for any read-oriented internal lookup that would otherwise rely on free-form search, query expansion, or tool selection outside reviewed control-plane paths."
commit_fixture "${missing_safe_query_repo}"
assert_fails_with "${missing_safe_query_repo}" "Missing required line in ${missing_safe_query_repo}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md: The assistant must use the Safe Query Gateway policy for any read-oriented internal lookup that would otherwise rely on free-form search, query expansion, or tool selection outside reviewed control-plane paths."

missing_prompt_injection_repo="${workdir}/missing-prompt-injection"
create_repo "${missing_prompt_injection_repo}"
write_required_artifacts "${missing_prompt_injection_repo}"
remove_text_from_file \
  "${missing_prompt_injection_repo}" \
  "docs/phase-15-identity-grounded-analyst-assistant-boundary.md" \
  "Prompt content, analyst notes, and optional-extension instructions are untrusted input."
commit_fixture "${missing_prompt_injection_repo}"
assert_fails_with "${missing_prompt_injection_repo}" "Missing required line in ${missing_prompt_injection_repo}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md: Prompt content, analyst notes, and optional-extension instructions are untrusted input."

missing_citation_repo="${workdir}/missing-citation"
create_repo "${missing_citation_repo}"
write_required_artifacts "${missing_citation_repo}"
remove_text_from_file \
  "${missing_citation_repo}" \
  "docs/phase-15-identity-grounded-analyst-assistant-boundary.md" \
  "The assistant must preserve citation completeness for every advisory claim."
commit_fixture "${missing_citation_repo}"
assert_fails_with "${missing_citation_repo}" "Missing required line in ${missing_citation_repo}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md: The assistant must preserve citation completeness for every advisory claim."

missing_identity_boundary_repo="${workdir}/missing-identity-boundary"
create_repo "${missing_identity_boundary_repo}"
write_required_artifacts "${missing_identity_boundary_repo}"
remove_text_from_file \
  "${missing_identity_boundary_repo}" \
  "docs/phase-15-identity-grounded-analyst-assistant-boundary.md" \
  "Alias-style fields may suggest a match, but when stable identifiers differ the assistant must keep the records distinct and report the ambiguity instead of normalizing them into one actor or asset."
commit_fixture "${missing_identity_boundary_repo}"
assert_fails_with "${missing_identity_boundary_repo}" "Missing required line in ${missing_identity_boundary_repo}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md: Alias-style fields may suggest a match, but when stable identifiers differ the assistant must keep the records distinct and report the ambiguity instead of normalizing them into one actor or asset."

missing_opensearch_boundary_repo="${workdir}/missing-opensearch-boundary"
create_repo "${missing_opensearch_boundary_repo}"
write_required_artifacts "${missing_opensearch_boundary_repo}"
remove_text_from_file "${missing_opensearch_boundary_repo}" "docs/phase-15-identity-grounded-analyst-assistant-boundary.md" "OpenSearch may contribute optional analytics or evidence lookups to the assistant path after the reviewed control-plane grounding path exists."
commit_fixture "${missing_opensearch_boundary_repo}"
assert_fails_with "${missing_opensearch_boundary_repo}" "Missing required line in ${missing_opensearch_boundary_repo}/docs/phase-15-identity-grounded-analyst-assistant-boundary.md: OpenSearch may contribute optional analytics or evidence lookups to the assistant path after the reviewed control-plane grounding path exists."

missing_test_repo="${workdir}/missing-test"
create_repo "${missing_test_repo}"
write_required_artifacts "${missing_test_repo}"
remove_text_from_file "${missing_test_repo}" "control-plane/tests/test_phase15_identity_grounded_analyst_assistant_boundary_docs.py" "    def test_phase15_boundary_design_doc_fails_closed_on_ambiguous_identity_metadata(self) -> None:"
commit_fixture "${missing_test_repo}"
assert_fails_with "${missing_test_repo}" "Missing required Phase 15 unittest-discoverable test in ${missing_test_repo}/control-plane/tests/test_phase15_identity_grounded_analyst_assistant_boundary_docs.py: test_phase15_boundary_design_doc_fails_closed_on_ambiguous_identity_metadata"

missing_ci_step_repo="${workdir}/missing-ci-step"
create_repo "${missing_ci_step_repo}"
write_required_artifacts "${missing_ci_step_repo}"
remove_text_from_file "${missing_ci_step_repo}" ".github/workflows/ci.yml" "      - name: Run Phase 15 identity-grounded analyst-assistant boundary validation"
commit_fixture "${missing_ci_step_repo}"
assert_fails_with "${missing_ci_step_repo}" "Missing required line in ${missing_ci_step_repo}/.github/workflows/ci.yml:       - name: Run Phase 15 identity-grounded analyst-assistant boundary validation"

echo "Phase 15 identity-grounded analyst-assistant boundary verifier fails closed for missing reviewed coverage."
