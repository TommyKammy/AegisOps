#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT
assertion_manifest="${workdir}/assertions.tsv"
assertion_jobs="${PHASE66_5_TEST_JOBS:-4}"
: >"${assertion_manifest}"

if [[ ! "${assertion_jobs}" =~ ^[1-9][0-9]*$ ]]; then
  echo "PHASE66_5_TEST_JOBS must be a positive integer" >&2
  exit 1
fi

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

complete_redaction_posture="secrets redacted, credentials redacted, customer-private data redacted, workstation-local paths redacted, pii redacted"

assert_passes() {
  local target="$1"

  printf 'pass\t%s\t\n' "${target}" >>"${assertion_manifest}"
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  printf 'fail\t%s\t%s\n' "${target}" "${expected}" >>"${assertion_manifest}"
}

run_assertion() {
  local expectation="$1"
  local target="$2"
  local expected_message="$3"
  local stdout_path="${target}.assert.out"
  local stderr_path="${target}.assert.err"

  if [[ "${expectation}" == "pass" ]]; then
    if ! PHASE66_5_SKIP_PATH_HYGIENE=1 bash "${target}/scripts/verify-phase-66-5-report-export-rc-proof.sh" "${target}" >"${stdout_path}" 2>"${stderr_path}"; then
      echo "Expected Phase 66.5 verifier success for: ${target#"${workdir}/"}" >&2
      cat "${stderr_path}" >&2
      return 1
    fi
    return 0
  fi

  if PHASE66_5_SKIP_PATH_HYGIENE=1 bash "${target}/scripts/verify-phase-66-5-report-export-rc-proof.sh" "${target}" >"${stdout_path}" 2>"${stderr_path}"; then
    echo "Expected Phase 66.5 verifier failure for ${target#"${workdir}/"} containing: ${expected_message}" >&2
    return 1
  fi
  if ! grep -Fq -- "${expected_message}" "${stderr_path}"; then
    echo "Missing expected Phase 66.5 verifier failure for ${target#"${workdir}/"}: ${expected_message}" >&2
    cat "${stderr_path}" >&2
    return 1
  fi
}

run_assertions() {
  local expectation
  local target
  local expected_message
  local pid
  local failed=0
  local -a pids
  pids=()

  while IFS=$'\t' read -r expectation target expected_message; do
    run_assertion "${expectation}" "${target}" "${expected_message}" &
    pids+=("$!")
    if ((${#pids[@]} >= assertion_jobs)); then
      for pid in "${pids[@]}"; do
        wait "${pid}" || failed=1
      done
      pids=()
    fi
  done <"${assertion_manifest}"

  for pid in "${pids[@]}"; do
    wait "${pid}" || failed=1
  done
  ((failed == 0))
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
printf '%s\n' "redaction_posture: ${complete_redaction_posture}, token: redacted" >>"${valid_redacted_credentials_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "password: redacted" >>"${valid_redacted_credentials_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_redacted_credentials_repo}"

valid_customer_private_redaction_repo="${workdir}/valid-customer-private-redaction"
copy_valid_repo "${valid_customer_private_redaction_repo}"
printf '%s\n' "redaction_posture: ${complete_redaction_posture}" >>"${valid_customer_private_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_customer_private_redaction_repo}"

valid_semicolon_redaction_repo="${workdir}/valid-semicolon-redaction"
copy_valid_repo "${valid_semicolon_redaction_repo}"
printf '%s\n' "redaction_posture: secrets redacted; credentials redacted; customer-private data redacted; workstation-local paths redacted; pii redacted" >>"${valid_semicolon_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_semicolon_redaction_repo}"

valid_customer_private_not_stored_repo="${workdir}/valid-customer-private-not-stored"
copy_valid_repo "${valid_customer_private_not_stored_repo}"
printf '%s\n' "redaction_posture: secrets redacted, credentials redacted, customer-private data not stored, workstation-local paths redacted, pii redacted" >>"${valid_customer_private_not_stored_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_customer_private_not_stored_repo}"

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

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  negative_required_value_repo="${workdir}/negative-required-value-${fixture_name}"
  copy_valid_repo "${negative_required_value_repo}"
  printf '%s\n' "${evidence_line}" >>"${negative_required_value_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${negative_required_value_repo}" "missing required evidence value detected"
done <<'EOF'
journey-no::journey_run_id: no
report-no::report_export_id: no; timestamp=2026-07-04T01:22:50Z; operator=reviewer-1; export_profile=bounded
report-false::report_export_id: false; timestamp=2026-07-04T01:22:50Z; operator=reviewer-1; export_profile=bounded
report-nil::report_export_id: nil; timestamp=2026-07-04T01:22:50Z; operator=reviewer-1; export_profile=bounded
EOF

report_export_without_timestamp_repo="${workdir}/report-export-without-timestamp"
copy_valid_repo "${report_export_without_timestamp_repo}"
printf '%s\n' "report_export_id: EXP-1 without timestamp" >>"${report_export_without_timestamp_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_export_without_timestamp_repo}" "missing required evidence value detected"

report_export_no_operator_repo="${workdir}/report-export-no-operator"
copy_valid_repo "${report_export_no_operator_repo}"
printf '%s\n' "report_export_id: EXP-1 no operator" >>"${report_export_no_operator_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_export_no_operator_repo}" "missing required evidence value detected"

export_format_without_checksum_repo="${workdir}/export-format-without-checksum"
copy_valid_repo "${export_format_without_checksum_repo}"
printf '%s\n' "export_format: PDF without checksum" >>"${export_format_without_checksum_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${export_format_without_checksum_repo}" "missing required evidence value detected"

bare_report_export_id_repo="${workdir}/bare-report-export-id"
copy_valid_repo "${bare_report_export_id_repo}"
printf '%s\n' "report_export_id: EXP-1" >>"${bare_report_export_id_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${bare_report_export_id_repo}" "missing required evidence value detected"

bare_export_format_repo="${workdir}/bare-export-format"
copy_valid_repo "${bare_export_format_repo}"
printf '%s\n' "export_format: PDF" >>"${bare_export_format_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${bare_export_format_repo}" "missing required evidence value detected"

missing_report_export_primary_id_repo="${workdir}/missing-report-export-primary-id"
copy_valid_repo "${missing_report_export_primary_id_repo}"
printf '%s\n' "report_export_id: timestamp=2026-07-04T01:22:50Z; operator=reviewer-1; export_profile=bounded" >>"${missing_report_export_primary_id_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_report_export_primary_id_repo}" "missing required evidence value detected"

missing_export_format_primary_value_repo="${workdir}/missing-export-format-primary-value"
copy_valid_repo "${missing_export_format_primary_value_repo}"
printf '%s\n' "export_format: file_name_pattern=report-*.pdf; checksum=sha256:abcdef123456" >>"${missing_export_format_primary_value_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_export_format_primary_value_repo}" "missing required evidence value detected"

missing_export_primary_values_table_repo="${workdir}/missing-export-primary-values-table"
copy_valid_repo "${missing_export_primary_values_table_repo}"
printf '%s\n' "| report_export_id | timestamp=2026-07-04T01:22:50Z | operator=reviewer-1 | export_profile=bounded |" >>"${missing_export_primary_values_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_export_primary_values_table_repo}" "missing required evidence value detected"

missing_format_primary_value_table_repo="${workdir}/missing-format-primary-value-table"
copy_valid_repo "${missing_format_primary_value_table_repo}"
printf '%s\n' "| export_format | file_name_pattern=report-*.pdf | checksum=sha256:abcdef123456 |" >>"${missing_format_primary_value_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_format_primary_value_table_repo}" "missing required evidence value detected"

complete_export_identity_repo="${workdir}/complete-export-identity"
copy_valid_repo "${complete_export_identity_repo}"
printf '%s\n' "report_export_id: EXP-1; timestamp=2026-07-04T01:22:50Z; operator=reviewer-1; export_profile=bounded" >>"${complete_export_identity_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "export_format: PDF; file_name_pattern=report-*.pdf; checksum=sha256:abcdef123456" >>"${complete_export_identity_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${complete_export_identity_repo}"

complete_export_identity_table_repo="${workdir}/complete-export-identity-table"
copy_valid_repo "${complete_export_identity_table_repo}"
printf '%s\n' "| report_export_id | EXP-1 | timestamp=2026-07-04T01:22:50Z | operator=reviewer-1 | export_profile=bounded |" >>"${complete_export_identity_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "| export_format | PDF | file_name_pattern=report-*.pdf | hash=sha256:abcdef123456 |" >>"${complete_export_identity_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${complete_export_identity_table_repo}"

while IFS='|' read -r fixture_name export_format file_extension; do
  supported_export_format_repo="${workdir}/supported-export-format-${fixture_name}"
  copy_valid_repo "${supported_export_format_repo}"
  printf '%s\n' "export_format: ${export_format}; file_name_pattern=report-*.${file_extension}; checksum=sha256:abcdef123456" >>"${supported_export_format_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_passes "${supported_export_format_repo}"
done <<'EOF'
pdf|PDF|pdf
csv|csv|csv
json|JSON|json
EOF

while IFS='|' read -r fixture_name export_format file_extension; do
  unsupported_export_format_repo="${workdir}/unsupported-export-format-${fixture_name}"
  copy_valid_repo "${unsupported_export_format_repo}"
  printf '%s\n' "export_format: ${export_format}; file_name_pattern=report-*.${file_extension}; checksum=sha256:abcdef123456" >>"${unsupported_export_format_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${unsupported_export_format_repo}" "missing required evidence value detected"
done <<'EOF'
executable|exe|exe
archive|zip|zip
custom|custom-report|custom
pdf-extension-mismatch|pdf|json
EOF

complete_export_identity_offset_repo="${workdir}/complete-export-identity-offset"
copy_valid_repo "${complete_export_identity_offset_repo}"
printf '%s\n' "report_export_id: EXP-1; timestamp=2024-02-29T01:22:50.123+09:00; operator=reviewer-1; export_profile=bounded" >>"${complete_export_identity_offset_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${complete_export_identity_offset_repo}"

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  placeholder_export_subfield_repo="${workdir}/placeholder-export-subfield-${fixture_name}"
  copy_valid_repo "${placeholder_export_subfield_repo}"
  printf '%s\n' "${evidence_line}" >>"${placeholder_export_subfield_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${placeholder_export_subfield_repo}" "missing required evidence value detected"
done <<'EOF'
timestamp::report_export_id: EXP-1; timestamp=unknown; operator=reviewer-1; export_profile=bounded
operator::report_export_id: EXP-1; timestamp=2026-07-04T01:22:50Z; operator=tbd; export_profile=bounded
profile::report_export_id: EXP-1; timestamp=2026-07-04T01:22:50Z; operator=reviewer-1; export_profile=not_provided
filename::export_format: PDF; file_name_pattern=placeholder; checksum=sha256:abcdef123456
checksum::export_format: PDF; file_name_pattern=report-*.pdf; checksum=unknown
EOF

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  invalid_timestamp_repo="${workdir}/invalid-timestamp-${fixture_name}"
  copy_valid_repo "${invalid_timestamp_repo}"
  printf '%s\n' "${evidence_line}" >>"${invalid_timestamp_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${invalid_timestamp_repo}" "missing required evidence value detected"
done <<'EOF'
nonsensical::report_export_id: EXP-1; timestamp=banana; operator=reviewer-1; export_profile=bounded
invalid-date::report_export_id: EXP-1; timestamp=2026-02-29T01:22:50Z; operator=reviewer-1; export_profile=bounded
invalid-time::report_export_id: EXP-1; timestamp=2026-07-04T25:22:50Z; operator=reviewer-1; export_profile=bounded
EOF

placeholder_export_subfield_table_repo="${workdir}/placeholder-export-subfield-table"
copy_valid_repo "${placeholder_export_subfield_table_repo}"
printf '%s\n' "| report_export_id | EXP-1 | timestamp=unknown | operator=reviewer-1 | export_profile=bounded |" >>"${placeholder_export_subfield_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${placeholder_export_subfield_table_repo}" "missing required evidence value detected"

missing_required_no_operator_table_repo="${workdir}/missing-required-no-operator-table"
copy_valid_repo "${missing_required_no_operator_table_repo}"
printf '%s\n' "| report_export_id | EXP-1 | no operator |" >>"${missing_required_no_operator_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_required_no_operator_table_repo}" "missing required evidence value detected"

hidden_limitation_repo="${workdir}/hidden-limitation"
copy_valid_repo "${hidden_limitation_repo}"
printf '%s\n' "limitation_references: hidden in report text" >>"${hidden_limitation_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hidden_limitation_repo}" "missing required evidence value detected"

hidden_limitation_extra_table_cell_repo="${workdir}/hidden-limitation-extra-table-cell"
copy_valid_repo "${hidden_limitation_extra_table_cell_repo}"
printf '%s\n' "| limitation_references | LIM-1 | hidden in report text |" >>"${hidden_limitation_extra_table_cell_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hidden_limitation_extra_table_cell_repo}" "missing required evidence value detected"

incomplete_limitation_without_follow_up_repo="${workdir}/incomplete-limitation-without-follow-up"
copy_valid_repo "${incomplete_limitation_without_follow_up_repo}"
printf '%s\n' "limitation_references: LIM-1; export evidence incomplete" >>"${incomplete_limitation_without_follow_up_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${incomplete_limitation_without_follow_up_repo}" "missing required evidence value detected"

complete_incomplete_limitation_repo="${workdir}/complete-incomplete-limitation"
copy_valid_repo "${complete_incomplete_limitation_repo}"
printf '%s\n' "limitation_references: LIM-1; export evidence incomplete; owner=operator-1; decision_date=2026-07-18; follow_up_date=2026-07-25" >>"${complete_incomplete_limitation_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${complete_incomplete_limitation_repo}"

complete_incomplete_limitation_table_repo="${workdir}/complete-incomplete-limitation-table"
copy_valid_repo "${complete_incomplete_limitation_table_repo}"
printf '%s\n' "| limitation_references | LIM-1 | export evidence incomplete | owner=operator-1 | decision_date=2026-07-18 | follow_up_date=2026-07-25 |" >>"${complete_incomplete_limitation_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${complete_incomplete_limitation_table_repo}"

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  placeholder_limitation_subfield_repo="${workdir}/placeholder-limitation-subfield-${fixture_name}"
  copy_valid_repo "${placeholder_limitation_subfield_repo}"
  printf '%s\n' "${evidence_line}" >>"${placeholder_limitation_subfield_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${placeholder_limitation_subfield_repo}" "missing required evidence value detected"
done <<'EOF'
owner::limitation_references: LIM-1; export evidence incomplete; owner=unknown; decision_date=2026-07-18; follow_up_date=2026-07-25
decision-date::limitation_references: LIM-1; export evidence incomplete; owner=operator-1; decision_date=tbd; follow_up_date=2026-07-25
follow-up-date::limitation_references: LIM-1; export evidence incomplete; owner=operator-1; decision_date=2026-07-18; follow_up_date=not_set
EOF

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  invalid_limitation_date_repo="${workdir}/invalid-limitation-date-${fixture_name}"
  copy_valid_repo "${invalid_limitation_date_repo}"
  printf '%s\n' "${evidence_line}" >>"${invalid_limitation_date_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${invalid_limitation_date_repo}" "missing required evidence value detected"
done <<'EOF'
nonsensical::limitation_references: LIM-1; export evidence incomplete; owner=operator-1; decision_date=banana; follow_up_date=later
invalid-decision-date::limitation_references: LIM-1; export evidence incomplete; owner=operator-1; decision_date=2026-02-29; follow_up_date=2026-07-25
invalid-follow-up-date::limitation_references: LIM-1; export evidence incomplete; owner=operator-1; decision_date=2026-07-18; follow_up_date=2026-04-31
EOF

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

table_hash_with_branch_phrase_repo="${workdir}/table-hash-with-branch-phrase"
copy_valid_repo "${table_hash_with_branch_phrase_repo}"
printf '%s\n' "| repository_revision | 0123456789abcdef0123456789abcdef01234567 | main branch |" >>"${table_hash_with_branch_phrase_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${table_hash_with_branch_phrase_repo}" "mutable repository revision detected"

table_hash_with_non_branch_note_repo="${workdir}/table-hash-with-non-branch-note"
copy_valid_repo "${table_hash_with_non_branch_note_repo}"
printf '%s\n' "| repository_revision | 0123456789abcdef0123456789abcdef01234567 | domain review complete |" >>"${table_hash_with_non_branch_note_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${table_hash_with_non_branch_note_repo}"

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

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  source_record_generated_artifact_repo="${workdir}/source-record-generated-artifact-${fixture_name}"
  copy_valid_repo "${source_record_generated_artifact_repo}"
  printf '%s\n' "${evidence_line}" >>"${source_record_generated_artifact_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${source_record_generated_artifact_repo}" "invalid source record reference detected"
done <<'EOF'
assignment::source_record_references: source alert AL-1; case CASE-1; evidence EV-1; approval AP-1; action request AR-1; execution receipt ER-1; reconciliation REC-1; generated artifact ART-1
table::| source_record_references | source alert AL-1 | case CASE-1 | evidence EV-1 | approval AP-1 | action request AR-1 | execution receipt ER-1 | reconciliation REC-1 | generated report artifact ART-1 |
EOF

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

source_record_report_file_repo="${workdir}/source-record-report-file"
copy_valid_repo "${source_record_report_file_repo}"
printf '%s\n' "source_record_references: report file" >>"${source_record_report_file_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_report_file_repo}" "invalid source record reference detected"

source_record_export_metadata_repo="${workdir}/source-record-export-metadata"
copy_valid_repo "${source_record_export_metadata_repo}"
printf '%s\n' "source_record_references: export metadata" >>"${source_record_export_metadata_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_export_metadata_repo}" "invalid source record reference detected"

source_record_report_export_repo="${workdir}/source-record-report-export"
copy_valid_repo "${source_record_report_export_repo}"
printf '%s\n' "source_record_references: report export" >>"${source_record_report_export_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_report_export_repo}" "invalid source record reference detected"

source_record_generated_report_file_repo="${workdir}/source-record-generated-report-file"
copy_valid_repo "${source_record_generated_report_file_repo}"
printf '%s\n' "source_record_references: generated report file" >>"${source_record_generated_report_file_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_generated_report_file_repo}" "invalid source record reference detected"

source_record_extra_table_cell_repo="${workdir}/source-record-extra-table-cell"
copy_valid_repo "${source_record_extra_table_cell_repo}"
printf '%s\n' "| source_record_references | CASE-1 | report metadata |" >>"${source_record_extra_table_cell_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_extra_table_cell_repo}" "invalid source record reference detected"

source_record_alert_only_repo="${workdir}/source-record-alert-only"
copy_valid_repo "${source_record_alert_only_repo}"
printf '%s\n' "source_record_references: alert AL-1 only" >>"${source_record_alert_only_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_alert_only_repo}" "incomplete source record references detected"

complete_source_record_references_repo="${workdir}/complete-source-record-references"
copy_valid_repo "${complete_source_record_references_repo}"
printf '%s\n' "source_record_references: source alert ALERT-1, case CASE-1, evidence EVD-1, approval APR-1, action request ACT-1, execution receipt REC-1, reconciliation record RCN-1" >>"${complete_source_record_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${complete_source_record_references_repo}"

complete_source_record_line="source alert ALERT-1; case CASE-1; evidence EVD-1; approval APR-1; action request ACT-1; execution receipt REC-1; reconciliation record RCN-1"
while IFS='|' read -r fixture_name present_reference identifierless_reference; do
  identifierless_source_record_repo="${workdir}/identifierless-source-record-${fixture_name}"
  copy_valid_repo "${identifierless_source_record_repo}"
  identifierless_source_record_line="${complete_source_record_line/${present_reference}/${identifierless_reference}}"
  printf '%s\n' "source_record_references: ${identifierless_source_record_line}" >>"${identifierless_source_record_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${identifierless_source_record_repo}" "incomplete source record references detected"
done <<'EOF'
source-alert|source alert ALERT-1|source alert
case|case CASE-1|case
evidence|evidence EVD-1|evidence
approval|approval APR-1|approval
action-request|action request ACT-1|action request
execution-receipt|execution receipt REC-1|execution receipt
reconciliation|reconciliation record RCN-1|reconciliation record
EOF

identifierless_source_alert_table_repo="${workdir}/identifierless-source-alert-table"
copy_valid_repo "${identifierless_source_alert_table_repo}"
printf '%s\n' "| source_record_references | source alert | case CASE-1 | evidence EVD-1 | approval APR-1 | action request ACT-1 | execution receipt REC-1 | reconciliation record RCN-1 |" >>"${identifierless_source_alert_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${identifierless_source_alert_table_repo}" "incomplete source record references detected"

while IFS='|' read -r fixture_name present_reference negated_reference; do
  negated_source_record_repo="${workdir}/negated-source-record-${fixture_name}"
  copy_valid_repo "${negated_source_record_repo}"
  negated_source_record_line="${complete_source_record_line/${present_reference}/${negated_reference}}"
  printf '%s\n' "source_record_references: ${negated_source_record_line}" >>"${negated_source_record_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${negated_source_record_repo}" "incomplete source record references detected"
done <<'EOF'
source-alert|source alert ALERT-1|no source alert record
case|case CASE-1|no case record
evidence|evidence EVD-1|no evidence record
approval|approval APR-1|no approval record
action-request|action request ACT-1|no action request record
execution-receipt|execution receipt REC-1|no execution receipt record
reconciliation|reconciliation record RCN-1|no reconciliation record
EOF

negated_source_record_table_repo="${workdir}/negated-source-record-table"
copy_valid_repo "${negated_source_record_table_repo}"
printf '%s\n' "| source_record_references | source alert ALERT-1 | no case record | evidence EVD-1 | approval APR-1 | action request ACT-1 | execution receipt REC-1 | reconciliation record RCN-1 |" >>"${negated_source_record_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${negated_source_record_table_repo}" "incomplete source record references detected"

valid_section_record_references_repo="${workdir}/valid-section-record-references"
copy_valid_repo "${valid_section_record_references_repo}"
printf '%s\n' "case_section_reference: CASE-SECTION-1; status=open; evidence_links=EVD-1; owner=operator-1; limitation_references=LIM-1" >>"${valid_section_record_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "action_section_reference: ACTION-SECTION-1; approval=APR-1; delegated_action_request=ACT-1; execution_receipt=REC-1; mismatch_posture=matched" >>"${valid_section_record_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "reconciliation_section_reference: RECON-SECTION-1; receipt=REC-1; outcome=matched; mismatch_state=matched; follow_up_owner=operator-1; linked_record=CASE-1" >>"${valid_section_record_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_section_record_references_repo}"

valid_section_record_references_table_repo="${workdir}/valid-section-record-references-table"
copy_valid_repo "${valid_section_record_references_table_repo}"
printf '%s\n' "| case_section_reference | CASE-SECTION-1 | status=open | evidence_links=EVD-1 | owner=operator-1 | limitation_references=LIM-1 |" >>"${valid_section_record_references_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "| action_section_reference | ACTION-SECTION-1 | approval=APR-1 | delegated_action_request=ACT-1 | execution_receipt=REC-1 | mismatch_posture=matched |" >>"${valid_section_record_references_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "| reconciliation_section_reference | RECON-SECTION-1 | receipt=REC-1 | outcome=matched | mismatch_state=matched | follow_up_owner=operator-1 | linked_record=CASE-1 |" >>"${valid_section_record_references_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_section_record_references_table_repo}"

valid_explicit_mismatch_states_repo="${workdir}/valid-explicit-mismatch-states"
copy_valid_repo "${valid_explicit_mismatch_states_repo}"
printf '%s\n' "action_section_reference: ACTION-SECTION-1; approval=APR-1; delegated_action_request=ACT-1; execution_receipt=REC-1; mismatch_posture=none" >>"${valid_explicit_mismatch_states_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "reconciliation_section_reference: RECON-SECTION-1; receipt=REC-1; outcome=reviewed; mismatch_state=mismatched; follow_up_owner=operator-1; linked_record=CASE-1" >>"${valid_explicit_mismatch_states_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${valid_explicit_mismatch_states_repo}"

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  invalid_mismatch_state_repo="${workdir}/invalid-mismatch-state-${fixture_name}"
  copy_valid_repo "${invalid_mismatch_state_repo}"
  printf '%s\n' "${evidence_line}" >>"${invalid_mismatch_state_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${invalid_mismatch_state_repo}" "missing required evidence value detected"
done <<'EOF'
posture-suffix::action_section_reference: ACTION-SECTION-1; approval=APR-1; delegated_action_request=ACT-1; execution_receipt=REC-1; mismatch_posture=matched_by_report
state-suffix::reconciliation_section_reference: RECON-SECTION-1; receipt=REC-1; outcome=reviewed; mismatch_state=matched_by_report; follow_up_owner=operator-1; linked_record=CASE-1
unknown-state::action_section_reference: ACTION-SECTION-1; approval=APR-1; delegated_action_request=ACT-1; execution_receipt=REC-1; mismatch_posture=unreviewed
EOF

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  placeholder_section_subfield_repo="${workdir}/placeholder-section-subfield-${fixture_name}"
  copy_valid_repo "${placeholder_section_subfield_repo}"
  printf '%s\n' "${evidence_line}" >>"${placeholder_section_subfield_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${placeholder_section_subfield_repo}" "missing required evidence value detected"
done <<'EOF'
case-status::case_section_reference: CASE-SECTION-1; status=unknown; evidence_links=EVD-1; owner=operator-1; limitation_references=LIM-1
case-owner::case_section_reference: CASE-SECTION-1; status=open; evidence_links=EVD-1; owner=none; limitation_references=LIM-1
action-approval::action_section_reference: ACTION-SECTION-1; approval=tbd; delegated_action_request=ACT-1; execution_receipt=REC-1; mismatch_posture=matched
action-receipt::action_section_reference: ACTION-SECTION-1; approval=APR-1; delegated_action_request=ACT-1; execution_receipt=unavailable; mismatch_posture=matched
reconciliation-outcome::reconciliation_section_reference: RECON-SECTION-1; receipt=REC-1; outcome=unknown; mismatch_state=matched; follow_up_owner=operator-1; linked_record=CASE-1
reconciliation-owner::reconciliation_section_reference: RECON-SECTION-1; receipt=REC-1; outcome=matched; mismatch_state=matched; follow_up_owner=none; linked_record=CASE-1
EOF

placeholder_section_subfield_table_repo="${workdir}/placeholder-section-subfield-table"
copy_valid_repo "${placeholder_section_subfield_table_repo}"
printf '%s\n' "| action_section_reference | ACTION-SECTION-1 | approval=unknown | delegated_action_request=ACT-1 | execution_receipt=REC-1 | mismatch_posture=matched |" >>"${placeholder_section_subfield_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${placeholder_section_subfield_table_repo}" "missing required evidence value detected"

while IFS= read -r action_reference; do
  fixture_name="${action_reference%%::*}"
  evidence_line="${action_reference#*::}"
  non_delegated_action_reference_repo="${workdir}/non-delegated-action-reference-${fixture_name}"
  copy_valid_repo "${non_delegated_action_reference_repo}"
  printf '%s\n' "${evidence_line}" >>"${non_delegated_action_reference_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${non_delegated_action_reference_repo}" "missing required evidence value detected"
done <<'EOF'
assignment::action_section_reference: ACTION-SECTION-1; approval=APR-1; action_request=ACT-1; execution_receipt=REC-1; mismatch_posture=matched
table::| action_section_reference | ACTION-SECTION-1 | approval=APR-1 | action_request=ACT-1 | execution_receipt=REC-1 | mismatch_posture=matched |
EOF

bare_section_references_repo="${workdir}/bare-section-references"
copy_valid_repo "${bare_section_references_repo}"
printf '%s\n' "case_section_reference: CASE-1" >>"${bare_section_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "action_section_reference: ACTION-1" >>"${bare_section_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "reconciliation_section_reference: REC-1" >>"${bare_section_references_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${bare_section_references_repo}" "missing required evidence value detected"

while IFS='|' read -r fixture_name incomplete_section_reference; do
  incomplete_section_reference_repo="${workdir}/incomplete-section-reference-${fixture_name}"
  copy_valid_repo "${incomplete_section_reference_repo}"
  printf '%s\n' "${incomplete_section_reference}" >>"${incomplete_section_reference_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${incomplete_section_reference_repo}" "missing required evidence value detected"
done <<'EOF'
case|case_section_reference: CASE-SECTION-1; evidence_links=EVD-1; owner=operator-1; limitation_references=LIM-1
action|action_section_reference: ACTION-SECTION-1; delegated_action_request=ACT-1; execution_receipt=REC-1; mismatch_posture=matched
reconciliation|reconciliation_section_reference: RECON-SECTION-1; receipt=REC-1; mismatch_state=matched; follow_up_owner=operator-1; linked_record=CASE-1
EOF

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

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  underscored_section_authority_repo="${workdir}/underscored-section-authority-${fixture_name}"
  copy_valid_repo "${underscored_section_authority_repo}"
  printf '%s\n' "${evidence_line}" >>"${underscored_section_authority_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${underscored_section_authority_repo}" "report section authority detected"
done <<'EOF'
underscore::case_section_reference: CASE-SECTION-1; status=closed_by_report; evidence_links=EVD-1; owner=operator-1; limitation_references=LIM-1
hyphen::case_section_reference: CASE-SECTION-1; status=closed-by-report; evidence_links=EVD-1; owner=operator-1; limitation_references=LIM-1
EOF

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

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  negated_required_label_repo="${workdir}/negated-required-label-${fixture_name}"
  copy_valid_repo "${negated_required_label_repo}"
  printf '%s\n' "${evidence_line}" >>"${negated_required_label_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${negated_required_label_repo}" "invalid RC label set detected"
done <<'EOF'
no-prefix::rc_label_set: rc-evidence no phase-66 report-export not-workflow-truth
without-prefix::rc_label_set: rc-evidence phase-66 without report-export not-workflow-truth
suffix::rc_label_set: rc-evidence phase-66 report-export excluded not-workflow-truth
table::| rc_label_set | rc-evidence | phase-66 | report-export | no not-workflow-truth |
EOF

bad_redaction_repo="${workdir}/bad-redaction"
copy_valid_repo "${bad_redaction_repo}"
printf '%s\n' "redaction_posture: not_needed" >>"${bad_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${bad_redaction_repo}" "invalid redaction posture detected"

raw_secret_redaction_repo="${workdir}/raw-secret-redaction"
copy_valid_repo "${raw_secret_redaction_repo}"
printf '%s\n' "redaction_posture: raw secrets included" >>"${raw_secret_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${raw_secret_redaction_repo}" "invalid redaction posture detected"

pii_included_redaction_repo="${workdir}/pii-included-redaction"
copy_valid_repo "${pii_included_redaction_repo}"
printf '%s\n' "redaction_posture: PII included" >>"${pii_included_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${pii_included_redaction_repo}" "invalid redaction posture detected"

pii_not_redacted_repo="${workdir}/pii-not-redacted"
copy_valid_repo "${pii_not_redacted_repo}"
printf '%s\n' "redaction_posture: PII not redacted" >>"${pii_not_redacted_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${pii_not_redacted_repo}" "invalid redaction posture detected"

credentials_included_redaction_repo="${workdir}/credentials-included-redaction"
copy_valid_repo "${credentials_included_redaction_repo}"
printf '%s\n' "redaction_posture: credentials included" >>"${credentials_included_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${credentials_included_redaction_repo}" "invalid redaction posture detected"

raw_credentials_included_redaction_repo="${workdir}/raw-credentials-included-redaction"
copy_valid_repo "${raw_credentials_included_redaction_repo}"
printf '%s\n' "redaction_posture: raw credentials included" >>"${raw_credentials_included_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${raw_credentials_included_redaction_repo}" "invalid redaction posture detected"

token_included_redaction_repo="${workdir}/token-included-redaction"
copy_valid_repo "${token_included_redaction_repo}"
printf '%s\n' "redaction_posture: token included" >>"${token_included_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${token_included_redaction_repo}" "invalid redaction posture detected"

token_included_redaction_table_repo="${workdir}/token-included-redaction-table"
copy_valid_repo "${token_included_redaction_table_repo}"
printf '%s\n' "| redaction_posture | token included |" >>"${token_included_redaction_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${token_included_redaction_table_repo}" "invalid redaction posture detected"

credentials_redacted_repo="${workdir}/credentials-redacted"
copy_valid_repo "${credentials_redacted_repo}"
printf '%s\n' "redaction_posture: ${complete_redaction_posture}, token: redacted" >>"${credentials_redacted_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${credentials_redacted_repo}"

incomplete_redaction_classes_repo="${workdir}/incomplete-redaction-classes"
copy_valid_repo "${incomplete_redaction_classes_repo}"
printf '%s\n' "redaction_posture: secrets redacted" >>"${incomplete_redaction_classes_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${incomplete_redaction_classes_repo}" "invalid redaction posture detected"

complete_redaction_classes_table_repo="${workdir}/complete-redaction-classes-table"
copy_valid_repo "${complete_redaction_classes_table_repo}"
printf '%s\n' "| redaction_posture | secrets redacted | credentials redacted | customer-private data redacted | workstation-local paths redacted | pii redacted |" >>"${complete_redaction_classes_table_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${complete_redaction_classes_table_repo}"

customer_private_redaction_repo="${workdir}/customer-private-redaction"
copy_valid_repo "${customer_private_redaction_repo}"
printf '%s\n' "redaction_posture: customer-private payloads" >>"${customer_private_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${customer_private_redaction_repo}" "invalid redaction posture detected"

workstation_local_redaction_repo="${workdir}/workstation-local-redaction"
copy_valid_repo "${workstation_local_redaction_repo}"
printf '%s\n' "redaction_posture: workstation-local paths included" >>"${workstation_local_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${workstation_local_redaction_repo}" "invalid redaction posture detected"

workstation_local_evidence_repo="${workdir}/workstation-local-evidence"
copy_valid_repo "${workstation_local_evidence_repo}"
printf '%s\n' "The proof stores workstation-local paths in the report." >>"${workstation_local_evidence_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${workstation_local_evidence_repo}" "workstation-local path evidence detected"

passive_workstation_local_evidence_repo="${workdir}/passive-workstation-local-evidence"
copy_valid_repo "${passive_workstation_local_evidence_repo}"
printf '%s\n' "Workstation-local paths are stored in the proof." >>"${passive_workstation_local_evidence_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_workstation_local_evidence_repo}" "workstation-local path evidence detected"

comment_workstation_local_evidence_repo="${workdir}/comment-workstation-local-evidence"
copy_valid_repo "${comment_workstation_local_evidence_repo}"
printf '%s\n' "<!-- proof stores workstation-local paths in the report -->" >>"${comment_workstation_local_evidence_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${comment_workstation_local_evidence_repo}" "workstation-local path evidence detected"

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

report_proves_source_truth_repo="${workdir}/report-proves-source-truth"
copy_valid_repo "${report_proves_source_truth_repo}"
printf '%s\n' "Report output proves source-record truth." >>"${report_proves_source_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_proves_source_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_confirms_workflow_truth_repo="${workdir}/report-confirms-workflow-truth"
copy_valid_repo "${report_confirms_workflow_truth_repo}"
printf '%s\n' "Report output confirms workflow truth." >>"${report_confirms_workflow_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_confirms_workflow_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  claim_text="${fixture#*::}"
  markdown_emphasis_claim_repo="${workdir}/markdown-emphasis-claim-${fixture_name}"
  copy_valid_repo "${markdown_emphasis_claim_repo}"
  printf '%s\n' "${claim_text}" >>"${markdown_emphasis_claim_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${markdown_emphasis_claim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"
done <<'EOF'
asterisk-bold::Report output **confirms** GA readiness.
underscore-bold::Report output __confirms__ GA readiness.
asterisk-italic::Report output *confirms* GA readiness.
underscore-italic::Report output _confirms_ GA readiness.
strikethrough::Report output ~~confirms~~ GA readiness.
EOF

report_validates_workflow_truth_repo="${workdir}/report-validates-workflow-truth"
copy_valid_repo "${report_validates_workflow_truth_repo}"
printf '%s\n' "Report output validates workflow truth." >>"${report_validates_workflow_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_validates_workflow_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

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

report_marks_case_closed_repo="${workdir}/report-marks-case-closed"
copy_valid_repo "${report_marks_case_closed_repo}"
printf '%s\n' "Report output marks case closed." >>"${report_marks_case_closed_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_marks_case_closed_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_triggers_action_execution_repo="${workdir}/report-triggers-action-execution"
copy_valid_repo "${report_triggers_action_execution_repo}"
printf '%s\n' "Report output triggers action execution." >>"${report_triggers_action_execution_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_triggers_action_execution_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_creates_case_closure_repo="${workdir}/report-creates-case-closure"
copy_valid_repo "${report_creates_case_closure_repo}"
printf '%s\n' "Report output creates case closure." >>"${report_creates_case_closure_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_creates_case_closure_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_completes_cases_repo="${workdir}/report-completes-cases"
copy_valid_repo "${report_completes_cases_repo}"
printf '%s\n' "Report output completes cases." >>"${report_completes_cases_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_completes_cases_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_report_closes_case_repo="${workdir}/passive-report-closes-case"
copy_valid_repo "${passive_report_closes_case_repo}"
printf '%s\n' "Cases are closed by report output." >>"${passive_report_closes_case_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_report_closes_case_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

completed_passive_report_closes_case_repo="${workdir}/completed-passive-report-closes-case"
copy_valid_repo "${completed_passive_report_closes_case_repo}"
printf '%s\n' "Cases have been closed by report output." >>"${completed_passive_report_closes_case_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${completed_passive_report_closes_case_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_report_authorizes_action_repo="${workdir}/passive-report-authorizes-action"
copy_valid_repo "${passive_report_authorizes_action_repo}"
printf '%s\n' "Action requests are authorized by report output." >>"${passive_report_authorizes_action_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_report_authorizes_action_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_report_determines_reconciliation_repo="${workdir}/passive-report-determines-reconciliation"
copy_valid_repo "${passive_report_determines_reconciliation_repo}"
printf '%s\n' "Reconciliation is determined by report output." >>"${passive_report_determines_reconciliation_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_report_determines_reconciliation_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_report_permits_approvals_repo="${workdir}/passive-report-permits-approvals"
copy_valid_repo "${passive_report_permits_approvals_repo}"
printf '%s\n' "Approvals are permitted by report output." >>"${passive_report_permits_approvals_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_report_permits_approvals_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_report_marks_cases_repo="${workdir}/passive-report-marks-cases"
copy_valid_repo "${passive_report_marks_cases_repo}"
printf '%s\n' "Cases are marked closed by report output." >>"${passive_report_marks_cases_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_report_marks_cases_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  claim_text="${fixture#*::}"
  semantic_authority_claim_repo="${workdir}/semantic-authority-claim-${fixture_name}"
  copy_valid_repo "${semantic_authority_claim_repo}"
  printf '%s\n' "${claim_text}" >>"${semantic_authority_claim_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${semantic_authority_claim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"
done <<'EOF'
passive-using::Cases are closed using report output.
passive-from::Action requests are authorized from report output.
passive-via::Reconciliation is determined via report output.
passive-through::Cases are closed through report output.
passive-based-on::Actions are executed based on report output.
truth-acts-as::Report output acts as workflow truth.
truth-functions-as::Report output functions as source-record truth.
truth-operates-as::Generated files operate as release truth.
truth-constitutes::Report output constitutes workflow truth.
truth-represents::Report metadata represents case truth.
authority-provides::Report output provides workflow authority.
authority-confers::Report output confers approval authority.
authority-conveys::Report output conveys case authority.
authority-bestows::Report output bestows action authority.
authority-delegates::Report output delegates reconciliation authority.
mutation-updates::Report output updates cases.
mutation-changes::Report output changes AegisOps records.
mutation-writes::Generated files write AegisOps records.
mutation-modifies::Report output modifies cases.
mutation-alters::Report output alters reconciliation.
mutation-deletes::Report output deletes records.
mutation-transitions::Report output transitions cases.
EOF

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  claim_text="${fixture#*::}"
  coordinated_positive_claim_repo="${workdir}/coordinated-positive-claim-${fixture_name}"
  copy_valid_repo "${coordinated_positive_claim_repo}"
  printf '%s\n' "${claim_text}" >>"${coordinated_positive_claim_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${coordinated_positive_claim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"
done <<'EOF'
readiness::This proof does not prove GA readiness, confirms GA readiness.
authority::Report output cannot close cases, approves action requests.
authority-provider::Report output does not act as workflow truth, provides approval authority.
EOF

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  claim_text="${fixture#*::}"
  safe_claim_scope_repo="${workdir}/safe-claim-scope-${fixture_name}"
  copy_valid_repo "${safe_claim_scope_repo}"
  printf '%s\n' "${claim_text}" >>"${safe_claim_scope_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_passes "${safe_claim_scope_repo}"
done <<'EOF'
negative-authority-list::Report output cannot close cases, approve action requests, execute actions, or reconcile records.
negative-semantic-list::Report output cannot act as workflow truth, provide approval authority, or update cases.
negative-truth::Report output does not act as workflow truth.
negative-passive::Cases are not closed using report output.
rc-evidence-demonstrates::Phase 66.5 demonstrates report export RC evidence.
rc-evidence-confirms::This proof confirms RC evidence for report export.
rc-evidence-validates::Report output validates report export RC evidence.
EOF

table_report_truth_repo="${workdir}/table-report-truth"
copy_valid_repo "${table_report_truth_repo}"
printf '%s\n' "| note | Report output is workflow truth. |" >>"${table_report_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${table_report_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_workflow_truth_created_repo="${workdir}/passive-workflow-truth-created"
copy_valid_repo "${passive_workflow_truth_created_repo}"
printf '%s\n' "Workflow truth is created by report output." >>"${passive_workflow_truth_created_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_workflow_truth_created_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_source_record_truth_created_repo="${workdir}/passive-source-record-truth-created"
copy_valid_repo "${passive_source_record_truth_created_repo}"
printf '%s\n' "Source-record truth is created by generated files." >>"${passive_source_record_truth_created_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_source_record_truth_created_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_case_truth_created_repo="${workdir}/passive-case-truth-created"
copy_valid_repo "${passive_case_truth_created_repo}"
printf '%s\n' "Case truth is created by screenshots." >>"${passive_case_truth_created_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_case_truth_created_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

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

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  claim_text="${fixture#*::}"
  inferred_readiness_claim_repo="${workdir}/inferred-readiness-claim-${fixture_name}"
  copy_valid_repo "${inferred_readiness_claim_repo}"
  printf '%s\n' "${claim_text}" >>"${inferred_readiness_claim_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${inferred_readiness_claim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"
done <<'EOF'
active-infers-rc::This proof infers RC pass.
active-inferred-ga::Report output inferred GA pass.
active-implies-ga::Generated files imply GA readiness.
active-concludes-rc::Phase 66.5 concludes RC pass.
passive-inferred-from::GA pass is inferred from report output.
passive-implied-through::RC pass was implied through generated files.
passive-indicated-using::GA readiness is indicated using verifier output.
customer-portal-ready::This proof is customer portal ready.
report-customer-portal-ready::Report export is customer portal ready.
hyphenated-customer-portal-ready::This proof is customer-portal ready.
ready-for-customer-portal::This proof is ready for customer portal.
mixed-negated-and-positive::This proof does not infer RC pass and report output infers GA pass.
EOF

safe_negated_inferred_readiness_repo="${workdir}/safe-negated-inferred-readiness"
copy_valid_repo "${safe_negated_inferred_readiness_repo}"
printf '%s\n' "This proof does not infer RC pass." >>"${safe_negated_inferred_readiness_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "GA pass is not inferred from report output." >>"${safe_negated_inferred_readiness_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${safe_negated_inferred_readiness_repo}"

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

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  claim_text="${fixture#*::}"
  passive_proved_overclaim_repo="${workdir}/passive-proved-overclaim-${fixture_name}"
  copy_valid_repo "${passive_proved_overclaim_repo}"
  printf '%s\n' "${claim_text}" >>"${passive_proved_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${passive_proved_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"
done <<'EOF'
report-output::GA readiness is proved by report output.
this-proof::GA readiness is proved by this proof.
report-export::Compliance certification is proved by report export.
EOF

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

generated_files_ga_overclaim_repo="${workdir}/generated-files-ga-overclaim"
copy_valid_repo "${generated_files_ga_overclaim_repo}"
printf '%s\n' "Generated files confirm GA readiness." >>"${generated_files_ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${generated_files_ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_output_compliance_overclaim_repo="${workdir}/report-output-compliance-overclaim"
copy_valid_repo "${report_output_compliance_overclaim_repo}"
printf '%s\n' "Report output confirms compliance certification." >>"${report_output_compliance_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_output_compliance_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

screenshots_portal_overclaim_repo="${workdir}/screenshots-portal-overclaim"
copy_valid_repo "${screenshots_portal_overclaim_repo}"
printf '%s\n' "Screenshots prove customer portal readiness." >>"${screenshots_portal_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${screenshots_portal_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

passive_generated_files_ga_overclaim_repo="${workdir}/passive-generated-files-ga-overclaim"
copy_valid_repo "${passive_generated_files_ga_overclaim_repo}"
printf '%s\n' "GA readiness is confirmed by generated files." >>"${passive_generated_files_ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${passive_generated_files_ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

plural_generated_files_ga_overclaim_repo="${workdir}/plural-generated-files-ga-overclaim"
copy_valid_repo "${plural_generated_files_ga_overclaim_repo}"
printf '%s\n' "Generated files are GA ready." >>"${plural_generated_files_ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${plural_generated_files_ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

negated_then_subordinate_overclaim_repo="${workdir}/negated-then-subordinate-overclaim"
copy_valid_repo "${negated_then_subordinate_overclaim_repo}"
printf '%s\n' "Generated files do not confirm GA readiness; screenshots prove customer portal readiness." >>"${negated_then_subordinate_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${negated_then_subordinate_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  secret_text="${fixture#*::}"
  bare_secret_value_repo="${workdir}/bare-secret-value-${fixture_name}"
  copy_valid_repo "${bare_secret_value_repo}"
  printf '%s\n' "${secret_text}" >>"${bare_secret_value_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${bare_secret_value_repo}" "production secret-looking value detected"
done <<'EOF'
bearer::Bearer eyJhbGciOiJIUzI1NiJ9.abcdefghijklmnop.signaturevalue
jwt::eyJhbGciOiJIUzI1NiJ9.abcdefghijklmnop.signaturevalue
basic::Basic QWxhZGRpbjpvcGVuIHNlc2FtZQ==
EOF

safe_bearer_posture_repo="${workdir}/safe-bearer-posture"
copy_valid_repo "${safe_bearer_posture_repo}"
printf '%s\n' "Bearer tokens are redacted before evidence is committed." >>"${safe_bearer_posture_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${safe_bearer_posture_repo}"

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

while IFS= read -r fixture; do
  fixture_name="${fixture%%::*}"
  evidence_line="${fixture#*::}"
  customer_private_rule_leak_repo="${workdir}/customer-private-rule-leak-${fixture_name}"
  copy_valid_repo "${customer_private_rule_leak_repo}"
  printf '%s\n' "${evidence_line}" >>"${customer_private_rule_leak_repo}/docs/phase-66-5-report-export-rc-proof.md"
  assert_fails_with "${customer_private_rule_leak_repo}" "customer-private data detected"
done <<'EOF'
stored::Customer-private data fails the proof and is stored in the report.
stores::The proof must reject customer-private data but stores it here.
EOF

safe_customer_private_rule_repo="${workdir}/safe-customer-private-rule"
copy_valid_repo "${safe_customer_private_rule_repo}"
printf '%s\n' "The proof must reject customer-private data." >>"${safe_customer_private_rule_repo}/docs/phase-66-5-report-export-rc-proof.md"
printf '%s\n' "Customer-private data fails the proof." >>"${safe_customer_private_rule_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${safe_customer_private_rule_repo}"

redacted_then_customer_private_leak_repo="${workdir}/redacted-then-customer-private-leak"
copy_valid_repo "${redacted_then_customer_private_leak_repo}"
printf '%s\n' "redaction_posture: secrets redacted, credentials redacted, customer-private data redacted; customer-private tickets are stored in the proof, workstation-local paths redacted, pii redacted." >>"${redacted_then_customer_private_leak_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${redacted_then_customer_private_leak_repo}" "customer-private data detected"

raw_customer_data_stored_repo="${workdir}/raw-customer-data-stored"
copy_valid_repo "${raw_customer_data_stored_repo}"
printf '%s\n' "Raw customer data is stored in the proof." >>"${raw_customer_data_stored_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${raw_customer_data_stored_repo}" "customer-private data detected"

raw_customer_data_included_repo="${workdir}/raw-customer-data-included"
copy_valid_repo "${raw_customer_data_included_repo}"
printf '%s\n' "Raw customer data was included in the proof." >>"${raw_customer_data_included_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${raw_customer_data_included_repo}" "customer-private data detected"

comment_customer_private_repo="${workdir}/comment-customer-private"
copy_valid_repo "${comment_customer_private_repo}"
printf '%s\n' "<!-- customer-private ticket export -->" >>"${comment_customer_private_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${comment_customer_private_repo}" "customer-private data detected"

wrapped_readme_claim_repo="${workdir}/wrapped-readme-claim"
copy_valid_repo "${wrapped_readme_claim_repo}"
printf '%s\n%s\n' "Phase 66.5 report export" "is GA ready." >>"${wrapped_readme_claim_repo}/README.md"
assert_fails_with "${wrapped_readme_claim_repo}" "Forbidden Phase 66.5 README claim matched"

pronoun_readme_claim_repo="${workdir}/pronoun-readme-claim"
copy_valid_repo "${pronoun_readme_claim_repo}"
printf '%s\n' "The Phase 66.5 report export proof proves GA readiness." >>"${pronoun_readme_claim_repo}/README.md"
assert_fails_with "${pronoun_readme_claim_repo}" "Forbidden Phase 66.5 README claim matched"

markdown_readme_claim_repo="${workdir}/markdown-readme-claim"
copy_valid_repo "${markdown_readme_claim_repo}"
printf '%s\n' "The Phase **66.5** report export proof **confirms** GA readiness." >>"${markdown_readme_claim_repo}/README.md"
assert_fails_with "${markdown_readme_claim_repo}" "Forbidden Phase 66.5 README claim matched"

future_phase_readme_claim_repo="${workdir}/future-phase-readme-claim"
copy_valid_repo "${future_phase_readme_claim_repo}"
printf '%s\n' "The Phase 67 proof proves GA readiness." >>"${future_phase_readme_claim_repo}/README.md"
assert_passes "${future_phase_readme_claim_repo}"

mixed_phase_readme_claim_repo="${workdir}/mixed-phase-readme-claim"
copy_valid_repo "${mixed_phase_readme_claim_repo}"
printf '%s\n' "The Phase 67 proof proves GA readiness. Phase 66.5 remains RC evidence only." >>"${mixed_phase_readme_claim_repo}/README.md"
assert_passes "${mixed_phase_readme_claim_repo}"

unscoped_readme_claim_repo="${workdir}/unscoped-readme-claim"
copy_valid_repo "${unscoped_readme_claim_repo}"
printf '%s\n' "This proof proves GA readiness." >>"${unscoped_readme_claim_repo}/README.md"
assert_passes "${unscoped_readme_claim_repo}"

safe_pronoun_readme_repo="${workdir}/safe-pronoun-readme"
copy_valid_repo "${safe_pronoun_readme_repo}"
printf '%s\n' "This proof does not prove GA readiness." >>"${safe_pronoun_readme_repo}/README.md"
assert_passes "${safe_pronoun_readme_repo}"

safe_limitation_repo="${workdir}/safe-limitation"
copy_valid_repo "${safe_limitation_repo}"
printf '%s\n' "Phase 66.5 records that report authority over AegisOps records remains out of scope." >>"${safe_limitation_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_passes "${safe_limitation_repo}"

run_assertions
echo "Phase 66.5 report export RC proof verifier self-test passed."
