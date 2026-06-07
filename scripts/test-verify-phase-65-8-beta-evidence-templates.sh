#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-8-beta-evidence-templates.sh"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

copy_repo_path() {
  local target="$1"
  local relative_path="$2"

  mkdir -p "${target}/$(dirname "${relative_path}")"
  cp -p "${repo_root}/${relative_path}" "${target}/${relative_path}"
}

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
  copy_repo_path "${target}" "docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
  copy_repo_path "${target}" "scripts/verify-phase-65-8-beta-evidence-templates.sh"
}

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

  if ! grep -Fq -- "${expected}" "${fail_stderr}"; then
    echo "Expected failure output to contain: ${expected}" >&2
    cat "${fail_stdout}" >&2
    cat "${fail_stderr}" >&2
    exit 1
  fi
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_beta_template_repo="${workdir}/missing-beta-template"
create_valid_repo "${missing_beta_template_repo}"
rm "${missing_beta_template_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${missing_beta_template_repo}" "Missing Phase 65.8 beta known-limitations template"

missing_design_partner_template_repo="${workdir}/missing-design-partner-template"
create_valid_repo "${missing_design_partner_template_repo}"
rm "${missing_design_partner_template_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${missing_design_partner_template_repo}" "Missing Phase 65.8 design-partner evidence template"

missing_owner_repo="${workdir}/missing-owner"
create_valid_repo "${missing_owner_repo}"
perl -0pi -e 's/\| Template owner \| `<named-owner>` \|\n//' "${missing_owner_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${missing_owner_repo}" 'Missing Phase 65.8 beta known-limitations template required statement: | Template owner | `<named-owner>` |'

missing_review_date_repo="${workdir}/missing-review-date"
create_valid_repo "${missing_review_date_repo}"
perl -0pi -e 's/\| Review date \| `<YYYY-MM-DD>` \|\n//' "${missing_review_date_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${missing_review_date_repo}" 'Missing Phase 65.8 design-partner evidence template required statement: | Review date | `<YYYY-MM-DD>` |'

missing_limitation_reference_repo="${workdir}/missing-limitation-reference"
create_valid_repo "${missing_limitation_reference_repo}"
perl -0pi -e 's/limitation reference/limitation pointer/g' "${missing_limitation_reference_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${missing_limitation_reference_repo}" "Missing Phase 65.8 beta known-limitations template required statement: limitation reference"

missing_evidence_reference_repo="${workdir}/missing-evidence-reference"
create_valid_repo "${missing_evidence_reference_repo}"
perl -0pi -e 's/evidence reference/evidence pointer/g' "${missing_evidence_reference_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${missing_evidence_reference_repo}" "Missing Phase 65.8 design-partner evidence template required statement: evidence reference"

missing_blocker_disposition_repo="${workdir}/missing-blocker-disposition"
create_valid_repo "${missing_blocker_disposition_repo}"
perl -0pi -e 's/Blocker disposition/Blocker state/g' "${missing_blocker_disposition_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${missing_blocker_disposition_repo}" "Missing Phase 65.8 beta known-limitations template required statement: Blocker disposition"

support_bundle_completion_repo="${workdir}/support-bundle-completion"
create_valid_repo "${support_bundle_completion_repo}"
printf '%s\n' "Support bundle evidence is complete for RC." >>"${support_bundle_completion_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${support_bundle_completion_repo}" "Forbidden Phase 65.8 template claim: Support bundle evidence is complete for RC."

support_bundle_completion_short_repo="${workdir}/support-bundle-completion-short"
create_valid_repo "${support_bundle_completion_short_repo}"
printf '%s\n' "Support bundle evidence is complete." >>"${support_bundle_completion_short_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${support_bundle_completion_short_repo}" "Forbidden Phase 65.8 template claim matched:"

rc_overclaim_repo="${workdir}/rc-overclaim"
create_valid_repo "${rc_overclaim_repo}"
printf '%s\n' "Phase 65.8 proves release-candidate readiness." >>"${rc_overclaim_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${rc_overclaim_repo}" "Forbidden Phase 65.8 template claim: Phase 65.8 proves release-candidate readiness."

rc_reordered_overclaim_repo="${workdir}/rc-reordered-overclaim"
create_valid_repo "${rc_reordered_overclaim_repo}"
printf '%s\n' "Phase 65.8 proves readiness for RC." >>"${rc_reordered_overclaim_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${rc_reordered_overclaim_repo}" "Forbidden Phase 65.8 template claim matched:"

ga_overclaim_repo="${workdir}/ga-overclaim"
create_valid_repo "${ga_overclaim_repo}"
printf '%s\n' "Phase 65.8 proves GA readiness." >>"${ga_overclaim_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${ga_overclaim_repo}" "Forbidden Phase 65.8 template claim: Phase 65.8 proves GA readiness."

commercial_overclaim_repo="${workdir}/commercial-overclaim"
create_valid_repo "${commercial_overclaim_repo}"
printf '%s\n' "AegisOps is commercially replacement ready." >>"${commercial_overclaim_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${commercial_overclaim_repo}" "Forbidden Phase 65.8 template claim: AegisOps is commercially replacement ready."

verifier_truth_repo="${workdir}/verifier-truth"
create_valid_repo "${verifier_truth_repo}"
printf '%s\n' "Verifier output is readiness truth." >>"${verifier_truth_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${verifier_truth_repo}" "Forbidden Phase 65.8 template claim: Verifier output is readiness truth."

customer_private_repo="${workdir}/customer-private"
create_valid_repo "${customer_private_repo}"
printf '%s\n' "The template includes customer private ticket data." >>"${customer_private_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${customer_private_repo}" "Forbidden Phase 65.8 template customer-private data"

unredacted_customer_repo="${workdir}/unredacted-customer"
create_valid_repo "${unredacted_customer_repo}"
printf '%s\n' "The template includes unredacted customer ticket data." >>"${unredacted_customer_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${unredacted_customer_repo}" "Forbidden Phase 65.8 template customer-private data"

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
printf '%s\n' "api_key = abc123" >>"${secret_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${secret_repo}" "Forbidden Phase 65.8 template production secret material"

backticked_secret_repo="${workdir}/backticked-secret"
create_valid_repo "${backticked_secret_repo}"
printf '%s\n' 'api_key = `abc123`' >>"${backticked_secret_repo}/docs/deployment/release/phase-65-8-design-partner-evidence-template.md"
assert_fails_with "${backticked_secret_repo}" "Forbidden Phase 65.8 template production secret material"

commented_date_repo="${workdir}/commented-date"
create_valid_repo "${commented_date_repo}"
perl -0pi -e 's/^- \*\*Date\*\*: 2026-06-07$/<!--\\n- **Date**: 2026-06-07\\n-->/m' "${commented_date_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${commented_date_repo}" "Missing or invalid Phase 65.8 beta known-limitations template date line"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
workstation_path="/""Users/example/design-partner-evidence.md"
printf '%s\n' "${workstation_path}" >>"${workstation_path_repo}/docs/deployment/release/phase-65-8-beta-known-limitations-template.md"
assert_fails_with "${workstation_path_repo}" "Forbidden Phase 65.8 template workstation-local absolute path"

echo "Phase 65.8 beta evidence template verifier self-test passed"
