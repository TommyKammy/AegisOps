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
  fixture_revision="$(git -C "${target}" rev-parse HEAD)"
  FIXTURE_REVISION="${fixture_revision}" perl -0pi -e 's/[0-9a-f]{40}/$ENV{FIXTURE_REVISION}/g' \
    "${target}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
  git -C "${target}" add docs/deployment/release/phase-65-4-integrity-evidence.yaml
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

release_identifier_mismatch_repo="${workdir}/release-identifier-mismatch"
create_valid_repo "${release_identifier_mismatch_repo}"
perl -0pi -e 's/^release_bundle_identifier:.*/release_bundle_identifier: aegisops-beta-deadbeef/m' "${release_identifier_mismatch_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${release_identifier_mismatch_repo}" "release_bundle_identifier must bind to repository_revision"

unresolved_revision_repo="${workdir}/unresolved-revision"
create_valid_repo "${unresolved_revision_repo}"
perl -0pi -e 's/[0-9a-f]{40}/deadbeef/g' "${unresolved_revision_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${unresolved_revision_repo}" "repository_revision must resolve to a Git commit or tag"

reference_not_path_like_repo="${workdir}/reference-not-path-like"
create_valid_repo "${reference_not_path_like_repo}"
perl -0pi -e 's#<evidence-dir>/offline-install-bundle\.sbom\.cdx\.json#offline-install-bundle#m' "${reference_not_path_like_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${reference_not_path_like_repo}" "Invalid Phase 65.4 integrity manifest sbom_reference for offline-install-bundle"

external_uri_reference_repo="${workdir}/external-uri-reference"
create_valid_repo "${external_uri_reference_repo}"
perl -0pi -e 's#<evidence-dir>/offline-install-bundle\.sbom\.cdx\.json#s3://bucket/offline-install-bundle.sbom.cdx.json#m' "${external_uri_reference_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${external_uri_reference_repo}" "Invalid Phase 65.4 integrity manifest artifact reference"

quoted_external_uri_reference_repo="${workdir}/quoted-external-uri-reference"
create_valid_repo "${quoted_external_uri_reference_repo}"
perl -0pi -e 's#<evidence-dir>/offline-install-bundle\.sbom\.cdx\.json#"s3://bucket/offline-install-bundle.sbom.cdx.json"#m' "${quoted_external_uri_reference_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${quoted_external_uri_reference_repo}" "Invalid Phase 65.4 integrity manifest artifact reference"

artifact_path_mismatch_repo="${workdir}/artifact-path-mismatch"
create_valid_repo "${artifact_path_mismatch_repo}"
perl -0pi -e 's#docs/deployment/release/phase-65-3-upgrade-manifest\.yaml#docs/deployment/release/missing-upgrade-manifest.yaml#m' "${artifact_path_mismatch_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${artifact_path_mismatch_repo}" "Invalid Phase 65.4 integrity manifest artifact_path for release-channel-upgrade-manifest"

missing_artifacts_key_repo="${workdir}/missing-artifacts-key"
create_valid_repo "${missing_artifacts_key_repo}"
perl -0pi -e 's/^artifacts:\n//m' "${missing_artifacts_key_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${missing_artifacts_key_repo}" "Missing Phase 65.4 integrity manifest artifacts"

sbom_scope_mismatch_repo="${workdir}/sbom-scope-mismatch"
create_valid_repo "${sbom_scope_mismatch_repo}"
perl -0pi -e 's#offline-install-bundle at repository revision [0-9a-f]{40} for beta/design-partner packaging review only#all artifacts for latest GA#m' "${sbom_scope_mismatch_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${sbom_scope_mismatch_repo}" "Invalid Phase 65.4 SBOM scope for offline-install-bundle"

real_sha256_repo="${workdir}/real-sha256"
create_valid_repo "${real_sha256_repo}"
perl -0pi -e 's#<sha256:offline-install-bundle>#aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa#m' "${real_sha256_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_passes "${real_sha256_repo}"

artifact_name_mismatch_repo="${workdir}/artifact-name-mismatch"
create_valid_repo "${artifact_name_mismatch_repo}"
perl -0pi -e 's#offline-install-bundle\.sha256#release-notes.sha256#m' "${artifact_name_mismatch_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${artifact_name_mismatch_repo}" "Missing Phase 65.4 checksum evidence for offline-install-bundle"

duplicate_artifact_field_repo="${workdir}/duplicate-artifact-field"
create_valid_repo "${duplicate_artifact_field_repo}"
perl -0pi -e 's#(    sbom_reference: <evidence-dir>/offline-install-bundle\.sbom\.cdx\.json\n)#$1    sbom_reference: <evidence-dir>/release-notes.sbom.cdx.json\n#m' "${duplicate_artifact_field_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${duplicate_artifact_field_repo}" "Invalid Phase 65.4 integrity manifest duplicate artifact field for offline-install-bundle: sbom_reference"

checksum_value_mismatch_repo="${workdir}/checksum-value-mismatch"
create_valid_repo "${checksum_value_mismatch_repo}"
perl -0pi -e 's#<sha256:offline-install-bundle>#<sha256:release-notes>#m' "${checksum_value_mismatch_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${checksum_value_mismatch_repo}" "Invalid Phase 65.4 artifact-name mismatch for offline-install-bundle"

unknown_artifact_field_repo="${workdir}/unknown-artifact-field"
create_valid_repo "${unknown_artifact_field_repo}"
perl -0pi -e 's#(    signing_identity: <beta-signing-identity>\n)#$1    production_signing_infrastructure: true\n#m' "${unknown_artifact_field_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${unknown_artifact_field_repo}" "Invalid Phase 65.4 integrity manifest artifact field for offline-install-bundle: production_signing_infrastructure"

quoted_artifact_field_repo="${workdir}/quoted-artifact-field"
create_valid_repo "${quoted_artifact_field_repo}"
perl -0pi -e 's#(    signing_identity: <beta-signing-identity>\n)#$1    "production_signing_infrastructure": true\n#m' "${quoted_artifact_field_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${quoted_artifact_field_repo}" "Invalid Phase 65.4 integrity manifest artifact field for offline-install-bundle: production_signing_infrastructure"

readiness_overclaim_repo="${workdir}/readiness-overclaim"
create_valid_repo "${readiness_overclaim_repo}"
printf '%s\n' "Phase 65.4 integrity evidence proves RC readiness." >>"${readiness_overclaim_repo}/docs/phase-65-4-integrity-evidence-contract.md"
assert_fails_with "${readiness_overclaim_repo}" "Forbidden Phase 65.4 integrity evidence claim"

verifier_truth_repo="${workdir}/verifier-truth"
create_valid_repo "${verifier_truth_repo}"
printf '%s\n' "The verifier output becomes readiness truth." >>"${verifier_truth_repo}/docs/phase-65-4-integrity-evidence-contract.md"
assert_fails_with "${verifier_truth_repo}" "verifier or issue-lint truth shortcut"

gate_acceptance_overclaim_repo="${workdir}/gate-acceptance-overclaim"
create_valid_repo "${gate_acceptance_overclaim_repo}"
printf '%s\n' "Phase 65.4 integrity evidence satisfies Beta gate acceptance." >>"${gate_acceptance_overclaim_repo}/docs/phase-65-4-integrity-evidence-contract.md"
assert_fails_with "${gate_acceptance_overclaim_repo}" "gate acceptance overclaim"

workstation_path_repo="${workdir}/workstation-path"
create_valid_repo "${workstation_path_repo}"
workstation_checksum_path="/""Users/example/release-notes.sha256"
WORKSTATION_CHECKSUM_PATH="${workstation_checksum_path}" perl -0pi -e 's#<evidence-dir>/release-notes\.sha256#$ENV{WORKSTATION_CHECKSUM_PATH}#m' "${workstation_path_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${workstation_path_repo}" "Invalid Phase 65.4 integrity manifest artifact reference"

tilde_path_repo="${workdir}/tilde-path"
create_valid_repo "${tilde_path_repo}"
perl -0pi -e 's#<evidence-dir>/offline-install-bundle\.sbom\.cdx\.json#~/offline-install-bundle.sbom.cdx.json#m' "${tilde_path_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${tilde_path_repo}" "Invalid Phase 65.4 integrity manifest artifact reference"

customer_private_reference_repo="${workdir}/customer-private-reference"
create_valid_repo "${customer_private_reference_repo}"
perl -0pi -e 's#<evidence-dir>/offline-install-bundle\.sbom\.cdx\.json#customer-private/offline-install-bundle.sbom.cdx.json#m' "${customer_private_reference_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${customer_private_reference_repo}" "Invalid Phase 65.4 integrity manifest artifact reference"

quoted_placeholder_revision_repo="${workdir}/quoted-placeholder-revision"
create_valid_repo "${quoted_placeholder_revision_repo}"
perl -0pi -e 's/^repository_revision:.*/repository_revision: "main"/m; s/^release_bundle_identifier:.*/release_bundle_identifier: aegisops-beta-"main"/m; s/repository revision [0-9a-f]{40}/repository revision "main"/g' "${quoted_placeholder_revision_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${quoted_placeholder_revision_repo}" "Missing Phase 65.4 integrity manifest value: repository_revision"

production_secret_repo="${workdir}/production-secret"
create_valid_repo "${production_secret_repo}"
printf '%s\n' "signing_secret: prod-secret-value" >>"${production_secret_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${production_secret_repo}" "Invalid Phase 65.4 integrity manifest top-level field: signing_secret"

quoted_top_level_key_repo="${workdir}/quoted-top-level-key"
create_valid_repo "${quoted_top_level_key_repo}"
printf '%s\n' '"production-signing-infrastructure": true' >>"${quoted_top_level_key_repo}/docs/deployment/release/phase-65-4-integrity-evidence.yaml"
assert_fails_with "${quoted_top_level_key_repo}" "Invalid Phase 65.4 integrity manifest top-level field: production-signing-infrastructure"

production_secret_doc_repo="${workdir}/production-secret-doc"
create_valid_repo "${production_secret_doc_repo}"
printf '%s\n' "password: prod-secret-value" >>"${production_secret_doc_repo}/docs/phase-65-4-integrity-evidence-contract.md"
assert_fails_with "${production_secret_doc_repo}" "production secret material"

missing_doc_term_repo="${workdir}/missing-doc-term"
create_valid_repo "${missing_doc_term_repo}"
remove_doc_text "${missing_doc_term_repo}" "missing signature evidence;"
assert_fails_with "${missing_doc_term_repo}" "Missing required Phase 65.4 integrity contract term"

echo "Phase 65.4 integrity evidence verifier self-test passed."
