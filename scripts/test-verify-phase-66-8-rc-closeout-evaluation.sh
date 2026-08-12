#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-66-8-rc-closeout-evaluation.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

assert_passes() {
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

  if bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
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

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/phase-66-closeout-evaluation.md"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"

  for path in \
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "docs/phase-65-closeout-evaluation.md" \
    "docs/phase-66-1-clean-host-rc-e2e-harness.md" \
    "docs/phase-66-2-wazuh-sample-signal-rc-proof.md" \
    "docs/phase-66-3-shuffle-sample-execution-rc-proof.md" \
    "docs/phase-66-4-ai-assisted-triage-rc-proof.md" \
    "docs/phase-66-5-report-export-rc-proof.md" \
    "docs/phase-66-6-rc-supportability-proof.md" \
    "docs/phase-66-7-rc-authority-boundary-proof-pack.md"; do
    copy_repo_path "${target}" "${path}"
  done

  for path in \
    "scripts/verify-phase-66-1-clean-host-rc-e2e-harness.sh" \
    "scripts/test-verify-phase-66-1-clean-host-rc-e2e-harness.sh" \
    "scripts/verify-phase-66-2-wazuh-sample-signal-rc-proof.sh" \
    "scripts/test-verify-phase-66-2-wazuh-sample-signal-rc-proof.sh" \
    "scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh" \
    "scripts/test-verify-phase-66-3-shuffle-sample-execution-rc-proof.sh" \
    "scripts/verify-phase-66-4-ai-assisted-triage-rc-proof.sh" \
    "scripts/test-verify-phase-66-4-ai-assisted-triage-rc-proof.sh" \
    "scripts/verify-phase-66-5-report-export-rc-proof.sh" \
    "scripts/test-verify-phase-66-5-report-export-rc-proof.sh" \
    "scripts/verify-phase-66-6-rc-supportability-proof.sh" \
    "scripts/test-verify-phase-66-6-rc-supportability-proof.sh" \
    "scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh" \
    "scripts/test-verify-phase-66-7-rc-authority-boundary-proof-pack.sh" \
    "scripts/verify-phase-66-8-rc-closeout-evaluation.sh" \
    "scripts/test-verify-phase-66-8-rc-closeout-evaluation.sh" \
    "scripts/verify-phase-51-3-pilot-beta-rc-ga-gate-contract.sh" \
    "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh" \
    "scripts/verify-maintainability-hotspots.sh" \
    "scripts/verify-publishable-path-hygiene.sh"; do
    copy_repo_path "${target}" "${path}"
  done

  git -C "${target}" init -q
  git -C "${target}" config user.email "aegisops@example.invalid"
  git -C "${target}" config user.name "AegisOps Test"
  git -C "${target}" add README.md docs scripts control-plane/aegisops
  git -C "${target}" commit -q -m "fixture"
}

new_fixture() {
  local name="$1"
  local target="${workdir}/${name}"

  cp -R "${workdir}/valid" "${target}"
  printf '%s\n' "${target}"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-66-closeout-evaluation.md"
}

comment_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E/<!-- $ENV{TEXT} -->/g' \
    "${target}/docs/phase-66-closeout-evaluation.md"
}

fence_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e \
    's/\Q$ENV{TEXT}\E/```\n$ENV{TEXT}\n```/g' \
    "${target}/docs/phase-66-closeout-evaluation.md"
}

blockquote_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E/> $ENV{TEXT}/g' \
    "${target}/docs/phase-66-closeout-evaluation.md"
}

duplicate_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e \
    's/\Q$ENV{TEXT}\E/$ENV{TEXT}\n$ENV{TEXT}/g' \
    "${target}/docs/phase-66-closeout-evaluation.md"
}

add_verdict_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e \
    's/^## Verdict\n/## Verdict\n$ENV{TEXT}\n/m' \
    "${target}/docs/phase-66-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="$(new_fixture "missing-doc")"
rm "${missing_doc_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66 RC closeout evaluation"

missing_reference_repo="$(new_fixture "missing-reference")"
rm "${missing_reference_repo}/docs/phase-66-7-rc-authority-boundary-proof-pack.md"
assert_fails_with "${missing_reference_repo}" \
  "Missing Phase 66 closeout reference docs/phase-66-7-rc-authority-boundary-proof-pack.md"

missing_readme_repo="$(new_fixture "missing-readme")"
perl -0pi -e \
  's/- \[Phase 66\.8 RC closeout evaluation\]\(docs\/phase-66-closeout-evaluation\.md\)[^\n]*\n//' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README Phase 66.8 closeout reference"

missing_heading_repo="$(new_fixture "missing-heading")"
perl -0pi -e 's/^## Accepted Limitations$/## Deferred Items/m' \
  "${missing_heading_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${missing_heading_repo}" \
  "Expected exactly one Phase 66 closeout section: ## Accepted Limitations"

missing_child_repo="$(new_fixture "missing-child")"
remove_doc_text "${missing_child_repo}" \
  "| #1404 | Phase 66.7 RC authority-boundary proof pack | Closed. \`docs/phase-66-7-rc-authority-boundary-proof-pack.md\` and its focused verifier and self-test collect negative observations across the Phase 66 journey without treating subordinate evidence as authority or accepting an RC or GA gate. |"
assert_fails_with "${missing_child_repo}" \
  "Expected exactly one Phase 66 child issue outcome row"

commented_child_repo="$(new_fixture "commented-child")"
comment_doc_text "${commented_child_repo}" \
  "| #1404 | Phase 66.7 RC authority-boundary proof pack | Closed. \`docs/phase-66-7-rc-authority-boundary-proof-pack.md\` and its focused verifier and self-test collect negative observations across the Phase 66 journey without treating subordinate evidence as authority or accepting an RC or GA gate. |"
assert_fails_with "${commented_child_repo}" \
  "Expected exactly one Phase 66 child issue outcome row"

fenced_child_repo="$(new_fixture "fenced-child")"
fence_doc_text "${fenced_child_repo}" \
  "| #1404 | Phase 66.7 RC authority-boundary proof pack | Closed. \`docs/phase-66-7-rc-authority-boundary-proof-pack.md\` and its focused verifier and self-test collect negative observations across the Phase 66 journey without treating subordinate evidence as authority or accepting an RC or GA gate. |"
assert_fails_with "${fenced_child_repo}" \
  "Expected exactly one Phase 66 child issue outcome row"

blockquote_child_repo="$(new_fixture "blockquote-child")"
blockquote_doc_text "${blockquote_child_repo}" \
  "| #1404 | Phase 66.7 RC authority-boundary proof pack | Closed. \`docs/phase-66-7-rc-authority-boundary-proof-pack.md\` and its focused verifier and self-test collect negative observations across the Phase 66 journey without treating subordinate evidence as authority or accepting an RC or GA gate. |"
assert_fails_with "${blockquote_child_repo}" \
  "Expected exactly one Phase 66 child issue outcome row"

duplicate_child_repo="$(new_fixture "duplicate-child")"
duplicate_doc_text "${duplicate_child_repo}" \
  "| #1404 | Phase 66.7 RC authority-boundary proof pack | Closed. \`docs/phase-66-7-rc-authority-boundary-proof-pack.md\` and its focused verifier and self-test collect negative observations across the Phase 66 journey without treating subordinate evidence as authority or accepting an RC or GA gate. |"
assert_fails_with "${duplicate_child_repo}" \
  "Expected exactly one Phase 66 child issue outcome row"

missing_surface_repo="$(new_fixture "missing-surface")"
remove_doc_text "${missing_surface_repo}" \
  "- \`docs/phase-66-6-rc-supportability-proof.md\`"
assert_fails_with "${missing_surface_repo}" \
  "Expected exactly one Phase 66 changed proof surface"

missing_verifier_repo="$(new_fixture "missing-verifier")"
remove_doc_text "${missing_verifier_repo}" \
  "- \`bash scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh\`"
assert_fails_with "${missing_verifier_repo}" \
  "Expected exactly one Phase 66 verifier evidence line"

missing_verifier_script_repo="$(new_fixture "missing-verifier-script")"
rm "${missing_verifier_script_repo}/scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh"
assert_fails_with "${missing_verifier_script_repo}" \
  "Missing Phase 66 verifier script scripts/verify-phase-66-7-rc-authority-boundary-proof-pack.sh"

missing_issue_lint_repo="$(new_fixture "missing-issue-lint")"
remove_doc_text "${missing_issue_lint_repo}" \
  "- \`node <codex-supervisor-root>/dist/index.js issue-lint 1405 --config <supervisor-config-path>\`"
assert_fails_with "${missing_issue_lint_repo}" \
  "Expected exactly one Phase 66 issue-lint evidence line"

missing_limitation_repo="$(new_fixture "missing-limitation")"
remove_doc_text "${missing_limitation_repo}" \
  "Phase 66 does not collect real beta or design-partner evidence, prove real design-partner success, use Phase 67 to accept or materialize GA, collect production launch evidence, approve production rollout, or establish self-service commercial readiness."
assert_fails_with "${missing_limitation_repo}" "Missing Phase 66 accepted limitation"

missing_handoff_repo="$(new_fixture "missing-handoff")"
remove_doc_text "${missing_handoff_repo}" \
  "Phase 67 must collect bounded GA-prerequisite evidence independently under \`docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md\`, using repo-owned evidence and explicit maintainer review; it cannot accept or materialize GA. Any later GA acceptance requires a separately scoped gate bound to current-revision evidence and independent human approval."
assert_fails_with "${missing_handoff_repo}" "Missing Phase 67 handoff boundary"

phase67_is_ga_repo="$(new_fixture "phase67-is-ga")"
add_verdict_text "${phase67_is_ga_repo}" "Phase 67 is GA."
assert_fails_with "${phase67_is_ga_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_remains_ga_repo="$(new_fixture "phase67-remains-ga")"
add_verdict_text "${phase67_remains_ga_repo}" "Phase 67 remains GA"
assert_fails_with "${phase67_remains_ga_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_becomes_ga_table_repo="$(new_fixture "phase67-becomes-ga-table")"
add_verdict_text "${phase67_becomes_ga_table_repo}" \
  "| Phase 67 | becomes | the GA gate |"
assert_fails_with "${phase67_becomes_ga_table_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_colon_mapping_repo="$(new_fixture "phase67-colon-mapping")"
add_verdict_text "${phase67_colon_mapping_repo}" \
  "Phase 67: becomes the GA gate."
assert_fails_with "${phase67_colon_mapping_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_stays_ga_repo="$(new_fixture "phase67-stays-ga")"
add_verdict_text "${phase67_stays_ga_repo}" "Phase 67 stays the GA gate!"
assert_fails_with "${phase67_stays_ga_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_equals_ga_repo="$(new_fixture "phase67-equals-ga")"
add_verdict_text "${phase67_equals_ga_repo}" "Phase 67 equals GA"
assert_fails_with "${phase67_equals_ga_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_accepts_ga_repo="$(new_fixture "phase67-accepts-ga")"
add_verdict_text "${phase67_accepts_ga_repo}" \
  "Phase 67 accepts the GA gate."
assert_fails_with "${phase67_accepts_ga_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_materializes_ga_repo="$(new_fixture "phase67-materializes-ga")"
add_verdict_text "${phase67_materializes_ga_repo}" "Phase 67 materializes GA."
assert_fails_with "${phase67_materializes_ga_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_negated_mappings_repo="$(new_fixture "phase67-negated-mappings")"
add_verdict_text "${phase67_negated_mappings_repo}" \
  $'Phase 67 is not GA.\nThis closeout does not claim Phase 67 remains GA.\nWe do not claim Phase 67 stays GA.\nPhase 67 must not remain GA.\nPhase 67 cannot become GA.\nThis policy can not establish that Phase 67 is GA.\nThese are not claims: Phase 67 equals GA.\nThe verifier must reject Phase 67 becomes GA.\nForbidden wording: Phase 67 stays the GA gate.\nNon-claims: Phase 67 remains GA.\n| Phase 67 equals the GA gate | false |'
assert_passes "${phase67_negated_mappings_repo}"

phase67_ga_qualifiers_repo="$(new_fixture "phase67-ga-qualifiers")"
add_verdict_text "${phase67_ga_qualifiers_repo}" \
  $'Phase 67 is GA-prerequisite validation.\nPhase 67 becomes the GA readiness boundary.\nPhase 67 remains GA evidence.\nPhase 67 stays GA criteria.\nPhase 67 equals the GA precondition.'
assert_passes "${phase67_ga_qualifiers_repo}"

phase67_unrelated_negation_repo="$(new_fixture "phase67-unrelated-negation")"
add_verdict_text "${phase67_unrelated_negation_repo}" \
  "Phase 67 is GA, but this does not claim production readiness."
assert_fails_with "${phase67_unrelated_negation_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_negation_before_positive_repo="$(new_fixture "phase67-negation-before-positive")"
add_verdict_text "${phase67_negation_before_positive_repo}" \
  "This does not claim production readiness, but Phase 67 remains GA."
assert_fails_with "${phase67_negation_before_positive_repo}" \
  "Phase 67 cannot accept or materialize GA"

phase67_unrelated_colon_negation_repo="$(new_fixture "phase67-unrelated-colon-negation")"
add_verdict_text "${phase67_unrelated_colon_negation_repo}" \
  "This release is not a drill: Phase 67 is GA."
assert_fails_with "${phase67_unrelated_colon_negation_repo}" \
  "Phase 67 cannot accept or materialize GA"

missing_recorded_result_repo="$(new_fixture "missing-recorded-result")"
remove_doc_text "${missing_recorded_result_repo}" \
  "Recorded result on 2026-07-24: issues #1397 through #1405 each reported \`execution_ready=yes\`, \`missing_required=none\`, \`missing_recommended=none\`, \`metadata_errors=none\`, and \`high_risk_blocking_ambiguity=none\`."
assert_fails_with "${missing_recorded_result_repo}" \
  "Missing required Phase 66 closeout term"

ga_ready_repo="$(new_fixture "ga-ready")"
printf '%s\n' "Phase 66 is GA ready." \
  >>"${ga_ready_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${ga_ready_repo}" "readiness or authority claim"

ready_for_ga_repo="$(new_fixture "ready-for-ga")"
printf '%s\n' "Phase 66 is ready for GA." \
  >>"${ready_for_ga_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${ready_for_ga_repo}" "readiness or authority claim"

generally_available_repo="$(new_fixture "generally-available")"
printf '%s\n' "AegisOps is generally available." \
  >>"${generally_available_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${generally_available_repo}" "readiness or authority claim"

ga_achieved_repo="$(new_fixture "ga-achieved")"
printf '%s\n' "GA readiness has been achieved." \
  >>"${ga_achieved_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${ga_achieved_repo}" "readiness or authority claim"

ga_table_repo="$(new_fixture "ga-table")"
printf '%s\n' "| GA gate | accepted |" \
  >>"${ga_table_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${ga_table_repo}" "readiness or authority claim"

production_ready_repo="$(new_fixture "production-ready")"
printf '%s\n' "AegisOps production rollout is ready." \
  >>"${production_ready_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${production_ready_repo}" "readiness or authority claim"

production_complete_repo="$(new_fixture "production-complete")"
printf '%s\n' "Production rollout readiness is complete." \
  >>"${production_complete_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${production_complete_repo}" "readiness or authority claim"

self_service_repo="$(new_fixture "self-service")"
printf '%s\n' "Self-service commercial readiness is achieved." \
  >>"${self_service_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${self_service_repo}" "readiness or authority claim"

parity_repo="$(new_fixture "broad-parity")"
printf '%s\n' "Broad enterprise SIEM/SOAR parity is achieved." \
  >>"${parity_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${parity_repo}" "readiness or authority claim"

verifier_truth_repo="$(new_fixture "verifier-truth")"
printf '%s\n' "Verifier output is readiness truth." \
  >>"${verifier_truth_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${verifier_truth_repo}" "readiness or authority claim"

issue_lint_truth_repo="$(new_fixture "issue-lint-truth")"
printf '%s\n' "Issue-lint output becomes closeout truth." \
  >>"${issue_lint_truth_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${issue_lint_truth_repo}" "readiness or authority claim"

wazuh_truth_repo="$(new_fixture "wazuh-truth")"
printf '%s\n' "Wazuh signals are workflow truth." \
  >>"${wazuh_truth_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${wazuh_truth_repo}" "readiness or authority claim"

closure_truth_repo="$(new_fixture "closure-truth")"
printf '%s\n' "Issue closure proves GA readiness." \
  >>"${closure_truth_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${closure_truth_repo}" "readiness or authority claim"

achieved_ga_repo="$(new_fixture "achieved-ga")"
printf '%s\n' "Phase 66 has achieved GA readiness." \
  >>"${achieved_ga_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${achieved_ga_repo}" "readiness or authority claim"

ready_for_production_repo="$(new_fixture "ready-for-production")"
printf '%s\n' "AegisOps is ready for production rollout." \
  >>"${ready_for_production_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${ready_for_production_repo}" "readiness or authority claim"

has_parity_repo="$(new_fixture "has-parity")"
printf '%s\n' "AegisOps has established broad enterprise SIEM/SOAR parity." \
  >>"${has_parity_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${has_parity_repo}" "readiness or authority claim"

denial_then_claim_repo="$(new_fixture "denial-then-claim")"
printf '%s\n' "Without external evidence, Phase 66 is GA ready." \
  >>"${denial_then_claim_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${denial_then_claim_repo}" \
  "Forbidden Phase 66 closeout evaluation"

elided_subject_repo="$(new_fixture "elided-subject")"
printf '%s\n' "Phase 66 does not claim GA readiness and it is GA ready." \
  >>"${elided_subject_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${elided_subject_repo}" \
  "Forbidden Phase 66 closeout evaluation"

issue_lint_gate_repo="$(new_fixture "issue-lint-gate")"
printf '%s\n' "Issue-lint output passes the GA gate." \
  >>"${issue_lint_gate_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${issue_lint_gate_repo}" "readiness or authority claim"

issue_lint_authoritative_repo="$(new_fixture "issue-lint-authoritative")"
printf '%s\n' "Issue-lint output is authoritative." \
  >>"${issue_lint_authoritative_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${issue_lint_authoritative_repo}" "readiness or authority claim"

wazuh_authority_repo="$(new_fixture "wazuh-authority")"
printf '%s\n' "Wazuh signals can close cases." \
  >>"${wazuh_authority_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${wazuh_authority_repo}" "readiness or authority claim"

commented_overclaim_repo="$(new_fixture "commented-overclaim")"
printf '%s\n' "<!-- Phase 66 is GA ready. -->" \
  >>"${commented_overclaim_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${commented_overclaim_repo}" "readiness or authority claim"

fenced_overclaim_repo="$(new_fixture "fenced-overclaim")"
printf '%s\n' '```text' "Phase 66 is GA ready." '```' \
  >>"${fenced_overclaim_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${fenced_overclaim_repo}" "readiness or authority claim"

secret_repo="$(new_fixture "secret")"
printf '%s\n' "api_key=actual-production-secret-value" \
  >>"${secret_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${secret_repo}" "production secret-looking value detected"

formatted_secret_repo="$(new_fixture "formatted-secret")"
printf '%s\n' 'api**_key**: actual-production-secret-value' \
  >>"${formatted_secret_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${formatted_secret_repo}" "production secret-looking value detected"

entity_secret_repo="$(new_fixture "entity-secret")"
printf '%s\n' 'api&#95;key&#61;actual-production-secret-value' \
  >>"${entity_secret_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${entity_secret_repo}" "production secret-looking value detected"

prose_secret_repo="$(new_fixture "prose-secret")"
printf '%s\n' "API key is actual-production-secret-value" \
  >>"${prose_secret_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${prose_secret_repo}" "production secret-looking value detected"

commented_secret_repo="$(new_fixture "commented-secret")"
printf '%s\n' "<!-- token=actual-production-secret-value -->" \
  >>"${commented_secret_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${commented_secret_repo}" "production secret-looking value detected"

customer_private_repo="$(new_fixture "customer-private")"
printf '%s\n' "This closeout includes unredacted customer ticket data." \
  >>"${customer_private_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

customer_id_repo="$(new_fixture "customer-id")"
printf '%s\n' "customer_id=customer-0042" \
  >>"${customer_id_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${customer_id_repo}" "customer-private data detected"

customer_email_repo="$(new_fixture "customer-email")"
printf '%s\n' "Evidence owner: alice@example.com" \
  >>"${customer_email_repo}/docs/phase-66-closeout-evaluation.md"
assert_fails_with "${customer_email_repo}" "customer-private data detected"

path_repo="$(new_fixture "path")"
users_segment="Users"
printf '%s\n' "Operator note references /${users_segment}/local/aegisops." \
  >>"${path_repo}/docs/phase-66-closeout-evaluation.md"
git -C "${path_repo}" add docs/phase-66-closeout-evaluation.md
git -C "${path_repo}" commit -q -m "path"
assert_fails_with "${path_repo}" \
  "Forbidden Phase 66 closeout evaluation absolute path usage detected"

echo "Phase 66.8 RC closeout verifier self-test passes."
