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
  copy_repo_path "${target}" "docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
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

missing_source_repo="${workdir}/missing-source-version"
create_valid_repo "${missing_source_repo}"
perl -0pi -e 's/^[[:space:]]*source_version:.*\n//mg' "${missing_source_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_source_repo}" "Missing Phase 65.3 upgrade manifest content: source version"

missing_target_repo="${workdir}/missing-target-version"
create_valid_repo "${missing_target_repo}"
perl -0pi -e 's/^[[:space:]]*target_version:.*\n//mg' "${missing_target_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_target_repo}" "Missing Phase 65.3 upgrade manifest content: target version"

missing_compatibility_repo="${workdir}/missing-compatibility"
create_valid_repo "${missing_compatibility_repo}"
perl -0pi -e 's/^[[:space:]]*compatibility_posture:.*\n//mg' "${missing_compatibility_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_compatibility_repo}" "Missing Phase 65.3 upgrade manifest content: compatible version posture case"

missing_incompatible_repo="${workdir}/missing-incompatible"
create_valid_repo "${missing_incompatible_repo}"
perl -0pi -e 's/^[[:space:]]*compatibility_posture: incompatible\n//m' "${missing_incompatible_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_incompatible_repo}" "Missing Phase 65.3 upgrade manifest content: incompatible version posture case"

missing_rollback_repo="${workdir}/missing-rollback"
create_valid_repo "${missing_rollback_repo}"
perl -0pi -e 's/^[[:space:]]*rollback_expectation:.*\n//mg' "${missing_rollback_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_rollback_repo}" "Missing Phase 65.3 upgrade manifest content: rollback expectation"

missing_required_checks_repo="${workdir}/missing-required-checks"
create_valid_repo "${missing_required_checks_repo}"
perl -0pi -e 's/^[[:space:]]*required_checks:\n(?:[[:space:]]*-[^\n]*\n)+//mg' "${missing_required_checks_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_required_checks_repo}" "Missing Phase 65.3 upgrade manifest content: required checks"

missing_limitations_repo="${workdir}/missing-limitations"
create_valid_repo "${missing_limitations_repo}"
perl -0pi -e 's/^[[:space:]]*known_limitation_references:\n(?:[[:space:]]*-[^\n]*\n)+//mg' "${missing_limitations_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${missing_limitations_repo}" "Missing Phase 65.3 upgrade manifest content: known limitation references"

silent_upgrade_repo="${workdir}/silent-upgrade"
create_valid_repo "${silent_upgrade_repo}"
printf '%s\n' "Silent auto-upgrade is enabled for compatible versions." >>"${silent_upgrade_repo}/docs/deployment/release/phase-65-3-upgrade-manifest.yaml"
assert_fails_with "${silent_upgrade_repo}" "silent auto-upgrade or automatic migration claim"

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
