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
release bundle identifier: aegisops-beta-<repository-revision>
repository revision: <repository-revision>
bundle owner: AegisOps maintainers
per-artifact owner: Platform maintainers
bundle creation timestamp: <bundle-created-at>
environment assumption: offline-beta-design-partner
exclusion review: no workstation-local paths, production secrets, customer-private data, hidden hosted dependency, hosted update service, silent update, production installer, entitlement, billing, RC pass, or GA pass claims.
verifier output: bash scripts/verify-phase-65-2-offline-install-bundle-contract.sh --bundle-dir <release-bundle-dir>
EOF_MANIFEST

  cat >"${target}/install/README.md" <<'EOF_INSTALL'
# Offline Install Entry

Run the reviewed install entrypoint from the release bundle root after host preflight passes.
Use repo-relative guidance and retain output under <evidence-dir>.
EOF_INSTALL

  cat >"${target}/config/runtime.env.sample" <<'EOF_ENV'
# Runtime environment sample

AEGISOPS_PROFILE=smb-single-node
AEGISOPS_RUNTIME_ENV=<runtime-env-file>
# Secrets must come from trusted local custody and must not be embedded here.
EOF_ENV

  cat >"${target}/evidence/install-preflight-output.txt" <<'EOF_EVIDENCE'
release bundle identifier: aegisops-beta-<repository-revision>
repository revision: <repository-revision>
preflight output: retained placeholder for beta/design-partner packaging review.
EOF_EVIDENCE

  copy_repo_path "${repo_root}" "${target}" "docs/phase-65-2-offline-install-bundle-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/phase-65-1-release-bundle-inventory.md"
  copy_repo_path "${repo_root}" "${target}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/first-user-stack.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/host-preflight-contract.md"
  copy_repo_path "${repo_root}" "${target}" "docs/deployment/clean-host-smoke-skeleton.md"
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

local_path_repo="${workdir}/local-path"
create_valid_repo "${local_path_repo}"
local_home_path="/""Users/example/aegisops"
printf '%s\n' "Do not use ${local_home_path} in publishable guidance." >>"${local_path_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "workstation-local absolute path" --repo-root "${local_path_repo}"

secret_repo="${workdir}/secret"
create_valid_repo "${secret_repo}"
printf '%s\n' "api_key = live-secret-looking-value" >>"${secret_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "production secret-looking value" --repo-root "${secret_repo}"

hosted_update_repo="${workdir}/hosted-update"
create_valid_repo "${hosted_update_repo}"
printf '%s\n' "Hosted update service is enabled by this bundle." >>"${hosted_update_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --repo-root "${hosted_update_repo}"

rc_claim_repo="${workdir}/rc-claim"
create_valid_repo "${rc_claim_repo}"
printf '%s\n' "Offline install bundle proves RC readiness." >>"${rc_claim_repo}/docs/phase-65-2-offline-install-bundle-contract.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --repo-root "${rc_claim_repo}"

valid_bundle="${workdir}/valid-bundle"
create_valid_bundle "${valid_bundle}"
assert_passes --bundle-dir "${valid_bundle}"

missing_bundle_metadata="${workdir}/missing-bundle-metadata"
create_valid_bundle "${missing_bundle_metadata}"
perl -0pi -e 's/^bundle creation timestamp:.*\n//m' "${missing_bundle_metadata}/BUNDLE-MANIFEST.md"
assert_fails_with "Missing offline install bundle metadata: bundle creation timestamp:" --bundle-dir "${missing_bundle_metadata}"

missing_bundle_artifact="${workdir}/missing-bundle-artifact"
create_valid_bundle "${missing_bundle_artifact}"
rm "${missing_bundle_artifact}/config/runtime.env.sample"
assert_fails_with "Missing offline install bundle required artifact: config/runtime.env.sample" --bundle-dir "${missing_bundle_artifact}"

bundle_local_path="${workdir}/bundle-local-path"
create_valid_bundle "${bundle_local_path}"
printf '%s\n' "operator path: ${local_home_path}" >>"${bundle_local_path}/BUNDLE-MANIFEST.md"
assert_fails_with "workstation-local absolute path" --bundle-dir "${bundle_local_path}"

bundle_secret="${workdir}/bundle-secret"
create_valid_bundle "${bundle_secret}"
printf '%s\n' "password: live-production-password" >>"${bundle_secret}/config/runtime.env.sample"
assert_fails_with "production secret-looking value" --bundle-dir "${bundle_secret}"

bundle_customer_private="${workdir}/bundle-customer-private"
create_valid_bundle "${bundle_customer_private}"
printf '%s\n' "Customer-private data included for convenience." >>"${bundle_customer_private}/BUNDLE-MANIFEST.md"
assert_fails_with "customer-private data claim" --bundle-dir "${bundle_customer_private}"

bundle_hidden_hosted="${workdir}/bundle-hidden-hosted"
create_valid_bundle "${bundle_hidden_hosted}"
printf '%s\n' "Hidden hosted dependency is required during install." >>"${bundle_hidden_hosted}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_hidden_hosted}"

bundle_silent_update="${workdir}/bundle-silent-update"
create_valid_bundle "${bundle_silent_update}"
printf '%s\n' "Silent auto-upgrade is enabled after install." >>"${bundle_silent_update}/install/README.md"
assert_fails_with "hosted, silent update, production installer, entitlement, or billing claim" --bundle-dir "${bundle_silent_update}"

bundle_ga_claim="${workdir}/bundle-ga-claim"
create_valid_bundle "${bundle_ga_claim}"
printf '%s\n' "Bundle manifest proves GA readiness." >>"${bundle_ga_claim}/BUNDLE-MANIFEST.md"
assert_fails_with "inferred Beta/RC/GA readiness claim" --bundle-dir "${bundle_ga_claim}"

echo "Phase 65.2 offline install bundle contract verifier self-test passed."
