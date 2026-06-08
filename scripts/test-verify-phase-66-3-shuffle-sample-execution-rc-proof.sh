#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh"

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
  copy_repo_path "${target}" "docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"

  for path in \
    "docs/phase-66-1-clean-host-rc-e2e-harness.md" \
    "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" \
    "docs/phase-51-6-authority-boundary-negative-test-policy.md" \
    "docs/deployment/shuffle-smb-single-node-profile-contract.md" \
    "docs/deployment/shuffle-reviewed-workflow-template-contract.md" \
    "docs/deployment/shuffle-notify-identity-owner-template-import-contract.md" \
    "docs/deployment/shuffle-manual-fallback-contract.md" \
    "docs/deployment/shuffle-authority-boundary-negative-tests.md" \
    "docs/deployment/case-timeline-authority-projection-contract.md" \
    "docs/phase-65-closeout-evaluation.md"; do
    copy_repo_path "${target}" "${path}"
  done

  for path in \
    "scripts/verify-phase-66-3-shuffle-sample-execution-rc-proof.sh" \
    "scripts/test-verify-phase-66-3-shuffle-sample-execution-rc-proof.sh" \
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
    "${target}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
}

comment_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E/<!-- $ENV{TEXT} -->/g' \
    "${target}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66.3 Shuffle sample execution RC proof"

missing_reference_repo="${workdir}/missing-reference"
copy_valid_repo "${missing_reference_repo}"
rm "${missing_reference_repo}/docs/deployment/shuffle-reviewed-workflow-template-contract.md"
assert_fails_with "${missing_reference_repo}" "Missing Phase 66.3 reference docs/deployment/shuffle-reviewed-workflow-template-contract.md"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 66\.3 Shuffle sample execution RC proof\]\(docs\/phase-66-3-shuffle-sample-execution-rc-proof\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical Phase 66.3 boundary bullet"

missing_authority_policy_baseline_repo="${workdir}/missing-authority-policy-baseline"
copy_valid_repo "${missing_authority_policy_baseline_repo}"
remove_doc_text "${missing_authority_policy_baseline_repo}" \
  "\`docs/phase-51-6-authority-boundary-negative-test-policy.md\`, "
assert_fails_with "${missing_authority_policy_baseline_repo}" "Missing required Phase 66.3 Shuffle sample execution proof term"

missing_action_request_row_repo="${workdir}/missing-action-request-row"
copy_valid_repo "${missing_action_request_row_repo}"
remove_doc_text "${missing_action_request_row_repo}" \
  "| \`action_request_id\` | AegisOps action request identifier for the delegated work. | Request text, ticket text, or workflow names cannot create action-request truth. |"
assert_fails_with "${missing_action_request_row_repo}" "Missing Phase 66.3 sample execution evidence field"

commented_receipt_row_repo="${workdir}/commented-receipt-row"
copy_valid_repo "${commented_receipt_row_repo}"
comment_doc_text "${commented_receipt_row_repo}" \
  "| \`execution_receipt_id\` | AegisOps normalized execution receipt linked to the Shuffle run. | Shuffle workflow success or callback payload alone cannot create execution receipt truth. |"
assert_fails_with "${commented_receipt_row_repo}" "Missing Phase 66.3 sample execution evidence field"

missing_delegation_term_repo="${workdir}/missing-delegation-term"
copy_valid_repo "${missing_delegation_term_repo}"
remove_doc_text "${missing_delegation_term_repo}" \
  "template identity, template version, owner, review status, correlation id, action request id, approval decision id, execution receipt id, normalized receipt reference, callback URL, callback secret reference, and idempotency key"
assert_fails_with "${missing_delegation_term_repo}" "Missing Phase 66.3 delegation, receipt, or reconciliation term"

missing_manual_fallback_citation_repo="${workdir}/missing-manual-fallback-citation"
copy_valid_repo "${missing_manual_fallback_citation_repo}"
remove_doc_text "${missing_manual_fallback_citation_repo}" \
  ", plus \`docs/deployment/shuffle-manual-fallback-contract.md\`"
assert_fails_with "${missing_manual_fallback_citation_repo}" "Missing Phase 66.3 delegation, receipt, or reconciliation term"

missing_manual_fallback_paths_repo="${workdir}/missing-manual-fallback-paths"
copy_valid_repo "${missing_manual_fallback_paths_repo}"
remove_doc_text "${missing_manual_fallback_paths_repo}" \
  " for unavailable, rejected, missing receipt, stale receipt, and mismatched receipt paths"
assert_fails_with "${missing_manual_fallback_paths_repo}" "Missing Phase 66.3 delegation, receipt, or reconciliation term"

missing_limitations_repo="${workdir}/missing-limitations"
copy_valid_repo "${missing_limitations_repo}"
remove_doc_text "${missing_limitations_repo}" \
  "It does not prove broad SOAR marketplace coverage, arbitrary connector import, autonomous remediation, Controlled Write readiness, Hard Write readiness, production customer workflow import, production automation authority, real design-partner success, Phase 66 closeout, Phase 67 GA readiness, or commercial replacement readiness."
assert_fails_with "${missing_limitations_repo}" "Missing Phase 66.3 accepted limitations boundary"

mutable_repository_revision_repo="${workdir}/mutable-repository-revision"
copy_valid_repo "${mutable_repository_revision_repo}"
printf '%s\n' "repository_revision: refs/remotes/origin/main" >>"${mutable_repository_revision_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${mutable_repository_revision_repo}" "mutable repository revision detected"

latest_repository_revision_repo="${workdir}/latest-repository-revision"
copy_valid_repo "${latest_repository_revision_repo}"
printf '%s\n' "repository_revision: latest" >>"${latest_repository_revision_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${latest_repository_revision_repo}" "non-immutable repository revision detected"

latest_repository_revision_table_repo="${workdir}/latest-repository-revision-table"
copy_valid_repo "${latest_repository_revision_table_repo}"
printf '%s\n' "| repository_revision | latest |" >>"${latest_repository_revision_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${latest_repository_revision_table_repo}" "non-immutable repository revision detected"

valid_repository_revision_repo="${workdir}/valid-repository-revision"
copy_valid_repo "${valid_repository_revision_repo}"
printf '%s\n' "repository_revision: 0123456789abcdef0123456789abcdef01234567" >>"${valid_repository_revision_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${valid_repository_revision_repo}"

invalid_shuffle_profile_repo="${workdir}/invalid-shuffle-profile"
copy_valid_repo "${invalid_shuffle_profile_repo}"
printf '%s\n' "shuffle_profile: enterprise-cluster" >>"${invalid_shuffle_profile_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${invalid_shuffle_profile_repo}" "invalid Shuffle profile detected"

invalid_shuffle_profile_table_repo="${workdir}/invalid-shuffle-profile-table"
copy_valid_repo "${invalid_shuffle_profile_table_repo}"
printf '%s\n' "| shuffle_profile | enterprise-cluster |" >>"${invalid_shuffle_profile_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${invalid_shuffle_profile_table_repo}" "invalid Shuffle profile detected"

valid_shuffle_profile_repo="${workdir}/valid-shuffle-profile"
copy_valid_repo "${valid_shuffle_profile_repo}"
printf '%s\n' "shuffle_profile: smb-single-node" >>"${valid_shuffle_profile_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${valid_shuffle_profile_repo}"

invalid_template_repo="${workdir}/invalid-template"
copy_valid_repo "${invalid_template_repo}"
printf '%s\n' "reviewed_template_id: unreviewed-notify-template" >>"${invalid_template_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${invalid_template_repo}" "invalid reviewed template detected"

not_reviewed_template_repo="${workdir}/not-reviewed-template"
copy_valid_repo "${not_reviewed_template_repo}"
printf '%s\n' "reviewed_template_id: not_reviewed" >>"${not_reviewed_template_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${not_reviewed_template_repo}" "invalid reviewed template detected"

unreviewed_template_table_repo="${workdir}/unreviewed-template-table"
copy_valid_repo "${unreviewed_template_table_repo}"
printf '%s\n' "| reviewed_template_id | unreviewed |" >>"${unreviewed_template_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${unreviewed_template_table_repo}" "invalid reviewed template detected"

direct_launch_repo="${workdir}/direct-launch"
copy_valid_repo "${direct_launch_repo}"
printf '%s\n' "direct_shuffle_launch: true" >>"${direct_launch_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${direct_launch_repo}" "bypass value detected"

direct_launch_table_repo="${workdir}/direct-launch-table"
copy_valid_repo "${direct_launch_table_repo}"
printf '%s\n' "| direct_shuffle_launch | true |" >>"${direct_launch_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${direct_launch_table_repo}" "bypass value detected"

approved_bypass_field_repo="${workdir}/approved-bypass-field"
copy_valid_repo "${approved_bypass_field_repo}"
printf '%s\n' "approval_bypass: accepted" >>"${approved_bypass_field_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${approved_bypass_field_repo}" "bypass value detected"

direct_launch_enabled_repo="${workdir}/direct-launch-enabled"
copy_valid_repo "${direct_launch_enabled_repo}"
printf '%s\n' "Direct Shuffle launch is enabled for this sample." >>"${direct_launch_enabled_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${direct_launch_enabled_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

raw_callback_binding_repo="${workdir}/raw-callback-binding"
copy_valid_repo "${raw_callback_binding_repo}"
printf '%s\n' "callback_binding_reference: raw_forwarded_headers" >>"${raw_callback_binding_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${raw_callback_binding_repo}" "invalid callback binding detected"

inferred_callback_binding_repo="${workdir}/inferred-callback-binding"
copy_valid_repo "${inferred_callback_binding_repo}"
printf '%s\n' "callback_binding_reference: inferred_callback_identity" >>"${inferred_callback_binding_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${inferred_callback_binding_repo}" "invalid callback binding detected"

raw_callback_binding_table_repo="${workdir}/raw-callback-binding-table"
copy_valid_repo "${raw_callback_binding_table_repo}"
printf '%s\n' "| callback_binding_reference | raw_forwarded_headers |" >>"${raw_callback_binding_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${raw_callback_binding_table_repo}" "invalid callback binding detected"

valid_callback_secret_reference_repo="${workdir}/valid-callback-secret-reference"
copy_valid_repo "${valid_callback_secret_reference_repo}"
printf '%s\n' "callback_secret_reference: vault/aegisops/shuffle-callback" >>"${valid_callback_secret_reference_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${valid_callback_secret_reference_repo}"

missing_callback_secret_reference_repo="${workdir}/missing-callback-secret-reference"
copy_valid_repo "${missing_callback_secret_reference_repo}"
printf '%s\n' "callback_secret_reference: missing" >>"${missing_callback_secret_reference_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${missing_callback_secret_reference_repo}" "missing required evidence value detected"

approval_bypass_repo="${workdir}/approval-bypass"
copy_valid_repo "${approval_bypass_repo}"
printf '%s\n' "Approval bypass is allowed for this Shuffle sample." >>"${approval_bypass_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${approval_bypass_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

approval_bypass_enabled_repo="${workdir}/approval-bypass-enabled"
copy_valid_repo "${approval_bypass_enabled_repo}"
printf '%s\n' "Approval bypass is enabled." >>"${approval_bypass_enabled_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${approval_bypass_enabled_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

missing_approval_repo="${workdir}/missing-approval"
copy_valid_repo "${missing_approval_repo}"
printf '%s\n' "approval_decision_id: missing" >>"${missing_approval_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${missing_approval_repo}" "missing required evidence value detected"

omitted_action_request_repo="${workdir}/omitted-action-request"
copy_valid_repo "${omitted_action_request_repo}"
printf '%s\n' "action_request_id: omitted" >>"${omitted_action_request_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${omitted_action_request_repo}" "missing required evidence value detected"

missing_approval_table_repo="${workdir}/missing-approval-table"
copy_valid_repo "${missing_approval_table_repo}"
printf '%s\n' "| approval_decision_id | missing |" >>"${missing_approval_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${missing_approval_table_repo}" "missing required evidence value detected"

missing_receipt_repo="${workdir}/missing-receipt"
copy_valid_repo "${missing_receipt_repo}"
printf '%s\n' "execution_receipt_id: missing" >>"${missing_receipt_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${missing_receipt_repo}" "missing required evidence value detected"

mismatched_journey_run_repo="${workdir}/mismatched-journey-run"
copy_valid_repo "${mismatched_journey_run_repo}"
printf '%s\n' "journey_run_id: mismatched" >>"${mismatched_journey_run_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${mismatched_journey_run_repo}" "missing required evidence value detected"

hidden_limitation_repo="${workdir}/hidden-limitation"
copy_valid_repo "${hidden_limitation_repo}"
printf '%s\n' "limitation_references: hidden in Shuffle execution text" >>"${hidden_limitation_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${hidden_limitation_repo}" "hidden limitation references detected"

hidden_limitation_table_repo="${workdir}/hidden-limitation-table"
copy_valid_repo "${hidden_limitation_table_repo}"
printf '%s\n' "| limitation_references | hidden in Shuffle execution text | reviewed |" >>"${hidden_limitation_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${hidden_limitation_table_repo}" "hidden limitation references detected"

underscored_hidden_limitation_repo="${workdir}/underscored-hidden-limitation"
copy_valid_repo "${underscored_hidden_limitation_repo}"
printf '%s\n' "limitation_references: hidden_in_shuffle_execution_text" >>"${underscored_hidden_limitation_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${underscored_hidden_limitation_repo}" "hidden limitation references detected"

direct_launch_delegation_repo="${workdir}/direct-launch-delegation"
copy_valid_repo "${direct_launch_delegation_repo}"
printf '%s\n' "delegation_payload_reference: direct_shuffle_launch" >>"${direct_launch_delegation_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${direct_launch_delegation_repo}" "invalid delegation payload detected"

direct_launch_delegation_table_repo="${workdir}/direct-launch-delegation-table"
copy_valid_repo "${direct_launch_delegation_table_repo}"
printf '%s\n' "| delegation_payload_reference | direct_shuffle_launch |" >>"${direct_launch_delegation_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${direct_launch_delegation_table_repo}" "invalid delegation payload detected"

shuffle_reconciliation_truth_repo="${workdir}/shuffle-reconciliation-truth"
copy_valid_repo "${shuffle_reconciliation_truth_repo}"
printf '%s\n' "Shuffle workflow success is AegisOps reconciliation truth." >>"${shuffle_reconciliation_truth_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_reconciliation_truth_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

shuffle_source_admission_truth_repo="${workdir}/shuffle-source-admission-truth"
copy_valid_repo "${shuffle_source_admission_truth_repo}"
printf '%s\n' "Shuffle is source admission truth." >>"${shuffle_source_admission_truth_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_source_admission_truth_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

shuffle_source_of_truth_repo="${workdir}/shuffle-source-of-truth"
copy_valid_repo "${shuffle_source_of_truth_repo}"
printf '%s\n' "Shuffle is approval source of truth." >>"${shuffle_source_of_truth_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_source_of_truth_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

shuffle_workflow_authority_repo="${workdir}/shuffle-workflow-authority"
copy_valid_repo "${shuffle_workflow_authority_repo}"
printf '%s\n' "Shuffle is workflow authority." >>"${shuffle_workflow_authority_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_workflow_authority_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

shuffle_executes_records_repo="${workdir}/shuffle-executes-records"
copy_valid_repo "${shuffle_executes_records_repo}"
printf '%s\n' "Shuffle executes AegisOps records after approval." >>"${shuffle_executes_records_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_executes_records_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

passive_shuffle_authority_repo="${workdir}/passive-shuffle-authority"
copy_valid_repo "${passive_shuffle_authority_repo}"
printf '%s\n' "AegisOps records are approved by Shuffle workflow success." >>"${passive_shuffle_authority_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${passive_shuffle_authority_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

optional_evidence_approves_records_repo="${workdir}/optional-evidence-approves-records"
copy_valid_repo "${optional_evidence_approves_records_repo}"
printf '%s\n' "Optional evidence approves AegisOps records." >>"${optional_evidence_approves_records_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${optional_evidence_approves_records_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

negation_bypass_authority_repo="${workdir}/negation-bypass-authority"
copy_valid_repo "${negation_bypass_authority_repo}"
printf '%s\n' "If callback cannot be verified, Shuffle approves AegisOps records." >>"${negation_bypass_authority_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${negation_bypass_authority_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

shuffle_cannot_but_executes_repo="${workdir}/shuffle-cannot-but-executes"
copy_valid_repo "${shuffle_cannot_but_executes_repo}"
printf '%s\n' "Shuffle cannot approve AegisOps records but does execute AegisOps records." >>"${shuffle_cannot_but_executes_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_cannot_but_executes_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

callback_receipt_shortcut_repo="${workdir}/callback-receipt-shortcut"
copy_valid_repo "${callback_receipt_shortcut_repo}"
printf '%s\n' "Callback payload creates execution receipt truth." >>"${callback_receipt_shortcut_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${callback_receipt_shortcut_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

callback_receipt_field_repo="${workdir}/callback-receipt-field"
copy_valid_repo "${callback_receipt_field_repo}"
printf '%s\n' "execution_receipt_id: callback_payload" >>"${callback_receipt_field_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${callback_receipt_field_repo}" "invalid execution receipt detected"

callback_receipt_wide_table_repo="${workdir}/callback-receipt-wide-table"
copy_valid_repo "${callback_receipt_wide_table_repo}"
printf '%s\n' "| execution_receipt_id | callback_payload | reviewed |" >>"${callback_receipt_wide_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${callback_receipt_wide_table_repo}" "invalid execution receipt detected"

shuffle_success_reconciliation_field_repo="${workdir}/shuffle-success-reconciliation-field"
copy_valid_repo "${shuffle_success_reconciliation_field_repo}"
printf '%s\n' "reconciliation_review_id: shuffle_success" >>"${shuffle_success_reconciliation_field_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_success_reconciliation_field_repo}" "invalid reconciliation review detected"

workflow_name_approval_repo="${workdir}/workflow-name-approval"
copy_valid_repo "${workflow_name_approval_repo}"
printf '%s\n' "Workflow names imply approval decision binding." >>"${workflow_name_approval_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${workflow_name_approval_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

ticket_text_action_request_field_repo="${workdir}/ticket-text-action-request-field"
copy_valid_repo "${ticket_text_action_request_field_repo}"
printf '%s\n' "action_request_id: ticket_text" >>"${ticket_text_action_request_field_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${ticket_text_action_request_field_repo}" "invalid action request detected"

ticket_text_action_request_table_repo="${workdir}/ticket-text-action-request-table"
copy_valid_repo "${ticket_text_action_request_table_repo}"
printf '%s\n' "| action_request_id | ticket_text |" >>"${ticket_text_action_request_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${ticket_text_action_request_table_repo}" "invalid action request detected"

comments_infer_approval_repo="${workdir}/comments-infer-approval"
copy_valid_repo "${comments_infer_approval_repo}"
printf '%s\n' "Comments infer approval decision binding." >>"${comments_infer_approval_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${comments_infer_approval_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

shuffle_state_approval_field_repo="${workdir}/shuffle-state-approval-field"
copy_valid_repo "${shuffle_state_approval_field_repo}"
printf '%s\n' "approval_decision_id: shuffle_state" >>"${shuffle_state_approval_field_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${shuffle_state_approval_field_repo}" "invalid approval decision detected"

ga_ready_repo="${workdir}/ga-ready"
copy_valid_repo "${ga_ready_repo}"
printf '%s\n' "Phase 66.3 proves GA readiness." >>"${ga_ready_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${ga_ready_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

ga_adjectival_ready_repo="${workdir}/ga-adjectival-ready"
copy_valid_repo "${ga_adjectival_ready_repo}"
printf '%s\n' "Phase 66.3 is GA ready." >>"${ga_adjectival_ready_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${ga_adjectival_ready_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

phase_achieves_ga_repo="${workdir}/phase-achieves-ga"
copy_valid_repo "${phase_achieves_ga_repo}"
printf '%s\n' "Phase 66.3 achieves GA readiness." >>"${phase_achieves_ga_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${phase_achieves_ga_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

phase_validates_ga_repo="${workdir}/phase-validates-ga"
copy_valid_repo "${phase_validates_ga_repo}"
printf '%s\n' "Phase 66.3 validates GA readiness." >>"${phase_validates_ga_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${phase_validates_ga_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

phase_enables_controlled_write_repo="${workdir}/phase-enables-controlled-write"
copy_valid_repo "${phase_enables_controlled_write_repo}"
printf '%s\n' "Phase 66.3 enables Controlled Write." >>"${phase_enables_controlled_write_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${phase_enables_controlled_write_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

commercial_replacement_ready_repo="${workdir}/commercial-replacement-ready"
copy_valid_repo "${commercial_replacement_ready_repo}"
printf '%s\n' "Phase 66.3 is commercial replacement ready." >>"${commercial_replacement_ready_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${commercial_replacement_ready_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

readme_ga_ready_repo="${workdir}/readme-ga-ready"
copy_valid_repo "${readme_ga_ready_repo}"
printf '%s\n' "Phase 66.3 proves GA readiness." >>"${readme_ga_ready_repo}/README.md"
assert_fails_with "${readme_ga_ready_repo}" "Forbidden Phase 66.3 README claim matched"

readme_shuffle_sample_ga_ready_repo="${workdir}/readme-shuffle-sample-ga-ready"
copy_valid_repo "${readme_shuffle_sample_ga_ready_repo}"
printf '%s\n' "The Shuffle sample execution RC proof proves GA readiness." >>"${readme_shuffle_sample_ga_ready_repo}/README.md"
assert_fails_with "${readme_shuffle_sample_ga_ready_repo}" "Forbidden Phase 66.3 README claim matched"

rc_pass_repo="${workdir}/rc-pass"
copy_valid_repo "${rc_pass_repo}"
printf '%s\n' "Phase 66.3 passes RC." >>"${rc_pass_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${rc_pass_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

broad_soar_repo="${workdir}/broad-soar"
copy_valid_repo "${broad_soar_repo}"
printf '%s\n' "The proof achieves broad SOAR marketplace coverage." >>"${broad_soar_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${broad_soar_repo}" "Forbidden Phase 66.3 Shuffle sample execution RC proof claim matched"

safe_limitation_repo="${workdir}/safe-limitation"
copy_valid_repo "${safe_limitation_repo}"
printf '%s\n' "Phase 66.3 confirms production automation remains out of scope." >>"${safe_limitation_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${safe_limitation_repo}"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "api_key: abcdefghijklmnop" >>"${secret_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${secret_repo}" "production secret-looking value detected"

basic_authorization_repo="${workdir}/basic-authorization"
copy_valid_repo "${basic_authorization_repo}"
printf '%s\n' "Authorization: Basic dXNlcjpwYXNzd29yZA==" >>"${basic_authorization_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${basic_authorization_repo}" "production secret-looking value detected"

aws_secret_access_key_repo="${workdir}/aws-secret-access-key"
copy_valid_repo "${aws_secret_access_key_repo}"
printf '%s\n' "aws_secret_access_key: wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" >>"${aws_secret_access_key_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${aws_secret_access_key_repo}" "production secret-looking value detected"

api_key_table_repo="${workdir}/api-key-table"
copy_valid_repo "${api_key_table_repo}"
printf '%s\n' "| api_key | abcdefghijklmnop |" >>"${api_key_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${api_key_table_repo}" "production secret-looking value detected"

customer_private_repo="${workdir}/customer-private"
copy_valid_repo "${customer_private_repo}"
printf '%s\n' "The proof includes customer-private ticket export." >>"${customer_private_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

customer_private_assignment_repo="${workdir}/customer-private-assignment"
copy_valid_repo "${customer_private_assignment_repo}"
printf '%s\n' "customer_private_data: exported-ticket" >>"${customer_private_assignment_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${customer_private_assignment_repo}" "customer-private data detected"

customer_private_table_repo="${workdir}/customer-private-table"
copy_valid_repo "${customer_private_table_repo}"
printf '%s\n' "| customer_private_data | exported-ticket |" >>"${customer_private_table_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${customer_private_table_repo}" "customer-private data detected"

customer_private_unrelated_negation_repo="${workdir}/customer-private-unrelated-negation"
copy_valid_repo "${customer_private_unrelated_negation_repo}"
printf '%s\n' "The proof must not include placeholder screenshots, but includes customer-private ticket export." >>"${customer_private_unrelated_negation_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_fails_with "${customer_private_unrelated_negation_repo}" "customer-private data detected"

customer_private_prohibition_repo="${workdir}/customer-private-prohibition"
copy_valid_repo "${customer_private_prohibition_repo}"
printf '%s\n' "The proof must not include customer-private ticket export." >>"${customer_private_prohibition_repo}/docs/phase-66-3-shuffle-sample-execution-rc-proof.md"
assert_passes "${customer_private_prohibition_repo}"

echo "Phase 66.3 Shuffle sample execution RC proof verifier self-test passed."
