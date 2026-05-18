#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-62-8-closeout-evaluation.sh"

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

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}/docs"
  cp "${repo_root}/docs/phase-62-closeout-evaluation.md" "${target}/docs/phase-62-closeout-evaluation.md"
  cp "${repo_root}/README.md" "${target}/README.md"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-62-closeout-evaluation.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

url_path_repo="${workdir}/url-path"
copy_valid_repo "${url_path_repo}"
users_segment="Users"
home_segment="home"
root_segment="root"
etc_segment="etc"
mnt_segment="mnt"
printf '%s\n' \
  "Reference URL: https://example.com/${home_segment}/docs/phase-62-closeout" \
  "Reference URL: https://example.com/${root_segment}/docs/phase-62-closeout" \
  "Reference URL: https://example.com/C:/${users_segment}/docs/phase-62-closeout" \
  >>"${url_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${url_path_repo}"

root_relative_link_repo="${workdir}/root-relative-link"
copy_valid_repo "${root_relative_link_repo}"
printf '%s\n' "[Reference](/docs/phase-62-closeout-evaluation)" >>"${root_relative_link_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${root_relative_link_repo}"

root_relative_link_query_repo="${workdir}/root-relative-link-query"
copy_valid_repo "${root_relative_link_query_repo}"
printf '%s\n' "[Reference](/docs/phase-62-closeout-evaluation?view=1#evidence)" >>"${root_relative_link_query_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${root_relative_link_query_repo}"

api_path_repo="${workdir}/api-path"
copy_valid_repo "${api_path_repo}"
printf '%s\n' "Endpoint path /api/v1/cases is documented." >>"${api_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${api_path_repo}"

optional_path_repo="${workdir}/optional-path"
copy_valid_repo "${optional_path_repo}"
printf '%s\n' "Endpoint path /optional/features remains documented." >>"${optional_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${optional_path_repo}"

gateway_ready_repo="${workdir}/gateway-ready"
copy_valid_repo "${gateway_ready_repo}"
printf '%s\n' "AegisOps is gateway-ready for docs." >>"${gateway_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${gateway_ready_repo}"

missing_doc_repo="${workdir}/missing-doc"
mkdir -p "${missing_doc_repo}/docs"
cp "${repo_root}/README.md" "${missing_doc_repo}/README.md"
assert_fails_with \
  "${missing_doc_repo}" \
  "Missing Phase 62 closeout evaluation: docs/phase-62-closeout-evaluation.md"

missing_readme_canonical_bullet_repo="${workdir}/missing-readme-canonical-bullet"
copy_valid_repo "${missing_readme_canonical_bullet_repo}"
perl -0pi -e 's/- \[Phase 62\.8 closeout evaluation\]\(docs\/phase-62-closeout-evaluation\.md\)[^\n]*\n/- Phase 62.8 closeout evaluation\\n/' \
  "${missing_readme_canonical_bullet_repo}/README.md"
assert_fails_with \
  "${missing_readme_canonical_bullet_repo}" \
  "Missing README canonical cross-phase boundary bullet: - [Phase 62.8 closeout evaluation](docs/phase-62-closeout-evaluation.md)"

missing_child_repo="${workdir}/missing-child"
copy_valid_repo "${missing_child_repo}"
remove_doc_text "${missing_child_repo}" \
  "| #1322 | Phase 62.8 Phase 62 closeout evaluation | Open until this document and focused closeout verifier land. |"
assert_fails_with \
  "${missing_child_repo}" \
  "Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: | #1322 | Phase 62.8 Phase 62 closeout evaluation | Open until this document and focused closeout verifier land. |"

missing_child_row_repo="${workdir}/missing-child-row"
copy_valid_repo "${missing_child_row_repo}"
remove_doc_text "${missing_child_row_repo}" \
  "| #1315 | Phase 62.1 reviewed automation catalog contract | Closed. \`docs/phase-62-reviewed-automation-catalog-contract.md\`, validation notes, focused verifier, and backend contract tests prove the bounded default Read, Notify, and Soft Write catalog without direct Shuffle launch, marketplace expansion, or write-authority overclaim. |"
assert_fails_with \
  "${missing_child_row_repo}" \
  "Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: | #1315 | Phase 62.1 reviewed automation catalog contract | Closed."

child_row_outside_table_repo="${workdir}/child-row-outside-table"
copy_valid_repo "${child_row_outside_table_repo}"
remove_doc_text "${child_row_outside_table_repo}" \
  "| #1316 | Phase 62.2 per-action policy registry | Closed. \`control-plane/aegisops/control_plane/actions/action_policy_registry.py\`, focused policy tests, and service persistence tests prove reviewed requester, reviewer, scope, idempotency, protected-target, and expiry checks for catalog actions. |"
printf '%s\n' \
  "| #1316 | Phase 62.2 per-action policy registry | Closed. \`control-plane/aegisops/control_plane/actions/action_policy_registry.py\`, focused policy tests, and service persistence tests prove reviewed requester, reviewer, scope, idempotency, protected-target, and expiry checks for catalog actions. |" \
  >>"${child_row_outside_table_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${child_row_outside_table_repo}" \
  "Missing Phase 62 child issue outcome row in Child Issue Outcomes table: | #1316 | Phase 62.2 per-action policy registry | Closed."

missing_issue_lint_repo="${workdir}/missing-issue-lint"
copy_valid_repo "${missing_issue_lint_repo}"
perl -0pi -e 's/- `node <codex-supervisor-root>\/dist\/index\.js issue-lint 1322 --config <supervisor-config-path>`.*\n//m' \
  "${missing_issue_lint_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${missing_issue_lint_repo}" \
  'Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: `node <codex-supervisor-root>/dist/index.js issue-lint 1322 --config <supervisor-config-path>`'

missing_issue_lint_summary_repo="${workdir}/missing-issue-lint-summary"
copy_valid_repo "${missing_issue_lint_summary_repo}"
remove_doc_text "${missing_issue_lint_summary_repo}" \
  'Each command should report `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`, and no blocking high-risk ambiguity before Phase 62 is considered fully closed.'
assert_fails_with \
  "${missing_issue_lint_summary_repo}" \
  'Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: Each command should report `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`'

issue_lint_summary_outside_section_repo="${workdir}/issue-lint-summary-outside-section"
copy_valid_repo "${issue_lint_summary_outside_section_repo}"
remove_doc_text "${issue_lint_summary_outside_section_repo}" \
  'Each command should report `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`, and no blocking high-risk ambiguity before Phase 62 is considered fully closed.'
printf '%s\n' \
  'Each command should report `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`, and no blocking high-risk ambiguity before Phase 62 is considered fully closed.' \
  >>"${issue_lint_summary_outside_section_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${issue_lint_summary_outside_section_repo}" \
  'Missing Phase 62 issue-lint evidence line in Issue-lint evidence section: Each command should report `execution_ready=yes`, `missing_required=none`, `metadata_errors=none`'

missing_authority_repo="${workdir}/missing-authority"
copy_valid_repo "${missing_authority_repo}"
remove_doc_text "${missing_authority_repo}" \
  "AegisOps records remain authoritative for case, evidence, approval, action request, execution receipt, reconciliation, audit, release, gate, limitation, and closeout truth."
assert_fails_with \
  "${missing_authority_repo}" \
  "Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: AegisOps records remain authoritative"

missing_path_hygiene_repo="${workdir}/missing-path-hygiene"
copy_valid_repo "${missing_path_hygiene_repo}"
remove_doc_text "${missing_path_hygiene_repo}" \
  "Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output."
assert_fails_with \
  "${missing_path_hygiene_repo}" \
  "Missing required Phase 62 closeout term in docs/phase-62-closeout-evaluation.md: Path hygiene rejects workstation-local absolute paths in publishable docs, scripts, tests, prompts, and validation output."

downstream_truth_repo="${workdir}/downstream-truth"
copy_valid_repo "${downstream_truth_repo}"
printf '%s\n' "Downstream workflow state is AegisOps truth." >>"${downstream_truth_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${downstream_truth_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: downstream workflow state is aegisops truth"

simulator_truth_repo="${workdir}/simulator-truth"
copy_valid_repo "${simulator_truth_repo}"
printf '%s\n' "Simulator output is production truth." >>"${simulator_truth_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${simulator_truth_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: simulator output is production truth"

shuffle_truth_sentence_repo="${workdir}/shuffle-truth-sentence"
copy_valid_repo "${shuffle_truth_sentence_repo}"
printf '%s\n' "Shuffle workflow state is AegisOps truth." >>"${shuffle_truth_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${shuffle_truth_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

simulator_truth_sentence_repo="${workdir}/simulator-truth-sentence"
copy_valid_repo "${simulator_truth_sentence_repo}"
printf '%s\n' "Simulator output is AegisOps production truth." >>"${simulator_truth_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${simulator_truth_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

ticket_truth_sentence_repo="${workdir}/ticket-truth-sentence"
copy_valid_repo "${ticket_truth_sentence_repo}"
printf '%s\n' "Ticket state is AegisOps truth." >>"${ticket_truth_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${ticket_truth_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

ui_authority_sentence_repo="${workdir}/ui-authority-sentence"
copy_valid_repo "${ui_authority_sentence_repo}"
printf '%s\n' "UI cache authorizes approvals." >>"${ui_authority_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${ui_authority_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

browser_authority_sentence_repo="${workdir}/browser-authority-sentence"
copy_valid_repo "${browser_authority_sentence_repo}"
printf '%s\n' "Browser state executes reviewed actions." >>"${browser_authority_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${browser_authority_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

controlled_write_repo="${workdir}/controlled-write"
copy_valid_repo "${controlled_write_repo}"
printf '%s\n' "Controlled Write is default enabled." >>"${controlled_write_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${controlled_write_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: controlled write is default enabled"

controlled_write_sentence_repo="${workdir}/controlled-write-sentence"
copy_valid_repo "${controlled_write_sentence_repo}"
printf '%s\n' "Controlled Write defaults are enabled." >>"${controlled_write_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${controlled_write_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: write-default overclaim"

hard_write_sentence_repo="${workdir}/hard-write-sentence"
copy_valid_repo "${hard_write_sentence_repo}"
printf '%s\n' "Hard Write defaults are enabled." >>"${hard_write_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${hard_write_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: write-default overclaim"

marketplace_repo="${workdir}/marketplace"
copy_valid_repo "${marketplace_repo}"
printf '%s\n' "Broad SOAR marketplace is complete." >>"${marketplace_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${marketplace_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: broad soar marketplace is complete"

marketplace_sentence_repo="${workdir}/marketplace-sentence"
copy_valid_repo "${marketplace_sentence_repo}"
printf '%s\n' "Broad SOAR marketplace coverage is available in this release." >>"${marketplace_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${marketplace_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: broad SOAR marketplace overclaim"

soar_marketplace_sentence_repo="${workdir}/soar-marketplace-sentence"
copy_valid_repo "${soar_marketplace_sentence_repo}"
printf '%s\n' "SOAR marketplace coverage is available." >>"${soar_marketplace_sentence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${soar_marketplace_sentence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: broad SOAR marketplace overclaim"

phase63_repo="${workdir}/phase63"
copy_valid_repo "${phase63_repo}"
printf '%s\n' "Phase 63 evidence expansion is implemented." >>"${phase63_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase63_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: phase 63 evidence expansion is implemented"

phase63_available_repo="${workdir}/phase63-available"
copy_valid_repo "${phase63_available_repo}"
printf '%s\n' "Phase 63 evidence expansion is available now." >>"${phase63_available_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase63_available_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase66_repo="${workdir}/phase66"
copy_valid_repo "${phase66_repo}"
printf '%s\n' "Phase 66 RC proof is fully complete." >>"${phase66_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase66_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

commercial_repo="${workdir}/commercial"
copy_valid_repo "${commercial_repo}"
printf '%s\n' "AegisOps is a commercial replacement for every SIEM/SOAR capability." >>"${commercial_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${commercial_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: aegisops is a commercial replacement for every siem/soar capability"

aegisops_has_entered_repo="${workdir}/aegisops-has-entered"
copy_valid_repo "${aegisops_has_entered_repo}"
printf '%s\n' "AegisOps has entered GA." >>"${aegisops_has_entered_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_has_entered_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_has_become_repo="${workdir}/aegisops-has-become"
copy_valid_repo "${aegisops_has_become_repo}"
printf '%s\n' "AegisOps has become GA." >>"${aegisops_has_become_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_has_become_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_became_repo="${workdir}/aegisops-became"
copy_valid_repo "${aegisops_became_repo}"
printf '%s\n' "AegisOps became GA." >>"${aegisops_became_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_became_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_has_been_repo="${workdir}/aegisops-has-been"
copy_valid_repo "${aegisops_has_been_repo}"
printf '%s\n' "AegisOps has been GA." >>"${aegisops_has_been_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_has_been_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_is_now_repo="${workdir}/aegisops-is-now"
copy_valid_repo "${aegisops_is_now_repo}"
printf '%s\n' "AegisOps is now GA." >>"${aegisops_is_now_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_is_now_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_is_officially_repo="${workdir}/aegisops-is-officially"
copy_valid_repo "${aegisops_is_officially_repo}"
printf '%s\n' "AegisOps is officially GA." >>"${aegisops_is_officially_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_is_officially_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_remains_repo="${workdir}/aegisops-remains"
copy_valid_repo "${aegisops_remains_repo}"
printf '%s\n' "AegisOps remains GA." >>"${aegisops_remains_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_remains_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_has_now_entered_repo="${workdir}/aegisops-has-now-entered"
copy_valid_repo "${aegisops_has_now_entered_repo}"
printf '%s\n' "AegisOps has now entered GA." >>"${aegisops_has_now_entered_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_has_now_entered_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_can_be_repo="${workdir}/aegisops-can-be"
copy_valid_repo "${aegisops_can_be_repo}"
printf '%s\n' "AegisOps can be GA ready." >>"${aegisops_can_be_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_can_be_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_has_proven_repo="${workdir}/aegisops-has-proven"
copy_valid_repo "${aegisops_has_proven_repo}"
printf '%s\n' "AegisOps has proven GA readiness." >>"${aegisops_has_proven_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_has_proven_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_commercially_hyphen_ready_repo="${workdir}/aegisops-commercially-hyphen-ready"
copy_valid_repo "${aegisops_commercially_hyphen_ready_repo}"
printf '%s\n' "AegisOps is commercially-ready." >>"${aegisops_commercially_hyphen_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_commercially_hyphen_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_release_candidate_hyphen_ready_repo="${workdir}/aegisops-release-candidate-hyphen-ready"
copy_valid_repo "${aegisops_release_candidate_hyphen_ready_repo}"
printf '%s\n' "AegisOps is release-candidate ready." >>"${aegisops_release_candidate_hyphen_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_release_candidate_hyphen_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

production_secret_repo="${workdir}/production-secret"
copy_valid_repo "${production_secret_repo}"
printf '%s\n' "Production secrets are valid evidence for Phase 62." >>"${production_secret_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${production_secret_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production secrets are valid"

production_secret_evidence_repo="${workdir}/production-secret-evidence"
copy_valid_repo "${production_secret_evidence_repo}"
printf '%s\n' "Production secrets count as valid evidence." >>"${production_secret_evidence_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${production_secret_evidence_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production-secret overclaim"

production_secret_used_repo="${workdir}/production-secret-used"
copy_valid_repo "${production_secret_used_repo}"
printf '%s\n' "Production secrets may be used for validation." >>"${production_secret_used_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${production_secret_used_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production-secret overclaim"

production_secret_acceptable_repo="${workdir}/production-secret-acceptable"
copy_valid_repo "${production_secret_acceptable_repo}"
printf '%s\n' "Production secret material is acceptable for closeout evidence." >>"${production_secret_acceptable_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${production_secret_acceptable_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production-secret overclaim"

live_secret_acceptable_repo="${workdir}/live-secret-acceptable"
copy_valid_repo "${live_secret_acceptable_repo}"
printf '%s\n' "Live secret material is acceptable for closeout evidence." >>"${live_secret_acceptable_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${live_secret_acceptable_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production-secret overclaim"

production_secret_satisfies_repo="${workdir}/production-secret-satisfies"
copy_valid_repo "${production_secret_satisfies_repo}"
printf '%s\n' "Production-secret evidence satisfies Phase 62 closeout evidence." >>"${production_secret_satisfies_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${production_secret_satisfies_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: production-secret overclaim"

production_secret_negative_context_repo="${workdir}/production-secret-negative-context"
copy_valid_repo "${production_secret_negative_context_repo}"
printf '%s\n' "Production secrets are not yet allowed." >>"${production_secret_negative_context_repo}/docs/phase-62-closeout-evaluation.md"
assert_passes "${production_secret_negative_context_repo}"

phase62_readiness_repo="${workdir}/phase62-readiness"
copy_valid_repo "${phase62_readiness_repo}"
printf '%s\n' "Phase 62 is RC ready." >>"${phase62_readiness_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_readiness_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_was_ready_repo="${workdir}/phase62-was-ready"
copy_valid_repo "${phase62_was_ready_repo}"
printf '%s\n' "Phase 62 was GA ready." >>"${phase62_was_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_was_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_direct_ga_repo="${workdir}/phase62-direct-ga"
copy_valid_repo "${phase62_direct_ga_repo}"
printf '%s\n' "Phase 62 is GA." >>"${phase62_direct_ga_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_direct_ga_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_reached_ga_repo="${workdir}/phase62-reached-ga"
copy_valid_repo "${phase62_reached_ga_repo}"
printf '%s\n' "Phase 62 reached GA." >>"${phase62_reached_ga_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_reached_ga_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_remains_ga_ready_repo="${workdir}/phase62-remains-ga-ready"
copy_valid_repo "${phase62_remains_ga_ready_repo}"
printf '%s\n' "Phase 62 remains GA ready." >>"${phase62_remains_ga_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_remains_ga_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_remained_ga_ready_repo="${workdir}/phase62-remained-ga-ready"
copy_valid_repo "${phase62_remained_ga_ready_repo}"
printf '%s\n' "Phase 62 remained GA ready." >>"${phase62_remained_ga_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_remained_ga_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_readiness_direct_repo="${workdir}/phase62-readiness-direct"
copy_valid_repo "${phase62_readiness_direct_repo}"
printf '%s\n' "Phase 62 is commercially ready." >>"${phase62_readiness_direct_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_readiness_direct_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_readiness_achieved_repo="${workdir}/phase62-readiness-achieved"
copy_valid_repo "${phase62_readiness_achieved_repo}"
printf '%s\n' "Phase 62 readiness is achieved." >>"${phase62_readiness_achieved_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_readiness_achieved_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_readiness_colon_repo="${workdir}/phase62-readiness-colon"
copy_valid_repo "${phase62_readiness_colon_repo}"
printf '%s\n' "This does not change our status: Phase 62 is GA ready." >>"${phase62_readiness_colon_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_readiness_colon_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_readiness_no_separator_repo="${workdir}/phase62-readiness-no-separator"
copy_valid_repo "${phase62_readiness_no_separator_repo}"
printf '%s\n' "This does not change our status Phase 62 is GA ready." >>"${phase62_readiness_no_separator_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_readiness_no_separator_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

required_rejection_piggyback_repo="${workdir}/required-rejection-piggyback"
copy_valid_repo "${required_rejection_piggyback_repo}"
printf '%s %s\n' \
  "Phase 62 must reject missing child evidence, missing verifier output, missing issue-lint summary, downstream workflow truth claims, simulator production truth claims, Controlled Write or Hard Write default enablement claims, broad SOAR marketplace claims, Phase 63 evidence expansion claims, Phase 66 RC proof claims, Beta/RC/GA/commercial-readiness claims, production secrets, and workstation-local paths." \
  "Phase 62 is GA ready." \
  >>"${required_rejection_piggyback_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${required_rejection_piggyback_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_has_become_repo="${workdir}/phase62-has-become"
copy_valid_repo "${phase62_has_become_repo}"
printf '%s\n' "Phase 62 has become RC ready." >>"${phase62_has_become_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_has_become_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_hyphen_ready_repo="${workdir}/phase62-hyphen-ready"
copy_valid_repo "${phase62_hyphen_ready_repo}"
printf '%s\n' "Phase 62 is RC-ready." >>"${phase62_hyphen_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_hyphen_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_without_prefix_repo="${workdir}/phase62-without-prefix"
copy_valid_repo "${phase62_without_prefix_repo}"
printf '%s\n' "Without delay, Phase 62 is commercially ready." >>"${phase62_without_prefix_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_without_prefix_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_without_any_prefix_repo="${workdir}/phase62-without-any-prefix"
copy_valid_repo "${phase62_without_any_prefix_repo}"
printf '%s\n' "Without any hesitation, Phase 62 is GA ready." >>"${phase62_without_any_prefix_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_without_any_prefix_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_markdown_ready_repo="${workdir}/phase62-markdown-ready"
copy_valid_repo "${phase62_markdown_ready_repo}"
printf '%s\n' "Phase 62 is **GA** ready." >>"${phase62_markdown_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_markdown_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_markdown_link_ready_repo="${workdir}/phase62-markdown-link-ready"
copy_valid_repo "${phase62_markdown_link_ready_repo}"
printf '%s\n' "Phase 62 is [GA](https://example.com) ready." >>"${phase62_markdown_link_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_markdown_link_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_html_ready_repo="${workdir}/phase62-html-ready"
copy_valid_repo "${phase62_html_ready_repo}"
printf '%s\n' "Phase 62 is <b>GA</b> ready." >>"${phase62_html_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_html_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_wrapped_ready_repo="${workdir}/phase62-wrapped-ready"
copy_valid_repo "${phase62_wrapped_ready_repo}"
printf '%s\n%s\n' "Phase 62 is" "GA ready." >>"${phase62_wrapped_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_wrapped_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_blank_wrapped_ready_repo="${workdir}/phase62-blank-wrapped-ready"
copy_valid_repo "${phase62_blank_wrapped_ready_repo}"
printf '%s\n\n%s\n' "Phase 62 is" "GA ready." >>"${phase62_blank_wrapped_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_blank_wrapped_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_three_line_wrapped_ready_repo="${workdir}/phase62-three-line-wrapped-ready"
copy_valid_repo "${phase62_three_line_wrapped_ready_repo}"
printf '%s\n%s\n%s\n' "Phase 62 is" "commercially" "ready." >>"${phase62_three_line_wrapped_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_three_line_wrapped_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_ga_hyphen_ready_repo="${workdir}/phase62-ga-hyphen-ready"
copy_valid_repo "${phase62_ga_hyphen_ready_repo}"
printf '%s\n' "Phase 62 is GA-ready." >>"${phase62_ga_hyphen_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_ga_hyphen_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_hyphen_subject_ga_ready_repo="${workdir}/phase62-hyphen-subject-ga-ready"
copy_valid_repo "${phase62_hyphen_subject_ga_ready_repo}"
printf '%s\n' "Phase-62 is GA ready." >>"${phase62_hyphen_subject_ga_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_hyphen_subject_ga_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_commercially_hyphen_ready_repo="${workdir}/phase62-commercially-hyphen-ready"
copy_valid_repo "${phase62_commercially_hyphen_ready_repo}"
printf '%s\n' "Phase 62 is commercially-ready." >>"${phase62_commercially_hyphen_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_commercially_hyphen_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase62_production_hyphen_ready_repo="${workdir}/phase62-production-hyphen-ready"
copy_valid_repo "${phase62_production_hyphen_ready_repo}"
printf '%s\n' "Phase 62 is production-ready." >>"${phase62_production_hyphen_ready_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase62_production_hyphen_ready_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase66_delivered_repo="${workdir}/phase66-delivered"
copy_valid_repo "${phase66_delivered_repo}"
printf '%s\n' "Phase 66 RC proof is delivered." >>"${phase66_delivered_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase66_delivered_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase66_negated_delivered_repo="${workdir}/phase66-negated-delivered"
copy_valid_repo "${phase66_negated_delivered_repo}"
printf '%s\n' "We do not deny that Phase 66 RC proof is delivered." >>"${phase66_negated_delivered_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase66_negated_delivered_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase66_hyphen_subject_repo="${workdir}/phase66-hyphen-subject"
copy_valid_repo "${phase66_hyphen_subject_repo}"
printf '%s\n' "Phase-66 RC proof is delivered." >>"${phase66_hyphen_subject_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase66_hyphen_subject_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

phase63_hyphen_noun_repo="${workdir}/phase63-hyphen-noun"
copy_valid_repo "${phase63_hyphen_noun_repo}"
printf '%s\n' "Phase 63 evidence-expansion is delivered." >>"${phase63_hyphen_noun_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${phase63_hyphen_noun_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

aegisops_negated_has_entered_repo="${workdir}/aegisops-negated-has-entered"
copy_valid_repo "${aegisops_negated_has_entered_repo}"
printf '%s\n' "We do not deny that AegisOps has entered GA." >>"${aegisops_negated_has_entered_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${aegisops_negated_has_entered_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: release-readiness overclaim"

ticket_source_of_truth_repo="${workdir}/ticket-source-of-truth"
copy_valid_repo "${ticket_source_of_truth_repo}"
printf '%s\n' "Ticket state is AegisOps source-of-truth for closure." >>"${ticket_source_of_truth_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${ticket_source_of_truth_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

ticket_status_authority_repo="${workdir}/ticket-status-authority"
copy_valid_repo "${ticket_status_authority_repo}"
printf '%s\n' "Ticket status closes AegisOps cases." >>"${ticket_status_authority_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${ticket_status_authority_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

ui_state_authority_repo="${workdir}/ui-state-authority"
copy_valid_repo "${ui_state_authority_repo}"
printf '%s\n' "UI state authorizes approvals." >>"${ui_state_authority_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${ui_state_authority_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

browser_cache_authority_repo="${workdir}/browser-cache-authority"
copy_valid_repo "${browser_cache_authority_repo}"
printf '%s\n' "Browser cache executes reviewed actions." >>"${browser_cache_authority_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${browser_cache_authority_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

ticket_status_closed_repo="${workdir}/ticket-status-closed"
copy_valid_repo "${ticket_status_closed_repo}"
printf '%s\n' "Ticket status closed AegisOps cases." >>"${ticket_status_closed_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${ticket_status_closed_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

ui_cache_approved_repo="${workdir}/ui-cache-approved"
copy_valid_repo "${ui_cache_approved_repo}"
printf '%s\n' "UI cache approved actions." >>"${ui_cache_approved_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${ui_cache_approved_repo}" \
  "Forbidden Phase 62 closeout evaluation claim: subordinate-surface authority overclaim"

absolute_path_repo="${workdir}/absolute-path"
copy_valid_repo "${absolute_path_repo}"
printf 'Run /%s/example/Dev/codex-supervisor/dist/index.js.\n' "Users" >>"${absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

root_absolute_path_repo="${workdir}/root-absolute-path"
copy_valid_repo "${root_absolute_path_repo}"
printf 'Run /%s/example/Dev/codex-supervisor/dist/index.js.\n' "${root_segment}" >>"${root_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${root_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

tmp_absolute_path_repo="${workdir}/tmp-absolute-path"
copy_valid_repo "${tmp_absolute_path_repo}"
printf 'Run /tmp/aegisops/phase-62-closeout.\n' >>"${tmp_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${tmp_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

tmp_single_segment_absolute_path_repo="${workdir}/tmp-single-segment-absolute-path"
copy_valid_repo "${tmp_single_segment_absolute_path_repo}"
printf 'Temporary files may be stored in /tmp during validation.\n' >>"${tmp_single_segment_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${tmp_single_segment_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

tmp_markdown_link_absolute_path_repo="${workdir}/tmp-markdown-link-absolute-path"
copy_valid_repo "${tmp_markdown_link_absolute_path_repo}"
printf 'Temporary files may be linked as [tmp](/tmp/aegisops/phase-62-closeout).\n' >>"${tmp_markdown_link_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${tmp_markdown_link_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

volume_absolute_path_repo="${workdir}/volume-absolute-path"
copy_valid_repo "${volume_absolute_path_repo}"
printf 'Run /Volumes/work/aegisops/phase-62-closeout.\n' >>"${volume_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${volume_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

opt_absolute_path_repo="${workdir}/opt-absolute-path"
copy_valid_repo "${opt_absolute_path_repo}"
printf 'Run /opt/dev/aegisops/phase-62-closeout.\n' >>"${opt_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${opt_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

file_uri_opt_absolute_path_repo="${workdir}/file-uri-opt-absolute-path"
copy_valid_repo "${file_uri_opt_absolute_path_repo}"
printf 'Use file:///opt/dev/aegisops/phase-62-closeout.\n' >>"${file_uri_opt_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${file_uri_opt_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

html_home_absolute_path_repo="${workdir}/html-home-absolute-path"
copy_valid_repo "${html_home_absolute_path_repo}"
printf '<a href="/%s/dev/aegisops">artifact</a>\n' "${users_segment}" >>"${html_home_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${html_home_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

html_file_uri_opt_absolute_path_repo="${workdir}/html-file-uri-opt-absolute-path"
copy_valid_repo "${html_file_uri_opt_absolute_path_repo}"
printf '<a href="file:///opt/dev/aegisops/phase-62-closeout">artifact</a>\n' >>"${html_file_uri_opt_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${html_file_uri_opt_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

file_uri_etc_absolute_path_repo="${workdir}/file-uri-etc-absolute-path"
copy_valid_repo "${file_uri_etc_absolute_path_repo}"
printf 'Use file:///etc/aegisops/phase-62-closeout.\n' >>"${file_uri_etc_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${file_uri_etc_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

etc_absolute_path_repo="${workdir}/etc-absolute-path"
copy_valid_repo "${etc_absolute_path_repo}"
printf 'Run /%s/aegisops/phase-62-closeout.\n' "${etc_segment}" >>"${etc_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${etc_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

wsl_tmp_absolute_path_repo="${workdir}/wsl-tmp-absolute-path"
copy_valid_repo "${wsl_tmp_absolute_path_repo}"
printf 'Run /%s/c/tmp/aegisops/phase-62-closeout.\n' "${mnt_segment}" >>"${wsl_tmp_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${wsl_tmp_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

windows_tmp_absolute_path_repo="${workdir}/windows-tmp-absolute-path"
copy_valid_repo "${windows_tmp_absolute_path_repo}"
printf 'Use C:\\tmp\\aegisops\\phase-62-closeout.\n' >>"${windows_tmp_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${windows_tmp_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

windows_slash_tmp_absolute_path_repo="${workdir}/windows-slash-tmp-absolute-path"
copy_valid_repo "${windows_slash_tmp_absolute_path_repo}"
printf 'Use C:/tmp/aegisops/phase-62-closeout.\n' >>"${windows_slash_tmp_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${windows_slash_tmp_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

windows_query_absolute_path_repo="${workdir}/windows-query-absolute-path"
copy_valid_repo "${windows_query_absolute_path_repo}"
printf 'https://example.com/download?path=C:/tmp/aegisops/phase-62-closeout\n' >>"${windows_query_absolute_path_repo}/docs/phase-62-closeout-evaluation.md"
assert_fails_with \
  "${windows_query_absolute_path_repo}" \
  "Forbidden Phase 62 closeout evaluation: workstation-local absolute path detected"

echo "Phase 62 closeout verifier negative tests pass."
