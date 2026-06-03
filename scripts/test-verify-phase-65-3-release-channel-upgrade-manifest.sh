#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh"

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
  copy_repo_path "${target}" "docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
  copy_repo_path "${target}" "docs/release/phase-65-beta-release-notes.md"
  copy_repo_path "${target}" "docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
}

assert_passes() {
  local target="$1"

  if ! PHASE_65_3_REVISION_REPO_ROOT="${repo_root}" bash "${verifier}" "${target}" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass for ${target}" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local target="$1"
  local expected="$2"

  if PHASE_65_3_REVISION_REPO_ROOT="${repo_root}" bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
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

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${missing_contract_repo}" "Missing Phase 65.3 release channel and upgrade manifest contract"

missing_manifest_repo="${workdir}/missing-manifest"
create_valid_repo "${missing_manifest_repo}"
rm "${missing_manifest_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_manifest_repo}" "Missing Phase 65.3 upgrade manifest artifact"

missing_readme_repo="${workdir}/missing-readme"
create_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 65\.3 release channel and upgrade manifest contract\]\(docs\/phase-65-3-release-channel-upgrade-manifest-contract\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical cross-phase boundary bullet"

missing_doc_source_repo="${workdir}/missing-doc-source-version"
create_valid_repo "${missing_doc_source_repo}"
remove_doc_text "${missing_doc_source_repo}" "- missing source version;"
assert_fails_with "${missing_doc_source_repo}" "Missing required Phase 65.3 contract term"

missing_release_notes_repo="${workdir}/missing-release-notes"
create_valid_repo "${missing_release_notes_repo}"
rm "${missing_release_notes_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${missing_release_notes_repo}" "Missing Phase 65.3 release notes reference"

forbidden_release_notes_repo="${workdir}/forbidden-release-notes"
create_valid_repo "${forbidden_release_notes_repo}"
printf '%s\n' "Hosted update service readiness is complete." >>"${forbidden_release_notes_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${forbidden_release_notes_repo}" "hosted update-service claim"

missing_channel_scope_repo="${workdir}/missing-channel-scope"
create_valid_repo "${missing_channel_scope_repo}"
perl -0pi -e 's/^channel_scope:.*\n//m' "${missing_channel_scope_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_channel_scope_repo}" "Missing Phase 65.3 upgrade manifest value: channel_scope"

missing_approval_record_repo="${workdir}/missing-approval-record"
create_valid_repo "${missing_approval_record_repo}"
perl -0pi -e 's/^approval_record:.*\n//m' "${missing_approval_record_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_approval_record_repo}" "Missing Phase 65.3 upgrade manifest value: approval_record"

true_non_claim_repo="${workdir}/true-non-claim"
create_valid_repo "${true_non_claim_repo}"
perl -0pi -e 's/^  silent_auto_upgrade: false$/  silent_auto_upgrade: true/m' "${true_non_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${true_non_claim_repo}" "Invalid Phase 65.3 upgrade manifest value: silent_auto_upgrade"

placeholder_revision_repo="${workdir}/placeholder-revision"
create_valid_repo "${placeholder_revision_repo}"
perl -0pi -e 's/^repository_revision:.*$/repository_revision: <repository-revision>/m' "${placeholder_revision_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${placeholder_revision_repo}" "Missing Phase 65.3 upgrade manifest value: repository_revision"

unresolved_revision_repo="${workdir}/unresolved-revision"
create_valid_repo "${unresolved_revision_repo}"
perl -0pi -e 's/^release_bundle_identifier:.*$/release_bundle_identifier: aegisops-beta-deadbeef1234/m; s/^repository_revision:.*$/repository_revision: deadbeef1234/m; s/^    target_version:.*$/    target_version: aegisops-beta-deadbeef1234/mg' "${unresolved_revision_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${unresolved_revision_repo}" "Invalid Phase 65.3 upgrade manifest repository revision"

missing_source_repo="${workdir}/missing-source-version"
create_valid_repo "${missing_source_repo}"
perl -0pi -e 's/^[[:space:]]*source_version:.*\n//mg' "${missing_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_source_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

missing_one_case_source_repo="${workdir}/missing-one-case-source-version"
create_valid_repo "${missing_one_case_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed\n//m' "${missing_one_case_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_one_case_source_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

missing_target_repo="${workdir}/missing-target-version"
create_valid_repo "${missing_target_repo}"
perl -0pi -e 's/^[[:space:]]*target_version:.*\n//mg' "${missing_target_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_target_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.target_version"

missing_compatibility_repo="${workdir}/missing-compatibility"
create_valid_repo "${missing_compatibility_repo}"
perl -0pi -e 's/^[[:space:]]*compatibility_posture:.*\n//mg' "${missing_compatibility_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_compatibility_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.compatibility_posture"

missing_incompatible_repo="${workdir}/missing-incompatible"
create_valid_repo "${missing_incompatible_repo}"
perl -0pi -e 's/^[[:space:]]*compatibility_posture: incompatible\n//m' "${missing_incompatible_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_incompatible_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: incompatible-unreviewed-source.compatibility_posture"

missing_rollback_repo="${workdir}/missing-rollback"
create_valid_repo "${missing_rollback_repo}"
perl -0pi -e 's/^[[:space:]]*rollback_expectation:.*\n//mg' "${missing_rollback_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_rollback_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.rollback_expectation"

missing_required_checks_repo="${workdir}/missing-required-checks"
create_valid_repo "${missing_required_checks_repo}"
perl -0pi -e 's/^[[:space:]]*required_checks:\n(?:[[:space:]]*-[^\n]*\n)+//mg' "${missing_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_required_checks_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.required_checks"

empty_required_checks_repo="${workdir}/empty-required-checks"
create_valid_repo "${empty_required_checks_repo}"
perl -0pi -e 's/^    required_checks:\n(?:      -[^\n]*\n)+/    required_checks:\n/mg' "${empty_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${empty_required_checks_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.required_checks"

missing_limitations_repo="${workdir}/missing-limitations"
create_valid_repo "${missing_limitations_repo}"
perl -0pi -e 's/^[[:space:]]*known_limitation_references:\n(?:[[:space:]]*-[^\n]*\n)+//mg' "${missing_limitations_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_limitations_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.known_limitation_references"

empty_limitations_repo="${workdir}/empty-limitations"
create_valid_repo "${empty_limitations_repo}"
perl -0pi -e 's/^    known_limitation_references:\n(?:      -[^\n]*\n)+/    known_limitation_references:\n/mg' "${empty_limitations_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${empty_limitations_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.known_limitation_references"

external_phase58_reference_repo="${workdir}/external-phase58-reference"
create_valid_repo "${external_phase58_reference_repo}"
perl -0pi -e 's#^    phase58_upgrade_plan_reference:.*$#    phase58_upgrade_plan_reference: https://example.invalid/phase-58-ticket#m' "${external_phase58_reference_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${external_phase58_reference_repo}" "Invalid Phase 65.3 upgrade manifest Phase 58 reference: compatible-reviewed-source"

silent_upgrade_repo="${workdir}/silent-upgrade"
create_valid_repo "${silent_upgrade_repo}"
printf '%s\n' "Silent auto-upgrade is enabled for compatible versions." >>"${silent_upgrade_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${silent_upgrade_repo}" "silent auto-upgrade or automatic migration claim"

mixed_silent_upgrade_repo="${workdir}/mixed-silent-upgrade"
create_valid_repo "${mixed_silent_upgrade_repo}"
printf '%s\n' "This contract does not claim hosted update service readiness and silent auto-upgrade is enabled after install." >>"${mixed_silent_upgrade_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${mixed_silent_upgrade_repo}" "positive claim after negated boundary detected"

hosted_update_repo="${workdir}/hosted-update"
create_valid_repo "${hosted_update_repo}"
printf '%s\n' "Hosted update service readiness is complete." >>"${hosted_update_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${hosted_update_repo}" "hosted update-service claim"

rc_claim_repo="${workdir}/rc-claim"
create_valid_repo "${rc_claim_repo}"
printf '%s\n' "Upgrade manifest proves RC readiness." >>"${rc_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${rc_claim_repo}" "inferred RC/GA readiness claim"

ga_claim_repo="${workdir}/ga-claim"
create_valid_repo "${ga_claim_repo}"
printf '%s\n' "Release-channel metadata proves GA readiness." >>"${ga_claim_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${ga_claim_repo}" "inferred RC/GA readiness claim"

truth_claim_repo="${workdir}/truth-claim"
create_valid_repo "${truth_claim_repo}"
printf '%s\n' "The manifest is upgrade truth." >>"${truth_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${truth_claim_repo}" "metadata, manifest, verifier, or issue-lint truth claim"

path_repo="${workdir}/path"
create_valid_repo "${path_repo}"
home_path="/""Users/example/aegisops"
printf '%s\n' "Retain evidence under ${home_path}." >>"${path_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${path_repo}" "workstation-local absolute path"

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
printf '%s\n' "api_key: actual-production-token" >>"${secret_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${secret_repo}" "production secret-looking value"

echo "Phase 65.3 release channel and upgrade manifest verifier self-test passed."
