#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-2-offline-install-bundle-contract.sh"

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

create_valid_bundle() {
  local target="$1"

  mkdir -p \
    "${target}/install" \
    "${target}/config" \
    "${target}/evidence" \
    "${target}/docs/deployment"

  cat >"${target}/BUNDLE-MANIFEST.md" <<'EOF_MANIFEST'
# Offline Install Bundle Manifest

contract identifier: phase-65-offline-install-bundle-contract-v1
inventory identifier: phase-65-release-bundle-inventory-v1
release bundle identifier: aegisops-beta-cea7db232373
repository revision: cea7db232373
bundle owner: AegisOps maintainers
per-artifact owner: Platform maintainers
bundle creation timestamp: 2026-06-02T00:00:00Z
environment assumption: offline-beta-design-partner
required artifact manifest path: BUNDLE-MANIFEST.md
exclusion review: no workstation-local paths, production secrets, customer-private data, hidden hosted dependency, hosted update service, silent update, production installer, entitlement, billing, RC pass, or GA pass claims.
verifier output: bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>
approval record: issue #1384 / PR #1389
EOF_MANIFEST

  cat >"${target}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

Run the reviewed offline install entrypoint from the release bundle root after host preflight passes.
Use the selected profile `smb-single-node`, keep dependency assumptions explicit, complete manual prerequisites, and retain output under <evidence-dir>.
EOF_INSTALL

  cat >"${target}/config/runtime.env.sample" <<'EOF_ENV'
# Runtime environment sample

AEGISOPS_PROFILE=smb-single-node
AEGISOPS_RUNTIME_ENV=<runtime-env-file>
AEGISOPS_SECRET_SOURCE_DOC=docs/deployment/env-secrets-certs-contract.md
# Secrets must come from trusted local custody and must not be embedded here.
EOF_ENV

  cat >"${target}/evidence/install-preflight-output.txt" <<'EOF_EVIDENCE'
release bundle identifier: aegisops-beta-cea7db232373
repository revision: cea7db232373
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

production_installer_repo="${workdir}/production-installer"
create_valid_repo "${production_installer_repo}"
printf '%s\n' "This bundle provides production installer completeness." >>"${production_installer_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${production_installer_repo}"

production_installer_complete_repo="${workdir}/production-installer-complete"
create_valid_repo "${production_installer_complete_repo}"
printf '%s\n' "Production installer is complete for this bundle." >>"${production_installer_complete_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${production_installer_complete_repo}"

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

placeholder_secret_sample_bundle="${workdir}/placeholder-secret-sample-bundle"
create_valid_bundle "${placeholder_secret_sample_bundle}"
printf '%s\n' "DB_PASSWORD=<db-password>" "API_KEY=placeholder" >>"${placeholder_secret_sample_bundle}/config/runtime.env.sample"
assert_passes --bundle-dir "${placeholder_secret_sample_bundle}"

dotted_revision_bundle="${workdir}/dotted-revision-bundle"
create_valid_bundle "${dotted_revision_bundle}"
perl -0pi -e 's/cea7db232373/v1.2.3/g; s/aegisops-beta-cea7db232373/aegisops-beta-v1.2.3/g' \
  "${dotted_revision_bundle}/BUNDLE-MANIFEST.md" \
  "${dotted_revision_bundle}/evidence/install-preflight-output.txt"
assert_passes --bundle-dir "${dotted_revision_bundle}"

dotted_revision_mismatch="${workdir}/dotted-revision-mismatch"
create_valid_bundle "${dotted_revision_mismatch}"
perl -0pi -e 's/cea7db232373/v1.2.3/g; s/aegisops-beta-cea7db232373/aegisops-beta-v1.2.3/g' \
  "${dotted_revision_mismatch}/BUNDLE-MANIFEST.md"
perl -0pi -e 's/cea7db232373/v1X2X3/g; s/aegisops-beta-cea7db232373/aegisops-beta-v1X2X3/g' \
  "${dotted_revision_mismatch}/evidence/install-preflight-output.txt"
assert_fails_with "Missing offline install bundle artifact content in evidence/install-preflight-output.txt: matching release bundle identifier" --bundle-dir "${dotted_revision_mismatch}"

missing_bundle_metadata="${workdir}/missing-bundle-metadata"
create_valid_bundle "${missing_bundle_metadata}"
perl -0pi -e 's/^bundle creation timestamp:.*\n//m' "${missing_bundle_metadata}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: bundle creation timestamp" --bundle-dir "${missing_bundle_metadata}"

missing_approval_record="${workdir}/missing-approval-record"
create_valid_bundle "${missing_approval_record}"
perl -0pi -e 's/^approval record:.*\n//m' "${missing_approval_record}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: approval record" --bundle-dir "${missing_approval_record}"

commented_manifest_metadata="${workdir}/commented-manifest-metadata"
create_valid_bundle "${commented_manifest_metadata}"
perl -0pi -e 's/^contract identifier:.*$/<!-- contract identifier: phase-65-offline-install-bundle-contract-v1 -->/m' "${commented_manifest_metadata}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: contract identifier" --bundle-dir "${commented_manifest_metadata}"

blank_bundle_owner="${workdir}/blank-bundle-owner"
create_valid_bundle "${blank_bundle_owner}"
perl -0pi -e 's/^bundle owner:.*$/bundle owner: /m' "${blank_bundle_owner}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata value: bundle owner" --bundle-dir "${blank_bundle_owner}"

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

missing_bundle_artifact="${workdir}/missing-bundle-artifact"
create_valid_bundle "${missing_bundle_artifact}"
rm "${missing_bundle_artifact}/config/runtime.env.sample"
assert_fails_with "Missing offline install bundle required artifact: config/runtime.env.sample" --bundle-dir "${missing_bundle_artifact}"

invalid_install_readme="${workdir}/invalid-install-readme"
create_valid_bundle "${invalid_install_readme}"
printf '%s\n' "# Offline Install Entry" "Run it." >"${invalid_install_readme}/install/README.md"
assert_fails_with "Missing offline install bundle artifact content in install/README.md" --bundle-dir "${invalid_install_readme}"

negated_install_readme="${workdir}/negated-install-readme"
create_valid_bundle "${negated_install_readme}"
cat >"${negated_install_readme}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

No offline install entrypoint is provided.
Selected profile is not documented.
Dependency assumptions and manual prerequisites are unavailable.
EOF_INSTALL
assert_fails_with "negated install guidance" --bundle-dir "${negated_install_readme}"

invalid_runtime_sample="${workdir}/invalid-runtime-sample"
create_valid_bundle "${invalid_runtime_sample}"
perl -0pi -e 's/^AEGISOPS_SECRET_SOURCE_DOC=.*\n//m' "${invalid_runtime_sample}/config/runtime.env.sample"
assert_fails_with "Missing offline install bundle artifact content in config/runtime.env.sample" --bundle-dir "${invalid_runtime_sample}"

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
perl -0pi -e 's/^release bundle identifier:.*$/release bundle identifier: aegisops-beta-cea7db232373-extra/m' "${suffix_preflight_revision}/evidence/install-preflight-output.txt"
assert_fails_with "Missing offline install bundle artifact content in evidence/install-preflight-output.txt: matching release bundle identifier" --bundle-dir "${suffix_preflight_revision}"

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

missing_bundled_secrets_contract="${workdir}/missing-bundled-secrets-contract"
create_valid_bundle "${missing_bundled_secrets_contract}"
rm "${missing_bundled_secrets_contract}/docs/deployment/env-secrets-certs-contract.md"
assert_fails_with "Missing offline install bundle required artifact: docs/deployment/env-secrets-certs-contract.md" --bundle-dir "${missing_bundled_secrets_contract}"

bundle_local_path="${workdir}/bundle-local-path"
create_valid_bundle "${bundle_local_path}"
printf '%s\n' "operator path: ${local_home_path}" >>"${bundle_local_path}/BUNDLE-MANIFEST.md"
assert_fails_with "workstation-local absolute path" --bundle-dir "${bundle_local_path}"

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

bundle_customer_private_copula="${workdir}/bundle-customer-private-copula"
create_valid_bundle "${bundle_customer_private_copula}"
printf '%s\n' "Customer-private records are included for convenience." >>"${bundle_customer_private_copula}/BUNDLE-MANIFEST.md"
assert_fails_with "customer-private data claim" --bundle-dir "${bundle_customer_private_copula}"

bundle_customer_private_required="${workdir}/bundle-customer-private-required"
create_valid_bundle "${bundle_customer_private_required}"
printf '%s\n' "Customer-private data is required during install." >>"${bundle_customer_private_required}/install/README.md"
assert_fails_with "customer-private data claim" --bundle-dir "${bundle_customer_private_required}"

bundle_hidden_hosted="${workdir}/bundle-hidden-hosted"
create_valid_bundle "${bundle_hidden_hosted}"
printf '%s\n' "Hidden hosted dependency is required during install." >>"${bundle_hidden_hosted}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_hidden_hosted}"

bundle_hidden_downloads="${workdir}/bundle-hidden-downloads"
create_valid_bundle "${bundle_hidden_downloads}"
printf '%s\n' "Hidden hosted downloads are required during install." >>"${bundle_hidden_downloads}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_hidden_downloads}"

bundle_silent_update="${workdir}/bundle-silent-update"
create_valid_bundle "${bundle_silent_update}"
printf '%s\n' "Silent auto-upgrade is enabled after install." >>"${bundle_silent_update}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_silent_update}"

bundle_network_update="${workdir}/bundle-network-update"
create_valid_bundle "${bundle_network_update}"
printf '%s\n' "Network update services are available after install." >>"${bundle_network_update}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_network_update}"

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

bundle_inline_comment_secret="${workdir}/bundle-inline-comment-secret"
create_valid_bundle "${bundle_inline_comment_secret}"
printf '%s\n' "AEGISOPS_PROFILE=smb-single-node # API_KEY=live-production-key" >>"${bundle_inline_comment_secret}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_inline_comment_secret}"

bundle_secret_key="${workdir}/bundle-secret-key"
create_valid_bundle "${bundle_secret_key}"
printf '%s\n' "SECRET_KEY=live-production-key-abcdef1234567890" >>"${bundle_secret_key}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_secret_key}"

bundle_production_secret_claim="${workdir}/bundle-production-secret-claim"
create_valid_bundle "${bundle_production_secret_claim}"
printf '%s\n' "Production secrets are included in this bundle." >>"${bundle_production_secret_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "production secret material claim" --bundle-dir "${bundle_production_secret_claim}"

bundle_ga_claim="${workdir}/bundle-ga-claim"
create_valid_bundle "${bundle_ga_claim}"
printf '%s\n' "Bundle manifest proves GA readiness." >>"${bundle_ga_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_ga_claim}"

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

bundle_self_authority="${workdir}/bundle-self-authority"
create_valid_bundle "${bundle_self_authority}"
printf '%s\n' "This bundle is billing authority." >>"${bundle_self_authority}/BUNDLE-MANIFEST.md"
assert_fails_with "bundle authority claim" --bundle-dir "${bundle_self_authority}"

bundle_stale_preflight_release="${workdir}/bundle-stale-preflight-release"
create_valid_bundle "${bundle_stale_preflight_release}"
cat >"${bundle_stale_preflight_release}/evidence/install-preflight-output.txt" <<'EOF_EVIDENCE'
previous release bundle identifier: aegisops-beta-cea7db232373
release bundle identifier: aegisops-beta-deadbeef1234
repository revision: cea7db232373
preflight output: retained placeholder for beta/design-partner packaging review.
EOF_EVIDENCE
assert_fails_with "Missing offline install bundle artifact content in evidence/install-preflight-output.txt: matching release bundle identifier" --bundle-dir "${bundle_stale_preflight_release}"

bundle_support_automation="${workdir}/bundle-support-automation"
create_valid_bundle "${bundle_support_automation}"
printf '%s\n' "Automatic support-bundle submission is enabled after install." >>"${bundle_support_automation}/install/README.md"
assert_fails_with "unsupported support-bundle automation claim" --bundle-dir "${bundle_support_automation}"

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
