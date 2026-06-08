#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"
base_valid_repo=""

assert_passes() {
  local target="$1"

  if ! PHASE66_4_SKIP_PATH_HYGIENE=1 bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_passes_with_path_hygiene() {
  local target="$1"

  if ! bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if PHASE66_4_SKIP_PATH_HYGIENE=1 bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail for ${target}" >&2
    cat "${fail_stdout}" >&2
    exit 1
  fi

  if ! grep -Fiq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

copy_repo_path() {
  local target="$1"
  local relative_path="$2"

  mkdir -p "${target}/$(dirname "${relative_path}")"
  cp -p "${repo_root}/${relative_path}" "${target}/${relative_path}"
}

copy_valid_repo() {
  local target="$1"
  local path

  if [[ -n "${base_valid_repo}" && -d "${base_valid_repo}/.git" ]]; then
    mkdir -p "${target}"
    cp -R "${base_valid_repo}/." "${target}/"
    return
  fi

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/phase-66-4-ai-assisted-triage-rc-proof.md"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"

  for path in \
    "docs/phase-66-1-clean-host-rc-e2e-harness.md" \
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "docs/phase-59-3-ai-trace-lifecycle-contract.md" \
    "docs/phase-59-4-ai-disabled-degraded-mode-contract.md" \
    "docs/phase-60-3-case-timeline-summary-agent.md" \
    "docs/phase-60-6-cited-recommendation-draft-agent.md" \
    "docs/phase-63-7-ai-grounding-adapter.md" \
    "docs/phase-65-closeout-evaluation.md"; do
    copy_repo_path "${target}" "${path}"
  done

  for path in \
    "scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh" \
    "scripts/test-verify-phase-66-4-ai-assisted-triage-rc-proof.sh" \
    "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh" \
    "scripts/verify-publishable-path-hygiene.sh"; do
    copy_repo_path "${target}" "${path}"
  done

  git -C "${target}" init -q
  git -C "${target}" config user.email "aegisops@example.invalid"
  git -C "${target}" config user.name "AegisOps Test"
  git -C "${target}" add README.md docs scripts control-plane/aegisops
  git -C "${target}" commit -q -m "fixture"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes_with_path_hygiene "${valid_repo}"
base_valid_repo="${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66.4 AI-assisted triage RC proof"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 66\.4 AI-assisted triage RC proof\]\(docs\/phase-66-4-ai-assisted-triage-rc-proof\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical Phase 66.4 boundary bullet"

missing_trace_lifecycle_repo="${workdir}/missing-trace-lifecycle"
copy_valid_repo "${missing_trace_lifecycle_repo}"
remove_doc_text "${missing_trace_lifecycle_repo}" \
  "The proof must cite \`docs/phase-59-3-ai-trace-lifecycle-contract.md\`"
assert_fails_with "${missing_trace_lifecycle_repo}" "Missing Phase 66.4 cited summary or reviewability term"

missing_citation_row_repo="${workdir}/missing-citation-row"
copy_valid_repo "${missing_citation_row_repo}"
remove_doc_text "${missing_citation_row_repo}" \
  "| \`source_evidence_references\` | Reviewed AegisOps evidence ids, alert ids, case ids, and source references used by the assistant. | Missing citations fail the proof. |"
assert_fails_with "${missing_citation_row_repo}" "Missing Phase 66.4 AI-assisted triage evidence field"

missing_review_state_repo="${workdir}/missing-review-state"
copy_valid_repo "${missing_review_state_repo}"
printf '%s\n' "operator_review_state: missing" >>"${missing_review_state_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${missing_review_state_repo}" "missing required evidence value detected"

invalid_review_state_repo="${workdir}/invalid-review-state"
copy_valid_repo "${invalid_review_state_repo}"
printf '%s\n' "operator_review_state: ai_approved" >>"${invalid_review_state_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${invalid_review_state_repo}" "invalid operator review state detected"

review_state_ai_suffix_table_repo="${workdir}/review-state-ai-suffix-table"
copy_valid_repo "${review_state_ai_suffix_table_repo}"
printf '%s\n' "| operator_review_state | accepted by AI | reviewed |" >>"${review_state_ai_suffix_table_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${review_state_ai_suffix_table_repo}" "invalid operator review state detected"

mutable_repository_revision_repo="${workdir}/mutable-repository-revision"
copy_valid_repo "${mutable_repository_revision_repo}"
printf '%s\n' "repository_revision: refs/remotes/origin/main" >>"${mutable_repository_revision_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${mutable_repository_revision_repo}" "mutable repository revision detected"

revision_hash_with_branch_repo="${workdir}/revision-hash-with-branch"
copy_valid_repo "${revision_hash_with_branch_repo}"
printf '%s\n' "repository_revision: 0123456789abcdef0123456789abcdef01234567 on origin/main" >>"${revision_hash_with_branch_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${revision_hash_with_branch_repo}" "mutable repository revision detected"

latest_repository_revision_table_repo="${workdir}/latest-repository-revision-table"
copy_valid_repo "${latest_repository_revision_table_repo}"
printf '%s\n' "| repository_revision | latest | reviewed |" >>"${latest_repository_revision_table_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${latest_repository_revision_table_repo}" "non-immutable repository revision detected"

ai_trace_shortcut_repo="${workdir}/ai-trace-shortcut"
copy_valid_repo "${ai_trace_shortcut_repo}"
printf '%s\n' "ai_trace_id: model_output" >>"${ai_trace_shortcut_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${ai_trace_shortcut_repo}" "invalid AI trace detected"

uncited_summary_repo="${workdir}/uncited-summary"
copy_valid_repo "${uncited_summary_repo}"
printf '%s\n' "cited_summary_id: uncited" >>"${uncited_summary_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${uncited_summary_repo}" "invalid citation evidence detected"

hidden_uncertainty_repo="${workdir}/hidden-uncertainty"
copy_valid_repo "${hidden_uncertainty_repo}"
printf '%s\n' "uncertainty_flags: hidden in assistant prose" >>"${hidden_uncertainty_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${hidden_uncertainty_repo}" "hidden uncertainty detected"

recommendation_authority_repo="${workdir}/recommendation-authority"
copy_valid_repo "${recommendation_authority_repo}"
printf '%s\n' "recommendation_draft_id: case_closed" >>"${recommendation_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${recommendation_authority_repo}" "recommendation authority shortcut detected"

recommendation_authority_table_repo="${workdir}/recommendation-authority-table"
copy_valid_repo "${recommendation_authority_table_repo}"
printf '%s\n' "| recommendation_draft_id | case_closed | reviewed |" >>"${recommendation_authority_table_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${recommendation_authority_table_repo}" "recommendation authority shortcut detected"

missing_degraded_posture_repo="${workdir}/missing-degraded-posture"
copy_valid_repo "${missing_degraded_posture_repo}"
printf '%s\n' "degraded_disabled_posture: not_needed" >>"${missing_degraded_posture_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${missing_degraded_posture_repo}" "invalid degraded or disabled posture detected"

missing_degraded_posture_table_repo="${workdir}/missing-degraded-posture-table"
copy_valid_repo "${missing_degraded_posture_table_repo}"
printf '%s\n' "| degraded_disabled_posture | required_for_rc | reviewed |" >>"${missing_degraded_posture_table_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${missing_degraded_posture_table_repo}" "invalid degraded or disabled posture detected"

prompt_injection_shortcut_repo="${workdir}/prompt-injection-shortcut"
copy_valid_repo "${prompt_injection_shortcut_repo}"
printf '%s\n' "prompt_injection_review_id: comply_with_prompt_instructions" >>"${prompt_injection_shortcut_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${prompt_injection_shortcut_repo}" "prompt-injection shortcut detected"

prompt_injection_shortcut_table_repo="${workdir}/prompt-injection-shortcut-table"
copy_valid_repo "${prompt_injection_shortcut_table_repo}"
printf '%s\n' "| prompt_injection_review_id | comply_with_prompt_instructions | reviewed |" >>"${prompt_injection_shortcut_table_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${prompt_injection_shortcut_table_repo}" "prompt-injection shortcut detected"

hidden_limitation_repo="${workdir}/hidden-limitation"
copy_valid_repo "${hidden_limitation_repo}"
printf '%s\n' "limitation_references: hidden in assistant output" >>"${hidden_limitation_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${hidden_limitation_repo}" "hidden limitation references detected"

hidden_limitation_table_repo="${workdir}/hidden-limitation-table"
copy_valid_repo "${hidden_limitation_table_repo}"
printf '%s\n' "| limitation_references | hidden in assistant output | reviewed |" >>"${hidden_limitation_table_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${hidden_limitation_table_repo}" "hidden limitation references detected"

ai_approves_records_repo="${workdir}/ai-approves-records"
copy_valid_repo "${ai_approves_records_repo}"
printf '%s\n' "AI output approves AegisOps records." >>"${ai_approves_records_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${ai_approves_records_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

safe_boundary_then_ai_authority_repo="${workdir}/safe-boundary-then-ai-authority"
copy_valid_repo "${safe_boundary_then_ai_authority_repo}"
printf '%s\n' "AI output cannot approve AegisOps records and AI output executes AegisOps records." >>"${safe_boundary_then_ai_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${safe_boundary_then_ai_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

safe_sentence_then_ai_authority_repo="${workdir}/safe-sentence-then-ai-authority"
copy_valid_repo "${safe_sentence_then_ai_authority_repo}"
printf '%s\n' "AI output cannot approve AegisOps records. AI output executes AegisOps records." >>"${safe_sentence_then_ai_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${safe_sentence_then_ai_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

modal_ai_authority_repo="${workdir}/modal-ai-authority"
copy_valid_repo "${modal_ai_authority_repo}"
printf '%s\n' "AI output can approve AegisOps records." >>"${modal_ai_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${modal_ai_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

modal_ai_execute_authority_repo="${workdir}/modal-ai-execute-authority"
copy_valid_repo "${modal_ai_execute_authority_repo}"
printf '%s\n' "AI output may execute AegisOps records." >>"${modal_ai_execute_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${modal_ai_execute_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

assistant_output_authority_repo="${workdir}/assistant-output-authority"
copy_valid_repo "${assistant_output_authority_repo}"
printf '%s\n' "Assistant output approves AegisOps records." >>"${assistant_output_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${assistant_output_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

assistant_recommendation_authority_repo="${workdir}/assistant-recommendation-authority"
copy_valid_repo "${assistant_recommendation_authority_repo}"
printf '%s\n' "Assistant recommendations close cases." >>"${assistant_recommendation_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${assistant_recommendation_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

model_recommendation_authority_repo="${workdir}/model-recommendation-authority"
copy_valid_repo "${model_recommendation_authority_repo}"
printf '%s\n' "Model recommendations execute action requests." >>"${model_recommendation_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${model_recommendation_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

ai_executes_actions_repo="${workdir}/ai-executes-actions"
copy_valid_repo "${ai_executes_actions_repo}"
printf '%s\n' "AI output executes actions." >>"${ai_executes_actions_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${ai_executes_actions_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

wrapped_ai_authority_repo="${workdir}/wrapped-ai-authority"
copy_valid_repo "${wrapped_ai_authority_repo}"
printf '%s\n%s\n' "AI output" "approves AegisOps records." >>"${wrapped_ai_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${wrapped_ai_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

passive_ai_authority_repo="${workdir}/passive-ai-authority"
copy_valid_repo "${passive_ai_authority_repo}"
printf '%s\n' "AegisOps cases are closed by AI recommendations." >>"${passive_ai_authority_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${passive_ai_authority_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

prompt_injection_overrides_repo="${workdir}/prompt-injection-overrides"
copy_valid_repo "${prompt_injection_overrides_repo}"
printf '%s\n' "Prompt injection compliance overrides AegisOps policy." >>"${prompt_injection_overrides_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${prompt_injection_overrides_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

phase_demonstrates_ga_repo="${workdir}/phase-demonstrates-ga"
copy_valid_repo "${phase_demonstrates_ga_repo}"
printf '%s\n' "Phase 66.4 demonstrates GA readiness." >>"${phase_demonstrates_ga_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${phase_demonstrates_ga_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

ai_readiness_truth_repo="${workdir}/ai-readiness-truth"
copy_valid_repo "${ai_readiness_truth_repo}"
printf '%s\n' "AI output proves readiness truth." >>"${ai_readiness_truth_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${ai_readiness_truth_repo}" "Forbidden Phase 66.4 AI-assisted triage RC proof claim matched"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "api_key: abcdefghijklmnop" >>"${secret_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${secret_repo}" "production secret-looking value detected"

github_pat_secret_repo="${workdir}/github-pat-secret"
copy_valid_repo "${github_pat_secret_repo}"
printf '%s\n' "github_pat_0123456789abcdef0123456789abcdef01234567" >>"${github_pat_secret_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${github_pat_secret_repo}" "production secret-looking value detected"

customer_private_repo="${workdir}/customer-private"
copy_valid_repo "${customer_private_repo}"
printf '%s\n' "The proof includes customer-private ticket export." >>"${customer_private_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

customer_private_semicolon_repo="${workdir}/customer-private-semicolon"
copy_valid_repo "${customer_private_semicolon_repo}"
printf '%s\n' "The proof must not include customer-private data; includes customer-private ticket export." >>"${customer_private_semicolon_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${customer_private_semicolon_repo}" "customer-private data detected"

customer_private_table_repo="${workdir}/customer-private-table"
copy_valid_repo "${customer_private_table_repo}"
printf '%s\n' "| customer_private_data | exported-ticket |" >>"${customer_private_table_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_fails_with "${customer_private_table_repo}" "customer-private data detected"

safe_limitation_repo="${workdir}/safe-limitation"
copy_valid_repo "${safe_limitation_repo}"
printf '%s\n' "Phase 66.4 records that AI approval remains out of scope." >>"${safe_limitation_repo}/docs/phase-66-4-ai-assisted-triage-rc-proof.md"
assert_passes "${safe_limitation_repo}"

echo "Phase 66.4 AI-assisted triage RC proof verifier self-test passed."
