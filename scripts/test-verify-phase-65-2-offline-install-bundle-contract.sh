#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-2-offline-install-bundle-contract.sh"
default_repository_revision="$(git -C "${repo_root}" rev-parse --short=12 HEAD)"
default_release_bundle_identifier="aegisops-beta-${default_repository_revision}"

workdir="$(mktemp -d)"
trap 'rm -rf "${workdir}"' EXIT

pass_stdout="${workdir}/pass.out"
pass_stderr="${workdir}/pass.err"
fail_stdout="${workdir}/fail.out"
fail_stderr="${workdir}/fail.err"

assert_passes() {
  if ! bash "${verifier}" "$@" >"${pass_stdout}" 2>"${pass_stderr}"; then
    echo "Expected verifier to pass: $*" >&2
    cat "${pass_stdout}" >&2
    cat "${pass_stderr}" >&2
    exit 1
  fi
}

assert_fails_with() {
  local expected="$1"
  shift

  if bash "${verifier}" "$@" >"${fail_stdout}" 2>"${fail_stderr}"; then
    echo "Expected verifier to fail: $*" >&2
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
  local source_root="$1"
  local target_root="$2"
  local relative_path="$3"

  mkdir -p "${target_root}/$(dirname "${relative_path}")"
  cp -pR "${source_root}/${relative_path}" "${target_root}/${relative_path}"
}

create_valid_repo() {
  local target="$1"

  mkdir -p "${target}"
  copy_repo_path "${repo_root}" "${target}" "README.md"
  copy_repo_path "${repo_root}" "${target}" "docs/phase-65-2-offline-install-bundle-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/phase-65-1-release-bundle-inventory.md"
  copy_repo_path "${repo_root}" "${target}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/first-user-stack.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/host-preflight-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/clean-host-smoke-skeleton.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/env-secrets-certs-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/runbook.md"
}

create_reviewed_tag_repo() {
  local target="$1"
  local tag="$2"

  create_valid_repo "${target}"
  git -C "${target}" init -q
  git -C "${target}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
  git -C "${target}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create reviewed offline bundle baseline"
  git -C "${target}" tag "${tag}"
}

replace_default_bundle_revision() {
  local revision="$1"
  shift

  DEFAULT_RELEASE_BUNDLE_IDENTIFIER="${default_release_bundle_identifier}" \
    DEFAULT_REPOSITORY_REVISION="${default_repository_revision}" \
    RELEASE_BUNDLE_IDENTIFIER="aegisops-beta-${revision}" \
    REPOSITORY_REVISION="${revision}" \
    perl -0pi -e '
      s/\Q$ENV{DEFAULT_RELEASE_BUNDLE_IDENTIFIER}\E/$ENV{RELEASE_BUNDLE_IDENTIFIER}/g;
      s/\Q$ENV{DEFAULT_REPOSITORY_REVISION}\E/$ENV{REPOSITORY_REVISION}/g;
    ' "$@"
}

create_valid_bundle() {
  local target="$1"

  mkdir -p \
    "${target}/install" \
    "${target}/config" \
    "${target}/evidence" \
    "${target}/docs/deployment"

  cat >"${target}/BUNDLE-MANIFEST.md" <<EOF_MANIFEST
# Offline Install Bundle Manifest

contract identifier: phase-65-offline-install-bundle-contract-v1
inventory identifier: phase-65-release-bundle-inventory-v1
release bundle identifier: ${default_release_bundle_identifier}
repository revision: ${default_repository_revision}
bundle owner: AegisOps maintainers
per-artifact owner: Platform maintainers
bundle creation timestamp: 2026-06-02T00:00:00Z
environment assumption: offline-beta-design-partner
required artifact manifest path: BUNDLE-MANIFEST.md
exclusion review: issue #1384 / PR #1389 reviewed no workstation-local paths, production secrets, customer-private data, hidden hosted dependency, hosted update service, silent update, production installer, entitlement, billing, RC pass, or GA pass claims.
verifier output: bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>
approval record: issue #1384 / PR #1389
EOF_MANIFEST

  cat >"${target}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

Run the offline install command `aegisops up --profile smb-single-node --runtime-env <runtime-env-file>` from the release bundle root after host preflight passes.
Use the selected profile `smb-single-node`, keep dependency assumptions explicit, complete manual prerequisites, and retain output under <evidence-dir>.
EOF_INSTALL

  cat >"${target}/config/runtime.env.sample" <<'EOF_ENV'
# Runtime environment sample

AEGISOPS_PROFILE=smb-single-node
AEGISOPS_RUNTIME_ENV=<runtime-env-file>
AEGISOPS_SECRET_SOURCE_DOC=docs/deployment/env-secrets-certs-contract.md
# Secrets must come from trusted local custody and must not be embedded here.
EOF_ENV

  cat >"${target}/evidence/install-preflight-output.txt" <<EOF_EVIDENCE
release bundle identifier: ${default_release_bundle_identifier}
repository revision: ${default_repository_revision}
preflight output: retained placeholder for beta/design-partner packaging review.
EOF_EVIDENCE

  copy_repo_path "${repo_root}" "${target}" "docs/phase-65-2-offline-install-bundle-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/phase-65-1-release-bundle-inventory.md"
  copy_repo_path "${repo_root}" "${target}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/first-user-stack.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/host-preflight-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/clean-host-smoke-skeleton.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/env-secrets-certs-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/runbook.md"
}

remove_doc_text() {
  local target="$1"
  local text="$2"

  TEXT="${text}" perl -0pi -e 's/\Q$ENV{TEXT}\E//g' \
    "${target}/docs/phase-65-2-offline-install-bundle-contract.md"
}

valid_repo="${workdir}/valid-repo"
create_valid_repo "${valid_repo}"
assert_passes --repo-root "${valid_repo}"

missing_doc_repo="${workdir}/missing-doc"
create_valid_repo "${missing_doc_repo}"
rm "${missing_doc_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "Missing Phase 65.2 offline install bundle contract" --repo-root "${missing_doc_repo}"

missing_readme_repo="${workdir}/missing-readme-link"
create_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 65\.2 offline install bundle contract\]\(docs\/phase-65-2-offline-install-bundle-contract\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "Missing README canonical cross-phase boundary bullet" --repo-root "${missing_readme_repo}"

missing_metadata_repo="${workdir}/missing-metadata"
create_valid_repo "${missing_metadata_repo}"
remove_doc_text "${missing_metadata_repo}" "bundle creation timestamp;"
assert_fails_with "Missing required Phase 65.2 offline bundle contract term" --repo-root "${missing_metadata_repo}"

missing_required_file_row_repo="${workdir}/missing-required-file-row"
create_valid_repo "${missing_required_file_row_repo}"
remove_doc_text "${missing_required_file_row_repo}" '| `config/runtime.env.sample` | Platform maintainers | Placeholder-only runtime configuration keys and secret-source instructions that cite `docs/deployment/env-secrets-certs-contract.md`. | Reject the bundle because runtime configuration custody is not inspectable. |'
assert_fails_with "Missing Phase 65.2 required bundle file row" --repo-root "${missing_required_file_row_repo}"

corrupt_inventory_repo="${workdir}/corrupt-inventory"
create_valid_repo "${corrupt_inventory_repo}"
printf '%s\n' "x" >"${corrupt_inventory_repo}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with "Missing inherited baseline contract term in docs/phase-65-1-release-bundle-inventory.md" --repo-root "${corrupt_inventory_repo}"

corrupt_gate_repo="${workdir}/corrupt-gate"
create_valid_repo "${corrupt_gate_repo}"
printf '%s\n' "x" >"${corrupt_gate_repo}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with "Missing inherited baseline contract term in docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" --repo-root "${corrupt_gate_repo}"

corrupt_env_contract_repo="${workdir}/corrupt-env-contract"
create_valid_repo "${corrupt_env_contract_repo}"
printf '%s\n' "x" >"${corrupt_env_contract_repo}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with "Missing inherited baseline contract term in docs/deployment/env-secrets-certs-contract.md" --repo-root "${corrupt_env_contract_repo}"

corrupt_runbook_repo="${workdir}/corrupt-runbook"
create_valid_repo "${corrupt_runbook_repo}"
printf '%s\n' "x" >"${corrupt_runbook_repo}/docs/runbook.md"
assert_fails_with "Missing inherited baseline contract term in docs/runbook.md" --repo-root "${corrupt_runbook_repo}"

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
local_home_path="/""Users/example/aegisops"
printf '%s\n' "Do not use ${local_home_path} in publishable guidance." >>"${local_path_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "workstation-local absolute path" --repo-root "${local_path_repo}"

file_url_local_path_repo="${workdir}/file-url-local-path"
create_valid_repo "${file_url_local_path_repo}"
file_url_home_path="file://${local_home_path}"
printf '%s\n' "Do not use ${file_url_home_path} in publishable guidance." >>"${file_url_local_path_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "workstation-local absolute path" --repo-root "${file_url_local_path_repo}"

system_absolute_path_repo="${workdir}/system-absolute-path"
create_valid_repo "${system_absolute_path_repo}"
printf '%s\n' "Do not use /etc/aegisops/runtime.env in publishable guidance." >>"${system_absolute_path_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "workstation-local absolute path" --repo-root "${system_absolute_path_repo}"

file_url_system_path_repo="${workdir}/file-url-system-path"
create_valid_repo "${file_url_system_path_repo}"
printf '%s\n' "Do not use file:///etc/aegisops/runtime.env in publishable guidance." >>"${file_url_system_path_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "workstation-local absolute path" --repo-root "${file_url_system_path_repo}"

root_path_repo="${workdir}/root-path"
create_valid_repo "${root_path_repo}"
root_home_path="/""root/private/aegisops"
printf '%s\n' "Do not use ${root_home_path} in publishable guidance." >>"${root_path_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "workstation-local absolute path" --repo-root "${root_path_repo}"

windows_posix_path_repo="${workdir}/windows-posix-path"
create_valid_repo "${windows_posix_path_repo}"
windows_posix_home_path="C:""/""Users/example/aegisops"
printf '%s\n' "Do not use ${windows_posix_home_path} in publishable guidance." >>"${windows_posix_path_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "workstation-local absolute path" --repo-root "${windows_posix_path_repo}"

json_escaped_path_repo="${workdir}/json-escaped-path"
create_valid_repo "${json_escaped_path_repo}"
json_escaped_home_path='\/'"home"'\/example\/aegisops'
printf '%s\n' "Do not use ${json_escaped_home_path} in publishable guidance." >>"${json_escaped_path_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "workstation-local absolute path" --repo-root "${json_escaped_path_repo}"

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
printf '%s\n' "api_key = live-secret-looking-value" >>"${secret_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "production secret-looking value" --repo-root "${secret_repo}"

hosted_update_repo="${workdir}/hosted-update"
create_valid_repo "${hosted_update_repo}"
printf '%s\n' "Hosted update service is enabled by this bundle." >>"${hosted_update_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${hosted_update_repo}"

hosted_update_readiness_repo="${workdir}/hosted-update-readiness"
create_valid_repo "${hosted_update_readiness_repo}"
printf '%s\n' "Hosted update service readiness is complete for this bundle." >>"${hosted_update_readiness_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${hosted_update_readiness_repo}"

mixed_negated_positive_claim_repo="${workdir}/mixed-negated-positive-claim"
create_valid_repo "${mixed_negated_positive_claim_repo}"
printf '%s\n' "This contract does not claim hosted update service readiness, but silent auto-upgrade is enabled after install." >>"${mixed_negated_positive_claim_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${mixed_negated_positive_claim_repo}"

release_channel_repo="${workdir}/release-channel"
create_valid_repo "${release_channel_repo}"
printf '%s\n' "Release-channel behavior is implemented by this bundle." >>"${release_channel_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${release_channel_repo}"

placeholder_credential_repo="${workdir}/placeholder-credential"
create_valid_repo "${placeholder_credential_repo}"
printf '%s\n' "Placeholder credentials are valid auth for beta install." >>"${placeholder_credential_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "placeholder credentials accepted as valid auth" --repo-root "${placeholder_credential_repo}"

placeholder_credential_treated_repo="${workdir}/placeholder-credential-treated"
create_valid_repo "${placeholder_credential_treated_repo}"
printf '%s\n' "Placeholder credentials are treated as valid auth for beta install." >>"${placeholder_credential_treated_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "placeholder credentials accepted as valid auth" --repo-root "${placeholder_credential_treated_repo}"

placeholder_login_repo="${workdir}/placeholder-login"
create_valid_repo "${placeholder_login_repo}"
printf '%s\n' "Sample credentials may be used to log in during the beta install." >>"${placeholder_login_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "placeholder credentials accepted as valid auth" --repo-root "${placeholder_login_repo}"

production_installer_repo="${workdir}/production-installer"
create_valid_repo "${production_installer_repo}"
printf '%s\n' "This bundle provides production installer completeness." >>"${production_installer_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${production_installer_repo}"

production_installer_complete_repo="${workdir}/production-installer-complete"
create_valid_repo "${production_installer_complete_repo}"
printf '%s\n' "Production installer is complete for this bundle." >>"${production_installer_complete_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${production_installer_complete_repo}"

customer_specific_secret_provisioning_repo="${workdir}/customer-specific-secret-provisioning"
create_valid_repo "${customer_specific_secret_provisioning_repo}"
printf '%s\n' "Customer-specific secret provisioning is supported by this bundle." >>"${customer_specific_secret_provisioning_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "customer-specific secret provisioning claim" --repo-root "${customer_specific_secret_provisioning_repo}"

sbom_completeness_repo="${workdir}/sbom-completeness"
create_valid_repo "${sbom_completeness_repo}"
printf '%s\n' "Offline install bundle proves SBOM completeness." >>"${sbom_completeness_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --repo-root "${sbom_completeness_repo}"

rc_claim_repo="${workdir}/rc-claim"
create_valid_repo "${rc_claim_repo}"
printf '%s\n' "Offline install bundle proves RC readiness." >>"${rc_claim_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --repo-root "${rc_claim_repo}"

reversed_rc_claim_repo="${workdir}/reversed-rc-claim"
create_valid_repo "${reversed_rc_claim_repo}"
printf '%s\n' "RC readiness is proven by verifier output." >>"${reversed_rc_claim_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --repo-root "${reversed_rc_claim_repo}"

reversed_truth_repo="${workdir}/reversed-truth"
create_valid_repo "${reversed_truth_repo}"
printf '%s\n' "Readiness truth is satisfied by issue-lint output." >>"${reversed_truth_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "verifier, issue-lint, install, or smoke truth claim" --repo-root "${reversed_truth_repo}"

valid_bundle="${workdir}/valid-bundle"
create_valid_bundle "${valid_bundle}"
assert_passes --bundle-dir "${valid_bundle}"
assert_passes --bundle-dir "${valid_bundle}/"
assert_passes --bundle-dir "${valid_bundle}/."

bundle_dir_symlink="${workdir}/bundle-dir-symlink"
ln -s "${valid_bundle}" "${bundle_dir_symlink}"
assert_fails_with "symlink is not allowed" --bundle-dir "${bundle_dir_symlink}"

valid_not_optional_install_readme="${workdir}/valid-not-optional-install-readme"
create_valid_bundle "${valid_not_optional_install_readme}"
printf '%s\n' "Manual prerequisites are not optional." >>"${valid_not_optional_install_readme}/install/README.md"
assert_passes --bundle-dir "${valid_not_optional_install_readme}"

placeholder_secret_sample_bundle="${workdir}/placeholder-secret-sample-bundle"
create_valid_bundle "${placeholder_secret_sample_bundle}"
printf '%s\n' "DB_PASSWORD=<db-password>" "API_KEY=placeholder" >>"${placeholder_secret_sample_bundle}/config/runtime.env.sample"
assert_passes --bundle-dir "${placeholder_secret_sample_bundle}"

runtime_sample_concrete_value_bundle="${workdir}/runtime-sample-concrete-value-bundle"
create_valid_bundle "${runtime_sample_concrete_value_bundle}"
printf '%s\n' "DATABASE_HOST=prod-db.internal" >>"${runtime_sample_concrete_value_bundle}/config/runtime.env.sample"
assert_fails_with "non-placeholder runtime sample value" --bundle-dir "${runtime_sample_concrete_value_bundle}"

dotted_revision_bundle="${workdir}/dotted-revision-bundle"
create_valid_bundle "${dotted_revision_bundle}"
replace_default_bundle_revision "v1.2.3" \
  "${dotted_revision_bundle}/BUNDLE-MANIFEST.md" \
  "${dotted_revision_bundle}/evidence/install-preflight-output.txt"
reviewed_tag_repo="${workdir}/reviewed-tag-repo"
create_reviewed_tag_repo "${reviewed_tag_repo}" "v1.2.3"
assert_passes --repo-root "${reviewed_tag_repo}" --bundle-dir "${dotted_revision_bundle}"

hex_like_tag_bundle="${workdir}/hex-like-tag-bundle"
create_valid_bundle "${hex_like_tag_bundle}"
replace_default_bundle_revision "20260602" \
  "${hex_like_tag_bundle}/BUNDLE-MANIFEST.md" \
  "${hex_like_tag_bundle}/evidence/install-preflight-output.txt"
hex_like_tag_repo="${workdir}/hex-like-tag-repo"
create_reviewed_tag_repo "${hex_like_tag_repo}" "20260602"
assert_passes --repo-root "${hex_like_tag_repo}" --bundle-dir "${hex_like_tag_bundle}"

slash_qualified_tag_bundle="${workdir}/slash-qualified-tag-bundle"
create_valid_bundle "${slash_qualified_tag_bundle}"
replace_default_bundle_revision "reviewed/phase-65.2" \
  "${slash_qualified_tag_bundle}/BUNDLE-MANIFEST.md" \
  "${slash_qualified_tag_bundle}/evidence/install-preflight-output.txt"
slash_qualified_tag_repo="${workdir}/slash-qualified-tag-repo"
create_reviewed_tag_repo "${slash_qualified_tag_repo}" "reviewed/phase-65.2"
assert_passes --repo-root "${slash_qualified_tag_repo}" --bundle-dir "${slash_qualified_tag_bundle}"

dotted_revision_mismatch="${workdir}/dotted-revision-mismatch"
create_valid_bundle "${dotted_revision_mismatch}"
replace_default_bundle_revision "v1.2.3" \
  "${dotted_revision_mismatch}/BUNDLE-MANIFEST.md"
replace_default_bundle_revision "v1X2X3" \
  "${dotted_revision_mismatch}/evidence/install-preflight-output.txt"
assert_fails_with "Missing offline install bundle artifact content in evidence/install-preflight-output.txt: matching release bundle identifier" --repo-root "${reviewed_tag_repo}" --bundle-dir "${dotted_revision_mismatch}"

missing_bundle_metadata="${workdir}/missing-bundle-metadata"
create_valid_bundle "${missing_bundle_metadata}"
perl -0pi -e 's/^bundle creation timestamp:.*\n//m' "${missing_bundle_metadata}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: bundle creation timestamp" --bundle-dir "${missing_bundle_metadata}"

invalid_bundle_timestamp="${workdir}/invalid-bundle-timestamp"
create_valid_bundle "${invalid_bundle_timestamp}"
perl -0pi -e 's/^bundle creation timestamp:.*$/bundle creation timestamp: 2026-99-99T99:99:99Z/m' "${invalid_bundle_timestamp}/BUNDLE-MANIFEST.md"
assert_fails_with "Invalid offline install bundle creation timestamp" --bundle-dir "${invalid_bundle_timestamp}"

documented_manifest_labels="${workdir}/documented-manifest-labels"
create_valid_bundle "${documented_manifest_labels}"
perl -0pi -e 's/^environment assumption:/reviewed environment assumption:/m; s/^verifier output:/verifier output reference:/m' "${documented_manifest_labels}/BUNDLE-MANIFEST.md"
assert_passes --bundle-dir "${documented_manifest_labels}"

duplicate_manifest_label_alias="${workdir}/duplicate-manifest-label-alias"
create_valid_bundle "${duplicate_manifest_label_alias}"
printf '%s\n' "reviewed environment assumption: offline-beta-design-partner" >>"${duplicate_manifest_label_alias}/BUNDLE-MANIFEST.md"
assert_fails_with "Duplicate offline install bundle metadata field: environment assumption" --bundle-dir "${duplicate_manifest_label_alias}"

missing_approval_record="${workdir}/missing-approval-record"
create_valid_bundle "${missing_approval_record}"
perl -0pi -e 's/^approval record:.*\n//m' "${missing_approval_record}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: approval record" --bundle-dir "${missing_approval_record}"

negated_exclusion_review="${workdir}/negated-exclusion-review"
create_valid_bundle "${negated_exclusion_review}"
perl -0pi -e 's/^exclusion review:.*$/exclusion review: not reviewed/m' "${negated_exclusion_review}/BUNDLE-MANIFEST.md"
assert_fails_with "Invalid offline install bundle metadata value: exclusion review" --bundle-dir "${negated_exclusion_review}"

negated_approval_record="${workdir}/negated-approval-record"
create_valid_bundle "${negated_approval_record}"
perl -0pi -e 's/^approval record:.*$/approval record: not approved/m' "${negated_approval_record}/BUNDLE-MANIFEST.md"
assert_fails_with "Invalid offline install bundle metadata value: approval record" --bundle-dir "${negated_approval_record}"

pending_approval_record="${workdir}/pending-approval-record"
create_valid_bundle "${pending_approval_record}"
perl -0pi -e 's/^approval record:.*$/approval record: issue #1384 pending approval/m' "${pending_approval_record}/BUNDLE-MANIFEST.md"
assert_fails_with "Invalid offline install bundle metadata value: approval record" --bundle-dir "${pending_approval_record}"

missing_approval_link="${workdir}/missing-approval-link"
create_valid_bundle "${missing_approval_link}"
perl -0pi -e 's/^approval record:.*$/approval record: maintainer reviewed/m' "${missing_approval_link}/BUNDLE-MANIFEST.md"
assert_fails_with "Invalid offline install bundle metadata value: approval record" --bundle-dir "${missing_approval_link}"

missing_exclusion_review_link="${workdir}/missing-exclusion-review-link"
create_valid_bundle "${missing_exclusion_review_link}"
perl -0pi -e 's/^exclusion review:.*$/exclusion review: reviewed/m' "${missing_exclusion_review_link}/BUNDLE-MANIFEST.md"
assert_fails_with "Invalid offline install bundle metadata value: exclusion review" --bundle-dir "${missing_exclusion_review_link}"

duplicate_manifest_metadata="${workdir}/duplicate-manifest-metadata"
create_valid_bundle "${duplicate_manifest_metadata}"
printf '%s\n' "release bundle identifier: aegisops-beta-deadbeef1234" >>"${duplicate_manifest_metadata}/BUNDLE-MANIFEST.md"
assert_fails_with "Duplicate offline install bundle metadata field: release bundle identifier" --bundle-dir "${duplicate_manifest_metadata}"

duplicate_preflight_metadata="${workdir}/duplicate-preflight-metadata"
create_valid_bundle "${duplicate_preflight_metadata}"
printf '%s\n' "repository revision: deadbeef123456" >>"${duplicate_preflight_metadata}/evidence/install-preflight-output.txt"
assert_fails_with "Invalid offline install bundle artifact metadata field in evidence/install-preflight-output.txt: repository revision" --bundle-dir "${duplicate_preflight_metadata}"

commented_manifest_metadata="${workdir}/commented-manifest-metadata"
create_valid_bundle "${commented_manifest_metadata}"
perl -0pi -e 's/^contract identifier:.*$/<!-- contract identifier: phase-65-offline-install-bundle-contract-v1 -->/m' "${commented_manifest_metadata}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: contract identifier" --bundle-dir "${commented_manifest_metadata}"

fenced_manifest_metadata="${workdir}/fenced-manifest-metadata"
create_valid_bundle "${fenced_manifest_metadata}"
perl -0pi -e 's/\A/```\n/; s/\z/\n```\n/' "${fenced_manifest_metadata}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: contract identifier" --bundle-dir "${fenced_manifest_metadata}"

tilde_fenced_manifest_metadata="${workdir}/tilde-fenced-manifest-metadata"
create_valid_bundle "${tilde_fenced_manifest_metadata}"
perl -0pi -e 's/\A/~~~\n/; s/\z/\n~~~\n/' "${tilde_fenced_manifest_metadata}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: contract identifier" --bundle-dir "${tilde_fenced_manifest_metadata}"

blank_bundle_owner="${workdir}/blank-bundle-owner"
create_valid_bundle "${blank_bundle_owner}"
perl -0pi -e 's/^bundle owner:.*$/bundle owner: /m' "${blank_bundle_owner}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: bundle owner" --bundle-dir "${blank_bundle_owner}"

unassigned_bundle_owner="${workdir}/unassigned-bundle-owner"
create_valid_bundle "${unassigned_bundle_owner}"
perl -0pi -e 's/^bundle owner:.*$/bundle owner: not assigned/m; s/^per-artifact owner:.*$/per-artifact owner: unassigned/m' "${unassigned_bundle_owner}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: bundle owner" --bundle-dir "${unassigned_bundle_owner}"

placeholder_bundle_revision="${workdir}/placeholder-bundle-revision"
create_valid_bundle "${placeholder_bundle_revision}"
perl -0pi -e 's/^release bundle identifier:.*$/release bundle identifier: aegisops-beta-<repository-revision>/m' "${placeholder_bundle_revision}/BUNDLE-MANIFEST.md"
assert_fails_with "Invalid offline install bundle release identifier" --bundle-dir "${placeholder_bundle_revision}"

placeholder_repository_revision="${workdir}/placeholder-repository-revision"
create_valid_bundle "${placeholder_repository_revision}"
perl -0pi -e 's/^repository revision:.*$/repository revision: <repository-revision>/m' "${placeholder_repository_revision}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: repository revision" --bundle-dir "${placeholder_repository_revision}"

mismatched_bundle_revision="${workdir}/mismatched-bundle-revision"
create_valid_bundle "${mismatched_bundle_revision}"
perl -0pi -e 's/^repository revision:.*$/repository revision: deadbeef1234/m' "${mismatched_bundle_revision}/BUNDLE-MANIFEST.md"
assert_fails_with "Invalid offline install bundle release binding" --bundle-dir "${mismatched_bundle_revision}"

unknown_bundle_revision="${workdir}/unknown-bundle-revision"
create_valid_bundle "${unknown_bundle_revision}"
replace_default_bundle_revision "notarealrevision" \
  "${unknown_bundle_revision}/BUNDLE-MANIFEST.md" \
  "${unknown_bundle_revision}/evidence/install-preflight-output.txt"
assert_fails_with "Invalid offline install bundle repository revision: notarealrevision does not resolve in repository" --bundle-dir "${unknown_bundle_revision}"

mutable_branch_revision="${workdir}/mutable-branch-revision"
create_valid_bundle "${mutable_branch_revision}"
replace_default_bundle_revision "main" \
  "${mutable_branch_revision}/BUNDLE-MANIFEST.md" \
  "${mutable_branch_revision}/evidence/install-preflight-output.txt"
assert_fails_with "Invalid offline install bundle repository revision: main is mutable" --bundle-dir "${mutable_branch_revision}"

missing_bundle_artifact="${workdir}/missing-bundle-artifact"
create_valid_bundle "${missing_bundle_artifact}"
rm "${missing_bundle_artifact}/config/runtime.env.sample"
assert_fails_with "Missing offline install bundle required artifact: config/runtime.env.sample" --bundle-dir "${missing_bundle_artifact}"

invalid_install_readme="${workdir}/invalid-install-readme"
create_valid_bundle "${invalid_install_readme}"
printf '%s\n' "# Offline Install Entry" "Run it." >"${invalid_install_readme}/install/README.md"
assert_fails_with "Missing offline install bundle artifact content in install/README.md" --bundle-dir "${invalid_install_readme}"

placeholder_install_command="${workdir}/placeholder-install-command"
create_valid_bundle "${placeholder_install_command}"
cat >"${placeholder_install_command}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

Offline install entrypoint: run the documented command.
Selected profile: smb-single-node.
Dependency assumptions and manual prerequisites are documented.
EOF_INSTALL
assert_fails_with "Missing offline install bundle artifact content in install/README.md: concrete install command" --bundle-dir "${placeholder_install_command}"

doctor_only_install_command="${workdir}/doctor-only-install-command"
create_valid_bundle "${doctor_only_install_command}"
perl -0pi -e 's/aegisops up/aegisops doctor/g' "${doctor_only_install_command}/install/README.md"
assert_fails_with "Missing offline install bundle artifact content in install/README.md: concrete install command" --bundle-dir "${doctor_only_install_command}"

multiline_install_command="${workdir}/multiline-install-command"
create_valid_bundle "${multiline_install_command}"
cat >"${multiline_install_command}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

Run the offline install entrypoint command from the release bundle root:

```sh
aegisops up \
  --profile smb-single-node \
  --runtime-env <runtime-env-file>
```

Selected profile: smb-single-node.
Dependency assumptions and manual prerequisites are documented.
EOF_INSTALL
assert_passes --bundle-dir "${multiline_install_command}"

negated_multiline_install_command="${workdir}/negated-multiline-install-command"
create_valid_bundle "${negated_multiline_install_command}"
cat >"${negated_multiline_install_command}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

Do not run this offline install entrypoint command; it is shown only as a placeholder for a later release:

```sh
aegisops up \
  --profile smb-single-node \
  --runtime-env <runtime-env-file>
```

Selected profile: smb-single-node.
Dependency assumptions and manual prerequisites are documented.
EOF_INSTALL
assert_fails_with "negated install command" --bundle-dir "${negated_multiline_install_command}"

negated_install_readme="${workdir}/negated-install-readme"
create_valid_bundle "${negated_install_readme}"
cat >"${negated_install_readme}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

No offline install entrypoint is provided.
Selected profile is not documented.
Dependency assumptions and manual prerequisites are unavailable.
EOF_INSTALL
assert_fails_with "negated install guidance" --bundle-dir "${negated_install_readme}"

negated_install_command="${workdir}/negated-install-command"
create_valid_bundle "${negated_install_command}"
cat >"${negated_install_command}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

Do not run `aegisops up --profile smb-single-node --runtime-env <runtime-env-file>`; this command is documented for a later release.
Selected profile: smb-single-node.
Dependency assumptions and manual prerequisites are documented.
EOF_INSTALL
assert_fails_with "negated install command" --bundle-dir "${negated_install_command}"

hosted_download_install_command="${workdir}/hosted-download-install-command"
create_valid_bundle "${hosted_download_install_command}"
printf '%s\n' 'Fetch dependency: `curl https://updates.example.com/aegisops/dependency.tgz`.' >>"${hosted_download_install_command}/install/README.md"
assert_fails_with "hosted download command" --bundle-dir "${hosted_download_install_command}"

registry_pull_install_command="${workdir}/registry-pull-install-command"
create_valid_bundle "${registry_pull_install_command}"
printf '%s\n' 'Fetch dependency: `docker pull ghcr.io/example/aegisops:latest`.' >>"${registry_pull_install_command}/install/README.md"
assert_fails_with "hosted download command" --bundle-dir "${registry_pull_install_command}"

unclassified_https_download="${workdir}/unclassified-https-download"
create_valid_bundle "${unclassified_https_download}"
printf '%s\n' "Fetch the dependency tarball from https://cdn.example.com/aegisops.tgz" >>"${unclassified_https_download}/install/README.md"
assert_fails_with "hosted download command" --bundle-dir "${unclassified_https_download}"

invalid_runtime_sample="${workdir}/invalid-runtime-sample"
create_valid_bundle "${invalid_runtime_sample}"
perl -0pi -e 's/^AEGISOPS_SECRET_SOURCE_DOC=.*\n//m' "${invalid_runtime_sample}/config/runtime.env.sample"
assert_fails_with "Missing offline install bundle artifact content in config/runtime.env.sample" --bundle-dir "${invalid_runtime_sample}"

runtime_sample_doc_only="${workdir}/runtime-sample-doc-only"
create_valid_bundle "${runtime_sample_doc_only}"
cat >"${runtime_sample_doc_only}/config/runtime.env.sample" <<'EOF_ENV'
AEGISOPS_SECRET_SOURCE_DOC=docs/deployment/env-secrets-certs-contract.md
EOF_ENV
assert_fails_with "Missing offline install bundle artifact content in config/runtime.env.sample: selected profile runtime configuration key" --bundle-dir "${runtime_sample_doc_only}"

runtime_sample_concrete_env="${workdir}/runtime-sample-concrete-env"
create_valid_bundle "${runtime_sample_concrete_env}"
perl -0pi -e 's/^AEGISOPS_RUNTIME_ENV=.*$/AEGISOPS_RUNTIME_ENV=\/etc\/aegisops\/runtime.env/m' "${runtime_sample_concrete_env}/config/runtime.env.sample"
assert_fails_with "Missing offline install bundle artifact content in config/runtime.env.sample: placeholder runtime env key" --bundle-dir "${runtime_sample_concrete_env}"

runtime_sample_profile_mismatch="${workdir}/runtime-sample-profile-mismatch"
create_valid_bundle "${runtime_sample_profile_mismatch}"
perl -0pi -e 's/^AEGISOPS_PROFILE=.*$/AEGISOPS_PROFILE=enterprise-prod/m' "${runtime_sample_profile_mismatch}/config/runtime.env.sample"
assert_fails_with "Missing offline install bundle artifact content in config/runtime.env.sample: selected profile runtime configuration key" --bundle-dir "${runtime_sample_profile_mismatch}"

hidden_install_readme_content="${workdir}/hidden-install-readme-content"
create_valid_bundle "${hidden_install_readme_content}"
cat >"${hidden_install_readme_content}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

Run it.
<!-- entrypoint selected profile dependency assumptions manual prerequisites -->
EOF_INSTALL
assert_fails_with "Missing offline install bundle artifact content in install/README.md" --bundle-dir "${hidden_install_readme_content}"

hidden_runtime_sample_content="${workdir}/hidden-runtime-sample-content"
create_valid_bundle "${hidden_runtime_sample_content}"
cat >"${hidden_runtime_sample_content}/config/runtime.env.sample" <<'EOF_ENV'
AEGISOPS_PROFILE=smb-single-node
<!-- docs/deployment/env-secrets-certs-contract.md -->
EOF_ENV
assert_fails_with "Missing offline install bundle artifact content in config/runtime.env.sample" --bundle-dir "${hidden_runtime_sample_content}"

invalid_preflight_revision="${workdir}/invalid-preflight-revision"
create_valid_bundle "${invalid_preflight_revision}"
perl -0pi -e 's/^repository revision:.*$/repository revision: deadbeef1234/m' "${invalid_preflight_revision}/evidence/install-preflight-output.txt"
assert_fails_with "Missing offline install bundle artifact content in evidence/install-preflight-output.txt: matching repository revision" --bundle-dir "${invalid_preflight_revision}"

suffix_preflight_revision="${workdir}/suffix-preflight-revision"
create_valid_bundle "${suffix_preflight_revision}"
perl -0pi -e "s/^release bundle identifier:.*\$/release bundle identifier: ${default_release_bundle_identifier}-extra/m" "${suffix_preflight_revision}/evidence/install-preflight-output.txt"
assert_fails_with "Missing offline install bundle artifact content in evidence/install-preflight-output.txt: matching release bundle identifier" --bundle-dir "${suffix_preflight_revision}"

stale_preflight_suffix_tokens="${workdir}/stale-preflight-suffix-tokens"
create_valid_bundle "${stale_preflight_suffix_tokens}"
cat >"${stale_preflight_suffix_tokens}/evidence/install-preflight-output.txt" <<EOF_EVIDENCE
release bundle identifier: ${default_release_bundle_identifier} stale-bundle
repository revision: ${default_repository_revision} stale-revision
preflight output: retained placeholder for beta/design-partner packaging review.
EOF_EVIDENCE
assert_fails_with "Missing offline install bundle artifact content in evidence/install-preflight-output.txt: matching release bundle identifier" --bundle-dir "${stale_preflight_suffix_tokens}"

invalid_bundled_inventory="${workdir}/invalid-bundled-inventory"
create_valid_bundle "${invalid_bundled_inventory}"
printf '%s\n' "# Invalid Inventory" >"${invalid_bundled_inventory}/docs/phase-65-1-release-bundle-inventory.md"
assert_fails_with "Missing offline install bundle inherited document content in docs/phase-65-1-release-bundle-inventory.md" --bundle-dir "${invalid_bundled_inventory}"

invalid_bundled_contract="${workdir}/invalid-bundled-contract"
create_valid_bundle "${invalid_bundled_contract}"
printf '%s\n' "# Invalid Contract" >"${invalid_bundled_contract}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "Missing offline install bundle inherited document content in docs/phase-65-2-offline-install-bundle-contract.md" --bundle-dir "${invalid_bundled_contract}"

invalid_bundled_gate="${workdir}/invalid-bundled-gate"
create_valid_bundle "${invalid_bundled_gate}"
printf '%s\n' "# Invalid Gate Contract" >"${invalid_bundled_gate}/docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
assert_fails_with "Missing offline install bundle inherited document content in docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md" --bundle-dir "${invalid_bundled_gate}"

invalid_bundled_env_contract="${workdir}/invalid-bundled-env-contract"
create_valid_bundle "${invalid_bundled_env_contract}"
printf '%s\n' "# Invalid Env Contract" >"${invalid_bundled_env_contract}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with "Missing offline install bundle inherited document content in docs/deployment/env-secrets-certs-contract.md" --bundle-dir "${invalid_bundled_env_contract}"

invalid_bundled_runbook="${workdir}/invalid-bundled-runbook"
create_valid_bundle "${invalid_bundled_runbook}"
printf '%s\n' "# Invalid Runbook" >"${invalid_bundled_runbook}/docs/runbook.md"
assert_fails_with "Missing offline install bundle inherited document content in docs/runbook.md" --bundle-dir "${invalid_bundled_runbook}"

reviewed_revision_doc_mismatch_repo="${workdir}/reviewed-revision-doc-mismatch-repo"
create_valid_repo "${reviewed_revision_doc_mismatch_repo}"
printf '%s\n' "Reviewed revision marker for offline bundle comparison." >>"${reviewed_revision_doc_mismatch_repo}/docs/runbook.md"
git -C "${reviewed_revision_doc_mismatch_repo}" init -q
git -C "${reviewed_revision_doc_mismatch_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${reviewed_revision_doc_mismatch_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create reviewed offline bundle doc revision"
git -C "${reviewed_revision_doc_mismatch_repo}" tag "reviewed-doc-v1"
reviewed_revision_doc_mismatch_bundle="${workdir}/reviewed-revision-doc-mismatch-bundle"
create_valid_bundle "${reviewed_revision_doc_mismatch_bundle}"
replace_default_bundle_revision "reviewed-doc-v1" \
  "${reviewed_revision_doc_mismatch_bundle}/BUNDLE-MANIFEST.md" \
  "${reviewed_revision_doc_mismatch_bundle}/evidence/install-preflight-output.txt"
assert_fails_with "Invalid offline install bundle inherited document content: docs/runbook.md" --repo-root "${reviewed_revision_doc_mismatch_repo}" --bundle-dir "${reviewed_revision_doc_mismatch_bundle}"

forbidden_inherited_doc_repo="${workdir}/forbidden-inherited-doc-repo"
create_valid_repo "${forbidden_inherited_doc_repo}"
printf '%s\n' "production secret material: alpha bravo charlie delta" >>"${forbidden_inherited_doc_repo}/docs/runbook.md"
git -C "${forbidden_inherited_doc_repo}" init -q
git -C "${forbidden_inherited_doc_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${forbidden_inherited_doc_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create forbidden inherited doc fixture"
git -C "${forbidden_inherited_doc_repo}" tag "forbidden-doc-v1"
forbidden_inherited_doc_bundle="${workdir}/forbidden-inherited-doc-bundle"
create_valid_bundle "${forbidden_inherited_doc_bundle}"
replace_default_bundle_revision "forbidden-doc-v1" \
  "${forbidden_inherited_doc_bundle}/BUNDLE-MANIFEST.md" \
  "${forbidden_inherited_doc_bundle}/evidence/install-preflight-output.txt"
printf '%s\n' "production secret material: alpha bravo charlie delta" >>"${forbidden_inherited_doc_bundle}/docs/runbook.md"
assert_fails_with "production secret material" --repo-root "${forbidden_inherited_doc_repo}" --bundle-dir "${forbidden_inherited_doc_bundle}"

forbidden_inherited_doc_claim_repo="${workdir}/forbidden-inherited-doc-claim-repo"
create_valid_repo "${forbidden_inherited_doc_claim_repo}"
printf '%s\n' "Offline install bundle proves GA readiness." >>"${forbidden_inherited_doc_claim_repo}/docs/runbook.md"
git -C "${forbidden_inherited_doc_claim_repo}" init -q
git -C "${forbidden_inherited_doc_claim_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${forbidden_inherited_doc_claim_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create forbidden inherited doc claim fixture"
git -C "${forbidden_inherited_doc_claim_repo}" tag "forbidden-doc-claim-v1"
forbidden_inherited_doc_claim_bundle="${workdir}/forbidden-inherited-doc-claim-bundle"
create_valid_bundle "${forbidden_inherited_doc_claim_bundle}"
replace_default_bundle_revision "forbidden-doc-claim-v1" \
  "${forbidden_inherited_doc_claim_bundle}/BUNDLE-MANIFEST.md" \
  "${forbidden_inherited_doc_claim_bundle}/evidence/install-preflight-output.txt"
printf '%s\n' "Offline install bundle proves GA readiness." >>"${forbidden_inherited_doc_claim_bundle}/docs/runbook.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --repo-root "${forbidden_inherited_doc_claim_repo}" --bundle-dir "${forbidden_inherited_doc_claim_bundle}"

forbidden_inherited_doc_direct_readiness_repo="${workdir}/forbidden-inherited-doc-direct-readiness-repo"
create_valid_repo "${forbidden_inherited_doc_direct_readiness_repo}"
printf '%s\n' "RC readiness is complete." >>"${forbidden_inherited_doc_direct_readiness_repo}/docs/runbook.md"
git -C "${forbidden_inherited_doc_direct_readiness_repo}" init -q
git -C "${forbidden_inherited_doc_direct_readiness_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${forbidden_inherited_doc_direct_readiness_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create forbidden inherited direct readiness fixture"
git -C "${forbidden_inherited_doc_direct_readiness_repo}" tag "forbidden-doc-direct-readiness-v1"
forbidden_inherited_doc_direct_readiness_bundle="${workdir}/forbidden-inherited-doc-direct-readiness-bundle"
create_valid_bundle "${forbidden_inherited_doc_direct_readiness_bundle}"
replace_default_bundle_revision "forbidden-doc-direct-readiness-v1" \
  "${forbidden_inherited_doc_direct_readiness_bundle}/BUNDLE-MANIFEST.md" \
  "${forbidden_inherited_doc_direct_readiness_bundle}/evidence/install-preflight-output.txt"
printf '%s\n' "RC readiness is complete." >>"${forbidden_inherited_doc_direct_readiness_bundle}/docs/runbook.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --repo-root "${forbidden_inherited_doc_direct_readiness_repo}" --bundle-dir "${forbidden_inherited_doc_direct_readiness_bundle}"

forbidden_inherited_doc_mixed_readiness_repo="${workdir}/forbidden-inherited-doc-mixed-readiness-repo"
create_valid_repo "${forbidden_inherited_doc_mixed_readiness_repo}"
printf '%s\n' "This runbook does not claim RC readiness, but GA readiness is proven by release notes." >>"${forbidden_inherited_doc_mixed_readiness_repo}/docs/runbook.md"
git -C "${forbidden_inherited_doc_mixed_readiness_repo}" init -q
git -C "${forbidden_inherited_doc_mixed_readiness_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${forbidden_inherited_doc_mixed_readiness_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create forbidden inherited mixed readiness fixture"
git -C "${forbidden_inherited_doc_mixed_readiness_repo}" tag "forbidden-doc-mixed-readiness-v1"
forbidden_inherited_doc_mixed_readiness_bundle="${workdir}/forbidden-inherited-doc-mixed-readiness-bundle"
create_valid_bundle "${forbidden_inherited_doc_mixed_readiness_bundle}"
replace_default_bundle_revision "forbidden-doc-mixed-readiness-v1" \
  "${forbidden_inherited_doc_mixed_readiness_bundle}/BUNDLE-MANIFEST.md" \
  "${forbidden_inherited_doc_mixed_readiness_bundle}/evidence/install-preflight-output.txt"
printf '%s\n' "This runbook does not claim RC readiness, but GA readiness is proven by release notes." >>"${forbidden_inherited_doc_mixed_readiness_bundle}/docs/runbook.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --repo-root "${forbidden_inherited_doc_mixed_readiness_repo}" --bundle-dir "${forbidden_inherited_doc_mixed_readiness_bundle}"

forbidden_inherited_doc_truth_claim_repo="${workdir}/forbidden-inherited-doc-truth-claim-repo"
create_valid_repo "${forbidden_inherited_doc_truth_claim_repo}"
printf '%s\n' "Readiness truth is satisfied by issue-lint output." >>"${forbidden_inherited_doc_truth_claim_repo}/docs/runbook.md"
git -C "${forbidden_inherited_doc_truth_claim_repo}" init -q
git -C "${forbidden_inherited_doc_truth_claim_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${forbidden_inherited_doc_truth_claim_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create forbidden inherited doc truth claim fixture"
git -C "${forbidden_inherited_doc_truth_claim_repo}" tag "forbidden-doc-truth-claim-v1"
forbidden_inherited_doc_truth_claim_bundle="${workdir}/forbidden-inherited-doc-truth-claim-bundle"
create_valid_bundle "${forbidden_inherited_doc_truth_claim_bundle}"
replace_default_bundle_revision "forbidden-doc-truth-claim-v1" \
  "${forbidden_inherited_doc_truth_claim_bundle}/BUNDLE-MANIFEST.md" \
  "${forbidden_inherited_doc_truth_claim_bundle}/evidence/install-preflight-output.txt"
printf '%s\n' "Readiness truth is satisfied by issue-lint output." >>"${forbidden_inherited_doc_truth_claim_bundle}/docs/runbook.md"
assert_fails_with "verifier, issue-lint, install, or smoke truth claim" --repo-root "${forbidden_inherited_doc_truth_claim_repo}" --bundle-dir "${forbidden_inherited_doc_truth_claim_bundle}"

forbidden_inherited_doc_support_bundle_repo="${workdir}/forbidden-inherited-doc-support-bundle-repo"
create_valid_repo "${forbidden_inherited_doc_support_bundle_repo}"
printf '%s\n' "This bundle supports automatic support bundle submission." >>"${forbidden_inherited_doc_support_bundle_repo}/docs/runbook.md"
git -C "${forbidden_inherited_doc_support_bundle_repo}" init -q
git -C "${forbidden_inherited_doc_support_bundle_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${forbidden_inherited_doc_support_bundle_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create forbidden inherited doc support bundle fixture"
git -C "${forbidden_inherited_doc_support_bundle_repo}" tag "forbidden-doc-support-bundle-v1"
forbidden_inherited_doc_support_bundle="${workdir}/forbidden-inherited-doc-support-bundle"
create_valid_bundle "${forbidden_inherited_doc_support_bundle}"
replace_default_bundle_revision "forbidden-doc-support-bundle-v1" \
  "${forbidden_inherited_doc_support_bundle}/BUNDLE-MANIFEST.md" \
  "${forbidden_inherited_doc_support_bundle}/evidence/install-preflight-output.txt"
printf '%s\n' "This bundle supports automatic support bundle submission." >>"${forbidden_inherited_doc_support_bundle}/docs/runbook.md"
assert_fails_with "unsupported support-bundle automation claim" --repo-root "${forbidden_inherited_doc_support_bundle_repo}" --bundle-dir "${forbidden_inherited_doc_support_bundle}"

forbidden_inherited_doc_sbom_complete_repo="${workdir}/forbidden-inherited-doc-sbom-complete-repo"
create_valid_repo "${forbidden_inherited_doc_sbom_complete_repo}"
printf '%s\n' "SBOM generation is complete." >>"${forbidden_inherited_doc_sbom_complete_repo}/docs/runbook.md"
git -C "${forbidden_inherited_doc_sbom_complete_repo}" init -q
git -C "${forbidden_inherited_doc_sbom_complete_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${forbidden_inherited_doc_sbom_complete_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create forbidden inherited doc SBOM fixture"
git -C "${forbidden_inherited_doc_sbom_complete_repo}" tag "forbidden-doc-sbom-complete-v1"
forbidden_inherited_doc_sbom_complete="${workdir}/forbidden-inherited-doc-sbom-complete"
create_valid_bundle "${forbidden_inherited_doc_sbom_complete}"
replace_default_bundle_revision "forbidden-doc-sbom-complete-v1" \
  "${forbidden_inherited_doc_sbom_complete}/BUNDLE-MANIFEST.md" \
  "${forbidden_inherited_doc_sbom_complete}/evidence/install-preflight-output.txt"
printf '%s\n' "SBOM generation is complete." >>"${forbidden_inherited_doc_sbom_complete}/docs/runbook.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --repo-root "${forbidden_inherited_doc_sbom_complete_repo}" --bundle-dir "${forbidden_inherited_doc_sbom_complete}"

forbidden_inherited_doc_hosted_download_repo="${workdir}/forbidden-inherited-doc-hosted-download-repo"
create_valid_repo "${forbidden_inherited_doc_hosted_download_repo}"
printf '%s\n' "Fetch the dependency tarball from https://cdn.example.com/aegisops.tgz" >>"${forbidden_inherited_doc_hosted_download_repo}/docs/runbook.md"
git -C "${forbidden_inherited_doc_hosted_download_repo}" init -q
git -C "${forbidden_inherited_doc_hosted_download_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" add README.md docs
git -C "${forbidden_inherited_doc_hosted_download_repo}" -c user.name="AegisOps Test" -c user.email="aegisops-test@example.invalid" commit -q -m "Create forbidden inherited doc hosted download fixture"
git -C "${forbidden_inherited_doc_hosted_download_repo}" tag "forbidden-doc-hosted-download-v1"
forbidden_inherited_doc_hosted_download="${workdir}/forbidden-inherited-doc-hosted-download"
create_valid_bundle "${forbidden_inherited_doc_hosted_download}"
replace_default_bundle_revision "forbidden-doc-hosted-download-v1" \
  "${forbidden_inherited_doc_hosted_download}/BUNDLE-MANIFEST.md" \
  "${forbidden_inherited_doc_hosted_download}/evidence/install-preflight-output.txt"
printf '%s\n' "Fetch the dependency tarball from https://cdn.example.com/aegisops.tgz" >>"${forbidden_inherited_doc_hosted_download}/docs/runbook.md"
assert_fails_with "hosted download command" --repo-root "${forbidden_inherited_doc_hosted_download_repo}" --bundle-dir "${forbidden_inherited_doc_hosted_download}"

missing_bundled_secrets_contract="${workdir}/missing-bundled-secrets-contract"
create_valid_bundle "${missing_bundled_secrets_contract}"
rm "${missing_bundled_secrets_contract}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with "Missing offline install bundle required artifact: docs/deployment/env-secrets-certs-contract.md" --bundle-dir "${missing_bundled_secrets_contract}"

bundle_local_path="${workdir}/bundle-local-path"
create_valid_bundle "${bundle_local_path}"
printf '%s\n' "operator path: ${local_home_path}" >>"${bundle_local_path}/BUNDLE-MANIFEST.md"
assert_fails_with "workstation-local absolute path" --bundle-dir "${bundle_local_path}"

bundle_file_url_local_path="${workdir}/bundle-file-url-local-path"
create_valid_bundle "${bundle_file_url_local_path}"
printf '%s\n' "operator path: ${file_url_home_path}" >>"${bundle_file_url_local_path}/install/README.md"
assert_fails_with "workstation-local absolute path" --bundle-dir "${bundle_file_url_local_path}"

bundle_system_absolute_path="${workdir}/bundle-system-absolute-path"
create_valid_bundle "${bundle_system_absolute_path}"
printf '%s\n' 'operator path: /var/lib/aegisops/runtime.env' >>"${bundle_system_absolute_path}/install/README.md"
assert_fails_with "workstation-local absolute path" --bundle-dir "${bundle_system_absolute_path}"

bundle_file_url_system_path="${workdir}/bundle-file-url-system-path"
create_valid_bundle "${bundle_file_url_system_path}"
printf '%s\n' 'operator path: file:///etc/aegisops/runtime.env' >>"${bundle_file_url_system_path}/BUNDLE-MANIFEST.md"
assert_fails_with "workstation-local absolute path" --bundle-dir "${bundle_file_url_system_path}"

bundle_workspace_path="${workdir}/bundle-workspace-path"
create_valid_bundle "${bundle_workspace_path}"
printf '%s\n' 'operator path: /workspace/AegisOps/build/output' >>"${bundle_workspace_path}/install/README.md"
assert_fails_with "workstation-local absolute path" --bundle-dir "${bundle_workspace_path}"

bundle_tmp_path="${workdir}/bundle-tmp-path"
create_valid_bundle "${bundle_tmp_path}"
printf '%s\n' 'operator path: /tmp/aegisops/bundle' >>"${bundle_tmp_path}/BUNDLE-MANIFEST.md"
assert_fails_with "workstation-local absolute path" --bundle-dir "${bundle_tmp_path}"

bundle_secret="${workdir}/bundle-secret"
create_valid_bundle "${bundle_secret}"
printf '%s\n' "password: live-production-password" >>"${bundle_secret}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_secret}"

bundle_placeholder_credential="${workdir}/bundle-placeholder-credential"
create_valid_bundle "${bundle_placeholder_credential}"
printf '%s\n' "Placeholder credentials are valid auth for bootstrap." >>"${bundle_placeholder_credential}/config/runtime.env.sample"
assert_fails_with "placeholder credentials accepted as valid auth" --bundle-dir "${bundle_placeholder_credential}"

bundle_customer_private="${workdir}/bundle-customer-private"
create_valid_bundle "${bundle_customer_private}"
printf '%s\n' "Customer-private data included for convenience." >>"${bundle_customer_private}/BUNDLE-MANIFEST.md"
assert_fails_with "customer-private data claim" --bundle-dir "${bundle_customer_private}"

bundle_reversed_customer_private="${workdir}/bundle-reversed-customer-private"
create_valid_bundle "${bundle_reversed_customer_private}"
printf '%s\n' "This bundle includes customer-private data for convenience." >>"${bundle_reversed_customer_private}/BUNDLE-MANIFEST.md"
assert_fails_with "customer-private data claim" --bundle-dir "${bundle_reversed_customer_private}"

bundle_customer_private_copula="${workdir}/bundle-customer-private-copula"
create_valid_bundle "${bundle_customer_private_copula}"
printf '%s\n' "Customer-private records are included for convenience." >>"${bundle_customer_private_copula}/BUNDLE-MANIFEST.md"
assert_fails_with "customer-private data claim" --bundle-dir "${bundle_customer_private_copula}"

bundle_customer_private_required="${workdir}/bundle-customer-private-required"
create_valid_bundle "${bundle_customer_private_required}"
printf '%s\n' "Customer-private data is required during install." >>"${bundle_customer_private_required}/install/README.md"
assert_fails_with "customer-private data claim" --bundle-dir "${bundle_customer_private_required}"

bundle_customer_private_label="${workdir}/bundle-customer-private-label"
create_valid_bundle "${bundle_customer_private_label}"
printf '%s\n' "customer-private records: Acme Corp incident INC-123 includes user jane@example.com" >>"${bundle_customer_private_label}/evidence/install-preflight-output.txt"
assert_fails_with "customer-private data" --bundle-dir "${bundle_customer_private_label}"

bundle_hidden_hosted="${workdir}/bundle-hidden-hosted"
create_valid_bundle "${bundle_hidden_hosted}"
printf '%s\n' "Hidden hosted dependency is required during install." >>"${bundle_hidden_hosted}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_hidden_hosted}"

bundle_hidden_downloads="${workdir}/bundle-hidden-downloads"
create_valid_bundle "${bundle_hidden_downloads}"
printf '%s\n' "Hidden hosted downloads are required during install." >>"${bundle_hidden_downloads}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_hidden_downloads}"

bundle_reversed_hidden_downloads="${workdir}/bundle-reversed-hidden-downloads"
create_valid_bundle "${bundle_reversed_hidden_downloads}"
printf '%s\n' "This bundle includes hidden hosted downloads." >>"${bundle_reversed_hidden_downloads}/BUNDLE-MANIFEST.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_reversed_hidden_downloads}"

bundle_silent_update="${workdir}/bundle-silent-update"
create_valid_bundle "${bundle_silent_update}"
printf '%s\n' "Silent auto-upgrade is enabled after install." >>"${bundle_silent_update}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_silent_update}"

bundle_network_update="${workdir}/bundle-network-update"
create_valid_bundle "${bundle_network_update}"
printf '%s\n' "Network update services are available after install." >>"${bundle_network_update}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_network_update}"

bundle_enables_hosted_update="${workdir}/bundle-enables-hosted-update"
create_valid_bundle "${bundle_enables_hosted_update}"
printf '%s\n' "This bundle enables hosted update services." >>"${bundle_enables_hosted_update}/BUNDLE-MANIFEST.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_enables_hosted_update}"

bundle_hosted_dependency_url="${workdir}/bundle-hosted-dependency-url"
create_valid_bundle "${bundle_hosted_dependency_url}"
printf '%s\n' "DEPENDENCY_URL=https://updates.example.com/aegisops/dependency.tgz" >>"${bundle_hosted_dependency_url}/config/runtime.env.sample"
assert_fails_with "hosted download command" --bundle-dir "${bundle_hosted_dependency_url}"

bundle_unclassified_https_download="${workdir}/bundle-unclassified-https-download"
create_valid_bundle "${bundle_unclassified_https_download}"
printf '%s\n' "Fetch the dependency tarball from https://cdn.example.com/aegisops.tgz" >>"${bundle_unclassified_https_download}/evidence/install-preflight-output.txt"
assert_fails_with "hosted download command" --bundle-dir "${bundle_unclassified_https_download}"

bundle_registry_pull="${workdir}/bundle-registry-pull"
create_valid_bundle "${bundle_registry_pull}"
printf '%s\n' 'Fetch dependency: `docker pull ghcr.io/example/aegisops:latest`.' >>"${bundle_registry_pull}/evidence/install-preflight-output.txt"
assert_fails_with "hosted download command" --bundle-dir "${bundle_registry_pull}"

bundle_background_entitlement="${workdir}/bundle-background-entitlement"
create_valid_bundle "${bundle_background_entitlement}"
printf '%s\n' "Background entitlement checks are enabled after install." >>"${bundle_background_entitlement}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_background_entitlement}"

bundle_entitlement_enforcement="${workdir}/bundle-entitlement-enforcement"
create_valid_bundle "${bundle_entitlement_enforcement}"
printf '%s\n' "Entitlement enforcement is enabled after install." >>"${bundle_entitlement_enforcement}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_entitlement_enforcement}"

bundle_production_billing="${workdir}/bundle-production-billing"
create_valid_bundle "${bundle_production_billing}"
printf '%s\n' "Production billing is enabled after install." >>"${bundle_production_billing}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_production_billing}"

bundle_bare_billing="${workdir}/bundle-bare-billing"
create_valid_bundle "${bundle_bare_billing}"
printf '%s\n' "Billing is enabled after install." >>"${bundle_bare_billing}/BUNDLE-MANIFEST.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_bare_billing}"

bundle_mixed_silent_update="${workdir}/bundle-mixed-silent-update"
create_valid_bundle "${bundle_mixed_silent_update}"
printf '%s\n' "Unsupported hosted update services are documented, and silent auto-upgrade is enabled after install." >>"${bundle_mixed_silent_update}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_mixed_silent_update}"

bundle_negated_clause_silent_update="${workdir}/bundle-negated-clause-silent-update"
create_valid_bundle "${bundle_negated_clause_silent_update}"
printf '%s\n' "This bundle does not claim hosted update service readiness and silent auto-upgrade is enabled after install." >>"${bundle_negated_clause_silent_update}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_negated_clause_silent_update}"

bundle_production_installer="${workdir}/bundle-production-installer"
create_valid_bundle "${bundle_production_installer}"
printf '%s\n' "This bundle provides production installer completeness." >>"${bundle_production_installer}/BUNDLE-MANIFEST.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_production_installer}"

bundle_checksum_completeness="${workdir}/bundle-checksum-completeness"
create_valid_bundle "${bundle_checksum_completeness}"
printf '%s\n' "Bundle files provide checksum completeness." >>"${bundle_checksum_completeness}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --bundle-dir "${bundle_checksum_completeness}"

bundle_sbom_generation="${workdir}/bundle-sbom-generation"
create_valid_bundle "${bundle_sbom_generation}"
printf '%s\n' "SBOM generation is supported by this bundle." >>"${bundle_sbom_generation}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --bundle-dir "${bundle_sbom_generation}"

bundle_sbom_generation_complete="${workdir}/bundle-sbom-generation-complete"
create_valid_bundle "${bundle_sbom_generation_complete}"
printf '%s\n' "SBOM generation is complete." >>"${bundle_sbom_generation_complete}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --bundle-dir "${bundle_sbom_generation_complete}"

bundle_migration_implementation="${workdir}/bundle-migration-implementation"
create_valid_bundle "${bundle_migration_implementation}"
printf '%s\n' "Migration guide implementation is supported by this bundle." >>"${bundle_migration_implementation}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --bundle-dir "${bundle_migration_implementation}"

bundle_licensing_conclusions="${workdir}/bundle-licensing-conclusions"
create_valid_bundle "${bundle_licensing_conclusions}"
printf '%s\n' "Licensing conclusions are approved by this bundle." >>"${bundle_licensing_conclusions}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --bundle-dir "${bundle_licensing_conclusions}"

bundle_commercial_replacement="${workdir}/bundle-commercial-replacement"
create_valid_bundle "${bundle_commercial_replacement}"
printf '%s\n' "Offline install bundle proves commercial replacement readiness." >>"${bundle_commercial_replacement}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --bundle-dir "${bundle_commercial_replacement}"

bundle_self_service_commercial="${workdir}/bundle-self-service-commercial"
create_valid_bundle "${bundle_self_service_commercial}"
printf '%s\n' "Bundle manifest proves self-service commercial readiness." >>"${bundle_self_service_commercial}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported completeness, approval, or readiness claim" --bundle-dir "${bundle_self_service_commercial}"

bundle_quoted_secret_key="${workdir}/bundle-quoted-secret-key"
create_valid_bundle "${bundle_quoted_secret_key}"
printf '%s\n' '"api_key": "live-production-key"' >>"${bundle_quoted_secret_key}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_quoted_secret_key}"

bundle_authorization_header="${workdir}/bundle-authorization-header"
create_valid_bundle "${bundle_authorization_header}"
printf '%s\n' "Authorization: Bearer live-production-token-abcdef1234567890" >>"${bundle_authorization_header}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_authorization_header}"

bundle_credential_url="${workdir}/bundle-credential-url"
create_valid_bundle "${bundle_credential_url}"
printf '%s\n' "DATABASE_URL=postgres://prod_user:live-production-password-abcdef123456@db.example/aegisops" >>"${bundle_credential_url}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_credential_url}"

bundle_inline_comment_secret="${workdir}/bundle-inline-comment-secret"
create_valid_bundle "${bundle_inline_comment_secret}"
printf '%s\n' "AEGISOPS_PROFILE=smb-single-node # API_KEY=live-production-key" >>"${bundle_inline_comment_secret}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_inline_comment_secret}"

bundle_secret_key="${workdir}/bundle-secret-key"
create_valid_bundle "${bundle_secret_key}"
printf '%s\n' "SECRET_KEY=live-production-key-abcdef1234567890" >>"${bundle_secret_key}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_secret_key}"

bundle_jwt_secret="${workdir}/bundle-jwt-secret"
create_valid_bundle "${bundle_jwt_secret}"
printf '%s\n' "JWT_SECRET=live-production-secret-abcdef1234567890" >>"${bundle_jwt_secret}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_jwt_secret}"

bundle_private_key="${workdir}/bundle-private-key"
create_valid_bundle "${bundle_private_key}"
printf '%s\n' "PRIVATE_KEY=live-production-key-abcdef1234567890" >>"${bundle_private_key}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_private_key}"

bundle_pgp_private_key="${workdir}/bundle-pgp-private-key"
create_valid_bundle "${bundle_pgp_private_key}"
printf '%s\n' "-----BEGIN PGP PRIVATE KEY BLOCK-----" >>"${bundle_pgp_private_key}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_pgp_private_key}"

bundle_production_secret_claim="${workdir}/bundle-production-secret-claim"
create_valid_bundle "${bundle_production_secret_claim}"
printf '%s\n' "Production secrets are included in this bundle." >>"${bundle_production_secret_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "production secret material claim" --bundle-dir "${bundle_production_secret_claim}"

bundle_reversed_production_secret_claim="${workdir}/bundle-reversed-production-secret-claim"
create_valid_bundle "${bundle_reversed_production_secret_claim}"
printf '%s\n' "This bundle includes production secret material." >>"${bundle_reversed_production_secret_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "production secret material claim" --bundle-dir "${bundle_reversed_production_secret_claim}"

bundle_production_secret_label="${workdir}/bundle-production-secret-label"
create_valid_bundle "${bundle_production_secret_label}"
printf '%s\n' "production secret material: alpha bravo charlie delta" >>"${bundle_production_secret_label}/config/runtime.env.sample"
assert_fails_with "production secret material" --bundle-dir "${bundle_production_secret_label}"

bundle_customer_specific_secret_provisioning="${workdir}/bundle-customer-specific-secret-provisioning"
create_valid_bundle "${bundle_customer_specific_secret_provisioning}"
printf '%s\n' "Customer-specific secret provisioning is supported by this bundle." >>"${bundle_customer_specific_secret_provisioning}/BUNDLE-MANIFEST.md"
assert_fails_with "customer-specific secret provisioning claim" --bundle-dir "${bundle_customer_specific_secret_provisioning}"

bundle_ga_claim="${workdir}/bundle-ga-claim"
create_valid_bundle "${bundle_ga_claim}"
printf '%s\n' "Bundle manifest proves GA readiness." >>"${bundle_ga_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_ga_claim}"

bundle_rc_proof="${workdir}/bundle-rc-proof"
create_valid_bundle "${bundle_rc_proof}"
printf '%s\n' "This bundle provides RC proof." >>"${bundle_rc_proof}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_rc_proof}"

bundle_files_readiness_claim="${workdir}/bundle-files-readiness-claim"
create_valid_bundle "${bundle_files_readiness_claim}"
printf '%s\n' "Bundle files prove RC gate acceptance." >>"${bundle_files_readiness_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_files_readiness_claim}"

bundle_release_notes_readiness_claim="${workdir}/bundle-release-notes-readiness-claim"
create_valid_bundle "${bundle_release_notes_readiness_claim}"
printf '%s\n' "Release notes satisfy RC gate acceptance." >>"${bundle_release_notes_readiness_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_release_notes_readiness_claim}"

bundle_reversed_ga_claim="${workdir}/bundle-reversed-ga-claim"
create_valid_bundle "${bundle_reversed_ga_claim}"
printf '%s\n' "GA readiness is proven by bundle manifest." >>"${bundle_reversed_ga_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_reversed_ga_claim}"

bundle_reversed_files_readiness_claim="${workdir}/bundle-reversed-files-readiness-claim"
create_valid_bundle "${bundle_reversed_files_readiness_claim}"
printf '%s\n' "RC readiness is proven by bundle files." >>"${bundle_reversed_files_readiness_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_reversed_files_readiness_claim}"

bundle_negated_clause_ga_claim="${workdir}/bundle-negated-clause-ga-claim"
create_valid_bundle "${bundle_negated_clause_ga_claim}"
printf '%s\n' "This bundle does not claim RC readiness, but GA readiness is proven by bundle manifest." >>"${bundle_negated_clause_ga_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_negated_clause_ga_claim}"

bundle_negated_clause_truth_claim="${workdir}/bundle-negated-clause-truth-claim"
create_valid_bundle "${bundle_negated_clause_truth_claim}"
printf '%s\n' "Verifier output is not readiness truth, but it is release truth." >>"${bundle_negated_clause_truth_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "positive claim after negated boundary" --bundle-dir "${bundle_negated_clause_truth_claim}"

bundle_reversed_truth="${workdir}/bundle-reversed-truth"
create_valid_bundle "${bundle_reversed_truth}"
printf '%s\n' "Release truth is established by verifier output." >>"${bundle_reversed_truth}/BUNDLE-MANIFEST.md"
assert_fails_with "verifier, issue-lint, install, or smoke truth claim" --bundle-dir "${bundle_reversed_truth}"

bundle_manifest_truth="${workdir}/bundle-manifest-truth"
create_valid_bundle "${bundle_manifest_truth}"
printf '%s\n' "Bundle manifest is release truth." >>"${bundle_manifest_truth}/BUNDLE-MANIFEST.md"
assert_fails_with "verifier, issue-lint, install, or smoke truth claim" --bundle-dir "${bundle_manifest_truth}"

bundle_authority="${workdir}/bundle-authority"
create_valid_bundle "${bundle_authority}"
printf '%s\n' "This contract is release gate authority." >>"${bundle_authority}/BUNDLE-MANIFEST.md"
assert_fails_with "bundle authority claim" --bundle-dir "${bundle_authority}"

bundle_gate_substitute="${workdir}/bundle-gate-substitute"
create_valid_bundle "${bundle_gate_substitute}"
printf '%s\n' "This contract is substitute evidence for the Phase 51.3 gate contract." >>"${bundle_gate_substitute}/BUNDLE-MANIFEST.md"
assert_fails_with "bundle authority claim" --bundle-dir "${bundle_gate_substitute}"

bundle_self_authority="${workdir}/bundle-self-authority"
create_valid_bundle "${bundle_self_authority}"
printf '%s\n' "This bundle is billing authority." >>"${bundle_self_authority}/BUNDLE-MANIFEST.md"
assert_fails_with "bundle authority claim" --bundle-dir "${bundle_self_authority}"

bundle_stale_preflight_release="${workdir}/bundle-stale-preflight-release"
create_valid_bundle "${bundle_stale_preflight_release}"
cat >"${bundle_stale_preflight_release}/evidence/install-preflight-output.txt" <<EOF_EVIDENCE
previous release bundle identifier: ${default_release_bundle_identifier}
release bundle identifier: aegisops-beta-deadbeef1234
repository revision: ${default_repository_revision}
preflight output: retained placeholder for beta/design-partner packaging review.
EOF_EVIDENCE
assert_fails_with "Missing offline install bundle artifact content in evidence/install-preflight-output.txt: matching release bundle identifier" --bundle-dir "${bundle_stale_preflight_release}"

bundle_support_automation="${workdir}/bundle-support-automation"
create_valid_bundle "${bundle_support_automation}"
printf '%s\n' "Automatic support-bundle submission is enabled after install." >>"${bundle_support_automation}/install/README.md"
assert_fails_with "unsupported support-bundle automation claim" --bundle-dir "${bundle_support_automation}"

bundle_reversed_support_automation="${workdir}/bundle-reversed-support-automation"
create_valid_bundle "${bundle_reversed_support_automation}"
printf '%s\n' "This bundle supports automatic support-bundle submission." >>"${bundle_reversed_support_automation}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported support-bundle automation claim" --bundle-dir "${bundle_reversed_support_automation}"

bundle_unhyphenated_support_automation="${workdir}/bundle-unhyphenated-support-automation"
create_valid_bundle "${bundle_unhyphenated_support_automation}"
printf '%s\n' "This bundle supports automatic support bundle submission." >>"${bundle_unhyphenated_support_automation}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported support-bundle automation claim" --bundle-dir "${bundle_unhyphenated_support_automation}"

bundle_negated_clause_support_automation="${workdir}/bundle-negated-clause-support-automation"
create_valid_bundle "${bundle_negated_clause_support_automation}"
printf '%s\n' "This bundle does not claim support readiness, but automatic support-bundle submission is enabled after install." >>"${bundle_negated_clause_support_automation}/BUNDLE-MANIFEST.md"
assert_fails_with "unsupported support-bundle automation claim" --bundle-dir "${bundle_negated_clause_support_automation}"

bundle_symlink_artifact="${workdir}/bundle-symlink-artifact"
create_valid_bundle "${bundle_symlink_artifact}"
mv "${bundle_symlink_artifact}/install/README.md" "${workdir}/external-install-readme.md"
ln -s "${workdir}/external-install-readme.md" "${bundle_symlink_artifact}/install/README.md"
assert_fails_with "symlink is not allowed" --bundle-dir "${bundle_symlink_artifact}"

echo "Phase 65.2 offline install bundle contract verifier self-test passed."
