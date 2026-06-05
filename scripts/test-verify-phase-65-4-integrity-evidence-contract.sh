#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
verifier="${repo_root}/scripts/verify-phase-65-4-integrity-evidence-contract.sh"

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
  copy_repo_path "${target}" "docs/phase-65-4-integrity-evidence-contract.md"
  copy_repo_path "${target}" "docs/phase-65-1-release-bundle-inventory.md"
  copy_repo_path "${target}" "docs/phase-65-2-offline-install-bundle-contract.md"
  copy_repo_path "${target}" "docs/phase-65-3-release-channel-upgrade-manifest-contract.md"
  copy_repo_path "${target}" "docs/phase-51-3-pilot-beta-rc-ga-gate-contract.md"
  copy_repo_path "${target}" "docs/deployment/release/phase-65-4-integrity-evidence.yaml"
  copy_repo_path "${target}" "scripts/verify-publishable-path-hygiene.sh"
  copy_repo_path "${target}" "scripts/verify-phase-65-4-integrity-evidence-contract.sh"
  mkdir -p "${target}/control-plane/aegisops/control_plane"
  : >"${target}/control-plane/aegisops/__init__.py"
  : >"${target}/control-plane/aegisops/control_plane/__init__.py"
  copy_repo_path "${target}" "control-plane/aegisops/control_plane/publishable_paths.py"
  git -C "${target}" init -q
  git -C "${target}" config user.email "phase-65-4-test@example.invalid"
  git -C "${target}" config user.name "Phase 65.4 Test"
  git -C "${target}" add README.md docs scripts control-plane
  git -C "${target}" commit -q -m "fixture"
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
    "${target}/docs/phase-65-4-integrity-evidence-contract.md"
}

valid_repo="${workdir}/valid"
create_valid_repo "${valid_repo}"
assert_passes "${valid_repo}"

missing_contract_repo="${workdir}/missing-contract"
create_valid_repo "${missing_contract_repo}"
rm "${missing_contract_repo}/docs/phase-65-4-integrity-evidence-contract.md"
assert_fails_with "${missing_contract_repo}" "Missing Phase 65.4 integrity evidence contract"

missing_manifest_repo="${workdir}/missing-manifest"
create_valid_repo "${missing_manifest_repo}"
rm "${missing_manifest_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${missing_manifest_repo}" "Missing Phase 65.4 integrity evidence manifest"

missing_readme_repo="${workdir}/missing-readme"
create_valid_repo "${missing_readme_repo}"
perl -0pi -e 's/- \[Phase 65\.4 integrity evidence contract\]\(docs\/phase-65-4-integrity-evidence-contract\.md\)[^\n]*\n//m' \
  "${missing_readme_repo}/README.md"
assert_fails_with "${missing_readme_repo}" "Missing README canonical cross-phase boundary bullet"

missing_sbom_repo="${workdir}/missing-sbom"
create_valid_repo "${missing_sbom_repo}"
perl -0pi -e 's/^    sbom_reference:.*\n//m' "${missing_sbom_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${missing_sbom_repo}" "Missing Phase 65.4 integrity manifest sbom_reference for offline-install-bundle"

missing_checksum_repo="${workdir}/missing-checksum"
create_valid_repo "${missing_checksum_repo}"
perl -0pi -e 's/^    checksum_reference:.*\n//m' "${missing_checksum_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${missing_checksum_repo}" "Missing Phase 65.4 integrity manifest checksum_reference for offline-install-bundle"

missing_signature_repo="${workdir}/missing-signature"
create_valid_repo "${missing_signature_repo}"
perl -0pi -e 's/^    signature_reference:.*\n//m' "${missing_signature_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${missing_signature_repo}" "Missing Phase 65.4 integrity manifest signature_reference for offline-install-bundle"

artifact_name_mismatch_repo="${workdir}/artifact-name-mismatch"
create_valid_repo "${artifact_name_mismatch_repo}"
perl -0pi -e 's#offline-install-bundle\.sha256#release-notes.sha256#m' "${artifact_name_mismatch_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${artifact_name_mismatch_repo}" "Missing Phase 65.4 checksum evidence for offline-install-bundle"

checksum_value_mismatch_repo="${workdir}/checksum-value-mismatch"
create_valid_repo "${checksum_value_mismatch_repo}"
perl -0pi -e 's#<sha256:offline-install-bundle>#<sha256:release-notes>#m' "${checksum_value_mismatch_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${checksum_value_mismatch_repo}" "Invalid Phase 65.4 artifact-name mismatch for offline-install-bundle"

readiness_overclaim_repo="${workdir}/readiness-overclaim"
create_valid_repo "${readiness_overclaim_repo}"
printf '%s\n' "Phase 65.4 integrity evidence proves RC readiness." >>"${readiness_overclaim_repo}/docs/phase-65-4-integrity-evidence-contract.md"
assert_fails_with "${readiness_overclaim_repo}" "Forbidden Phase 65.4 integrity evidence claim"

verifier_truth_repo="${workdir}/verifier-truth"
create_valid_repo "${verifier_truth_repo}"
printf '%s\n' "The verifier output becomes readiness truth." >>"${verifier_truth_repo}/docs/phase-65-4-integrity-evidence-contract.md"
assert_fails_with "${verifier_truth_repo}" "verifier or issue-lint truth shortcut"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
workstation_checksum_path="/""Users/example/release-notes.sha256"
WORKSTATION_CHECKSUM_PATH="${workstation_checksum_path}" perl -0pi -e 's#<evidence-dir>/release-notes\.sha256#$ENV{WORKSTATION_CHECKSUM_PATH}#m' "${workstation_path_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${workstation_path_repo}" "Invalid Phase 65.4 integrity manifest artifact reference"

production_secret_repo="${workdir}/production-secret"
create_valid_repo "${production_secret_repo}"
printf '%s\n' "signing_secret: prod-secret-value" >>"${production_secret_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${production_secret_repo}" "Invalid Phase 65.4 integrity manifest top-level field: signing_secret"

production_secret_doc_repo="${workdir}/production-secret-doc"
create_valid_repo "${production_secret_doc_repo}"
printf '%s\n' "password: prod-secret-value" >>"${production_secret_doc_repo}/docs/phase-65-4-integrity-evidence-contract.md"
assert_fails_with "${production_secret_doc_repo}" "production secret material"

missing_doc_term_repo="${workdir}/missing-doc-term"
create_valid_repo "${missing_doc_term_repo}"
remove_doc_text "${missing_doc_term_repo}" "missing signature evidence;"
assert_fails_with "${missing_doc_term_repo}" "Missing required Phase 65.4 integrity contract term"

echo "Phase 65.4 integrity evidence verifier self-test passed."
