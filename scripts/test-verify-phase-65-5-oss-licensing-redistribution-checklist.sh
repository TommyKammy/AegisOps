#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh"

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
  local fixture_revision

  mkdir -p "${target}"
  copy_repo_path "${target}" "README.md"
  copy_repo_path "${target}" "docs/phase-65-5-oss-licensing-redistribution-checklist.md"
  copy_repo_path "${target}" "docs/phase-65-1-release-bundle-inventory.md"
  copy_repo_path "${target}" "docs/phase-65-2-offline-install-bundle-contract.md"
  copy_repo_path "${target}" "docs/phase-65-4-integrity-evidence-contract.md"
  copy_repo_path "${target}" "docs/phase-51-5-competitive-gap-matrix.md"
  copy_repo_path "${target}" "docs/deployment/wazuh-smb-single-node-profile-contract.md"
  copy_repo_path "${target}" "docs/deployment/shuffle-smb-single-node-profile-contract.md"
  copy_repo_path "${target}" "docs/deployment/shuffle-reviewed-workflow-template-contract.md"
  copy_repo_path "${target}" "docs/phase-58-6-support-bundle-redaction-contract.md"
  copy_repo_path "${target}" "docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
  copy_repo_path "${target}" "scripts/verify-phase-65-5-oss-licensing-redistribution-checklist.sh"
  copy_repo_path "${target}" "scripts/test-verify-phase-65-5-oss-licensing-redistribution-checklist.sh"
  copy_repo_path "${target}" "scripts/verify-publishable-path-hygiene.sh"
  mkdir -p "${target}/control-plane/aegisops/control_plane"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  git -C "${target}" init -q
  git -C "${target}" config user.email "phase-65-5-test@example.invalid"
  git -C "${target}" config user.name "Phase 65.5 Test"
  git -C "${target}" add README.md docs scripts control-plane
  git -C "${target}" commit -q -m "fixture"
  fixture_revision="$(git -C "${target}" rev-parse HEAD)"
  FIXTURE_REVISION="${fixture_revision}" perl -0pi -e 's/[0-9a-f]{40}/$ENV{FIXTURE_REVISION}/g' \
    "${target}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
  git -C "${target}" add docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml
  git -C "${target}" commit -q -m "bind fixture revision"
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

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-65-5-oss-licensing-redistribution-checklist.md"
assert_fails_with "${missing_doc_repo}" "Missing Phase 65.5 OSS licensing and redistribution review checklist"

missing_record_repo="${workdir}/missing-record"
create_valid_repo "${missing_record_repo}"
rm "${missing_record_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_record_repo}" "Missing Phase 65.5 OSS licensing and redistribution checklist record"

missing_readme_repo="${workdir}/missing-readme"
create_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 65\.5 OSS licensing and redistribution review checklist\]\(docs\/phase-65-5-oss-licensing-redistribution-checklist\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical cross-phase boundary bullet"

missing_owner_repo="${workdir}/missing-owner"
create_valid_repo "${missing_owner_repo}"
perl -0pi -e 's/^review_owner:.*\n//m' "${missing_owner_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_owner_repo}" "Missing Phase 65.5 licensing checklist value: review_owner"

missing_reviewed_date_repo="${workdir}/missing-reviewed-date"
create_valid_repo "${missing_reviewed_date_repo}"
perl -0pi -e 's/^reviewed_date:.*\n//m' "${missing_reviewed_date_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_reviewed_date_repo}" "Missing Phase 65.5 licensing checklist value: reviewed_date"

invalid_reviewed_date_repo="${workdir}/invalid-reviewed-date"
create_valid_repo "${invalid_reviewed_date_repo}"
perl -0pi -e 's/^reviewed_date:.*/reviewed_date: 2026\/06\/07/m' "${invalid_reviewed_date_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${invalid_reviewed_date_repo}" "Invalid Phase 65.5 licensing checklist value: reviewed_date"

missing_conclusion_repo="${workdir}/missing-conclusion"
create_valid_repo "${missing_conclusion_repo}"
perl -0pi -e 's/^conclusion:.*\n//m' "${missing_conclusion_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_conclusion_repo}" "Missing Phase 65.5 licensing checklist value: conclusion"

conclusion_overclaim_repo="${workdir}/conclusion-overclaim"
create_valid_repo "${conclusion_overclaim_repo}"
perl -0pi -e 's/^conclusion:.*/conclusion: Accepted as legal advice and production distribution approval for RC readiness./m' "${conclusion_overclaim_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${conclusion_overclaim_repo}" "Invalid Phase 65.5 licensing checklist value: conclusion"

missing_blocker_repo="${workdir}/missing-blocker"
create_valid_repo "${missing_blocker_repo}"
perl -0pi -e 's/^blocker_disposition:\n  open_blockers:.*\n  disposition:.*\n//m' "${missing_blocker_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_blocker_repo}" "Missing Phase 65.5 licensing checklist value: open_blockers"

missing_wazuh_posture_repo="${workdir}/missing-wazuh-posture"
create_valid_repo "${missing_wazuh_posture_repo}"
perl -0pi -e 's/separate reviewed upstream redistribution approval before inclusion/separate review before inclusion/m' "${missing_wazuh_posture_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_wazuh_posture_repo}" "Missing Phase 65.5 licensing checklist Wazuh posture"

missing_shuffle_posture_repo="${workdir}/missing-shuffle-posture"
create_valid_repo "${missing_shuffle_posture_repo}"
perl -0pi -e 's/separate reviewed upstream redistribution approval before inclusion/separate review before inclusion/g' "${missing_shuffle_posture_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_shuffle_posture_repo}" "Missing Phase 65.5 licensing checklist Wazuh posture"
perl -0pi -e 's/separate review before inclusion/separate reviewed upstream redistribution approval before inclusion/' "${missing_shuffle_posture_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_shuffle_posture_repo}" "Missing Phase 65.5 licensing checklist Shuffle posture"

missing_artifact_scope_repo="${workdir}/missing-artifact-scope"
create_valid_repo "${missing_artifact_scope_repo}"
perl -0pi -e 's/^artifact_scope:\n(?:  - artifact_class:.*?(?=\n[A-Za-z0-9_-]+:|\z))//ms' "${missing_artifact_scope_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_artifact_scope_repo}" "Missing Phase 65.5 licensing checklist artifact_scope"

missing_wazuh_artifact_repo="${workdir}/missing-wazuh-artifact"
create_valid_repo "${missing_wazuh_artifact_repo}"
perl -0pi -e 's/\n  - artifact_class: wazuh-profile-package\n    scope_owner: Platform maintainers\n    scope_reference: docs\/deployment\/wazuh-smb-single-node-profile-contract\.md\n    redistribution_posture: repo-owned-profile-config-only-upstream-wazuh-material-requires-separate-reviewed-approval\n    blocker_status: none_for_checklist_record\n    boundary_note: Wazuh remains a subordinate detection substrate and cannot become release truth, gate truth, workflow truth, or readiness truth\.//m' \
  "${missing_wazuh_artifact_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_wazuh_artifact_repo}" "Missing Phase 65.5 licensing checklist artifact_class: wazuh-profile-package"

missing_artifact_owner_repo="${workdir}/missing-artifact-owner"
create_valid_repo "${missing_artifact_owner_repo}"
perl -0pi -e 's/^    scope_owner: Platform maintainers\n//m' "${missing_artifact_owner_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${missing_artifact_owner_repo}" "Missing Phase 65.5 licensing checklist scope_owner for wazuh-profile-package"

wrong_artifact_owner_repo="${workdir}/wrong-artifact-owner"
create_valid_repo "${wrong_artifact_owner_repo}"
perl -0pi -e 's/(artifact_class: wazuh-profile-package\n    scope_owner: )Platform maintainers/$1AegisOps maintainers/m' \
  "${wrong_artifact_owner_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${wrong_artifact_owner_repo}" "Invalid Phase 65.5 licensing checklist scope_owner for wazuh-profile-package"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
workstation_reference="/""Users/example/license-review.md"
WORKSTATION_REFERENCE="${workstation_reference}" perl -0pi -e 's#docs/phase-65-1-release-bundle-inventory\.md#$ENV{WORKSTATION_REFERENCE}#m' \
  "${workstation_path_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${workstation_path_repo}" "Invalid Phase 65.5 licensing checklist"

release_identifier_mismatch_repo="${workdir}/release-identifier-mismatch"
create_valid_repo "${release_identifier_mismatch_repo}"
perl -0pi -e 's/^release_bundle_identifier:.*/release_bundle_identifier: aegisops-beta-deadbeef/m' "${release_identifier_mismatch_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${release_identifier_mismatch_repo}" "release_bundle_identifier must bind to repository_revision"

unresolved_revision_repo="${workdir}/unresolved-revision"
create_valid_repo "${unresolved_revision_repo}"
perl -0pi -e 's/[0-9a-f]{40}/deadbeef/g' "${unresolved_revision_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${unresolved_revision_repo}" "repository_revision must be a 40-character commit SHA or reviewed Git tag"

revision_missing_checklist_repo="${workdir}/revision-missing-checklist"
create_valid_repo "${revision_missing_checklist_repo}"
empty_tree="$(git -C "${revision_missing_checklist_repo}" mktree </dev/null)"
revision_missing_checklist="$(printf '%s\n' "missing checklist evidence" | git -C "${revision_missing_checklist_repo}" commit-tree "${empty_tree}")"
REVISION_MISSING_CHECKLIST="${revision_missing_checklist}" perl -0pi -e 's/[0-9a-f]{40}/$ENV{REVISION_MISSING_CHECKLIST}/g' \
  "${revision_missing_checklist_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${revision_missing_checklist_repo}" "repository_revision must contain README.md"

non_claim_true_repo="${workdir}/non-claim-true"
create_valid_repo "${non_claim_true_repo}"
perl -0pi -e 's/^  legal_advice: false/  legal_advice: true/m' "${non_claim_true_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${non_claim_true_repo}" "Invalid Phase 65.5 licensing checklist value: legal_advice"

legal_advice_claim_repo="${workdir}/legal-advice-claim"
create_valid_repo "${legal_advice_claim_repo}"
printf '%s\n' "Phase 65.5 licensing checklist provides legal advice." >>"${legal_advice_claim_repo}/docs/phase-65-5-oss-licensing-redistribution-checklist.md"
assert_fails_with "${legal_advice_claim_repo}" "Forbidden Phase 65.5 licensing checklist claim"

production_distribution_claim_repo="${workdir}/production-distribution-claim"
create_valid_repo "${production_distribution_claim_repo}"
printf '%s\n' "AegisOps redistribution checklist approves production distribution approval." >>"${production_distribution_claim_repo}/docs/phase-65-5-oss-licensing-redistribution-checklist.md"
assert_fails_with "${production_distribution_claim_repo}" "Forbidden Phase 65.5 licensing checklist claim"

rc_overclaim_repo="${workdir}/rc-overclaim"
create_valid_repo "${rc_overclaim_repo}"
printf '%s\n' "The Phase 65.5 checklist proves RC readiness." >>"${rc_overclaim_repo}/docs/phase-65-5-oss-licensing-redistribution-checklist.md"
assert_fails_with "${rc_overclaim_repo}" "Forbidden Phase 65.5 licensing checklist claim"

ga_overclaim_repo="${workdir}/ga-overclaim"
create_valid_repo "${ga_overclaim_repo}"
printf '%s\n' "The licensing checklist confirms GA readiness." >>"${ga_overclaim_repo}/docs/phase-65-5-oss-licensing-redistribution-checklist.md"
assert_fails_with "${ga_overclaim_repo}" "Forbidden Phase 65.5 licensing checklist claim"

verifier_truth_repo="${workdir}/verifier-truth"
create_valid_repo "${verifier_truth_repo}"
printf '%s\n' "The verifier output becomes readiness truth." >>"${verifier_truth_repo}/docs/phase-65-5-oss-licensing-redistribution-checklist.md"
assert_fails_with "${verifier_truth_repo}" "verifier or issue-lint truth shortcut"

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
printf '%s\n' "token = abc123" >>"${secret_repo}/docs/deployment/release/phase-65-5-oss-licensing-redistribution-checklist.yaml"
assert_fails_with "${secret_repo}" "production secret material"

customer_private_repo="${workdir}/customer-private"
create_valid_repo "${customer_private_repo}"
printf '%s\n' "The bundle includes customer-private data." >>"${customer_private_repo}/docs/phase-65-5-oss-licensing-redistribution-checklist.md"
assert_fails_with "${customer_private_repo}" "customer-private data"

echo "Phase 65.5 OSS licensing and redistribution checklist verifier self-test passed"
