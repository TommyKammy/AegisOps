#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

copy_repo_path() {
  local target="$1"
  local path="$2"

  mkdir -p "${target}/$(dirname "${path}")"
  cp -R "${repo_root}/${path}" "${target}/${path}"
}

copy_valid_repo() {
  local target="$1"

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/phase-66-5-report-export-rc-proof.md"
  copy_repo_path "${target}" "docs/phase-66-1-clean-host-rc-e2e-harness.md"
  copy_repo_path "${target}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  copy_repo_path "${target}" "docs/phase-51-6-authority-boundary-negative-test-policy.md"
  copy_repo_path "${target}" "docs/getting-started/first-user-demo-report-export.md"
  copy_repo_path "${target}" "docs/phase-49-5-pilot-reporting-executive-summary-export-validation.md"
  copy_repo_path "${target}" "docs/phase-65-closeout-evaluation.md"
  copy_repo_path "${target}" "scripts/verify-phase-66-5-report-export-rc-proof.sh"
  copy_repo_path "${target}" "scripts/test-verify-phase-66-5-report-export-rc-proof.sh"
  copy_repo_path "${target}" "scripts/verify-phase-51-6-authority-boundary-negative-test-policy.sh"
  copy_repo_path "${target}" "scripts/verify-publishable-path-hygiene.sh"
}

assert_passes() {
  local target="$1"

  PHASE66_5_SKIP_PATH_HYGIENE=1 bash "${target}/scripts/verify-phase-66-5-report-export-rc-proof.sh" "${target}" >/tmp/phase66_5_pass.out 2>/tmp/phase66_5_pass.err || {
    cat /tmp/phase66_5_pass.err >&2
    exit 1
  }
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if PHASE66_5_SKIP_PATH_HYGIENE=1 bash "${target}/scripts/verify-phase-66-5-report-export-rc-proof.sh" "${target}" >/tmp/phase66_5_fail.out 2>/tmp/phase66_5_fail.err; then
    echo "Expected Phase 66.5 verifier failure containing: ${expected}" >&2
    exit 1
  fi
  if ! grep -Fq -- "${expected}" /tmp/phase66_5_fail.err; then
    echo "Missing expected Phase 66.5 verifier failure: ${expected}" >&2
    cat /tmp/phase66_5_fail.err >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
copy_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

valid_explicit_labels_repo="${workdir}/valid-explicit-labels"
copy_valid_repo "${valid_explicit_labels_repo}"
printf '%s\n' "rc_label_set: rc-evidence phase-66 report-export not-workflow-truth" >>"${valid_explicit_labels_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_explicit_labels_repo}"

valid_redacted_credentials_repo="${workdir}/valid-redacted-credentials"
copy_valid_repo "${valid_redacted_credentials_repo}"
printf '%s\n' "redaction_posture: token: redacted" >>"${valid_redacted_credentials_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "password: redacted" >>"${valid_redacted_credentials_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_redacted_credentials_repo}"

valid_customer_private_redaction_repo="${workdir}/valid-customer-private-redaction"
copy_valid_repo "${valid_customer_private_redaction_repo}"
printf '%s\n' "redaction_posture: customer-private data redacted" >>"${valid_customer_private_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_customer_private_redaction_repo}"

mixed_redacted_and_secret_repo="${workdir}/mixed-redacted-and-secret"
copy_valid_repo "${mixed_redacted_and_secret_repo}"
printf '%s\n' "token: redacted api_key: abcdefghijklmnop" >>"${mixed_redacted_and_secret_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${mixed_redacted_and_secret_repo}" "production secret-looking value detected"

missing_doc_repo="${workdir}/missing-doc"
copy_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 66.5 report export RC proof"

missing_readme_repo="${workdir}/missing-readme"
copy_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 66\.5 report export RC proof\][^\n]*\n//' "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical Phase 66.5 boundary bullet"

missing_row_repo="${workdir}/missing-row"
copy_valid_repo "${missing_row_repo}"
perl -0pi -e 's/^\| `redaction_posture` \|[^\n]*\n//m' "${missing_row_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_row_repo}" "Phase 66.5 report export evidence field"

missing_required_repo="${workdir}/missing-required"
copy_valid_repo "${missing_required_repo}"
printf '%s\n' "report_export_id: missing because export failed" >>"${missing_required_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_required_repo}" "missing required evidence value detected"

missing_required_late_repo="${workdir}/missing-required-late"
copy_valid_repo "${missing_required_late_repo}"
printf '%s\n' "report_export_id: export unavailable" >>"${missing_required_late_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_required_late_repo}" "missing required evidence value detected"

empty_required_assignment_repo="${workdir}/empty-required-assignment"
copy_valid_repo "${empty_required_assignment_repo}"
printf '%s\n' "report_export_id:" >>"${empty_required_assignment_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${empty_required_assignment_repo}" "missing required evidence value detected"

empty_source_record_assignment_repo="${workdir}/empty-source-record-assignment"
copy_valid_repo "${empty_source_record_assignment_repo}"
printf '%s\n' "source_record_references:" >>"${empty_source_record_assignment_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${empty_source_record_assignment_repo}" "missing required evidence value detected"

empty_required_table_cell_repo="${workdir}/empty-required-table-cell"
copy_valid_repo "${empty_required_table_cell_repo}"
printf '%s\n' "| report_export_id | |" >>"${empty_required_table_cell_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${empty_required_table_cell_repo}" "missing required evidence value detected"

missing_required_extra_table_cell_repo="${workdir}/missing-required-extra-table-cell"
copy_valid_repo "${missing_required_extra_table_cell_repo}"
printf '%s\n' "| report_export_id | EXP-1 | missing timestamp |" >>"${missing_required_extra_table_cell_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_required_extra_table_cell_repo}" "missing required evidence value detected"

unavailable_required_repo="${workdir}/unavailable-required"
copy_valid_repo "${unavailable_required_repo}"
printf '%s\n' "report_export_id: unavailable" >>"${unavailable_required_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${unavailable_required_repo}" "missing required evidence value detected"

hidden_limitation_repo="${workdir}/hidden-limitation"
copy_valid_repo "${hidden_limitation_repo}"
printf '%s\n' "limitation_references: hidden in report text" >>"${hidden_limitation_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hidden_limitation_repo}" "missing required evidence value detected"

hidden_limitation_extra_table_cell_repo="${workdir}/hidden-limitation-extra-table-cell"
copy_valid_repo "${hidden_limitation_extra_table_cell_repo}"
printf '%s\n' "| limitation_references | LIM-1 | hidden in report text |" >>"${hidden_limitation_extra_table_cell_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hidden_limitation_extra_table_cell_repo}" "missing required evidence value detected"

mutable_revision_repo="${workdir}/mutable-revision"
copy_valid_repo "${mutable_revision_repo}"
printf '%s\n' "repository_revision: origin/main" >>"${mutable_revision_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${mutable_revision_repo}" "mutable repository revision detected"

hash_with_branch_repo="${workdir}/hash-with-branch"
copy_valid_repo "${hash_with_branch_repo}"
printf '%s\n' "repository_revision: 0123456789abcdef0123456789abcdef01234567 on origin/main" >>"${hash_with_branch_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hash_with_branch_repo}" "mutable repository revision detected"

table_hash_with_branch_repo="${workdir}/table-hash-with-branch"
copy_valid_repo "${table_hash_with_branch_repo}"
printf '%s\n' "| repository_revision | 0123456789abcdef0123456789abcdef01234567 | origin/main |" >>"${table_hash_with_branch_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${table_hash_with_branch_repo}" "mutable repository revision detected"

source_record_shortcut_repo="${workdir}/source-record-shortcut"
copy_valid_repo "${source_record_shortcut_repo}"
printf '%s\n' "source_record_references: report text" >>"${source_record_shortcut_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_shortcut_repo}" "invalid source record reference detected"

source_record_report_output_repo="${workdir}/source-record-report-output"
copy_valid_repo "${source_record_report_output_repo}"
printf '%s\n' "source_record_references: report output" >>"${source_record_report_output_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_report_output_repo}" "invalid source record reference detected"

source_record_generated_file_repo="${workdir}/source-record-generated-file"
copy_valid_repo "${source_record_generated_file_repo}"
printf '%s\n' "source_record_references: generated file" >>"${source_record_generated_file_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_generated_file_repo}" "invalid source record reference detected"

source_record_downloaded_artifact_repo="${workdir}/source-record-downloaded-artifact"
copy_valid_repo "${source_record_downloaded_artifact_repo}"
printf '%s\n' "| source_record_references | downloaded artifact |" >>"${source_record_downloaded_artifact_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_downloaded_artifact_repo}" "invalid source record reference detected"

source_record_report_metadata_repo="${workdir}/source-record-report-metadata"
copy_valid_repo "${source_record_report_metadata_repo}"
printf '%s\n' "source_record_references: report metadata" >>"${source_record_report_metadata_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_report_metadata_repo}" "invalid source record reference detected"

source_record_report_labels_repo="${workdir}/source-record-report-labels"
copy_valid_repo "${source_record_report_labels_repo}"
printf '%s\n' "source_record_references: report labels" >>"${source_record_report_labels_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_report_labels_repo}" "invalid source record reference detected"

source_record_report_artifact_repo="${workdir}/source-record-report-artifact"
copy_valid_repo "${source_record_report_artifact_repo}"
printf '%s\n' "source_record_references: report artifact" >>"${source_record_report_artifact_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_report_artifact_repo}" "invalid source record reference detected"

source_record_extra_table_cell_repo="${workdir}/source-record-extra-table-cell"
copy_valid_repo "${source_record_extra_table_cell_repo}"
printf '%s\n' "| source_record_references | CASE-1 | report metadata |" >>"${source_record_extra_table_cell_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_extra_table_cell_repo}" "invalid source record reference detected"

valid_section_record_references_repo="${workdir}/valid-section-record-references"
copy_valid_repo "${valid_section_record_references_repo}"
printf '%s\n' "action_section_reference: approval record APR-1, execution receipt REC-1" >>"${valid_section_record_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "reconciliation_section_reference: reconciliation section REC-1" >>"${valid_section_record_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_section_record_references_repo}"

section_authority_repo="${workdir}/section-authority"
copy_valid_repo "${section_authority_repo}"
printf '%s\n' "case_section_reference: case closed by report" >>"${section_authority_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${section_authority_repo}" "report section authority detected"

section_authority_canonical_prefix_repo="${workdir}/section-authority-canonical-prefix"
copy_valid_repo "${section_authority_canonical_prefix_repo}"
printf '%s\n' "| case_section_reference | Reviewed case section closed by report | invalid |" >>"${section_authority_canonical_prefix_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${section_authority_canonical_prefix_repo}" "report section authority detected"

section_authority_noun_repo="${workdir}/section-authority-noun"
copy_valid_repo "${section_authority_noun_repo}"
printf '%s\n' "action_section_reference: approval via report" >>"${section_authority_noun_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${section_authority_noun_repo}" "report section authority detected"

section_closure_noun_repo="${workdir}/section-closure-noun"
copy_valid_repo "${section_closure_noun_repo}"
printf '%s\n' "case_section_reference: case closure via report" >>"${section_closure_noun_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${section_closure_noun_repo}" "report section authority detected"

section_authority_extra_table_cell_repo="${workdir}/section-authority-extra-table-cell"
copy_valid_repo "${section_authority_extra_table_cell_repo}"
printf '%s\n' "| case_section_reference | reviewed case section | case closure via report |" >>"${section_authority_extra_table_cell_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${section_authority_extra_table_cell_repo}" "report section authority detected"

missing_labels_repo="${workdir}/missing-labels"
copy_valid_repo "${missing_labels_repo}"
printf '%s\n' "rc_label_set: without labels" >>"${missing_labels_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_labels_repo}" "invalid RC label set detected"

incomplete_labels_repo="${workdir}/incomplete-labels"
copy_valid_repo "${incomplete_labels_repo}"
printf '%s\n' "rc_label_set: rc-evidence phase-66 report-export only" >>"${incomplete_labels_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${incomplete_labels_repo}" "invalid RC label set detected"

workflow_truth_label_repo="${workdir}/workflow-truth-label"
copy_valid_repo "${workflow_truth_label_repo}"
printf '%s\n' "rc_label_set: rc-evidence phase-66 report-export not-workflow-truth workflow-truth" >>"${workflow_truth_label_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${workflow_truth_label_repo}" "invalid RC label set detected"

production_truth_extra_table_cell_label_repo="${workdir}/production-truth-extra-table-cell-label"
copy_valid_repo "${production_truth_extra_table_cell_label_repo}"
printf '%s\n' "| rc_label_set | rc-evidence phase-66 report-export not-workflow-truth | production-truth |" >>"${production_truth_extra_table_cell_label_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${production_truth_extra_table_cell_label_repo}" "invalid RC label set detected"

bad_redaction_repo="${workdir}/bad-redaction"
copy_valid_repo "${bad_redaction_repo}"
printf '%s\n' "redaction_posture: not_needed" >>"${bad_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${bad_redaction_repo}" "invalid redaction posture detected"

raw_secret_redaction_repo="${workdir}/raw-secret-redaction"
copy_valid_repo "${raw_secret_redaction_repo}"
printf '%s\n' "redaction_posture: raw secrets included" >>"${raw_secret_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${raw_secret_redaction_repo}" "invalid redaction posture detected"

customer_private_redaction_repo="${workdir}/customer-private-redaction"
copy_valid_repo "${customer_private_redaction_repo}"
printf '%s\n' "redaction_posture: customer-private payloads" >>"${customer_private_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${customer_private_redaction_repo}" "invalid redaction posture detected"

workstation_local_redaction_repo="${workdir}/workstation-local-redaction"
copy_valid_repo "${workstation_local_redaction_repo}"
printf '%s\n' "redaction_posture: workstation-local paths included" >>"${workstation_local_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${workstation_local_redaction_repo}" "invalid redaction posture detected"

redaction_extra_table_cell_repo="${workdir}/redaction-extra-table-cell"
copy_valid_repo "${redaction_extra_table_cell_repo}"
printf '%s\n' "| redaction_posture | reviewed | raw secrets included |" >>"${redaction_extra_table_cell_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${redaction_extra_table_cell_repo}" "invalid redaction posture detected"

report_truth_repo="${workdir}/report-truth"
copy_valid_repo "${report_truth_repo}"
printf '%s\n' "Report output is workflow truth." >>"${report_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

ui_state_truth_repo="${workdir}/ui-state-truth"
copy_valid_repo "${ui_state_truth_repo}"
printf '%s\n' "UI state is workflow truth." >>"${ui_state_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${ui_state_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_evidence_truth_repo="${workdir}/report-evidence-truth"
copy_valid_repo "${report_evidence_truth_repo}"
printf '%s\n' "Report output is evidence truth." >>"${report_evidence_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_evidence_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_source_of_truth_repo="${workdir}/report-source-of-truth"
copy_valid_repo "${report_source_of_truth_repo}"
printf '%s\n' "Report output is source of truth for case closure." >>"${report_source_of_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_source_of_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_creates_source_truth_repo="${workdir}/report-creates-source-truth"
copy_valid_repo "${report_creates_source_truth_repo}"
printf '%s\n' "Report output creates source-record truth." >>"${report_creates_source_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_creates_source_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_creates_workflow_truth_repo="${workdir}/report-creates-workflow-truth"
copy_valid_repo "${report_creates_workflow_truth_repo}"
printf '%s\n' "Report output creates workflow truth." >>"${report_creates_workflow_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_creates_workflow_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_export_ga_ready_repo="${workdir}/report-export-ga-ready"
copy_valid_repo "${report_export_ga_ready_repo}"
printf '%s\n' "Report export is GA ready." >>"${report_export_ga_ready_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_export_ga_ready_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_export_proves_ga_repo="${workdir}/report-export-proves-ga"
copy_valid_repo "${report_export_proves_ga_repo}"
printf '%s\n' "The report export proves GA readiness." >>"${report_export_proves_ga_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_export_proves_ga_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_export_sla_repo="${workdir}/report-export-sla"
copy_valid_repo "${report_export_sla_repo}"
printf '%s\n' "The report export confirms production SLA reporting." >>"${report_export_sla_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_export_sla_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_closes_case_repo="${workdir}/report-closes-case"
copy_valid_repo "${report_closes_case_repo}"
printf '%s\n' "Report output closes cases." >>"${report_closes_case_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_closes_case_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_authorizes_action_repo="${workdir}/report-authorizes-action"
copy_valid_repo "${report_authorizes_action_repo}"
printf '%s\n' "Report output authorizes action requests." >>"${report_authorizes_action_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_authorizes_action_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_determines_reconciliation_repo="${workdir}/report-determines-reconciliation"
copy_valid_repo "${report_determines_reconciliation_repo}"
printf '%s\n' "Report output determines reconciliation." >>"${report_determines_reconciliation_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_determines_reconciliation_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_report_closes_case_repo="${workdir}/passive-report-closes-case"
copy_valid_repo "${passive_report_closes_case_repo}"
printf '%s\n' "Cases are closed by report output." >>"${passive_report_closes_case_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_report_closes_case_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

completed_passive_report_closes_case_repo="${workdir}/completed-passive-report-closes-case"
copy_valid_repo "${completed_passive_report_closes_case_repo}"
printf '%s\n' "Cases have been closed by report output." >>"${completed_passive_report_closes_case_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${completed_passive_report_closes_case_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

table_report_truth_repo="${workdir}/table-report-truth"
copy_valid_repo "${table_report_truth_repo}"
printf '%s\n' "| note | Report output is workflow truth. |" >>"${table_report_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${table_report_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_approved_action_repo="${workdir}/report-approved-action"
copy_valid_repo "${report_approved_action_repo}"
printf '%s\n' "Report output approved action requests." >>"${report_approved_action_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_approved_action_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_authoritative_repo="${workdir}/report-authoritative"
copy_valid_repo "${report_authoritative_repo}"
printf '%s\n' "Report output is authoritative for cases." >>"${report_authoritative_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_authoritative_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_workflow_authority_repo="${workdir}/report-workflow-authority"
copy_valid_repo "${report_workflow_authority_repo}"
printf '%s\n' "Report output is workflow authority." >>"${report_workflow_authority_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_workflow_authority_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_approval_authority_repo="${workdir}/report-approval-authority"
copy_valid_repo "${report_approval_authority_repo}"
printf '%s\n' "Report output is approval authority." >>"${report_approval_authority_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_approval_authority_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_authority_for_cases_repo="${workdir}/report-authority-for-cases"
copy_valid_repo "${report_authority_for_cases_repo}"
printf '%s\n' "Report output is the authority for cases." >>"${report_authority_for_cases_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_authority_for_cases_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_case_closure_repo="${workdir}/report-case-closure"
copy_valid_repo "${report_case_closure_repo}"
printf '%s\n' "Report output is case closure." >>"${report_case_closure_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_case_closure_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_action_execution_repo="${workdir}/report-action-execution"
copy_valid_repo "${report_action_execution_repo}"
printf '%s\n' "Report output is action execution." >>"${report_action_execution_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_action_execution_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_override_repo="${workdir}/report-override"
copy_valid_repo "${report_override_repo}"
printf '%s\n' "Report sections override case records." >>"${report_override_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_override_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

cannot_semicolon_bypass_repo="${workdir}/cannot-semicolon-bypass"
copy_valid_repo "${cannot_semicolon_bypass_repo}"
printf '%s\n' "Report output cannot be ignored; report output is workflow truth." >>"${cannot_semicolon_bypass_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${cannot_semicolon_bypass_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

cannot_and_bypass_repo="${workdir}/cannot-and-bypass"
copy_valid_repo "${cannot_and_bypass_repo}"
printf '%s\n' "Report output cannot be ignored and is workflow truth." >>"${cannot_and_bypass_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${cannot_and_bypass_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

cannot_comma_bypass_repo="${workdir}/cannot-comma-bypass"
copy_valid_repo "${cannot_comma_bypass_repo}"
printf '%s\n' "Report output cannot be ignored, closes cases." >>"${cannot_comma_bypass_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${cannot_comma_bypass_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

safe_second_sentence_bypass_repo="${workdir}/safe-second-sentence-bypass"
copy_valid_repo "${safe_second_sentence_bypass_repo}"
printf '%s\n' "Report output is workflow truth. It cannot be ignored." >>"${safe_second_sentence_bypass_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${safe_second_sentence_bypass_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

safe_phrase_and_bypass_repo="${workdir}/safe-phrase-and-bypass"
copy_valid_repo "${safe_phrase_and_bypass_repo}"
printf '%s\n' "AegisOps records remain authoritative and report output is workflow truth." >>"${safe_phrase_and_bypass_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${safe_phrase_and_bypass_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

does_not_prove_and_bypass_repo="${workdir}/does-not-prove-and-bypass"
copy_valid_repo "${does_not_prove_and_bypass_repo}"
printf '%s\n' "This proof does not prove GA readiness and is GA ready." >>"${does_not_prove_and_bypass_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${does_not_prove_and_bypass_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

rc_overclaim_repo="${workdir}/rc-overclaim"
copy_valid_repo "${rc_overclaim_repo}"
printf '%s\n' "Phase 66.5 proves release-candidate readiness." >>"${rc_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${rc_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

proof_rc_overclaim_repo="${workdir}/proof-rc-overclaim"
copy_valid_repo "${proof_rc_overclaim_repo}"
printf '%s\n' "This proof passes RC." >>"${proof_rc_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${proof_rc_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

ga_overclaim_repo="${workdir}/ga-overclaim"
copy_valid_repo "${ga_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms GA readiness." >>"${ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

proof_ga_overclaim_repo="${workdir}/proof-ga-overclaim"
copy_valid_repo "${proof_ga_overclaim_repo}"
printf '%s\n' "This proof proves GA readiness." >>"${proof_ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${proof_ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

verifier_ga_overclaim_repo="${workdir}/verifier-ga-overclaim"
copy_valid_repo "${verifier_ga_overclaim_repo}"
printf '%s\n' "Verifier output confirms GA readiness." >>"${verifier_ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${verifier_ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

issue_lint_ga_overclaim_repo="${workdir}/issue-lint-ga-overclaim"
copy_valid_repo "${issue_lint_ga_overclaim_repo}"
printf '%s\n' "Issue-lint output confirms GA readiness." >>"${issue_lint_ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${issue_lint_ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

verifier_readiness_truth_validate_repo="${workdir}/verifier-readiness-truth-validate"
copy_valid_repo "${verifier_readiness_truth_validate_repo}"
printf '%s\n' "Verifier output validates readiness truth." >>"${verifier_readiness_truth_validate_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${verifier_readiness_truth_validate_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

issue_lint_readiness_truth_validate_repo="${workdir}/issue-lint-readiness-truth-validate"
copy_valid_repo "${issue_lint_readiness_truth_validate_repo}"
printf '%s\n' "Issue-lint output validates readiness truth." >>"${issue_lint_readiness_truth_validate_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${issue_lint_readiness_truth_validate_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

compliance_overclaim_repo="${workdir}/compliance-overclaim"
copy_valid_repo "${compliance_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms compliance certification." >>"${compliance_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${compliance_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

authorizes_rc_overclaim_repo="${workdir}/authorizes-rc-overclaim"
copy_valid_repo "${authorizes_rc_overclaim_repo}"
printf '%s\n' "Phase 66.5 authorizes RC pass." >>"${authorizes_rc_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${authorizes_rc_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

establishes_ga_overclaim_repo="${workdir}/establishes-ga-overclaim"
copy_valid_repo "${establishes_ga_overclaim_repo}"
printf '%s\n' "Phase 66.5 establishes GA readiness." >>"${establishes_ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${establishes_ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

guarantees_compliance_overclaim_repo="${workdir}/guarantees-compliance-overclaim"
copy_valid_repo "${guarantees_compliance_overclaim_repo}"
printf '%s\n' "Phase 66.5 guarantees compliance certification." >>"${guarantees_compliance_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${guarantees_compliance_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_compliance_overclaim_repo="${workdir}/passive-compliance-overclaim"
copy_valid_repo "${passive_compliance_overclaim_repo}"
printf '%s\n' "Compliance is certified by Phase 66.5." >>"${passive_compliance_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_compliance_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_ga_overclaim_repo="${workdir}/passive-ga-overclaim"
copy_valid_repo "${passive_ga_overclaim_repo}"
printf '%s\n' "GA readiness is established by this proof." >>"${passive_ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_rc_overclaim_repo="${workdir}/passive-rc-overclaim"
copy_valid_repo "${passive_rc_overclaim_repo}"
printf '%s\n' "RC pass is authorized by Phase 66.5." >>"${passive_rc_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_rc_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_customer_portal_overclaim_repo="${workdir}/passive-customer-portal-overclaim"
copy_valid_repo "${passive_customer_portal_overclaim_repo}"
printf '%s\n' "Customer portal readiness is confirmed by Phase 66.5." >>"${passive_customer_portal_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_customer_portal_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_production_sla_overclaim_repo="${workdir}/passive-production-sla-overclaim"
copy_valid_repo "${passive_production_sla_overclaim_repo}"
printf '%s\n' "Production SLA reporting is validated by this proof." >>"${passive_production_sla_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_production_sla_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_commercial_replacement_overclaim_repo="${workdir}/passive-commercial-replacement-overclaim"
copy_valid_repo "${passive_commercial_replacement_overclaim_repo}"
printf '%s\n' "Commercial replacement readiness is established by this proof." >>"${passive_commercial_replacement_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_commercial_replacement_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

certify_compliance_overclaim_repo="${workdir}/certify-compliance-overclaim"
copy_valid_repo "${certify_compliance_overclaim_repo}"
printf '%s\n' "Phase 66.5 certifies compliance." >>"${certify_compliance_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${certify_compliance_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

supportability_overclaim_repo="${workdir}/supportability-overclaim"
copy_valid_repo "${supportability_overclaim_repo}"
printf '%s\n' "Phase 66.5 proves supportability." >>"${supportability_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${supportability_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

closeout_evidence_overclaim_repo="${workdir}/closeout-evidence-overclaim"
copy_valid_repo "${closeout_evidence_overclaim_repo}"
printf '%s\n' "This proof satisfies closeout evidence." >>"${closeout_evidence_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${closeout_evidence_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

proof_compliance_identity_repo="${workdir}/proof-compliance-identity"
copy_valid_repo "${proof_compliance_identity_repo}"
printf '%s\n' "This proof is compliance certification." >>"${proof_compliance_identity_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${proof_compliance_identity_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

proof_sla_identity_repo="${workdir}/proof-sla-identity"
copy_valid_repo "${proof_sla_identity_repo}"
printf '%s\n' "This proof is production SLA reporting." >>"${proof_sla_identity_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${proof_sla_identity_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

proof_design_partner_identity_repo="${workdir}/proof-design-partner-identity"
copy_valid_repo "${proof_design_partner_identity_repo}"
printf '%s\n' "This proof is real design-partner export success." >>"${proof_design_partner_identity_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${proof_design_partner_identity_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

hyphenated_compliance_overclaim_repo="${workdir}/hyphenated-compliance-overclaim"
copy_valid_repo "${hyphenated_compliance_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms compliance-certification readiness." >>"${hyphenated_compliance_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hyphenated_compliance_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

portal_overclaim_repo="${workdir}/portal-overclaim"
copy_valid_repo "${portal_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms customer portal readiness." >>"${portal_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${portal_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

hyphenated_portal_overclaim_repo="${workdir}/hyphenated-portal-overclaim"
copy_valid_repo "${hyphenated_portal_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms customer-portal readiness." >>"${hyphenated_portal_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hyphenated_portal_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

hyphenated_sla_overclaim_repo="${workdir}/hyphenated-sla-overclaim"
copy_valid_repo "${hyphenated_sla_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms production-SLA reporting." >>"${hyphenated_sla_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hyphenated_sla_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

hyphenated_commercial_overclaim_repo="${workdir}/hyphenated-commercial-overclaim"
copy_valid_repo "${hyphenated_commercial_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms commercial-replacement readiness." >>"${hyphenated_commercial_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hyphenated_commercial_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

secret_repo="${workdir}/secret"
copy_valid_repo "${secret_repo}"
printf '%s\n' "api_key: abcdefghijklmnop" >>"${secret_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${secret_repo}" "production secret-looking value detected"

comment_secret_repo="${workdir}/comment-secret"
copy_valid_repo "${comment_secret_repo}"
printf '%s\n' "<!-- api_key: abcdefghijklmnop -->" >>"${comment_secret_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${comment_secret_repo}" "production secret-looking value detected"

customer_private_repo="${workdir}/customer-private"
copy_valid_repo "${customer_private_repo}"
printf '%s\n' "The proof includes customer-private ticket export." >>"${customer_private_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

customer_private_plural_repo="${workdir}/customer-private-plural"
copy_valid_repo "${customer_private_plural_repo}"
printf '%s\n' "Customer-private tickets are stored in the proof." >>"${customer_private_plural_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${customer_private_plural_repo}" "customer-private data detected"

customer_private_prohibition_bypass_repo="${workdir}/customer-private-prohibition-bypass"
copy_valid_repo "${customer_private_prohibition_bypass_repo}"
printf '%s\n' "The proof stores customer-private ticket export and customer-private data fails the proof." >>"${customer_private_prohibition_bypass_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${customer_private_prohibition_bypass_repo}" "customer-private data detected"

customer_private_exposes_prohibition_bypass_repo="${workdir}/customer-private-exposes-prohibition-bypass"
copy_valid_repo "${customer_private_exposes_prohibition_bypass_repo}"
printf '%s\n' "The proof exposes customer-private ticket export and customer-private data fails the proof." >>"${customer_private_exposes_prohibition_bypass_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${customer_private_exposes_prohibition_bypass_repo}" "customer-private data detected"

comment_customer_private_repo="${workdir}/comment-customer-private"
copy_valid_repo "${comment_customer_private_repo}"
printf '%s\n' "<!-- customer-private ticket export -->" >>"${comment_customer_private_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${comment_customer_private_repo}" "customer-private data detected"

wrapped_readme_claim_repo="${workdir}/wrapped-readme-claim"
copy_valid_repo "${wrapped_readme_claim_repo}"
printf '%s\n%s\n' "Phase 66.5 report export" "is GA ready." >>"${wrapped_readme_claim_repo}/README.md"
assert_fails_with "${wrapped_readme_claim_repo}" "Forbidden Phase 66.5 README claim matched"

safe_limitation_repo="${workdir}/safe-limitation"
copy_valid_repo "${safe_limitation_repo}"
printf '%s\n' "Phase 66.5 records that report authority over AegisOps records remains out of scope." >>"${safe_limitation_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${safe_limitation_repo}"

echo "Phase 66.5 report export RC proof verifier self-test passed."
