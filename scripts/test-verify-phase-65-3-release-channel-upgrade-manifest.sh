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
  copy_repo_path "${target}" "docs/phase-65-1-release-bundle-inventory.md"
  copy_repo_path "${target}" "docs/phase-65-2-offline-install-bundle-contract.md"
  copy_repo_path "${target}" "docs/phase-58-5-upgrade-rollback-plan-contract.md"
  copy_repo_path "${target}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  copy_repo_path "${target}" "docs/phase-64-5-phase66-limitation-handoff.md"
  copy_repo_path "${target}" "docs/release/phase-65-beta-release-notes.md"
  copy_repo_path "${target}" "docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
  copy_repo_path "${target}" "scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh"
  copy_repo_path "${target}" "scripts/verify-publishable-path-hygiene.sh"
  copy_repo_path "${target}" "scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh"
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

  assert_fails_with_revision_repo "${target}" "${expected}" "${repo_root}"
}

assert_fails_with_revision_repo() {
  local target="$1"
  local expected="$2"
  local revision_root="$3"

  if PHASE_65_3_REVISION_REPO_ROOT="${revision_root}" bash "${verifier}" "${target}" >"${fail_stdout}" 2>"${fail_stderr}"; then
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

create_revision_repo_with_unreachable_commit() {
  local target="$1"
  local initial_branch

  git init -q "${target}"
  git -C "${target}" config user.email "phase-65-3-test@example.invalid"
  git -C "${target}" config user.name "Phase 65.3 Test"
  printf '%s\n' "current package head" >"${target}/package-head.txt"
  git -C "${target}" add package-head.txt
  git -C "${target}" commit -q -m "current package head"
  initial_branch="$(git -C "${target}" symbolic-ref --short HEAD)"
  git -C "${target}" checkout -q --orphan unreachable-source
  git -C "${target}" rm -q -rf .
  printf '%s\n' "unreachable source revision" >"${target}/source.txt"
  git -C "${target}" add source.txt
  git -C "${target}" commit -q -m "unreachable source revision"
  git -C "${target}" rev-parse HEAD
  git -C "${target}" checkout -q "${initial_branch}"
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

wrong_release_notes_repo="${workdir}/wrong-release-notes-reference"
create_valid_repo "${wrong_release_notes_repo}"
perl -0pi -e 's#^release_notes_reference:.*$#release_notes_reference: docs/phase-65-3-release-channel-upgrade-manifest-contract.md#m' "${wrong_release_notes_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${wrong_release_notes_repo}" "Invalid Phase 65.3 upgrade manifest release notes reference"

traversal_release_notes_repo="${workdir}/traversal-release-notes-reference"
create_valid_repo "${traversal_release_notes_repo}"
printf '%s\n' "# Fake Release Notes" >"${traversal_release_notes_repo}/scripts/fake-release-notes.md"
perl -0pi -e 's#^release_notes_reference:.*$#release_notes_reference: docs/release/../../scripts/fake-release-notes.md#m' "${traversal_release_notes_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${traversal_release_notes_repo}" "Invalid Phase 65.3 upgrade manifest release notes reference"

readiness_release_notes_repo="${workdir}/readiness-release-notes-reference"
create_valid_repo "${readiness_release_notes_repo}"
printf '%s\n' "# Production Readiness Release Notes" >"${readiness_release_notes_repo}/docs/release/production-readiness-release-notes.md"
perl -0pi -e 's#^release_notes_reference:.*$#release_notes_reference: docs/release/production-readiness-release-notes.md#m' "${readiness_release_notes_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${readiness_release_notes_repo}" "Invalid Phase 65.3 upgrade manifest release notes reference"

mixed_case_readiness_release_notes_repo="${workdir}/mixed-case-readiness-release-notes-reference"
create_valid_repo "${mixed_case_readiness_release_notes_repo}"
printf '%s\n' "# Production Readiness Release Notes" >"${mixed_case_readiness_release_notes_repo}/docs/release/production-Readiness-release-notes.md"
perl -0pi -e 's#^release_notes_reference:.*$#release_notes_reference: docs/release/production-Readiness-release-notes.md#m' "${mixed_case_readiness_release_notes_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${mixed_case_readiness_release_notes_repo}" "Invalid Phase 65.3 upgrade manifest release notes reference"

forbidden_release_notes_repo="${workdir}/forbidden-release-notes"
create_valid_repo "${forbidden_release_notes_repo}"
printf '%s\n' "Hosted update service readiness is complete." >>"${forbidden_release_notes_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${forbidden_release_notes_repo}" "hosted update-service claim"

missing_inventory_reference_repo="${workdir}/missing-inventory-reference"
create_valid_repo "${missing_inventory_reference_repo}"
rm "${missing_inventory_reference_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with "${missing_inventory_reference_repo}" "Missing Phase 65.1 release bundle inventory reference"

missing_offline_bundle_reference_repo="${workdir}/missing-offline-bundle-reference"
create_valid_repo "${missing_offline_bundle_reference_repo}"
rm "${missing_offline_bundle_reference_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "${missing_offline_bundle_reference_repo}" "Missing Phase 65.2 offline install bundle contract reference"

missing_phase58_check_script_repo="${workdir}/missing-phase58-check-script"
create_valid_repo "${missing_phase58_check_script_repo}"
rm "${missing_phase58_check_script_repo}/scripts/verify-phase-58-5-upgrade-rollback-plan-contract.sh"
assert_fails_with "${missing_phase58_check_script_repo}" "Missing Phase 58.5 upgrade and rollback verifier script reference"

missing_path_hygiene_check_script_repo="${workdir}/missing-path-hygiene-check-script"
create_valid_repo "${missing_path_hygiene_check_script_repo}"
rm "${missing_path_hygiene_check_script_repo}/scripts/verify-publishable-path-hygiene.sh"
assert_fails_with "${missing_path_hygiene_check_script_repo}" "Missing publishable path hygiene verifier script reference"

missing_phase65_check_script_repo="${workdir}/missing-phase65-check-script"
create_valid_repo "${missing_phase65_check_script_repo}"
rm "${missing_phase65_check_script_repo}/scripts/verify-phase-65-3-release-channel-upgrade-manifest.sh"
assert_fails_with "${missing_phase65_check_script_repo}" "Missing Phase 65.3 release channel and upgrade manifest verifier script reference"

missing_channel_scope_repo="${workdir}/missing-channel-scope"
create_valid_repo "${missing_channel_scope_repo}"
perl -0pi -e 's/^channel_scope:.*\n//m' "${missing_channel_scope_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_channel_scope_repo}" "Missing Phase 65.3 upgrade manifest value: channel_scope"

missing_approval_record_repo="${workdir}/missing-approval-record"
create_valid_repo "${missing_approval_record_repo}"
perl -0pi -e 's/^approval_record:.*\n//m' "${missing_approval_record_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_approval_record_repo}" "Missing Phase 65.3 upgrade manifest value: approval_record"

duplicate_channel_repo="${workdir}/duplicate-release-channel"
create_valid_repo "${duplicate_channel_repo}"
printf '%s\n' "release_channel: ga" >>"${duplicate_channel_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${duplicate_channel_repo}" "Invalid Phase 65.3 upgrade manifest value: release_channel"

release_channel_override_repo="${workdir}/release-channel-override"
create_valid_repo "${release_channel_override_repo}"
printf '%s\n' "release_channel_override: production" >>"${release_channel_override_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${release_channel_override_repo}" "Invalid Phase 65.3 upgrade manifest top-level field: release_channel_override"

nested_channel_repo="${workdir}/nested-release-channel"
create_valid_repo "${nested_channel_repo}"
perl -0pi -e 's/^release_channel:.*\n//m; s/^non_claims:\n/non_claims:\n  release_channel: beta-design-partner\n/m' "${nested_channel_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${nested_channel_repo}" "Missing Phase 65.3 upgrade manifest value: release_channel"

nested_channel_scope_repo="${workdir}/nested-channel-scope"
create_valid_repo "${nested_channel_scope_repo}"
perl -0pi -e 's/^channel_scope:.*\n//m; s/^non_claims:\n/non_claims:\n  channel_scope: beta\/design-partner packaging review only; not RC, GA, production rollout, entitlement, billing, support readiness, or commercial replacement readiness.\n/m' "${nested_channel_scope_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${nested_channel_scope_repo}" "Missing Phase 65.3 upgrade manifest value: channel_scope"

true_non_claim_repo="${workdir}/true-non-claim"
create_valid_repo "${true_non_claim_repo}"
perl -0pi -e 's/^  silent_auto_upgrade: false$/  silent_auto_upgrade: true/m' "${true_non_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${true_non_claim_repo}" "Invalid Phase 65.3 upgrade manifest value: silent_auto_upgrade"

top_level_non_claim_repo="${workdir}/top-level-non-claim"
create_valid_repo "${top_level_non_claim_repo}"
perl -0pi -e 's/^  silent_auto_upgrade: false\n//m; s/^non_claims:\n/non_claims:\n/m; s/^compatibility_cases:\n/silent_auto_upgrade: false\ncompatibility_cases:\n/m' "${top_level_non_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${top_level_non_claim_repo}" "Invalid Phase 65.3 upgrade manifest top-level field: silent_auto_upgrade"

missing_non_claims_block_repo="${workdir}/missing-non-claims-block"
create_valid_repo "${missing_non_claims_block_repo}"
perl -0pi -e 's/^non_claims:\n(?:  [a-z_]+: false\n)+//m' "${missing_non_claims_block_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_non_claims_block_repo}" "Missing Phase 65.3 upgrade manifest value: non_claims"

extra_true_non_claim_repo="${workdir}/extra-true-non-claim"
create_valid_repo "${extra_true_non_claim_repo}"
perl -0pi -e 's/^non_claims:\n/non_claims:\n  production_rollout_readiness: true\n/m' "${extra_true_non_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${extra_true_non_claim_repo}" "Invalid Phase 65.3 upgrade manifest value: production_rollout_readiness"

for non_claim_key in \
  hosted_update_service \
  automatic_migration \
  automatic_rollback \
  rc_readiness \
  ga_readiness \
  commercial_replacement_readiness; do
  true_non_claim_repo="${workdir}/true-non-claim-${non_claim_key}"
  create_valid_repo "${true_non_claim_repo}"
  perl -0pi -e "s/^  ${non_claim_key}: false$/  ${non_claim_key}: true/m" "${true_non_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
  assert_fails_with "${true_non_claim_repo}" "Invalid Phase 65.3 upgrade manifest value: ${non_claim_key}"
done

duplicate_non_claim_repo="${workdir}/duplicate-non-claim"
create_valid_repo "${duplicate_non_claim_repo}"
printf '%s\n' "  silent_auto_upgrade: true" >>"${duplicate_non_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${duplicate_non_claim_repo}" "Invalid Phase 65.3 upgrade manifest value: silent_auto_upgrade"

placeholder_revision_repo="${workdir}/placeholder-revision"
create_valid_repo "${placeholder_revision_repo}"
perl -0pi -e 's/^repository_revision:.*$/repository_revision: <repository-revision>/m' "${placeholder_revision_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${placeholder_revision_repo}" "Missing Phase 65.3 upgrade manifest value: repository_revision"

unresolved_revision_repo="${workdir}/unresolved-revision"
create_valid_repo "${unresolved_revision_repo}"
perl -0pi -e 's/^release_bundle_identifier:.*$/release_bundle_identifier: aegisops-beta-deadbeef1234/m; s/^repository_revision:.*$/repository_revision: deadbeef1234/m; s/^    target_version:.*$/    target_version: aegisops-beta-deadbeef1234/mg' "${unresolved_revision_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${unresolved_revision_repo}" "Invalid Phase 65.3 upgrade manifest repository revision"

unreachable_revision_git_repo="${workdir}/revision-repo"
unreachable_revision="$(create_revision_repo_with_unreachable_commit "${unreachable_revision_git_repo}")"
unreachable_revision_repo="${workdir}/unreachable-revision"
create_valid_repo "${unreachable_revision_repo}"
perl -0pi -e "s/^release_bundle_identifier:.*\$/release_bundle_identifier: aegisops-beta-${unreachable_revision}/m; s/^repository_revision:.*\$/repository_revision: ${unreachable_revision}/m; s/^    target_version:.*\$/    target_version: aegisops-beta-${unreachable_revision}/mg" "${unreachable_revision_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with_revision_repo "${unreachable_revision_repo}" "is not reachable from repository head" "${unreachable_revision_git_repo}"

missing_source_repo="${workdir}/missing-source-version"
create_valid_repo "${missing_source_repo}"
perl -0pi -e 's/^[[:space:]]*source_version:.*\n//mg' "${missing_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_source_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

missing_one_case_source_repo="${workdir}/missing-one-case-source-version"
create_valid_repo "${missing_one_case_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed\n//m' "${missing_one_case_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_one_case_source_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

missing_incompatible_source_repo="${workdir}/missing-incompatible-source-version"
create_valid_repo "${missing_incompatible_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-unreviewed-prior-release\n//m' "${missing_incompatible_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_incompatible_source_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: incompatible-unreviewed-source.source_version"

rc_source_repo="${workdir}/rc-source-version"
create_valid_repo "${rc_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: aegisops-rc-1-reviewed/m' "${rc_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${rc_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

duplicate_source_repo="${workdir}/duplicate-source-version"
create_valid_repo "${duplicate_source_repo}"
perl -0pi -e 's/^  - case_identifier: compatible-reviewed-source$/  - case_identifier: compatible-reviewed-source\n    source_version: beta-only/m' "${duplicate_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${duplicate_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

beta_only_source_repo="${workdir}/beta-only-source-version"
create_valid_repo "${beta_only_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: beta-only/m' "${beta_only_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${beta_only_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

inferred_source_repo="${workdir}/inferred-source-version"
create_valid_repo "${inferred_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: inferred/m' "${inferred_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${inferred_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

floating_source_repo="${workdir}/floating-source-version"
create_valid_repo "${floating_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: develop/m' "${floating_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${floating_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

embedded_branch_source_repo="${workdir}/embedded-branch-source-version"
create_valid_repo "${embedded_branch_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: aegisops-main-reviewed/m' "${embedded_branch_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${embedded_branch_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

latest_qualified_source_repo="${workdir}/latest-qualified-source-version"
create_valid_repo "${latest_qualified_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: aegisops-latest-reviewed/m' "${latest_qualified_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${latest_qualified_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

rc_suffix_source_repo="${workdir}/rc-suffix-source-version"
create_valid_repo "${rc_suffix_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: aegisops-1.0.0-rc1/m' "${rc_suffix_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${rc_suffix_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

block_scalar_source_repo="${workdir}/block-scalar-source-version"
create_valid_repo "${block_scalar_source_repo}"
perl -0pi -e 's/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: |\n      aegisops-0.4.0-reviewed/m; s/^    compatibility_reason: Source version aegisops-0\.4\.0-reviewed/    compatibility_reason: Source version |/m' "${block_scalar_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${block_scalar_source_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

missing_target_repo="${workdir}/missing-target-version"
create_valid_repo "${missing_target_repo}"
perl -0pi -e 's/^[[:space:]]*target_version:.*\n//mg' "${missing_target_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_target_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.target_version"

self_upgrade_source_repo="${workdir}/self-upgrade-source-version"
create_valid_repo "${self_upgrade_source_repo}"
perl -0pi -e 'my ($target) = /^    target_version: (.*)$/m; s/^    source_version: aegisops-0\.4\.0-reviewed$/    source_version: $target/m' "${self_upgrade_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${self_upgrade_source_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.source_version"

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

automatic_rollback_repo="${workdir}/automatic-rollback"
create_valid_repo "${automatic_rollback_repo}"
perl -0pi -e 's/^    rollback_expectation: rollback_owner=aegisops-release-owner; rollback_trigger=failed required checks or release-gate rejection; rollback_target=last-reviewed-release-bundle; rollback_evidence_reference=docs\/phase-58-5-upgrade-rollback-plan-contract.md$/    rollback_expectation: automatic rollback/m' "${automatic_rollback_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${automatic_rollback_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.rollback_expectation"

missing_rollback_evidence_repo="${workdir}/missing-rollback-evidence"
create_valid_repo "${missing_rollback_evidence_repo}"
perl -0pi -e 's/; rollback_evidence_reference=docs\/phase-58-5-upgrade-rollback-plan-contract.md//g' "${missing_rollback_evidence_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_rollback_evidence_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.rollback_expectation"

rollback_only_evidence_repo="${workdir}/rollback-only-evidence"
create_valid_repo "${rollback_only_evidence_repo}"
perl -0pi -e 's/^    rollback_expectation: .*rollback_evidence_reference=docs\/phase-58-5-upgrade-rollback-plan-contract.md$/    rollback_expectation: rollback_evidence_reference=docs\/phase-58-5-upgrade-rollback-plan-contract.md/mg' "${rollback_only_evidence_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${rollback_only_evidence_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.rollback_expectation"

placeholder_rollback_repo="${workdir}/placeholder-rollback-subfields"
create_valid_repo "${placeholder_rollback_repo}"
perl -0pi -e 's#rollback_owner=aegisops-release-owner; rollback_trigger=failed required checks or release-gate rejection; rollback_target=last-reviewed-release-bundle#rollback_owner=todo; rollback_trigger=todo; rollback_target=todo#m' "${placeholder_rollback_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${placeholder_rollback_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.rollback_expectation"

sibling_reason_repo="${workdir}/sibling-derived-reason"
create_valid_repo "${sibling_reason_repo}"
perl -0pi -e 's/^    compatibility_reason:.*$/    compatibility_reason: same as previous/mg' "${sibling_reason_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${sibling_reason_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.compatibility_reason"

vague_reason_repo="${workdir}/vague-compatibility-reason"
create_valid_repo "${vague_reason_repo}"
perl -0pi -e 's/^    compatibility_reason:.*$/    compatibility_reason: compatible/mg' "${vague_reason_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${vague_reason_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.compatibility_reason"

unbound_reason_repo="${workdir}/unbound-compatibility-reason"
create_valid_repo "${unbound_reason_repo}"
perl -0pi -e 's/^    compatibility_reason:.*$/    compatibility_reason: Reviewed package evidence exists for upgrade review./mg' "${unbound_reason_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${unbound_reason_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.compatibility_reason"

missing_required_checks_repo="${workdir}/missing-required-checks"
create_valid_repo "${missing_required_checks_repo}"
perl -0pi -e 's/^[[:space:]]*required_checks:\n(?:[[:space:]]*-[^\n]*\n)+//mg' "${missing_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_required_checks_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.required_checks"

empty_required_checks_repo="${workdir}/empty-required-checks"
create_valid_repo "${empty_required_checks_repo}"
perl -0pi -e 's/^    required_checks:\n(?:      -[^\n]*\n)+/    required_checks:\n/mg' "${empty_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${empty_required_checks_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.required_checks"

readiness_required_checks_repo="${workdir}/readiness-required-checks"
create_valid_repo "${readiness_required_checks_repo}"
perl -0pi -e 's/^    required_checks:\n/    required_checks:\n      - bash scripts\/verify-production-readiness.sh\n/mg' "${readiness_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${readiness_required_checks_repo}" "Invalid Phase 65.3 upgrade manifest required check reference: compatible-reviewed-source.required_checks"

duplicate_required_checks_repo="${workdir}/duplicate-required-checks"
create_valid_repo "${duplicate_required_checks_repo}"
perl -0pi -e 's/^    required_checks:\n/    required_checks:\n      - bash scripts\/verify-production-readiness.sh\n    required_checks:\n/m' "${duplicate_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${duplicate_required_checks_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.required_checks"

absolute_required_checks_repo="${workdir}/absolute-required-checks"
create_valid_repo "${absolute_required_checks_repo}"
perl -0pi -e 's#^    required_checks:\n#    required_checks:\n      - bash /tmp/extra-check.sh\n#m' "${absolute_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${absolute_required_checks_repo}" "Invalid Phase 65.3 upgrade manifest required check reference: compatible-reviewed-source.required_checks"

external_required_checks_repo="${workdir}/external-required-checks"
create_valid_repo "${external_required_checks_repo}"
perl -0pi -e 's#^    required_checks:\n#    required_checks:\n      - bash https://example.invalid/extra-check.sh\n#m' "${external_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${external_required_checks_repo}" "Invalid Phase 65.3 upgrade manifest required check reference: compatible-reviewed-source.required_checks"

missing_limitations_repo="${workdir}/missing-limitations"
create_valid_repo "${missing_limitations_repo}"
perl -0pi -e 's/^[[:space:]]*known_limitation_references:\n(?:[[:space:]]*-[^\n]*\n)+//mg' "${missing_limitations_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_limitations_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.known_limitation_references"

empty_limitations_repo="${workdir}/empty-limitations"
create_valid_repo "${empty_limitations_repo}"
perl -0pi -e 's/^    known_limitation_references:\n(?:      -[^\n]*\n)+/    known_limitation_references:\n/mg' "${empty_limitations_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${empty_limitations_repo}" "Missing Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.known_limitation_references"

external_limitation_reference_repo="${workdir}/external-limitation-reference"
create_valid_repo "${external_limitation_reference_repo}"
perl -0pi -e 's#^    known_limitation_references:\n#    known_limitation_references:\n      - https://example.invalid/phase-66-limitation-ticket\n#m' "${external_limitation_reference_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${external_limitation_reference_repo}" "Invalid Phase 65.3 upgrade manifest limitation reference: compatible-reviewed-source.known_limitation_references"

external_phase58_reference_repo="${workdir}/external-phase58-reference"
create_valid_repo "${external_phase58_reference_repo}"
perl -0pi -e 's#^    phase58_upgrade_plan_reference:.*$#    phase58_upgrade_plan_reference: https://example.invalid/phase-58-ticket#m' "${external_phase58_reference_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${external_phase58_reference_repo}" "Invalid Phase 65.3 upgrade manifest Phase 58 reference: compatible-reviewed-source"

external_incompatible_phase58_reference_repo="${workdir}/external-incompatible-phase58-reference"
create_valid_repo "${external_incompatible_phase58_reference_repo}"
perl -0pi -e 's#^    phase58_upgrade_plan_reference:.*$#++$seen == 2 ? "    phase58_upgrade_plan_reference: https://example.invalid/phase-58-ticket" : $&#egm' "${external_incompatible_phase58_reference_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${external_incompatible_phase58_reference_repo}" "Invalid Phase 65.3 upgrade manifest Phase 58 reference: incompatible-unreviewed-source"

external_phase51_reference_repo="${workdir}/external-phase51-reference"
create_valid_repo "${external_phase51_reference_repo}"
perl -0pi -e 's#^    phase51_gate_boundary_reference:.*$#    phase51_gate_boundary_reference: https://example.invalid/phase-51-ticket#m' "${external_phase51_reference_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${external_phase51_reference_repo}" "Invalid Phase 65.3 upgrade manifest Phase 51 reference: compatible-reviewed-source"

duplicate_compatibility_cases_repo="${workdir}/duplicate-compatibility-cases"
create_valid_repo "${duplicate_compatibility_cases_repo}"
printf '%s\n' "compatibility_cases: []" >>"${duplicate_compatibility_cases_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${duplicate_compatibility_cases_repo}" "Invalid Phase 65.3 upgrade manifest content: compatibility cases"

per_case_release_channel_repo="${workdir}/per-case-release-channel"
create_valid_repo "${per_case_release_channel_repo}"
perl -0pi -e 's/^  - case_identifier: compatible-reviewed-source$/  - case_identifier: compatible-reviewed-source\n    release_channel: ga/m' "${per_case_release_channel_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${per_case_release_channel_repo}" "Invalid Phase 65.3 upgrade manifest compatibility case field: compatible-reviewed-source.release_channel"

silent_upgrade_repo="${workdir}/silent-upgrade"
create_valid_repo "${silent_upgrade_repo}"
printf '%s\n' "Silent auto-upgrade is enabled for compatible versions." >>"${silent_upgrade_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${silent_upgrade_repo}" "silent auto-upgrade or automatic migration claim"

silent_upgrade_reordered_repo="${workdir}/silent-upgrade-reordered"
create_valid_repo "${silent_upgrade_reordered_repo}"
printf '%s\n' "Auto-upgrade runs silently." >>"${silent_upgrade_reordered_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${silent_upgrade_reordered_repo}" "silent auto-upgrade or automatic migration claim"

reordered_automatic_migration_repo="${workdir}/reordered-automatic-migration"
create_valid_repo "${reordered_automatic_migration_repo}"
printf '%s\n' "Migration runs automatically after install." >>"${reordered_automatic_migration_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${reordered_automatic_migration_repo}" "silent auto-upgrade or automatic migration claim"

reordered_automatic_rollback_repo="${workdir}/reordered-automatic-rollback"
create_valid_repo "${reordered_automatic_rollback_repo}"
printf '%s\n' "Rollback happens automatically after failed required checks." >>"${reordered_automatic_rollback_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${reordered_automatic_rollback_repo}" "silent auto-upgrade or automatic migration claim"

mixed_silent_upgrade_repo="${workdir}/mixed-silent-upgrade"
create_valid_repo "${mixed_silent_upgrade_repo}"
printf '%s\n' "This contract does not claim hosted update service readiness and silent auto-upgrade is enabled after install." >>"${mixed_silent_upgrade_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${mixed_silent_upgrade_repo}" "positive claim after negated boundary detected"

comma_mixed_silent_upgrade_repo="${workdir}/comma-mixed-silent-upgrade"
create_valid_repo "${comma_mixed_silent_upgrade_repo}"
printf '%s\n' "This contract does not claim hosted update service readiness, silent auto-upgrade is enabled after install." >>"${comma_mixed_silent_upgrade_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${comma_mixed_silent_upgrade_repo}" "positive claim after negated boundary detected"

hosted_update_repo="${workdir}/hosted-update"
create_valid_repo "${hosted_update_repo}"
printf '%s\n' "Hosted update service readiness is complete." >>"${hosted_update_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${hosted_update_repo}" "hosted update-service claim"

hosted_updates_available_repo="${workdir}/hosted-updates-available"
create_valid_repo "${hosted_updates_available_repo}"
printf '%s\n' "Hosted updates are available." >>"${hosted_updates_available_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${hosted_updates_available_repo}" "hosted update-service claim"

rc_claim_repo="${workdir}/rc-claim"
create_valid_repo "${rc_claim_repo}"
printf '%s\n' "Upgrade manifest proves RC readiness." >>"${rc_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${rc_claim_repo}" "inferred RC/GA readiness claim"

ga_claim_repo="${workdir}/ga-claim"
create_valid_repo "${ga_claim_repo}"
printf '%s\n' "Release-channel metadata proves GA readiness." >>"${ga_claim_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${ga_claim_repo}" "inferred RC/GA readiness claim"

direct_rc_ready_repo="${workdir}/direct-rc-ready-claim"
create_valid_repo "${direct_rc_ready_repo}"
printf '%s\n' "Phase 66 RC is ready." >>"${direct_rc_ready_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${direct_rc_ready_repo}" "inferred RC/GA readiness claim"

direct_ga_ready_repo="${workdir}/direct-ga-ready-claim"
create_valid_repo "${direct_ga_ready_repo}"
printf '%s\n' "Phase 67 GA is ready." >>"${direct_ga_ready_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${direct_ga_ready_repo}" "inferred RC/GA readiness claim"

beta_claim_repo="${workdir}/beta-claim"
create_valid_repo "${beta_claim_repo}"
printf '%s\n' "Upgrade manifest proves Beta gate acceptance." >>"${beta_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${beta_claim_repo}" "inferred RC/GA readiness claim"

beta_gate_claimed_repo="${workdir}/beta-gate-claimed"
create_valid_repo "${beta_gate_claimed_repo}"
printf '%s\n' "Beta gate acceptance is claimed." >>"${beta_gate_claimed_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${beta_gate_claimed_repo}" "inferred RC/GA readiness claim"

production_rollout_repo="${workdir}/production-rollout"
create_valid_repo "${production_rollout_repo}"
printf '%s\n' "Production rollout is ready for beta users." >>"${production_rollout_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${production_rollout_repo}" "entitlement, billing, or commercial readiness claim"

reordered_production_rollout_repo="${workdir}/reordered-production-rollout"
create_valid_repo "${reordered_production_rollout_repo}"
printf '%s\n' "Rollout is ready for production." >>"${reordered_production_rollout_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${reordered_production_rollout_repo}" "entitlement, billing, or commercial readiness claim"

reordered_entitlement_repo="${workdir}/reordered-entitlement"
create_valid_repo "${reordered_entitlement_repo}"
printf '%s\n' "Entitlement enforcement is complete for production users." >>"${reordered_entitlement_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${reordered_entitlement_repo}" "entitlement, billing, or commercial readiness claim"

plural_production_entitlement_repo="${workdir}/plural-production-entitlements"
create_valid_repo "${plural_production_entitlement_repo}"
printf '%s\n' "Production entitlements are enforced." >>"${plural_production_entitlement_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${plural_production_entitlement_repo}" "entitlement, billing, or commercial readiness claim"

support_readiness_repo="${workdir}/support-readiness"
create_valid_repo "${support_readiness_repo}"
printf '%s\n' "Support readiness is complete." >>"${support_readiness_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${support_readiness_repo}" "entitlement, billing, or commercial readiness claim"

support_ready_repo="${workdir}/support-ready"
create_valid_repo "${support_ready_repo}"
printf '%s\n' "Support is ready." >>"${support_ready_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${support_ready_repo}" "entitlement, billing, or commercial readiness claim"

migration_readiness_repo="${workdir}/migration-readiness"
create_valid_repo "${migration_readiness_repo}"
printf '%s\n' "Migration readiness is complete." >>"${migration_readiness_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${migration_readiness_repo}" "entitlement, billing, or commercial readiness claim"

migration_ready_repo="${workdir}/migration-ready"
create_valid_repo "${migration_ready_repo}"
printf '%s\n' "Migration is ready." >>"${migration_ready_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${migration_ready_repo}" "entitlement, billing, or commercial readiness claim"

self_service_commercial_repo="${workdir}/self-service-commercial"
create_valid_repo "${self_service_commercial_repo}"
printf '%s\n' "Self-service commercial readiness is complete." >>"${self_service_commercial_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${self_service_commercial_repo}" "entitlement, billing, or commercial readiness claim"

self_service_commercial_space_repo="${workdir}/self-service-commercial-space"
create_valid_repo "${self_service_commercial_space_repo}"
printf '%s\n' "Self service commercial readiness is complete." >>"${self_service_commercial_space_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${self_service_commercial_space_repo}" "entitlement, billing, or commercial readiness claim"

billing_provided_repo="${workdir}/billing-provided"
create_valid_repo "${billing_provided_repo}"
printf '%s\n' "Billing is provided." >>"${billing_provided_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${billing_provided_repo}" "entitlement, billing, or commercial readiness claim"

html_entity_billing_repo="${workdir}/html-entity-billing"
create_valid_repo "${html_entity_billing_repo}"
printf '%s\n' "Billing is avail&#97;ble." >>"${html_entity_billing_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${html_entity_billing_repo}" "entitlement, billing, or commercial readiness claim"

design_partner_completeness_repo="${workdir}/design-partner-completeness"
create_valid_repo "${design_partner_completeness_repo}"
printf '%s\n' "Design-partner evidence completeness is complete." >>"${design_partner_completeness_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${design_partner_completeness_repo}" "entitlement, billing, or commercial readiness claim"

direct_design_partner_completeness_repo="${workdir}/direct-design-partner-completeness"
create_valid_repo "${direct_design_partner_completeness_repo}"
printf '%s\n' "Design-partner evidence is complete." >>"${direct_design_partner_completeness_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${direct_design_partner_completeness_repo}" "entitlement, billing, or commercial readiness claim"

truth_claim_repo="${workdir}/truth-claim"
create_valid_repo "${truth_claim_repo}"
printf '%s\n' "The manifest is upgrade truth." >>"${truth_claim_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${truth_claim_repo}" "metadata, manifest, verifier, or issue-lint truth claim"

install_truth_repo="${workdir}/install-truth"
create_valid_repo "${install_truth_repo}"
printf '%s\n' "The manifest is install truth." >>"${install_truth_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${install_truth_repo}" "metadata, manifest, verifier, or issue-lint truth claim"

direct_verifier_truth_repo="${workdir}/direct-verifier-truth"
create_valid_repo "${direct_verifier_truth_repo}"
printf '%s\n' "Verifier is readiness truth." >>"${direct_verifier_truth_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${direct_verifier_truth_repo}" "metadata, manifest, verifier, or issue-lint truth claim"

authority_success_repo="${workdir}/authority-success"
create_valid_repo "${authority_success_repo}"
printf '%s\n' "The manifest proves live upgrade success." >>"${authority_success_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${authority_success_repo}" "authority-boundary success claim"

runtime_authority_repo="${workdir}/runtime-authority"
create_valid_repo "${runtime_authority_repo}"
printf '%s\n' "The manifest is runtime execution authority." >>"${runtime_authority_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${runtime_authority_repo}" "authority-boundary success claim"

substrate_mutation_repo="${workdir}/substrate-mutation"
create_valid_repo "${substrate_mutation_repo}"
printf '%s\n' "The manifest approves substrate mutation." >>"${substrate_mutation_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${substrate_mutation_repo}" "authority-boundary success claim"

release_readiness_approval_repo="${workdir}/release-readiness-approval"
create_valid_repo "${release_readiness_approval_repo}"
printf '%s\n' "The manifest approves release readiness." >>"${release_readiness_approval_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${release_readiness_approval_repo}" "authority-boundary success claim"

support_authority_repo="${workdir}/support-authority"
create_valid_repo "${support_authority_repo}"
printf '%s\n' "The manifest is support authority." >>"${support_authority_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${support_authority_repo}" "authority-boundary success claim"

entitlement_authority_repo="${workdir}/entitlement-authority"
create_valid_repo "${entitlement_authority_repo}"
printf '%s\n' "The manifest is entitlement authority." >>"${entitlement_authority_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${entitlement_authority_repo}" "authority-boundary success claim"

negated_authority_boundary_repo="${workdir}/negated-authority-boundary"
create_valid_repo "${negated_authority_boundary_repo}"
perl -0pi -e 's#^authority_boundary:.*#authority_boundary: This is not subordinate packaging and planning evidence only, but it still references the Phase 51.3 gate contract.#m' "${negated_authority_boundary_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${negated_authority_boundary_repo}" "Invalid Phase 65.3 upgrade manifest authority boundary"

path_repo="${workdir}/path"
create_valid_repo "${path_repo}"
home_path="/""Users/example/aegisops"
printf '%s\n' "Retain evidence under ${home_path}." >>"${path_repo}/docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
assert_fails_with "${path_repo}" "workstation-local absolute path"

non_home_path_repo="${workdir}/non-home-path"
create_valid_repo "${non_home_path_repo}"
printf '%s\n' "Retain evidence under /var/lib/aegisops." >>"${non_home_path_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${non_home_path_repo}" "workstation-local absolute path"

windows_drive_path_repo="${workdir}/windows-drive-path"
create_valid_repo "${windows_drive_path_repo}"
printf '%s\n' "Retain evidence under C:\\Temp\\aegisops." >>"${windows_drive_path_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${windows_drive_path_repo}" "workstation-local absolute path"

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
printf '%s\n' "api_key: actual-production-token" >>"${secret_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${secret_repo}" "Invalid Phase 65.3 upgrade manifest top-level field: api_key"

bearer_token_repo="${workdir}/bearer-token-secret"
create_valid_repo "${bearer_token_repo}"
printf '%s\n' "bearer_token: actual-production-token" >>"${bearer_token_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${bearer_token_repo}" "Invalid Phase 65.3 upgrade manifest top-level field: bearer_token"

authorization_bearer_repo="${workdir}/authorization-bearer-secret"
create_valid_repo "${authorization_bearer_repo}"
printf '%s\n' "Authorization: Bearer actual-production-token" >>"${authorization_bearer_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${authorization_bearer_repo}" "production secret-looking value"

generic_token_repo="${workdir}/generic-token-secret"
create_valid_repo "${generic_token_repo}"
printf '%s\n' "token: actual-production-token" >>"${generic_token_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${generic_token_repo}" "Invalid Phase 65.3 upgrade manifest top-level field: token"

customer_private_repo="${workdir}/customer-private-prose"
create_valid_repo "${customer_private_repo}"
printf '%s\n' "customer-private data includes tenant record 123" >>"${customer_private_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${customer_private_repo}" "customer-private data detected"

underscored_customer_private_repo="${workdir}/underscored-customer-private"
create_valid_repo "${underscored_customer_private_repo}"
printf '%s\n' "customer_private_data: tenant-record-123" >>"${underscored_customer_private_repo}/docs/release/phase-65-beta-release-notes.md"
assert_fails_with "${underscored_customer_private_repo}" "customer-private data detected"

echo "Phase 65.3 release channel and upgrade manifest verifier self-test passed."
