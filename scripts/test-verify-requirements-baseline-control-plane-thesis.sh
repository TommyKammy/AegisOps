#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-requirements-baseline-control-plane-thesis.sh"
canonical_doc="${repo_root}/docs/requirements-baseline.md"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

create_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  git -C "${target}" init -q
  git -C "${target}" config user.name "Codex Test"
  git -C "${target}" config user.email "codex@example.com"
}

write_canonical_doc() {
  local target="$1"

  cp "${canonical_doc}" "${target}/docs/requirements-baseline.md"
  git -C "${target}" add docs/requirements-baseline.md
}

remove_text_from_doc() {
  local target="$1"
  local expected_text="$2"
  local doc_path="${target}/docs/requirements-baseline.md"

  REMOVE_TEXT="${expected_text}" perl -0pi -e 's/\Q$ENV{REMOVE_TEXT}\E\n?//g' "${doc_path}"
  git -C "${target}" add docs/requirements-baseline.md
}

replace_text_in_doc() {
  local target="$1"
  local from_text="$2"
  local to_text="$3"
  local doc_path="${target}/docs/requirements-baseline.md"

  FROM_TEXT="${from_text}" TO_TEXT="${to_text}" perl -0pi -e 's/\Q$ENV{FROM_TEXT}\E/$ENV{TO_TEXT}/g' "${doc_path}"
  git -C "${target}" add docs/requirements-baseline.md
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
write_canonical_doc "${valid_repo}"
commit_fixture "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_repo "${missing_doc_repo}"
commit_fixture "${missing_doc_repo}"
assert_fails_with "${missing_doc_repo}" "Missing requirements baseline document:"

missing_thesis_repo="${workdir}/missing-thesis"
create_repo "${missing_thesis_repo}"
write_canonical_doc "${missing_thesis_repo}"
remove_text_from_doc "${missing_thesis_repo}" "AegisOps is a governed SecOps control plane."
commit_fixture "${missing_thesis_repo}"
assert_fails_with "${missing_thesis_repo}" "AegisOps is a governed SecOps control plane."

missing_analytic_signal_repo="${workdir}/missing-analytic-signal"
create_repo "${missing_analytic_signal_repo}"
write_canonical_doc "${missing_analytic_signal_repo}"
remove_text_from_doc "${missing_analytic_signal_repo}" "Upstream detections, findings, correlations, and product-native alerting artifacts from external substrates are treated as **Analytic Signals**."
commit_fixture "${missing_analytic_signal_repo}"
assert_fails_with "${missing_analytic_signal_repo}" "Upstream detections, findings, correlations, and product-native alerting artifacts from external substrates are treated as **Analytic Signals**."

missing_action_execution_repo="${workdir}/missing-action-execution"
create_repo "${missing_action_execution_repo}"
write_canonical_doc "${missing_action_execution_repo}"
remove_text_from_doc "${missing_action_execution_repo}" "- Action Execution"
commit_fixture "${missing_action_execution_repo}"
assert_fails_with "${missing_action_execution_repo}" "- Action Execution"

missing_action_execution_summary_repo="${workdir}/missing-action-execution-summary"
create_repo "${missing_action_execution_summary_repo}"
write_canonical_doc "${missing_action_execution_summary_repo}"
replace_text_in_doc \
  "${missing_action_execution_summary_repo}" \
  "| AegisOps control plane | Alert, case, evidence, observation, lead, recommendation, approval, action-request, action-execution, hunt, AI-trace, and reconciliation ownership |" \
  "| AegisOps control plane | Alert, case, evidence, observation, lead, recommendation, approval, action-request, hunt, AI-trace, and reconciliation ownership |"
commit_fixture "${missing_action_execution_summary_repo}"
assert_fails_with "${missing_action_execution_summary_repo}" "action-request, action-execution, hunt, AI-trace, and reconciliation ownership"

missing_non_goal_repo="${workdir}/missing-non-goal"
create_repo "${missing_non_goal_repo}"
write_canonical_doc "${missing_non_goal_repo}"
remove_text_from_doc "${missing_non_goal_repo}" "AegisOps will **not** rebuild Shuffle-class routine automation breadth in-house."
commit_fixture "${missing_non_goal_repo}"
assert_fails_with "${missing_non_goal_repo}" "AegisOps will **not** rebuild Shuffle-class routine automation breadth in-house."

missing_action_execution_truth_repo="${workdir}/missing-action-execution-truth"
create_repo "${missing_action_execution_truth_repo}"
write_canonical_doc "${missing_action_execution_truth_repo}"
replace_text_in_doc \
  "${missing_action_execution_truth_repo}" \
  "AegisOps owns approval decisions, action intent, action-execution truth, evidence linkage, and reconciliation" \
  "AegisOps owns approval decisions, action intent, evidence linkage, and reconciliation"
commit_fixture "${missing_action_execution_truth_repo}"
assert_fails_with "${missing_action_execution_truth_repo}" "AegisOps owns approval decisions, action intent, action-execution truth, evidence linkage, and reconciliation"

legacy_phrase_repo="${workdir}/legacy-phrase"
create_repo "${legacy_phrase_repo}"
write_canonical_doc "${legacy_phrase_repo}"
replace_text_in_doc "${legacy_phrase_repo}" "OpenSearch MAY be used as an optional or transitional analytics substrate." "OpenSearch MAY be used as an optional or transitional analytics substrate.\n\n**(OpenSearch + Sigma + n8n)**"
commit_fixture "${legacy_phrase_repo}"
assert_fails_with "${legacy_phrase_repo}" "Forbidden legacy requirements baseline statement present: **(OpenSearch + Sigma + n8n)**"

echo "Requirements baseline verifier enforces the governed control-plane thesis."
