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

mutable_revision_repo="${workdir}/mutable-revision"
copy_valid_repo "${mutable_revision_repo}"
printf '%s\n' "repository_revision: origin/main" >>"${mutable_revision_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${mutable_revision_repo}" "mutable repository revision detected"

hash_with_branch_repo="${workdir}/hash-with-branch"
copy_valid_repo "${hash_with_branch_repo}"
printf '%s\n' "repository_revision: 0123456789abcdef0123456789abcdef01234567 on origin/main" >>"${hash_with_branch_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${hash_with_branch_repo}" "mutable repository revision detected"

source_record_shortcut_repo="${workdir}/source-record-shortcut"
copy_valid_repo "${source_record_shortcut_repo}"
printf '%s\n' "source_record_references: report text" >>"${source_record_shortcut_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${source_record_shortcut_repo}" "invalid source record reference detected"

section_authority_repo="${workdir}/section-authority"
copy_valid_repo "${section_authority_repo}"
printf '%s\n' "case_section_reference: case closed by report" >>"${section_authority_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${section_authority_repo}" "report section authority detected"

missing_labels_repo="${workdir}/missing-labels"
copy_valid_repo "${missing_labels_repo}"
printf '%s\n' "rc_label_set: without labels" >>"${missing_labels_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${missing_labels_repo}" "invalid RC label set detected"

bad_redaction_repo="${workdir}/bad-redaction"
copy_valid_repo "${bad_redaction_repo}"
printf '%s\n' "redaction_posture: not_needed" >>"${bad_redaction_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${bad_redaction_repo}" "invalid redaction posture detected"

report_truth_repo="${workdir}/report-truth"
copy_valid_repo "${report_truth_repo}"
printf '%s\n' "Report output is workflow truth." >>"${report_truth_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_truth_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

report_closes_case_repo="${workdir}/report-closes-case"
copy_valid_repo "${report_closes_case_repo}"
printf '%s\n' "Report output closes cases." >>"${report_closes_case_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${report_closes_case_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

rc_overclaim_repo="${workdir}/rc-overclaim"
copy_valid_repo "${rc_overclaim_repo}"
printf '%s\n' "Phase 66.5 proves release-candidate readiness." >>"${rc_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${rc_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

ga_overclaim_repo="${workdir}/ga-overclaim"
copy_valid_repo "${ga_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms GA readiness." >>"${ga_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${ga_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

compliance_overclaim_repo="${workdir}/compliance-overclaim"
copy_valid_repo "${compliance_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms compliance certification." >>"${compliance_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${compliance_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

portal_overclaim_repo="${workdir}/portal-overclaim"
copy_valid_repo "${portal_overclaim_repo}"
printf '%s\n' "Phase 66.5 confirms customer portal readiness." >>"${portal_overclaim_repo}/docs/phase-66-5-report-export-rc-proof.md"
assert_fails_with "${portal_overclaim_repo}" "Forbidden Phase 66.5 report export RC proof claim matched"

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
